# CTK-Android Results and Evidence Inventory

> Generated from saved machine-readable artifacts only (`outputs/`, `results/`, run manifests, logs, committed configuration). Nothing in this document changes a metric, gate, threshold, seed, family set, hyperparameter or promoted artifact. Where two sources disagree the discrepancy is listed in Sections 4 and 35 rather than silently resolved. All differences are absolute recall (or rate) differences unless stated; "pos" is the number of paired seeds with a positive effect; CIs are the pipeline's 95% BCa paired intervals across seeds. Development numbers are always labelled development-only.

## Contents

1. Executive Summary
2. Evidence Sources and Provenance
3. Complete Experiment Inventory
4. Run Reconciliation
5. Development Evidence
6. Fairness and Hyperparameter Audit (development only)
7. Confirmatory Main Results
8. Collaboration Decomposition
9. Own-Domain Results
10. Worst-Client Results
11. Natural-Scarcity Results
12. Dose-Response Results
13. Family-Level Results
14. Client-Level Results
15. Model-Family Replication
16. Family-Set Replication
17. Support Sensitivity
18. Operating-Point Sensitivity
19. Robustness Matrix (main CTK result)
20. Negative Controls
21. Statistical Evidence
22. Gate Outcomes
23. Claim Inventory
24. Warnings and Anomalies
25. Runtime and Compute Evidence
26. Potentially Underused Existing Evidence
27. Evidence-Preserving Improvement Opportunities
28. Novelty Strengthening Opportunities
29. Claim Strengthening Opportunities
30. Rejected and Narrowed Claims: Can Anything Legitimately Be Improved?
31. Generic-Pooling-Majority Analysis
32. Feature-Novelty Analysis
33. New-Mechanism Analysis
34. Dose-Response Narrowing Analysis
35. Narrative-versus-Evidence Audit
36. Experiments That Would Likely Add Little Value
37. Genuine Evidence Gaps
38. Possible Post-Confirmatory Extensions
39. Decision Support — Recommended Next Actions
40. Suggested Final Scientific Story
41. Complete Artifact Index

## 1. Executive Summary

Confirmatory results (seeds 100 to 109) unless stated. Levels are means across seeds (the pipeline computes intervals only for paired differences).

| Result | Estimate | 95% CI | Positive seeds | Population | Model | Operating point | Status |
|---|---|---|---|---|---|---|---|
| Local unseen-family recall | 0.507 | n/a (level; seed sd 0.060) | n/a | federation-wide | MLP, local | alpha 0.05 | confirmatory (level, no interval) |
| No-family collaborative recall | 0.521 | n/a (level; seed sd 0.073) | n/a | federation-wide | MLP, fedavg | alpha 0.05 | confirmatory (level, no interval) |
| Peer-family collaborative recall | 0.638 | n/a (level; seed sd 0.084) | n/a | federation-wide | MLP, fedavg | alpha 0.05 | confirmatory (level, no interval) |
| Full-exposure recall | 0.682 | n/a (level; seed sd 0.084) | n/a | federation-wide | MLP, fedavg | alpha 0.05 | confirmatory (level, no interval) |
| Total collaboration gain | +0.132 | [+0.090, +0.167] | 10/10 | federation-wide | MLP, FedAvg | alpha 0.05 | confirmatory: gate collaboration-benefit promoted |
| Generic pooling gain | +0.014 | [-0.038, +0.054] | 7/10 | federation-wide | MLP, FedAvg | alpha 0.05 | confirmatory: not different from zero |
| CTK gain | +0.117 | [+0.090, +0.145] | 10/10 | federation-wide | MLP, FedAvg | alpha 0.05 | confirmatory: gate complementary-knowledge promoted |
| Own-domain CTK gain | +0.107 | [+0.068, +0.144] | 10/10 | own-domain | MLP, FedAvg | alpha 0.05 | confirmatory: gate own-domain-benefit promoted (own-domain pooling gain -0.069) |
| Worst-client CTK effect | +0.173 | [+0.116, +0.242] | 10/10 | worst client | MLP, FedAvg | alpha 0.05 | confirmatory: gate worst-client-benefit promoted |
| Natural-scarcity effect (CTK-like contrast) | +0.113 | [+0.094, +0.128] | 10/10 | federation-wide | MLP, FedAvg | alpha 0.05 | confirmatory, no gate |
| Known-family cost (change vs local) | -0.033 | seed range [-0.062, -0.003] (no interval computed) | 0/10 | known-family | MLP, FedAvg | alpha 0.05 | confirmatory; strongest arm FedProx -0.006 -> gate known-family-safety promoted |
| Permutation-control effect (CTK) | -0.001 | [-0.007, +0.007] | 4/10 | federation-wide | MLP, FedAvg | alpha 0.05 | confirmatory: null-compatible within +/-0.03 |
| Main dose-response result (gain over zero dose at all available, effective dose about 296) | +0.124 | seed sd 0.047 (no interval computed) | 10/10 | federation-wide hidden family | MLP, FedAvg | alpha 0.05 | confirmatory; gate `dose-response` narrowed and NOT interpreted (N1) |
| Main robustness result (FedAvg CTK gain, federation-wide, 14 scopes) | +0.064 to +0.143 | all intervals above zero | at least 9/10 | federation-wide | MLP, linear, trees; 4 family/support regimes; 3 salts; 3 alphas | alpha 0.01 to 0.10 | confirmatory; no formal robustness gate |

### Inventory in one place

| Item | Count |
|---|---|
| Experiments defined | 14 |
| Planned runs (smoke 11 + development 25 + confirmatory 140) | 176 |
| Run directories found | 176 |
| Valid runs (completed, all structural validations passed) | 176 |
| Development runs | 25 |
| Confirmatory runs | 140 |
| Smoke runs | 11 |
| Claim gates implemented | 12 |
| Promoted / narrowed / rejected / insufficient | 8 / 1 / 3 / 0 |

### What the evidence says, and what to read carefully

**Strong and stable.** The MLP collaboration gain is carried by the complementary component: FedAvg CTK +0.117 (10/10 seeds, permutation control null) against generic pooling +0.014 (not different from zero). It holds in the own domain (+0.107), for the worst client (+0.173), in natural scarcity (+0.113), for linear and tree models, three alternative partition salts, three operating points, lower training support and both family-support regimes; package-only grouping does not inflate it.

**Read carefully.** (1) The effect is about half as large on the disjoint replication family set (+0.064). (2) Generic pooling *lowers* own-domain recall of a locally hidden family (-0.069; negative in 9 of 12 scopes); the own-domain total gain is only +0.038. (3) The linear model has the opposite composition (pooling about two thirds). (4) FedAvg loses 0.033 known-family recall (concentrated at `anzhi`); the promoted known-family-safety claim refers to the strongest arm, FedProx. (5) The feature-novelty hypothesis is unresolved, not refuted (rho +0.57 and +0.33 with 7 and 8 families). (6) The dose-response gate outcome (`narrowed`) rests on gate mechanics that may not match the Roadmap text and is not interpreted (N1); requested dose is realised at about 8%. (7) Two support-sensitivity runs (seed 106) exceed the FPR tolerance at the primary alpha. (8) The new-mechanism trigger does not fire (headroom 0.049 and 0.029).

**Is the central claim already strong enough?** The central complementary-knowledge finding is well supported by the current evidence *as scoped above*. The open items are wording precision (Section 27.3), the dose-gate discrepancy (N1) and external validity (Section 37), none of which changes the promoted CTK result.

## 2. Evidence Sources and Provenance

### 2.1 What was read

Roadmap (`docs/Roadmap.md`), technical contract, Audit Matrix, both decision logs, README, all four configuration files, the three run plans (`outputs/plans/*`), every run directory (`status.json`, `manifest.json`, `validation.json`, `provenance.json`, `metrics/*.parquet`, `thresholds.parquet`, `exposure.parquet`, `novelty.parquet`), the analysis and statistics artifacts per mode, the generated report tables and figures, the promoted `results/` tree, the runtime logs in `outputs/logs/*.jsonl` and Git history for result-affecting changes.

### 2.2 Frozen provenance of the promoted confirmatory evidence

| Item | Value |
|---|---|
| Execution mode of `results/` | confirmatory |
| Configuration fingerprint (frozen at Stage F) | `84ec9a19d140924ee72af71cf893bc6b0152e307cc9bf861319237b4d4d0ac83` |
| Roadmap digest recorded at promotion | `09a329281b63debcf29cd1c17c3ef519d38d14a717bf75314f53870957f36854` |
| Code revision recorded in `results/provenance/code.json` | `e079972095dbfd852e1a1ffb887be0e959cdc91f` |
| Environment recorded at promotion | python=3.12.3, platform=Linux-6.18.33.2-microsoft-standard-WSL2-x86_64-with-glibc2.39, torch=2.14.0+cu130, numpy=2.5.3, polars=1.44.2, scikit_learn=1.9.1, device=cuda |
| Confirmatory seeds | 100, 101, 102, 103, 104, 105, 106, 107, 108, 109 |
| Development seeds | 1, 2, 3, 4, 5 |
| Smoke seeds | 0 |
| Confirmatory operating points (alpha) | 0.01, 0.05, 0.1 (primary 0.05) |
| Statistics | BCa paired bootstrap (9999 resamples), exact Wilcoxon, Holm within the primary contrast family, cluster bootstrap (2000 resamples), statistics seed 20260924 |

Source data fingerprints: lamda: `e9908f9a50ba1068a362f9fc943017afed2bb05dbccaaa1579d093c1ead677a9`; androzoo: `f0d118739757cf9135830e2f20f444fb28adb426fe4a3c3329178c7084a97904`.

### 2.3 Provenance notes that affect reading the evidence

- `results/provenance/code.json` records revision `e079972` (the Stage F freeze commit). The current `results/gates/claims.csv` was regenerated after a small wording fix to the representation-limited-family gate that was committed later; the recorded revision therefore does not contain that fix. No numeric outcome changed (see Section 35, item N3).
- Run provenance keys on source data, resolved training configuration, budget, operating and novelty settings and the experiment specification, not on a source-code fingerprint (a deliberate decision recorded in `docs/decisions/implementation-decisions.md`). A code change that alters evaluation logic is therefore not detected as staleness; the confirmatory runs were all executed after the final evaluation-logic change.
- Evidence collection excludes stale runs and logs them. All 320 stale-run log events belong to development seeds 1 to 5 (history before the frozen-hyperparameter re-run). No confirmatory run was ever stale.

## 3. Complete Experiment Inventory

All 14 experiments defined in `configs/experiments.yaml` are listed. Client scope for every experiment is the same four simulated domains (`anzhi`, `appchina`, `play-early`, `play-late`, from the AndroZoo market plus a 2019-06 Play era boundary); dataset scope is LAMDA release `var_thresh_0.01` (1,008,381 rows, 925 binary features) joined to AndroZoo metadata. Operating points for every experiment are alpha 0.01, 0.05 (primary) and 0.10.

| Experiment | Modes | Scientific purpose | Roadmap | Research question | Hypothesis | Gates fed | Model | Family set | Grouping | Eligibility profile | Train rows/client | Learners (arms) | Conditions | Salts | Runs completed / planned |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `end-to-end` | smoke | Pipeline feasibility at smoke scale (Stage C). | §38 Stage C | - | - | - | mlp | primary | component | smoke | 800 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1 |
| `baseline-fairness` | development | Baseline-fairness grids for local epochs, fine-tuning epochs and FedProx strength (Stage D). No confirmatory role. | §16.3, §38 Stage D | - | - | frozen hyperparameters | mlp | primary | component | primary | 6000 | local, fedavg, fedprox, fedavg-finetune | peer-present + fairness grids | [0] | development: 5/5 |
| `controlled-exposure` | development, confirmatory | Primary experiment. Hides a target family from one client (hide-from-target), compares local, centralized and four federated arms, blend, with peer-present, family-absent-everywhere and full-exposure conditions. | §13, §18, §19 | RQ1, RQ2, RQ4, RQ5, RQ7, RQ9 (also RQ6 via novelty) | H1, H2, H3, H4, H6, H8, H9 (H7) | local-deficit, collaboration-benefit, complementary-knowledge, generic-pooling-majority, own-domain-benefit, worst-client-benefit, known-family-safety, family-dependence, representation-limited-family, feature-novelty-explanation, new-mechanism-trigger | mlp | primary | component | primary | 6000 | local, central, fedavg, fedprox, fedavg-finetune, blend | peer-present, family-absent-everywhere, full-exposure | [0] | development: 5/5, confirmatory: 10/10 |
| `peer-dose-response` | development, confirmatory | Varies requested peer exposure of the hidden family (0, 1, 10, 50, 100, 500, 1000, all) with target exposure at zero. | §20 | RQ3 | H5 | dose-response | mlp | primary | component | primary | 6000 | central, fedavg, fedavg-finetune | peer-present + dose sweep | [0] | development: 5/5, confirmatory: 10/10 |
| `natural-scarcity` | development, confirmatory | Uses naturally scarce families (target share at most 5%) instead of constructed hiding; validates the controlled design. | §21 | RQ2 (validation), RQ4 | H3 (validation) | none (no claim gate consumes it) | mlp | primary | component | primary | 6000 | local, central, fedavg | peer-present, family-absent-everywhere | [0] | development: 5/5, confirmatory: 10/10 |
| `family-permutation-control` | development, confirmatory | Negative control: family labels permuted so a peer-family-present arm carries no genuine family information. | §27 | RQ2 (negative control) | H3 | complementary-knowledge (null-compatibility condition) | mlp | primary | component | primary | 6000 | local, central, fedavg | peer-present, family-absent-everywhere | [0] | development: 5/5, confirmatory: 10/10 |
| `replication-family-set` | smoke, confirmatory | Disjoint replication family set with the same design. | §12, §28 | RQ8, RQ6 | H3, H4, H7 | complementary-knowledge (third scope), feature-novelty-explanation (second scope) | mlp | replication | component | primary | 6000 | local, central, fedavg, fedprox, fedavg-finetune, blend | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `model-family-replication-linear` | smoke, confirmatory | Same design with a linear classifier. | §28 | RQ8 | H3 | representation-limited-family (second model family) | linear | primary | component | primary | 6000 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `model-family-replication-trees` | smoke, confirmatory | Same design with gradient-boosted trees; centralized arms only (trees are not federated). | §28 | RQ8 | H3 | representation-limited-family (second model family) | gradient-boosted-trees | primary | component | primary | 6000 | local, central | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `training-support-sensitivity` | smoke, confirmatory | Lower per-client training budget (1,500 instead of 6,000 rows). | §15, §28 | RQ8 | - | none (descriptive) | mlp | primary | component | primary | 1500 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `partition-salt-sensitivity` | smoke, confirmatory | Three alternative partition salts per seed. | §11, §28 | RQ8 | - | none (descriptive) | mlp | primary | component | primary | 6000 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [1, 2, 3] | smoke: 3/3, confirmatory: 30/30 |
| `family-support-sensitivity-low` | smoke, confirmatory | Lower family support thresholds (peer fit 100, federation test 30). | §12, §28 | RQ8 | - | none (descriptive) | mlp | primary | component | low | 6000 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `family-support-sensitivity-high` | smoke, confirmatory | Higher family support thresholds (peer fit 300, federation test 100). | §12, §28 | RQ8 | - | none (descriptive) | mlp | primary | component | high | 6000 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |
| `package-only-grouping` | smoke, confirmatory | Leakage-hardening sensitivity: package-only grouping instead of package plus exact feature-vector components. | §11.4, §27, §28 | RQ8 | - | none (descriptive) | mlp | primary | package-only | primary | 6000 | local, central, fedavg | peer-present, family-absent-everywhere, full-exposure | [0] | smoke: 1/1, confirmatory: 10/10 |

The pipeline computes no formal robustness gate. Only `controlled-exposure`, `peer-dose-response`, `family-permutation-control`, `replication-family-set` (CTK and feature-novelty scopes) and the two model-family replications (representation-limited-family claim only) feed a claim gate. `natural-scarcity`, both support sensitivities, `training-support-sensitivity`, `partition-salt-sensitivity` and `package-only-grouping` feed no gate and are presented descriptively in Sections 11 and 15 to 19.

## 4. Run Reconciliation

Sources cross-checked for every run: the run plan (`run-matrix.parquet`), the run directory (`status.json`, `manifest.json`, `validation.json`), the analysis run index (`outputs/analysis/<mode>/run-index.parquet`), the promoted `results/gates/seed-status.csv` and the runtime log (`run-finished` events). "Valid" means status `completed` with every structural validation passed. "Warn" counts non-structural validation failures (`operating-point-realised`). "Executions" counts logged `run-finished` events (including superseded re-runs).

| Mode | Experiment | Planned | Run dirs | Completed | Valid | Warn | Missing | Duplicate/extra | Infeasible | Logged executions | Superseded executions |
|---|---|---|---|---|---|---|---|---|---|---|---|
| smoke | `end-to-end` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `replication-family-set` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| smoke | `model-family-replication-linear` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `model-family-replication-trees` | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| smoke | `training-support-sensitivity` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `partition-salt-sensitivity` | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `family-support-sensitivity-low` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `family-support-sensitivity-high` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | `package-only-grouping` | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| development | `baseline-fairness` | 5 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 21 | 16 |
| development | `controlled-exposure` | 5 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 15 | 10 |
| development | `peer-dose-response` | 5 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 15 | 10 |
| development | `natural-scarcity` | 5 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 15 | 10 |
| development | `family-permutation-control` | 5 | 5 | 5 | 5 | 0 | 0 | 0 | 0 | 15 | 10 |
| confirmatory | `controlled-exposure` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `peer-dose-response` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `natural-scarcity` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `family-permutation-control` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `replication-family-set` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `model-family-replication-linear` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `model-family-replication-trees` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `training-support-sensitivity` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `partition-salt-sensitivity` | 30 | 30 | 30 | 30 | 0 | 0 | 0 | 0 | 30 | 0 |
| confirmatory | `family-support-sensitivity-low` | 10 | 10 | 10 | 10 | 1 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `family-support-sensitivity-high` | 10 | 10 | 10 | 10 | 1 | 0 | 0 | 0 | 10 | 0 |
| confirmatory | `package-only-grouping` | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 10 | 0 |

| Mode | Planned | Run dirs | Completed | Valid | Warn | Missing | Extra | Infeasible | Executions | Superseded |
|---|---|---|---|---|---|---|---|---|---|---|
| confirmatory | 140 | 140 | 140 | 140 | 2 | 0 | 0 | 0 | 140 | 0 |
| development | 25 | 25 | 25 | 25 | 0 | 0 | 0 | 0 | 81 | 56 |
| smoke | 11 | 11 | 11 | 11 | 1 | 0 | 0 | 0 | 1 | 0 |
| **all** | 176 | 176 | 176 | 176 | 3 | 0 | 0 | 0 | 222 | 56 |

Cross-source checks for confirmatory runs: plan rows 140; run directories 140; analysis run index 140 rows, all `completed`; promoted seed-status 140 rows, all `completed`. Every source agrees. The confirmatory plan lists 0 infeasible runs; the development and smoke plans list 0 and 0.

Notes on reading the table:

- **Smoke.** The plan holds 11 smoke runs (`end-to-end` plus one smoke-scale executability check for each of the eight confirmatory-only experiments, added during the audit). The smoke `end-to-end` run was executed by the `smoke` command (13 s; logged in `smoke.jsonl`, hence 0 in the `run.jsonl` execution count). One further smoke run (`replication-family-set`) was executed by hand through the CLI. The remaining nine smoke runs were executed by the integration tests, so their executions are in no persistent log; their directories and status files exist and are valid, except for one non-structural warning (smoke `model-family-replication-trees`). Smoke evidence is not scientific evidence.
- **Development.** 25 current runs (5 experiments x seeds 1 to 5). The logged executions exceed 25 because every development run was re-executed after protocol-relevant changes (frozen hyperparameters, calibration-set AUROC, duplicate-count columns); the superseded executions are history, not current evidence, and the analysis collects only the 25 current, non-stale runs.
- **Superseded failure.** One superseded development execution (`baseline-fairness`, seed 1, 17:02 UTC) ended `failed-validation` on the structural check `hidden-rows-in-test-only`; the check was corrected and the run re-executed. The current run passes (Section 24, A11).
- **Confirmatory.** 140 executions for 140 planned runs: no superseded, no duplicate, no stale, no infeasible run.

## 5. Development Evidence

**Everything in this section is development-only (seeds 1 to 5). None of it is confirmatory.** Development evidence was used for debugging, fairness grids, gate design and the frozen hyperparameters. The development claim table below is shown for completeness; it is not interpretable as a claim outcome because the gates require at least 8 positive seeds and only 5 exist.

### 5.1 Development experiments run

| Experiment | Runs (seeds 1 to 5) | Arms per run | Mean seconds per run (current run) | Purpose |
|---|---|---|---|---|
| `baseline-fairness` | 5 | 10 | 78 | Baseline-fairness grids for local epochs, fine-tuning epochs and FedProx strength (Stage D). No confirmatory role. |
| `controlled-exposure` | 5 | 16 | 91 | Primary experiment. Hides a target family from one client (hide-from-target), compares local, centralized and four federated arms, blend, with peer-present, family-absent-everywhere and full-exposure conditions. |
| `peer-dose-response` | 5 | 24 | 101 | Varies requested peer exposure of the hidden family (0, 1, 10, 50, 100, 500, 1000, all) with target exposure at zero. |
| `natural-scarcity` | 5 | 5 | 46 | Uses naturally scarce families (target share at most 5%) instead of constructed hiding; validates the controlled design. |
| `family-permutation-control` | 5 | 5 | 46 | Negative control: family labels permuted so a peer-family-present arm carries no genuine family information. |

### 5.2 Development effect estimates (FedAvg, alpha 0.05)

| Experiment | Estimand | Federation-wide (mean, 95% CI, positive seeds of 5) | Own-domain |
|---|---|---|---|
| `controlled-exposure` | total-gain | +0.172 [+0.102, +0.221] pos 5/5 | +0.175 [+0.115, +0.231] pos 5/5 |
| `controlled-exposure` | pooling-gain | +0.016 [-0.107, +0.066] pos 4/5 | -0.005 [-0.046, +0.022] pos 2/5 |
| `controlled-exposure` | ctk-gain | +0.157 [+0.120, +0.188] pos 5/5 | +0.180 [+0.103, +0.228] pos 5/5 |
| `natural-scarcity` | total-gain | +0.207 [+0.170, +0.237] pos 5/5 | +0.101 [+0.081, +0.120] pos 5/5 |
| `natural-scarcity` | pooling-gain | +0.067 [+0.026, +0.115] pos 4/5 | -0.031 [-0.073, +0.011] pos 2/5 |
| `natural-scarcity` | ctk-gain | +0.141 [+0.115, +0.163] pos 5/5 | +0.132 [+0.089, +0.185] pos 5/5 |
| `family-permutation-control` | total-gain | +0.083 [+0.056, +0.129] pos 5/5 | -0.071 [-0.095, -0.054] pos 0/5 |
| `family-permutation-control` | pooling-gain | +0.091 [+0.069, +0.146] pos 5/5 | -0.068 [-0.091, -0.047] pos 0/5 |
| `family-permutation-control` | ctk-gain | -0.008 [-0.017, +0.002] pos 2/5 | -0.003 [-0.013, +0.004] pos 1/5 |
| `controlled-exposure` | local-deficit (central vs full exposure) | +0.199 [+0.124, +0.242] pos 5/5 | +0.231 [+0.136, +0.335] pos 5/5 |

### 5.3 Development claim-gate table (not interpretable)

| Claim | Development status | Scopes passed / total |
|---|---|---|
| local-deficit | insufficient-evidence | 0/2 |
| collaboration-benefit | promoted | 2/2 |
| complementary-knowledge | insufficient-evidence | 0/3 |
| generic-pooling-majority | rejected | 0/2 |
| dose-response | narrowed | 2/3 |
| own-domain-benefit | promoted | 1/1 |
| worst-client-benefit | promoted | 1/1 |
| known-family-safety | rejected | 1/2 |
| family-dependence | promoted | 1/1 |
| representation-limited-family | rejected | 0/3 |
| feature-novelty-explanation | insufficient-evidence | 0/2 |
| new-mechanism-trigger | rejected | 0/2 |

With 5 development seeds the 8-positive-seed requirement cannot be met, which is why several development gates read `insufficient-evidence` or `rejected` (for example known-family-safety and representation-limited-family). Development effect sizes were broadly in line with the later confirmatory ones (FedAvg CTK gain +0.157 development against +0.117 confirmatory; permutation control -0.008 against -0.001), but they are not evidence.

### 5.4 Development runtime history

Development runs finished between 16:11 and 19:04 on 2026-09-24 (logged `run-finished` events), with repeated re-execution after design and logging changes; the 25 current development runs took 0.50 h of run time in total.

## 6. Fairness and Hyperparameter Audit (development only)

Stage D selected three hyperparameters on development seeds 1 to 5 by the highest mean own-domain calibration-partition AUROC (test rows never used; ties to the smaller value). Each grid value was trained as a local (or FedProx / fine-tuned) arm under the primary MLP.

| Parameter | Grid value | Mean calibration AUROC | Dev seeds | Selection | Position of selected value |
|---|---|---|---|---|---|
| fedprox-strength | 0.001 | 0.9236 | 5 |  |  |
| fedprox-strength | 0.01 | 0.9309 | 5 |  |  |
| fedprox-strength | 0.1 | 0.9312 | 5 | **selected** | grid edge |
| finetune-epochs | 2 | 0.9193 | 5 | **selected** | grid edge |
| finetune-epochs | 5 | 0.9159 | 5 |  |  |
| finetune-epochs | 10 | 0.9153 | 5 |  |  |
| local-epochs | 10 | 0.9286 | 5 | **selected** | grid edge |
| local-epochs | 20 | 0.9211 | 5 |  |  |
| local-epochs | 40 | 0.9184 | 5 |  |  |

| Grid | Selected | Gap to next-best | Reading |
|---|---|---|---|
| local-epochs | 10 | 0.0075 | Selected value is the smallest tested; AUROC falls monotonically with more epochs, so longer local training over-fits rather than under-fits. No sign of under-training. |
| finetune-epochs | 2 | 0.0034 | Selected value is the smallest tested; more fine-tuning slightly lowers calibration AUROC. No sign of under-training. |
| fedprox-strength | 0.1 | 0.0003 | Selected value is the largest tested and the gap to 0.01 is tiny (0.0003), so the FedProx setting is effectively flat between 0.01 and 0.1 and worse at 0.001. |

**Which model families and arms were tuned.** Explicitly tuned: local epochs (MLP), fine-tuning epochs (MLP), FedProx strength (MLP). Fixed, not searched: centralized epochs (20), FedAvg rounds (20) and FedAvg local epochs (2), blend weight (0.5), MLP width and dropout, linear model settings, gradient-boosted-tree settings (100 iterations, depth 6, learning rate 0.1). The Roadmap's fairness requirement (Section 16.3) asks for grids for local training duration, fine-tuning duration and FedProx strength; that requirement is met. Centralized and FedAvg budgets were not tuned, which the protocol amendment records as a known limitation.

**Is any remaining issue a true scientific concern?** Two are worth stating. (1) The three selections are grid-edge selections; the grids were not extended (an optional refinement, not a protocol violation). (2) Local epochs are 10 while the centralized model trains for 20 epochs and FedAvg for 20 rounds of 2 local epochs; the local arm, on which every gain is measured, is therefore the least-trained arm in epoch count, although its own selection curve shows that more local epochs reduced calibration AUROC. This does not look like an under-trained baseline, but a reader can reasonably ask for the corresponding centralized-epoch curve. The grids are not reopened here.

## 7. Confirmatory Main Results

Primary experiment `controlled-exposure`: 10 confirmatory seeds (100 to 109), 7 hidden (client, family) pairs per seed, 16 arms, MLP, 6,000 training rows per client, alpha 0.05 unless stated. **All numbers in this and later sections are confirmatory unless labelled otherwise.** Level tables give the mean across the 10 seeds with the across-seed standard deviation; the pipeline computes no interval for a level, only for paired differences.

### 7.1 Detection levels, controlled exposure (federation-wide unseen-family recall, alpha 0.05)

| Learner | Peer family present | Family absent everywhere | Full exposure |
|---|---|---|---|
| local | 0.507 (sd 0.060) | (not defined) | (not defined) |
| central | 0.659 (sd 0.085) | 0.528 (sd 0.070) | 0.708 (sd 0.080) |
| fedavg | 0.638 (sd 0.084) | 0.521 (sd 0.073) | 0.682 (sd 0.084) |
| fedprox | 0.646 (sd 0.095) | 0.511 (sd 0.089) | 0.685 (sd 0.091) |
| fedavg-finetune | 0.614 (sd 0.054) | 0.537 (sd 0.055) | 0.668 (sd 0.063) |
| blend | 0.634 (sd 0.084) | 0.559 (sd 0.064) | 0.654 (sd 0.093) |

The `local` arm is trained only on its own client's data and does not depend on peer exposure, so it is defined once (under `peer-present`).

### 7.2 All headline detection metrics (alpha 0.05, mean across 10 seeds, peer-family-present condition)

| Metric | local | central | fedavg | fedprox | fedavg-finetune | blend |
|---|---|---|---|---|---|---|
| Federation-wide unseen-family recall | 0.507 | 0.659 | 0.638 | 0.646 | 0.614 | 0.634 |
| Own-domain unseen-family recall | 0.499 | 0.555 | 0.537 | 0.558 | 0.505 | 0.571 |
| Family-macro unseen-family recall | 0.454 | 0.569 | 0.558 | 0.551 | 0.543 | 0.548 |
| Micro unseen-family recall | 0.567 | 0.718 | 0.670 | 0.686 | 0.657 | 0.684 |
| Worst-client unseen-family recall | 0.279 | 0.411 | 0.425 | 0.380 | 0.407 | 0.373 |
| Known-family recall | 0.729 | 0.729 | 0.696 | 0.722 | 0.691 | 0.746 |
| Worst-client FNR (unseen) | 0.721 | 0.589 | 0.575 | 0.620 | 0.593 | 0.627 |
| Realised FPR (mean client) | 0.050 | 0.051 | 0.051 | 0.051 | 0.050 | 0.051 |
| Worst-client FPR | 0.062 | 0.064 | 0.066 | 0.065 | 0.064 | 0.067 |
| AUROC (own test) | 0.927 | 0.927 | 0.915 | 0.927 | 0.918 | 0.932 |
| AUPRC (own test) | 0.872 | 0.876 | 0.852 | 0.869 | 0.868 | 0.880 |
| Client recall dispersion | 0.176 | 0.197 | 0.170 | 0.192 | 0.162 | 0.192 |
| Family recall dispersion | 0.226 | 0.271 | 0.241 | 0.270 | 0.231 | 0.264 |
| FPR dispersion | 0.009 | 0.009 | 0.010 | 0.010 | 0.010 | 0.010 |

### 7.3 The same metrics under the two reference conditions (mean across seeds)

**Condition `family-absent-everywhere`**

| Metric | central | fedavg | fedprox | fedavg-finetune | blend |
|---|---|---|---|---|---|
| Federation-wide unseen-family recall | 0.528 | 0.521 | 0.511 | 0.537 | 0.559 |
| Own-domain unseen-family recall | 0.436 | 0.430 | 0.436 | 0.444 | 0.506 |
| Family-macro unseen-family recall | 0.438 | 0.434 | 0.427 | 0.459 | 0.470 |
| Micro unseen-family recall | 0.633 | 0.605 | 0.593 | 0.625 | 0.638 |
| Worst-client unseen-family recall | 0.225 | 0.252 | 0.210 | 0.273 | 0.293 |
| Known-family recall | 0.709 | 0.687 | 0.700 | 0.685 | 0.742 |
| Worst-client FNR (unseen) | 0.775 | 0.748 | 0.790 | 0.727 | 0.707 |
| Realised FPR (mean client) | 0.051 | 0.051 | 0.051 | 0.050 | 0.051 |
| Worst-client FPR | 0.065 | 0.064 | 0.065 | 0.063 | 0.065 |
| AUROC (own test) | 0.913 | 0.900 | 0.916 | 0.905 | 0.930 |
| AUPRC (own test) | 0.856 | 0.839 | 0.854 | 0.851 | 0.877 |
| Client recall dispersion | 0.235 | 0.211 | 0.223 | 0.202 | 0.208 |
| Family recall dispersion | 0.272 | 0.251 | 0.267 | 0.250 | 0.264 |
| FPR dispersion | 0.009 | 0.009 | 0.009 | 0.009 | 0.010 |

**Condition `full-exposure`**

| Metric | central | fedavg | fedprox | fedavg-finetune | blend |
|---|---|---|---|---|---|
| Federation-wide unseen-family recall | 0.708 | 0.682 | 0.685 | 0.668 | 0.654 |
| Own-domain unseen-family recall | 0.663 | 0.619 | 0.653 | 0.620 | 0.636 |
| Family-macro unseen-family recall | 0.605 | 0.599 | 0.586 | 0.592 | 0.573 |
| Micro unseen-family recall | 0.745 | 0.695 | 0.724 | 0.694 | 0.697 |
| Worst-client unseen-family recall | 0.454 | 0.462 | 0.414 | 0.474 | 0.392 |
| Known-family recall | 0.728 | 0.692 | 0.723 | 0.682 | 0.745 |
| Worst-client FNR (unseen) | 0.546 | 0.538 | 0.586 | 0.526 | 0.608 |
| Realised FPR (mean client) | 0.051 | 0.050 | 0.051 | 0.050 | 0.051 |
| Worst-client FPR | 0.064 | 0.065 | 0.065 | 0.062 | 0.066 |
| AUROC (own test) | 0.928 | 0.918 | 0.928 | 0.920 | 0.934 |
| AUPRC (own test) | 0.880 | 0.856 | 0.873 | 0.873 | 0.883 |
| Client recall dispersion | 0.187 | 0.173 | 0.190 | 0.159 | 0.193 |
| Family recall dispersion | 0.265 | 0.236 | 0.266 | 0.228 | 0.259 |
| FPR dispersion | 0.009 | 0.010 | 0.010 | 0.009 | 0.010 |

Dispersion metrics are the standard deviation of recall (or FPR) across clients or families within a seed, averaged over seeds; lower means more even behaviour.

## 8. Collaboration Decomposition

Definitions (Roadmap section 19): total gain = R(peer-family-present) - R(local); generic pooling gain = R(family-absent-everywhere) - R(local); CTK gain = R(peer-family-present) - R(family-absent-everywhere); complementary share = CTK / total (reported only when total is resolved: the pipeline requires a mean total gain of at least 0.02); oracle-gap recovery = (R(arm) - R(local)) / (R(central full exposure) - R(local)). Paired seed differences with 95% BCa intervals; alpha 0.05; controlled-exposure.

### 8.1 FedAvg

| Population | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Generic pooling gain | CTK gain |
|---|---|---|---|---|---|---|---|
| Federation-wide | 0.507 | 0.521 | 0.638 | 0.682 | +0.132 [+0.090, +0.167] pos 10/10 | +0.014 [-0.038, +0.054] pos 7/10 | +0.117 [+0.090, +0.145] pos 10/10 |
| Own-domain | 0.499 | 0.430 | 0.537 | 0.619 | +0.038 [+0.015, +0.062] pos 8/10 | -0.069 [-0.108, -0.040] pos 1/10 | +0.107 [+0.068, +0.144] pos 10/10 |
| Worst client | 0.279 | 0.252 | 0.425 | 0.462 | +0.146 [+0.080, +0.240] pos 10/10 | -0.026 [-0.080, +0.013] pos 3/10 | +0.173 [+0.116, +0.242] pos 10/10 |
| Family-macro | 0.454 | 0.434 | 0.558 | 0.599 | +0.104 [+0.066, +0.139] pos 10/10 | -0.020 [-0.062, +0.017] pos 5/10 | +0.124 [+0.102, +0.153] pos 10/10 |

| Population | Complementary share (ratio of means, CI) | Pooling share | Oracle-gap recovery | Local deficit vs full exposure |
|---|---|---|---|---|
| Federation-wide | +0.890 [+0.646, +1.389] | +0.110 [-0.389, +0.354] | +0.625 [+0.476, +0.770] pos 10/10 | not computed (centralized only) |
| Own-domain | +2.829 [+1.878, +6.706] | -1.829 [-5.706, -0.878] | +0.230 [+0.069, +0.392] pos 8/10 | not computed (centralized only) |
| Worst client | +1.181 [+0.910, +1.810] | -0.181 [-0.810, +0.090] | +0.748 [+0.425, +1.028] pos 9/10 | not computed (centralized only) |
| Family-macro | +1.194 [+0.865, +1.894] | -0.194 [-0.894, +0.135] | +0.673 [+0.521, +0.898] pos 10/10 | not computed (centralized only) |

### 8.2 Centralized

| Population | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Generic pooling gain | CTK gain |
|---|---|---|---|---|---|---|---|
| Federation-wide | 0.507 | 0.528 | 0.659 | 0.708 | +0.152 [+0.101, +0.195] pos 10/10 | +0.022 [-0.034, +0.067] pos 7/10 | +0.131 [+0.086, +0.181] pos 10/10 |
| Own-domain | 0.499 | 0.436 | 0.555 | 0.663 | +0.056 [+0.018, +0.098] pos 8/10 | -0.063 [-0.100, -0.021] pos 1/10 | +0.118 [+0.068, +0.181] pos 9/10 |
| Worst client | 0.279 | 0.225 | 0.411 | 0.454 | +0.133 [+0.034, +0.234] pos 9/10 | -0.054 [-0.137, +0.010] pos 1/10 | +0.187 [+0.137, +0.277] pos 10/10 |
| Family-macro | 0.454 | 0.438 | 0.569 | 0.605 | +0.115 [+0.071, +0.158] pos 10/10 | -0.016 [-0.074, +0.037] pos 5/10 | +0.131 [+0.095, +0.173] pos 10/10 |

| Population | Complementary share (ratio of means, CI) | Pooling share | Oracle-gap recovery | Local deficit vs full exposure |
|---|---|---|---|---|
| Federation-wide | +0.858 [+0.600, +1.280] | +0.142 [-0.280, +0.400] | +0.706 [+0.484, +0.867] pos 10/10 | +0.201 [+0.164, +0.231] pos 10/10 |
| Own-domain | +2.127 [+1.127, +3.722] | -1.127 [-2.722, -0.127] | +0.371 [+0.129, +0.667] pos 8/10 | +0.164 [+0.122, +0.233] pos 10/10 |
| Worst client | +1.406 [+0.904, +4.145] | -0.406 [-3.145, +0.096] | +1.153 [+0.801, +1.712] pos 10/10 | +0.175 [+0.078, +0.302] pos 9/10 |
| Family-macro | +1.138 [+0.733, +1.897] | -0.138 [-0.897, +0.267] | +0.757 [+0.506, +0.979] pos 10/10 | +0.150 [+0.111, +0.214] pos 10/10 |

Share rows show a ratio of seed means and its ratio-of-means bootstrap interval (positive-seed counts are not defined for ratios). Shares above 1 occur when the generic pooling component is negative (own-domain), which the roadmap flags as a case where the ratio should be read with the components, not on its own.

### 8.3 Other collaborative arms (federation-wide, alpha 0.05; descriptive levels, mean across seeds)

| Arm | Pooling gain | CTK gain | Total gain | Full exposure minus peer-present | Oracle-gap recovery (peer-present) |
|---|---|---|---|---|---|
| central | +0.022 | +0.131 | +0.152 | +0.049 | 0.76 |
| fedavg | +0.014 | +0.117 | +0.132 | +0.043 | 0.65 |
| fedprox | +0.004 | +0.135 | +0.139 | +0.039 | 0.69 |
| fedavg-finetune | +0.030 | +0.077 | +0.107 | +0.055 | 0.53 |
| blend | +0.053 | +0.075 | +0.127 | +0.020 | 0.63 |

FedProx, fine-tuning and blend appear only in `controlled-exposure` and `replication-family-set`; the pipeline computes paired intervals for centralized and FedAvg only, so the rows above are mean differences without intervals. Oracle-gap recovery here divides by the centralized full-exposure gap for every arm.

## 9. Own-Domain Results

The own-domain population is the hidden-family malware from the target client's own market or era (Roadmap 14.1). It exists only for the clients that hold a hidden family in a given seed, so it rests on fewer rows and clients than the federation-wide population.

| Estimand (FedAvg, alpha 0.05) | Federation-wide | Own-domain |
|---|---|---|
| total-gain | +0.132 [+0.090, +0.167] pos 10/10 | +0.038 [+0.015, +0.062] pos 8/10 |
| pooling-gain | +0.014 [-0.038, +0.054] pos 7/10 | -0.069 [-0.108, -0.040] pos 1/10 |
| ctk-gain | +0.117 [+0.090, +0.145] pos 10/10 | +0.107 [+0.068, +0.144] pos 10/10 |

Own-domain reading: the complementary gain survives on the own-domain population (+0.107, 10 of 10 seeds), but the generic pooling gain is **negative** on it (-0.069, 1 of 10 seeds positive): adding other clients' data while withholding the family from everyone leaves a client worse at detecting its own locally hidden family than local training alone. The total own-domain gain is therefore small (+0.038) even though the complementary component is large. This pattern repeats in centralized (-0.063), in most sensitivities (the own-domain pooling gain is negative in 9 of 12 experiment/salt scopes and positive for the linear model, the replication set and lower training support; Section 24, A2) and at alpha 0.10 (-0.066); at alpha 0.01 it is also negative (-0.048).

Own-domain support by client (hidden-family test rows, controlled-exposure): `anzhi`: 8/10 seeds, 19144 rows; `appchina`: 10/10 seeds, 9959 rows; `play-early`: 10/10 seeds, 13216 rows; `play-late`: 6/10 seeds, 642 rows. The own-domain metric is therefore dominated by the clients and seeds that hold a hidden family with enough test support (Roadmap 12.2); it is reported "where support permits".

## 10. Worst-Client Results

| Estimand (alpha 0.05) | FedAvg worst client | Centralized worst client |
|---|---|---|
| total-gain | +0.146 [+0.080, +0.240] pos 10/10 | +0.133 [+0.034, +0.234] pos 9/10 |
| pooling-gain | -0.026 [-0.080, +0.013] pos 3/10 | -0.054 [-0.137, +0.010] pos 1/10 |
| ctk-gain | +0.173 [+0.116, +0.242] pos 10/10 | +0.187 [+0.137, +0.277] pos 10/10 |
| oracle-gap-recovery | +0.748 [+0.425, +1.028] pos 9/10 | +1.153 [+0.801, +1.712] pos 10/10 |

The worst client is the client with the lowest unseen-family recall in each seed, so worst-client differences compare potentially different clients across arms. FedAvg worst-client CTK gain is +0.173 (10 of 10 seeds) against a worst-client pooling gain of -0.026 (3 of 10 seeds positive): the worst-off client gains from peer-held family knowledge and not from generic pooling, which is Roadmap hypothesis H6 exactly as stated. Worst-client oracle-gap recovery for centralized is 1.15 (CI 0.80 to 1.71): with the family present, the worst client recovers more than the full-exposure oracle gap on average; this ratio has a wide interval and should not be read as "beats the oracle".

Worst-client recall levels (peer-family present, mean across seeds): local: 0.279, central: 0.411, fedavg: 0.425, fedprox: 0.380, fedavg-finetune: 0.407, blend: 0.373; full exposure (centralized) 0.454; family absent everywhere (FedAvg) 0.252.

## 11. Natural-Scarcity Results

Natural scarcity uses families whose target-client share is at most 5% (config `natural_scarcity.max_target_share`), with at least 150 peer fit rows and 15 own-domain test rows, instead of constructed hiding. Across the 10 seeds the plan holds 99 (client, family) target pairs over 7 distinct families (between 8 and 11 pairs per seed); the number of pairs varies by seed because eligibility is recomputed for each partition.

### 11.1 Natural scarcity versus controlled exposure (FedAvg, alpha 0.05)

| Estimand | Population | Natural scarcity | Controlled exposure |
|---|---|---|---|
| total-gain | Federation-wide | +0.213 [+0.176, +0.242] pos 10/10 | +0.132 [+0.090, +0.167] pos 10/10 |
| total-gain | Own-domain | +0.059 [+0.015, +0.092] pos 8/10 | +0.038 [+0.015, +0.062] pos 8/10 |
| total-gain | Worst client | +0.227 [+0.173, +0.273] pos 10/10 | +0.146 [+0.080, +0.240] pos 10/10 |
| pooling-gain | Federation-wide | +0.100 [+0.072, +0.131] pos 10/10 | +0.014 [-0.038, +0.054] pos 7/10 |
| pooling-gain | Own-domain | -0.051 [-0.078, -0.020] pos 2/10 | -0.069 [-0.108, -0.040] pos 1/10 |
| pooling-gain | Worst client | +0.087 [+0.055, +0.114] pos 9/10 | -0.026 [-0.080, +0.013] pos 3/10 |
| ctk-gain | Federation-wide | +0.113 [+0.094, +0.128] pos 10/10 | +0.117 [+0.090, +0.145] pos 10/10 |
| ctk-gain | Own-domain | +0.110 [+0.076, +0.139] pos 10/10 | +0.107 [+0.068, +0.144] pos 10/10 |
| ctk-gain | Worst client | +0.140 [+0.084, +0.180] pos 9/10 | +0.173 [+0.116, +0.242] pos 10/10 |

### 11.2 Natural scarcity, centralized

| Estimand | Population | Natural scarcity (centralized) |
|---|---|---|
| total-gain | Federation-wide | +0.248 [+0.213, +0.281] pos 10/10 |
| total-gain | Own-domain | +0.110 [+0.062, +0.155] pos 9/10 |
| total-gain | Worst client | +0.195 [+0.160, +0.229] pos 10/10 |
| pooling-gain | Federation-wide | +0.129 [+0.096, +0.171] pos 10/10 |
| pooling-gain | Own-domain | +0.006 [-0.037, +0.059] pos 5/10 |
| pooling-gain | Worst client | +0.018 [-0.040, +0.064] pos 7/10 |
| ctk-gain | Federation-wide | +0.119 [+0.105, +0.135] pos 10/10 |
| ctk-gain | Own-domain | +0.105 [+0.073, +0.135] pos 10/10 |
| ctk-gain | Worst client | +0.176 [+0.145, +0.214] pos 10/10 |

### 11.3 Levels (mean across seeds, alpha 0.05, federation-wide)

| Arm / condition | Natural scarcity | Controlled exposure |
|---|---|---|
| local / peer-present | 0.552 (sd 0.068) | 0.507 (sd 0.060) |
| fedavg / family-absent-everywhere | 0.653 (sd 0.051) | 0.521 (sd 0.073) |
| fedavg / peer-present | 0.766 (sd 0.032) | 0.638 (sd 0.084) |
| central / family-absent-everywhere | 0.681 (sd 0.046) | 0.528 (sd 0.070) |
| central / peer-present | 0.801 (sd 0.028) | 0.659 (sd 0.085) |

Direction agreement: the FedAvg complementary gain is positive in natural scarcity (+0.113, 10 of 10 seeds) as in controlled exposure (+0.117), on the federation-wide, own-domain and worst-client populations alike, and the two estimates are almost identical in size. The natural-scarcity federation-wide pooling gain (+0.100) is much larger than in controlled exposure (+0.014); the two designs therefore agree on the CTK component but not on the size of the generic component. The protocol does not pool natural and controlled estimates and this document does not either. No claim gate consumes natural scarcity.

Natural-scarcity development result (development-only, 5 seeds): FedAvg CTK gain +0.141 federation-wide and +0.132 own-domain (Section 5.2).

## 12. Dose-Response Results

Requested peer exposure is applied to the hidden family with the target client at zero exposure. Effective dose is the number of peer training rows of that family actually present in the peer clients' training sets. Rows below are means over the 70 (seed, family) units per level (10 seeds x 7 families); "gain over zero dose" is the recall difference to the zero-dose model of the same seed and family. The pipeline computes no confidence interval for the dose curve; the seed standard deviation and positive-seed counts are shown instead.

### 12.1 FedAvg

| Requested dose (peer family rows) | Mean effective dose | Median effective dose | Mean recall | Gain over zero dose | Seed sd of gain | Seeds with positive gain |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0 | 0.437 | +0.000 | 0 | - |
| 1 | 0.1 | 0 | 0.433 | -0.004 | 0.012 | 5/10 |
| 10 | 0.9 | 1 | 0.441 | +0.003 | 0.010 | 8/10 |
| 50 | 4.5 | 4 | 0.448 | +0.011 | 0.015 | 9/10 |
| 100 | 9.0 | 9 | 0.457 | +0.020 | 0.022 | 9/10 |
| 500 | 43.1 | 50 | 0.505 | +0.068 | 0.033 | 10/10 |
| 1000 | 79.4 | 74 | 0.527 | +0.090 | 0.040 | 10/10 |
| all available | 296.2 | 106 | 0.562 | +0.124 | 0.047 | 10/10 |

### 12.2 Centralized

| Requested dose (peer family rows) | Mean effective dose | Median effective dose | Mean recall | Gain over zero dose | Seed sd of gain | Seeds with positive gain |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0 | 0.447 | +0.000 | 0 | - |
| 1 | 0.1 | 0 | 0.451 | +0.005 | 0.028 | 6/10 |
| 10 | 0.9 | 1 | 0.447 | +0.001 | 0.024 | 4/10 |
| 50 | 4.5 | 4 | 0.454 | +0.007 | 0.044 | 7/10 |
| 100 | 9.0 | 9 | 0.453 | +0.006 | 0.040 | 6/10 |
| 500 | 43.1 | 50 | 0.515 | +0.068 | 0.070 | 9/10 |
| 1000 | 79.4 | 74 | 0.523 | +0.077 | 0.058 | 9/10 |
| all available | 296.2 | 106 | 0.556 | +0.110 | 0.070 | 10/10 |

### 12.3 FedAvg + fine-tuning

| Requested dose (peer family rows) | Mean effective dose | Median effective dose | Mean recall | Gain over zero dose | Seed sd of gain | Seeds with positive gain |
|---|---|---|---|---|---|---|
| 0 | 0.0 | 0 | 0.460 | +0.000 | 0 | - |
| 1 | 0.1 | 0 | 0.460 | +0.000 | 0.009 | 6/10 |
| 10 | 0.9 | 1 | 0.463 | +0.003 | 0.009 | 7/10 |
| 50 | 4.5 | 4 | 0.473 | +0.013 | 0.017 | 7/10 |
| 100 | 9.0 | 9 | 0.480 | +0.020 | 0.027 | 8/10 |
| 500 | 43.1 | 50 | 0.506 | +0.045 | 0.021 | 10/10 |
| 1000 | 79.4 | 74 | 0.524 | +0.064 | 0.026 | 10/10 |
| all available | 296.2 | 106 | 0.550 | +0.090 | 0.029 | 10/10 |

## 13. Family-Level Results

Per-family values are means over the seeds in which the family was eligible (`seeds`), pooled hits over pooled trials at the federation-wide population, alpha 0.05. `Support` is the mean number of federation-wide hidden-family test rows per seed. `Rescue status` is the pipeline's classification (poorly rescued = full-exposure recall below 0.60 in the primary model). Novelty is the training-only primary descriptor (nearest-known-family distance).

### 13.1 Primary family set (`controlled-exposure`), FedAvg

| Family | Seeds | Support | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Pooling gain | CTK gain | Novelty | Rescue status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| revmob | 10 | 609 | 0.260 | 0.183 | 0.525 | 0.557 | +0.266 | -0.077 | +0.343 | 3.32 | poorly-rescued-under-full-exposure |
| leadbolt | 10 | 818 | 0.304 | 0.309 | 0.585 | 0.645 | +0.281 | +0.005 | +0.277 | 2.71 | rescued |
| adwo | 10 | 920 | 0.671 | 0.564 | 0.665 | 0.696 | -0.006 | -0.107 | +0.101 | 2.06 | rescued |
| airpush | 10 | 2419 | 0.669 | 0.699 | 0.783 | 0.855 | +0.115 | +0.030 | +0.084 | 2.55 | rescued |
| hiddad | 10 | 404 | 0.298 | 0.236 | 0.265 | 0.319 | -0.032 | -0.062 | +0.029 | 4.19 | poorly-rescued-under-full-exposure |
| gappusin | 10 | 1501 | 0.321 | 0.281 | 0.310 | 0.359 | -0.011 | -0.040 | +0.029 | 1.59 | poorly-rescued-under-full-exposure |
| dowgin | 10 | 5911 | 0.658 | 0.768 | 0.771 | 0.762 | +0.113 | +0.110 | +0.003 | 1.89 | rescued |

### 13.2 Primary family set (`controlled-exposure`), centralized

| Family | Seeds | Support | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Pooling gain | CTK gain | Novelty | Rescue status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| revmob | 10 | 609 | 0.260 | 0.246 | 0.560 | 0.539 | +0.301 | -0.014 | +0.315 | 3.32 | poorly-rescued-under-full-exposure |
| leadbolt | 10 | 818 | 0.304 | 0.290 | 0.594 | 0.648 | +0.290 | -0.014 | +0.304 | 2.71 | rescued |
| airpush | 10 | 2419 | 0.669 | 0.665 | 0.773 | 0.859 | +0.104 | -0.003 | +0.108 | 2.55 | rescued |
| gappusin | 10 | 1501 | 0.321 | 0.315 | 0.402 | 0.453 | +0.081 | -0.006 | +0.087 | 1.59 | poorly-rescued-under-full-exposure |
| adwo | 10 | 920 | 0.671 | 0.505 | 0.565 | 0.585 | -0.106 | -0.166 | +0.060 | 2.06 | poorly-rescued-under-full-exposure |
| dowgin | 10 | 5911 | 0.658 | 0.837 | 0.866 | 0.864 | +0.208 | +0.179 | +0.029 | 1.89 | rescued |
| hiddad | 10 | 404 | 0.298 | 0.210 | 0.225 | 0.283 | -0.073 | -0.087 | +0.014 | 4.19 | poorly-rescued-under-full-exposure |

### 13.3 Replication family set, FedAvg

| Family | Seeds | Support | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Pooling gain | CTK gain | Novelty | Rescue status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inmobi | 10 | 582 | 0.498 | 0.706 | 0.872 | 0.896 | +0.374 | +0.208 | +0.166 | 5.43 | rescued |
| domob | 10 | 399 | 0.551 | 0.437 | 0.565 | 0.586 | +0.014 | -0.114 | +0.128 | 1.95 | poorly-rescued-under-full-exposure |
| utchi | 6 | 519 | 0.008 | 0.017 | 0.133 | 0.221 | +0.125 | +0.009 | +0.116 | 3.10 | poorly-rescued-under-full-exposure |
| youmi | 10 | 667 | 0.346 | 0.293 | 0.352 | 0.354 | +0.006 | -0.053 | +0.059 | 1.54 | poorly-rescued-under-full-exposure |
| smsreg | 10 | 1275 | 0.562 | 0.611 | 0.660 | 0.683 | +0.098 | +0.049 | +0.049 | 2.85 | rescued |
| kuguo | 10 | 3631 | 0.580 | 0.560 | 0.587 | 0.608 | +0.007 | -0.020 | +0.027 | 1.70 | rescued |
| dnotua | 10 | 251 | 0.591 | 0.619 | 0.626 | 0.543 | +0.035 | +0.028 | +0.007 | 2.42 | poorly-rescued-under-full-exposure |
| zdtad | 6 | 524 | 0.776 | 0.713 | 0.694 | 0.674 | -0.082 | -0.063 | -0.019 | 2.01 | rescued |

### 13.4 Replication family set, centralized

| Family | Seeds | Support | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Pooling gain | CTK gain | Novelty | Rescue status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| utchi | 6 | 519 | 0.008 | 0.085 | 0.441 | 0.438 | +0.433 | +0.077 | +0.356 | 3.10 | poorly-rescued-under-full-exposure |
| inmobi | 10 | 582 | 0.498 | 0.581 | 0.817 | 0.831 | +0.320 | +0.083 | +0.236 | 5.43 | rescued |
| domob | 10 | 399 | 0.551 | 0.419 | 0.514 | 0.558 | -0.037 | -0.131 | +0.095 | 1.95 | poorly-rescued-under-full-exposure |
| kuguo | 10 | 3631 | 0.580 | 0.638 | 0.718 | 0.740 | +0.138 | +0.058 | +0.081 | 1.70 | rescued |
| smsreg | 10 | 1275 | 0.562 | 0.699 | 0.751 | 0.773 | +0.189 | +0.137 | +0.052 | 2.85 | rescued |
| youmi | 10 | 667 | 0.346 | 0.294 | 0.347 | 0.356 | +0.000 | -0.052 | +0.052 | 1.54 | poorly-rescued-under-full-exposure |
| zdtad | 6 | 524 | 0.776 | 0.866 | 0.881 | 0.865 | +0.105 | +0.090 | +0.015 | 2.01 | rescued |
| dnotua | 10 | 251 | 0.591 | 0.629 | 0.614 | 0.627 | +0.023 | +0.038 | -0.015 | 2.42 | rescued |

### 13.5 Natural scarcity, FedAvg

| Family | Seeds | Support | Local | No-family collab. | Peer-family collab. | Full exposure | Total gain | Pooling gain | CTK gain | Novelty | Rescue status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| revmob | 10 | 620 | 0.282 | 0.160 | 0.497 | n/a | +0.215 | -0.122 | +0.337 | 3.32 | rescued |
| leadbolt | 10 | 821 | 0.408 | 0.365 | 0.678 | n/a | +0.270 | -0.043 | +0.313 | 2.71 | rescued |
| airpush | 10 | 2419 | 0.565 | 0.669 | 0.819 | n/a | +0.253 | +0.104 | +0.150 | 2.55 | rescued |
| gappusin | 10 | 1501 | 0.520 | 0.695 | 0.794 | n/a | +0.274 | +0.174 | +0.099 | 1.59 | rescued |
| hiddad | 6 | 457 | 0.306 | 0.160 | 0.186 | n/a | -0.120 | -0.145 | +0.025 | 4.19 | rescued |
| adwo | 8 | 923 | 0.777 | 0.881 | 0.906 | n/a | +0.129 | +0.104 | +0.025 | 2.06 | rescued |
| dowgin | 10 | 5935 | 0.621 | 0.798 | 0.796 | n/a | +0.174 | +0.177 | -0.002 | 1.89 | rescued |

### 13.6 Representation-limited status across model families (centralized, full exposure, alpha 0.05)

| Family | MLP (primary) | Linear | Trees | Primary status | Representation-limited status |
|---|---|---|---|---|---|
| adwo | 0.585 | 0.667 | 0.761 | poor in primary | primary only |
| airpush | 0.859 | 0.692 | 0.799 | not poor in primary |  |
| dowgin | 0.864 | 0.823 | 0.919 | not poor in primary |  |
| gappusin | 0.453 | 0.411 | 0.584 | poor in primary | confirmed by an independent model |
| hiddad | 0.283 | 0.154 | 0.179 | poor in primary | confirmed by an independent model |
| leadbolt | 0.648 | 0.433 | 0.525 | not poor in primary |  |
| revmob | 0.539 | 0.399 | 0.495 | poor in primary | confirmed by an independent model |

Families that stay below 0.60 in the primary MLP and in at least one independent model family: gappusin, hiddad, revmob (3 of 4 poor in the primary model). Wording remains "under the tested static representation and models"; none of these families is claimed undetectable.

### 13.7 Hidden-family effective peer dose per family (from the dose experiment; mean effective peer rows at requested dose `all available`)

| Family | Mean effective peer rows | FedAvg gain over zero dose | Seeds present |
|---|---|---|---|
| revmob | 55 | +0.336 | 10 |
| leadbolt | 84 | +0.268 | 10 |
| adwo | 287 | +0.085 | 10 |
| airpush | 208 | +0.082 | 10 |
| hiddad | 32 | +0.070 | 10 |
| gappusin | 219 | +0.034 | 10 |
| dowgin | 1188 | -0.004 | 10 |

## 14. Client-Level Results

Pooled over the 10 confirmatory seeds of `controlled-exposure` (sum of hits over sum of trials), alpha 0.05, FedAvg. Own-domain populations exist only for a client's seeds in which it holds a hidden family.

| Client | Rows | Malware prevalence | Benign rows | Packages | Distinct families | Local own-domain recall | No-family (FedAvg) | Peer-family (FedAvg) | CTK gain | Full exposure (FedAvg) | Known-family recall local | Known-family recall FedAvg | Known-family change | Realised FPR local | Realised FPR FedAvg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anzhi | 104,287 | 87.1% | 13,486 | 72,451 | 310 | 0.776 | 0.686 | 0.691 | +0.005 | 0.700 | 0.701 | 0.632 | -0.069 | 0.053 | 0.057 |
| appchina | 88,282 | 83.3% | 14,704 | 50,013 | 413 | 0.393 | 0.340 | 0.370 | +0.030 | 0.433 | 0.719 | 0.705 | -0.014 | 0.047 | 0.049 |
| play-early | 319,122 | 23.8% | 243,137 | 290,817 | 433 | 0.652 | 0.624 | 0.710 | +0.086 | 0.840 | 0.753 | 0.738 | -0.015 | 0.047 | 0.045 |
| play-late | 320,474 | 5.4% | 303,274 | 257,743 | 281 | 0.307 | 0.192 | 0.407 | +0.215 | 0.827 | 0.745 | 0.709 | -0.036 | 0.050 | 0.050 |

Sample counts and prevalence come from `results/tables/dataset-client-audit.csv` (client rows before partitioning); the recall columns come from the run-level `metrics/clients.parquet` of the ten controlled-exposure runs. The FedAvg known-family recall drops most at `anzhi`; `appchina` and `play-early` are nearly unchanged. The `benign` population's recall is the realised FPR at the threshold calibrated per client on benign calibration rows.

Worst and best own-domain hidden family per client (FedAvg, peer family present, pooled over seeds, families with at least 15 pooled test rows):

| Client | Worst family | Recall | Best family | Recall | Families |
|---|---|---|---|---|---|
| anzhi | gappusin | 0.167 | hiddad | 0.821 | 5 |
| appchina | revmob | 0.172 | airpush | 0.991 | 7 |
| play-early | hiddad | 0.408 | adwo | 0.923 | 6 |
| play-late | hiddad | 0.194 | leadbolt | 0.851 | 4 |

## 15. Model-Family Replication

MLP (`controlled-exposure`), linear classifier and gradient-boosted trees (centralized arms only) under the same design. FedAvg exists for the MLP and linear model only.

| Model | Local | No-family | Peer-family | Full exposure | Total gain | Pooling gain | CTK gain | CTK share (mean/mean) | Known-family change vs local |
|---|---|---|---|---|---|---|---|---|---|
| MLP (primary), centralized | 0.507 | 0.528 | 0.659 | 0.708 | +0.152 [+0.101, +0.195] pos 10/10 | +0.022 [-0.034, +0.067] pos 7/10 | +0.131 [+0.086, +0.181] pos 10/10 | 0.86 | +0.000 |
| MLP (primary), FedAvg | 0.507 | 0.521 | 0.638 | 0.682 | +0.132 [+0.090, +0.167] pos 10/10 | +0.014 [-0.038, +0.054] pos 7/10 | +0.117 [+0.090, +0.145] pos 10/10 | 0.89 | -0.033 |
| Linear, centralized | 0.279 | 0.502 | 0.584 | 0.616 | +0.305 [+0.280, +0.346] pos 10/10 | +0.223 [+0.200, +0.252] pos 10/10 | +0.082 [+0.065, +0.103] pos 10/10 | 0.27 | +0.106 |
| Linear, FedAvg | 0.279 | 0.460 | 0.553 | 0.583 | +0.274 [+0.245, +0.306] pos 10/10 | +0.181 [+0.152, +0.214] pos 10/10 | +0.094 [+0.075, +0.110] pos 10/10 | 0.34 | +0.066 |
| Trees, centralized | 0.517 | 0.570 | 0.672 | 0.720 | +0.155 [+0.117, +0.230] pos 10/10 | +0.053 [+0.008, +0.094] pos 8/10 | +0.102 [+0.076, +0.137] pos 10/10 | 0.66 | -0.026 |

Own-domain and worst-client CTK gain by model:

| Model | Own-domain CTK gain | Worst-client CTK gain | Own-domain pooling gain | Worst-client pooling gain |
|---|---|---|---|---|
| MLP, centralized | +0.118 [+0.068, +0.181] pos 9/10 | +0.187 [+0.137, +0.277] pos 10/10 | -0.063 [-0.100, -0.021] pos 1/10 | -0.054 [-0.137, +0.010] pos 1/10 |
| MLP, FedAvg | +0.107 [+0.068, +0.144] pos 10/10 | +0.173 [+0.116, +0.242] pos 10/10 | -0.069 [-0.108, -0.040] pos 1/10 | -0.026 [-0.080, +0.013] pos 3/10 |
| Linear, centralized | +0.073 [+0.053, +0.087] pos 10/10 | +0.091 [+0.052, +0.141] pos 10/10 | +0.152 [+0.108, +0.210] pos 10/10 | +0.061 [+0.014, +0.177] pos 7/10 |
| Linear, FedAvg | +0.098 [+0.085, +0.119] pos 10/10 | +0.079 [+0.047, +0.129] pos 10/10 | +0.109 [+0.073, +0.149] pos 10/10 | +0.042 [-0.009, +0.139] pos 6/10 |
| Trees, centralized | +0.117 [+0.085, +0.185] pos 10/10 | +0.166 [+0.111, +0.288] pos 10/10 | -0.029 [-0.064, -0.006] pos 4/10 | -0.036 [-0.099, +0.031] pos 2/10 |

Operating-point quality (alpha 0.05; mean realised FPR and largest absolute gap over arms and seeds):

| Model | Mean realised FPR / max gap |
|---|---|
| MLP | 0.0507 / 0.0126 |
| Linear | 0.0512 / 0.0123 |
| Trees | 0.0515 / 0.0113 |

Reading: the complementary gain is positive in all three model families with intervals above zero and 10 of 10 positive seeds (linear FedAvg +0.094, trees centralized +0.102, MLP FedAvg +0.117), so it is not specific to the neural model. The composition differs: for the linear model the generic pooling component is large (+0.181 FedAvg, +0.223 centralized; pooling is about two thirds of the total), for the MLP it is near zero, and for trees it is small (+0.053). The claim that pooling is not the majority of the benefit is therefore established for the MLP only (Section 31); the linear model shows the opposite composition.

## 16. Family-Set Replication

Primary set (7 families, 7 pairs per seed) against the disjoint replication set (8 families; 6 to 8 eligible pairs per seed). Same design, MLP, alpha 0.05.

| Population | Estimand (FedAvg) | Primary set | Replication set |
|---|---|---|---|
| Federation-wide | total-gain | +0.132 [+0.090, +0.167] pos 10/10 | +0.081 [+0.042, +0.128] pos 8/10 |
| Federation-wide | pooling-gain | +0.014 [-0.038, +0.054] pos 7/10 | +0.017 [-0.020, +0.066] pos 6/10 |
| Federation-wide | ctk-gain | +0.117 [+0.090, +0.145] pos 10/10 | +0.064 [+0.038, +0.077] pos 9/10 |
| Own-domain | total-gain | +0.038 [+0.015, +0.062] pos 8/10 | +0.055 [+0.006, +0.130] pos 6/10 |
| Own-domain | pooling-gain | -0.069 [-0.108, -0.040] pos 1/10 | +0.014 [-0.035, +0.088] pos 7/10 |
| Own-domain | ctk-gain | +0.107 [+0.068, +0.144] pos 10/10 | +0.042 [+0.001, +0.091] pos 8/10 |
| Worst client | total-gain | +0.146 [+0.080, +0.240] pos 10/10 | +0.010 [-0.055, +0.068] pos 6/10 |
| Worst client | pooling-gain | -0.026 [-0.080, +0.013] pos 3/10 | -0.037 [-0.090, +0.020] pos 2/10 |
| Worst client | ctk-gain | +0.173 [+0.116, +0.242] pos 10/10 | +0.047 [+0.028, +0.067] pos 9/10 |
| Family-macro | total-gain | +0.104 [+0.066, +0.139] pos 10/10 | +0.082 [+0.034, +0.120] pos 8/10 |
| Family-macro | pooling-gain | -0.020 [-0.062, +0.017] pos 5/10 | +0.013 [-0.021, +0.043] pos 8/10 |
| Family-macro | ctk-gain | +0.124 [+0.102, +0.153] pos 10/10 | +0.069 [+0.045, +0.098] pos 9/10 |

| Learner | Primary: peer | Primary: no-family | Primary: full | Replication: peer | Replication: no-family | Replication: full |
|---|---|---|---|---|---|---|
| local | 0.507 | - | - | 0.576 | - | - |
| central | 0.659 | 0.528 | 0.708 | 0.710 | 0.623 | 0.729 |
| fedavg | 0.638 | 0.521 | 0.682 | 0.657 | 0.593 | 0.669 |
| fedprox | 0.646 | 0.511 | 0.685 | 0.711 | 0.663 | 0.721 |
| fedavg-finetune | 0.614 | 0.537 | 0.668 | 0.644 | 0.595 | 0.665 |
| blend | 0.634 | 0.559 | 0.654 | 0.674 | 0.632 | 0.686 |

Known-family change vs local (FedAvg): primary -0.033, replication -0.036; centralized primary +0.000, replication -0.008.

Family dependence: across-family spread of the FedAvg CTK gain (largest minus smallest family mean) is 0.339 in the primary set and 0.185 in the replication set. Individual families range from +0.003 to +0.343 (primary) and -0.019 to +0.166 (replication).

Reading: the central story replicates in direction, statistical support and rank (CTK gain positive with intervals above zero in every population, 9 of 10 seeds federation-wide) but at about half the magnitude on the federation-wide population (+0.064 against +0.117), with a weaker own-domain effect (+0.042, interval lower bound +0.001, 8 of 10 seeds) and a weak worst-client centralized effect (+0.054, interval crossing zero, 6 of 10 seeds). It is best described as **partial replication with a materially smaller effect size**; it depends on the family set in magnitude but not in sign. The generic pooling component is near zero on the replication set (+0.017), as in the primary set.

## 17. Support Sensitivity

Training support: `training-support-sensitivity` (1,500 rows per client instead of 6,000). Family support: `family-support-sensitivity-low` (peer fit at least 100, federation test at least 30) and `-high` (300, 100), each with its own eligibility-specific partitions. Alpha 0.05, MLP.

| Regime | Learner | Total gain (fed-wide) | Pooling gain (fed-wide) | CTK gain (fed-wide) | CTK gain (own-domain) | CTK gain (worst client) |
|---|---|---|---|---|---|---|
| Primary (6,000 rows, primary eligibility) | fedavg | +0.132 [+0.090, +0.167] pos 10/10 | +0.014 [-0.038, +0.054] pos 7/10 | +0.117 [+0.090, +0.145] pos 10/10 | +0.107 [+0.068, +0.144] pos 10/10 | +0.173 [+0.116, +0.242] pos 10/10 |
| Primary (6,000 rows, primary eligibility) | central | +0.152 [+0.101, +0.195] pos 10/10 | +0.022 [-0.034, +0.067] pos 7/10 | +0.131 [+0.086, +0.181] pos 10/10 | +0.118 [+0.068, +0.181] pos 9/10 | +0.187 [+0.137, +0.277] pos 10/10 |
| Lower training support (1,500 rows) | fedavg | +0.222 [+0.179, +0.265] pos 10/10 | +0.115 [+0.076, +0.161] pos 10/10 | +0.107 [+0.087, +0.128] pos 10/10 | +0.102 [+0.074, +0.153] pos 10/10 | +0.113 [+0.070, +0.151] pos 10/10 |
| Lower training support (1,500 rows) | central | +0.269 [+0.226, +0.315] pos 10/10 | +0.179 [+0.145, +0.215] pos 10/10 | +0.090 [+0.062, +0.118] pos 10/10 | +0.119 [+0.064, +0.178] pos 9/10 | +0.122 [+0.073, +0.192] pos 9/10 |
| Lower family support | fedavg | +0.149 [+0.085, +0.194] pos 9/10 | +0.006 [-0.059, +0.046] pos 6/10 | +0.143 [+0.116, +0.163] pos 10/10 | +0.149 [+0.098, +0.193] pos 10/10 | +0.187 [+0.109, +0.280] pos 9/10 |
| Lower family support | central | +0.151 [+0.083, +0.199] pos 9/10 | +0.013 [-0.058, +0.051] pos 7/10 | +0.138 [+0.111, +0.166] pos 10/10 | +0.171 [+0.117, +0.210] pos 10/10 | +0.169 [+0.104, +0.267] pos 9/10 |
| Higher family support | fedavg | +0.139 [+0.105, +0.168] pos 10/10 | +0.022 [-0.024, +0.054] pos 8/10 | +0.117 [+0.090, +0.141] pos 10/10 | +0.090 [+0.058, +0.135] pos 10/10 | +0.146 [+0.108, +0.193] pos 10/10 |
| Higher family support | central | +0.150 [+0.098, +0.199] pos 10/10 | +0.030 [-0.019, +0.073] pos 6/10 | +0.119 [+0.091, +0.156] pos 10/10 | +0.140 [+0.082, +0.195] pos 10/10 | +0.147 [+0.117, +0.172] pos 10/10 |

Every regime plans 7 hidden (client, family) pairs per seed.

Reading: the FedAvg CTK gain is stable to modestly stronger under every regime (+0.107 at low training support, +0.143 at low family support, +0.117 at high family support against +0.117 primary; all intervals above zero, at least 9 of 10 seeds on the federation-wide population). Lower training support does not weaken CTK; it raises the generic pooling gain (+0.115 FedAvg federation-wide, +0.179 centralized), consistent with less local data making pooling more valuable, so the CTK share falls to about half. CTK is not sensitive to family-support thresholds.

## 18. Operating-Point Sensitivity

Intended FPR targets 0.01, 0.05 (primary) and 0.10 for every arm; thresholds are calibrated per client on benign calibration rows and never on test rows. Roadmap 17: the 1% target is a tail-resolution sensitivity; where benign calibration support cannot resolve the 99th percentile the status is `insufficient-evidence`. Every stored operating status in the confirmatory arm metrics is `valid` (no arm was flagged insufficient at any alpha).

**FedAvg, federation-wide**

| Experiment | Estimand | alpha 0.01 | alpha 0.05 (primary) | alpha 0.10 |
|---|---|---|---|---|
| `controlled-exposure` | ctk-gain | +0.076 [+0.037, +0.125] pos 9/10 | +0.117 [+0.090, +0.145] pos 10/10 | +0.134 [+0.110, +0.164] pos 10/10 |
| `controlled-exposure` | pooling-gain | +0.035 [-0.023, +0.106] pos 5/10 | +0.014 [-0.038, +0.054] pos 7/10 | -0.000 [-0.043, +0.029] pos 7/10 |
| `controlled-exposure` | total-gain | +0.111 [+0.043, +0.171] pos 8/10 | +0.132 [+0.090, +0.167] pos 10/10 | +0.133 [+0.110, +0.167] pos 10/10 |
| `replication-family-set` | ctk-gain | +0.057 [+0.026, +0.077] pos 9/10 | +0.064 [+0.038, +0.077] pos 9/10 | +0.080 [+0.060, +0.101] pos 10/10 |
| `replication-family-set` | pooling-gain | -0.050 [-0.143, +0.019] pos 4/10 | +0.017 [-0.020, +0.066] pos 6/10 | +0.052 [+0.012, +0.096] pos 8/10 |
| `replication-family-set` | total-gain | +0.007 [-0.096, +0.082] pos 6/10 | +0.081 [+0.042, +0.128] pos 8/10 | +0.132 [+0.090, +0.187] pos 10/10 |
| `family-permutation-control` | ctk-gain | -0.008 [-0.025, +0.009] pos 3/10 | -0.001 [-0.007, +0.007] pos 4/10 | +0.003 [-0.008, +0.010] pos 7/10 |
| `family-permutation-control` | pooling-gain | +0.077 [+0.046, +0.121] pos 10/10 | +0.080 [+0.061, +0.101] pos 10/10 | +0.080 [+0.067, +0.100] pos 10/10 |
| `family-permutation-control` | total-gain | +0.069 [+0.030, +0.113] pos 8/10 | +0.079 [+0.057, +0.105] pos 10/10 | +0.083 [+0.065, +0.106] pos 10/10 |
| `natural-scarcity` | ctk-gain | +0.098 [+0.082, +0.128] pos 10/10 | +0.113 [+0.094, +0.128] pos 10/10 | +0.118 [+0.102, +0.133] pos 10/10 |
| `natural-scarcity` | pooling-gain | +0.130 [+0.082, +0.165] pos 9/10 | +0.100 [+0.072, +0.131] pos 10/10 | +0.059 [+0.037, +0.086] pos 9/10 |
| `natural-scarcity` | total-gain | +0.228 [+0.172, +0.279] pos 10/10 | +0.213 [+0.176, +0.242] pos 10/10 | +0.177 [+0.154, +0.202] pos 10/10 |

**FedAvg CTK gain, other populations**

| Experiment | Population | alpha 0.01 | alpha 0.05 | alpha 0.10 |
|---|---|---|---|---|
| `controlled-exposure` | own-domain | +0.071 [+0.046, +0.102] pos 10/10 | +0.107 [+0.068, +0.144] pos 10/10 | +0.132 [+0.085, +0.176] pos 10/10 |
| `controlled-exposure` | worst client | +0.049 [+0.014, +0.113] pos 10/10 | +0.173 [+0.116, +0.242] pos 10/10 | +0.225 [+0.185, +0.277] pos 10/10 |
| `replication-family-set` | own-domain | +0.042 [+0.023, +0.065] pos 9/10 | +0.042 [+0.001, +0.091] pos 8/10 | +0.060 [+0.031, +0.089] pos 8/10 |
| `replication-family-set` | worst client | +0.006 [+0.002, +0.017] pos 7/10 | +0.047 [+0.028, +0.067] pos 9/10 | +0.112 [+0.067, +0.157] pos 9/10 |
| `natural-scarcity` | own-domain | +0.119 [+0.095, +0.154] pos 10/10 | +0.110 [+0.076, +0.139] pos 10/10 | +0.114 [+0.088, +0.153] pos 10/10 |
| `natural-scarcity` | worst client | +0.078 [+0.041, +0.139] pos 10/10 | +0.140 [+0.084, +0.180] pos 9/10 | +0.204 [+0.168, +0.236] pos 10/10 |

**Realised FPR against intended FPR** (mean client, all arms, seeds and experiments; the pipeline's tolerance is 0.02):

| Intended FPR | Mean realised FPR | Mean absolute gap | Largest absolute gap | Arm-seed values with gap above 0.02 | Values |
|---|---|---|---|---|---|
| 0.01 | 0.0106 | 0.0013 | 0.0068 | 0 | 1260 |
| 0.05 | 0.0509 | 0.0039 | 0.0251 | 3 | 1260 |
| 0.1 | 0.1020 | 0.0073 | 0.0364 | 39 | 1260 |

At the primary 0.05 target, three arm-seed values exceed the 0.02 tolerance, all at seed 106 of the two family-support sensitivities: 0.0251 (`family-support-sensitivity-low`, centralized full exposure), 0.0202 and 0.0200 (`family-support-sensitivity-high`, centralized full exposure and peer present); every other experiment stays below 0.018. The validation check that produced the two warnings applies only to the primary alpha. At alpha 0.10, 39 arm-seed values exceed the tolerance, in 12 experiment-seed groups (seeds 103, 105, 106; the largest, 0.036, in the two support sensitivities at seed 106); no check flags them. Section 24.2 lists them.

Reading: the CTK effect is present at all three operating points (FedAvg federation-wide +0.076, +0.117, +0.134 at 0.01, 0.05, 0.10; positive seeds 9, 10, 10 of 10) and grows with the FPR budget, as expected of a recall gain. At 0.01 the interval is wider (+0.037 to +0.125). The own-domain CTK effect is positive with an interval above zero at every alpha in the three experiments shown (primary +0.071, +0.107, +0.132). The own-domain pooling gain is negative at all three alphas in the primary set (-0.048, -0.069, -0.066) but not in the replication set (-0.070, +0.014, +0.058). The permutation control stays near zero at all three alphas on the federation-wide population (-0.008, -0.001, +0.003).

## 19. Robustness Matrix (main CTK result)

FedAvg CTK gain on the federation-wide population at alpha 0.05 unless stated (centralized for trees, which have no federated arm). The category uses the CTK gate thresholds only as a reading aid (mean at least 0.03, interval above zero, at least 8 of 10 seeds); it does **not** create a claim.

| Scope | CTK gain | 95% CI | Positive seeds | Practical threshold met (all three parts) | Direction | Reading |
|---|---|---|---|---|---|---|
| Primary family set, MLP, FedAvg (reference) | +0.117 | [+0.090, +0.145] | 10/10 | yes | positive | positive and practically meaningful |
| Primary family set, MLP, centralized | +0.131 | [+0.086, +0.181] | 10/10 | yes | positive | positive and practically meaningful |
| Replication family set, MLP, FedAvg | +0.064 | [+0.038, +0.077] | 9/10 | yes | positive | positive and practically meaningful |
| Replication family set, MLP, centralized | +0.087 | [+0.051, +0.147] | 10/10 | yes | positive | positive and practically meaningful |
| Linear classifier, FedAvg | +0.094 | [+0.075, +0.110] | 10/10 | yes | positive | positive and practically meaningful |
| Linear classifier, centralized | +0.082 | [+0.065, +0.103] | 10/10 | yes | positive | positive and practically meaningful |
| Gradient-boosted trees, centralized | +0.102 | [+0.076, +0.137] | 10/10 | yes | positive | positive and practically meaningful |
| Lower training support (1,500 rows), FedAvg | +0.107 | [+0.087, +0.128] | 10/10 | yes | positive | positive and practically meaningful |
| Lower family support, FedAvg | +0.143 | [+0.116, +0.163] | 10/10 | yes | positive | positive and practically meaningful |
| Higher family support, FedAvg | +0.117 | [+0.090, +0.141] | 10/10 | yes | positive | positive and practically meaningful |
| Operating point alpha 0.01, FedAvg | +0.076 | [+0.037, +0.125] | 9/10 | yes | positive | positive and practically meaningful |
| Operating point alpha 0.1, FedAvg | +0.134 | [+0.110, +0.164] | 10/10 | yes | positive | positive and practically meaningful |
| Alternative partition salt 1, FedAvg | +0.129 | [+0.105, +0.165] | 10/10 | yes | positive | positive and practically meaningful |
| Alternative partition salt 2, FedAvg | +0.131 | [+0.102, +0.160] | 10/10 | yes | positive | positive and practically meaningful |
| Alternative partition salt 3, FedAvg | +0.119 | [+0.094, +0.145] | 10/10 | yes | positive | positive and practically meaningful |
| Package-only grouping (weaker leakage protection), FedAvg | +0.107 | [+0.083, +0.126] | 10/10 | yes | positive | positive and practically meaningful |
| Own-domain population, FedAvg | +0.107 | [+0.068, +0.144] | 10/10 | yes | positive | positive and practically meaningful |
| Worst client, FedAvg | +0.173 | [+0.116, +0.242] | 10/10 | yes | positive | positive and practically meaningful |
| Family-macro average, FedAvg | +0.124 | [+0.102, +0.153] | 10/10 | yes | positive | positive and practically meaningful |
| Natural scarcity, FedAvg | +0.113 | [+0.094, +0.128] | 10/10 | yes | positive | positive and practically meaningful |

Strict identity grouping (package plus exact feature-vector components) is the primary design, so the reference row is also the strict-grouping row.

Micro-pooled sensitivities from the pipeline's robustness table (FedAvg CTK gain from pooled hits over pooled trials, federation-wide, alpha 0.05, no separate significance rule; **different aggregation from the primary estimand**, see Section 35 item N5):

| Experiment | Sensitivity | Micro CTK gain | 95% CI | Seeds |
|---|---|---|---|---|
| `controlled-exposure` | all-families | +0.066 | [+0.049, +0.083] | 10 |
| `controlled-exposure` | deduplicated-test | +0.055 | [+0.042, +0.068] | 10 |
| `controlled-exposure` | top-family-removal | +0.139 | [+0.109, +0.178] | 10 |
| `family-permutation-control` | all-families | -0.001 | [-0.018, +0.006] | 10 |
| `family-permutation-control` | deduplicated-test | -0.001 | [-0.019, +0.006] | 10 |
| `family-permutation-control` | top-family-removal | -0.001 | [-0.014, +0.009] | 10 |
| `family-support-sensitivity-high` | all-families | +0.065 | [+0.052, +0.074] | 10 |
| `family-support-sensitivity-high` | deduplicated-test | +0.056 | [+0.046, +0.065] | 10 |
| `family-support-sensitivity-high` | top-family-removal | +0.140 | [+0.111, +0.161] | 10 |
| `family-support-sensitivity-low` | all-families | +0.066 | [+0.053, +0.081] | 10 |
| `family-support-sensitivity-low` | deduplicated-test | +0.057 | [+0.045, +0.066] | 10 |
| `family-support-sensitivity-low` | top-family-removal | +0.148 | [+0.121, +0.183] | 10 |
| `model-family-replication-linear` | all-families | +0.080 | [+0.070, +0.088] | 10 |
| `model-family-replication-linear` | deduplicated-test | +0.074 | [+0.062, +0.083] | 10 |
| `model-family-replication-linear` | top-family-removal | +0.082 | [+0.061, +0.106] | 10 |
| `natural-scarcity` | all-families | +0.084 | [+0.070, +0.099] | 10 |
| `natural-scarcity` | deduplicated-test | +0.070 | [+0.060, +0.081] | 10 |
| `natural-scarcity` | top-family-removal | +0.195 | [+0.178, +0.228] | 10 |
| `package-only-grouping` | all-families | +0.067 | [+0.047, +0.084] | 10 |
| `package-only-grouping` | deduplicated-test | +0.051 | [+0.030, +0.065] | 10 |
| `package-only-grouping` | top-family-removal | +0.153 | [+0.128, +0.178] | 10 |
| `partition-salt-sensitivity` | all-families | +0.075 | [+0.066, +0.085] | 30 |
| `partition-salt-sensitivity` | deduplicated-test | +0.062 | [+0.054, +0.071] | 30 |
| `partition-salt-sensitivity` | top-family-removal | +0.157 | [+0.141, +0.178] | 30 |
| `replication-family-set` | all-families | +0.052 | [+0.021, +0.072] | 10 |
| `replication-family-set` | deduplicated-test | +0.044 | [+0.018, +0.060] | 10 |
| `replication-family-set` | top-family-removal | +0.075 | [+0.048, +0.106] | 10 |
| `training-support-sensitivity` | all-families | +0.070 | [+0.048, +0.087] | 10 |
| `training-support-sensitivity` | deduplicated-test | +0.063 | [+0.045, +0.082] | 10 |
| `training-support-sensitivity` | top-family-removal | +0.104 | [+0.076, +0.132] | 10 |

De-duplicated test representations (each identical feature vector counted once per family and scope) lower the micro CTK gain in the primary set from +0.066 to +0.055 (about 16%); removing the three highest-support families raises it to +0.139. Both remain positive with intervals above zero and 10 of 10 seeds.

## 20. Negative Controls

### 20.1 Family-label permutation (Roadmap 27, 31.2)

| Quantity | Estimate | 95% BCa CI | Positive seeds |
|---|---|---|---|
| Real families: FedAvg CTK gain (controlled exposure) | +0.117 | [+0.090, +0.145] | 10/10 |
| Permuted labels: FedAvg CTK gain | -0.001 | [-0.007, +0.007] | 4/10 |
| Permuted labels: centralized CTK gain | -0.004 | [-0.008, +0.002] | 2/10 |

Predeclared null-compatibility rule: the 95% BCa interval of the permutation-control CTK gain must lie within +/-0.03 absolute recall (the CTK practical-effect threshold). The permuted FedAvg interval [-0.007, +0.007] lies entirely inside the band: **null-compatible (equivalent)**. The real effect (+0.117) is far outside the band the permuted estimate occupies (a ratio is not informative because the permuted estimate is essentially zero). Other populations under permutation: own-domain +0.011 [-0.004, +0.036] pos 6/10; worst client -0.001 [-0.023, +0.011] pos 6/10. The own-domain permuted interval [-0.004, +0.036] reaches slightly beyond the +0.03 band edge, so by the same rule it would be unresolved rather than equivalent (at alpha 0.10 the own-domain permuted FedAvg gain is +0.029 [+0.010, +0.050] pos 7/10, interval excluding zero); the worst-client interval [-0.023, +0.011] lies inside the band. The rule in the gate is evaluated on the federation-wide population only, so the own-domain claim is not separately covered by a null-compatibility check.

A design note that affects reading: under permutation the *generic pooling* gain is not null on the federation-wide population (+0.080 [+0.061, +0.101] pos 10/10) and negative on the own-domain population (-0.078 [-0.093, -0.058] pos 0/10). Permuting labels turns the hidden "family" into a random malware subset, so removing it everywhere (family absent) still leaves closely related samples in the training data; the generic component then carries the whole effect and the complementary component is zero, which is what a valid negative control should show. The control is null-compatible for CTK; it is not a null for pooling and was not designed to be.

Development permutation control (development-only): FedAvg CTK -0.008 [-0.017, +0.002], 2 of 5 seeds positive.

### 20.2 Other controls

| Control | Evidence |
|---|---|
| Family absent everywhere | Implemented as a condition in every decomposition experiment. Validation `family-absent-everywhere` (target families absent from every client in the absent arms) passed in all 140 confirmatory runs. |
| Zero-dose condition | Dose 0 is the zero-exposure anchor of the dose curve; the gain at dose 0 is 0 by construction. The requested-dose-1 gain is -0.004 (FedAvg), indistinguishable from zero, and effective dose at requested 1 is 0 in the median unit. |
| Sample-size matching | Validation `sample-size-matched` passed in all runs (per-client training sizes identical across arms). |
| Hidden family absent from target training; hidden rows only from test | Validations `hidden-family-absent-from-target` and `hidden-rows-in-test-only` passed in all 140 runs. |
| Training excludes test; threshold from benign calibration | Validations `training-excludes-test` and `threshold-from-benign-calibration` passed in all runs. |
| Grouping sensitivity | `package-only-grouping`: FedAvg CTK +0.107 [+0.083, +0.126] against +0.117 under strict grouping; the weaker leakage protection does not inflate CTK. Pooling gain is +0.031 [-0.014, +0.079]. |

Structural validation failures across the 140 confirmatory runs: 0.

## 21. Statistical Evidence

**Unit of inference.** The paired difference per confirmatory seed (n = 10 for every experiment; salt-sensitivity has 10 seeds per salt). Hidden families are pooled inside a seed by the pipeline's own aggregation, so the seed is the independent replicate. **Intervals.** 95% BCa paired bootstrap, 9,999 resamples. **Tests.** Exact two-sided Wilcoxon signed-rank on the 10 paired differences (the smallest attainable p-value with n = 10 is 0.00195, reached whenever all 10 differences share a sign). **Multiplicity.** Holm correction within the primary contrast family only: the three FedAvg federation-wide contrasts (total gain, generic pooling gain, CTK gain) of `controlled-exposure` at alpha 0.05; the centralized versions form a reference family without correction; everything else is exploratory. **Practical thresholds.** Local deficit gap 0.05 (8 of 10 seeds), collaboration gain 0.02, CTK gain 0.03 (8 of 10 seeds), dose gain 0.03 at 100 effective peers, known-family tolerance 0.02, FPR tolerance 0.02, poor full recall 0.60, novelty association 0.3 in absolute Spearman, heterogeneity 0.10, mechanism gaps 0.10 (mean) and 0.15 (worst client). **Equivalence band.** +/-0.03 for the permutation control.

Stored estimates: 1884 paired-effect rows (experiment x salt x alpha x population x learner x estimand); 3 in the primary family, 3 in the reference family, 1878 exploratory. Cluster-bootstrap intervals exist only for `controlled-exposure` (one per seed).

**Primary contrast family (FedAvg, federation-wide, alpha 0.05, controlled exposure)**

| Estimand | Mean | Median | 95% BCa CI | Positive seeds | Raw exact Wilcoxon p | Holm-adjusted p | Effect size (mean / seed sd) |
|---|---|---|---|---|---|---|---|
| total-gain | +0.1316 | +0.1336 | [+0.0902, +0.1668] | 10/10 | 0.00195 | 0.00586 | 2.02 |
| pooling-gain | +0.0145 | +0.0297 | [-0.0378, +0.0541] | 7/10 | 0.55664 | 0.55664 | 0.19 |
| ctk-gain | +0.1171 | +0.1149 | [+0.0895, +0.1451] | 10/10 | 0.00195 | 0.00586 | 2.49 |

**Cluster bootstrap** (family-hit resampling by identity component, FedAvg complementary difference, per seed; 2,000 resamples): all 10 per-seed 95% intervals lie above zero (lower bounds +0.016 to +0.085, upper bounds +0.043 to +0.158). These intervals quantify within-seed sampling uncertainty over identity components; they are not combined with the seed-level BCa intervals.

**Interval availability.** Ratio estimates (shares, oracle-gap recovery) have ratio-of-means bootstrap intervals but no Wilcoxon test. Model-family and sensitivity experiments have BCa intervals and exact Wilcoxon p-values in `paired-effects.parquet` but no Holm correction (exploratory by design).

Across all stored CTK-gain rows (300), 272 have a 95% interval entirely above zero; the 28 that do not are listed here: family-permutation-control central family alpha 0.01 salt 0 (+0.007 [-0.013, +0.022]); family-permutation-control fedavg family alpha 0.01 salt 0 (-0.013 [-0.032, +0.005]); family-permutation-control central federation alpha 0.01 salt 0 (+0.005 [-0.016, +0.016]); family-permutation-control fedavg federation alpha 0.01 salt 0 (-0.008 [-0.025, +0.009]); family-permutation-control central own alpha 0.01 salt 0 (+0.010 [-0.008, +0.025]); family-permutation-control fedavg own alpha 0.01 salt 0 (+0.003 [-0.008, +0.011]); family-permutation-control central worst alpha 0.01 salt 0 (-0.008 [-0.024, +0.008]); family-permutation-control fedavg worst alpha 0.01 salt 0 (+0.002 [-0.007, +0.012]); family-permutation-control central family alpha 0.05 salt 0 (-0.001 [-0.005, +0.004]); family-permutation-control fedavg family alpha 0.05 salt 0 (-0.001 [-0.012, +0.008]); family-permutation-control central federation alpha 0.05 salt 0 (-0.004 [-0.008, +0.002]); family-permutation-control fedavg federation alpha 0.05 salt 0 (-0.001 [-0.007, +0.007]); family-permutation-control central own alpha 0.05 salt 0 (-0.002 [-0.011, +0.010]); family-permutation-control fedavg own alpha 0.05 salt 0 (+0.011 [-0.004, +0.036]); family-permutation-control central worst alpha 0.05 salt 0 (-0.018 [-0.031, -0.003]); family-permutation-control fedavg worst alpha 0.05 salt 0 (-0.001 [-0.023, +0.011]); family-permutation-control central family alpha 0.1 salt 0 (+0.004 [-0.007, +0.010]); family-permutation-control fedavg family alpha 0.1 salt 0 (+0.003 [-0.007, +0.011]); family-permutation-control central federation alpha 0.1 salt 0 (+0.003 [-0.008, +0.008]); family-permutation-control fedavg federation alpha 0.1 salt 0 (+0.003 [-0.008, +0.010]); family-permutation-control central own alpha 0.1 salt 0 (+0.003 [-0.004, +0.019]); family-permutation-control central worst alpha 0.1 salt 0 (+0.001 [-0.017, +0.013]); family-permutation-control fedavg worst alpha 0.1 salt 0 (-0.006 [-0.023, +0.008]); partition-salt-sensitivity fedavg worst alpha 0.01 salt 2 (+0.018 [-0.016, +0.037]); partition-salt-sensitivity fedavg worst alpha 0.01 salt 3 (+0.015 [-0.002, +0.032]); replication-family-set central worst alpha 0.01 salt 0 (-0.017 [-0.034, +0.008]); replication-family-set central worst alpha 0.05 salt 0 (+0.054 [-0.002, +0.213]); training-support-sensitivity fedavg worst alpha 0.01 salt 0 (+0.005 [-0.000, +0.013]).

## 22. Gate Outcomes

Structural validity gates (Roadmap 31.1) are enforced per run by the validation checks: every confirmatory run passed all structural checks (Section 24 for the two non-structural operating-point warnings). The twelve implemented claim gates follow. "Measured" values are re-derived from the saved artifacts with the gate's own rule; the outcome column is the stored `results/gates/claims.csv` value.

| Gate | RQ | Hypothesis | Exact criterion | Practical threshold | Measured (confirmatory, alpha 0.05) | Supporting experiment(s) | Outcome (scopes passed) | Allowed wording |
|---|---|---|---|---|---|---|---|---|
| local-deficit | RQ1 | H1 | Central local deficit vs full exposure at least 0.05, 95% CI above 0, at least 8 of 10 positive seeds, in both populations | 0.05; 8 seeds | federation-wide +0.201 [+0.164, +0.231] pos 10/10; own-domain +0.164 [+0.122, +0.233] pos 10/10 | controlled-exposure (MLP, centralized) | **promoted** (2/2) | supported in every evaluated scope |
| collaboration-benefit | RQ2 | H2 | FedAvg total gain at least 0.02 with CI above 0, both populations | 0.02 | federation-wide +0.132 [+0.090, +0.167] pos 10/10; own-domain +0.038 [+0.015, +0.062] pos 8/10 | controlled-exposure (MLP, FedAvg) | **promoted** (2/2) | supported in every evaluated scope |
| complementary-knowledge | RQ2 | H3 | FedAvg CTK gain at least 0.03, CI above 0, at least 8 of 10 seeds in three scopes (primary federation-wide, primary own-domain, replication federation-wide) AND permutation-control interval within +/-0.03 AND no failed validation run | 0.03; 8 seeds; band 0.03 | primary fed-wide +0.117 [+0.090, +0.145] pos 10/10; primary own-domain +0.107 [+0.068, +0.144] pos 10/10; replication fed-wide +0.064 [+0.038, +0.077] pos 9/10; permutation -0.001 [-0.007, +0.007] pos 4/10 (equivalent) | controlled-exposure, replication-family-set, family-permutation-control | **promoted** (3/3) | supported in every evaluated scope |
| generic-pooling-majority | RQ2 | H3 | FedAvg generic-pooling share above 0.5 with the CI excluding 0.5 (promote); refuted when the CI upper bound is below 0.5 | 0.5 | federation-wide share +0.110 [-0.389, +0.354]; own-domain share -1.829 [-5.706, -0.878] | controlled-exposure (MLP, FedAvg) | **rejected** (0/2) | not supported; report the measured components without the claim |
| dose-response | RQ3 | H5 | Three criteria: curve non-decreasing within tolerance 0.02; a level with mean effective dose at least 100 improves recall by at least 0.03 over zero dose; not driven by one family | 0.02; 100 peers; 0.03 | non-decreasing: True; levels with mean effective dose >= 100 among requested doses: 0 (mean effective dose at requested 1000 is 79.4); family criterion evaluated on the same empty set | peer-dose-response (MLP, FedAvg) | **narrowed** (1/3) | supported only in the scopes that passed; state the restriction |
| own-domain-benefit | RQ4 | H2/H3 | FedAvg own-domain CTK gain interval above 0 (min effect 0, no seed requirement) | > 0 | +0.107 [+0.068, +0.144] pos 10/10 | controlled-exposure | **promoted** (1/1) | supported in every evaluated scope |
| worst-client-benefit | RQ5 | H6 | FedAvg worst-client CTK gain interval above 0 | > 0 | +0.173 [+0.116, +0.242] pos 10/10 | controlled-exposure | **promoted** (1/1) | supported in every evaluated scope |
| known-family-safety | RQ7 | H8 | Strongest federated arm (highest federation-wide unseen recall among FedAvg, FedProx, FedAvg+fine-tune): known-family recall change vs local within +/-0.02 and FPR change at most 0.02 | 0.02; 0.02 | strongest arm = fedprox; known-family change -0.0063; FPR change +0.0011. Other arms: FedAvg -0.0325, FedAvg+fine-tune -0.0376 | controlled-exposure | **promoted** (2/2) | supported in every evaluated scope |
| family-dependence | RQ5 | H4 | Across-family spread (max minus min of mean FedAvg CTK gain per family) at least 0.10 | 0.10 | spread 0.293 (16 families pooled over all experiments); 0.339 within the primary set only | family-rescue table (all experiments) | **promoted** (1/1) | supported in every evaluated scope |
| representation-limited-family | RQ5 | - | Families whose full-exposure centralized recall is below 0.60 in the primary model and in linear or trees | 0.60 | 3 of 4 primary-poor families confirmed by an independent model: gappusin, hiddad, revmob | controlled-exposure, model-family-replication-linear, -trees | **promoted** (3/4) | supported only in the scopes that passed; state the restriction |
| feature-novelty-explanation | RQ6 | H7 | Spearman absolute rho at least 0.3 with a CI excluding 0 in both family sets, consistent direction | absolute rho 0.3 | primary rho +0.571 [-0.412, +1.000], p 0.180 (7 families); replication rho +0.333 [-0.570, +1.000], p 0.420 (8 families) | controlled-exposure, replication-family-set | **rejected** (0/2) | not supported; report the measured components without the claim |
| new-mechanism-trigger | RQ9 | H9 | Best simple baseline leaves more than 0.10 mean or 0.15 worst-client recall to centralized full exposure | 0.10; 0.15 | mean-recall gap +0.049; worst-client gap +0.029 (best baseline by mean: centralized peer-present; best by worst client: FedAvg) | controlled-exposure | **rejected** (0/2) | not supported; report the measured components without the claim |

Counts: promoted 8, narrowed 1, rejected 3, insufficient-evidence 0 (12 gates).

Notes on interpretation of gate mechanics are collected in Section 35 (items N1, N2, N4, N6 and N13): the dose-response gate's mechanical failure of two of its three criteria, the pooling of families across experiments in the family-dependence gate, the known-family gate's dependence on which arm is "strongest", the meaning of `rejected` for the feature-novelty gate, and the missing own-domain null check.

## 23. Claim Inventory

Format per claim: related RQ/hypothesis; supporting experiments; quantitative result; uncertainty and seed consistency; gate outcome; exact allowed wording; scope restrictions; limitations. Descriptive observations that are not formal claims follow the table.

| Claim | RQ / hypothesis | Supporting experiments | Quantitative result | Uncertainty and seed consistency | Gate outcome | Exact allowed wording | Scope restrictions | Limitations |
|---|---|---|---|---|---|---|---|---|
| local-deficit | RQ1/H1 | controlled-exposure | Centralized local deficit +0.201 federation-wide, +0.164 own-domain | 10/10 positive seeds in both; CIs above 0.16 | **promoted** (2/2) | supported in every evaluated scope | MLP, alpha 0.05, 7 hidden pairs per seed, static features | Deficit is measured against a centralized full-exposure reference, not against FedAvg full exposure (FedAvg full-exposure local deficit is not computed) |
| collaboration-benefit | RQ2/H2 | controlled-exposure | FedAvg total gain +0.132 federation-wide, +0.038 own-domain | 10/10 and 8/10 positive seeds; CIs above 0 | **promoted** (2/2) | supported in every evaluated scope | MLP FedAvg; own-domain effect is small (+0.038) | Own-domain benefit passes the 0.02 bar with a small margin; the benefit is entirely the complementary component (generic pooling is negative in own domain) |
| complementary-knowledge | RQ2/H3 | controlled-exposure, replication-family-set, family-permutation-control | FedAvg CTK gain +0.117 (fed-wide), +0.107 (own-domain), +0.064 (replication) | three gate scopes have intervals above zero (lower bounds +0.090, +0.068, +0.038) with 10/10, 10/10 and 9/10 positive seeds; permutation interval [-0.007, +0.007] inside the +/-0.03 band | **promoted** (3/3) | supported in every evaluated scope | Static-feature MLP FedAvg; replication effect about half the primary size | Effect size on the replication set is materially smaller; linear model has a different composition (Section 15) |
| generic-pooling-majority | RQ2/H3 | controlled-exposure | Pooling share +0.110 federation-wide (upper CI +0.354), -1.83 own-domain | upper bounds below 0.5 in both populations | **rejected** (0/2) | not supported; report the measured components without the claim | MLP only | A rejected majority claim; it is positive evidence that pooling is not the majority for the MLP, but the linear model shows pooling above half (Section 31) |
| dose-response | RQ3/H5 | peer-dose-response | FedAvg gain over zero dose rises from -0.004 (requested 1) to +0.124 (all available), 10/10 seeds positive at requested 500, 1000 and all | see Section 12 | **narrowed** (1/3) | supported only in the scopes that passed; state the restriction | Requested dose is realised at about 8% (Section 12); outcome reflects gate mechanics (Section 34) | Treat the gate outcome as unresolved for interpretation (possible implementation discrepancy N1) |
| own-domain-benefit | RQ4 | controlled-exposure | +0.107 [+0.068, +0.144] pos 10/10 | 10/10 seeds; CI above 0 | **promoted** (1/1) | supported in every evaluated scope | Own-domain population of clients holding a hidden family; play-late supports it in 6 of 10 seeds | Dominated by the clients with large own-domain support (`anzhi`, `play-early`, `appchina`) |
| worst-client-benefit | RQ5/H6 | controlled-exposure | +0.173 [+0.116, +0.242] pos 10/10 | 10/10 seeds; CI above 0 | **promoted** (1/1) | supported in every evaluated scope | Worst client is defined per seed | Worst client can differ between arms |
| known-family-safety | RQ7/H8 | controlled-exposure | Strongest federated arm (fedprox) known-family change -0.0063; FPR change +0.0011 | tolerance +/-0.02 | **promoted** (2/2) | supported in every evaluated scope | Holds for the strongest arm and for centralized (+0.000) and blend (+0.017) | FedAvg (-0.033) and FedAvg + fine-tuning (-0.038) lose more than 0.02 known-family recall; the promoted claim must not be read as "FedAvg has no known-family cost" |
| family-dependence | RQ5/H4 | family-rescue table | Across-family spread 0.293 (pooled), 0.339 (primary set) | not interval-based (point spread only) | **promoted** (1/1) | supported in every evaluated scope | 16 families, 2 sets | The gate uses point means without family-level intervals |
| representation-limited-family | RQ5 | controlled-exposure, model-family replications | 3 of 4 primary-poor families (gappusin, hiddad, revmob) stay below 0.60 in an independent model | threshold-based | **promoted** (3/4) | supported only in the scopes that passed; state the restriction | "under the tested static representation and models" | Scoped wording applies because one poor family (`adwo`) is not confirmed |
| feature-novelty-explanation | RQ6/H7 | controlled-exposure, replication-family-set | rho +0.57 (7 families) and +0.33 (8 families) | CIs [-0.41, 1.00] and [-0.57, 1.00] | **rejected** (0/2) | not supported; report the measured components without the claim | one predeclared descriptor | Rejected by the gate's non-pass rule, but the data are underpowered (Section 32) |
| new-mechanism-trigger | RQ9/H9 | controlled-exposure | Best simple baseline leaves +0.049 mean and +0.029 worst-client recall to centralized full exposure | thresholds 0.10 and 0.15 | **rejected** (0/2) | not supported; report the measured components without the claim | MLP static features | No headroom under this representation; not a statement about other representations |

**Descriptive observations that are not formal claims** (no gate; not upgraded here): FedAvg CTK gain agrees between natural scarcity and controlled exposure (Section 11); CTK is positive in linear and tree models; generic pooling *reduces* own-domain recall of a locally hidden family in almost every scope; oracle-gap recovery is about 0.63 (FedAvg) to 0.71 (centralized) federation-wide; family-level heterogeneity is large; dose response is monotone in the means; the permutation control is null for CTK.

## 24. Warnings and Anomalies

### 24.1 Operating-point warnings in real runs

| Experiment | Seed | Mode | Model | Intended FPR | Realised FPR (mean client) | Absolute gap | Structural? | Effect on interpretation |
|---|---|---|---|---|---|---|---|---|
| `family-support-sensitivity-low` | 106 | confirmatory | MLP, centralized full exposure (largest); FedAvg and other arms also above 0.02 at alpha 0.10 | 0.05 | 0.0751 | 0.0251 | Non-structural | Recall comparisons for this seed are not equal-FPR evidence at alpha 0.05 for the affected arm (Roadmap 31.1); the seed is retained in the paired means. Not re-partitioned or re-run. |
| `family-support-sensitivity-high` | 106 | confirmatory | MLP, centralized full exposure and peer present | 0.05 | 0.0702 (full), 0.0700 (peer) | 0.0202, 0.0200 | Non-structural | Same seed and partition family as above; same reading. |
| `model-family-replication-trees` | 0 | smoke | Trees | 0.05 | (smoke run) | above 0.02 | Non-structural | Smoke run only; not evidence. |

Cause visible in the artifacts: in seed 106 the `anzhi` client has a large calibration-to-test shift for benign rows under the low and high eligibility partitions (centralized full exposure: realised FPR 0.130 and 0.118 at a 0.05 target and 0.216 and 0.220 at a 0.10 target, with 4,057 benign calibration rows and 2,534 benign test rows, operating status `valid`), while the primary-eligibility partition of the same seed gives 0.055 and 0.115 for `anzhi` (2,286 calibration rows, 2,411 test rows). The shift is a property of those partitions; `appchina` is also above target there (0.065 at 0.05). No re-partitioning or re-run was done.

### 24.2 Other operating-point deviations that no check flags

At alpha 0.10, 39 arm-seed values exceed the 0.02 tolerance (largest 0.0364) in 12 experiment-seed groups. The validation gate checks the primary alpha only, consistent with Roadmap 31.1, so the pipeline reports none of them. They affect only the alpha 0.10 sensitivity rows, including those of the primary experiment (`controlled-exposure`, seed 105, largest 0.0241); the primary alpha rows are affected only by the two support-sensitivity runs above.

| Experiment | Seed | Arm-seed values above 0.02 at alpha 0.10 | Largest gap |
|---|---|---|---|
| `family-support-sensitivity-low` | 106 | 7 | 0.0364 |
| `family-support-sensitivity-high` | 106 | 7 | 0.0350 |
| `model-family-replication-linear` | 105 | 3 | 0.0271 |
| `partition-salt-sensitivity` | 105 | 3 | 0.0260 |
| `controlled-exposure` | 105 | 4 | 0.0241 |
| `peer-dose-response` | 105 | 7 | 0.0240 |
| `training-support-sensitivity` | 105 | 1 | 0.0239 |
| `natural-scarcity` | 105 | 1 | 0.0230 |
| `family-support-sensitivity-low` | 105 | 2 | 0.0225 |
| `model-family-replication-trees` | 103 | 1 | 0.0221 |
| `training-support-sensitivity` | 103 | 1 | 0.0220 |
| `replication-family-set` | 105 | 2 | 0.0214 |

### 24.3 Anomalies and unexpected findings

| ID | Experiment | Seed | Anomaly / warning | Magnitude / meaning | Structural or not | Effect on evidence / action |
|---|---|---|---|---|---|---|
| A1 | peer-dose-response | all | Requested dose is realised at about 8% of the request (requested 100 -> mean 9.0 effective peer rows; 1000 -> 79.4; all available -> 296.2, median 106) | Dose labels overstate exposure; interpret on effective dose | Non-structural; Roadmap 20 anticipates caps | Interpretation only; also drives the dose-gate outcome (Section 34) |
| A2 | controlled-exposure and 8 others | all | FedAvg generic pooling gain on the own-domain population is negative in 9 of 12 experiment/salt scopes, with the 95% interval entirely below zero in 8 (controlled -0.069, 1 of 10 seeds positive); it is positive for the linear model (+0.109), the replication set (+0.014) and lower training support (+0.040) | Pooling without the family hurts a client on its own hidden family | Finding, not a defect | Explains the small own-domain total gain (Section 9) |
| A3 | controlled-exposure | all | FedAvg known-family recall falls 0.033 below local (10/10 seeds negative, concentrated at `anzhi` -0.069) | Known-family cost exists for FedAvg and FedAvg+fine-tune | Finding | The promoted known-family-safety claim refers to the strongest arm (FedProx) |
| A4 | replication-family-set | all | Two families (`utchi`, `zdtad`) are eligible in only 6 of 10 seeds; eligible pairs per seed range 6 to 8 | Replication set is unbalanced across seeds | Design consequence of pre-split eligibility | Family-level means use 6 seeds for those two |
| A5 | natural-scarcity | all | Target pairs per seed range 8 to 11; `classification` shows `rescued` for every family although the experiment has no full-exposure arm (full recall is missing) | Rescue labels in the natural-scarcity family table are not informative | Reporting artifact | Do not read rescue status from natural scarcity |
| A6 | family-permutation-control | all | Generic pooling gain is +0.080 federation-wide and -0.078 own-domain while CTK is null | Consistent with a valid negative control for CTK; not a pooling null | Finding | Section 20 |
| A7 | model-family-replication-linear | all | Linear local recall is 0.279 (weak); generic pooling gain is +0.181, pooling share about two thirds | Composition of the benefit depends on the model class | Finding | Section 15 |
| A8 | controlled-exposure | all | `play-late` supports the own-domain population in only 6 of 10 seeds (642 rows) while `anzhi` has 19,144 rows over 8 seeds | Own-domain estimates are dominated by large-support clients | Design consequence | Section 9 |
| A9 | robustness table | all | Micro-pooled FedAvg CTK gain (+0.066) differs from the primary CTK gain (+0.117) because rows are pooled across families | Two different aggregations are both called CTK gain in artifacts | Documentation issue | Section 35 item N5 |
| A10 | development | dev | Development claim table shows `insufficient-evidence`/`rejected` for gates that need 8 seeds | Not interpretable (5 seeds) | Expected | Section 5.3 |
| A11 | baseline-fairness | 1 (development) | One superseded development execution (2026-09-24 17:02 UTC) failed the structural check `hidden-rows-in-test-only` (status `failed-validation`); the validation logic was then corrected to test the hidden rows the metrics actually used and the run was re-executed | Historical; the current run is `completed` with all structural checks passed | Structural at the time; superseded | None for current evidence; recorded for completeness |
| A12 | family-permutation-control | all | Own-domain permuted FedAvg CTK gain is +0.011 [-0.004, +0.036] at alpha 0.05 (upper end beyond the +0.03 band edge) and +0.029 [+0.010, +0.050] at alpha 0.10 (interval excludes zero) | The permutation control is cleanly null on the federation-wide population (the gated one) but not cleanly equivalent on the own-domain population | Finding; the gate does not cover own-domain | Do not cite the permutation control as an own-domain null without this caveat |

**Not available in the artifacts.** Convergence diagnostics (training loss curves), numerical-instability flags and fallback-behaviour counters are not persisted by the pipeline; no such anomaly is reported because none was recorded, not because none occurred. Provenance and staleness inconsistencies found: the code revision recorded in `results/provenance/code.json` predates the final gate-wording commit (Section 2.3); no stale confirmatory run exists.

## 25. Runtime and Compute Evidence

Per-run seconds are the `run-finished` durations of the current (non-superseded) executions. Runs of the last eight confirmatory experiments overlapped in parallel (Section 25.2), so their per-run seconds include CPU/GPU contention.

| Experiment | Mode | Runs | Mean s/run | Min s | Max s | Total minutes |
|---|---|---|---|---|---|---|
| `baseline-fairness` | development | 5 | 78 | 73 | 80 | 6.5 |
| `controlled-exposure` | development | 5 | 91 | 89 | 96 | 7.6 |
| `controlled-exposure` | confirmatory | 10 | 86 | 80 | 94 | 14.4 |
| `peer-dose-response` | development | 5 | 101 | 97 | 104 | 8.4 |
| `peer-dose-response` | confirmatory | 10 | 93 | 89 | 95 | 15.5 |
| `natural-scarcity` | development | 5 | 46 | 44 | 48 | 3.9 |
| `natural-scarcity` | confirmatory | 10 | 43 | 38 | 47 | 7.2 |
| `family-permutation-control` | development | 5 | 46 | 44 | 47 | 3.8 |
| `family-permutation-control` | confirmatory | 10 | 45 | 43 | 49 | 7.5 |
| `replication-family-set` | confirmatory | 10 | 118 | 78 | 187 | 19.7 |
| `model-family-replication-linear` | confirmatory | 10 | 63 | 59 | 74 | 10.6 |
| `model-family-replication-trees` | confirmatory | 10 | 103 | 85 | 132 | 17.2 |
| `training-support-sensitivity` | confirmatory | 10 | 47 | 43 | 51 | 7.8 |
| `partition-salt-sensitivity` | confirmatory | 30 | 83 | 76 | 94 | 41.7 |
| `family-support-sensitivity-low` | confirmatory | 10 | 78 | 66 | 83 | 12.9 |
| `family-support-sensitivity-high` | confirmatory | 10 | 62 | 45 | 81 | 10.4 |
| `package-only-grouping` | confirmatory | 10 | 87 | 74 | 99 | 14.5 |

### 25.1 Campaign totals

| Item | Value |
|---|---|
| Confirmatory runs | 140 |
| Confirmatory sum of per-run seconds | 2.99 h |
| Confirmatory campaign wall clock (first run start to last run finish in the log) | 83 min (2026-09-24T19:42:50 to 2026-09-24T21:05:57 UTC) |
| Development current runs | 25 runs, 0.50 h |
| Preprocessing (first full run) | 293 s |
| Smoke command | 13 s |
| Report per run of `run` / `report` | about 7 s development, 16 s confirmatory |

### 25.2 Parallel execution and resources

The first four confirmatory experiments (`controlled-exposure`, `peer-dose-response`, `natural-scarcity`, `family-permutation-control`) and part of `replication-family-set` ran one at a time. The remaining experiments ran as five parallel worker processes (linear and low family support; trees and high family support; package-only and training-support; salt-sensitivity seeds 100 to 104; salt-sensitivity seeds 105 to 109) plus the tail of `replication-family-set` (six processes at peak). Ad-hoc observations during that period (not logged by the pipeline): one process used about one core, 3 GB of RAM and 2.5 GB of GPU memory; at six processes the load average was 9.0 on 10 cores, GPU utilisation about 75% and about 14 GB RAM remained available. CPU, GPU and memory are not recorded in any run artifact. The trees experiment uses several cores per process.

Approximate sequential compute if run one after another with the uncontended per-run times (first four experiments: 43 to 93 s per run): about 3.0 h measured (inflated by contention for the parallel part); the wall-clock campaign took 83 minutes, a ratio of 2.2 between summed run time and wall time.

## 26. Potentially Underused Existing Evidence

Findings that already exist in the saved evidence but are not (or only weakly) reflected in the formal claim set. None is promoted here.

| ID | Existing evidence | Quantitative result | Already claimed? | Possible legitimate use |
|---|---|---|---|---|
| U1 | Complementary component dominates the MLP collaboration benefit | FedAvg CTK share 0.89 [+0.65, +1.39] against pooling share 0.11 [-0.39, +0.35]; pooling gain +0.014 [-0.038, +0.054] pos 7/10 | The rejected generic-pooling-majority gate is a one-sided statement about pooling; nothing formally states that CTK exceeds half of the benefit | A descriptive statement of the measured decomposition; a formal dominance claim would need a fresh predeclared test (Section 31) |
| U2 | Generic pooling lowers own-domain recall of a locally hidden family | FedAvg own-domain pooling gain -0.069 [-0.108, -0.040] pos 1/10; negative in 9 of 12 experiment/salt scopes (interval below zero in 8) | No gate targets it; appears only inside decomposition tables | A bounded finding about cross-domain pooling and deployment-domain detection (needs the caveats that it is absent for the linear model and low-support training) |
| U3 | Natural scarcity reproduces the controlled CTK effect | CTK +0.113 [+0.094, +0.128] pos 10/10 against +0.117 [+0.090, +0.145] pos 10/10 | No gate consumes natural scarcity | External-validity support for the controlled design (not pooled numerically) |
| U4 | Unanimity across seeds and partitions | Of the 20 rows of the robustness matrix, 18 are positive in 10 of 10 seeds and all 20 in at least 9 of 10; salts 1 to 3 give +0.129, +0.131, +0.119 | Only summarised as a gate scope count | A strong stability statement for the primary effect |
| U5 | No leakage inflation | Package-only grouping +0.107 [+0.083, +0.126] pos 10/10 against strict grouping +0.117 [+0.090, +0.145] pos 10/10 | Sensitivity is outside the gate set | Supports the leakage-hardening choice without weakening it |
| U6 | Model-class breadth of CTK | Linear FedAvg +0.094 [+0.075, +0.110] pos 10/10; trees centralized +0.102 [+0.076, +0.137] pos 10/10 | Model replications feed only the representation-limited claim | Classifier-independence of the CTK sign and rough size (the composition with pooling differs by class) |
| U7 | Worst-client benefit is entirely complementary | Worst-client CTK +0.173 [+0.116, +0.242] pos 10/10 against worst-client pooling -0.026 [-0.080, +0.013] pos 3/10 | Gate uses only the CTK interval above zero | Directly answers H6 (peer knowledge, not pooling, helps the worst client) |
| U8 | Oracle-gap recovery | FedAvg recovers 0.63 of the centralized full-exposure gap federation-wide; centralized 0.71 | Estimand implemented but unused by any gate | Quantifies residual headroom (Section 33) |
| U9 | A large-support family hides the effect in pooled numbers | Micro-pooled CTK gain rises from +0.066 to +0.139 when the three highest-support families are removed; `dowgin` (5,911 test rows) has CTK +0.003 and pooling +0.110 | Only a robustness row | Explains why pooled and macro-averaged CTK estimates differ and that the effect concentrates in low-support families |
| U10 | The permutation control is null at all three operating points | FedAvg permuted CTK -0.008, -0.001, +0.003 at alpha 0.01, 0.05, 0.10 (all intervals within +/-0.03) | Only the primary alpha enters the gate | Strengthens the causal reading of CTK across operating points |
| U11 | A simple blend matches heavier baselines | Blend own-domain recall 0.571 (best of the six arms), known-family change +0.017, federation-wide 0.634 against FedAvg 0.638 | Blend is not analysed with intervals | Supports the "no mechanism headroom" reading and a low-cost deployment story |
| U12 | FedProx has the smallest known-family cost among federated arms | FedProx known-family change -0.006 against FedAvg -0.033 | Used only to select the "strongest" arm | Useful nuance for the security-cost message |

## 27. Evidence-Preserving Improvement Opportunities

Everything below can be done with the existing confirmatory evidence and without changing any experiment outcome, gate, threshold, seed or family selection.

### 27.1 Better use of existing results

- Present the complementary-knowledge result as one coherent chain that the data already support: local deficit (+0.20 federation-wide) -> collaboration helps (+0.13) -> the gain is complementary (+0.117) rather than generic (+0.014) -> it survives own-domain evaluation (+0.107) and the worst client (+0.173) -> it replicates in direction on a disjoint family set (+0.064), across linear and tree models, three alternative partition salts, three operating points, lower training support and both family-support regimes -> a permutation control is null -> natural scarcity gives the same size effect.
- Give the replication family set its own headline row instead of a third scope inside one gate: the halving of the effect is informative, not a defect.
- Show natural scarcity next to controlled exposure (agreement in CTK, disagreement in pooling) as the external-validity evidence it is.
- Report worst-client evidence with the pooling contrast beside it (+0.173 against -0.026).
- Present representation-limited families as a bounded finding: three of four poorly rescued families stay poor in an independent model (`gappusin`, `hiddad`, `revmob`), while `adwo` does not.

### 27.2 Better statistical presentation (existing statistics only)

- Paired-seed plots and forest plots of the 20 robustness rows (mean, BCa interval, positive seeds).
- Family-level dot plots with seed ranges (already in the family rescue map; add per-family seed spread).
- A stacked decomposition plot (pooling, CTK) by population and model class: the composition difference between MLP, linear and trees is visible at once.
- Client-level small multiples for own-domain recall (Section 14), including the `anzhi` known-family cost.
- Dose curve on effective dose (not requested dose) with per-family lines.
- A table of Holm-adjusted primary contrasts next to the exploratory estimates so the reader sees which numbers are inferential.

### 27.3 Better claim wording

Candidates where current wording is under-stated, over-broad, or insufficiently scoped (the gates stay unchanged; see also Section 29):

| Claim | Current wording | Evidence | Suggested wording | Why the suggestion stays valid |
|---|---|---|---|---|
| known-family-safety (promoted) | "supported in every evaluated scope" | Strongest arm FedProx -0.006; centralized +0.000; blend +0.017; FedAvg -0.033, FedAvg+fine-tune -0.038 | "No material known-family cost for the strongest federated arm (FedProx) or centralized pooling; FedAvg loses 0.033 known-family recall, concentrated at one client" | Names the arm the gate actually tested and reports the cost that exists (too broad as written) |
| complementary-knowledge (promoted) | "supported in every evaluated scope" | +0.117 primary, +0.064 replication, positive in 20 of 20 robustness scopes | "Peer-held family knowledge adds 0.06 to 0.13 absolute unseen-family recall at a fixed 5% FPR across two disjoint family sets, three model classes and three operating points; the size depends on the family set" | States the range and its dependence (insufficiently scoped as written) |
| collaboration-benefit (promoted) | "supported in every evaluated scope" | Federation-wide +0.132; own-domain +0.038 | "FedAvg improves federation-wide unseen-family recall by 0.13; on the client's own domain the improvement is small (0.04) because the generic pooling component is negative there" | The own-domain scope passes the 0.02 bar narrowly; the plain wording hides that |
| generic-pooling-majority (rejected) | "not supported; report the measured components" | Pooling share +0.11 (upper CI 0.35) | "For the MLP, generic pooling accounts for at most about a third of the federation-wide collaboration gain (upper bound 0.35)" | A rejected majority claim is stronger than the neutral wording; the statement is confined to the MLP because the linear model shows the opposite composition |
| dose-response (narrowed) | "supported only in the scopes that passed; state the restriction" | Means are monotone and 10 of 10 seeds are positive at requested 500 and above | Do not rewrite until the gate discrepancy N1 is resolved (Section 34) | Wording follows an outcome that may be a gate artifact |

### 27.4 Better result organisation

The evidence supports the narrative *local deficit -> collaboration helps -> generic pooling alone does not explain the gain (MLP) -> peer threat knowledge provides the incremental benefit -> effect survives own-domain evaluation -> worst client improves -> known-family cost is small for the strongest arm (larger for FedAvg) -> effect varies by family -> several families stay representation-limited*. Two amendments are needed to keep it honest: the generic-pooling statement holds for the MLP but not for the linear model, and "known-family cost is small" is arm-specific. The current report leads with the decomposition figure and tables; the negative own-domain pooling gain and the natural-scarcity agreement are buried in tables.

### 27.5 Better figures and tables from existing evidence

Forest plot of the CTK gain over all scopes; stacked pooling/CTK bars per model class; own-domain versus federation-wide slopegraph by experiment; dose curve on effective dose with family lines; client-level known-family change chart; alpha-profile plot (0.01, 0.05, 0.10) for CTK and pooling; a warnings/anomalies table in the appendix; a run-reconciliation table in the appendix.

## 28. Novelty Strengthening Opportunities

The Roadmap (section 33) forbids priority language ("first", "novel", "unprecedented", "state of the art") unless independently proven, and requires a citation-chaining audit before submission. Nothing in this section asserts literature novelty; it states what the project does and what would need checking.

### 28.1 Methodological

| Element | What the project does | Supporting evidence here | Literature collision to check before any novelty statement |
|---|---|---|---|
| Controlled family exposure with hide-from-target | Removes a chosen family from one client only, holding all else fixed, with validations that hidden rows are test-only | All 140 runs passed the hidden-family and test-only validations | Rare-class transfer and missing-class federated learning; controlled class-removal ablations |
| Matched family-absent-everywhere control | Same training budget and clients, family removed from every client | Enables the pooling / complementary split; permutation control null | Class-incremental and rare-class FL baselines that lack a matched pooled control |
| Pooling versus complementary decomposition with oracle-gap | Three-way decomposition with seed-paired BCa intervals | Section 8; composition differs by model class | Attribution-of-benefit analyses in FL (data volume versus knowledge transfer) |
| Own-domain versus federation-wide evaluation | Same decomposition on the deployment-domain population | Section 9; own-domain pooling negative | Domain-shift evaluations in Android malware FL |
| Peer-dose-response | Manipulates peer family exposure with the target at zero | Section 12; gate outcome unresolved (N1) | Sample-efficiency and data-scarcity studies in FL |
| Worst-client CTK analysis | Worst-client effect with the pooling contrast beside it | +0.173 against -0.026 | Fairness / worst-group analyses in FL |
| Natural-scarcity validation | Uses naturally rare families rather than constructed hiding | CTK agrees with controlled design | Natural-experiment validation of constructed manipulations |
| Identity-safe grouping | Connected components over package and exact feature-vector identity | Package-only sensitivity shows no inflation | Leakage-aware Android dataset splits (package, time, family) |
| Family-level full-exposure ceilings | Per-family full-exposure recall as an oracle ceiling | Section 13.6 | Per-class ceilings in imbalanced FL |
| Representation-limited family analysis | Requires poor full recall in the primary model and an independent model | 3 of 4 families confirmed | Class-difficulty analyses that do not separate exposure from representation |

### 28.2 Empirical

Supported and potentially notable *as measured findings under this setup*: (1) for the MLP the collaboration gain is carried by the complementary component while the generic component is near zero federation-wide and negative in the own domain; (2) natural scarcity reproduces the controlled CTK size; (3) the worst client gains from peer knowledge and not from pooling; (4) FedProx and centralized pooling show no known-family cost while FedAvg pays 0.033; (5) the complementary effect is family dependent (range +0.003 to +0.343 in the primary set) and three families stay representation-limited; (6) the CTK sign is stable across MLP, linear and tree models, salts, operating points and support levels. Not supported: a model-independent *size* of CTK, or a universal composition of the benefit.

### 28.3 Measurement

Total gain, generic pooling gain, CTK gain, complementary share, oracle-gap recovery, dose curve on effective dose, family-level rescue ceiling, own-domain and worst-client CTK are all implemented with paired intervals. What makes them useful is their combination under a fixed FPR and a matched control; each ingredient (gain decomposition, oracle ceilings, dose curves) exists in other fields, so any novelty statement must be about the combination and the Android FL setting, and must survive the citation audit.

### 28.4 Negative-result value

Rejected claims strengthen the contribution when presented as bounds: pooling is not the majority for the MLP (share upper bound 0.35); the new-mechanism trigger does not fire (residual headroom 0.049 mean and 0.029 worst client against thresholds 0.10 and 0.15), so standard baselines capture most of the available benefit under this representation; the feature-novelty hypothesis is unresolved rather than refuted (Section 32). "Full exposure still fails" for three families, which is an explicitly allowed outcome in Roadmap 32.

### 28.5 Novelty statements the current evidence does not support

- Any "first", "novel" or priority claim (forbidden by Roadmap 33).
- That CTK dominates generic pooling in general (only the MLP; the linear model shows the opposite).
- That novelty in feature space explains CTK (underpowered, CI includes zero).
- That a new collaboration mechanism is needed or beneficial (the trigger does not fire).
- That the dose curve reaches a saturation point or that N samples suffice (the curve is still rising at the largest requested level and the gate outcome is unresolved).
- That results transfer beyond this dataset, the static 925-feature representation and the four simulated client domains.

## 29. Claim Strengthening Opportunities

No gate, threshold or hypothesis is changed. "Stronger defensible version" means better use of evidence that already exists.

| Claim | Current strength | Existing evidence not fully used | Stronger defensible version | Requires new experiments? |
|---|---|---|---|---|
| local-deficit | promoted | Replication-set, linear and trees local deficits are available in the family tables but not in the gate | "Local models miss about 0.20 (federation-wide) and 0.16 (own-domain) unseen-family recall relative to a centralized full-exposure reference, in 10 of 10 seeds" | No |
| collaboration-benefit | promoted | Primary set: federation-wide total gain positive with intervals above zero at alpha 0.05 and 0.10 and at 0.01 (+0.111 [+0.043, +0.171] pos 8/10); own-domain at alpha 0.01 +0.023 [-0.022, +0.057] pos 7/10 (interval includes 0); replication set at alpha 0.01 +0.007 [-0.096, +0.082] pos 6/10 (interval includes 0) | Add scope: "federation-wide at alpha 0.05 and 0.10 in both family sets; small and less certain in the own domain and at alpha 0.01" | No |
| complementary-knowledge | promoted | 20 of 20 robustness rows positive with intervals above 0; salts, models, support, operating points, natural scarcity | "... and persists across ... " (Section 27.3); state range 0.06 to 0.13 and that the replication effect is about half | No |
| generic-pooling-majority | rejected | Upper CI 0.35 federation-wide; linear model differs | State the bound for the MLP and the linear-model contrast; no promotion | No (a dominance claim would need fresh seeds) |
| dose-response | narrowed | Monotone means; 10/10 positive seeds at requested 500+; unclear gate mechanics | Wait for resolution of N1 (Section 34) | Possibly a corrected re-evaluation of stored evidence (not done here) or a focused fresh-seed dose experiment |
| own-domain-benefit | promoted | FedAvg own-domain CTK gain has an interval above zero in 11 of 11 non-control experiment/salt scopes at alpha 0.05 | Add that generic pooling is negative on the same population | No |
| worst-client-benefit | promoted | Positive in all model classes, salts and operating points except replication centralized (+0.054, CI touches 0) | Add the contrast with pooling and the replication weakness | No |
| known-family-safety | promoted | FedAvg cost -0.033 (10/10 seeds negative) | Arm-specific wording (Section 27.3) | No |
| family-dependence | promoted | Spread 0.339 in the primary set and 0.185 in the replication set | Report both spreads and the per-family intervals | Optional: family-level BCa intervals from stored seed values |
| representation-limited-family | promoted (scoped) | 3 of 4 confirmed; `adwo` not confirmed | Name the three families and the models | No |
| feature-novelty-explanation | rejected | rho +0.57 (n=7) and +0.33 (n=8), wide CIs; consistent positive direction for distance descriptors | Report as underpowered / unresolved, not as refuted (Section 32) | A fresh-seed extension with more families is the only legitimate route |
| new-mechanism-trigger | rejected | Headroom 0.049 mean and 0.029 worst client | "Standard baselines recover about 0.53 to 0.76 of the full-exposure gap; the remaining headroom is below the mechanism thresholds" | No |

## 30. Rejected and Narrowed Claims: Can Anything Legitimately Be Improved?

For each rejected or narrowed claim: why it failed, the numbers, the gate, robustness, the apparent nature of the failure and the response class. No gate is changed, no subset is chosen, and no evidence is dropped.

| Claim | Why it failed and actual values | Gate threshold | Seed and robustness behaviour | Nature of the failure | Response |
|---|---|---|---|---|---|
| generic-pooling-majority (rejected) | The share of the FedAvg gain attributable to generic pooling is small: 0.11 federation-wide (CI [-0.39, +0.35]), -1.83 own-domain (CI [-5.71, -0.88]); the gate refutes a majority when the upper bound is below 0.5 | Threshold 0.5. Both upper bounds are below it | Positive for pooling seeds: 7/10 (fed-wide), 1/10 (own-domain); model-dependent (linear pooling share about two thirds) | Genuinely negative for the MLP; model-specific overall (does not hold for linear) | Leave as a valid negative finding; improve presentation; a formal CTK-dominance test needs fresh seeds (Section 31) |
| dose-response (narrowed, 1 of 3 criteria) | Criterion 1 (monotone within 0.02) passes; criteria 2 and 3 are evaluated on an empty set because no requested dose level has mean effective dose of at least 100 and the all-available level is excluded from the curve | Tolerance 0.02; effective dose 100; gain 0.03 | Means rise monotonically; 10/10 seeds positive at requested 500, 1000 and all; descriptive units with effective dose >= 100 gain about +0.045 (Section 34) | Threshold- and implementation-specific (possible discrepancy N1), not a negative finding about the curve | Resolve the gate discrepancy first (deeper analysis of existing evidence); then, if warranted, a separately frozen fresh-seed dose experiment; do not reinterpret the gate here |
| feature-novelty-explanation (rejected) | Two scopes fail the absolute rho >= 0.3 with CI-excluding-zero rule: primary rho +0.571 (CI [-0.412, +1.000], p 0.180, 7 families), replication rho +0.333 (CI [-0.570, +1.000], p 0.420, 8 families) | absolute rho 0.3 and CI excluding 0 | Direction is positive in both sets; absolute rho point estimates exceed 0.3 in both; the interval is the problem | Underpowered (n = 7 and 8), not refuted | Improve presentation (report as unresolved); no descriptor search; further work only as a separate exploratory question with more families |
| new-mechanism-trigger (rejected) | The best simple baseline leaves 0.049 mean and 0.029 worst-client recall to centralized full exposure, below 0.10 and 0.15 | Thresholds 0.10 and 0.15 | Consistent across baselines (largest gap 0.094 mean for FedAvg+fine-tune, 0.081 worst-client for blend) | Genuinely negative for a mechanism (no headroom), in this representation | Leave as a valid finding: the mechanism line is closed by the protocol |

Representation-limited-family is promoted but carries the scoped wording because one primary-poor family (`adwo`) is not confirmed by an independent model; no response is needed.

## 31. Generic-Pooling-Majority Analysis

| Quantity (FedAvg, MLP, alpha 0.05) | Federation-wide | Own-domain |
|---|---|---|
| Local recall (mean) | 0.507 | 0.499 |
| No-family collaborative recall | 0.521 | 0.430 |
| Peer-family collaborative recall | 0.638 | 0.537 |
| Total gain | +0.132 [+0.090, +0.167] pos 10/10 | +0.038 [+0.015, +0.062] pos 8/10 |
| Generic pooling gain | +0.014 [-0.038, +0.054] pos 7/10 | -0.069 [-0.108, -0.040] pos 1/10 |
| CTK gain | +0.117 [+0.090, +0.145] pos 10/10 | +0.107 [+0.068, +0.144] pos 10/10 |
| Pooling share | +0.110 [-0.389, +0.354] | -1.829 [-5.706, -0.878] |
| Complementary share | +0.890 [+0.646, +1.389] | +2.829 [+1.878, +6.706] |

Seed-level decomposition, FedAvg federation-wide (alpha 0.05):

| Seed | Total gain | Pooling gain | CTK gain | CTK share (seed) |
|---|---|---|---|---|
| 100 | +0.044 | -0.139 | +0.183 | 4.18 |
| 101 | +0.177 | +0.039 | +0.138 | 0.78 |
| 102 | +0.116 | -0.036 | +0.153 | 1.31 |
| 103 | +0.186 | +0.094 | +0.092 | 0.49 |
| 104 | +0.113 | +0.028 | +0.085 | 0.75 |
| 105 | +0.231 | +0.054 | +0.177 | 0.76 |
| 106 | +0.023 | -0.062 | +0.085 | 3.67 |
| 107 | +0.099 | +0.031 | +0.068 | 0.68 |
| 108 | +0.151 | +0.009 | +0.142 | 0.94 |
| 109 | +0.175 | +0.126 | +0.049 | 0.28 |

**Composition across contexts** (FedAvg unless stated; federation-wide; CTK share = CTK / total from the mean effects):

| Context | Total | Pooling | CTK | CTK share | Pooling share |
|---|---|---|---|---|---|
| MLP primary | +0.132 | +0.014 | +0.117 | 0.89 | 0.11 |
| MLP primary, centralized | +0.152 | +0.022 | +0.131 | 0.86 | 0.14 |
| MLP replication set | +0.081 | +0.017 | +0.064 | 0.79 | 0.21 |
| Linear | +0.274 | +0.181 | +0.094 | 0.34 | 0.66 |
| Trees (centralized) | +0.155 | +0.053 | +0.102 | 0.66 | 0.34 |
| Natural scarcity | +0.213 | +0.100 | +0.113 | 0.53 | 0.47 |
| Lower training support | +0.222 | +0.115 | +0.107 | 0.48 | 0.52 |
| MLP primary, alpha 0.01 | +0.111 | +0.035 | +0.076 | 0.68 | 0.32 |
| MLP primary, alpha 0.10 | +0.133 | -0.000 | +0.134 | 1.00 | -0.00 |

**Does the rejection give positive scientific evidence that the benefit is not primarily generic additional data?** For the MLP federation-wide population, partly yes: the pooling share is below one half with its upper interval bound at 0.35, the pooling gain interval includes zero (7 of 10 seeds positive) and pooling is negative in the own domain. That supports "generic additional data does not explain most of the benefit **for this MLP under this design**". It does not establish that pooling is small (the interval reaches down to -0.39), it is not shown for the linear model (pooling share about 0.66) or for natural scarcity (0.47), and the gate never tested the converse (CTK above half). The federation-wide CTK share interval [0.65, 1.39] lies above 0.5, which is descriptive support only.

**What a formal test of CTK dominance would need.** A new hypothesis, motivated after seeing this evidence, with its own frozen design: the pre-declared criterion would be that the complementary share's interval lies above 0.5 and the pooling share's interval below 0.5, in the federation-wide population for FedAvg and centralized MLPs, with at least 8 of 10 seeds where CTK exceeds pooling, across the primary and the replication family sets, and with linear and tree models reported as scope-limiting contrasts. It would use fresh, untouched seeds and could not alter the current outcome of `generic-pooling-majority`.

## 32. Feature-Novelty Analysis

| Family set | Primary descriptor (nearest-known-family distance) rho | 95% CI | p | Families | absolute rho >= 0.3 and CI excludes 0? |
|---|---|---|---|---|---|
| controlled-exposure | +0.571 | [-0.412, +1.000] | 0.180 | 7 | no |
| replication-family-set | +0.333 | [-0.570, +1.000] | 0.420 | 8 | no |

Descriptive Spearman correlations of the four other stored descriptors with FedAvg CTK gain, family means (**exploratory, no p-values or intervals, not used for any decision; listed only because they are already computed and to show direction consistency**):

| Descriptor | Primary set | Replication set |
|---|---|---|
| centroid-distance-to-known-malware | +0.50 (n=7) | +0.55 (n=8) |
| distance-to-benign-centroid | +0.64 (n=7) | +0.33 (n=8) |
| fraction-active-features-known | -0.61 (n=7) | -0.38 (n=8) |
| max-jaccard-to-known-family | -0.21 (n=7) | +0.10 (n=8) |
| nearest-known-family-distance | +0.57 (n=7) | +0.33 (n=8) |

Distance-type descriptors correlate positively with CTK gain (families further from known malware or from the benign centroid gain more) and the similarity-type descriptors negatively (families already represented among known malware gain less), in both sets, which is the direction hypothesis H7 predicts. With 7 and 8 families a Spearman correlation needs about absolute rho >= 0.79 and 0.74 for two-sided 5% significance (standard critical values), which is why a point estimate of +0.57 cannot clear the gate. Family-level scatter is in `results/figures/feature-novelty-versus-ctk-gain.png`; the values behind it are in Section 13 (novelty column).

**Assessment.** The novelty hypothesis is *unresolved and underpowered*, not shown to be false: a consistently signed moderate correlation on 7 and 8 families with intervals spanning almost the whole range. Other reasons the descriptor may be weak are all plausible and untested here: family labels (AVClass2) may be noisy semantics, the static 925-bit representation may not capture the behaviour that makes a family novel, and relationships may be nonlinear (none was predeclared). The gate labels this `rejected` because a non-pass with resolved associations is treated as refuted; Section 35 item N4 discusses the label. **No descriptor search is recommended.** If pursued, treat it as a separate exploratory question with many more families (for example a dataset with more labelled families) and a single predeclared descriptor.

## 33. New-Mechanism Analysis

Residual headroom to centralized full exposure (mean and worst-client recall, alpha 0.05, peer family present):

| Baseline | Federation-wide recall | Mean-recall gap to full exposure | Worst-client recall | Worst-client gap | Oracle-gap recovery (mean) | Known-family change vs local |
|---|---|---|---|---|---|---|
| central | 0.659 | +0.049 | 0.411 | +0.042 | 0.76 | +0.000 |
| fedavg | 0.638 | +0.070 | 0.425 | +0.029 | 0.65 | -0.033 |
| fedprox | 0.646 | +0.062 | 0.380 | +0.074 | 0.69 | -0.006 |
| fedavg-finetune | 0.614 | +0.094 | 0.407 | +0.047 | 0.53 | -0.038 |
| blend | 0.634 | +0.074 | 0.373 | +0.081 | 0.63 | +0.017 |

The gate takes the best baseline per metric: mean gap +0.049 (centralized peer-present) against 0.10 and worst-client gap +0.029 (FedAvg) against 0.15. Neither is exceeded, so the trigger fails and "the mechanism line is closed" (Roadmap 31.2). The numbers support the wording *strong standard collaborative baselines recover most of the practically available benefit under the tested static representation* (0.53 to 0.76 of the oracle gap federation-wide, depending on the arm), with the caveat that the full-exposure reference is itself only 0.708. A new mechanism would add complexity without a demonstrated headroom; the remaining errors are concentrated in representation-limited families (Section 13.6), which a collaboration mechanism cannot fix if the features do not separate them.

## 34. Dose-Response Narrowing Analysis

Full curves are in Section 12. Summary for FedAvg (means over 10 seeds x 7 families):

Successive recall differences along the requested-dose axis (tolerance for the monotone criterion is -0.02): -0.004, +0.008, +0.008, +0.009, +0.048, +0.022, +0.035. The most negative step is -0.0042 (requested 0 -> 1), inside the tolerance, so criterion 1 (monotone) **passes**.

**Why the gate reads `narrowed` (1 of 3 criteria).** Criterion 2 asks whether a level with at least 100 effective peer samples improves recall by 0.03 over zero dose. The implementation evaluates the *level mean* of effective dose and drops the `all available` level (`dose` is null) from the curve before applying the filter. The highest requested level has a mean effective dose of 79.4, so no level qualifies and criterion 2 is evaluated on an empty set (false). Criterion 3 (not driven by one family) is computed on the same empty set (false). At the unit level the evidence is different: 70 of 210 FedAvg (seed, family, dose) units reach an effective dose of at least 100 (across 5 families); their mean gain over zero dose is +0.045, and 50% of them gain at least 0.03. This is descriptive and is **not** a re-evaluation of the gate.

**Onset and saturation (descriptive).** Mean FedAvg gain stays within noise up to requested 50 (effective about 4), reaches +0.020 at requested 100 (effective 9), crosses 0.03 between requested 100 and 500 (effective about 9 to 43), and keeps rising to +0.124 at all available (effective about 296, median 106). There is no saturation within the tested range; the curve is still rising at the largest level. Centralized and FedAvg+fine-tuning show the same shape (+0.110 and +0.090 at all available); centralized is noisier (seed sd 0.070) and shows less gain than FedAvg at requested 100 (+0.006 against +0.020).

**Family heterogeneity.** At all available, FedAvg gains range from revmob +0.336, leadbolt +0.268, adwo +0.085, airpush +0.082, hiddad +0.070, gappusin +0.034, dowgin -0.004 (Section 13.7); the two families with the largest gains (`revmob`, `leadbolt`) have the smallest effective peer support (55 and 84 rows), while `dowgin` with 1,188 effective rows shows no gain, so the curve is family-dependent in level. Leaving out any single family the mean FedAvg gain at all available stays between +0.089 and +0.146.

**Model heterogeneity and seed consistency.** Positive seeds for FedAvg gain over zero dose: 5/10 at requested 1, 8/10 at 10, 9/10 at 50 and 100, 10/10 at 500, 1000 and all; for centralized 6, 4, 7, 6, 9, 9, 10 of 10 (noisier); for fine-tuning 6, 7, 7, 8, 10, 10, 10.

**Existing evidence already supports a useful scoped statement**, provided the discrepancy is resolved first: FedAvg unseen-family recall rises with effective peer exposure of the hidden family, with no measurable gain up to about 4 effective rows, a gain above 0.03 reached somewhere between about 9 and 43 effective rows, and further increase up to about 300; the size at a given effective dose depends on the family. **Would a focused fresh-seed dose experiment materially improve the story?** Yes if it realises the requested dose exactly (so that requested equals effective) and samples more effective levels between 10 and 300; otherwise it would repeat the same realisation problem. That would be a new design (Section 38, E2).

## 35. Narrative-versus-Evidence Audit

Sources audited: `README.md`, Roadmap wording (sections 6, 20, 31, 32), gate wording (`claims.csv`), `docs/Audit Matrix.md`, decision logs, generated tables and figures. Numeric artifacts cross-check: `results/gates/claims.csv` equals `results/tables/claim-gates.csv` and the stored `claim-gates.parquet`; every parquet under `results/evidence/` and `results/statistics/` is byte-identical to its `outputs/` source; the run counts agree across plans, directories, run index and seed-status (Section 4). **No wording was changed.**

| ID | Where | Finding | Consequence / status |
|---|---|---|---|
| N1 | `analysis/gates.py` (dose gate) vs Roadmap 31.2 dose-response | Roadmap: "exposure of at least 100 effective peer samples improves recall by at least 0.03 over zero dose". Implementation applies the 100-peer test to the *level mean* of effective dose and excludes the `all available` level, so no level qualifies (highest mean 79.4) and two of three criteria are evaluated on an empty set. At unit level 70 of 210 FedAvg units reach 100 effective peers with mean gain +0.045. | Possible implementation discrepancy affecting the `dose-response` outcome (`narrowed`). Affected artifacts: `claim-gates.parquet`, `results/gates/claims.csv`, `results/tables/claim-gates.csv`. **The dose-response gate outcome is not interpreted in this document.** Not fixed, not re-evaluated. |
| N2 | `family_dependence` gate vs Roadmap 31.2 | Gate pools per-family mean CTK over *all* experiments (including the permutation control and sensitivity experiments) and uses a point spread of at least 0.10. The Roadmap allows evidence across the two frozen family sets or family-level intervals. | Outcome is robust: spread 0.293 pooled, 0.339 primary set only, 0.362 primary plus replication. Wording in the claim is unaffected; the implementation scope is looser than the text. |
| N3 | `results/provenance/code.json` | Records revision e079972 (Stage F freeze). The promoted `claims.csv` was regenerated after the representation-limited wording change committed later (a61f0ed); the promotion ran on a working tree ahead of the recorded revision. | Provenance mismatch of one gate-wording field; no numeric evidence differs. Not changed. |
| N4 | `feature-novelty-explanation` outcome label | Gate returns `rejected` whenever the association does not pass and associations exist, even though the intervals span almost [-0.5, 1.0] with 7 and 8 families. Roadmap 32 reserves rejection for a resolved negative; the data are unresolved. | Label is stronger than the evidence. Report as unresolved/underpowered (Section 32). Gate not changed. |
| N5 | `results/tables/robustness.csv` vs paired effects | The robustness table reports the FedAvg CTK gain as pooled hits over pooled trials (micro), e.g. +0.066 for the primary set, while every other CTK figure is the primary paired estimand (+0.117). Both are labelled "complementary gain" without distinguishing the aggregation. The `robustness-summary` figure plots paired effects, not the table. | Two aggregations under one name; a reader comparing the table and figure will see different numbers for the same experiment. |
| N6 | `known-family-safety` promoted wording | Gate tests only the strongest federated arm (FedProx, -0.006). The primary decomposition arm FedAvg shows -0.033 (10 of 10 seeds negative) and FedAvg+fine-tuning -0.038. | "Supported in every evaluated scope" is broader than the evidence for FedAvg; see Section 27.3. Gate not changed. |
| N7 | README, "Commands and durations" | States "about 140 runs in roughly 2.5 hours". The logs give a confirmatory wall clock of about 83 minutes (1.4 h) and a summed run time of 3.0 h. | Stale/incorrect timing statement. The README also says the last eight experiments ran as five parallel workers, but part of `replication-family-set` ran sequentially. Not changed. |
| N8 | Roadmap H3 (section 6) | H3 expects generic pooling to explain "a substantial fraction" of the benefit while CTK is a separate positive component. For the MLP the pooling component is not substantial (share +0.11, CI [-0.39, +0.35]). | Hypothesis partly failed as the Roadmap allows (failure narrows the claim). The README and decision docs make no contrary statement. |
| N9 | `family-level` table, natural scarcity | `classification` shows `rescued` for every natural-scarcity family although that experiment has no full-exposure arm. | Rescue labels for natural scarcity are not meaningful (Section 24, A5). |
| N10 | `robustness-summary` figure | Rendering: 33 y-axis labels overlap vertically at the default figure height; the three partition salts share identical labels; the permutation control (a negative control, not a robustness scope) is drawn among the robustness rows. | Presentation defect; the figure should not be used as the sole robustness display. |
| N11 | Audit Matrix | Row "Confirmatory evidence" lists two non-structural warnings; a third arm value above 0.02 at the primary alpha (family-support-high, peer present, 0.0200) and 39 alpha-0.10 gaps are not mentioned. Other rows are consistent with this document (8 promoted, 1 narrowed, 3 rejected; 140 runs). | Minor omission; no numeric contradiction. |
| N13 | Own-domain claim vs permutation control | The null-compatibility rule (95% BCa interval within +/-0.03) is evaluated only on the federation-wide population. On the own-domain population the permuted FedAvg CTK interval is [-0.004, +0.036] at alpha 0.05 and [+0.010, +0.050] at alpha 0.10. | The promoted own-domain-benefit claim is not separately protected by a null-compatible control; the caveat belongs in its wording (Section 20, A12). Gate not changed. |
| N12 | Table and figure captions | `results/` tables and figures carry no captions or alpha/population annotations beyond figure titles and axis labels (for example the decomposition figure title says federation-wide; the tables state alpha only in a column). | Alpha and population must be carried by the prose; the tables are safe only when read with their column names. |

Checked and found consistent: run counts (140/140, 25/25, 11/11); seeds (100 to 109, 1 to 5, 0); claim counts (8 promoted, 1 narrowed, 3 rejected, 0 insufficient); the frozen hyperparameters (10, 2, 0.1) in the config, Roadmap 16.3 and the amendment log; the permutation rule (95% BCa within +/-0.03) in Roadmap, config and gate; alpha values in tables; no mix of own-domain and federation-wide columns was found in the generated tables; no stale claim statuses in the README or Audit Matrix.

## 36. Experiments That Would Likely Add Little Value

| Proposed experiment | Existing evidence that already addresses it | Expected incremental value | Recommendation |
|---|---|---|---|
| More seeds of `controlled-exposure` | Ten paired seeds already give intervals that exclude zero with 10/10 positive seeds; the seed spread (sd 0.047) is small relative to the effect | Very low | Skip |
| Additional partition salts | Three alternative salts already give +0.129, +0.131, +0.119 (all 10/10) | Very low | Skip |
| More operating points | Alpha 0.01, 0.05, 0.10 all show the effect and its growth with alpha | Low | Skip |
| A third model class of the same kind (another shallow classifier) | Linear and trees already show the sign is model independent and the composition is model dependent | Low | Skip unless a deep architecture is a reviewer request |
| Re-running the permutation control with more permutations | Interval [-0.007, +0.007] is inside the band by a factor above four; null at all three alphas | Low | Skip |
| A new collaboration mechanism | The trigger does not fire (headroom 0.049 and 0.029); representation limits, not collaboration limits, dominate the remaining errors | Negative (adds complexity) | Do not pursue |
| More hyperparameter tuning of the local, FedProx or fine-tuning baselines | Grid results are flat or monotone; selected values give the best calibration AUROC | Low | Skip; a centralized-epoch curve is the one optional addition |
| Repeating package-only grouping | No inflation observed (+0.107 against +0.117) | Very low | Skip |
| Another development-mode run of anything | Development evidence cannot support claims; confirmatory evidence exists | None | Skip |

## 37. Genuine Evidence Gaps

| Gap | Why it matters | Already partially addressed? | Best way to address it | New runs required? |
|---|---|---|---|---|
| External validity beyond LAMDA and AndroZoo | Every result rests on one dataset, one static 925-feature representation and four simulated domains | No | Independent Android dataset with family labels (post-confirmatory extension E4) | Yes |
| Dose-response gate specification (N1) | The narrowed outcome is a gate mechanics question and the dose curve is uninterpretable at requested labels (8% realisation) | Partly (curves exist on effective dose) | Resolve the gate question by a documented amendment before any interpretation; then, if needed, a fresh design with exact dose realisation (E2) | Only for E2 |
| Feature-novelty power | 7 and 8 families cannot resolve a moderate association (CI [-0.41, 1.0]) | Partly (consistent direction) | A dataset or design with many more labelled families, one predeclared descriptor (E3) | Yes |
| CTK versus pooling dominance is model dependent | The MLP shows CTK dominance, the linear model shows pooling dominance; no gate tests composition across models | Partly (Section 15) | Predeclared composition claim on fresh seeds (E1) | Yes |
| Own-domain evidence rests on few clients | Own-domain hidden-family support: `play-late` 6 of 10 seeds and 642 rows; two clients supply most rows; own-domain total gain small | Partly | Report per-client own-domain CTK (already in Section 14); a design with more own-domain support if pursued | Optional |
| FedAvg known-family cost mechanism | FedAvg loses 0.033 known-family recall, concentrated at `anzhi`; cause not investigated | No | Analysis of stored scores by client (no new runs) before any experiment | No for the analysis |
| Deep or larger models | Single MLP width and depth, untuned centralized and FedAvg budgets | Partly (linear and trees) | A single frozen alternative MLP as a replication (low priority) | Yes |
| Temporal deployment realism | Static split within a partition; no drift, no online updates | No | Out of scope for the current protocol; state as a limitation | Yes |
| Representation-limited families | Three families stay poor under full exposure; cause (features or labels) unknown | Partly | Feature-level diagnostics on stored data; not a collaboration experiment | No |

## 38. Possible Post-Confirmatory Extensions

**Every proposal below is a new hypothesis or extension motivated after seeing the current confirmatory evidence. It must use a separately frozen design and fresh untouched seeds and must not alter the original confirmatory claim outcomes.** None is recommended merely because it may produce a positive result.

| Extension | Motivation from current evidence | Exact new question | Suggested design | Fresh seeds required | Scientific value | Risk of post-hoc bias | Priority |
|---|---|---|---|---|---|---|---|
| E1 CTK-versus-pooling dominance | MLP shows CTK share +0.89 (CI [0.65, 1.39]) and pooling share +0.11; the linear model shows the opposite; the majority claim tested only pooling | Is the complementary share above one half for MLP FedAvg and centralized on both family sets, and does the composition depend on model class? | Predeclared criterion: complementary share interval above 0.5 and pooling share interval below 0.5, at least 8 of 10 seeds with CTK > pooling; primary and replication family sets; linear and trees as predeclared contrasts | 10 new seeds (for example a range not used so far) | High: converts a rejected one-sided claim into a stated result and resolves the model-dependence question | Post-hoc selection of the criterion; mitigated by predeclaration | Medium |
| E2 Dose-response with exact effective dose | Requested dose realised at about 8%; the gate outcome is unresolved (N1); the curve is still rising at the largest level | What is the effective peer exposure at which recall begins to rise and does it saturate? | Sample the requested dose after budget subsampling so that effective equals requested (or stratify the training subsample), levels at 5, 10, 25, 50, 100, 200, 400 effective peers, target at zero, FedAvg and centralized, primary family set | 10 new seeds | High if the gate discrepancy is resolved by amendment first; otherwise it repeats the same ambiguity | Level choice made after seeing the curve | Medium |
| E3 Feature-novelty with many more families | rho +0.57 and +0.33 with 7 and 8 families; consistent direction of distance descriptors | Does one predeclared training-only descriptor predict CTK gain with adequate power? | Requires a family universe of at least 25 eligible families (lower support thresholds or another dataset); one predeclared descriptor; no descriptor search | 10 new seeds; new family set | Medium | Fishing risk if more than one descriptor is examined | Low to medium |
| E4 Independent dataset replication | All evidence is one dataset and representation | Does the CTK/pooling decomposition and negative own-domain pooling gain appear on another Android family-labelled dataset? | Same protocol on an independent corpus with family labels; freeze before running | Fresh seeds; new data | High for external validity | Different labels and features change effect size; interpretation must be scoped | Medium |
| E5 Own-domain pooling penalty | Own-domain pooling gain is negative in 9 of 12 scopes (8 with intervals below 0) | Is the negative own-domain pooling gain a general effect of cross-domain pooling or specific to this design? | Predeclared contrast of pooling gain on the own-domain population, per client, with a control that removes cross-domain data | Fresh seeds | Medium (a bounded finding about domain shift) | Post-hoc emphasis | Low to medium |

## 39. Decision Support — Recommended Next Actions

### A. No-new-run improvements

| Action | Why | Evidence motivating it | New runs needed | Expected scientific value | Risk | Priority |
|---|---|---|---|---|---|---|
| Resolve gate discrepancy N1 by a documented protocol amendment (Roadmap 47) before interpreting the dose claim | The narrowed outcome is a gate mechanics artifact candidate | Sections 12, 34; N1 | No | High: removes the only unresolved confirmatory outcome | Amendment process must not be used to rescue a claim; decide the rule by reading the Roadmap text, then apply it to the stored evidence | 1 |
| Rewrite the four wordings in Section 27.3 (known-family, complementary, collaboration, pooling) | Wording is broader or narrower than the evidence | Sections 9, 15, 27.3 | No | High | Must stay within the gates | 2 |
| Add the robustness forest plot, composition plot and per-client figures (Section 27) | The current robustness figure is unreadable (N10) and hides model-class composition | Sections 15, 19, N10 | No | Medium | None | 3 |
| Correct the README timing sentence (N7) and the provenance note (N3); document N4, N5, N9, N11 | Stale statements | Section 35 | No | Low-medium | None | 4 |
| Add an appendix with the run reconciliation, warnings table and alpha 0.10 deviations | Traceability and honesty about seed 106 | Sections 4, 24 | No | Medium | None | 5 |
| Analyse the FedAvg known-family cost per client from stored scores | Cause is unexplained | Section 14 | No | Medium | Descriptive only | 6 |
| Position the work using the Roadmap section 33 list and run the citation-chaining audit before any novelty wording | Roadmap requires it | Section 28 | No | High for submission | None | 7 |

### B. New fresh-seed extensions (only when scientifically justified)

| Action | Why | Evidence motivating it | New runs needed | Expected scientific value | Risk | Priority |
|---|---|---|---|---|---|---|
| E1 CTK-versus-pooling dominance | New question: Is the complementary share above one half for MLP FedAvg and centralized on both family sets, and does the composition depend on model class? | MLP shows CTK share +0.89 (CI [0.65, 1.39]) and pooling share +0.11; the linear model shows the opposite; the majority claim tested only pooling | Yes | High: converts a rejected one-sided claim into a stated result and resolves the model-dependence question | Post-hoc selection of the criterion; mitigated by predeclaration | Medium |
| E2 Dose-response with exact effective dose | New question: What is the effective peer exposure at which recall begins to rise and does it saturate? | Requested dose realised at about 8%; the gate outcome is unresolved (N1); the curve is still rising at the largest level | Yes | High if the gate discrepancy is resolved by amendment first; otherwise it repeats the same ambiguity | Level choice made after seeing the curve | Medium |
| E3 Feature-novelty with many more families | New question: Does one predeclared training-only descriptor predict CTK gain with adequate power? | rho +0.57 and +0.33 with 7 and 8 families; consistent direction of distance descriptors | Yes | Medium | Fishing risk if more than one descriptor is examined | Low to medium |
| E4 Independent dataset replication | New question: Does the CTK/pooling decomposition and negative own-domain pooling gain appear on another Android family-labelled dataset? | All evidence is one dataset and representation | Yes | High for external validity | Different labels and features change effect size; interpretation must be scoped | Medium |
| E5 Own-domain pooling penalty | New question: Is the negative own-domain pooling gain a general effect of cross-domain pooling or specific to this design? | Own-domain pooling gain is negative in 9 of 12 scopes (8 with intervals below 0) | Yes | Medium (a bounded finding about domain shift) | Post-hoc emphasis | Low to medium |

### C. Work to avoid

- Changing the failed or narrowed gates, thresholds or practical-effect bounds to rescue a claim.
- Replacing or dropping families or seeds after seeing outcomes (for example dropping `adwo` or seed 106).
- Searching many novelty descriptors until one correlates.
- Adding a new federated mechanism (no headroom).
- Repeating experiments that already answer the same question (Section 36).
- Presenting development numbers as confirmatory findings.
- Reading the dose gate outcome in either direction before N1 is settled.

## 40. Suggested Final Scientific Story

Ranked only by coherence with the evidence, scientific defensibility, novelty potential and additional work — not by how positive they sound.

| Narrative | Central contribution and strongest supporting results | Important negative findings | Novelty angle | Limitations / evidence still missing | Additional work |
|---|---|---|---|---|---|
| 1. A measured decomposition of federated malware detection gains under controlled family exposure | Under a fixed 5% FPR the MLP collaboration gain is complementary (+0.117) rather than generic (+0.014); it holds for the worst client (+0.173) and the own domain (+0.107) while generic pooling hurts the own domain (-0.069); it replicates in direction on a disjoint set (+0.064), across linear and tree models, salts, operating points and support levels; a permutation control is null | Pooling not the majority for the MLP (bound 0.35); no mechanism headroom; feature novelty unresolved; FedAvg known-family cost 0.033; three representation-limited families; effect size and composition depend on family set and model class | A matched-control decomposition method plus a bounded empirical characterisation (subject to the citation audit) | Single dataset and representation; dose-response unresolved; own-domain support thin | Low: wording, figures, N1 amendment |
| 2. Collaboration value is family dependent and bounded by representation | Range of family CTK gains +0.003 to +0.343; three families stay below 0.60 under full exposure in two model classes; novelty direction consistent but underpowered | Replication effect halves; pooling composition varies by model | Family-level rescue and ceiling analysis as the contribution, decomposition as support | Family-level intervals absent; only 15 families | Low to medium: family-level intervals, per-client analysis |
| 3. A negative-result-forward chapter: standard collaboration is sufficient | No mechanism headroom (0.049, 0.029), no CTK-specific mechanism justified, feature novelty unresolved, dose unresolved; the positive result is that peers matter for specific families | Same numbers as story 1, framed around what is not needed | Explicit bounds on when a new mechanism is unjustified | Weaker on novelty; depends on the static representation; dose left open | Low |

Story 1 is the one the evidence supports most directly; stories 2 and 3 are compatible with it and can be chapters within it. Stories are ranked 1 > 2 > 3 by coherence and defensibility, and 1 > 3 > 2 by amount of extra work.

## 41. Complete Artifact Index

| Conclusion | Experiment plan | Run directory / metric artifact | Analysis artifact | Statistical / gate artifact | Result table | Figure |
|---|---|---|---|---|---|---|
| Run counts (140 confirmatory, 25 development, 11 smoke) | `outputs/plans/<mode>/run-matrix.parquet` | `outputs/runs/<mode>/<experiment>/seed-N[-salt-K]/{status,manifest,validation}.json` | - | - | `results/gates/seed-status.csv` | - |
| Primary decomposition (total, pooling, CTK, shares, oracle gap) | `outputs/plans/confirmatory/run-matrix.parquet` | `outputs/runs/confirmatory/controlled-exposure/seed-*/metrics/summary.parquet` | `outputs/analysis/confirmatory/collaboration-decomposition.parquet` | `outputs/statistics/confirmatory/paired-effects.parquet` | `results/tables/collaboration-decomposition.csv` | `results/figures/collaboration-decomposition.png` |
| Primary arm levels and headline metrics | same | `.../metrics/{summary,clients,families,discrimination,operating-points}.parquet` | `outputs/analysis/confirmatory/arm-metrics.parquet` | - | `results/tables/primary-arm-comparison.csv` | `results/figures/mean-versus-worst-client.png`, `own-domain-versus-federation-wide.png`, `known-versus-unseen-tradeoff.png` |
| Dose response | same | `outputs/runs/confirmatory/peer-dose-response/seed-*/{metrics,exposure.parquet}` | `outputs/analysis/confirmatory/peer-dose-response.parquet` | `claim-gates.parquet` (dose row) | `results/tables/peer-dose-response.csv` | `results/figures/peer-dose-response.png` |
| Family-level results and rescue status | same | `.../metrics/families.parquet`, `novelty.parquet` | `outputs/analysis/confirmatory/family-rescue.parquet` | - | `results/tables/family-level.csv` | `results/figures/family-rescue-map.png` |
| Feature novelty | same | `outputs/runs/confirmatory/{controlled-exposure,replication-family-set}/seed-*/novelty.parquet` | `outputs/analysis/confirmatory/feature-novelty.parquet` | `claim-gates.parquet` | `results/tables/claim-gates.csv` | `results/figures/feature-novelty-versus-ctk-gain.png` |
| Robustness, sensitivities, salts, models | same | `outputs/runs/confirmatory/<experiment>/...` | `outputs/analysis/confirmatory/robustness.parquet` | `paired-effects.parquet` | `results/tables/robustness.csv` | `results/figures/robustness-summary.png` |
| Permutation control | same | `outputs/runs/confirmatory/family-permutation-control/...` | `collaboration-decomposition.parquet` | `paired-effects.parquet`, `claim-gates.parquet` | `results/tables/claim-gates.csv` | `results/figures/robustness-summary.png` |
| Gate outcomes and claims | - | - | - | `outputs/statistics/confirmatory/claim-gates.parquet` | `results/gates/claims.csv`, `results/tables/claim-gates.csv` | - |
| Cluster bootstrap | - | `.../scores/*.parquet`, partitions | - | `outputs/statistics/confirmatory/cluster-bootstrap.parquet` | - | - |
| Development evidence and fairness selection | `outputs/plans/development/run-matrix.parquet` | `outputs/runs/development/...` | `outputs/analysis/development/{arm-metrics,fairness-selection,...}.parquet` | `outputs/statistics/development/*.parquet` | - | - |
| Runtime | - | `outputs/logs/run.jsonl` (`run-finished`) | - | - | - | - |
| Provenance | - | `results/provenance/{protocol,code,environment,source-data}.json`, `results/manifest.json` | - | - | - | - |

Report tables and figures for each mode are also under `outputs/report/<mode>/`. The promoted `results/` tree is the confirmatory subset and is byte-identical to the `outputs/` sources for the parquet files.
