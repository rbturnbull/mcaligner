# Contributing

Thanks for helping with MCAligner. Bug reports, feature ideas and pull requests are welcome.

## Setting up

```bash
git clone https://github.com/rbturnbull/mcaligner && cd mcaligner
uv sync --all-groups
uv run pytest
```

Python 3.11 to 3.14 are supported. The repository pins 3.13 for development (`.python-version`).

## Before opening a pull request

- `uv run pytest` must pass. Aim for **100% line and branch coverage** (it is reported, but a shortfall does not fail CI). The tests never call a real model or
  the network; agents are tested with the scripted models in `tests/scripted.py`.
- `./mkdocs.sh` (Sphinx with warnings as errors) must build the documentation. Update the docs and
  `CHANGELOG.md` for user-visible changes.
- Keep `uv.lock` current when you change dependencies (`uv lock`); CI installs with `--locked`.
- Match the surrounding code: type hints, short docstrings, pydantic models for return values, and
  `CorpusError` subclasses for expected failures.

`AGENTS.md` records the design decisions and the measurements behind them. Read it before changing
how the agents, rules or scorer behave, and add what you learned to it.

## Changes that affect accuracy or cost

Say what you measured. The agents' output varies between runs, so a difference of about 0.015 F1
on 80 sentence pairs is noise. Give the corpus, the number of pairs, the guidelines, the models,
the cost and ideally two runs. Tune on a dev subset and report on a held-out one.

## Reporting a bug

Include `mcaligner --version`, the command, the settings and the error. Do not paste API keys or text
you may not share.
