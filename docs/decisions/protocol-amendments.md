# Protocol Amendments

## 2026-09-24 - Pre-split family eligibility (Roadmap 11.3, 12.2)

Problem: 12.2 required a test-support check while 11.3 forbade test rows from influencing eligibility.
Resolution (user decision): eligibility is fixed before the split from corpus-wide support and component structure. The partitioner constructs the split to satisfy minimum fit and test support for every eligible client-family combination; only feasible combinations enter the plan. Test rows never change eligibility after the split.
No confirmatory results existed; no results invalidated.
