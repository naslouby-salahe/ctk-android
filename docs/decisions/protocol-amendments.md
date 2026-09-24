# Protocol Amendments

## 2026-09-24 - Pre-split family eligibility (Roadmap 11.3, 12.2)

Problem: 12.2 required a test-support check while 11.3 forbade test rows from influencing eligibility.
Resolution (user decision): eligibility is fixed before the split from corpus-wide support and component structure. The partitioner constructs the split to satisfy minimum fit and test support for every eligible client-family combination; only feasible combinations enter the plan. Test rows never change eligibility after the split.
No confirmatory results existed; no results invalidated.

## 2026-09-24 - Permutation-control null compatibility (Roadmap 27, 31.2)

Problem: the complementary-knowledge gate required a "null-compatible" permutation control without a decision rule. A placeholder (`permutation_null_max = 0.01`) was used during development and rejected the claim on a control of -0.010 (95% CI -0.016 to -0.004) against +0.162 for the real families.
Resolution (user decision): null compatibility is a 95% BCa equivalence criterion. The paired interval of the permutation-control complementary gain must lie within +/-0.03 absolute recall, the already predeclared complementary-knowledge practical-effect threshold. An interval entirely outside the band rejects the claim; an interval straddling a band edge, or an unavailable interval, leaves it INSUFFICIENT_EVIDENCE. No new threshold or ratio rule is introduced and `permutation_null_max` is removed.
No confirmatory results existed; no results invalidated.

## 2026-09-24 - Stage D fairness grids and hyperparameter freeze (Roadmap 16.3, 38)

Grids (predeclared in `configs/experiments.yaml`): local epochs {10, 20, 40}, fine-tuning epochs {2, 5, 10}, FedProx strength {0.001, 0.01, 0.1}. Selection rule: highest mean own-domain calibration-partition AUROC across development seeds and clients, ties to the smaller value; test rows never used, no new threshold. Result on development seeds 1-5: local epochs 10, fine-tuning epochs 2, FedProx strength 0.1. All three are grid-edge selections and the FedProx gap is small; grids were not extended. FedAvg rounds/local epochs and centralized epochs stay at their configured values (not searched).
Consequence: every development run made under the previous hyperparameters is stale (run provenance fingerprints the resolved training configuration) and is re-run under the frozen values. No confirmatory seed has been run.

## 2026-09-24 - Stage F protocol freeze (Roadmap 38)

Frozen before any confirmatory seed: data (LAMDA release var_thresh_0.01 fingerprint e9908f9a50ba1068a362f9fc943017afed2bb05dbccaaa1579d093c1ead677a9; AndroZoo metadata fingerprint f0d118739757cf9135830e2f20f444fb28adb426fe4a3c3329178c7084a97904), client definitions, family sets, metrics, statistical plan, the twelve claim gates (including the permutation equivalence rule), hyperparameters (local epochs 10, fine-tuning epochs 2, FedProx 0.1), the eight figures and seven tables, and confirmatory seeds 100 to 109. Configuration fingerprint 84ec9a19d140924ee72af71cf893bc6b0152e307cc9bf861319237b4d4d0ac83 at code revision dccf996; the confirmatory plan is 140 runs, none infeasible. Pre-confirmatory checks: doctor passes, the smoke run passes, the development rerun reproduces the frozen selection, and the confirmatory directories were empty. Any later change to a frozen item is a protocol amendment (Roadmap 47) and is recorded here.
Authorisation: the user instructed the confirmatory stages to proceed ("continue the implementation and don't stop until all is finished").
