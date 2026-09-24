# Protocol Amendments

## 2026-09-24 - Pre-split family eligibility (Roadmap 11.3, 12.2)

Problem: 12.2 required a test-support check while 11.3 forbade test rows from influencing eligibility.
Resolution (user decision): eligibility is fixed before the split from corpus-wide support and component structure. The partitioner constructs the split to satisfy minimum fit and test support for every eligible client-family combination; only feasible combinations enter the plan. Test rows never change eligibility after the split.
No confirmatory results existed; no results invalidated.

## 2026-09-24 - Permutation-control null compatibility (Roadmap 27, 31.2)

Problem: the complementary-knowledge gate required a "null-compatible" permutation control without a decision rule. A placeholder (`permutation_null_max = 0.01`) was used during development and rejected the claim on a control of -0.010 (95% CI -0.016 to -0.004) against +0.162 for the real families.
Resolution (user decision): null compatibility is a 95% BCa equivalence criterion. The paired interval of the permutation-control complementary gain must lie within +/-0.03 absolute recall, the already predeclared complementary-knowledge practical-effect threshold. An interval entirely outside the band rejects the claim; an interval straddling a band edge, or an unavailable interval, leaves it INSUFFICIENT_EVIDENCE. No new threshold or ratio rule is introduced and `permutation_null_max` is removed.
No confirmatory results existed; no results invalidated.
