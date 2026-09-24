# Implementation Decisions

- 2026-09-24: Repository held only docs; implementation is greenfield.
- Google Play era boundary frozen at `2019-06` (median `year_month` of 639,596 single-market Google Play rows; count-balancing rule, no outcome data used).
- Data verified: 1,008,381 rows, 925 features (`var_thresh_0.01`), unique SHA, complete AndroZoo linkage, singleton labels use `singleton:<sha>`.
- Family-set membership: deterministic rank interleaving of named families by corpus support (no split or test information); per-seed eligibility (150 peer fit / 50 test) recorded as typed statuses.
- Eligibility is pre-split (see protocol-amendments.md); partitioner is support-constrained.
- Empirical finding: 6 cells in 5 LAMDA rows hold value 2 (all other 932,752,419 cells are 0/1). The loader binarizes to presence (`>0`) at the source boundary so the model input and the identity vector are the same binary representation; the count is recorded in the source audit.
