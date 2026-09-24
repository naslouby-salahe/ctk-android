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

## 2026-09-24 - Post-confirmatory reassessment: correctness fixes and evidence-preserving analyses (Roadmap 20, 21, 28, 31.3, 39, 38 Stage L)

Scope statement: no original confirmatory arm, threshold, seed, family set, hyperparameter, or gate was changed. No run was retrained; every number below was recomputed from the stored confirmatory artifacts. Fresh seeds are not required. Roadmap text before this amendment has fingerprint 09a329281b63debcf29cd1c17c3ef519d38d14a717bf75314f53870957f36854 (recorded in the earlier `results/provenance/protocol.json`).

### Implementation defects corrected (the rule was already in the Roadmap)

1. Dose-response gate (Roadmap 20, 31.2). Old outcome: NARROWED, 1 of 3 criteria. Defect: the level table was filtered with `dose is not null`, which silently dropped the `all available` level (its requested dose is null), so the only level whose mean effective exposure reaches 100 peer samples (296.2) was never tested; the family-robustness test additionally used a different, row-level, exposure filter restricted to the 1000 level. Requested dose 100 realises a mean of only 9.0 effective samples and requested 1000 realises 79.4, so the criterion was unreachable under the old code. Correction: levels are grouped including the null-dose level, ordered by mean effective exposure, and the criterion, monotonicity and family-robustness tests all use the same qualifying levels. Thresholds (100 samples, +0.03, monotone tolerance 0.02) are unchanged. Corrected outcome: PROMOTED, 3 of 3 (all-available level: CTK gain 0.124 over zero dose; leave-one-family-out mean at least 0.089; recall non-decreasing within tolerance). An observation-level reading of the same criterion (the 70 FedAvg family-seed rows with at least 100 effective samples) also passes (mean gain 0.045; leave-one-family-out at least 0.040), so the outcome does not depend on the level-versus-observation ambiguity. Roadmap 20 now states the semantics. Affected artifacts: `claim-gates`, `peer-dose-response` table (now level-based with the all-available level labelled). Regression tests fail under the old implementation.
2. Family-dependence gate scope (Roadmap 31.2). Defect: FedAvg family gains were averaged across every experiment (natural scarcity, permutation control, sensitivities, dose runs), not the frozen family sets. Correction: only the primary (controlled-exposure) and replication family sets are used, threshold 0.10 unchanged. Outcome unchanged (PROMOTED): spread across the 15 frozen-set families is 0.362 (primary set 0.339, replication set 0.185). Regression tests added.
3. Micro-pooled robustness (Roadmap 28). Defect: the partition-salt sensitivity pooled its three salts as 30 pseudo-seeds (seed_count 30). Correction: salts are separate rows with 10 seeds each. The column previously called `mean_difference` is `micro_pooled_ctk_gain` with an `aggregation` label; the seed-paired estimand keeps its own name. Values for non-salt rows are unchanged.
4. Family-level table for natural scarcity classified every family as rescued when no full-exposure arm exists; it now reads not-classifiable.
5. Known-family-safety wording. Gate mechanics unchanged (strongest federated arm, as written). The stored wording now states that support is for the strongest federated arm only; arm-specific changes are tabulated.
6. Non-deterministic reporting order. Family-level novelty scores were averaged and correlated in a hash-dependent family order, so the feature-novelty bootstrap interval and 1e-15 float noise changed between regenerations (replication-set interval endpoints moved by up to 0.025; rho, p-values and the gate outcome did not). Scores are now ordered by family and the primary-arm table has a fixed column order. Stored rho, p-values, gate outcomes, seed-level metrics and all paired effects are bit-identical to the first promotion; only the feature-novelty bootstrap endpoints and micro-pooled BCa endpoints (resampling order, fourth decimal) differ.
7. Provenance. `results/provenance/code.json` recorded git HEAD (e079972, the freeze commit) while the working tree already contained the representation-limited wording change later committed in a61f0ed. Effect: wording only; no numeric evidence or gate outcome depended on it. Provenance now records `execution_revision` (last commit at or before the first confirmatory run was written; runs were written 19:44 to 21:05 on 2026-09-24; training-relevant code is identical between dccf996, e079972), `analysis_revision` (HEAD when analysis ran) and `analysis_sources_clean`. Historical revision values are not rewritten.

### Roadmap changes

| Section | Old intent | New wording | Reason | Changes a scientific degree of freedom | Changes an original result | Fresh seeds |
|---|---|---|---|---|---|---|
| 20 | Effective count is reported | Requested versus effective dose, all-available semantics | Ambiguity behind defect 1 | No (criteria unchanged) | Dose gate outcome corrected by defect 1 | No |
| 21 | Natural scarcity validates, not pooled | Named the principal external check; still not merged or gated | Clarify role | No | No | No |
| 28 | Robust = survives checks | Robust = persistence of sign and practical magnitude, not identical proportions | Clarify | No | No | No |
| 31.3 (new) | none | Evidence classes A to D; post-confirmatory analyses; arm-specific known-family wording; feature-novelty non-passage is unresolved, not disproven; bounded generic-pooling statement for the primary MLP; own-domain permutation caveat; family-dependence scope | Interpretation and reporting discipline | No | No | No |
| 38 Stage L, 39 | Publication figures | Includes post-confirmatory class C tables and figures; forest plot replaces the overlapping robustness figure | Reporting | No | No | No |

New class C analyses (evidence-preserving, existing runs only): local-baseline-anchored worst client, federated-arm trade-off, canonical robustness synthesis, family-level mechanism patterns, natural-scarcity side-by-side, permutation-control audit by population and alpha, mechanism headroom table, operating-point fidelity table.

## 2026-09-24 - Wording corrections, per-client analysis and novelty positioning (Roadmap H5, 20, 21, 31.3, 33, 42)

Scope statement: wording and class C additions only. No original confirmatory arm, threshold, seed, family set, hyperparameter or gate was changed; no original confirmatory number changed; no model was trained; no new seeds are required. Each row below: scientific degree of freedom changed: no; original result changed: no; fresh seeds: no.

| Section | Previous wording | New wording | Reason | Evidence source |
|---|---|---|---|---|
| 21 (and the 2026-09-24 amendment row for 21) | Natural scarcity is "the principal external check" of the controlled-exposure phenomenon | Principal within-dataset (ecological) validation; same LAMDA/AndroZoo corpus; not independent-dataset or external validation | Natural scarcity uses the same corpus; calling it external overstated it | `natural-scarcity-comparison.csv` (numbers unchanged) |
| 31.3 C | "elevated as validation of the controlled-exposure phenomenon" | "elevated as within-dataset (natural-exposure) validation ... not external validation" | Same | same |
| 42 Limited external replication | natural scarcity listed among internal replications | annotated as within-dataset | Same | none needed |
| H5 | single sentence: increase and diminishing returns | H5 declared compound; the dose gate tests only the increase; saturation unresolved | The promoted gate does not establish saturation; recall still rises at the largest effective exposure | `peer-dose-response.csv` (recall 0.437 to 0.562, no plateau) |
| 31.3 M (new) | none | Dose interpretation: increase supported, saturation not established | Keep the two parts of H5 apart | same |
| 31.3 L (new) | none | Per-client CTK analysis, class C, descriptive, no gate, interval only with at least 8 contributing seeds | Missing client-level evidence | `client-ctk-analysis.csv` from stored client metrics |
| 31.3 N (new), 33 | Pre-submission citation-chaining audit only | Bounded audit performed; no direct collision, three partial; "no closely matching study found in the audited literature" wording only; audit limits stated | Literature collision audit | `docs/Novelty Audit.md` |

The formal-interval rule in the per-client analysis reuses the existing `ctk_min_positive_seeds` value (8) as a minimum contributing-seed count; no new threshold is introduced, and rows below it are reported descriptively without an interval.

## 2026-09-25 - Per-client interval rule corrected (Roadmap 31.3 L)

Problem: the per-client analysis showed a BCa interval only for clients with at least 8 contributing seeds, justified by the gate's 8-of-10 positive-seed rule. That rule has nothing to do with whether a bootstrap interval is appropriate; it was an arbitrary and mis-justified reuse.
Correction: all clients are reported with their number of contributing seeds; intervals are labelled exploratory small-n BCa intervals and are shown whenever the existing helper can compute them (at least 3 seeds, non-constant effect), otherwise omitted (`interval-omitted-not-computable`). No threshold is used. The implementation requirement of the helper is documented separately from the scientific reading (intervals with 6 to 10 seeds and unequal support are unstable and are descriptive).
Effect: point estimates for every client are unchanged (maximum absolute difference 0.0); play-late now shows exploratory intervals (federation-wide CTK 0.328, 0.224 to 0.431). No original confirmatory result, gate, threshold, seed or family set changed; the analysis remains class C; no new seeds are required; no scientific degree of freedom changed.

## 2026-09-25 - Novelty positioning narrowed after the deeper audit; external-validity wording (Roadmap 33, 42, 31.3 L, N)

Wording only. Scientific degree of freedom changed: no. Original confirmatory result changed: no. Fresh seeds required: no.

| Section | Previous wording | New wording | Reason | Evidence source |
|---|---|---|---|---|
| 31.3 L | Per-client intervals "shown whenever the helper can compute one" (after the 2026-09-25 correction) | Adds that this is an implementation requirement, not a scientific threshold, and that intervals with 6 to 10 seeds are unstable and descriptive | Avoid implying precision | `client-ctk-analysis.csv` |
| 31.3 N, 33 | First audit: no direct collision, three partial | Second audit: no direct collision, four partial (adds Bi et al.); dose and natural scarcity described as partially anticipated; audit limits stated | Deeper reading of seven papers in full plus forward/backward chaining | `docs/Novelty Audit.md` |
| 42 Limited external replication | Independent validation named as the remedy | Adds the feasibility finding: no publicly verified independent corpus meets all requirements; replication is optional and gated on a support pre-check | Desk assessment of candidate datasets, none downloaded | `docs/Second Dataset Feasibility.md` |
