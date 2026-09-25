# CTK-Android Research Evidence

Every number below is read from the machine-readable artifacts in `results/` (promoted from `outputs/`), produced by the analysis code at the revision named in section 2. Nothing was retrained for this document. Evidence classes are labelled throughout:

- **[A]** original confirmatory evidence (predeclared experiment and gate);
- **[B]** predeclared confirmatory robustness or sensitivity evidence;
- **[C]** post-confirmatory evidence-preserving analysis of already-generated data (not a preregistered claim);

"CTK" is the complementary-threat-knowledge gain: recall with the family present at peers minus recall when the family is absent everywhere, for the same learner. Confidence intervals are 95% BCa over the 10 confirmatory seeds (100 to 109) unless stated; "positive seeds" counts seeds with a gain above zero. The practical threshold is +0.03 absolute recall.

- **[D]** new prospective extension: separately frozen protocol, fresh seeds (200 to 209 for EXT-1; 300 to 309, 310 to 319, 320 to 329 and 330 to 339 for the four extension-b studies), never pooled with the original seeds or with each other and never counted in the original 9/0/3 gate outcome. Positioning and feasibility material (literature, datasets) is also labelled [D] and contains no experimental result.

Structure: sections 1 to 27 are the original evidence (class A/B, with class C analyses in 5.1, 9, 12, 12.1, 14 and 14.1); 28 is the reviewer-gap matrix; 29 to 32 are literature and dataset feasibility; 33 holds the prospective extensions (register, results in 33.2, diagnostics in 33.4, proof-of-concept decisions in 33.3); 34 to 39 are open gaps, decision support including the final experiment assessment, claims, story, limitations and the artifact index.

## 1. Executive Scientific Summary

Evidence classes are defined at the top of this document. Every number is read from the machine-readable artifacts in `results/` (promoted from `outputs/`).

1. **Collaboration helps locally unseen families [A].** Local unseen-family recall is 0.507 (federation-wide, 5% FPR); FedAvg reaches 0.638 (+0.132, CI 0.090 to 0.167, 10/10 seeds). Full-exposure central training reaches 0.708 (local deficit 0.201, CI 0.164 to 0.231).
2. **For the primary MLP with controlled exposure, the gain is dominated by complementary peer-held family knowledge, not generic pooling [A/B].** CTK +0.117 (0.090, 0.145), 10/10 seeds, Holm p = 0.0059; pooling +0.014 (-0.038, 0.054); CTK share 0.89 (0.65, 1.39), pooling share 0.11 (-0.39, 0.35). Not general: natural scarcity, lower training support and the linear model have pooling shares of about one half or more (sections 6, 10, 16, 18).
3. **The CTK effect persists in sign and practical magnitude** across own-domain (+0.107), worst client (+0.173), family-macro (+0.124), natural scarcity (+0.113), a disjoint family set (+0.064), linear (+0.094) and tree (+0.102) models, both support levels, three operating points, three salts and package-only grouping [A/B]. Excluding negative-control rows, 269 of 276 paired-seed rows and all 33 micro-pooled rows exceed +0.03; the seven exceptions are worst-client estimates at 1% FPR.
4. **The own-domain null control is unresolved in v1 and resolved prospectively in EXT-1 [A/D].** The original own-domain permutation interval extended past +0.03; in a separately frozen extension with fresh seeds 200 to 209 (EXT-1) the own-domain FedAvg permutation CTK at 5% FPR is +0.006 (-0.004, 0.014), inside the equivalence band. Never pooled with the original seeds (sections 20.1, 22).
5. **CTK heterogeneity: largest estimated share between families federation-wide, between clients own-domain [C, descriptive].** In a family x client x seed REML decomposition of the primary set, the family component is estimated at 63% of federation-wide CTK variance (seed-bootstrap 36 to 78%; client 7%, seed 2%) but only 15% of own-domain variance, where the client component is estimated at 59% (15 to 89%, four clients); in the replication set no component dominates and family-by-client plus residual carry most variance. Four clients, 22 (client, family) cells (section 12.1). Where pooling is negative, part of positive CTK is numerically offset by the negative pooling in the same cell (an accounting split, not a causal mechanism; section 5.1).
6. **Known-family cost is arm- and client-specific [A/C].** FedProx, the strongest arm, changes known-family recall by -0.006 (within ±0.02); FedAvg (-0.033) and fine-tuning (-0.038) exceed it; the loss is largest at anzhi (-0.065) and play-late (-0.037) for FedAvg and moves to play-early (-0.029) for FedProx.
7. **Aggregate metrics mask the unseen-family gain [C].** FedAvg lowers aggregate AUROC by 0.012 (0.009 to 0.016) and AUPRC by 0.020 versus local while federation-wide unseen-family recall rises by 0.132; in the primary set 6 of 16 arm/metric contrasts on federation-wide recall (all against local) are flagged as a masked gain and none as a masked loss; the replication set flags 9 of 16 (15 rows, 8 distinct recall contrasts; section 14.1).
8. **Dose-response gate: corrected from NARROWED to PROMOTED (implementation defect) [A]; prospective exact dose [D].** Recall rises with effective exposure (0.437 to 0.562; section 11). With exactly 10 to 200 peer samples (seeds 310 to 319) FedAvg CTK rises 0.031, 0.050, 0.075, 0.119, 0.151. The curve is consistent with diminishing marginal returns, but no plateau is observed through 200 samples. Families differ in dose requirement: six respond by 10 to 25 samples, five need 50 to 100 and four do not respond at 200; natural peer exposure is worth about 90 exact samples (33.2, 33.4).
9. **Feature novelty is unresolved in the original gate [A]; a modest, imprecise association in a prospective 32-family study [D].** Original: Spearman 0.57 (7 families) and 0.33 (8 families), intervals span zero; stored status "rejected". Prospective (seeds 300 to 309): rho 0.392 (family-bootstrap CI 0.062 to 0.654), permutation p 0.026. Removing any one of the five incompletely eligible families leaves rho 0.349 to 0.388; three are among the five strongest positive influences. The 27-always-eligible sensitivity is rho 0.274 (CI -0.099 to 0.581), so the positive point estimate is not dependent on one incomplete family, while precision is weaker in the stable-eligibility subset. Headroom (full exposure minus local recall) is a stronger family-level correlate (0.52) than the novelty descriptor (33.2, 33.4).
10. **No headroom for a new federated mechanism [A]; representation limits are family-specific [D].** Several families stay poorly recalled under full exposure in several model classes. In a same-application replication (EXT-REP, seeds 330 to 339) richer McNdroid static features raise full-exposure recall of the priority families (+0.082), gappusin (+0.146) and adwo (+0.328) and raise CTK (+0.070); these gains keep lower bounds above zero at exactly 5% test FPR (33.4). No hiddad rescue is demonstrated: McNdroid static remains unresolved, while call-graph and report-JSON representations do not rescue it. Not external validation.
11. **Original gate counts: 9 promoted, 0 narrowed, 3 rejected, 0 insufficient** (the original promotion recorded 8/1/3). No extension outcome changes these counts.
12. **Literature: no direct collision (41 rows: 0 DIRECT, 4 PARTIAL, 34 ADJACENT, 3 NONE).** CyberForce already has an unmatched federated absent-everywhere arm, a peer-holder sweep, local curves and robust aggregators on the absent malware; CELEST, FLEKD-IDS and Shao/Otani et al. show local-versus-federated or missing-mass contrasts on a missing class. Popoola et al. report class-specific federated results but do not report a local-only result on the locally missing class, so they are ADJACENT under the identification-based rule. Not found: the volume-matched decomposition into generic pooling and family-specific transfer with own-domain, worst-client, exact-dose, placebo and natural-scarcity evaluation (section 29). FID-SPA and FEDroid remain unavailable for full-text assessment.
13. **No independent Android corpus with a real client axis is available.** KronoDroid is MARGINAL (era-confounded clients); McNdroid overlaps LAMDA by 81%; MH-1M, Hypercube, APIGraph, AndroCT and Droidware lack a market or source axis; an AndroZoo-markets replication on markets outside LAMDA's four is possible in principle but not independent of the source (sections 30 to 32, 35.1).
14. **The gain is family-specific [D].** No placebo stratum shows a materially positive effect; the largest positive point estimate is about +0.014, while the pooled federation-wide placebo is -0.001 (-0.008, 0.006). Peer reallocation (36% of rows) does not change this. CTK exceeds the placebo by +0.095 (0.079, 0.116) (33.2, 33.4).
15. **Robust aggregation does not erase the rare peer in the primary set [D].** Trimmed-mean CTK is within 0.020 of mean CTK in every primary-set stratum; replication-set and some own-domain strata fail the frozen non-inferiority margin, mostly through seed-to-seed spread; families held by one peer have low CTK under every aggregator, so rare-peer erasure is not supported (33.2, 33.4).
16. **CTK is concentrated in a reproducible family core [C].** Family CTK ranks agree between the confirmatory study and 32 fresh families (Spearman 0.86 to 0.89); 21 of 32 fresh families have CTK above zero and one below. Aggregate AUROC/AUPRC fall while unseen-family recall rises (section 14.1).

## 2. Evidence Provenance

- Data: LAMDA release `var_thresh_0.01` (fingerprint `e9908f9a…677a9`) with AndroZoo metadata (`f0d11873…97904`); 1,008,381 rows, 925 binary features. Source: `results/provenance/source-data.json`.
- Protocol: frozen before any confirmatory seed (`docs/decisions/protocol-amendments.md`, Stage F); configuration fingerprint recorded in `results/provenance/protocol.json`. The Roadmap was amended after the campaign (Roadmap 20, 21, 28, 31.3, 38, 39); the amendment log states that no arm, threshold, seed, family set, hyperparameter or gate changed.
- Code provenance (`results/provenance/code.json`) now separates three revisions: **execution** `e079972` (freeze commit; training-relevant code identical to `dccf996`; runs were written 19:44 to 21:05 on 2026-09-24), **analysis/promotion** = the revision recorded in that file, with `analysis_sources_clean: true`, and **final reporting** = the commit containing this document. An earlier promotion recorded `e079972` while the working tree already held a wording-only change to the representation-limited claim; that affected wording only, not numbers or outcomes.
- Post-hoc class C analyses added after the extension (5.1, 12.1, 14.1) are recomputed from the stored runs by the `posthoc` workflow (section 39); they use the same frozen family sets, alpha and seeds and change no original estimate.
- Environment: `results/provenance/environment.json` (Python 3.12.3, torch 2.14.0+cu130, CUDA).
- Determinism: regenerating the promotion twice yields byte-identical evidence parquet and CSV tables; PDF figure bytes differ (embedded metadata), so `manifest.json` digests of PDFs change between regenerations. Fixing a family-ordering bug made the feature-novelty and micro-pooled bootstrap intervals reproducible; rho, p-values, means and gate outcomes are unchanged relative to the first promotion.

## 3. Experiment and Run Inventory [A/B]

140 of 140 planned confirmatory runs completed (no failed validation, none infeasible, none stale; `results/gates/seed-status.csv`):

| Experiment | Runs | Role |
|---|---|---|
| controlled-exposure | 10 | primary decomposition (A) |
| peer-dose-response | 10 | dose gate (A) |
| natural-scarcity | 10 | validation (B) |
| family-permutation-control | 10 | negative control (A) |
| replication-family-set | 10 | disjoint family set (A) |
| model-family-replication-linear / -trees | 10 + 10 | model classes (B; trees have local and central arms only) |
| training-support-sensitivity | 10 | 1,500 rows/client (B) |
| family-support-sensitivity-low / -high | 10 + 10 | eligibility thresholds (B) |
| partition-salt-sensitivity | 30 | salts 1, 2, 3 × 10 seeds (B) |
| package-only-grouping | 10 | weaker grouping (B) |

Clients (`results/tables/dataset-client-audit.csv`): anzhi (104,287 rows, 90,801 malware), appchina (88,282; 73,578), play-early (319,122; 75,985), play-late (320,474; 17,200). Primary set: 7 hidden families (adwo, airpush, dowgin, gappusin, hiddad, leadbolt, revmob); replication set: 8 (dnotua, domob, inmobi, kuguo, smsreg, utchi, youmi, zdtad). Operating point: every group reaches a valid operating point; the mean realised FPR deviates from the target by at most +0.002, +0.004 and +0.007 at 1%, 5% and 10% targets (`operating-point-fidelity.csv`).

## 4. Primary Controlled-Exposure Results [A]

Seed-mean recall, 5% FPR (`primary-arm-comparison.csv`):

| Arm (peer-present) | Fed.-wide unseen | Own-domain | Worst client | Known family |
|---|---|---|---|---|
| local | 0.507 | 0.499 | 0.279 | 0.729 |
| FedAvg | 0.638 | 0.537 | 0.425 | 0.696 |
| FedProx | 0.646 | 0.558 | 0.380 | 0.722 |
| FedAvg + fine-tune | 0.614 | 0.505 | 0.407 | 0.691 |
| blend | 0.634 | 0.571 | 0.373 | 0.746 |
| central | 0.659 | 0.555 | 0.411 | 0.729 |
| central, full exposure | 0.708 | 0.663 | 0.454 | 0.728 |

Realised FPR stays within 0.0009 of local for every arm. Total gain of FedAvg over local: +0.132 (0.090 to 0.167, 10/10; own-domain +0.038, 8/10; worst client +0.146, 10/10). Oracle-gap recovery (share of the local-to-full gap closed): 0.63 (0.48 to 0.77) federation-wide, 0.23 (0.07 to 0.39) own-domain, 0.75 (0.42 to 1.03) worst client. The own-domain recovery is small: most of the own-domain deficit remains.

## 5. Collaboration Decomposition [A]

FedAvg, 5% FPR, seed-paired macro estimand (`collaboration-decomposition.csv`, `paired-effects.parquet`):

| Population | Total gain | Pooling gain (no-family minus local) | CTK gain | CTK share | Pooling share |
|---|---|---|---|---|---|
| Federation-wide | 0.132 (0.090, 0.167) | 0.014 (-0.038, 0.054) | **0.117 (0.090, 0.145)**, 10/10 | 0.89 (0.65, 1.39) | 0.11 (-0.39, 0.35) |
| Own-domain | 0.038 (0.015, 0.062) | -0.069 (-0.108, -0.040) | 0.107 (0.068, 0.144), 10/10 | 2.83 (1.88, 6.71) | -1.83 (-5.71, -0.88) |
| Worst client | 0.146 (0.080, 0.240) | -0.026 (-0.080, 0.013) | 0.173 (0.116, 0.242), 10/10 | 1.18 (0.91, 1.81) | -0.18 (-0.81, 0.09) |
| Family-macro | 0.104 (0.066, 0.139) | -0.020 (-0.062, 0.017) | 0.124 (0.102, 0.153), 10/10 | 1.19 (0.86, 1.89) | -0.19 (-0.89, 0.14) |

A share above 1 means the generic-pooling component is negative: pooling without the family lowers recall on it (negative transfer) and peer-held family knowledge more than repairs that. Centralized reference: CTK 0.131 (0.086, 0.181). A cluster bootstrap over test-row components, computed within each seed, gives a federation-wide FedAvg CTK interval whose lower bound is above zero in all 10 seeds (lowest 0.016; `cluster-bootstrap.parquet`). Alpha 0.01 and 0.10 give CTK +0.076 (0.037, 0.125) and +0.134 (0.110, 0.164).

### 5.1 Negative transfer: repair versus new capability [C]

Post-confirmatory, exploratory (`negative-transfer-decomposition.csv`; definitions in `src/ctk_android/analysis/hidden_family.py`). Unit: one (client, hidden family) cell within a seed, FedAvg, 5% FPR, frozen family sets. Pooling gain = family-absent-everywhere minus local recall; CTK = peer-present minus family-absent-everywhere; a cell is *hurt* when pooling is negative. Repair = min(max(CTK, 0), max(-pooling, 0)) is the part of a positive CTK that only returns recall lost to negative pooling; new capability = max(CTK, 0) minus repair; harm = min(CTK, 0); repair share = repair / (repair + new capability). Cells are averaged within each seed and summarised over the 10 seeds with BCa intervals. Cell-mean CTK (0.124 federation-wide, 0.109 own-domain) differs slightly from section 5 because cells are equally weighted.

| Set, population | Pooling gain (hurt seeds) | Repair | New capability | Harm | Repair share |
|---|---|---|---|---|---|
| Primary, federation-wide | -0.020 (-0.062, 0.017), 5/10 | 0.033 (0.020, 0.054) | 0.093 (0.075, 0.129) | -0.002 | 0.26 |
| Primary, own-domain | **-0.062 (-0.102, -0.022)**, 7/10 | 0.070 (0.047, 0.113) | 0.049 (0.029, 0.072) | -0.009 | 0.59 |
| Replication, federation-wide | +0.013 (-0.021, 0.043), 2/10 | 0.024 (0.014, 0.036) | 0.053 (0.036, 0.075) | -0.008 | 0.31 |
| Replication, own-domain | -0.008 (-0.045, 0.061), 6/10 | 0.024 (0.013, 0.037) | 0.051 (0.031, 0.089) | -0.017 | 0.32 |

- **Federation-wide, most of CTK is new capability** (share of repair 0.26 primary); **own-domain, 0.59 of truncated positive CTK falls in the repair accounting bound** (primary), coinciding with cells where own-domain pooling was negative. This is an accounting split of observed differences, not a causal repair mechanism; truncation at zero inflates both repair and new capability under test-sampling noise (a binomial-noise null gives own-domain new capability of about 0.03 versus 0.049 observed).
- **By client (primary set):** pooling is negative at play-late own-domain (-0.275, -0.520 to -0.063, 6 seeds) and at anzhi federation-wide (-0.090, -0.150 to -0.032, 8 seeds); replication anzhi is also negative in both populations (-0.069 and -0.077, intervals below zero), whereas replication play-late has a positive pooling gain in both populations (+0.141 and +0.149, intervals above zero, 9 seeds). Elsewhere intervals span zero.
- **By cell:** in the primary set 11 of 22 (client, family) cells have a negative mean pooling gain federation-wide (6 with an interval below zero) and 15 of 22 own-domain (5); in the replication set 9 of 23 (6) and 8 of 23 (4). **By family (primary, federation-wide):** adwo pooling -0.107 (-0.223, -0.025), repair share 0.58; revmob -0.077 (-0.152, -0.030) but new capability 0.265 of CTK 0.343 (share 0.23); dowgin is the opposite case (pooling +0.110, CTK +0.003).
- **Caveats.** Repair is an accounting bound (the smaller of the recall lost and the CTK gained per cell), not a causal effect; cells are observed in 1 to 6 seeds and own-domain cells can have as few as about 10 hidden trials per seed, so cell-level intervals are unstable; four clients; no multiplicity correction; the cell counts of "hurt" are descriptive.

## 6. Generic Pooling Versus Complementary Threat Knowledge [A, with B/C context]

The gate `generic-pooling-majority` is **rejected** (0 of 2 scopes; the pooling-share upper bounds are 0.354 and -0.878, both below 0.5) and remains so. What the intervals support, scoped:

- **Primary MLP, controlled exposure [A]:** generic pooling does not account for the majority of the collaboration gain, and CTK is the dominant measured component.
- **Not generalizable [B]:** natural scarcity (FedAvg federation-wide: pooling gain +0.100, CI 0.072 to 0.131; share 0.47, CI 0.38 to 0.56; CTK share 0.53, CI 0.44 to 0.62), lower training support (pooling share 0.52, CI 0.40 to 0.62), and the linear model (pooling gain +0.181, share 0.66, CI 0.60 to 0.73; CTK +0.094, share 0.34) have a large pooling component. No dominance claim is made for any model class or design other than the primary MLP controlled-exposure setting. Trees (centralized): pooling +0.053 (0.008, 0.094), CTK +0.102, CTK share 0.66 (0.52, 0.98).

## 7. Own-Domain Results [A]

Own-domain CTK (FedAvg) is +0.107 (0.068 to 0.144), 10/10 seeds; the gate `own-domain-benefit` is promoted. Own-domain total gain is only +0.038 because pooling costs -0.069 (nine of ten seeds negative). FedProx improves own-domain recall by +0.059 (0.021, 0.103) and blend by +0.072 (0.053, 0.098). Own-domain pooling is decomposed into repair and new capability in section 5.1; the own-domain permutation control is discussed in section 22.

## 8. Worst-Client Results [A]

The predeclared worst-client CTK (FedAvg) is +0.173 (0.116 to 0.242), 10/10; total gain +0.146 (0.080, 0.240). In this predeclared analysis each arm takes its own minimum client, so identities can differ across arms; section 9 removes that limitation as a robustness check. Worst-client estimates are the least stable across scopes: at the 1% FPR operating point CTK is +0.049 (0.014, 0.113) for the primary set and below +0.03 in several sensitivities.

## 9. Local-Baseline-Anchored Worst-Client Robustness [C]

Post-confirmatory, exploratory support; it does not replace the gate. Within each seed the worst client under the **local baseline** is frozen and followed through every arm (`anchored-worst-client.csv`, `anchored-client-selection.csv`). Selected clients across the 10 seeds: appchina 5, anzhi 3, play-late 2 (mean local recall 0.288, 0.234, 0.321).

| Learner | Total gain | Pooling gain | CTK gain | Positive seeds (CTK) |
|---|---|---|---|---|
| FedAvg | 0.166 (0.085, 0.292) | -0.003 (-0.028, 0.033) | **0.169 (0.095, 0.297)** | 9/10 |
| central | 0.182 (0.114, 0.289) | -0.006 (-0.049, 0.065) | 0.188 (0.132, 0.313) | 10/10 |

The same client benefits: CTK is about +0.17 with an interval well above +0.03, and pooling is about zero. Caution: selecting on the local baseline biases total and pooling gains upward (regression to the mean); the CTK contrast compares two collaborative arms and is the cleaner estimate.

## 10. Natural-Scarcity (Within-Dataset) Validation [B]

Side by side with controlled exposure, FedAvg, 5% FPR (`natural-scarcity-comparison.csv`; the estimands are **not** pooled). Both use the same 7 families and 4 clients.

| | Controlled | Natural scarcity |
|---|---|---|
| CTK federation-wide | 0.117 (0.090, 0.145), 10/10 | 0.113 (0.094, 0.128), 10/10 |
| CTK own-domain | 0.107 (0.068, 0.144), 10/10 | 0.110 (0.076, 0.139), 10/10 |
| CTK worst client | 0.173 (0.116, 0.242), 10/10 | 0.140 (0.084, 0.180), 9/10 |
| CTK family-macro | 0.124 (0.102, 0.153) | 0.161 (0.147, 0.181) |
| Total gain federation-wide | 0.132 | 0.213 (0.176, 0.242) |
| Pooling gain federation-wide | 0.014 | 0.100 (0.072, 0.131) |

Interpretation: the CTK magnitude is essentially the same in the artificial and the natural design, with the same sign, seed consistency and ten of ten positive seeds, which is within-dataset validation (same LAMDA/AndroZoo corpus, not external or independent-dataset validation) that the controlled-exposure effect is not merely an artefact of deleting family examples. What differs is the decomposition: under natural scarcity ordinary pooling contributes roughly as much as CTK, so total gains are larger. Operating point: realised FPR 0.0503 to 0.0510 in both designs. Natural scarcity has no full-exposure arm, so family rescue classification is "not classifiable" there.

## 11. Dose-Response Results [A, corrected]

Gate correction: the original gate dropped the `all available` level because its requested dose is null, so the only level with at least 100 effective peer samples was never tested (old outcome NARROWED, 1 of 3). The corrected gate compares each level's effective exposure with the criterion and gives **PROMOTED, 3 of 3** with unchanged thresholds. Details in `docs/decisions/protocol-amendments.md`. FedAvg, 70 family-seed rows per level (`peer-dose-response.csv`):

| Requested dose | Mean effective dose | Recall | CTK gain vs zero | Meets 100-sample criterion |
|---|---|---|---|---|
| 0 | 0 | 0.437 | 0 | no |
| 1 | 0.09 | 0.433 | -0.004 | no |
| 10 | 0.86 | 0.441 | +0.003 | no |
| 50 | 4.5 | 0.448 | +0.011 | no |
| 100 | 9.0 | 0.457 | +0.020 | no |
| 500 | 43.1 | 0.505 | +0.068 | no |
| 1000 | 79.4 | 0.527 | +0.090 | no (34 of 70 rows individually do) |
| all available | 296.2 | 0.562 | **+0.124** | yes |

What the curve shows: the gate-supported statement is that recall improves as effective peer exposure increases and the predeclared dose-response gate is satisfied. The confirmatory gate alone does not establish diminishing marginal returns or a saturation point; recall is still rising at the largest effective exposure. The prospective exact-dose extension (class D, seeds 310 to 319, section 33.2) is consistent with diminishing marginal returns, but observes no plateau through 200 exact peer samples. Requested doses badly overstate exposure (client caps and availability): requested 100 delivers about 9 samples, so "100 samples" is only reached by the all-available level and part of the 1000 level. Observation-level sensitivity (the 70 rows with at least 100 effective samples) gives mean gain +0.045; leave-one-family-out mean at least 0.040 (five families, one with two rows). Not driven by one family under either reading (level reading: at least +0.089). The dose effect is family-dependent: dowgin shows no gain (-0.004) even with a mean of 1,188 effective samples, revmob (+0.336) and leadbolt (+0.268) show large gains at 55 and 84 samples. Centralized and fine-tuned arms follow the same rising shape (all-available gain +0.110 and +0.090); this section's confirmatory result remains unchanged.

## 12. Family-Level Mechanism Patterns [C, descriptive]

Primary set, FedAvg unless stated (`family-mechanism-patterns.csv`); local / no-family / peer-family recall; CTK; pooling gain; full-exposure central recall; linear and tree full-exposure recall. No classes are formally defined; the groupings below are descriptive examples.

| Family | Local | No-family | Peer | CTK | Pooling | Full | Linear full | Trees full |
|---|---|---|---|---|---|---|---|---|
| revmob | 0.260 | 0.183 | 0.525 | +0.343 | -0.077 | 0.539 | 0.399 | 0.495 |
| leadbolt | 0.304 | 0.309 | 0.585 | +0.277 | +0.005 | 0.648 | 0.433 | 0.525 |
| adwo | 0.671 | 0.564 | 0.665 | +0.101 | -0.107 | 0.585 | 0.667 | 0.761 |
| airpush | 0.669 | 0.699 | 0.783 | +0.084 | +0.030 | 0.859 | 0.692 | 0.799 |
| hiddad | 0.298 | 0.236 | 0.265 | +0.029 | -0.062 | 0.283 | 0.154 | 0.179 |
| gappusin | 0.321 | 0.281 | 0.310 | +0.029 | -0.040 | 0.453 | 0.411 | 0.584 |
| dowgin | 0.658 | 0.768 | 0.771 | +0.003 | +0.110 | 0.864 | 0.823 | 0.919 |

- **Exposure-limited, strongly CTK-responsive:** revmob and leadbolt (low local and no-family recall, large CTK gain, peer recall approaching the full-exposure level). Replication set: inmobi (+0.166) and utchi (+0.116, from a local recall of 0.008).
- **Generic-pooling-responsive, CTK small:** dowgin (pooling +0.110, CTK +0.003; local recall already 0.658). In the replication set smsreg and inmobi also show positive pooling.
- **Representation-limited:** hiddad (CTK +0.029; full-exposure recall 0.283; linear 0.154 and trees 0.179 are also poor) and gappusin (CTK +0.029; full 0.453; linear 0.411). Under the tested LAMDA-static representation and model classes, peer exposure does not rescue them and full exposure does not either.
- **Already represented / low headroom:** adwo (local 0.671; peer recall equals local, its positive CTK arises because the no-family arm is *worse* than local, pooling -0.107), airpush and dowgin (high local recall). In the replication set zdtad (local 0.776, peer 0.694: collaboration lowers recall, CTK -0.019), kuguo (+0.027), dnotua (+0.007).
- CTK is a counterfactual against family-absent pooling. For adwo, hiddad, gappusin and revmob the pooling gain is negative, so CTK partly measures repair of negative transfer; the total gain (peer minus local) is the deployment-relevant number: revmob +0.266, leadbolt +0.281, airpush +0.115, dowgin +0.113, adwo -0.006, hiddad -0.032, gappusin -0.011.

### 12.1 Heterogeneity structure [C]

Post-confirmatory, exploratory (`ctk-variance-components.csv`, `family-associations.csv`, `family-client-ctk.csv`).

- **Variance components (family x client x seed REML) [C].** `ctk-heterogeneity-components.csv`; crossed random effects for family, client, family-by-client and seed on the per-cell FedAvg CTK (response: one value per seed, client and hidden family; 70 observations in 22 (client, family) cells, 19 observed in more than one seed, primary set; 72 observations in 23 cells, 21 replicated, replication set; 4 clients; the REML optimizer converged in all fits, two components at a variance boundary; the own-domain splits are weakly identified: statsmodels MixedLM stops at nearby but different client and seed values). Shares of variance with 95% percentile bootstrap intervals over 2,000 seed resamples (a seed drawn twice is treated as two seeds, which biases residual shares downward, so residual-share intervals are anti-conservative):

| Set, population | Family | Client | Family x client | Seed | Residual |
|---|---|---|---|---|---|
| Primary, federation-wide | **63.0%** (36, 78) | 7.0% (0, 38) | 7.1% (1, 24) | 2.0% (0, 8) | 20.9% (5, 24) |
| Primary, own-domain | 15.4% (2, 48) | **58.5%** (15, 89) | 2.4% (0, 33) | 0.0% (0, 5) | 23.7% (4, 25) |
| Replication, federation-wide | 6.1% (0, 30) | 12.4% (0, 31) | 25.2% (15, 72) | 4.0% (0, 10) | **52.3%** (11, 55) |
| Replication, own-domain | 4.8% (0, 39) | 0.0% (0, 3) | 13.9% (2, 73) | 2.8% (0, 26) | **78.5%** (10, 87) |

  Reading: in the primary set family identity dominates federation-wide CTK, while own-domain CTK varies most between clients (largely play-late, section 14); in the replication set no component is clearly dominant and most variance is residual, which own-domain is largely test-sampling noise (residual 0.0199 versus reference 0.0128). This supersedes the earlier client-averaged family-by-seed decomposition (`ctk-variance-components.csv`: family 69.5%, seed 7.5%, residual 23.1% primary; 27.3%, 8.5%, 64.2% replication), which could not separate clients. Caveats: the residual mixes true three-way interaction with sampling noise; own-domain residual variance (0.0112) is about equal to the reference sampling noise implied by the trial counts (0.0107), so own-domain residual shares are largely sampling noise, whereas federation-wide residuals (0.0047 versus 0.0004) are not; the client component rests on four clients, and 0 lower bounds are variance-boundary estimates; the bootstrap resamples seeds only and treats families and clients as fixed; intervals are wide.
- **Family-level associations (descriptive, 8 tests, no multiplicity claim).** Spearman association between family local recall and CTK gain: primary rho -0.32 (p 0.48, n 7), replication rho -0.81 (p 0.015, n 8; not significant after a Holm correction over the eight tests, 0.12). Lower local recall is descriptively associated with larger CTK (exposure-limited families benefit most), consistent with the family patterns above; the total gain and pooling-gain associations are partly mechanical (total = pooling + CTK).
- **Hidden-family by target-client table.** 22 (client, family) target pairs are observed in the primary set, each in only 1 to 6 seeds and with as few as 10 hidden test trials per seed, so per-pair intervals are unstable; the pattern is descriptive: strong CTK at play-late for revmob (+0.50, 5/5 seeds) and leadbolt (+0.61, 3/3), at appchina for revmob (+0.11) and leadbolt (+0.14), near zero for dowgin and hiddad at every client, and negative for dowgin at play-early (-0.09). Per-pair inference would require more seeds or a dedicated design (section 34).

## 13. Representation-Limited Families [A]

The gate `representation-limited-family` is promoted with scoped wording: 3 of 4 poorly recalled primary families (full-exposure central recall below 0.60) are also poor in an independent model class (linear or trees): hiddad, gappusin, revmob. adwo (full 0.585) is poor only for the MLP; linear 0.667 and trees 0.761 are adequate. Bounded interpretation, under the tested static representation and models: exposure alone does not explain all family-level failures. Independent-model evidence exists only for the primary family set; replication-set families (for example utchi, full 0.438) have no cross-model check. The prospective same-application representation replication EXT-REP (33.2, class D) reports that this limitation is family-specific to the tested LAMDA static space; it does not alter this gate (promoted, 3 of 4) or the 9/0/3 count.

## 14. Client-Level Results [C]

Post-confirmatory, evidence-preserving, descriptive and exploratory; it creates no gate, uses stored client metrics only (`client-ctk-analysis.csv`, `client-ctk-analysis.png`) and changes no original outcome. Federation-wide population, MLP, 5% FPR. For each client the decomposition is computed per seed and averaged; every client is reported, with its number of contributing seeds. Intervals are **exploratory small-n BCa intervals** over the contributing seeds (10, 10, 8 and 6 seeds); they are shown whenever the existing BCa helper can compute one (it needs at least 3 seeds and a non-constant effect) and are omitted otherwise. No seed-count threshold is used, and the 8-of-10 positive-seed rule of the complementary-knowledge gate has nothing to do with interval validity. With 6 to 10 seeds and unequal support the intervals are unstable and understate uncertainty from unequal per-seed support; read them as descriptive. Client identities differ from the anchored worst client of section 9. Support: local malware rows and prevalence from the client audit; hidden-family test trials per seed and eligible (seed, family) pairs from the run metrics.

| Client | Malware rows (prevalence) | Seeds | Pairs | Hidden trials/seed | Local | No-family | Peer | Full | Total gain | Pooling gain | CTK gain | CTK seeds positive |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| anzhi | 90,801 (87%) | 8 | 17 | 3,899 | 0.513 | 0.439 | 0.517 | 0.558 | +0.005 (-0.056, 0.086) | **-0.074 (-0.141, -0.022)** | +0.078 (0.032, 0.141) | 7/8 |
| appchina | 73,578 (83%) | 10 | 24 | 4,493 | 0.397 | 0.419 | 0.492 | 0.521 | +0.095 (0.054, 0.139) | +0.022 (-0.012, 0.085) | +0.073 (0.031, 0.119) | 8/10 |
| play-early | 75,985 (24%) | 10 | 18 | 3,890 | 0.621 | 0.706 | 0.788 | 0.845 | +0.166 (0.092, 0.255) | +0.084 (-0.003, 0.198) | +0.082 (0.043, 0.199) | 10/10 |
| play-late | 17,200 (5.4%) | 6 | 11 | 1,802 | 0.493 | 0.484 | 0.812 | 0.862 | +0.319 (0.192, 0.424) | -0.009 (-0.152, 0.073) | +0.328 (0.224, 0.431) | 6/6 |

Known-family recall change versus local, federation-wide (all 10 seeds contribute; exploratory BCa intervals) and realised benign FPR of the FedAvg arm:

| Client | FedAvg | FedProx | Centralized | Realised FPR (FedAvg) |
|---|---|---|---|---|
| anzhi | **-0.065 (-0.097, -0.034)** | -0.001 (-0.013, 0.009) | -0.007 | 0.060 |
| appchina | -0.015 (-0.030, 0.006) | +0.020 (0.005, 0.034) | -0.007 | 0.049 |
| play-early | -0.014 (-0.036, -0.000) | **-0.029 (-0.043, -0.015)** | +0.024 (0.005, 0.034) | 0.044 |
| play-late | **-0.037 (-0.055, -0.016)** | -0.016 (-0.039, 0.011) | -0.009 | 0.050 |

Bold entries exceed the ±0.02 tolerance used by the known-family gate (a gate defined on the client mean, not per client).

Answers, all descriptive:

1. **Largest CTK:** play-late (+0.328, exploratory interval 0.224 to 0.431, 6 seeds); the other three clients are similar (+0.073 to +0.082, intervals above zero, lower bounds at or just above +0.03).
2. **Little CTK:** none is zero or negative. Own-domain CTK is small for anzhi (+0.029, interval -0.001 to 0.073, 4/8 seeds) and appchina (+0.025, 0.002 to 0.050, 6/10).
3. **Benefit mostly from generic pooling:** none; play-early has the largest pooling gain (+0.084, interval -0.003 to 0.198), about half its total gain, with a wide interval.
4. **Negative pooling:** anzhi (-0.074, exploratory interval -0.141 to -0.022), and own-domain pooling is negative for all four clients (largest for play-late, -0.286, exploratory interval -0.535 to -0.081, on only about 107 trials per seed). Anzhi's net FedAvg gain is about zero (+0.005, interval spans zero): its CTK gain is offset by negative pooling. Centralized and FedProx are slightly negative there (-0.021, -0.031).
5. **Known-family cost:** FedAvg exceeds the tolerance for anzhi (-0.065) and play-late (-0.037); appchina and play-early are near it (-0.015, -0.014). FedProx removes the anzhi and play-late losses but loses -0.029 on play-early; centralized is within tolerance everywhere except a +0.024 gain on play-early.
6. **Is the cost concentrated in one client?** For FedAvg it is largest at anzhi and second largest at play-late, so it is not a single-client artefact; the mean of the four changes (-0.033) reproduces the arm mean. For FedProx the residual cost moves to a different client (play-early). The cost is therefore arm-by-client specific, and averages hide it.
7. **Less local malware support, more CTK?** The lowest-support client (play-late, 17,200 malware rows) has the largest CTK but with only 6 seeds and about half the hidden-family test trials; the other three clients (74k to 91k malware rows) show no gradation. Descriptively suggestive, not resolved.
8. **Prevalence:** the two Google Play clients (24% and 5.4% malware) have larger total gains (+0.166, +0.319) than the two third-party markets (+0.005, +0.095). With four clients this is descriptively associated with prevalence and market type, not evidence of a relationship, and it is confounded with support and seed availability.
9. **Late Google Play:** it behaves differently (largest total gain and CTK, lowest support) but its estimates rest on 6 of 10 seeds and 11 pairs, so its exploratory intervals should be treated as descriptive.
10. **Support imbalance:** anzhi loses 2 seeds (no federation-wide hidden-family test rows in those seeds) and play-late 4; own-domain rows for play-late average about 107 trials per seed. Patterns that involve play-late are plausibly driven partly by support imbalance; this analysis cannot separate the two.

Realised FPR differs by client: anzhi 0.060 versus 0.044 to 0.050 for the others, within the 0.02 realised-FPR tolerance but a reminder that per-client operating points are noisier than the pooled one. Causal language is not warranted with four clients.

### 14.1 Aggregate discrimination and client-level harm [C]

From `arm-metrics.parquet` (controlled exposure, peer-present, 5% FPR calibration; macro over clients on the test partition, all families):

| Arm | AUROC | AUPRC | Client-recall dispersion |
|---|---|---|---|
| local | 0.927 | 0.872 | 0.176 |
| FedAvg | 0.915 | 0.852 | 0.170 |
| FedProx | 0.927 | 0.869 | 0.192 |
| FedAvg + fine-tune | 0.918 | 0.868 | 0.163 |
| blend | 0.932 | 0.880 | 0.192 |
| central | 0.927 | 0.876 | 0.197 |
| central, full exposure | 0.928 | 0.880 | 0.187 |
| FedAvg, family absent everywhere | 0.900 | 0.839 | 0.211 |

Aggregate discrimination does not show the collaboration benefit: FedAvg and fine-tuning are below local although their unseen-family recall is higher by 0.13 and 0.11, because the aggregate pools mostly known-family malware. This is the same structure as the "misleading convergence certificate" in Otani et al. (overall accuracy flat while rare-class recall falls). The family-absent-everywhere FedAvg model is worse than every other arm (AUROC 0.900), so peer-held family data also helps aggregate discrimination relative to no family, but only to the level of local training. Aggregate AUROC/AUPRC do not reflect the unseen-family recall change here, which supports reporting unseen-family recall at fixed FPR alongside them.

**Aggregate-metric masking [C]** (`aggregate-metric-masking.csv`; 64 rows: 2 family sets x 4 federated arms x 2 contrasts x 2 aggregate metrics x 2 recall metrics). For each seed the difference in AUROC or AUPRC between two arms is paired with the difference in unseen-family recall at 5% FPR; BCa intervals over the 10 seeds. A **masked gain** is flagged when the recall interval lies above +0.03 while the aggregate-metric interval is not positive (masked loss: the mirror image); a seed is a "gain missed" seed when recall rises by at least 0.03 while the aggregate difference is at most zero.

| Peer-present arm versus local (primary set, federation-wide recall) | Delta AUROC | Delta AUPRC | Delta recall | Gain-missed seeds (AUROC / AUPRC) | Flag |
|---|---|---|---|---|---|
| FedAvg | -0.012 (-0.016, -0.009) | -0.020 (-0.026, -0.016) | +0.132 (0.090, 0.167) | 9 / 9 of 10 | masked gain |
| FedProx | -0.000 (-0.003, 0.001) | -0.003 (-0.007, -0.001) | +0.139 (0.089, 0.188) | 5 / 7 | masked gain |
| FedAvg + fine-tune | -0.009 (-0.012, -0.007) | -0.004 (-0.008, -0.002) | +0.107 (0.073, 0.134) | 9 / 7 | masked gain |
| blend | +0.005 (0.004, 0.006) | +0.008 (0.006, 0.010) | +0.127 (0.094, 0.161) | 0 / 0 | not masked |

- The 15 flagged rows are 8 distinct recall contrasts, each counted once per aggregate metric; a point-estimate version of the flag would give 29, so the count depends on the flag definition. In the primary set 6 of 16 federation-wide-recall contrasts are flagged (all three arms that lack a positive aggregate gain, both metrics); none against the family-absent baseline, whose aggregate difference is positive (FedAvg +0.015 AUROC). In the replication set 9 of 16 are flagged (6 against local, 3 against the family-absent baseline). Own-domain recall flags none (its recall intervals reach below +0.03, for example FedAvg +0.038, 0.015 to 0.062), although FedAvg misses the gain in 4 of 10 seeds (5 of 10 in the replication set). No masked loss is flagged; 5 seed-level false-reassurance instances exist over all 64 rows. 18 of the 64 rows have opposed interval verdicts (aggregate negative, recall positive).
- The across-seed correlation between aggregate and recall differences is inconsistent in sign and size (FedAvg versus local: -0.23 for AUROC, +0.92 for AUPRC), so an aggregate metric is not a proxy for the unseen-family effect. Caveats: the flag uses the same +0.03 practical threshold as the CTK gate; ten seeds; class C, no gate.

Share of clients that beat local training on unseen-family recall (a negative-transfer view, as in FedCollab's individual-participation rate): FedAvg total gain is positive for 4 of 4 clients in point estimate and has an interval excluding zero for 3 of 4 (anzhi +0.005, interval -0.056 to 0.086). Negative-transfer components are the pooling gains above (section 14) and their repair-versus-new-capability split (section 5.1): negative pooling at anzhi (-0.074) and, for own-domain evaluation, at all four clients.

## 15. Known-Family Safety and Federated Arm Trade-Offs [A + C]

Gate `known-family-safety` (promoted, strongest arm only): the strongest federated arm by federation-wide unseen recall is FedProx; its known-family change is -0.006 and FPR change +0.001, both within tolerance.

Arm comparison versus local, 5% FPR, seed-paired (`federated-arm-tradeoff.csv`, class C; no score or ranking is defined):

| Arm | Fed.-wide unseen change | Own-domain change | Worst-client change | CTK | Known-family change | FPR change | Full-exposure gap | Oracle-gap recovery |
|---|---|---|---|---|---|---|---|---|
| FedAvg | +0.132 | +0.038 | +0.146 | +0.117 | **-0.033 (-0.044, -0.021), outside ±0.02** | +0.0009 | 0.070 | 0.63 |
| FedProx | +0.139 | +0.059 | +0.101 | +0.135 | -0.006 (-0.019, 0.002), within | +0.0011 | 0.062 | 0.64 |
| FedAvg + fine-tune | +0.107 | +0.006 | +0.129 | +0.077 | **-0.038 (-0.047, -0.028), outside** | +0.0004 | 0.094 | 0.56 |
| blend | +0.127 | +0.072 | +0.095 | +0.075 | +0.017, within | +0.0012 | 0.074 | 0.63 |
| central (reference) | +0.152 | +0.056 | +0.133 | +0.131 | +0.000, within | +0.0009 | 0.049 | 0.71 |

Paired FedProx minus FedAvg: CTK +0.018 (0.001, 0.031; 8/10); known-family recall +0.026 (0.011, 0.041; 8/10); own-domain +0.022 (-0.002, 0.046); federation-wide unseen +0.008 (-0.008, 0.038, not resolved); worst-client -0.045 (-0.099, 0.007; 4/10 positive, not resolved). Descriptive reading: FedProx delivers an unseen-family benefit similar to or slightly larger than FedAvg with a much smaller known-family cost, while its worst-client gain is smaller (unresolved). FedAvg and local fine-tuning incur known-family losses beyond the predeclared tolerance; wording must not imply that all arms are safe. Fine-tuning has a smaller CTK gain than FedAvg (-0.040 paired, CI -0.062 to -0.022). This is a descriptive deployment trade-off, not a predeclared winner.

## 16. Model-Family Replication [B]

FedAvg for the linear model, centralized for trees (trees have no federated arm), federation-wide, 5% FPR:

| Model | CTK gain | Total gain | Pooling gain | CTK share | Positive seeds (CTK) |
|---|---|---|---|---|---|
| MLP (FedAvg) | 0.117 (0.090, 0.145) | 0.132 | 0.014 | 0.89 | 10/10 |
| Linear (FedAvg) | 0.094 (0.075, 0.110) | 0.274 | 0.181 (0.152, 0.214) | 0.34 (0.27, 0.40) | 10/10 |
| Linear (central) | 0.082 (0.065, 0.103) | 0.305 | 0.223 | 0.27 | 10/10 |
| Trees (central) | 0.102 (0.076, 0.137) | 0.155 | 0.053 (0.008, 0.094) | 0.66 (0.52, 0.98) | 10/10 |

The CTK effect persists in sign and practical magnitude across model classes (own-domain: linear +0.098, trees +0.117; worst client: linear +0.079, trees +0.166). The decomposition does not: for the linear model generic pooling is the larger component. The local deficit is 0.337 (linear) and 0.204 (trees) versus 0.201 (MLP).

## 17. Replication Family Set [A]

Disjoint set of 8 families, FedAvg: CTK federation-wide +0.064 (0.038, 0.077), 9/10 seeds; own-domain +0.042 (0.001, 0.091), 8/10; worst client +0.047 (0.028, 0.067), 9/10; family-macro +0.069 (0.045, 0.098). Total gain +0.081 (0.042, 0.128), local deficit 0.153. The effect replicates in sign and exceeds the +0.03 threshold but is roughly half the primary-set size, and the own-domain interval barely excludes zero. Family spread inside this set is large (CTK from -0.019 to +0.166). The family-dependence gate spans both frozen sets (15 families, spread 0.362) and is promoted.

## 18. Support Sensitivity [B]

FedAvg CTK federation-wide (5% FPR): lower training support (1,500 rows) +0.107 (0.087, 0.128); low family support +0.143 (0.116, 0.163); high family support +0.117 (0.090, 0.141); all 10/10 seeds. Under lower training support the pooling gain rises to +0.115 (share 0.52), so the decomposition is support-dependent while the CTK effect is not.

## 19. Operating-Point Sensitivity [B]

FedAvg CTK, primary family set: 1% FPR federation-wide +0.076 (0.037, 0.125), 9/10; 5% +0.117; 10% +0.134 (0.110, 0.164). Worst client: +0.049 (0.014, 0.113) at 1%, +0.173 at 5%, +0.225 (0.185, 0.277) at 10%; own-domain +0.071, +0.107, +0.132. Effects shrink at the strictest operating point and worst-client estimates at 1% fall under +0.03 in several sensitivities (section 21). Realised FPR is within +0.002/+0.004/+0.007 of target.

## 20. Partition and Leakage Robustness [B]

Partition salts 1, 2, 3 (reported separately, each with 10 seeds): CTK +0.129 (0.105, 0.165), +0.131 (0.102, 0.160), +0.119 (0.094, 0.145). Package-only grouping (weaker than the strict identity-component grouping used in the primary design): +0.107 (0.083, 0.126). Micro-pooled sensitivities (hits/trials pooled per seed, a different estimand from the seed-paired one), primary set: all families +0.066 (0.049, 0.083); representation-deduplicated test +0.055 (0.041, 0.068); removing the three highest-support families +0.139 (0.111, 0.180). Leakage hardening does not remove the effect. The micro-pooled magnitude (0.066) is smaller than the seed-paired macro estimate (0.117) because high-support families with little CTK (for example dowgin) dominate pooled counts; removing them raises it.

### 20.1 EXT-1: own-domain and worst-client permutation control replication with fresh seeds [D]

Frozen before execution (protocol text in the Roadmap 31.4; hypothesis, arms, endpoints and interpretation rules fixed in advance). Same experiment code and hyperparameters as the original `family-permutation-control`; fresh seed range 200 to 209 (mode `extension`); never pooled with seeds 100 to 109. FedAvg CTK under permuted family labels, seed-paired, 95% BCa, equivalence band ±0.03 (`results/extension/permutation-control-audit.csv`):

| Population | Alpha | CTK (CI) | Positive seeds | Outcome |
|---|---|---|---|---|
| Own-domain (**primary endpoint**) | 0.05 | +0.006 (-0.004, 0.014) | 7/10 | **equivalent** |
| Own-domain | 0.01 / 0.10 | -0.002 (-0.016, 0.011) / +0.009 (-0.016, 0.025) | 6/10 / 8/10 | equivalent |
| Federation-wide | 0.01 / 0.05 / 0.10 | -0.010 (-0.028, 0.007) / +0.003 (-0.002, 0.008) / +0.004 (-0.015, 0.011) | 4, 6, 8 | equivalent |
| Worst client | 0.01 / 0.05 / 0.10 | -0.002 / -0.005 (-0.022, 0.007) / +0.011 (-0.002, 0.026) | 5, 6, 6 | equivalent |
| Family-macro | 0.05 / 0.10 | +0.004 (-0.000, 0.009) / +0.008 | 6, 8 | equivalent |
| Family-macro | 0.01 | -0.015 (-0.039, 0.006) | 5/10 | unresolved (not a pre-specified endpoint) |

Interpretation, per the rule frozen in advance: the primary endpoint is met (interval inside ±0.03), so the own-domain null control is clean in the extension (v1 and EXT-1 status: section 22). The original permutation result and the original gate counts are unchanged. The centralized arm's worst-client control is unresolved at 1% and 5% FPR (secondary, not a pre-specified endpoint). One family-macro cell at 1% FPR straddles the band edge.

## 21. Canonical CTK Robustness Synthesis [B/C]

`ctk-robustness-synthesis.csv` (336 rows: 300 seed-paired macro, 36 micro-pooled; each row labelled with aggregation, scope, learner, alpha, salt or sensitivity, evidence class) and `ctk-robustness-forest.png`. Of the 300 seed-paired rows, 24 belong to the family-label permutation control (a negative control whose expected value is zero); of the remaining 276, 269 have a mean at or above +0.03. All 33 non-control micro-pooled rows are at or above +0.03 (the other 3 micro rows are the permutation control). The seven paired rows below the practical threshold are all worst-client estimates at the 1% FPR target: high family support 0.028; linear 0.015; lower training support 0.005; salts 2 and 3 about 0.017 and 0.015; replication FedAvg 0.006; replication centralized -0.017. At 5% FPR every federation-wide scope exceeds +0.03 with a positive interval. Seed-paired and micro-pooled rows are never mixed in one estimate.

## 22. Negative Controls [A, plus C audit, D extension]

Family-label permutation, CTK. **Status: own-domain control unresolved in v1 (original seeds 100 to 109), resolved prospectively in EXT-1 (extension seeds 200 to 209, section 20.1); the federation-wide control is clean in both.** The v1 estimates are kept as history (`permutation-control-audit.csv`):

| Population | Alpha | FedAvg CTK (CI), v1 | Outcome vs ±0.03 band, v1 |
|---|---|---|---|
| Federation-wide (gate) | 0.05 | -0.001 (-0.007, 0.007) | equivalent [A] |
| Federation-wide | 0.01 / 0.10 | -0.008 (-0.025, 0.009) / +0.003 (-0.008, 0.010) | equivalent |
| Own-domain | 0.05 | +0.011 (-0.004, 0.036) | **unresolved** (extends past +0.03) [C] |
| Own-domain | 0.10 | +0.029 (0.010, 0.050) | **unresolved** |
| Own-domain | 0.01 | +0.003 (-0.008, 0.011) | equivalent |
| Worst client | 0.01 / 0.05 / 0.10 | +0.002 / -0.001 / -0.006 | equivalent |

No retrospective own-domain permutation gate was added and the original gate counts are unchanged. Other negative-control checks (family-absent-everywhere condition, zero-dose agreement, sample-size matching, target-independence assertions) passed as structural validations. Two further controls that a reviewer would ask for, a coherent wrong-family placebo and rare-peer erasure by robust aggregation, are not covered by the permutation control; they were tested in a prospective extension (class D, seeds 320 to 329; results in 33.2).

## 23. Feature-Novelty Analysis [A gate; C interpretation]

Predeclared descriptor (nearest-known-family distance) versus FedAvg CTK: primary set rho 0.571 (p = 0.180, interval -0.412 to 1.0, 7 families); replication set rho 0.333 (p = 0.420, interval about -0.57 to 1.0, 8 families). The gate (association at least 0.3 with an interval excluding zero in both sets) is **not satisfied** and its stored status stays "rejected". Interpretation: the point estimates are positive in both sets and above the 0.3 magnitude, so the direction is consistent, but with 7 and 8 families the intervals are far too wide to establish or exclude an association. Novelty is neither supported nor contradicted in the original evidence; it is unresolved, and no further descriptors were searched. The same predeclared descriptor was tested prospectively on 32 fresh families (class D, section 33.2), which does not change this gate status. Family-level values are in `family-mechanism-patterns.csv` and the novelty scatter figure.

## 24. Statistical Evidence [A]

Ten seeds; paired Wilcoxon exact p-values reach the minimum attainable 0.00195 when all seeds agree. Primary contrast family (FedAvg, federation-wide, alpha 0.05, Holm across total, pooling, CTK): total gain p = 0.0059, CTK p = 0.0059, pooling p = 0.557. BCa intervals over 10 seeds; small-sample caution applies to every interval. Seed direction: FedAvg CTK is positive in 10/10 seeds for the primary federation-wide, own-domain, worst-client and family-macro scopes and for natural scarcity except worst client (9/10); the replication set is 8/10 to 9/10 by metric.

## 25. Gate Outcomes [A]

`results/gates/claims.csv`:

| Claim | Status | Scopes | Note |
|---|---|---|---|
| local-deficit | promoted | 2/2 | |
| collaboration-benefit | promoted | 2/2 | |
| complementary-knowledge | promoted | 3/3 | federation-wide, own-domain, replication; permutation equivalent |
| generic-pooling-majority | rejected | 0/2 | pooling is not the majority for the primary MLP |
| dose-response | promoted | 3/3 | corrected from narrowed (section 11) |
| own-domain-benefit | promoted | 1/1 | v1 permutation caveat, resolved in the extension (section 22) |
| worst-client-benefit | promoted | 1/1 | |
| known-family-safety | promoted | 2/2 | strongest federated arm (FedProx) only |
| family-dependence | promoted | 1/1 | scope corrected to the frozen family sets; spread 0.362 |
| representation-limited-family | promoted | 3/4 | scoped wording |
| feature-novelty-explanation | rejected | 0/2 | unresolved evidence (section 23) |
| new-mechanism-trigger | rejected | 0/2 | no headroom (section 27) |

Totals: 9 promoted, 0 narrowed, 3 rejected, 0 insufficient-evidence.

## 26. Claim Inventory

Strongest defensible claims (class in brackets):

1. [A] For the primary MLP, collaboration improves recall on locally unseen families (+0.132) and most of that improvement is complementary peer-held family knowledge rather than generic pooling.
2. [A/B] The CTK effect persists in sign and practical magnitude in own-domain, worst-client, natural-scarcity, replication-set, linear and tree, support, operating-point and partition sensitivities.
3. [B] Natural scarcity reproduces the CTK magnitude within the same corpus (+0.113 versus +0.117), a within-dataset validation of the controlled design (not external validation); its decomposition differs.
4. [A/C] FedProx preserves known-family recall within tolerance while retaining the unseen-family benefit; FedAvg and fine-tuning do not.
5. [A] Peer-family benefit grows with effective exposure, and several families stay poorly recalled even under full exposure (representation limits), while standard baselines leave no headroom for a new mechanism.

## 27. Negative and Narrowed Findings

- Generic-pooling-majority rejected; and the linear, natural-scarcity and lower-support settings show large pooling components, so no model-general CTK dominance.
- Feature-novelty gate not satisfied (unresolved).
- New-mechanism trigger not met. Headroom versus central full exposure (`mechanism-headroom.csv`), mean gap (threshold 0.10): FedAvg 0.070 (0.043, 0.096), FedProx 0.062 (0.022, 0.089), fine-tune 0.094 (0.057, 0.138), blend 0.074 (0.049, 0.104), central 0.049 (0.020, 0.078); worst-client gap (threshold 0.15): FedAvg 0.029 (-0.026, 0.087), FedProx 0.074 (0.023, 0.126), fine-tune 0.047, blend 0.081, central 0.042. The mean gaps have upper bounds up to 0.138, so a residual gap cannot be excluded for fine-tuning, but the point estimates are below both triggers for every baseline; strong simple baselines already recover 0.56 to 0.71 of the exposure-related gap. Remaining failures for hiddad and gappusin persist under full exposure and in other model classes: representation, not federated optimization, is the more important remaining limitation, for this static representation and dataset only.
- Known-family cost of FedAvg and fine-tuning; own-domain oracle-gap recovery only 0.23; negative pooling own-domain (section 5.1).
- Dose: no saturation, unreachable low requested doses, dowgin flat.

## 28. Evidence-Preserving Scientific Improvements

Class C additions, all from stored runs: hidden-family variance components (12.1), negative-transfer repair versus new capability (5.1), aggregate-metric masking (14.1), per-client CTK analysis (section 14), local-anchored worst client (section 9), arm trade-off (15), robustness synthesis and forest plot (21), family patterns (12), natural-versus-controlled table and figure (10), permutation audit by population and alpha (22), headroom and operating-point fidelity tables. Corrected implementation defects (dose gate level handling, family-dependence scope, per-salt micro rows, natural-scarcity classification, provenance split, non-deterministic ordering) are logged in `docs/decisions/protocol-amendments.md`. No original confirmatory seed-level metric, paired effect, threshold or family set changed.

### 28.1 Reviewer-Gap Matrix

What a strong reviewer, informed by the literature audit (section 29), would expect this study to contain. "Existing evidence" means stored confirmatory artifacts or class C analyses. Comparator assessment: the task is a binary detector whose hidden unit is a family inside the positive class, so class-label-space methods are undefined baselines; the comparators that do test the CTK question are a coherent wrong-family placebo and rare-peer erasure by robust aggregation.

| Potential gap | Literature precedent | Does CTK already address it? | Importance | Needs new experiment? | Recommended action |
|---|---|---|---|---|---|
| Local-only baseline and a negative-transfer view (does collaboration hurt some clients?) | CELEST Table III (local versus global on the unseen family); FedCollab (individual participation rate); negative-transfer survey | yes: local arm, total gain, pooling gain, per-client table, repair versus new capability | High | no | reported (sections 5.1, 14) |
| Volume-matched peers (is the gain just more data?) | Breitholtz et al. (fixed 2,000 samples per client) | yes: the family-absent-everywhere arm has identical training volume (`train_rows` equal across arms; sample-size matching validated) | High | no | state explicitly (section 22) |
| **Coherent wrong-family placebo** (peers hold a different family of the same size): separates family-specific from generic-malware and relatedness effects, the literature's own explanation of transfer (CELEST, CyberForce, Ishfaq zero-day) | none of the read papers has one | yes for label-independent artefacts: the family-label permutation control restores a random malware subset with the original family-size distribution and gives CTK equivalent to zero, which rules out label-independent artefacts but not relatedness | **Critical** | yes | **Done [D]**: placebo effect -0.001 (-0.008, 0.006), equivalent to zero; CTK is family-specific (33.2) |
| **Rare-peer erasure by robust aggregation** (Trimmed Mean, Krum erase the rare holder) | CyberForce | tested in the extension (33.2), FedAvg-based | Critical if aggregation is not plain FedAvg; otherwise state scope | yes (mean versus robust-aggregator arm) | **Done [D]**: not erased in the primary set; attenuation possible in the replication set (33.2) |
| Missing-class label-space FL methods (FedRS restricted softmax, FedLC logit calibration, FedMR/FedGELA manifold and ETF fixes, FedLMD label masking, FedNTD not-true distillation, FedVLS vacant-class distillation) | image-classification literature; Shao/Otani et al.: label-skew methods cannot recover a missing direction without samples | no: baselines are FedAvg, FedProx, fine-tuning, blend, central | Low (a reviewer will still ask) | not with the current task | not baselines: a binary head has two classes present at every client, so these corrections are undefined or degenerate for a family inside the positive class; FedVLS's class-wise accuracy diagnosis is the conceptual analogue (cite). FedRoD and FedGELA personalised accuracies weight classes by each client's own mix and never score a locally missing class. A family-as-class multi-class variant would be a different task; not run |
| Negative-transfer and client-selection baselines (FedCollab, FedAwS-style) | negative-transfer survey | partly: pooling gain and per-client harm are measured (5.1, 14) | Medium | no | reported; they test harm to known classes, not family hiding |
| Prototype or representation explanations (FedP3E, FedProto, FedGELA/FedMR geometry) | mechanism explanations in several papers | partly: two model classes and a full-exposure ceiling | Medium, only if a representation mechanism is claimed (it is not) | optional | not a mechanism claim; representation replication run as EXT-REP (33.2): richer McNdroid static features raise gappusin, revmob (interval touches zero) and adwo, hiddad unresolved for McNdroid static and not rescued by call graph or report-JSON; call graph and report-JSON do not help the priority set; class D, same-application |
| Family-aware auxiliary objective (family-label head or family-contrastive loss) as the only genuine method upper bound | none read | no | Medium to high for a method paper; a measurement paper may still be asked | yes | not planned; limitation (needs reliable family labels; AVClass2 labels are noisy) |
| Aggregate discrimination metrics and fixed-FPR recall | CELEST reports PR-AUC and FPR at recall 0.9; Shao/Otani et al. show accuracy flat while recall falls | yes: recall at fixed FPR is primary; AUROC/AUPRC stored | Medium | no | reported; aggregate metrics mask the gain (14.1) |
| Worst-client and dispersion metrics | q-FFL, AFL, TERM | yes: worst client, anchored worst client, client-recall dispersion | Medium | no | reported (sections 8, 9) |
| Family-relatedness confound (Mirai/Gafgyt transfer even locally; "similar behaviors") | CELEST, CyberForce | partly: nearest-known-family descriptor (unresolved in the original gate) and family variance components (12.1) | Medium to high | larger-family study | **Done [D]**: rho 0.392 on 32 families, moderate association with a power caveat (33.2); the placebo row above is the direct test |
| Own-domain negative control | none | yes: unresolved in v1, resolved prospectively in EXT-1 | Medium | done | see section 22 |
| Uncertainty and seeds | comparators use 0 to 8 seeds, rarely test | yes: 10 seeds, BCa, exact Wilcoxon, Holm on the primary contrast family | High | no | strength |
| Heterogeneity beyond a range statistic | rare in FL | yes: family x client x seed variance components (12.1) | Medium | no | added (class C) |
| External-dataset replication | Bi et al. and others use Drebin/AndroZoo; none replicates a decomposition | no | High | only if a suitable corpus exists | not feasible with audited public data (sections 30, 31) |
| Dose over peer samples, exact effective dose | Breitholtz (labels per client), Otani (missing mass), CyberForce (peer fraction), CELEST (client count) | yes: exact effective dose 10 to 200 in the extension; rises, no saturation | Medium | done | **Done [D]** (33.2) |
| Temporal generalization (LAMDA is longitudinal) | LAMDA, concept-drift literature | not the question of this study | Medium | not for this claim | limitation |
| Communication and privacy costs | most FL papers | out of scope | Low | no | limitation |

## 29. Novelty Assessment [D, positioning only]

Bounded literature audit (open-access retrieval and citation chaining; no priority claim) with an identification-based verdict rule (29.2). Final result: **0 DIRECT, 4 PARTIAL, 34 ADJACENT, 3 NONE** over 41 rows. The contribution is narrowed to the volume-matched decomposition and its evaluation (29.6): the individual arms (local-versus-federated on a missing class, an unmatched absent-everywhere arm, a peer-holder sweep, robust aggregators on an absent malware) have precedent, chiefly in CyberForce.

### 29.1 Reading depth (what was actually read)

Depth labels are conservative: "full text" only where the body including experiments was read. "Verified" marks papers re-read independently in the latest pass; "prior note" marks depth taken from the earlier note and not re-read.

| Depth | Papers |
|---|---|
| **Full text** | CyberForce (arXiv 2308.05978v4, the TDSC author manuscript), CELEST (arXiv 2205.11459), FLEKD-IDS (Shen et al., arXiv 2401.11968), Shao/Otani et al. (IEICE 2026, J-STAGE), Popoola et al. (IEEE IoT-J 2021, accepted-version author manuscript, DOI 10.1109/JIOT.2021.3100755), Breitholtz/Zec et al. (arXiv 2508.18774), Sci. Rep. 2025 rare-attack federated transfer learning (s41598-025-02068-x, publisher XML), PROTEAN (arXiv 2507.05524), ZAID (arXiv 2602.16098), Entente (NDSS 2026, arXiv 2503.14284), FedVLS (arXiv 2401.02329), FedP3E (arXiv 2507.07258), Ciaramella et al. (IST 2026), Ishfaq et al. (PLOS One 2026), FedCKD (PAKDD 2026), Liu et al. (Cybersecurity 2026, prose only); earlier-pass notes: FedAwS, GLFC, CELM and nine security-venue papers (Botacin RAID 2024, Rey et al., Sarhan et al., FedCRI, FedIoC campaign, LiM, DW-FedAvg, FedHGCDroid, drift-aware federated continual learning) |
| **Main text or targeted** | MAP, Bi et al., FedGELA, FedMR, FedRS, FedLMD, FedRoD, FedLC, FedNTD, FedCollab and the negative-transfer survey |
| **Secondary descriptions only** | An FGCS 2025 LLM-assisted federated IDS (S0167739X25006132, publisher returned 403) |
| **Abstract or snippet only** | Taiwo et al., COR-FL, M2FD, FALCON, FL-MalDrift (skim), Xenos et al., Serpanos et al., the contribution-estimation papers, FAMCF/EC2/Meta-MAMC, FedProto family, FedExIT, "Who to trust" |
| **Unavailable (abstract only after retries)** | FID-SPA (IEEE IoT-J 2026, doi 10.1109/JIOT.2026.3717956) and FEDroid (IEEE TIFS 2023, doi 10.1109/TIFS.2023.3287395): OpenAlex and Semantic Scholar report closed access, no arXiv or repository copy; Unpaywall was not queried because it requires an e-mail address |

Dataset papers (LAMDA, KronoDroid, MH-1M, AndroTruth, McNdroid, Maloid-DS, AMD, CICMalDroid, CCCS-CIC-AndMal-2020) were read for dataset facts only and are not collision candidates.

**Search and method.** About 25 discovery calls on a general academic index and an arXiv/alphaXiv discovery tool, about 200 distinct records screened by title and abstract, plus a proceedings-level sweep of security venues (USENIX Security, CCS, NDSS, RAID, DIMVA, ACSAC, IEEE S&P, DSN, Computers & Security, TDSC, TIFS, TOPS) that surfaced RAID 2024 (Botacin et al.), FEDroid, M2FD and one NDSS 2022 federated-intrusion paper; these indexes do not expose proceedings reliably, so absence from results is not evidence of absence. Targeted searches for "hidden family", "held-out family", "unseen family", "zero-day family", "complementary knowledge", "negative transfer" and "leave-one-family-out" combined with federated or malware terms found no direct collision. Forward citations: CELEST (6 to 12 citing works) and CyberForce (8 to 11) were chained through OpenAlex and Semantic Scholar without identifying parameters and contained nothing relevant; Shao/Otani forward citations were not yet indexed. Alternative-terminology searches ("class-missing federated", "label skew absent class", "unseen malware family federated peer", "missing class support rare class") surfaced two intrusion-detection papers (FLEKD-IDS, the Sci. Rep. 2025 paper). The federated intrusion-detection literature commonly uses "drop attack class k at client j" designs and is under-sampled here; such papers typically reach PARTIAL through a local-versus-federated contrast, not through the CTK decomposition. Checklist applied to each read paper: problem; how client labels are created; absence by design or incidental; controlled single-client removal with the rest matched; volume matching; class removed everywhere as control; isolation of the peer effect for the client lacking the class; evaluation population; dose or support sweep; worst-client or per-client analysis; full-exposure reference; natural versus artificial scarcity; representation-level explanation; pooling versus class-specific decomposition.

### 29.2 Collision matrix

Columns: Miss = missing/vacant/disjoint classes at clients; Rem = controlled removal of a specific class from a specific client; Match = total sample size matched; Abs = class removed from all clients as a control; Dec = pooling-versus-class-knowledge decomposition; Dose = peer-sample or peer-fraction dose of the missing class; Own = own-domain evaluation of the missing class at the target client; Wst = worst-client analysis; Nat = artificial intervention validated against natural scarcity; Full = full-exposure or centralized reference; ExpRep = exposure-versus-representation diagnosis. y / p (partial) / n (not found in what was read); for abstract-only rows "n" means "not visible" and is weak evidence.

Verdict rule (final, stated so the counts can be reproduced). Criteria scored from the text read: **A** deliberate local absence (a named class or family made absent at identified clients while at least one peer holds it); **B** a metric specific to the locally absent class; **C** an exposure contrast that holds the deprived client's own data fixed and varies its access to the class through collaboration: (i) local-only versus a federation in which peers hold it, (ii) peer-present versus absent-everywhere, or (iii) a sweep over peer holders or peer samples. IID or centralized references, method-versus-method comparisons and forgetting diagnostics do not count as C, because they change the deprived client's own data or do not vary peer exposure. **D** CTK identification: C(ii) with training volume otherwise matched plus a local-only arm, used to split the gain into generic pooling and class-specific transfer. DIRECT = A + B + D; PARTIAL = A + B + C (borderline when a criterion is only partial); ADJACENT = relevant problem or method without A, B and C together; NONE = dataset or non-federated work. The earlier rule counted any reference condition (including IID or centralized) as PARTIAL and therefore scored problem overlap rather than overlap in identification strategy; it was replaced for that reason, not to reduce collisions (the new rule also adds FLEKD-IDS as PARTIAL).

| CELEST (HTTP-log threat detection, two university networks; PR-AUC and FPR at recall 0.9, not recall) | full | y | p (family swapped between the two networks) | n | p (label budget 0 anomalies remain unlabeled) | n | p (client count 4 to 30) | p (two sites) | n | n | p | n | PARTIAL |
| CyberForce (federated RL for moving-target-defence mitigation; action accuracy, not detection) | full | y | p (fraction of clients missing a malware) | n | p (100% missing, not matched) | n | p (fraction of peers holding) | p | n | n | p (IID only) | n | PARTIAL |
| FedVLS, Guo et al. (images, text; global accuracy) | full | y | n | n | n | n | n | n | p (client-level class-wise accuracy) | n | p | p | ADJACENT (was PARTIAL) |
| Breitholtz/Zec et al. (images; global accuracy) | full | y | p (label-set size) | y (2,000 samples per client) | n | n | p (labels per client) | n | n | n | n | n | ADJACENT (was PARTIAL) |
| Shao/Otani et al. 2026 (fall detection, binary, SisFall; recall, F1, AUCPR) | full | y | p (all positives withheld from ceil(K rho) clients) | n | n | p (theory: irreducible bias) | p (missing mass rho) | n | n | n | y (rho = 0) | n | PARTIAL |
| Bi et al. (Android Drebin/AndroZoo, SMS; global accuracy) | main | y (k families per client) | n | n | n | n | p (k only) | n | n | n | y | n | ADJACENT (was PARTIAL) |
| FedP3E, Darwish et al. (N-BaIoT, 3 clients; global accuracy) | full | y | n | n | n | n | n | n | n | n | p (IID) | n | ADJACENT (was PARTIAL) |
| MAP, Li et al. (images) | main | y | p (centralized targeted-class experiment) | p | n | n | p (number of classes) | n | p | p | p | p | ADJACENT (was PARTIAL) |
| Ishfaq et al. zero-day federated ensemble (Win32 malware images, 28 families) | full | y | n | n | p (family absent everywhere, no target-only arm) | n | n | n | n | n | n | n | ADJACENT (was PARTIAL) |
| FLEKD-IDS, Shen et al. (CICIDS2019, 7 clients each dropping one attack class; per-class detection) | full | y | y (one class per client) | n | n | n | n | n | n | n | n | p | PARTIAL (new) |
| Sci. Rep. 2025 rare-attack federated transfer learning (NIDS; attacks excluded at some clients) | full | y | p | n | n | n | n | p (per-client confusion matrices) | n | n | n | n | ADJACENT (new; method-versus-method only) |
| Entente (NDSS 2026, federated graph intrusion detection; full text) | full | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Popoola et al. (IEEE IoT-J 2021, federated zero-day botnet detection; one traffic class omitted per partition; local comparison is aggregate, not missing-class-specific) | full | y | y | n | n | n | n | n | n | n | p | n | ADJACENT (no class-specific local-versus-federated contrast) |
| PROTEAN (X-IIoTID, 5G-NIDD; per-class local-only versus federated accuracy on classes a participant lacks) | full | p (Dirichlet, incidental) | n | n | n | n | n | p | n | n | n | p (3 seeds) | ADJACENT (absence incidental, fails A) |
| ZAID (IoBT zones; zero-day classes withheld from all training) | full | n | n | n | y (absent everywhere only) | n | n | n | n | n | n | n | ADJACENT |
| FGCS 2025 LLM-assisted federated IDS (one organisation lacks one attack type; with versus without the LLM loop) | abstract | y | y | n | n | n | n | n | n | n | n | n | ADJACENT (method-versus-method, fails C) |
| GLFC, Dong et al. (class-incremental images) | prior note | y | n | n | n | n | n | n | n | n | n | p | ADJACENT |
| CELM, Ukaye et al. (images, dermatology) | prior note | y | n | p | n | n | n | n | n | p | p | p | ADJACENT |
| FedRS, Li and Zhan (images; restricted softmax) | main | y | n | n | n | n | n | n | n | p | n | p | ADJACENT |
| FedLMD, Lu et al. (images; label-masking distillation) | main | y | n | n | n | n | n | n | n | n | n | p | ADJACENT |
| FedCKD, Le et al. (images, logs; label-exclusive clients) | full | y | n | p | n | n | n | n | n | n | y | n | ADJACENT |
| FedGELA; FedMR (images; partially class-disjoint data) | main | y | n | n | n | n | n | p (personal accuracy on each client's own class mix) | n | p | n | p | ADJACENT |
| FedRoD; FedLC; FedNTD; FedAwS (images) | targeted; targeted; targeted; prior note | y | n | n | n | n | n | p (per-class local-model diagnostics) | n | p | n | p | ADJACENT |
| Ciaramella et al. (Android, AMD plus Play crawl, binary; Dirichlet over benign/malware only) | full | n | n | n | n | n | n | n | n | n | y | n | ADJACENT |
| Liu et al. Cybersecurity 2026 (Windows BIG 2015 family classification, FedBN) | full (prose) | n (class-dominant, none absent) | n | n | n | n | n | p (local adaptation) | n | n | y | n | ADJACENT |
| FEDroid, Fang et al. (Android) | abstract (unavailable) | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| FID-SPA (IoT, 2026) | abstract (unavailable) | y | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Taiwo et al. (malware images, class entropy) | abstract | p | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Botacin et al. RAID 2024 (three-region AV data); Rey et al. (N-BaIoT, seen versus unseen devices) | prior note | n; p | n | n | n | n | n | n | n | n | y | n | ADJACENT |
| Android FL group: FedHGCDroid, FedDRC, uitAnDiNeFed, DW-FedAvg, Lee, Kushwaha | mixed | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Drift group: FL-MalDrift, M2FD, FALCON, COR-FL, SCFM-FedRL, drift-aware federated continual learning | mixed | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Security-organisation FL: Xenos et al., Serpanos et al., Sarhan et al. (CTI), FedCRI, FedIoC campaign | abstract to prior note | n | n | n | n | n | n | n | n | n | y | n | ADJACENT |
| FedExIT (medical images) | abstract | y | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| "Who to trust" (federated distillation, class mismatch) | abstract | y | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| FedProto, FedSA, FedHCL (prototype FL) | abstract | p | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| FAMCF, EC2, Meta-MAMC (few-shot Android family classification, non-FL) | abstract | y | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| Contribution estimation and data valuation (Wei, Zhu, Chen, Li) | abstract | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| FedCollab, Bao et al. (negative transfer) | targeted | n | n | n | n | n | n | n | n | n | n | n | ADJACENT |
| LAMDA, Haque et al. (primary data source) | dataset | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NONE (data) |
| KronoDroid, MH-1M, Maloid-DS, AMD, CICMalDroid, CCCS-CIC-AndMal-2020 (datasets) | dataset | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NONE (data) |
| Molina-Coronado et al. (fair comparison of Android detectors, non-FL) | abstract | n | n | n | n | n | n | n | n | n | n | n | NONE |

Counts under the final rule over the 41 rows above (a row may group closely related papers): **0 DIRECT, 4 PARTIAL (CyberForce, CELEST, FLEKD-IDS and borderline Shao/Otani), 34 ADJACENT, 3 NONE**. Popoola et al. is ADJACENT: although its federated tables report the omitted class, its local-only comparison reports aggregate metrics and does not identify transfer for that class. Under the earlier, looser rule the first 34 rows were 0/9/22/3; six of those PARTIALs became ADJACENT (29.3). No read paper combines controlled single-client removal, a volume-matched absent-everywhere control and a pooling-versus-family decomposition. Clarification of B: a class-specific metric on a test set shared by all clients counts; own-domain evaluation is scored in the checklist, not in the rule.

### 29.3 PARTIAL collisions and changed verdicts

PARTIAL under the final rule:

- **CyberForce (full text; the strongest collision).** Federated RL for moving-target-defence mitigation; the metric is the global model's action accuracy on the absent malware, not detection. Its weak non-IID experiment (Sec. V-B4, Tables VIII to X) removes one malware from m of N clients: m = N is a federated absent-everywhere arm, m < N is peer-present, the sweep over m is a peer-holder dose, and Figs. 4 to 5 plot local-only curves. So all three CTK arms exist in rough form. Nothing is volume-matched, the gain is not decomposed, the deprived client's own domain is not evaluated, and there are no seeds or intervals. It compares FedAvg, Krum and Trimmed Mean on the absent malware (Tables IX and X) and warns that robust aggregators erase rare holders; its Fig. 4 also has a family absent everywhere (Beurk) with a near family missing at one or seven clients (Bdvl). It explains transfer by "similar behaviors" within a family. Table IX (FedAvg still 89 to 98% with 7 to 10 of 10 clients missing) contradicts the prose and Table X (0% at 20 of 20); only Table X and the prose are usable.
- **CELEST (full text).** Two university networks with malware families swapped between them (Table III); local versus global PR-AUC on the family the deployed network has not seen (for example DEM 0.26 locally versus 0.75 federated). C(i) only: no matched absent-everywhere arm (the label-budget-0 arm is unmatched), no decomposition ("malware families share some common characteristics"), no seeds or intervals; one Table III value (0.5483) appears twice and should not be cited.
- **FLEKD-IDS, Shen et al. (full text; new).** Seven CICIDS2019 clients each drop one attack class ("Drop Label k", Table IV); each local model detects its dropped class at 0.00% while the federated model detects it (for example UDPLag 75.28%). C(i) on a deliberately deprived client; no absent-everywhere arm, no matching, shared test set, no seeds.
- **Popoola et al. 2021 (accepted-version author manuscript read).** One traffic class is omitted from each partition; Tables II–V describe those omissions and Tables XV report per-class federated results. The localized-learning comparison in Tables XVI–XVII reports aggregate client metrics, not the omitted class's local-only performance. It therefore does not establish a class-specific local-versus-federated exposure contrast (C) under the frozen rule and is ADJACENT. The study has no matched absent-everywhere arm or pooling decomposition. DOI: [10.1109/JIOT.2021.3100755](https://doi.org/10.1109/JIOT.2021.3100755).
- **Shao/Otani et al. 2026 (full text; borderline).** Withholds all positive (fall) windows from a fraction rho of clients (0 to 0.8), rho = 0 as full exposure; recall, F1 and AUCPR over 5 seeds with paired t-tests; the "misleading convergence certificate" (accuracy flat while recall falls). C(iii) is a missing-mass sweep; B is only partial because recall is measured on a pooled held-out test set; the whole positive class is absent, not a family within it; differences about 0.03.

Changed from PARTIAL to ADJACENT (each lacks A, B or C as defined; the ingredients they share are acknowledged in 29.4):

- **FedVLS.** Vacant classes arise incidentally from Dirichlet or shard splits; the only per-client comparison is the initial global versus the updated local model (a forgetting diagnosis), not an exposure contrast; 3 runs with oracle round selection.
- **Breitholtz/Zec et al.** Random label sets at matched volume (2,000 samples per client) with 10 seeds and bootstrap intervals, but only global test accuracy; no metric on a locally absent class.
- **Bi et al.** Android family skew (k random families per client), global metrics and a centralized reference only; the plus-minus values are the SD over the last 10 rounds, not seeds.
- **FedP3E.** Disjoint classes by design across three N-BaIoT silos, but only global metrics and IID or method comparisons; single run.
- **MAP.** Random incomplete classes; its Fig. 7 is a centralized experiment scoring observed classes (the reverse question); relevant to negative pooling.
- **Ishfaq et al.** Families absent from every node (an absent-everywhere number, 94.6 +/- 0.4; leave-one-family-out 87.1 +/- 0.6) with no node deprived while peers hold the family; internally inconsistent (4, 7 and 28 nodes).

### 29.4 What the closest read designs do not do

No read paper has: a specific family removed from a specific client with the rest of training matched; that family removed from all clients as a matched control paired with a peer-held condition; a decomposition of collaboration gain into generic pooling and family-specific peer knowledge; a peer-sample dose for one family; own-domain and worst-client evaluation of the hidden family; a like-for-like natural versus artificial comparison of the same estimand. Overlaps to acknowledge: CyberForce contains an unmatched federated absent-everywhere arm, a peer-holder sweep and local-only curves in one experiment; local-versus-federated recall on a deliberately dropped class (CELEST, FLEKD-IDS); absent-everywhere numbers (Ishfaq et al., CELEST budget 0); missing-mass sweeps (Otani et al.); matched per-client volume with seeded bootstrap intervals (Breitholtz/Zec et al.); MAP's centralized targeted-class experiment; natural and synthetic splits side by side in MAP and CELM; Android family skew (Bi et al.); mechanism explanations at the logit, classifier or prototype level (FedVLS, FedGELA, FedMR, FedRS, FedP3E).

| Ingredient | Verdict from read literature |
|---|---|
| locally missing family/class at a client | present (CELEST, CyberForce, FedVLS, MAP, Bi, FedP3E, Otani, CELM, GLFC) |
| matched controlled removal | partial (FLEKD-IDS one class per client, Otani removal fraction, CyberForce m-of-N removal, MAP centralized analogue); not matched to volume |
| class absent from all clients as control | partial (CyberForce m = N paired with m < N but unmatched; Ishfaq zero-day and CELEST budget 0 unpaired) |
| full-exposure reference | present in several (Otani rho = 0, Bi, Ciaramella, FedCKD centralized bound) |
| decomposition total / pooling / complementary | not found (Otani: theory of a bias floor only) |
| own-domain evaluation of the hidden class | partial at two sites (CELEST, CyberForce per malware); not with worst-client |
| worst-client evaluation | partial per-client diagnostics (FedVLS, MAP); no worst-client CTK |
| peer dose | partial (peer fraction, missing mass, client count, labels per client); not peer samples of one family |
| natural-scarcity check of the same estimand | not found (natural and synthetic side by side in MAP, CELM) |
| exposure-versus-representation diagnosis | partial mechanism explanations; no full-exposure plus cross-model diagnosis |

### 29.5 Reassessed candidate contributions

| Candidate | Verdict | Reason |
|---|---|---|
| N1 controlled-exposure decomposition (volume-matched family-absent-everywhere control separating pooling from complementary knowledge) | PLAUSIBLE DIFFERENTIATOR, narrowed | CyberForce pairs an unmatched federated absent-everywhere arm with peer-present arms and local curves, so the arms themselves are not new; the volume matching and the decomposition into pooling and family-specific transfer were not found. |
| N2 malware-family CTK in Android FL | PLAUSIBLE DIFFERENTIATOR | Bi et al., Ciaramella et al. and FedP3E are the nearest Android/IoT FL papers; none measures per-family counterfactual recall for a locally missing family. |
| N3 own-domain decomposition | PLAUSIBLE DIFFERENTIATOR | Not found; CELEST and CyberForce evaluate the locally missing family at two sites and one federation, without decomposition. |
| N4 worst-client CTK | PLAUSIBLE DIFFERENTIATOR (weak) | Per-client diagnostics exist; worst-client class-specific complementary effect not found. Worst-client fairness is generic, so this is a combination claim only. |
| N5 natural-scarcity validation | PARTIAL COLLISION | Reporting natural and synthetic partitions together is established (MAP, CELM); a check that a controlled-removal decomposition reproduces at the same magnitude under natural scarcity was not found. |
| N6 peer-sample dose response | PARTIAL COLLISION | Sweeps of peer fraction (CyberForce), missing mass (Otani et al.), classes or labels per client (MAP, Breitholtz et al.) and Dirichlet skew (FedVLS, CELM) exist; a sweep of peer samples of one missing family linked to the incremental benefit was not found. |
| N7 exposure-versus-representation diagnosis | PLAUSIBLE DIFFERENTIATOR | Mechanism explanations exist (MAP proxy collapse, FedVLS logits, GLFC gradients, FedGELA/FedMR classifier geometry); a full-exposure plus independent-model-class diagnosis of family-level failures was not found. |
| N8 combined framework | PLAUSIBLE DIFFERENTIATOR | No paper provides essentially the same measurement framework; most ingredients individually have partial precedent. |

Weakened relative to the first audit: N5 and N6 (partial collisions), "Android malware FL with families absent from clients" (Bi et al.), disjoint malware classes across clients (FedP3E), and the empirical direction that federation helps on a locally unseen family (CELEST, CyberForce, Otani et al.). Differentiated: N1 and N8, because no read paper has a matched family-absent-everywhere control paired with a peer-held condition or a decomposition.

### 29.6 Strongest defensible positioning (narrowed)

Prior work already establishes that classes absent from a client are poorly recognized (FedVLS, MAP, Otani et al.), that federated clients benefit on a class or malware they lack locally (CELEST, CyberForce, FLEKD-IDS), that the number of clients lacking a malware can be swept up to none holding it (CyberForce), and studies Android and IoT malware FL under non-IID partitions (Bi et al., FedP3E, Ciaramella et al.). Wording supported by the final audit:

> Prior work shows that a client can benefit from federation on a class or malware it lacks locally (CELEST; CyberForce; FLEKD-IDS) and that missing-class or missing-mass conditions affect classification performance (Shao/Otani et al.; Popoola et al.). CyberForce further varies how many clients lack a malware, up to none holding it, and compares robust aggregators on that absent malware. In the literature we could access, we found no study that pairs a peer-present arm with a volume-matched absent-everywhere arm for the same deprived client, which is what separates generic pooling from family-specific knowledge held by peers, and none that reports this separation for Android malware families on the deprived client's own data and on the worst client, with an exact peer-sample dose, a coherent wrong-family placebo and multi-seed uncertainty. FEDroid and FID-SPA full text remain unavailable.

Dose and natural scarcity are individually partially anticipated and are not presented as independent novelty.

### 29.7 Limits

- In the final pass CELEST, CyberForce, Breitholtz/Zec, Shao/Otani, FLEKD-IDS and the Sci. Rep. 2025 paper were read in full and 13 others in targeted sections; earlier passes read further papers in full; several relevant papers are main-text, targeted or abstract-only, where an "n" is weak evidence of absence. FID-SPA (IEEE IoT-J 2026, doi 10.1109/JIOT.2026.3717956) and FEDroid (IEEE TIFS 2023, doi 10.1109/TIFS.2023.3287395) remain unavailable (paywalled, no preprint); FID-SPA's abstract (incomplete attack categories per client) makes it the unresolved paper most likely to be PARTIAL. An institutional copy should be obtained before any submission. The CyberForce publisher version was not read (the author manuscript was).
- Cybersecurity 2026 was read as prose through a third-party conversion, without table cells; the Ishfaq et al. and CyberForce sources are internally inconsistent and are cited only where consistent.
- Security-venue proceedings (USENIX Security, CCS, NDSS, S&P, RAID, ACSAC, DIMVA, DSN, TDSC, TIFS, TOPS, Computers & Security) were covered through index and web search only; absence from search is not evidence of absence. The federated intrusion-detection literature is under-sampled. Forward citations were obtained for CELEST and CyberForce only.
- Fairness-in-FL and negative-transfer literatures were sampled, not audited in depth. Reviewer-relevant comparators are assessed in section 28.1.
- Re-run this audit at submission time.

### 29.8 Closest ten papers

1. CyberForce (IEEE TDSC; arXiv 2308.05978), m-of-N removal with an unmatched absent-everywhere endpoint, a peer-holder sweep and local curves; mitigation, not detection; PARTIAL, full text.
2. CELEST (arXiv 2205.11459), local versus federated PR-AUC on a family held by the peer network; HTTP-log threat detection; PARTIAL, full text.
3. FLEKD-IDS, Shen et al. (arXiv 2401.11968), one attack class dropped per client, local 0% versus federated detection; PARTIAL, full text.
4. Shao/Otani et al. 2026 (IEICE), withheld positives, missing-mass sweep, recall over 5 seeds; PARTIAL (borderline), full text.
5. Sci. Rep. 2025 rare-attack federated transfer learning, attacks excluded per client, per-client confusion matrices; ADJACENT, full text.
6. FedVLS (AAAI 2025), vacant-class accuracy collapse; ADJACENT, targeted re-read.
7. Ishfaq et al. (PLOS One 2026), zero-day families absent everywhere; ADJACENT, full text earlier.
8. FedCKD (PAKDD 2026), label-exclusive clients; ADJACENT.
9. Bi et al. 2024, Android malware FL with family-skewed clients; ADJACENT.
10. MAP (IEEE TKDE 2024), incomplete classes and a centralized experiment on negative pooling; ADJACENT.

## 30. External Dataset Feasibility [D, positioning and feasibility only]

Requirements taken from the frozen design: family labels with enough support (eligibility `peer_min_fit` 150, `federation_min_test` 50, `own_domain_min_test` 15, `target_min_fit` 20, `target_min_remaining_fit` 500, inside a 60/20/20 identity-safe split), benign samples at every client (5% FPR calibration needs at least 10 expected benign exceedances), a defensible client/domain axis, stable identity, static features, and enough families for a primary set of 7 and a disjoint replication set of 8. Facts below come from the datasets themselves where downloaded and otherwise from the dataset pages or papers; unverified items are marked.

| Dataset | Family labels | Benign | Client/domain axis | Identity | Family support (verified) | Access | Verdict |
|---|---|---|---|---|---|---|---|
| **KronoDroid** (processed CSVs, downloaded and audited, section 31) | 240 (real device) / 209 (emulator), AVClass-style, partly generic | yes (36,755 / 35,246) | chronological only: two APK-internal file dates, no market | sha256 + package | 35 families with >=100 rows, 19 with >=250 (real device) | GitHub, no stated licence, "no other restriction" besides citation | **MARGINAL** |
| **McNdroid** (metadata and hash overlap computed, section 32) | AVClass2 (same labelling as LAMDA), rare families collapsed to "singleton" | yes (535,358) | none (client axis would come from the LAMDA join) | sha256 | 73 non-singleton families with >=250 malware, 32 with >=1000 | Hugging Face, CC-BY-4.0, ungated | **not independent** (81% of its apps are in LAMDA); representation check only |
| **CCCS-CIC-AndMal-2020** (published per-family table parsed) | 191 families in 14 categories | yes: 200k, drawn from AndroZoo (likely overlaps LAMDA benign) | none: no dates or market on the page | not on the page | 52 families with >=250, 22 with >=1000 (192 rows, 170,974 samples) | free redistribution with citation; static features must be regenerated from APKs | WEAK (support yes, client axis no) |
| **MH-1M** (Dataverse metadata sampled) | only 4 coarse VT categories; family names only inside a 13 GB label dump | yes: 1,221,421 | year only (2010 to 2024) | sha256 | not available from the metadata | CC0; features 50.9 GB | WEAK, and AndroZoo-only (overlaps LAMDA) |
| **AndroTruth / ThreatIntel-Andro** | expert-report labels, 187 (146) families | **no** | VT first-submission date | sha256 | long tail, at most about 15 families >=250 | GitHub; no explicit licence; APKs on request | NOT SUITABLE (malware only) |
| **Drebin, AMD, MalGenome, CICMalDroid 2020** | Drebin 179 families (5,560, malware only), AMD 71 families (24,650, malware only), MalGenome discontinued, CICMalDroid categories only | mostly no | none | mixed | small | various | NOT SUITABLE (not re-verified by download; based on the papers) |
| **Maloid-DS, OmniDroid** | Maloid-DS 345 families (47,971 malware, about 139 per family), OmniDroid none usable | unclear | none found | unclear | not obtained | no public download found | UNKNOWN / NEEDS ACCESS |
| **Ciaramella et al. (IST 2026) data** | malware side is the public AMD (71 families; 15 with >=200 samples, 7 with >=1,000, more than 40 under 100) | benign half is an unreleased Play crawl | none: clients are a synthetic Dirichlet partition over benign/malware only | none released | as AMD | "on request" only | NOT SUITABLE as released (a replication would have to be built on AMD with its own benign source and split) |
| **Droidware** (Mendeley/IEEE DataPort) | family and market fields unconfirmed | yes (265,423 apps, 2019 to 2026) | unconfirmed | unconfirmed | not verified | public dataset | UNKNOWN (field list must be checked by hand) |

**Verdict on a second independent Android dataset: DO NOT RUN, DEFER.** No audited public corpus meets all requirements. The only one with an independent source, benign samples, a family column and a date axis that could be downloaded and inspected (KronoDroid) fails the unweakened gate for the 7+8 design and would test a different, era-confounded question. A poorly matched replication would be less informative than an explicit one-corpus limitation. Re-open only if a corpus with real market or source metadata, benign samples and at least 15 families with several hundred de-duplicated samples at three or more clients becomes available.

### 30.1 Can the CTK protocol be reused, per plausible candidate?


Plausible candidates after screening: KronoDroid (directly audited and marginal because its emulator/real-device client split is era-confounded), CCCS-CIC-AndMal-2020 (support but no client axis), McNdroid and MH-1M (not independent; useful only for a representation or feature-extraction replication).

| Question | KronoDroid | CCCS-CIC-AndMal-2020 | McNdroid / MH-1M |
|---|---|---|---|
| 1. Same estimands unchanged? | yes, once clients exist | yes | yes |
| 2. Same family eligibility logic? | yes, but few families likely meet 150/50 support at two or more clients | yes for large families | yes |
| 3. Same 60/20/20 identity-safe split? | only if per-sample hash/package are available; not verified | not verified | SHA-256 available; package names in MH-1M |
| 4. Family-absent-everywhere control? | yes (data operation) | yes | yes |
| 5. Full exposure? | yes | yes | yes |
| 6. Own-domain evaluation defined? | needs hidden-family test support at each client | needs an invented client axis | yes by era |
| 7. Peer dose manipulable? | limited by per-family support | yes | yes |
| 8. Primary and replication family sets? | uncertain (about 172 samples per family on average) | probably | yes |
| 9. Client definitions defensible? | era windows are defensible but confound families with time | **no** (no market, time or source) | era windows only |
| 10. Design change so large it is a different study? | moderate: different features (200 static), era-based clients, unknown label provenance: a conceptual replication | large: clients would have to be invented | small, but it is then a re-analysis of largely the same apps, not an independent replication |

## 31. KronoDroid Direct Data Audit [D]

Processed files were downloaded from https://github.com/aleguma/kronodroid (HEAD `c6ec342167bc449967a802824d068900ac8120c5`, no Git LFS, 178 MB, stored under `data/kronodroid/raw/`, git-ignored; checksums and byte sizes in the working notes). Raw logs and APKs need an emailed request and were not fetched. The repository reports no licence; the README releases the data for research "with no other restriction than ... cite the KronoDroid paper".

| | Emulator | Real device |
|---|---|---|
| Rows | 63,991 | 78,137 |
| Benign / malware | 35,246 / 28,745 | 36,755 / 41,382 |
| Distinct families (`MalFamily`) | 209 | 240 |
| Malware rows with no family | 91 | 165 |
| Families with >=100 / 250 / 500 / 1000 rows | 27 / 14 / 11 / 8 | 35 / 19 / 14 / 9 |
| Largest family share | 22.8% (Airpush/StopSMS) | 18.9% |
| Feature columns | 483 (289 dynamic syscall counts, 166 binary permission bits, 177 to 186 constant) | 484 |

- **Label provenance:** not documented; names are AVClass-style (Airpush/StopSMS, Waps/Simhosy) and several are generic (Agent, Malap, Boogr, FakeApp). `Detection_Ratio` and `Scanners` are VirusTotal columns and must be excluded as label leakage.
- **Timestamps:** only two per row (earliest/latest modification date of files inside the APK, not VirusTotal first-seen); about 4% are placeholders or impossible dates; about 63% of benign apps date from 2011 while malware clusters in 2012 to 2014, so benign and malware are strongly separated by year.
- **Identity:** `Package` and `sha256` exist; 4 duplicated hashes with conflicting labels; about 5,000 to 5,700 packages have several versions; 185 to 249 packages occur as both benign and malware, so a component-level identity-safe split is necessary. Emulator and real-device sets share 99% of sha256 (63,320), so they are one replication opportunity, not two.
- **Candidate clients, chosen a priori from metadata only** (Android-version eras <=2013, 2014 to 2016, 2017 to 2018, 2019 to 2020; equal-duration 3.25-year windows; support-balanced windows), with sha256 or package de-duplication. The unweakened primary eligibility rule with a 60/20/20 approximation (real device):

| Construction | Eligible targets | Distinct eligible families | Families also passing the 600-row candidate floor | Clients OK at 5% FPR |
|---|---|---|---|---|
| Eras, hash dedup | 35 | 16 | 14 | 4/4 |
| Equal-duration, hash dedup | 34 | 13 | 12 | 4/4 |
| Support-balanced, hash dedup | 40 | 15 | 14 | 4/4 |
| Eras, package dedup | 28 | 13 | 11 | 3/4 |
| Equal-duration, package dedup | 25 | 11 | 9 | 4/4 |
| Support-balanced, package dedup | 25 | 12 | 10 | 3/4 |

Emulator results are weaker (at most 9 families). Eligible pairs concentrate in the same handful of families in every construction, several of them generic labels.

**Feasibility verdict: MARGINAL.** At most 14 families pass with the candidate floor (7 primary plus 7 replication, zero slack, none under package-level dedup); clients are purely chronological, so hidden-family identity is confounded with era; benign/malware year separation confounds detection with time; the feature space (166 permission bits plus syscall counts) is not the 925-feature LAMDA space, so effects would not be like-for-like. **Decision: DO NOT RUN.** The one-corpus limitation is retained.

## 32. Representation-Replication Feasibility (McNdroid) [D]

Hypothesis that a representation replication could test (N7): families that remain poorly detected under full exposure in the LAMDA static space (hiddad, gappusin, revmob) are rescued by a richer representation.

- **Data:** Hugging Face `IQSeC-Lab/McNdroid`, CC-BY-4.0, ungated; metadata 858,859 apps (535,358 benign, 323,501 malware), 2013 to 2025 without 2015; three aligned representations by sha256: static binary 2,390 features (93 MB), a report-derived "JSON behavioural" vector of 17,483 features (0.3 GB; the contents are static-analysis-report derived, not sandbox traces, so "dynamic" is a misnomer), and a call-graph vector of 2,793 features (9.66 GB dense).
- **Overlap with LAMDA (computed by sha256):** 696,012 apps, 81.0% of McNdroid and 69.0% of LAMDA; binary label and year agree on 100%; family labels agree on 100% wherever neither side is "singleton" (McNdroid collapses rare families), so the labelling is derived from the same AVClass2 run. It is therefore **not independent external validation**.
- **Family support (McNdroid malware / LAMDA malware / overlap):** hiddad 2,520 / 2,586 / 2,227; gappusin 7,326 / 9,036 / 4,055; revmob 6,739 / 6,873 / 5,958; leadbolt 6,416 / 6,589 / 4,502; adwo 5,077 / 6,096 / 2,104; youmi 4,278 / 5,021 / 3,227; smsreg 14,567 / 15,114 / 11,226; kuguo 14,772 / 20,966 / 9,351; dnotua 10,574 / 10,171 / 9,980; zdtad 1,973 / 2,986 / 1,267 (others in the working tables).
- **Feasibility:** technically feasible; hashes are aligned across all three representations. Costs: a new data-source adapter and a separate preprocessing namespace for the overlap subset (about 19% of McNdroid and 31% of LAMDA apps have no counterpart, mostly 2013 to 2014 and 2024 to 2025); the graph modality needs streaming; a separately frozen protocol; model input dimensions differ.
- **Status: run.** A first development harness (pooled threshold) led to a wrong "full run not justified" call (33.3); after the corrected per-client-threshold harness the study was frozen (Amendment A2) and run as EXT-REP with fresh seeds 330 to 339 (33.2). Not external validation: 81% overlap and the same AVClass2 labels.

## 33. New Scientific Extensions

Only literature-justified additions were considered. Each was assessed against what the stored evidence already answers. The extension-b studies are separately frozen [D] studies with fresh seeds (protocols and freeze manifest in `docs/temp/extension-protocol/`); none can change the original 9/0/3 gate outcome and none is pooled with seeds 100 to 109, 200 to 209 or with each other. The four extension-b studies use seeds 300 to 339 in disjoint ranges.

| Experiment | Scientific weakness addressed | Existing evidence sufficient? | Status |
|---|---|---|---|
| **EXT-1** own-domain / worst-client permutation control, seeds 200 to 209 | own-domain null control unresolved in v1 | no | **done** (section 20.1; v1 and EXT-1 status in section 22) |
| **EXT-CTRL** coherent wrong-family placebo and robust aggregation, seeds 320 to 329 | "adds generic malware volume or relatedness, not family knowledge"; rare-peer erasure (28.1) | no | **done** (33.2) |
| **EXT-DOSE** exact effective dose, seeds 310 to 319 | saturation and dose thresholds | partly | **done** (33.2) |
| **EXT-LFAM** larger-family explanatory study, seeds 300 to 309 | why CTK varies; predeclared descriptor on more families | no (7 to 8 families, wide intervals) | **done** (33.2) |
| Representation replication on McNdroid (feasibility in section 32) | exposure versus representation (N7); not external validation (81% overlap) | partly (linear and tree models) | **done** as EXT-REP, seeds 330 to 339 (33.2); the earlier "not justified" call was superseded (33.3) |
| External replication on KronoDroid | corpus dependence | no | DO NOT RUN: MARGINAL (section 31) |
| Missing-class-aware baselines (FedRS, FedLC, FedVLS and others) | comparator gap | not applicable | not run; inapplicability argued in 28.1 |
| Broader CTK-versus-pooling dominance study | model-general claim | no | not run unless a general claim is wanted |
| New federated mechanism | headroom | headroom below both triggers | not run |

### 33.1 Feature-novelty mechanism reassessment

After full reading, the literature points to two other candidate mechanism variables: classifier-level margin/logit collapse for vacant classes (FedVLS, MAP, FedLC) and prototype or class-conditional representation distance (FedMR, FedP3E). The originally predeclared descriptor (nearest known-family distance) is the same family-relatedness idea that CELEST and CyberForce themselves invoke, so it remains the most appropriate training-only descriptor and is the one used in EXT-LFAM. Logit and margin variables need trained models on the hidden family and cannot be computed from training-only evidence, so they are not retrofitted into H7 or EXT-LFAM. No additional descriptors were searched.

### 33.2 Extension-b results [D]

Class D, fresh seeds, FedAvg, one corpus. Files in `results/extension-b/`. Frozen designs: `docs/temp/extension-protocol/` (Amendment A1, recorded before any seed 310 to 329 run, is described under EXT-CTRL). Original gate counts remain 9 promoted, 0 narrowed, 3 rejected.

**EXT-LFAM: larger-family feature-novelty study (seeds 300 to 309).** 32 families in 4 batches of 8 (`large-family-selection.csv`), descriptor predeclared as nearest-known-family distance, mean federation test support 723 (minimum 50). CTK is defined for all 32 families; five families have fewer than 10 contributing seeds (umpay 2, anydown 6, gumen 7, feiwo 8, utchi 8). Family CTK: mean +0.068, between-family SD 0.076, within-family seed SD 0.031, reliability 0.83.

| Result | Value |
|---|---|
| Spearman rho, descriptor versus CTK, 32 families | **0.392**, family-bootstrap 95% CI 0.062 to 0.654, p = 0.027 |
| Minimum detectable \|rho\| (power caveat) | about 0.48 |
| rho in the 14 previously used families / the 18 new families | 0.516 (p = 0.059) / 0.395 (p = 0.104) |
| Families with CTK at least +0.03 / at most -0.03 | 21 / 2 (23 with \|CTK\| at least 0.03) |
| Most negative | baiduprotect -0.044, feiwo -0.037 |
| Largest | revmob +0.285, leadbolt +0.240, utchi +0.174, inmobi +0.166 |

Frozen rule: an interval above 0 means a supported moderate explanatory variable. The rule is met, with the caveat that the study cannot reliably detect \|rho\| below about 0.48, so the point estimate is imprecise and the association is neither strong nor causal. Permutation p (9,999 Monte Carlo permutations of the descriptor over families, as the frozen protocol requires) 0.026; the asymptotic Spearman p is 0.027. Seed-level rho over the 10 fresh seeds (frozen descriptive element): median 0.22, range -0.06 to 0.43, positive in 9 of 10 seeds; single seeds are noisier than the family means.

Eligibility-stability sensitivity (no training; `large-family-eligibility-stability*`). The 32 families were frozen from the seed-000 partition without outcomes; re-applying the same eligibility rule to fresh seeds finds 27 eligible in all 10 seeds, utchi and feiwo in 8, gumen in 7, anydown in 6 and umpay in 2 (mean eligible fraction 0.94; 29 to 32 families and 77 to 81 eligible client-family pairs per seed). On the 27 stable families rho is 0.274 (95% CI -0.099 to 0.581). Each single-family deletion among the five leaves a positive rho, but the stable-eligibility interval spans zero. The positive 32-family association is therefore not dependent on any one incompletely eligible family; its inferential strength is sensitive to restricting the analysis to always-eligible families. The frozen 32-family result stays primary. This is a prospective association on 32 families; it does not change the original feature-novelty gate ("rejected", section 23), and the original 7 and 8 family estimates stay as reported.

For the five incompletely eligible families, the table reports contributing extension seeds, eligible client-family-seed pairs, total target-family test rows supporting the family CTK estimate, the frozen novelty distance, mean CTK, influence (full-sample rho minus leave-one-family-out rho), and leave-one-family-out rho. Influence is descriptive; these are five of the frozen 32, not a selected replacement population.

| Family | Contributing seeds | Eligible pairs | Test rows | Novelty | CTK | Influence Δrho | LOO rho |
|---|---|---:|---:|---:|---:|---:|---:|
| umpay | 307, 309 | 2 | 141 | 1.907 | -0.008 | +0.008 | 0.383 |
| anydown | 301, 302, 304, 305, 306, 309 | 6 | 910 | 2.605 | +0.154 | +0.028 | 0.364 |
| gumen | 300, 301, 303, 305, 306, 307, 309 | 7 | 407 | 2.307 | +0.053 | +0.004 | 0.388 |
| feiwo | 300, 301, 302, 304, 305, 306, 308, 309 | 8 | 1,654 | 1.609 | -0.037 | +0.043 | 0.349 |
| utchi | 301, 302, 303, 304, 305, 306, 308, 309 | 15 | 3,482 | 3.194 | +0.174 | +0.024 | 0.368 |

These values reproduce the machine-readable eligibility, family CTK and influence tables. All five individual leave-one-out correlations remain positive. Seed-level rho is positive in 9/10 seeds (median 0.22, range -0.06 to 0.43); the association is broadly positive at the family level but modest and imprecise, with three incompletely eligible families carrying appreciable leverage.

**EXT-DOSE: exact effective dose (seeds 310 to 319).** Peers hold exactly 10, 25, 50, 100 or 200 samples of the hidden family (level 0 and the natural peer-present arm also run). The consistency file checks realised effective dose against the requested level for every checked row (mismatches: 0; training volume identical across levels; target holds no hidden-family rows at level 0). FedAvg, 5% FPR, federation-wide, family-macro CTK:

| Exact effective dose | 10 | 25 | 50 | 100 | 200 | natural peer-present |
|---|---|---|---|---|---|---|
| Pooled family sets | +0.031 | +0.050 | +0.075 | +0.119 | +0.151 | +0.111 |
| Primary set | +0.046 | +0.082 | +0.117 | +0.165 | +0.200 | +0.143 |
| Replication set | +0.017 | +0.022 | +0.037 | +0.078 | +0.106 | +0.081 |

Own-domain, pooled sets: +0.027, +0.047, +0.074, +0.125, +0.150 (natural +0.090). Dose 0 equals family-absent-everywhere (pooled -0.000, interval -0.003 to 0.002). H-DOSE-1 (onset and a family-macro CTK non-decreasing across exact levels) is met in every FedAvg scope except the replication set, own-domain, 1% FPR (CTK 0.0102 at 25 samples, 0.0088 at 50); pooled federation-wide FedAvg onset at 25 samples. (The monotonicity check was corrected in the final verification pass to compare every consecutive level, as frozen; it had compared only the top and bottom levels. Only that secondary cell changed.) H-DOSE-2 (saturation) is **not met**: the increment from 100 to 200 samples is +0.032 (0.020, 0.046) pooled, +0.036 (0.019, 0.059) primary, +0.029 (0.009, 0.055) replication and +0.025 (0.008, 0.047) own-domain, and every interval extends beyond the frozen +/-0.03 band. The claim is bounded: saturation was not observed up to 200 exact peer samples; it does not establish that no saturation exists at larger doses. Independently recomputed from the raw per-run metrics: 0.0305, 0.0504, 0.0750, 0.1193, 0.1512 and increment +0.0319 (0.0201, 0.0463); structural checks 0 mismatches over 1,764 records (every training set 6,000 rows; peers hold exactly d, the target 0), nested draws verified. One structural-warning run: dose-primary seed 317 has a realised-FPR gap of 0.024 (tolerance 0.02; a non-blocking warning by design). Proof-of-concept lesson (three development seeds): a plateau near 100 was suggested; the prospective full run did not confirm it.

**EXT-CTRL: coherent wrong-family placebo and robust aggregation (seeds 320 to 329).** The placebo arm gives each peer the same number of rows of a different, non-hidden family (chosen by closeness of peer fit count) in place of the hidden family. Where a peer lacked enough placebo-family rows the shortfall was moved to other peers and recorded as `reallocated` (`controls-placebo-pairs.csv`: 143 pairs, 73 with reallocation, 14,304 of 39,881 placebo rows, 36%). The total is matched exactly but per-peer matching is weak for reallocated pairs. Placebo families are chosen from row counts only (no outcome); they are not systematically the nearest known family (median rank 48 of about 153 by descriptor closeness). FedAvg, 5% FPR, federation-wide, pooled family sets unless stated:

| Quantity | Estimate (95% BCa) | Verdict |
|---|---|---|
| Placebo effect (placebo minus absent-everywhere) | -0.001 (-0.008, 0.006) | equivalent to zero |
| CTK minus placebo effect | +0.095 (0.079, 0.116) | above +0.03 |
| H-CTRL-1 | met federation-wide in the primary set, the replication set and pooled | family-specific |
| Own-domain | pooled met; primary and replication per-set placebo intervals are too wide to fall inside the band | pooled only |
| Mean-aggregation CTK / trimmed-mean CTK / lower-median CTK | +0.095 / +0.088 / +0.126 | each above +0.03 |
| Trimmed minus mean | -0.007 (-0.028, 0.009) pooled | non-inferior pooled |
| Trimmed minus mean, replication set | -0.012 (-0.043, 0.001); trimmed-mean CTK +0.042 (0.017, 0.065) | **fails the frozen -0.03 margin** |
| H-CTRL-2 | met in the primary set and pooled at 5% FPR; **not met in the replication set** (any alpha) or pooled at 10% FPR | see below |

Reading: the placebo is not a pure relatedness test (the placebo family's nearest-known distance is recorded as a descriptor only), but adding an equal amount of coherent malware of another family does not raise recall on the hidden family. Robust aggregation did not erase the rare holder in the primary set (trimmed-mean CTK +0.136 versus mean +0.137), but in the replication set the trimmed-mean estimate is lower than the mean estimate and its difference cannot be shown non-inferior, so an attenuation cannot be excluded there. The second robust aggregator is the coordinate-wise **lower** median because with four clients a standard median equals the trimmed mean (Amendment A1); its CTK exceeds the mean's (+0.032 pooled), so it does not attenuate the effect. Scope: FedAvg mean, trimmed mean and lower median only; Krum and other robust aggregators were not run.

**EXT-REP: representation replication on SHA-aligned LAMDA/McNdroid applications (seeds 330 to 339, mode `extension-b`, class D).** Frozen in Amendment A2 before any EXT-REP partition, feature cache or run existed (`docs/temp/extension-protocol/EXT-REP-representation-replication.md`, `FREEZE.md`). Design: the 554,136 rows shared by four representations, with identical rows, identical partitions and identical clients: R0 LAMDA static (925 features; the baseline on the overlap subset), R1 McNdroid static (2,390), R2 call graph (2,793, standardised), R3 report-JSON (17,483 columns, signed log1p, reduced to columns with at least 1% positive prevalence, standardised). Every R2/R3 column selection and standardisation is fitted by each trained model from exactly its own training rows (local: that client's rows; central and FedAvg: the pooled rows of that arm) and applied unchanged to its calibration and test rows. Original MLP pipeline, per-target-client 5% FPR thresholds, FedAvg arms as in the original design. Estimand: central full-exposure federation-wide recall at 5% FPR, seed-paired difference versus R0; priority set P = {hiddad, gappusin, revmob}, contrast set C = {leadbolt, airpush, dowgin}; BCa 9,999 resamples, Holm across the nine per-family P-by-representation tests. This is NOT external validation: 81% of McNdroid applications are in LAMDA and the family labels come from the same AVClass2 run. Files: `results/extension-b/representation-{effects,levels,verdicts,eligibility,seed-effects,run-index}` and `representation-code.json`.

Baselines on the overlap (R0, central full exposure, federation-wide): hiddad 0.409, gappusin 0.699, revmob 0.317, adwo 0.435. They differ from the original full-population central full-exposure values (0.283, 0.453, 0.539, 0.585) because the overlap subset and its partitions differ; they are not comparable to the original gate values, which are unchanged.

| Difference versus R0 (federation-wide, 5% FPR) | McNdroid static | Call graph | Report-JSON |
|---|---|---|---|
| priority-macro (P) | +0.082 (0.053, 0.132), 10/10 seeds | +0.006 (-0.035, 0.036) | -0.132 (-0.176, -0.064) |
| gappusin | +0.146 (0.051, 0.282), 9/10, Holm p 0.031 | +0.027 (-0.019, 0.118), Holm 1.0 | -0.083 (-0.151, 0.023) |
| revmob | +0.086 (-0.001, 0.167), 7/10, Holm 0.65 | +0.045 (-0.016, 0.120), Holm 1.0 | -0.149 (-0.217, -0.069) |
| hiddad | +0.013 (-0.046, 0.159), 3/10 positive, Holm 1.0 | -0.055 (-0.103, -0.023) | -0.164 (-0.248, -0.102), Holm 0.018 |
| adwo (exploratory) | +0.328 (0.196, 0.448), 9/10 | +0.073 (-0.017, 0.171) | -0.175 (-0.263, -0.069) |
| contrast set C | -0.029 (-0.050, -0.010) | +0.036 (-0.015, 0.080); leadbolt +0.120, airpush +0.130, dowgin -0.143 | -0.261 (-0.287, -0.219) |

CTK (FedAvg, federation-wide, priority-macro) by representation: R0 0.167 (0.133, 0.198), McNdroid static 0.237 (0.197, 0.288), call graph 0.206 (0.166, 0.246), report-JSON 0.108 (0.085, 0.140); paired differences versus R0 +0.070 (0.029, 0.100), +0.039 (0.022, 0.064) and -0.059 (-0.091, -0.040). CTK is not removed by a richer representation: it rises with McNdroid static and call-graph features and falls with the report-JSON representation, whose full-exposure recall is also lower.

Frozen verdicts (`representation-verdicts.csv`): **H-REP-1 MET** (McNdroid static priority-macro lower bound 0.053 above +0.03). **H-REP-2 NOT MET** under the frozen rule (each hiddad upper bound below +0.03): call graph (upper -0.023) and report-JSON (upper -0.102) exclude a meaningful rescue, but the McNdroid-static hiddad interval (-0.046, 0.159) is too wide to exclude one. Failing this no-rescue criterion is not evidence of a rescue: no representation has a hiddad lower bound above +0.03 and the static point estimate is about zero (3/10 positive seeds). The hiddad status is therefore **unresolved** (`rep1-met-hiddad-unresolved`). The frozen outcome map labelled this branch "some representation rescues hiddad"; that label confused a failed equivalence with an effect and was corrected in the final verification pass (three-way status: rescue shown, no meaningful rescue, unresolved; formal rule, numbers and threshold unchanged). Accurate summary: representation limits are family-specific; richer McNdroid static features raise full-exposure recall of gappusin and adwo (revmob in point estimate, interval touching zero); hiddad shows no rescue under call graph or report-JSON and remains unresolved for McNdroid static; call-graph features leave the priority set unchanged and report-JSON features lower recall for every family; the original representation-limited gate (promoted, 3 of 4) and the 9/0/3 count are unchanged. Eligibility: seven of the eight primary families were eligible in every seed; frmy was not eligible on the overlap in any seed and is dropped without replacement (`representation-eligibility.csv`). Operating point: every R2 and R3 run records a non-blocking realised-FPR warning (largest gap 0.029 against the 0.02 tolerance), as the earlier runs did.

Limitations (stated once): the overlap is not independent of LAMDA (81% of McNdroid apps; same AVClass2 labels); provider-side feature selection (LAMDA variance filter, McNdroid 2013-fit selector) cannot be reconstructed train-only; dimensionality differs across representations (richer representations have more features), so the contrast is between these added representations, not a causal statement about richness per se; the call-graph vectors are 9.66 GB downloaded from Hugging Face `IQSeC-Lab/McNdroid` (CC-BY-4.0).

### 33.3 Proof-of-concept decisions (development seeds, not evidence)

Proofs of concept used development seeds (`docs/temp/poc/`) and are not confirmatory. Values are decision inputs only.

| Candidate | POC result | Expected scientific value | Expected effect / uncertainty | Full run justified? |
|---|---|---|---|---|
| Representation replication (McNdroid) | first harness (development seeds 1 to 5, pooled threshold) reproduced the baseline badly (gappusin 0.94 versus 0.45) and gave a wrong "not justified" call; the corrected per-client-threshold harness (`docs/temp/poc/mcndroid_repr_poc_v2_*.csv`) and the pipeline R0 development smoke agreed with the primary pipeline | medium: N7 only, not external validation (81% overlap) | development effects for McNdroid static (gappusin, revmob, adwo positive, hiddad about 0) motivated but did not fix the frozen hypotheses | **Yes**, frozen (Amendment A2) and run as EXT-REP (33.2) |
| Larger-family explanation | no dedicated POC; families selected by a frozen rule | medium | wide intervals expected with 7 to 8 families | **Yes**, run (EXT-LFAM, 33.2) |
| Exact effective dose | three development seeds suggested a plateau near 100 | medium | saturation claim needed | **Yes**, run (EXT-DOSE); the plateau was not confirmed prospectively |
| Coherent wrong-family placebo | development seeds run | high (reviewer-critical) | needs equivalence within +/-0.03 | **Yes**, run (EXT-CTRL) |
| Rare-peer erasure (robust aggregation) | development seeds run | high if a non-mean aggregator is in scope | trimmed mean and median | **Yes**, run (EXT-CTRL) |
| Family-aware auxiliary objective | not run | method paper only | would be a new mechanism; headroom gate closed (section 27) | No |
| Missing-class-aware baselines (FedRS, FedLMD, FedLC, FedCKD and others, read) | not added | low | undefined or degenerate in the binary setting (28.1) | No |
| External dataset | audited (sections 30 to 32) | highest if a suitable corpus existed | Ciaramella benign half unreleased; MH-1M and Droidware unconfirmed; KronoDroid marginal | No corpus suitable |

POC lesson: the first development harness used a pooled threshold, reproduced the baseline badly (gappusin 0.94 versus 0.45 in the primary study) and led to a wrong "full run not justified" call. The corrected per-client-threshold harness (`docs/temp/poc/mcndroid_repr_poc_v2_*.csv`) and the pipeline R0 development smoke agreed with the primary pipeline; the full run was then frozen (A2) and run. The earlier statement that gappusin is not representation-limited on the overlap came from the flawed harness and is withdrawn; in EXT-REP the R0 overlap baseline for gappusin is 0.699 (33.2). The development numbers in the earlier POC are not evidence.

### 33.4 Diagnostics of the extension evidence [C analyses of D data]

Computed from the stored extension runs by `ctk-android diagnostics --mode extension-b` (no training, no new gate; files `results/extension-b/diagnostics-*`). They characterise the frozen results; none changes a frozen verdict.

**EXT-REP at equalised realised FPR.** The primary reading uses each target client's calibration-derived 5% FPR threshold; realised test FPR is 0.052 to 0.054 on average for every representation and arm (per client 0.019 to 0.110), so R1 does not run at a looser operating point than R0. Diagnostic reading: recall at exactly 5% test benign FPR (empirical ROC of the target client's own benign test rows against the federation-wide hidden-family test rows, linear interpolation), same seeds and BCa.

For the FedAvg peer-present arm, mean realised test FPR by representation is R0 LAMDA static 0.05411, R1 McNdroid static 0.05341, R2 call graph 0.05378 and R3 report-JSON 0.05341. The priority-macro central full-exposure recall at the calibration threshold and at the diagnostic exact-5%-FPR threshold is:

| Representation | Calibrated recall | Realised test FPR (FedAvg peer-present) | Exact-5%-FPR recall | Exact-FPR difference vs R0 |
|---|---:|---:|---:|---:|
| R0 LAMDA static | 0.475 | 0.05411 | 0.488 | reference |
| R1 McNdroid static | 0.557 | 0.05341 | 0.546 | +0.058 (0.025, 0.138) |
| R2 call graph | 0.481 | 0.05378 | 0.482 | -0.006 (-0.042, 0.025) |
| R3 report-JSON | 0.343 | 0.05341 | 0.348 | -0.140 (-0.179, -0.100) |

Differences versus R0 for the required family groups and CTK are shown below under both readings. Values are paired mean differences (95% BCa interval); each cell gives calibration-threshold then exact-5%-test-FPR results. The adwo row is exploratory.

| Endpoint | R1 McNdroid static | R2 call graph | R3 report-JSON |
|---|---|---|---|
| Priority macro, central full exposure | +0.082 (0.053, 0.132); +0.058 (0.025, 0.138) | +0.006 (-0.035, 0.036); -0.006 (-0.042, 0.025) | -0.132 (-0.176, -0.064); -0.140 (-0.179, -0.100) |
| gappusin | +0.146 (0.051, 0.282); +0.138 (0.047, 0.252) | +0.027 (-0.019, 0.118); +0.027 (-0.016, 0.104) | -0.083 (-0.151, 0.023); -0.068 (-0.142, 0.028) |
| revmob | +0.086 (-0.001, 0.167); +0.075 (-0.001, 0.129) | +0.045 (-0.016, 0.120); +0.057 (0.005, 0.119) | -0.149 (-0.217, -0.069); -0.140 (-0.208, -0.062) |
| hiddad | +0.013 (-0.046, 0.159); -0.038 (-0.160, 0.094) | -0.055 (-0.103, -0.023); -0.100 (-0.241, -0.041) | -0.164 (-0.248, -0.102); -0.212 (-0.314, -0.135) |
| adwo (exploratory) | +0.328 (0.196, 0.448); +0.320 (0.184, 0.415) | +0.073 (-0.017, 0.171); +0.075 (-0.018, 0.184) | -0.175 (-0.263, -0.069); -0.182 (-0.250, -0.106) |
| Contrast macro | -0.029 (-0.050, -0.010); -0.028 (-0.056, -0.008) | +0.036 (-0.015, 0.080); +0.026 (-0.025, 0.078) | -0.261 (-0.287, -0.219); -0.263 (-0.285, -0.235) |
| FedAvg CTK, priority macro | +0.070 (0.029, 0.100); +0.083 (0.043, 0.116) | +0.039 (0.022, 0.064); +0.050 (0.031, 0.087) | -0.059 (-0.091, -0.040); -0.053 (-0.097, -0.035) |

The operating-point diagnostic preserves the direction for most family and CTK contrasts. For R1 McNdroid static, priority-macro recall improves versus R0 under both readings, although the exact-FPR lower bound (+0.025) does not clear the frozen +0.03 margin; gappusin and adwo remain positive and contrast-macro remains negative. R2 call-graph priority-macro is near zero under both readings, while revmob is positive in the exact-FPR diagnostic. R3 report-JSON reduces priority-macro recall under both readings. No hiddad rescue is demonstrated under either reading: call graph and report-JSON are negative; McNdroid static remains unresolved. These are sensitivity results and do not replace the calibration-threshold primary endpoint. Call-graph logits are finite but extreme in 0.3 to 1.6% of score rows (up to about 5e5 in magnitude) because test rows can be non-zero on columns that are nearly constant in a model's training rows; there are no NaN or infinite scores and the realised FPR remains in range.

**EXT-LFAM influence and stability.** Leave-one-family-out rho ranges 0.340 to 0.463 (median 0.385; jackknife SE 0.151); no single family changes rho by more than 0.052 (inmobi, a stable family). Three of the five families with incomplete eligibility (feiwo, anydown, utchi) are among the five most influential, all with positive influence, because they sit in concordant corners (feiwo low on both variables; anydown and utchi high on both). Each of the five individual deletions leaves rho positive (0.349 to 0.388); restricting to all 27 always-eligible families gives rho 0.274 (95% CI -0.110 to 0.583). Family CTK itself is reproducible across seeds (Kendall W 0.58 over the 27 complete families; family-mean reliability 0.83; split-half 0.86), so the imprecision is in the weak descriptor-CTK link and family count, not in noisy CTK (disattenuated rho about 0.43). Seed-count-weighted Spearman 0.362. Reading: broadly positive at the family level, not dependent on an individual incompletely eligible family, but modest and imprecise; three such families carry appreciable leverage and the stable-eligibility sensitivity interval spans zero.

**EXT-DOSE curve shape.** Every consecutive increment in the pooled federation-wide curve is positive (0 to 10: +0.031; 10 to 25: +0.021; 25 to 50: +0.025; 50 to 100: +0.044; 100 to 200: +0.032), while gain per 10 peer samples falls overall: this is consistent with diminishing marginal returns, with no plateau observed through 200. A descriptive saturating (Emax) fit has the lowest AIC in every set: pooled Emax 0.214 (0.167, 0.276), half-effect dose 79 (49, 135) samples; primary set 0.252 and 53 (34, 82); replication set not identified (half-effect dose 201, 85 to 671). The natural peer-present arm is worth about 90 exact peer samples (primary 77, replication 113). Families separate by dose requirement (federation-wide): early responders (mean CTK at least +0.03 by 10 to 25 samples: revmob, leadbolt, inmobi, domob, airpush, hiddad), late responders (50 to 100 samples: adwo, gappusin, youmi, smsreg, utchi) and non-responders at 200 (dowgin, dnotua, kuguo, zdtad). Dose response tracks the confirmatory family CTK (Spearman 0.94 with CTK at 200) and local headroom (local recall -0.69), not the full-exposure ceiling (-0.14); non-responders already have high local recall. Families account for about half of the variance of CTK at 200 (0.53, 0.22 to 0.78; primary 0.75, replication 0.28). By target client, CTK at 200 ranges from 0.080 (appchina) to 0.314 (play-late). Fits describe 0 to 200 only; nothing is extrapolated.

**EXT-CTRL strata.** No placebo stratum shows a materially positive effect; the largest positive client-level point estimate is about +0.014, and the pooled federation-wide placebo is -0.001 (-0.008, 0.006). Placebo effects are slightly negative in 13 of 18 set x population x alpha cells (-0.001 to -0.012). Peer reallocation does not materially change the placebo result. H-CTRL-1 fails in three own-domain cells (primary 5%, replication 1% and 5%), from wide lower tails or small CTK, not from a materially positive placebo. Reallocated and non-reallocated pairs are both inside the band in 14 of 18 strata; the one stratum whose difference excludes zero (primary own-domain 5%) is negative and driven by leadbolt pairs whose placebo family is frmy. Placebo relatedness (centroid distance, rank, fit ratio) shows no consistent association with the placebo effect. Aggregation: in the primary set trimmed-mean CTK is within 0.020 of the mean in every stratum and the lower median is at or above the mean in 5 of 6; H-CTRL-2 failures elsewhere come mostly from the non-inferiority margin (wide seed-to-seed spread of the difference), not from lost CTK. Rare-peer erasure is not supported: families held by essentially one peer have low CTK under every aggregator, the plain mean included, and within them trimmed minus mean is indistinguishable from zero while the lower median is often higher than the mean.

**Unified synthesis (class C; confirmatory seeds and the 32-family study).**
- CTK is concentrated in a stable core of families: revmob and leadbolt are 0.24 to 0.34 in controlled exposure, natural scarcity and the 32-family study; family ranks agree between the confirmatory primary set and the 32-family study (Spearman 0.86 own-domain, 0.89 federation-wide, 7 shared families). Among 32 fresh families 21 have CTK intervals above zero and only one (baiduprotect, -0.044) below.
- Headroom (full-exposure minus local recall) is the most useful family-level predictor in the 32-family study (Spearman 0.52, 0.13 to 0.80), ahead of the nearest-known-family descriptor (0.39) and support (0.31 to 0.38); pretreatment cell-level mixed models (local recall, local and peer support, novelty) explain at most 20% of CTK variance through fixed effects, and family identity carries most of the rest. (A model with headroom and pooling is an identity, CTK = headroom - pooling - residual gap, and is not interpreted.)
- A five-way taxonomy (exposure-limited, representation-limited, low headroom, pooling-responsive, negative-transfer-sensitive) from the existing thresholds does not separate: families carry zero to three labels, labels flip between populations and family sets (silhouette 0.14 to 0.25), and revmob is poor under full exposure in three model classes yet has the largest CTK. Only an exposure-limited core (leadbolt, airpush, inmobi, adwo) keeps its label in both family studies.
- FedProx versus FedAvg: in the primary set FedProx has slightly higher CTK (+0.018, 0.001 to 0.031) and higher known-family recall (+0.026); in the replication set the CTK difference is -0.018 to -0.021 (interval spans zero) and pooling is higher (+0.041), so FedProx does not add CTK reliably; there is no CTK-for-safety trade-off.
- The large play-late own-domain CTK in the primary set (0.48) is family composition (revmob and leadbolt targets) and does not replicate in the replication set (0.004).

## 34. Remaining Evidence Gaps

- **One corpus.** LAMDA with AndroZoo market metadata and four simulated market clients; no independent Android corpus with a real client axis exists in the audited public data (35.1). Natural scarcity is a within-dataset validation (section 10).
- **Model generality of the decomposition.** CTK keeps its sign and practical size across model classes, but the pooling share is model- and design-dependent (linear 0.66, natural scarcity 0.47); dominance of CTK is shown for the primary MLP under controlled exposure only.
- **Mechanism.** Why some families transfer and others do not is described, not explained: family identity and headroom carry most of the variance; the novelty descriptor association is modest and imprecise; no taxonomy separates cleanly (33.4).
- **Saturation.** The exact-dose curve is consistent with diminishing marginal returns, but no plateau is observed through 200 samples; the replication set's half-effect dose is not identified (33.4).
- **Own-domain precision.** Own-domain controls and robust-aggregation contrasts are wide in some strata (EXT-CTRL own-domain at 1% and 5% FPR); worst-client estimates are unstable at 1% FPR.
- **Representation.** No hiddad rescue is demonstrated: McNdroid static remains unresolved, while call-graph and report-JSON representations do not rescue it; the representation study is same-application, not external.
- **Literature coverage.** FEDroid and FID-SPA full text unavailable; Popoola et al. assessed from its accepted-version author manuscript; the federated intrusion-detection and security-venue literatures are sampled, not exhausted (29.7).

## 35. Decision Support for Open Items [D]

Final assessment of every further experiment considered, after the diagnostics in 33.4. None is run: each is either already answered, would not change a main claim, or lacks a uniquely defensible design with the available data.

| Candidate | Gap | Already answered? | POC needed? | Expected scientific value | Cost | Decision |
|---|---|---|---|---|---|---|
| Exact doses above 200 | where the curve saturates | partly: diminishing returns shown, primary-set half-effect dose 53 (34, 82); replication not identified | no | low to medium: would locate a plateau for some families, not change any claim | medium (peer support caps doses above 200 for most families) | not run; stated as a limit |
| FedProx-focused prospective confirmation | deployment recommendation | yes: primary +0.018 CTK and +0.026 known-family, not replicated in the replication set (33.4) | no | low | medium | not run |
| Broader representation comparison | representation versus exposure | partly: EXT-REP plus equal-FPR diagnostic (33.4) | no | low: no independent representation source beyond McNdroid | high | not run |
| Another robust aggregator (Krum) | rare-peer erasure | largely: trimmed mean and lower median show no erasure mechanism (33.4); CyberForce already reports Krum on an absent malware | no | low | medium | not run |
| Another coherent placebo | placebo generality | yes: no materially positive placebo stratum (largest point estimate about +0.014); pooled federation-wide effect -0.001 (-0.008, 0.006); reallocation and relatedness do not change the conclusion (33.4) | no | low | medium | not run |
| Larger family study | association precision | partly: 32 families, influence analysed (33.4); detecting rho about 0.3 needs about 85 eligible families, more than the corpus supports | no | low | high | not run |
| Independent dataset | corpus dependence | no suitable corpus (35.1) | feasibility count only | highest if one existed | high | not run; AndroZoo-markets replication recorded as the only possible route, not independent |
| Family-aware auxiliary objective | method upper bound | no | yes | method-paper value only; the headroom gate for a new mechanism is closed (section 27) | high | not run |
| Missing-class comparator reformulation (family-as-class head) | comparator gap | no | yes | changes the task; the binary detector is the studied setting | high | not run |
| Literature-motivated experiments | CyberForce, FLEKD-IDS designs | CyberForce's unmatched arms and robust aggregators are already covered by the matched design and EXT-CTRL | no | low | n/a | not run |

Readiness: no remaining experiment would change a main claim; the open items are limits of the corpus and literature access, not missing analyses.

### 35.1 Is a second independent Android dataset worth it? Not with current public data

Criteria for a usable corpus: a real client or source axis (market, vendor, region or organisation), benign samples, stable identities, family labels, and at least 15 families with several hundred de-duplicated samples at three or more clients. KronoDroid is MARGINAL (emulator versus real-device split, era-window clients confound family with time; section 31). McNdroid is not independent (81% of its apps are in LAMDA) and serves only as a representation check (section 32). MH-1M and MH-100K (AndroZoo-derived, no market axis in the release), Hypercube (Google Play only), APIGraph (malware and benign from different provenance, md5 only), AndroCT (years only), Droidware (binary labels), Drebin, AMD and MalRadar (no benign or no market axis), CIC-AndMal2017 and CCCS-CIC-AndMal-2020 (no market axis) fail on the client axis, benign samples or family labels. The only route to real market clients is AndroZoo's market field on markets outside LAMDA's four (for example mi.com, hiapk, angeeks) with AVClass labels from MH-1M VirusTotal reports; it would need a feasibility count first and shares LAMDA's source, so it would be a new-market, not an independent-corpus, replication. A poorly matched replication would be less informative than an explicit one-corpus limitation.

## 36. Claims and Allowed Wording

| Claim | Class | Status | Allowed wording |
|---|---|---|---|
| Local absence lowers recall on the hidden family | A | supported | "A locally hidden family is detected less well than under full exposure (local deficit 0.201, CI 0.164 to 0.231)." |
| Collaboration recovers part of the deficit | A/C | supported with qualification | "Recovers most federation-wide but little own-domain (oracle-gap recovery 0.63 versus 0.23)." |
| For the primary MLP with controlled exposure the gain is mostly family-specific peer knowledge | A | supported | "CTK +0.117 versus pooling +0.014 (primary MLP, controlled exposure, one corpus)." |
| The gain is specific to the hidden family, not extra coherent malware | D | supported | "No material target-family benefit is detected for an equal amount of another coherent family (placebo -0.001, CI -0.008 to 0.006); CTK exceeds placebo by +0.095 (FedAvg, federation-wide, seeds 320 to 329)." |
| The decomposition is model- and design-general | A/B | **not supported** | "The split between pooling and family-specific knowledge is model- and design-dependent." |
| CTK keeps sign and practical size across populations, models, supports, operating points, splits | B | supported for sign and magnitude | "Persists in sign and practical magnitude", never "identical". |
| Own-domain CTK is not a permutation artefact | A + D | resolved prospectively | "Unresolved in the original seeds (100 to 109); equivalent to zero in a separately frozen extension with fresh seeds 200 to 209 (EXT-1)." Never pool. |
| Natural scarcity confirms the effect | B | within-dataset only | "Within-dataset natural-exposure validation", never "external validation". |
| Benefit grows with peer exposure | A + D | supported; saturation not shown | "CTK rises with exact peer exposure through 200 samples and is consistent with diminishing marginal returns, but no plateau is observed within the tested range; families differ in the exposure they need." |
| Feature novelty explains CTK | A (gate) + D | original unresolved; prospective association modest and imprecise | "A modest positive association on 32 families (rho 0.39, CI 0.06 to 0.65); each single deletion among five incompletely eligible families leaves positive rho, while the always-eligible 27-family sensitivity is uncertain"; never causal. |
| Robust aggregation erases the rare peer | D | not observed | "Trimmed-mean and lower-median CTK stay close to mean CTK in the primary set; some replication and own-domain contrasts fail the frozen non-inferiority margin; families held by one peer have low CTK under every aggregator." |
| Richer representations change which families are poorly detected | D | supported, bounded | "Richer McNdroid static features raise full-exposure recall of gappusin and adwo and raise CTK, also at equalised 5% test FPR; no hiddad rescue is demonstrated (McNdroid static unresolved; call graph and report-JSON do not rescue it); same-application, not external validation." |
| CTK is concentrated in a family core | C | supported, descriptive | "CTK varies mainly by family; family ranks reproduce across seeds and family sets." |
| Novel / first | D | **forbidden** | Use the positioning paragraph in 29.6. |
| Generalizes beyond LAMDA | none | not supported | State the single-corpus limitation. |

The original gate counts (9 promoted, 0 narrowed, 3 rejected, section 25) are unchanged by any class C or D addition.

## 37. Contribution and Publication Story

### 37.1 Primary contribution

The primary contribution is a **controlled-exposure measurement design that isolates peer-held family knowledge**: for a client that lacks a malware family, a volume-matched family-absent-everywhere federation and a local arm split the collaboration gain into generic pooling and family-specific transfer, evaluated on the deprived client's own domain and on the worst client. Applied to Android malware, it shows that the gain on a locally hidden family is family-specific peer knowledge rather than generic pooling (primary MLP), confirmed by a coherent wrong-family placebo. What is differentiated from prior work is the matched decomposition and its evaluation; local-versus-federated gains on a missing class, absent-everywhere arms, peer-holder sweeps and robust aggregators on a missing class all have precedent (section 29).

### 37.2 Ranking of results for the manuscript

Main text, in order:
1. Controlled-exposure decomposition, primary MLP (sections 4 to 6): CTK +0.117 versus pooling +0.014 [A].
2. Family-specific placebo (33.2, 33.4): placebo -0.001, CTK minus placebo +0.095 [D].
3. Own-domain and worst-client results with negative own-domain pooling and its accounting split (sections 5.1, 7, 8), with the EXT-1 control [A, C, D].
4. Exact-dose curve: consistent with diminishing marginal returns and no plateau through 200 samples; family-dependent dose requirements; natural exposure worth about 90 samples (33.2, 33.4) [D].
5. Family heterogeneity: a reproducible family core, headroom as the main correlate, masking by aggregate metrics (12, 14.1, 33.4) [C].
6. Robustness of sign and magnitude, and the model- and design-dependence of the pooling share (sections 16 to 21) [B].

Supplement: natural scarcity details, EXT-REP and its equal-FPR diagnostic, robust aggregation, EXT-LFAM and its influence analysis, FedProx trade-off, per-client tables, variance components, the taxonomy attempt, operating-point and salt sensitivities.

### 37.3 Reviewer-safe story

> In a controlled-exposure design on one Android malware corpus, hiding a family from one client lowers that client's detection of it. Collaboration recovers part of the deficit, and for the primary MLP most of the federation-wide gain comes from peers holding that specific family rather than from generic pooling: peers holding an equal amount of a different coherent family provide essentially no material target-family benefit. The family-specific gain grows with the number of peer samples and is consistent with diminishing marginal returns through 200 samples; no plateau is observed within the tested range. It varies strongly and reproducibly between families, and survives own-domain and worst-client evaluation, natural scarcity within the corpus, a disjoint family set and other model classes in sign and practical size; the split between pooling and family-specific knowledge is model- and design-dependent. Some families remain poorly detected even with full exposure, and richer static features help some of them, so exposure and representation limits are family-specific. All findings are for one corpus and need independent replication.

### 37.4 Next actions

1. Report the study as a single-corpus controlled-exposure decomposition with class labels A to D visible.
2. Obtain FID-SPA and FEDroid through a library if possible before submission; re-check the closest papers against work published through the submission date.
3. Re-open external replication only if a corpus meeting 35.1 appears.

## 38. Warnings and Limitations

- Class C analyses (5.1, 9, 12, 12.1, 14, 14.1, 33.4) are exploratory support, never preregistered claims; the extension studies (class D: EXT-1 seeds 200 to 209; EXT-LFAM 300 to 309; EXT-DOSE 310 to 319; EXT-CTRL 320 to 329; EXT-REP 330 to 339) are never pooled with the original seeds or each other and change no original gate, seed, threshold or family set (9/0/3).
- The dose-gate outcome was changed by a bug correction (original promotion "narrowed"); the fix did not use outcomes (an observation-level reading gives the same result).
- CTK is a counterfactual against family-absent pooling; where pooling is negative, CTK overstates the deployment gain (adwo, hiddad, gappusin). Use total gain for deployment statements.
- Micro-pooled and seed-paired estimands differ in magnitude and are labelled `micro_pooled_ctk_gain` and `paired-seed-macro`.
- Selecting the worst client on the local baseline biases total and pooling gains upward.
- Static binary features, four simulated clients, ten seeds per study, wide BCa intervals; nothing generalizes beyond this corpus without replication. Per-client results are descriptive.
- PDF figures are not byte-deterministic.
- Representation study: same-application replication on an 81%-overlap subset with identical AVClass2 labels, provider-side feature selection not reconstructable, different dimensionality per representation; the H-REP-1 margin holds under the calibration reading only (33.4).
- Evidence-class labels inside two original artefacts are inconsistent and left unchanged to keep the confirmatory artefacts immutable: `natural-scarcity-comparison` labels its controlled-exposure rows B (they are the class A estimates of sections 4 and 5), and the permutation-control rows are C in `permutation-control-audit` but B in `ctk-robustness-synthesis`. The text of this document uses the correct classes.
- Downloaded external datasets are kept outside the repository and `results/`; they are not redistributed.
- The literature audit is bounded (29.7) and licenses no priority claim.

## 39. Complete Artifact Index

`results/` (promoted, mode confirmatory; digests in `manifest.json`):

- Evidence parquet: `run-index`, `arm-metrics`, `collaboration-decomposition`, `family-rescue`, `peer-dose-response`, `feature-novelty`, `robustness`, `anchored-worst-client`, `anchored-client-selection`, `federated-arm-tradeoff`, `ctk-robustness-synthesis`, `family-mechanism-patterns`, `natural-scarcity-comparison`, `permutation-control-audit`, `mechanism-headroom`, `operating-point-fidelity`, `client-ctk-analysis`.
- Statistics: `paired-effects.parquet`, `cluster-bootstrap.parquet`.
- Gates: `claims.csv`, `seed-status.csv`.
- Tables (CSV, 23): client-ctk-analysis, dataset-client-audit, primary-arm-comparison, collaboration-decomposition, peer-dose-response, family-level, claim-gates, robustness, the other class B/C tables listed above, and the three hidden-family tables listed under additional class C evidence.
- Figures (PDF and PNG, 11): collaboration-decomposition, mean-versus-worst-client, own-domain-versus-federation-wide, peer-dose-response, family-rescue-map, feature-novelty-versus-ctk-gain, known-versus-unseen-tradeoff, ctk-robustness-forest, federated-arm-tradeoff, natural-versus-controlled, client-ctk-analysis.
- Provenance: `code.json`, `protocol.json`, `source-data.json`, `environment.json`.
- Extension (class D, `results/extension/`): run index, paired effects, `permutation-control-audit.csv`, provenance; seeds 200 to 209.
- Additional class C evidence: `ctk-variance-components`, `family-associations`, `family-client-ctk`, and the hidden-family post-hoc analyses `ctk-heterogeneity-components` (12.1), `aggregate-metric-masking` (14.1) and `negative-transfer-decomposition` (5.1), each as parquet in `results/evidence/` and CSV in `results/tables/`. The three post-hoc tables are produced from the stored runs by `uv run ctk-android posthoc --promote` (workflow `workflows/posthoc.py`, analysis `analysis/hidden_family.py`); nothing is retrained.
- Extension-b (class D, `results/extension-b/`): EXT-LFAM `large-family-summary`, `large-family-ctk`, `large-family-seed-ctk`, `large-family-selection` (seeds 300 to 309); EXT-DOSE `exact-dose-effects`, `exact-dose-verdicts`, `exact-dose-consistency`, `exact-dose-family-curves`, `exact-dose-seed-effects`, `exact-dose-run-index` (seeds 310 to 319); EXT-CTRL `controls-effects`, `controls-verdicts`, `controls-placebo-pairs`, `controls-seed-effects`, `controls-run-index` (seeds 320 to 329); EXT-REP `representation-effects`, `representation-levels`, `representation-verdicts`, `representation-eligibility`, `representation-seed-effects`, `representation-run-index`, `representation-code.json` (seeds 330 to 339); each as CSV and parquet, plus `run-index` and code provenance JSON. Frozen designs: `docs/temp/extension-protocol/` (with `FREEZE.md`); proofs of concept: `docs/temp/poc/`.
- Positioning, feasibility and extension register (class D): sections 29 to 33 of this document.
- Protocol and decisions: `docs/Roadmap.md` (31.3 post-confirmatory clarifications, 31.4 extension protocol), `docs/decisions/protocol-amendments.md`, `docs/decisions/implementation-decisions.md`.
