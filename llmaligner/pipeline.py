"""The rules → align → score loop over a writable alignment set.

Before the first round, code links what is near-certain (see
:mod:`llmaligner.rules`). Then each round:

1. **Align.** The aligner works on pairs it has not seen yet and on pairs with
   links below the threshold, in batches of several pairs per task. Links at or
   above the threshold are shown as settled and kept.
2. **Score** (optional). The scorer rates the links the aligner set or changed;
   links it rates below the threshold go back to the aligner next round.
3. **Rules** run again: confident new links are now evidence for the lexicon rule.

Rounds stop when no link is below the threshold, a round changes nothing, or
the round limit is reached. Every task is one model request when the evidence
in the prompt is enough (the agents may call read tools for more).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import anyio
from mcparser.corpus import CorpusStore
from mcparser.corpus.alignment import Link
from pydantic import BaseModel
from pydantic_ai.exceptions import UserError

from .agents.outputs import ALIGNER_AGENT, TaskBatch
from .agents.prompts import PairItem, task_prompt
from .agents.team import AlignerTeam, ModelUsage
from .lexicon import TranslationTable
from .rules import RULE_AGENT, RuleCount, Rules, RulesReport
from .settings import Settings


class TaskResult(BaseModel):
    round: int
    role: str
    sent_ids: list[str]
    summary: str | None = None
    error: str | None = None


class RoundReport(BaseModel):
    round: int
    aligned: int
    scored: int
    tasks: int
    changed: int
    rule_links: int
    low_confidence: int


class RunReport(BaseModel):
    target: str
    pairs: int
    links: int
    low_confidence: int
    mean_confidence: float
    rounds: list[RoundReport]
    rules: RulesReport
    tasks: list[TaskResult]
    total: ModelUsage
    usage: dict[str, ModelUsage]


ScoreKey = tuple[str, str, bool, float]


class Pipeline:
    """Runs rules, aligner and scorer rounds over one writable alignment set.

    ``sent_ids`` restricts the work to some pairs (default: every sentence of
    source A that is also in source B); ``evidence`` names the alignment sets
    used as translation evidence (default all); ``progress`` receives a line
    of text after every task and round.
    """

    def __init__(
        self,
        store: CorpusStore,
        target: str,
        team: AlignerTeam,
        settings: Settings,
        sent_ids: list[str] | None = None,
        evidence: list[str] | None = None,
        progress: Callable[[str], None] | None = None,
    ):
        self.store = store
        self.target = target
        self.team = team
        self.settings = settings
        self.alignment = store.alignment(target)
        self.alignment.require_writable()
        ids_b = {sentence.sent_id for sentence in self.alignment.source_b.sentences}
        available = [s.sent_id for s in self.alignment.source_a.sentences if s.sent_id in ids_b]
        for sent_id in sent_ids or []:
            self.store.get_parallel(target, sent_id)  # fails clearly for an unknown pair
        self.sent_ids = [i for i in available if i in set(sent_ids)] if sent_ids is not None else available
        self.evidence = evidence
        self.progress = progress or (lambda message: None)
        self.rules = Rules(store, target, settings.rules, evidence=evidence)
        self.rules_report = RulesReport()
        self.tasks: list[TaskResult] = []
        self.scored: set[ScoreKey] = set()
        """Links the scorer has rated (with the S/P and confidence it gave), so they are not rated again."""
        self.round = 0

    # ------------------------------------------------------------ state

    def confidence(self, sent_id: str) -> dict[str, float]:
        return {link.key: self.alignment.confidence(link) for link in self.alignment.links(sent_id)}

    def low_confidence(self) -> int:
        threshold = self.settings.threshold
        return sum(
            self.alignment.confidence(link) < threshold for sent_id in self.sent_ids for link in self.alignment.links(sent_id)
        )

    def seen_by_aligner(self) -> set[str]:
        return {edit.sent_id for edit in self.alignment.history if edit.agent == ALIGNER_AGENT}

    def _item(self, sent_id: str, review: list[Link], settled: list[Link]) -> PairItem:
        return PairItem(
            sent_id=sent_id,
            a=self.alignment.source_a.sentence(sent_id),
            b=self.alignment.source_b.sentence(sent_id),
            settled=settled,
            review=review,
        )

    def to_align(self) -> list[PairItem]:
        """Pairs the aligner has not seen, and pairs with links below the threshold."""
        seen = self.seen_by_aligner()
        items = []
        for sent_id in self.sent_ids:
            links = self.alignment.links(sent_id)
            settled = [link for link in links if self.alignment.confidence(link) >= self.settings.threshold]
            review = [link for link in links if self.alignment.confidence(link) < self.settings.threshold]
            if sent_id not in seen or review:
                items.append(self._item(sent_id, review, settled))
        return items

    def to_score(self) -> list[PairItem]:
        """Pairs with links that the aligner set or changed and the scorer has not rated."""
        items = []
        for sent_id in self.sent_ids:
            links = self.alignment.links(sent_id)
            review = [
                link for link in links
                if link.agent == ALIGNER_AGENT and (sent_id, link.key, link.sure, self.alignment.confidence(link)) not in self.scored
            ]  # fmt: skip
            if review:
                items.append(self._item(sent_id, review, [link for link in links if link not in review]))
        return items

    def batches(self, items: list[PairItem]) -> list[list[PairItem]]:
        """Tasks of at most ``batch_sentences`` pairs and ``batch_words`` words."""
        groups: list[list[PairItem]] = []
        size = 0
        for item in items:
            if groups and len(groups[-1]) < self.settings.batch_sentences and size + item.words <= self.settings.batch_words:
                groups[-1].append(item)
                size += item.words
            else:
                groups.append([item])
                size = item.words
        return groups

    def changed_since(self, seq: int) -> int:
        """Pairs whose links an agent (not the rules) changed after history entry ``seq``."""
        return sum(
            edit.seq > seq and edit.agent != RULE_AGENT and edit.old != edit.new for edit in self.alignment.history
        )

    def apply_rules(self) -> int:
        self.rules.refresh()
        report = self.rules.apply(self.sent_ids)
        self.rules_report.sentences = report.sentences
        for name, count in report.rules.items():
            self.rules_report.rules.setdefault(name, RuleCount()).links += count.links
        return report.total

    # ------------------------------------------------------------ tasks

    async def _each(self, batches: list[list[PairItem]], work: Callable[[list[PairItem]], Awaitable[None]]) -> None:
        if self.settings.concurrency == 1:
            for batch in batches:
                await work(batch)
            return
        limiter = anyio.CapacityLimiter(self.settings.concurrency)

        async def limited(batch: list[PairItem]) -> None:
            async with limiter:
                await work(batch)

        async with anyio.create_task_group() as group:
            for batch in batches:
                group.start_soon(limited, batch)

    async def _task(self, role: str, items: list[PairItem], table: TranslationTable | None) -> None:
        sent_ids = [item.sent_id for item in items]
        result = TaskResult(round=self.round, role=role, sent_ids=sent_ids)
        label = f"[round {self.round}] {role} {', '.join(sent_ids)}"
        if role == "aligner":
            batch = TaskBatch(self.target, sent_ids, settled={item.sent_id: item.settled for item in items})
        else:
            batch = TaskBatch(self.target, sent_ids, review={item.sent_id: item.review for item in items})
        try:
            names = (self.alignment.source_a.name, self.alignment.source_b.name)
            prompt = task_prompt(
                role, items, {i: self.confidence(i) for i in sent_ids}, table, names,
                self.settings.misc_keys, self.settings.candidates,
            )  # fmt: skip
            answer = await self.team.run(role, prompt, batch)
            result.summary = answer.summary
            if role == "scorer":
                for sent_id in sent_ids:
                    for link in self.alignment.links(sent_id):
                        self.scored.add((sent_id, link.key, link.sure, self.alignment.confidence(link)))
            self.progress(f"{label}: {result.summary}")
        except UserError:
            raise  # configuration problems (e.g. a missing API key) stop the run
        except Exception as error:  # one failed task must not lose a long run
            result.error = f"{type(error).__name__}: {error}"
            self.progress(f"{label} FAILED: {result.error}")
        self.tasks.append(result)

    async def align(self) -> tuple[int, int]:
        """Run the aligner where needed. Returns (pairs, tasks)."""
        items = self.to_align()
        table = TranslationTable(self.store, self.evidence, min_confidence=self.settings.evidence_confidence)
        batches = self.batches(items)
        await self._each(batches, lambda batch: self._task("aligner", batch, table))
        return len(items), len(batches)

    async def score(self) -> tuple[int, int]:
        """Run the scorer on the aligner's unrated links. Returns (pairs, tasks)."""
        if not self.settings.enabled("scorer"):
            return 0, 0
        items = self.to_score()
        batches = self.batches(items)
        await self._each(batches, lambda batch: self._task("scorer", batch, None))
        return len(items), len(batches)

    # ------------------------------------------------------------ run

    async def run(self, rounds: int | None = None) -> RunReport:
        """Apply the rules, then run up to ``rounds`` align/score rounds (default from the settings)."""
        rounds = rounds or self.settings.rounds
        reports: list[RoundReport] = []
        async with self.team:
            self.progress(f"Rules linked {self.apply_rules()} word pairs.")
            for number in range(1, rounds + 1):
                self.round = number
                start = len(self.alignment.history)
                aligned, align_tasks = await self.align()
                scored, score_tasks = await self.score()
                rule_links = self.apply_rules()
                reports.append(
                    RoundReport(
                        round=number, aligned=aligned, scored=scored, tasks=align_tasks + score_tasks,
                        changed=self.changed_since(start), rule_links=rule_links, low_confidence=self.low_confidence(),
                    )
                )  # fmt: skip
                self.progress(f"Round {number}: {reports[-1].model_dump()}")
                if align_tasks == 0 or reports[-1].changed == 0 or reports[-1].low_confidence == 0:
                    break
        return self.report(reports)

    def report(self, rounds: list[RoundReport]) -> RunReport:
        links = [link for sent_id in self.sent_ids for link in self.alignment.links(sent_id)]
        scores = [self.alignment.confidence(link) for link in links]
        return RunReport(
            target=self.target,
            pairs=len(self.sent_ids),
            links=len(links),
            low_confidence=self.low_confidence(),
            mean_confidence=round(sum(scores) / len(scores), 3) if scores else 0.0,
            rounds=rounds,
            rules=self.rules_report,
            tasks=self.tasks,
            total=self.team.total(),
            usage=self.team.usage,
        )
