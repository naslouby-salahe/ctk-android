# CTK-Android Results and Evidence Inventory

Every number below is read from the machine-readable artifacts in `results/` (promoted from `outputs/`), produced by the analysis code at the revision named in section 2. Nothing was retrained for this document. Evidence classes are labelled throughout:

- **[A]** original confirmatory evidence (predeclared experiment and gate);
- **[B]** predeclared confirmatory robustness or sensitivity evidence;
- **[C]** post-confirmatory evidence-preserving analysis of already-generated data (not a preregistered claim);
- **[D]** proposed future work (no result).

"CTK" is the complementary-threat-knowledge gain: recall with the family present at peers minus recall when the family is absent everywhere, for the same learner. Confidence intervals are 95% BCa over the 10 confirmatory seeds (100 to 109) unless stated; "positive seeds" counts seeds with a gain above zero. The practical threshold is +0.03 absolute recall.

## 1. Executive Summary

1. **Collaboration helps locally unseen families [A].** Local unseen-family recall is 0.507 (federation-wide, 5% FPR); FedAvg reaches 0.638 (+0.132, CI 0.090 to 0.167, 10/10 seeds). Full-exposure central training reaches 0.708 (local deficit 0.201, CI 0.164 to 0.231).
2. **For the primary MLP with controlled exposure, the gain is dominated by complementary peer-held family knowledge, not generic pooling [A/B].** CTK is +0.117 (CI 0.090 to 0.145, 10/10 seeds; Holm-adjusted p = 0.0059); generic pooling is +0.014 (CI -0.038 to 0.054). The CTK share is 0.89 (CI 0.65 to 1.39) and the pooling share 0.11 (CI -0.39 to 0.35). This is *not* general: under natural scarcity, lower training support and for the linear model the pooling share is roughly one half or more (sections 6, 10, 16, 18).
3. **The CTK effect persists** in own-domain evaluation (+0.107), worst client (+0.173), family-macro (+0.124), natural scarcity (+0.113), a disjoint replication family set (+0.064), linear (+0.094) and tree (+0.102, centralized only) models, both support levels, three operating points, three partition salts and package-only grouping. Excluding the 27 negative-control rows, 269 of 276 paired-seed rows and 33 of 33 micro-pooled rows exceed +0.03; all seven exceptions are worst-client estimates at the 1% FPR operating point (section 21). Magnitude is family- and model-dependent.
4. **The federation-wide permutation control is clean [A]** (CTK -0.001, CI -0.007 to 0.007), but the own-domain control is not (FedAvg, 5% FPR: CI -0.004 to 0.036 extends past +0.03), so causal wording for the own-domain population carries a caveat (section 22).
5. **Known-family cost is arm-specific [A/C].** FedProx, the strongest federated arm by federation-wide unseen recall, changes known-family recall by -0.006 (within the ±0.02 tolerance). Plain FedAvg (-0.033) and FedAvg with fine-tuning (-0.038) exceed the tolerance. Blend (+0.017) and centralized (+0.000) are within it.
6. **Dose-response gate: corrected from NARROWED to PROMOTED (implementation defect, section 11).** The curve rises with effective exposure (0.437 to 0.562 recall); effective exposure is far below requested exposure, and saturation is not shown.
7. **Feature novelty is unresolved, not disproven [A].** Spearman rho 0.57 (7 families) and 0.33 (8 families), directionally consistent, intervals span zero. The stored gate status remains "rejected" for provenance.
8. **No headroom for a new federated mechanism [A].** The best simple baselines leave 0.049 to 0.094 mean and 0.029 to 0.081 worst-client recall below the full-exposure reference, under the 0.10 and 0.15 triggers. Several families stay poorly recalled even under full exposure (representation-limited).
9. **Gate counts after correction: 9 promoted, 0 narrowed, 3 rejected, 0 insufficient** (the original promotion recorded 8 promoted, 1 narrowed, 3 rejected).
10. Novelty: **NOT EXTERNALLY VERIFIED** beyond a very limited search (section 29).

## 2. Evidence Provenance

- Data: LAMDA release `var_thresh_0.01` (fingerprint `e9908f9a…677a9`) with AndroZoo metadata (`f0d11873…97904`); 1,008,381 rows, 925 binary features. Source: `results/provenance/source-data.json`.
- Protocol: frozen before any confirmatory seed (`docs/decisions/protocol-amendments.md`, Stage F); configuration fingerprint recorded in `results/provenance/protocol.json`. The Roadmap was amended after the campaign (Roadmap 20, 21, 28, 31.3, 38, 39); the amendment log states that no arm, threshold, seed, family set, hyperparameter or gate changed.
- Code provenance (`results/provenance/code.json`) now separates three revisions: **execution** `e079972` (freeze commit; training-relevant code identical to `dccf996`; runs were written 19:44 to 21:05 on 2026-09-24), **analysis/promotion** = the revision recorded in that file, with `analysis_sources_clean: true`, and **final reporting** = the commit containing this document. An earlier promotion recorded `e079972` while the working tree already held a wording-only change to the representation-limited claim; that affected wording only, not numbers or outcomes.
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

## 6. Generic Pooling Versus Complementary Threat Knowledge [A, with B/C context]

The gate `generic-pooling-majority` is **rejected** (0 of 2 scopes; the pooling-share upper bounds are 0.354 and -0.878, both below 0.5) and remains so. What the intervals support, scoped:

- **Primary MLP, controlled exposure [A]:** generic pooling does not account for the majority of the collaboration gain, and CTK is the dominant measured component.
- **Not generalizable [B]:** natural scarcity (FedAvg federation-wide: pooling gain +0.100, CI 0.072 to 0.131; share 0.47, CI 0.38 to 0.56; CTK share 0.53, CI 0.44 to 0.62), lower training support (pooling share 0.52, CI 0.40 to 0.62), and the linear model (pooling gain +0.181, share 0.66, CI 0.60 to 0.73; CTK +0.094, share 0.34) have a large pooling component. No dominance claim is made for any model class or design other than the primary MLP controlled-exposure setting. Trees (centralized): pooling +0.053 (0.008, 0.094), CTK +0.102, CTK share 0.66 (0.52, 0.98).

## 7. Own-Domain Results [A]

Own-domain CTK (FedAvg) is +0.107 (0.068 to 0.144), 10/10 seeds; the gate `own-domain-benefit` is promoted. Own-domain total gain is only +0.038 because pooling costs -0.069 (nine of ten seeds negative). FedProx improves own-domain recall by +0.059 (0.021, 0.103) and blend by +0.072 (0.053, 0.098). Caveat: the own-domain permutation control is not equivalence-clean (section 22).

## 8. Worst-Client Results [A]

The predeclared worst-client CTK (FedAvg) is +0.173 (0.116 to 0.242), 10/10; total gain +0.146 (0.080, 0.240). In this predeclared analysis each arm takes its own minimum client, so identities can differ across arms; section 9 removes that limitation as a robustness check. Worst-client estimates are the least stable across scopes: at the 1% FPR operating point CTK is +0.049 (0.014, 0.113) for the primary set and below +0.03 in several sensitivities.

## 9. Local-Baseline-Anchored Worst-Client Robustness [C]

Post-confirmatory, exploratory support; it does not replace the gate. Within each seed the worst client under the **local baseline** is frozen and followed through every arm (`anchored-worst-client.csv`, `anchored-client-selection.csv`). Selected clients across the 10 seeds: appchina 5, anzhi 3, play-late 2 (mean local recall 0.288, 0.234, 0.321).

| Learner | Total gain | Pooling gain | CTK gain | Positive seeds (CTK) |
|---|---|---|---|---|
| FedAvg | 0.166 (0.085, 0.292) | -0.003 (-0.028, 0.033) | **0.169 (0.095, 0.297)** | 9/10 |
| central | 0.182 (0.114, 0.289) | -0.006 (-0.049, 0.065) | 0.188 (0.132, 0.313) | 10/10 |

The same client benefits: CTK is about +0.17 with an interval well above +0.03, and pooling is about zero. Caution: selecting on the local baseline biases total and pooling gains upward (regression to the mean); the CTK contrast compares two collaborative arms and is the cleaner estimate.

## 10. Natural-Scarcity Validation [B]

Side by side with controlled exposure, FedAvg, 5% FPR (`natural-scarcity-comparison.csv`; the estimands are **not** pooled). Both use the same 7 families and 4 clients.

| | Controlled | Natural scarcity |
|---|---|---|
| CTK federation-wide | 0.117 (0.090, 0.145), 10/10 | 0.113 (0.094, 0.128), 10/10 |
| CTK own-domain | 0.107 (0.068, 0.144), 10/10 | 0.110 (0.076, 0.139), 10/10 |
| CTK worst client | 0.173 (0.116, 0.242), 10/10 | 0.140 (0.084, 0.180), 9/10 |
| CTK family-macro | 0.124 (0.102, 0.153) | 0.161 (0.147, 0.181) |
| Total gain federation-wide | 0.132 | 0.213 (0.176, 0.242) |
| Pooling gain federation-wide | 0.014 | 0.100 (0.072, 0.131) |

Interpretation: the CTK magnitude is essentially the same in the artificial and the natural design, with the same sign, seed consistency and ten of ten positive seeds, which is strong external validation that the controlled-exposure effect is not an artefact of deleting data. What differs is the decomposition: under natural scarcity ordinary pooling contributes roughly as much as CTK, so total gains are larger. Operating point: realised FPR 0.0503 to 0.0510 in both designs. Natural scarcity has no full-exposure arm, so family rescue classification is "not classifiable" there.

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

What the curve shows: recall is non-decreasing within tolerance and rises with effective exposure, with no saturation across the tested range, so diminishing returns are **not** established. Requested doses badly overstate exposure (client caps and availability): requested 100 delivers about 9 samples, so "100 samples" is only reached by the all-available level and part of the 1000 level. Observation-level sensitivity (the 70 rows with at least 100 effective samples) gives mean gain +0.045; leave-one-family-out mean at least 0.040 (five families, one with two rows). Not driven by one family under either reading (level reading: at least +0.089). The dose effect is family-dependent: dowgin shows no gain (-0.004) even with a mean of 1,188 effective samples, revmob (+0.336) and leadbolt (+0.268) show large gains at 55 and 84 samples. Centralized and fine-tuned arms follow the same rising shape (all-available gain +0.110 and +0.090).

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
- **Representation-limited:** hiddad (CTK +0.029; full-exposure recall 0.283; linear 0.154 and trees 0.179 are also poor) and gappusin (CTK +0.029; full 0.453; linear 0.411). Peer exposure does not rescue them and full exposure does not either.
- **Already represented / low headroom:** adwo (local 0.671; peer recall equals local, its positive CTK arises because the no-family arm is *worse* than local, pooling -0.107), airpush and dowgin (high local recall). In the replication set zdtad (local 0.776, peer 0.694: collaboration lowers recall, CTK -0.019), kuguo (+0.027), dnotua (+0.007).
- CTK is a counterfactual against family-absent pooling. For adwo, hiddad, gappusin and revmob the pooling gain is negative, so CTK partly measures repair of negative transfer; the total gain (peer minus local) is the deployment-relevant number: revmob +0.266, leadbolt +0.281, airpush +0.115, dowgin +0.113, adwo -0.006, hiddad -0.032, gappusin -0.011.

## 13. Representation-Limited Families [A]

The gate `representation-limited-family` is promoted with scoped wording: 3 of 4 poorly recalled primary families (full-exposure central recall below 0.60) are also poor in an independent model class (linear or trees): hiddad, gappusin, revmob. adwo (full 0.585) is poor only for the MLP; linear 0.667 and trees 0.761 are adequate. Bounded interpretation, under the tested static representation and models: exposure alone does not explain all family-level failures. Independent-model evidence exists only for the primary family set; replication-set families (for example utchi, full 0.438) have no cross-model check.

## 14. Client-Level Results [A/C]

Client audit is in section 3. The predeclared analyses report client aggregates (mean over clients, worst client, own-domain per target client). The local-worst client is not fixed: appchina in 5 seeds, anzhi in 3 and play-late in 2 (section 9). Per-client CTK effects were not a predeclared output and are not reported here.

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

## 21. Canonical CTK Robustness Synthesis [B/C]

`ctk-robustness-synthesis.csv` (336 rows: 300 seed-paired macro, 36 micro-pooled; each row labelled with aggregation, scope, learner, alpha, salt or sensitivity, evidence class) and `ctk-robustness-forest.png`. Of the 300 seed-paired rows, 24 belong to the family-label permutation control (a negative control whose expected value is zero); of the remaining 276, 269 have a mean at or above +0.03. All 33 non-control micro-pooled rows are at or above +0.03 (the other 3 micro rows are the permutation control). The seven paired rows below the practical threshold are all worst-client estimates at the 1% FPR target: high family support 0.028; linear 0.015; lower training support 0.005; salts 2 and 3 about 0.017 and 0.015; replication FedAvg 0.006; replication centralized -0.017. At 5% FPR every federation-wide scope exceeds +0.03 with a positive interval. Seed-paired and micro-pooled rows are never mixed in one estimate.

## 22. Negative Controls [A, plus C audit]

Family-label permutation, CTK (`permutation-control-audit.csv`):

| Population | Alpha | FedAvg CTK (CI) | Outcome vs ±0.03 band |
|---|---|---|---|
| Federation-wide (gate) | 0.05 | -0.001 (-0.007, 0.007) | equivalent [A] |
| Federation-wide | 0.01 / 0.10 | -0.008 (-0.025, 0.009) / +0.003 (-0.008, 0.010) | equivalent |
| Own-domain | 0.05 | +0.011 (-0.004, 0.036) | **unresolved** (extends past +0.03) [C] |
| Own-domain | 0.10 | +0.029 (0.010, 0.050) | **unresolved** |
| Own-domain | 0.01 | +0.003 (-0.008, 0.011) | equivalent |
| Worst client | 0.01 / 0.05 / 0.10 | +0.002 / -0.001 / -0.006 | equivalent |

The gated federation-wide control is clean. The own-domain control is an unresolved post-confirmatory robustness caveat for the causal interpretation of the own-domain CTK; no retrospective own-domain permutation gate is added. Other negative-control checks (family-absent-everywhere condition, zero-dose agreement, sample-size matching, target-independence assertions) passed as structural validations.

## 23. Feature-Novelty Analysis [A gate; C interpretation]

Predeclared descriptor (nearest-known-family distance) versus FedAvg CTK: primary set rho 0.571 (p = 0.180, interval -0.412 to 1.0, 7 families); replication set rho 0.333 (p = 0.420, interval about -0.57 to 1.0, 8 families). The gate (association at least 0.3 with an interval excluding zero in both sets) is **not satisfied** and its stored status stays "rejected". Interpretation: the point estimates are positive in both sets and above the 0.3 magnitude, so the direction is consistent, but with 7 and 8 families the intervals are far too wide to establish or exclude an association. Novelty is neither supported nor contradicted; it is unresolved, and no further descriptors were searched. Family-level values are in `family-mechanism-patterns.csv` and the novelty scatter figure.

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
| own-domain-benefit | promoted | 1/1 | with permutation caveat |
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
3. [B] Natural scarcity reproduces the CTK magnitude (+0.113 versus +0.117), validating the controlled design; its decomposition differs.
4. [A/C] FedProx preserves known-family recall within tolerance while retaining the unseen-family benefit; FedAvg and fine-tuning do not.
5. [A] Peer-family benefit grows with effective exposure, and several families stay poorly recalled even under full exposure (representation limits), while standard baselines leave no headroom for a new mechanism.

## 27. Negative and Narrowed Findings

- Generic-pooling-majority rejected; and the linear, natural-scarcity and lower-support settings show large pooling components, so no model-general CTK dominance.
- Feature-novelty gate not satisfied (unresolved).
- New-mechanism trigger not met. Headroom versus central full exposure (`mechanism-headroom.csv`), mean gap (threshold 0.10): FedAvg 0.070 (0.043, 0.096), FedProx 0.062 (0.022, 0.089), fine-tune 0.094 (0.057, 0.138), blend 0.074 (0.049, 0.104), central 0.049 (0.020, 0.078); worst-client gap (threshold 0.15): FedAvg 0.029 (-0.026, 0.087), FedProx 0.074 (0.023, 0.126), fine-tune 0.047, blend 0.081, central 0.042. The mean gaps have upper bounds up to 0.138, so a residual gap cannot be excluded for fine-tuning, but the point estimates are below both triggers for every baseline; strong simple baselines already recover 0.56 to 0.71 of the exposure-related gap. Remaining failures for hiddad and gappusin persist under full exposure and in other model classes: representation, not federated optimization, is the more important remaining limitation, for this static representation and dataset only.
- Known-family cost of FedAvg and fine-tuning; own-domain permutation caveat; own-domain oracle-gap recovery only 0.23.
- Dose: no saturation, unreachable low requested doses, dowgin flat.

## 28. Evidence-Preserving Scientific Improvements

Class C additions, all from stored runs: local-anchored worst client (section 9), arm trade-off (15), robustness synthesis and forest plot (21), family patterns (12), natural-versus-controlled table and figure (10), permutation audit by population and alpha (22), headroom and operating-point fidelity tables. Corrected implementation defects (dose gate level handling, family-dependence scope, per-salt micro rows, natural-scarcity classification, provenance split, non-deterministic ordering) are logged in `docs/decisions/protocol-amendments.md`. No original confirmatory seed-level metric, paired effect, threshold or family set changed.

## 29. Novelty Assessment

**NOT EXTERNALLY VERIFIED.** Only a limited web search was performed (federated Android malware detection; missing-class federated learning). It found federated Android malware work that reports detection of unseen variants and vacant-class methods in label-skewed federated learning (for example FedVLS-style distillation, class-absent feature transfer), but no exhaustive audit of rare-class FL, class-removal studies, contribution decomposition, or cross-silo malware literature was done. No first, novel, or state-of-the-art claim is made. Candidate distinguishing dimensions to verify in a proper literature audit: controlled exposure with a matched family-absent-everywhere collaborative control; the pooling-versus-complementary decomposition; own-domain and worst-client decomposition; natural-scarcity validation; effective-dose analysis; exposure-versus-representation family diagnosis; cross-model replication.

## 30. Remaining Evidence Gaps

- One dataset (LAMDA plus AndroZoo metadata), simulated market clients, four clients; no independent Android dataset.
- Feature novelty unresolved with 7 to 8 families.
- Dose criterion reached only at the top levels; effective dose unequal to requested dose; no saturation region.
- Own-domain permutation control unresolved; worst-client estimates unstable at 1% FPR.
- Trees have no federated arm; cross-model checks cover the primary family set only.
- Per-client CTK not analysed; only 10 seeds.
- Model-general CTK-versus-pooling dominance not established.

## 31. Possible Future Extensions [D]

No result exists for any item; none was run.

| Possible action | Existing evidence | Scientific benefit | Requires new training? | Risk of post-hoc bias | Recommendation |
|---|---|---|---|---|---|
| No-new-run publication improvements (more figures, per-client tables, literature audit) | Full stored artifacts | High for clarity and honesty | No | Low if labelled class C | Do first |
| Independent Android dataset replication | None | Highest external validity | Yes, new data and fresh seeds | Low if protocol frozen first | Recommended |
| Exact-effective-dose follow-up | Requested and effective doses diverge; criterion met only at top levels | Resolves dose threshold and saturation | Yes, fresh seeds, dose defined on effective exposure | Medium (design after seeing curve; fix design before running) | Recommended if dose claims matter |
| Larger-family novelty/explanation study | rho 0.57 and 0.33 on 7 to 8 families, underpowered | Could resolve feature-novelty | Yes (more families, fresh seeds) | Medium-high (descriptor choice) | Only with predeclared descriptor and family count |
| Broader CTK-versus-pooling dominance study (all model classes, designs) | Dominance only for primary MLP controlled; linear and natural differ | Model-general claim | Yes, fresh seeds | Medium | Optional |
| Fixed-target follow-up on FedProx trade-off | Descriptive only | Would make a deployment recommendation confirmatory | Yes | Medium | Optional |
| New federated mechanism | Headroom below triggers | None demonstrated | Yes | High | Do not pursue |
| Additional descriptor searches on existing families | Underpowered | Low | No | High (multiplicity) | Do not pursue |

## 32. Warnings and Limitations

- Class C analyses are exploratory support and must not be presented as preregistered claims.
- The dose-gate outcome was changed by a bug correction; the original promotion recorded "narrowed". Both outcomes are documented and the change did not use favourable outcomes to choose the fix (an observation-level reading gives the same result).
- CTK is a counterfactual against family-absent pooling; where pooling is negative, CTK overstates the deployment gain (adwo, hiddad, gappusin). Use total gain for deployment statements.
- Micro-pooled and seed-paired estimands differ in magnitude and are labelled `micro_pooled_ctk_gain` and `paired-seed-macro` respectively.
- Selecting the worst client on the local baseline biases total and pooling gains upward.
- Static binary features, four simulated clients, ten seeds, wide BCa intervals; nothing generalizes beyond this representation and dataset without replication.
- PDF figures are not byte-deterministic.

## 33. Complete Artifact Index

`results/` (promoted, mode confirmatory; digests in `manifest.json`):

- Evidence parquet: `run-index`, `arm-metrics`, `collaboration-decomposition`, `family-rescue`, `peer-dose-response`, `feature-novelty`, `robustness`, `anchored-worst-client`, `anchored-client-selection`, `federated-arm-tradeoff`, `ctk-robustness-synthesis`, `family-mechanism-patterns`, `natural-scarcity-comparison`, `permutation-control-audit`, `mechanism-headroom`, `operating-point-fidelity`.
- Statistics: `paired-effects.parquet`, `cluster-bootstrap.parquet`.
- Gates: `claims.csv`, `seed-status.csv`.
- Tables (CSV, 16): dataset-client-audit, primary-arm-comparison, collaboration-decomposition, peer-dose-response, family-level, claim-gates, robustness, and the nine class B/C tables above.
- Figures (PDF and PNG, 10): collaboration-decomposition, mean-versus-worst-client, own-domain-versus-federation-wide, peer-dose-response, family-rescue-map, feature-novelty-versus-ctk-gain, known-versus-unseen-tradeoff, ctk-robustness-forest, federated-arm-tradeoff, natural-versus-controlled.
- Provenance: `code.json`, `protocol.json`, `source-data.json`, `environment.json`.
- Protocol and decisions: `docs/Roadmap.md` (31.3 post-confirmatory clarifications), `docs/decisions/protocol-amendments.md`, `docs/decisions/implementation-decisions.md`.
