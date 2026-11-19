# Changelog

All notable changes to MCAligner. The format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.2.0a1]

First alpha release on PyPI. Install with `pip install --pre mcaligner`.

### Added
- `mcaligner run`: rules, aligner agent, scorer agent and refinement rounds over two parsed CoNLL-U files, with
  batching, concurrency, a cost report and a resumable alignment set (JSON Lines, MCParser's format).
- Rules without a model (identical symbols, transliterated names, dominant lexicon match).
- `mcaligner evaluate` (P/R/F1 over sure and all links, AER), `lexicon` (bilingual lexicon export), `rules`
  (apply or measure the rules), `settings`, and `mcp serve` / `mcp config` (MCParser's MCP server plus the
  exploration tools `similar_pairs`, `lemma_links`, `link_examples`, `pair_words`, `category_links`,
  `alignment_stats`).
- Bundled annotation guidelines (`--guidelines`): `grc-lat` (default), `bicross`, and drafts for `grc-cop`,
  `grc-ar`, `lat-ar`, `grc-syr`, `syr-ar`, `got-lat`.
- `--columns`, `--tools` and `--link-punctuation` to control what the agents see and may do.
- `mcaligner --version`, documentation, and a project logo.
