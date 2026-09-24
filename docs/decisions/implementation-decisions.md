# Implementation Decisions

- 2026-09-24: Repository held only docs; implementation is greenfield.
- Google Play era boundary frozen at `2019-06` (median `year_month` of 639,596 single-market Google Play rows; count-balancing rule, no outcome data used).
- Data verified: 1,008,381 rows, 925 features (`var_thresh_0.01`), unique SHA, complete AndroZoo linkage, singleton labels use `singleton:<sha>`.
- Family-set membership: deterministic rank interleaving of named families by corpus support (no split or test information); per-seed eligibility (150 peer fit / 50 test) recorded as typed statuses.
- Eligibility is pre-split (see protocol-amendments.md); partitioner is support-constrained.
- Empirical finding: 6 cells in 5 LAMDA rows hold value 2 (all other 932,752,419 cells are 0/1). The loader binarizes to presence (`>0`) at the source boundary so the model input and the identity vector are the same binary representation; the count is recorded in the source audit.
- 2026-09-24 (user decision): source-code fingerprints and any dirty-tree check are removed. Stage and run provenance are keyed by source, configuration, seed, partition and experiment identity only. Deviation from technical_docs 43 (which lists code identity): the git revision is still recorded in `results/provenance/code.json`, but code edits no longer invalidate artifacts. An unreadable `provenance.json` is treated as stale and rebuilt.
- Logging: every log line is `logs.<level>(LogEvent.X, {LogField.Y: value})`; events and field keys are enums, only `logs.py` touches structlog/logging, and each command writes readable console output plus `outputs/logs/<command>.jsonl`. Tests enforce enum-only events and keys, no `print`, and that every CLI entry point and preprocessing stage reaches an emission.
- Typing: signatures and fields use semantic aliases only. Generic numpy aliases and raw `pl.DataFrame`/`pl.Series` are defined once in `types.py` and are not allowed elsewhere; `bool`, inline `dict[...]`, bare `np.ndarray` and anonymous fixed tuples are forbidden outside `types.py`. Documented exceptions: `ANN401` is ignored only in `types.py` for the matplotlib `Protocol` facade (matplotlib's stubs leave `**kwargs` unknown), and `enums.LibraryOption` holds `Literal`-typed third-party option strings.

## Smoke mode covers every experiment

The eight confirmatory-only experiments list `smoke` in `modes` so the smoke plan exercises each of them end to end on the smoke seed with smoke training. This checks executability only (no evidence is used); confirmatory results still require seeds 100 to 109. Development-mode experiment specs are unchanged, so development runs stay fresh.
