# Implementation Decisions

- 2026-09-24: Repository held only docs; implementation is greenfield.
- Google Play era boundary frozen at `2019-06` (median `year_month` of 639,596 single-market Google Play rows; count-balancing rule, no outcome data used).
- Data verified: 1,008,381 rows, 925 features (`var_thresh_0.01`), unique SHA, complete AndroZoo linkage, singleton labels use `singleton:<sha>`.
- Family-set membership: deterministic rank interleaving of named families by corpus support (no split or test information); per-seed eligibility (150 peer fit / 50 test) recorded as typed statuses.
- Eligibility is pre-split (see protocol-amendments.md); partitioner is support-constrained.
