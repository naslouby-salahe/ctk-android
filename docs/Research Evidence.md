# CTK-Android Research Evidence

Every number below is read from the machine-readable artifacts in `results/` (promoted from `outputs/`), produced by the analysis code at the revision named in section 2. Nothing was retrained for this document. Evidence classes are labelled throughout:

- **[A]** original confirmatory evidence (predeclared experiment and gate);
- **[B]** predeclared confirmatory robustness or sensitivity evidence;
- **[C]** post-confirmatory evidence-preserving analysis of already-generated data (not a preregistered claim);

"CTK" is the complementary-threat-knowledge gain: recall with the family present at peers minus recall when the family is absent everywhere, for the same learner. Confidence intervals are 95% BCa over the 10 confirmatory seeds (100 to 109) unless stated; "positive seeds" counts seeds with a gain above zero. The practical threshold is +0.03 absolute recall.

- **[D]** new prospective extension: separately frozen protocol, fresh seeds 200 to 209, never pooled with the original seeds and never counted in the original 9/0/3 gate outcome. Positioning and feasibility material (literature, datasets) is also labelled [D] and contains no experimental result.

This single document replaces the former `docs/Results.md`, `docs/Novelty Audit.md` and `docs/Second Dataset Feasibility.md`. Sections 1 to 27 are the experimental evidence; 28 to 33 are improvements, literature, dataset feasibility and extensions; 34 to 39 are gaps, decision support, claims, story, limitations and the artifact index.

## 1. Executive Scientific Summary

Evidence classes are defined in section 2. Every number is read from the machine-readable artifacts in `results/` (promoted from `outputs/`).

1. **Collaboration helps locally unseen families [A].** Local unseen-family recall is 0.507 (federation-wide, 5% FPR); FedAvg reaches 0.638 (+0.132, CI 0.090 to 0.167, 10/10 seeds). Full-exposure central training reaches 0.708 (local deficit 0.201, CI 0.164 to 0.231).
2. **For the primary MLP with controlled exposure, the gain is dominated by complementary peer-held family knowledge, not generic pooling [A/B].** CTK +0.117 (0.090, 0.145), 10/10 seeds, Holm p = 0.0059; pooling +0.014 (-0.038, 0.054); CTK share 0.89 (0.65, 1.39), pooling share 0.11 (-0.39, 0.35). Not general: natural scarcity, lower training support and the linear model have pooling shares of about one half or more (sections 6, 10, 16, 18).
3. **The CTK effect persists in sign and practical magnitude** across own-domain (+0.107), worst client (+0.173), family-macro (+0.124), natural scarcity (+0.113), a disjoint family set (+0.064), linear (+0.094) and tree (+0.102) models, both support levels, three operating points, three salts and package-only grouping [A/B]. Excluding negative-control rows, 269 of 276 paired-seed rows and all 33 micro-pooled rows exceed +0.03; the seven exceptions are worst-client estimates at 1% FPR.
4. **The own-domain null control is now resolved [D].** In the original campaign the own-domain permutation interval extended past +0.03 (unresolved). In a separately frozen extension with fresh seeds 200 to 209 (EXT-1), the own-domain FedAvg permutation CTK at 5% FPR is +0.006 (-0.004, 0.014), inside the equivalence band; federation-wide and worst-client controls are also equivalent. The extension is reported separately and is not pooled with the original seeds (section 20, 33).
5. **Family identity is the dominant source of CTK variation [C].** In a two-way decomposition of per-family, per-seed CTK, family explains 69% of the variance in the primary set (27% in the replication set), seed 7% and 9%, family-by-seed residual 23% and 64% (section 12).
6. **Known-family cost is arm- and client-specific [A/C].** FedProx, the strongest arm, changes known-family recall by -0.006 (within ±0.02); FedAvg (-0.033) and fine-tuning (-0.038) exceed it; the loss is largest at anzhi (-0.065) and play-late (-0.037) for FedAvg and moves to play-early (-0.029) for FedProx.
7. **Aggregate metrics hide the unseen-family gain [C].** Aggregate test AUROC/AUPRC of FedAvg (0.915/0.852) and fine-tuning (0.918/0.868) is not better than local (0.927/0.872) although unseen-family recall rises by 0.13 and 0.11; only blend (0.932/0.880) exceeds local. A reviewer reading only aggregate discrimination would conclude collaboration does not help (section 14).
8. **Dose-response gate: corrected from NARROWED to PROMOTED (implementation defect).** Recall rises with effective exposure (0.437 to 0.562); saturation was not observed (section 11).
9. **Feature novelty is unresolved, not disproven [A].** Spearman 0.57 (7 families) and 0.33 (8 families), intervals span zero. The stored gate status remains "rejected".
10. **No headroom for a new federated mechanism [A]**; several families stay poorly recalled even under full exposure and in other model classes (representation-limited).
11. **Original gate counts: 9 promoted, 0 narrowed, 3 rejected, 0 insufficient** (the original promotion recorded 8/1/3). No extension outcome changes these counts.
12. **Literature: no direct collision after full-text reading of the closest papers.** The closest experimental analogue is CELEST (family first seen at one network, present at a peer, local versus federated on that family), followed by FedVLS, Breitholtz et al., Otani et al., Bi et al. and CyberForce (sections 25 to 27). The combined measurement design was not found in any full-text paper; individual ingredients have precedent.
13. **External replication is not justified by the data available now.** KronoDroid, inspected directly, is MARGINAL (at most 14 families pass the unweakened gate, era-confounded clients); McNdroid overlaps LAMDA by 81% and can only support a representation check; no other audited corpus meets the requirements (sections 29 to 31).

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

What the curve shows: the gate-supported statement is that recall improves as effective peer exposure increases and the predeclared dose-response gate is satisfied. What is **not** established is a saturation point: recall is still rising at the largest effective exposure, so the diminishing-returns half of H5 is unresolved. Requested doses badly overstate exposure (client caps and availability): requested 100 delivers about 9 samples, so "100 samples" is only reached by the all-available level and part of the 1000 level. Observation-level sensitivity (the 70 rows with at least 100 effective samples) gives mean gain +0.045; leave-one-family-out mean at least 0.040 (five families, one with two rows). Not driven by one family under either reading (level reading: at least +0.089). The dose effect is family-dependent: dowgin shows no gain (-0.004) even with a mean of 1,188 effective samples, revmob (+0.336) and leadbolt (+0.268) show large gains at 55 and 84 samples. Centralized and fine-tuned arms follow the same rising shape (all-available gain +0.110 and +0.090).

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

### 12.1 Heterogeneity structure [C]

Post-confirmatory, exploratory (`ctk-variance-components.csv`, `family-associations.csv`, `family-client-ctk.csv`).

- **Variance components.** Two-way decomposition (family by seed, no replication) of the per-family, per-seed FedAvg CTK (mean over evaluating clients): primary set (7 families, 10 seeds) family 69.5%, seed 7.5%, family-by-seed residual 23.1%; replication set (8 families, 10 seeds) family 27.3%, seed 8.5%, residual 64.2%. Family identity dominates in the primary set; in the replication set most variation is family-by-seed, so which families are hidden and how in a given seed matters more there. This quantifies "family dependence" beyond the gate's range statistic.
- **Family-level associations (descriptive, 8 tests, no multiplicity claim).** Spearman association between family local recall and CTK gain: primary rho -0.32 (p 0.48, n 7), replication rho -0.81 (p 0.015, n 8; not significant after a Holm correction over the eight tests, 0.12). Lower local recall is descriptively associated with larger CTK (exposure-limited families benefit most), consistent with the family patterns above; the total gain and pooling-gain associations are partly mechanical (total = pooling + CTK).
- **Hidden-family by target-client table.** 22 (client, family) target pairs are observed in the primary set, each in only 1 to 6 seeds and with as few as 10 hidden test trials per seed, so per-pair intervals are unstable; the pattern is descriptive: strong CTK at play-late for revmob (+0.50, 5/5 seeds) and leadbolt (+0.61, 3/3), at appchina for revmob (+0.11) and leadbolt (+0.14), near zero for dowgin and hiddad at every client, and negative for dowgin at play-early (-0.09). Per-pair inference would require more seeds or a dedicated design (section 34).

## 13. Representation-Limited Families [A]

The gate `representation-limited-family` is promoted with scoped wording: 3 of 4 poorly recalled primary families (full-exposure central recall below 0.60) are also poor in an independent model class (linear or trees): hiddad, gappusin, revmob. adwo (full 0.585) is poor only for the MLP; linear 0.667 and trees 0.761 are adequate. Bounded interpretation, under the tested static representation and models: exposure alone does not explain all family-level failures. Independent-model evidence exists only for the primary family set; replication-set families (for example utchi, full 0.438) have no cross-model check.

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

Aggregate discrimination does not show the collaboration benefit: FedAvg and fine-tuning are below local although their unseen-family recall is higher by 0.13 and 0.11, because the aggregate pools mostly known-family malware. This is the same structure as the "misleading convergence certificate" in Otani et al. (overall accuracy flat while rare-class recall falls). The family-absent-everywhere FedAvg model is worse than every other arm (AUROC 0.900), so peer-held family data also helps aggregate discrimination relative to no family, but only to the level of local training. Reporting unseen-family recall at fixed FPR, as this study does, is therefore necessary and not a choice of convenience.

Share of clients that beat local training on unseen-family recall (a negative-transfer view, as in FedCollab's individual-participation rate): FedAvg total gain is positive for 4 of 4 clients in point estimate and has an interval excluding zero for 3 of 4 (anzhi +0.005, interval -0.056 to 0.086). Negative-transfer gap components are the pooling gains in section 8 and 9: negative pooling at anzhi (-0.074) and, for own-domain evaluation, at all four clients.

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

Interpretation, per the rule frozen in advance: the primary endpoint is met (interval inside ±0.03), so the own-domain null control is clean in the extension; the original caveat is reported as "unresolved in v1 (seeds 100 to 109), resolved in v2 (seeds 200 to 209)". The original permutation result and the original gate counts are unchanged. The centralized arm's worst-client control is unresolved at 1% and 5% FPR (secondary, not a pre-specified endpoint). One family-macro cell at 1% FPR straddles the band edge.

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
3. [B] Natural scarcity reproduces the CTK magnitude within the same corpus (+0.113 versus +0.117), a within-dataset validation of the controlled design (not external validation); its decomposition differs.
4. [A/C] FedProx preserves known-family recall within tolerance while retaining the unseen-family benefit; FedAvg and fine-tuning do not.
5. [A] Peer-family benefit grows with effective exposure, and several families stay poorly recalled even under full exposure (representation limits), while standard baselines leave no headroom for a new mechanism.

## 27. Negative and Narrowed Findings

- Generic-pooling-majority rejected; and the linear, natural-scarcity and lower-support settings show large pooling components, so no model-general CTK dominance.
- Feature-novelty gate not satisfied (unresolved).
- New-mechanism trigger not met. Headroom versus central full exposure (`mechanism-headroom.csv`), mean gap (threshold 0.10): FedAvg 0.070 (0.043, 0.096), FedProx 0.062 (0.022, 0.089), fine-tune 0.094 (0.057, 0.138), blend 0.074 (0.049, 0.104), central 0.049 (0.020, 0.078); worst-client gap (threshold 0.15): FedAvg 0.029 (-0.026, 0.087), FedProx 0.074 (0.023, 0.126), fine-tune 0.047, blend 0.081, central 0.042. The mean gaps have upper bounds up to 0.138, so a residual gap cannot be excluded for fine-tuning, but the point estimates are below both triggers for every baseline; strong simple baselines already recover 0.56 to 0.71 of the exposure-related gap. Remaining failures for hiddad and gappusin persist under full exposure and in other model classes: representation, not federated optimization, is the more important remaining limitation, for this static representation and dataset only.
- Known-family cost of FedAvg and fine-tuning; own-domain permutation caveat; own-domain oracle-gap recovery only 0.23.
- Dose: no saturation, unreachable low requested doses, dowgin flat.

## 28. Evidence-Preserving Scientific Improvements

Class C additions, all from stored runs: per-client CTK analysis (section 14), local-anchored worst client (section 9), arm trade-off (15), robustness synthesis and forest plot (21), family patterns (12), natural-versus-controlled table and figure (10), permutation audit by population and alpha (22), headroom and operating-point fidelity tables. Corrected implementation defects (dose gate level handling, family-dependence scope, per-salt micro rows, natural-scarcity classification, provenance split, non-deterministic ordering) are logged in `docs/decisions/protocol-amendments.md`. No original confirmatory seed-level metric, paired effect, threshold or family set changed.

### 28.1 Reviewer-Gap Matrix

What a strong reviewer, informed by the full-text literature, would expect this study to contain. "Existing evidence" means stored confirmatory artifacts or class C analyses.

| Potential gap | Literature precedent | Does CTK already address it? | Importance | Can existing evidence answer it? | Needs new experiment? | Recommended action |
|---|---|---|---|---|---|---|
| Local-only baseline and a negative-transfer view (does collaboration hurt some clients?) | CELEST Table III (local vs global on unseen family); FedCollab (individual participation rate); negative-transfer survey (gap = with source minus without) | yes: local arm, total gain, pooling gain, per-client table, known-family cost | High | yes: 3 of 4 clients have a total-gain interval above zero; anzhi about zero; pooling negative at anzhi | no | reported (sections 9, 14) |
| Volume-matched peers (is the gain just more data?) | Breitholtz et al. (fixed 2,000 samples per client while label sets vary) | yes: family-absent-everywhere arm has identical training volume (run logs: `train_rows` equal across arms) and sample-size matching is a structural validation | High | yes | no | state explicitly (sections 5, 20) |
| Placebo: is restoring the family just adding a different malware distribution? | none of the read papers has one | partly: the family-label permutation control restores a random malware subset with the original family-size distribution and yields CTK equivalent to zero (federation-wide, original; own-domain and worst-client, extension EXT-1) | High | yes for label-independent artefacts; a real other-family placebo (add a coherent different family with equal counts) is not implemented | optional, low expected value | permutation control judged sufficient; real-other-family placebo NOT run (section 33) |
| Own-domain negative control | none | unresolved in v1 | Medium | no | yes, cheap | **run**: EXT-1, resolved in v2 (section 20.1) |
| Missing-class-aware FL baselines (FedRS, FedLC, FedVLS, FedMR, FedGELA) | many image-classification papers; Otani et al. argue label-skew methods cannot recover a missing direction without samples | no: baselines are FedAvg, FedProx, fine-tuning, blend, central | Medium | no | not with the current task: these methods correct softmax or logit statistics of a label space in which the class is missing; our detector is binary and the hidden unit is a family inside the positive class, so they are undefined without turning the task into multi-class family classification | not added; documented as a limitation; a family-multiclass formulation would be a new mechanism study (headroom gate already closed) |
| Robust aggregators erase rare-peer knowledge | CyberForce (Trimmed Mean, Krum) | not tested (benign setting, FedAvg weighted mean) | Low to medium | no | optional | limitation; adversary-free scope |
| Aggregate discrimination metrics (AUROC/AUPRC) and fixed-FPR recall | CELEST reports PR-AUC and FPR at recall 0.9 | yes: recall at fixed FPR is primary; AUROC/AUPRC stored | Medium | yes: aggregate metrics do not show the gain (section 14.1) | no | reported |
| Worst-client and dispersion metrics | q-FFL, AFL, TERM (worst-10%, variance) | yes: worst client, anchored worst client, client-recall dispersion | Medium | yes | no | reported (section 8) |
| Family-relatedness confound (Mirai/Gafgyt transfer even locally) | CELEST; CyberForce hypothesis | partly: nearest-known-family distance descriptor, unresolved | Medium | descriptor unresolved with 7 to 8 families | larger-family study (optional) | limitation; no descriptor fishing (section 21) |
| Uncertainty and seeds | prior work uses 0 to 8 seeds, rarely tests | yes: 10 seeds, BCa, exact Wilcoxon, Holm on the primary contrast family | High | yes | no | strength |
| Heterogeneity beyond a range statistic | hierarchical or variance reporting is rare in FL | now yes: variance components (section 12.1) | Medium | yes | no | added (class C) |
| External-dataset replication | Bi et al. and others use Drebin/AndroZoo; none replicates a decomposition | no | High | no | only if a suitable corpus exists | not feasible with audited public data (sections 29, 30) |
| Representation replication (richer features) | CyberForce and Cybersecurity 2026 (FedBN) offer representation-side explanations | partly: two model classes, full-exposure ceiling | Medium | no | McNdroid feasible but engineering-heavy | DEFER (section 32) |
| Dose over peer samples, exact effective dose | Breitholtz (labels per client), Otani (missing mass rho), CELEST (client count) | partly: requested and effective dose analysed, no saturation | Medium | no | exact-effective-dose experiment (optional) | not run (section 33) |
| Temporal generalization (LAMDA is longitudinal) | LAMDA, concept-drift literature | not the question of this study | Medium | no | not for this claim | limitation |
| Communication and privacy costs | most FL papers | out of scope | Low | n/a | no | limitation |

## 29. Novelty Assessment [D, positioning only]

### 29.0 Update after the full-text strengthening pass

A third pass read the primary sources in full where they could be retrieved (19 of 48 retained literature notes are full text; 4 primary sources remained unavailable after retries: FedRS (KDD 2021), FedLMD, FedCKD, FID-SPA; the rest are targeted or abstract-level notes with depth recorded per note). It added CELEST, CyberForce, Otani et al., FedGELA, FedMR, FedRoD, FedAwS, FedLC, FedNTD, Zec/Breitholtz FedPALS and Maverick-class papers, and a proceedings-level security-venue sweep. Verdicts are unchanged in category: N1, N2, N3, N7 and N8 stay plausible differentiators; N4 stays weak-plausible; N5 and N6 stay partial collisions; no direct collision was found. Two findings sharpen the positioning: (a) missing-class methods (FedRS, FedLC, FedVLS, FedMR, FedGELA) correct softmax or logit label-space statistics and are undefined for a family that lives inside the positive class of a binary detector, so they are not applicable baselines; (b) CELEST and CyberForce name family relatedness and rare-peer erasure by robust aggregation as confounds, which the decomposition here measures rather than assumes. Retry retrieval of the unavailable sources was attempted and is recorded as a blocker, not as evidence. No priority claim is made. The sections below are the second-pass audit text, retained unchanged except for renumbering.

### 29.1 What was done

- **Search:** about 25 search or discovery calls across a general academic index (Semantic Scholar/Scopus/arXiv-style) and an arXiv/alphaXiv discovery tool, plus four arXiv API title lookups to obtain full-text access, and six Semantic Scholar citation-graph requests (four returned data, two were rate-limited). Across both audits roughly 200 distinct records were screened by title and abstract; 35 matrix rows resulted.
- **Reading depth (reported per paper below):** seven papers were read in full, extracted text, by structured checklist (FedVLS, Breitholtz et al., MAP, Bi et al., GLFC, CELM, FedP3E); every other paper was assessed from its abstract only, and where the primary source was not read at all this is stated. Three dataset papers (MH-1M, AndroTruth, McNdroid) were read for dataset facts only; they are not collision candidates.
- **Checklist applied to each full-text paper:** problem definition; how client labels are created; whether classes are absent by design or incidentally; whether absence is controlled (one class removed from one client with the rest matched); sample-count matching; class removed from all clients as a control; whether the effect of peers holding the class is isolated for the client lacking it; evaluation population; dose or support sweep; worst-client or per-client analysis; full-exposure reference; natural versus artificial scarcity; representation-level explanation; decomposition of collaboration benefit into generic pooling versus class-specific knowledge.
- **Backward chaining:** reference lists and related work of the full-text papers (FedRS, FedAwS, FedGELA/FedMR partially class-disjoint data, FedROD, class-imbalance FL, FEDroid, DW-FedAvg, FedCRI/others cited by Bi et al.).
- **Forward chaining (citations of the close papers):** MAP: 16 citing papers, none on malware or a controlled absent-class design. LAMDA: 12 citing papers, one federated (a drift-aware federated continual-learning Android malware paper, 2026, abstract-level only, drift focus). Breitholtz et al. and FedP3E: no citing papers indexed (recent). FedVLS: request rate-limited, not retrieved. CELM, FedRS, FEDroid, Otani et al.: not retrievable.
- **Synonym coverage:** vacant / missing / absent / incomplete / class-deficient / disjoint / partially class-disjoint / label-set heterogeneity / label-skew / rare / minority / long-tail / class coverage / class-specific contribution / locally unseen. Different terminology found: partially class-disjoint data (FedGELA, FedMR), positive-labels-only (FedAwS), "Maverick" rare classes (CELM).
- **Security-venue sweep:** USENIX Security, CCS, NDSS, RAID, DIMVA, ACSAC, IEEE S&P, DSN, Computers & Security, TDSC, TIFS and TOPS were queried by name in combination with federated/collaborative malware terms and, for Computers & Security, with a journal filter. The indexes do not expose conference proceedings reliably: the sweep surfaced one RAID 2024 paper (cross-regional malware detection, Botacin et al.), FEDroid (TIFS 2023), M2FD (Computers & Security 2025), and an NDSS 2022 federated-intrusion paper cited by Bi et al. (not read). No proceedings from USENIX Security, CCS, S&P, ACSAC, DIMVA or TDSC/TOPS were retrieved by these queries; absence from the search results is not evidence of absence from those venues.


### 29.2 Collision matrix

Columns: Miss = missing/vacant/incomplete/disjoint classes at clients; Rem = controlled removal of a specific class from a specific client, rest matched; Match = total sample size matched; Abs = class removed from all clients as matched control; Dec = pooling-versus-class-knowledge decomposition; Dose = peer-sample dose of the missing class; Own = own-domain evaluation of the missing class at the target client; Wst = worst-client analysis; Nat = artificial intervention validated against natural scarcity; Full = full-exposure or centralized reference; ExpRep = exposure-versus-representation diagnosis. y / p (partial) / n (not found in what was read). "n" for an abstract-only paper means "not visible in the abstract" and is weak evidence.

| Paper | Year | Venue | Domain | Miss | Rem | Match | Abs | Dec | Dose | Own | Wst | Nat | Full | ExpRep | Collision | Reading depth |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Exploring Vacant Classes in Label-Skewed FL (FedVLS), Guo et al. | 2025 | AAAI (arXiv 2401.02329) | images, text | y (Dirichlet/shard skew) | n | n | n | n | n | n | p (client-3 confusion, client-0 table) | n | p (initial global model as teacher/reference) | p (logit/loss-level cause) | PARTIAL | FULL TEXT |
| FL with Heterogeneous and Private Label Sets, Breitholtz et al. | 2025 | arXiv preprint | images | y (labels per client swept) | p (label-set size manipulated) | y (samples per client fixed at 2,000) | n | n | p (labels per client, not peer samples of a class) | n | n | n | n | n | PARTIAL | FULL TEXT |
| Objective Mismatch in FL under Missing Class Support, Otani et al. | 2026 | IEICE Trans. Fundamentals | fall detection, synthetic | y (rare class absent at most clients) | n | n | n | n (theory: irreducible bias) | n | n | n | n | n | n | PARTIAL | ABSTRACT ONLY |
| Enabling Privacy-Preserving Cyber Threat Detection with FL, Bi et al. | 2024 | arXiv preprint | Android malware (Drebin+AndroZoo), SMS spam | y (k families per client, by design) | n | n | n | n | n | n | n | n | y (centralized comparison) | n | PARTIAL | FULL TEXT |
| MAP: Model Aggregation and Personalization in FL with Incomplete Classes, Li et al. | 2024 | IEEE TKDE (arXiv 2404.09232) | images | y | p (centralized targeted-class experiment) | p (same targeted samples, not total) | n | n | p (sweeps number of targeted classes) | n | p (per-client change histogram) | p (FEMNIST natural vs random assignment, no like-for-like) | p | p (classifier-proxy collapse) | ADJACENT | FULL TEXT |
| Federated Class-Incremental Learning (GLFC), Dong et al. | 2022 | CVPR (arXiv 2203.11473) | images | y (60% classes per client, new classes over time) | n | n | n | n | n | n | n | n | n | p (last-layer gradient explanation) | ADJACENT | FULL TEXT |
| CELM: class-wise contribution estimation, Ukaye et al. | 2026 | arXiv preprint | images, dermatology | y (PLS/SLS/Dirichlet/Maverick) | n | p (PLS totals fixed) | n | n | n | n | n | p (FedISIC natural vs synthetic splits, no like-for-like) | p (IID sanity check) | p (logit probes) | ADJACENT | FULL TEXT |
| FedP3E: prototype exchange, non-IID IoT malware, Darwish et al. | 2025 | arXiv preprint | IoT malware (N-BaIoT), 3 clients | y (disjoint/rare variants by design) | n | n | n | n | n | n | n | n | p (IID scenario) | n | ADJACENT | FULL TEXT |
| FEDroid: comprehensive Android malware detection with FL, Fang et al. | 2023 | IEEE TIFS | Android malware | n (variants via evolution) | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| A method for real-world privacy-preserving Android malware detection through FL, Ciaramella et al. | 2025 | Inf. Softw. Technol. | Android malware, 71 families | n (IID vs non-IID) | n | n | n | n | n | n | n | n | y (centralized comparison) | n | ADJACENT | ABSTRACT ONLY |
| FedRS: FL with restricted softmax for label-distribution non-IID data, Li & Zhan | 2021 | KDD | images | y | n | n | n | n | n | n | n | n | n | p | ADJACENT | described only in MAP/FedVLS/CELM (primary not read) |
| FL for Malware Image Classification under Data Heterogeneity, Taiwo et al. | 2026 | preprint/journal (not stated) | malware images | p (class entropy) | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| Cross-Regional Malware Detection via Model Distilling and FL, Botacin et al. | 2024 | RAID | AV-company malware, 3 regions | n | n | n | n | n | n | n | n | n | y (global combined) | n | ADJACENT | ABSTRACT ONLY |
| FL for Malware Detection in IoT Devices, Rey et al. | 2021 | Computer Networks | IoT malware (N-BaIoT) | p (seen vs unseen devices) | n | n | n | n | n | n | n | n | y (local vs centralized vs FL) | n | ADJACENT | ABSTRACT ONLY |
| FedHGCDroid; FedDRC; uitAnDiNeFed; DW-FedAvg; Lee (Sensors); Kushwaha | 2022–25 | Entropy; CSCWD; Wireless Netw.; CCPE; Sensors; ICICV | Android malware | n | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FL-MalDrift; M2FD; FALCON; COR-FL; SCFM-FedRL; drift-aware federated continual learning (2026) | 2025–26 | Sci. Rep.; Comput. Secur.; IEEE TMC; conferences; IEEE Access | Android malware, drift | n | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| Cross-silo FL in SOCs (Xenos et al.); FL in malware detection (Serpanos et al.); CTI sharing via FL (Sarhan et al.) | 2021–25 | Int. J. Inf. Secur.; ETFA; J. Netw. Syst. Manage. | malware/intrusion, organizations | n | n | n | n | n | n | n | n | n | y | n | ADJACENT | ABSTRACT ONLY |
| Federated Attack Campaign Detection via Contrastive Encoding of Threat Indicators | 2026 | arXiv preprint | threat intelligence | n | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FedExIT, Saha et al. | 2025 | Information Fusion | images, medical | y | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| Who to Trust? Aggregating client predictions in federated distillation (class mismatch) | 2025 | arXiv preprint | images | y | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FedAwS (positive labels only); FedGELA / FedMR (partially class-disjoint data); FedROD | 2020–24 | ICML; NeurIPS; ICLR | images | y | n | n | n | n | n | n | n | n | n | n | ADJACENT | not read (cited in read papers) |
| Contribution estimation / data valuation in FL (Wei et al.; Zhu et al.; Chen et al., VLDB 2024; Li et al. CVPR 2024) | 2020–24 | various | generic | n | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FedCollab (negative transfer, collaboration structure), Bao et al. | 2023 | arXiv preprint | generic | n | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FedProto and prototype FL (Tan et al.; FedSA; FedHCL) | 2021–25 | AAAI-era/various | generic | p | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| FAMCF; EC2; Meta-MAMC (few-shot / zero-day Android family classification, non-FL) | 2020–24 | Comput. Secur.; IEEE TDSC; ACM TOSEM | Android malware | y (few-shot families) | n | n | n | n | n | n | n | n | n | n | ADJACENT | ABSTRACT ONLY |
| LAMDA, Haque et al. (primary data source) | 2025 | arXiv preprint | Android malware dataset | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NONE (data) | ABSTRACT ONLY |
| KronoDroid; MH-1M; Maloid-DS; AMD; CICMalDroid; CCCS-CIC-AndMal-2020 (datasets) | 2018–25 | various | datasets | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NONE (data) | ABSTRACT ONLY |
| Fair comparison of Android malware detectors, Molina-Coronado et al. | 2022 | Comput. Secur. | Android malware (non-FL) | n | n | n | n | n | n | n | n | n | n | n | NONE | ABSTRACT ONLY |

Counts over the rows above (a row may group several closely related papers): **0 DIRECT, 4 PARTIAL, 20 ADJACENT, 3 NONE**.

Papers by depth: **7 full text** (FedVLS, Breitholtz et al., MAP, Bi et al., GLFC, CELM, FedP3E); **0 methods-and-results-only**; **0 abstract-and-intro** (the earlier audit's "abstract + intro" entries for CELM and FedP3E are upgraded to full text); **about 25 abstract only**; a further group not read (FedRS, FedAwS, FedGELA, FedMR, FedROD, cited in read papers).


### 29.3 Explanation of every PARTIAL collision

- **FedVLS (full text).** Vacant classes (absent from a client's Dirichlet or shard draw) are its subject; it compares class-wise accuracy of the initial global model and of the locally updated model on vacant classes (Fig. 1, Table 12), and explains the local decay at the logit/loss level. It is not a controlled design: absence is "incidental" to the partition, there is no matched removal, no matched sample count, no class-absent-everywhere control, no peer dose, no own-domain population, and headline evaluation is global test accuracy. Overlap: the evaluation motif (locally absent classes, local versus global recall) and a mechanism-level explanation.
- **Breitholtz et al. (full text).** Manipulates the number of labels each client holds while fixing samples per client (2,000), which is close to our matched-size principle, and sweeps label-set size (a coarse dose over label diversity). It measures global accuracy of aggregation methods, not recall on a locally hidden class, and has no absent-everywhere control or decomposition. Overlap: exposure manipulated at fixed sample volume.
- **Otani et al. (abstract only).** Proves an irreducible bias for rare classes absent from most clients under FedAvg-type objectives. Consistent with our FedAvg known-family/unseen-family trade-off. Because only the abstract was accessible, its experimental design (synthetic and one real fall-detection dataset) is unverified; classified PARTIAL on stated topic, with high uncertainty.
- **Bi et al. (full text).** Android malware FL on Drebin (179 families, 133 after filtering) and AndroZoo benign, with a "family-based non-IID" setting where each client holds only k families (k in {1..4} cross-device, {5..30} cross-silo), and a centralized reference. It finds unstable training as k shrinks and no clear performance pattern. Overlap: same domain, families absent from clients by design, centralized reference. Non-overlap: only a global held-out test set (no per-family or per-client recall), no controlled removal, no matched control, no decomposition, no dose (only skew parameters), binary detection task.


### 29.4 What the closest full-text designs do not do

Across the seven full-text papers none has: a specific class deliberately removed from a specific client with the rest of training matched; a class removed from all clients as a control; a measurement isolating the effect of peers holding the class for the client lacking it; a sweep of how many samples of that class peers hold; own-domain or worst-client evaluation of the missing class; a like-for-like natural versus artificial comparison of the same estimand; a decomposition of collaboration benefit into generic pooling and class-specific knowledge. Partial overlaps that must be acknowledged: MAP's centralized targeted-class experiment (Fig. 7) and its observation that extra classes can hurt a client's own-class accuracy (compatible with our negative pooling); MAP and CELM report natural (FEMNIST, FedISIC) and synthetic splits side by side; FedP3E has fully disjoint malware class sets across three clients; Bi et al. has families absent from clients on Android malware; FedVLS and MAP give logit/proxy-level explanations of missing-class failure.

Ingredient coverage:

| Ingredient | Verdict from audited literature |
|---|---|
| locally missing family/class at a client | present (FedVLS, MAP, Bi, FedP3E, CELM, GLFC) |
| matched controlled removal | not found (MAP centralized analogue only) |
| target class present at peers | implicit everywhere; not isolated |
| class absent from all clients as matched control | not found |
| full-exposure reference | partial (centralized comparisons in Bi, Ciaramella; IID references) |
| decomposition total / pooling / complementary | not found |
| own-domain evaluation of the hidden class | not found |
| worst-client evaluation | partial per-client diagnostics (FedVLS, MAP); no worst-client CTK |
| peer-sample dose | not found (label-count and class-count sweeps exist) |
| natural-scarcity check of the same estimand | not found (natural and synthetic splits reported side by side in MAP, CELM) |
| exposure-versus-representation diagnosis | partial mechanism explanations; no full-exposure plus cross-model diagnosis |


### 29.5 Reassessed candidate contributions

| Candidate | Verdict | Reason |
|---|---|---|
| N1 controlled-exposure decomposition (matched family-absent-everywhere control separating pooling from complementary knowledge) | PLAUSIBLE DIFFERENTIATOR | Not found in seven full-text reads; MAP's centralized inclusion experiment is the nearest analogue and is not federated or decomposed. |
| N2 malware-family CTK in Android FL | PLAUSIBLE DIFFERENTIATOR | Bi et al., FedP3E and Ciaramella et al. are the nearest Android/IoT FL papers; none measures per-family counterfactual recall for a locally missing family. |
| N3 own-domain decomposition | PLAUSIBLE DIFFERENTIATOR | Not found; FedVLS's local-model diagnostics evaluate vacant classes but on a global test set. |
| N4 worst-client CTK | PLAUSIBLE DIFFERENTIATOR (weak) | Per-client diagnostics exist (FedVLS, MAP); worst-client class-specific complementary effect not found. Worst-client fairness is generic, so this is a combination claim only; fairness-in-FL literature (q-FFL-type) was not audited in depth. |
| N5 natural-scarcity validation | PARTIAL COLLISION | Reporting natural and synthetic partitions together is established (MAP with FEMNIST, CELM with FedISIC); what was not found is a check that a controlled-removal decomposition reproduces at the same magnitude under natural scarcity. Downgraded from the first audit. |
| N6 peer-sample dose response | PARTIAL COLLISION | Sweeps of classes per client (MAP) and labels per client (Breitholtz et al.) and Dirichlet skew (FedVLS, CELM) exist; a sweep of peer samples of the missing class linked to the incremental benefit for a client was not found. |
| N7 exposure-versus-representation diagnosis | PLAUSIBLE DIFFERENTIATOR | Mechanism explanations exist (MAP proxy collapse, FedVLS logits, GLFC last-layer gradients); a full-exposure plus independent-model-class diagnosis of family-level failures was not found. |
| N8 combined framework | PLAUSIBLE DIFFERENTIATOR | No paper found providing essentially the same measurement framework; most ingredients individually have partial precedent. |


### 29.6 Strongest defensible positioning (narrowed)

Prior work already establishes that classes absent from a client are poorly recognized (FedVLS, MAP, Otani et al.), studies Android and IoT malware FL under non-IID partitions including families held by only some clients (Bi et al., FedP3E, FEDroid, Ciaramella et al.), and reports natural and synthetic partitions side by side (MAP, CELM). Wording supported by the audit:

> In the audited literature we found no closely matching study that isolates, for a client that lacks a malware family, the effect of peers holding that family by combining a controlled hidden-family design with a matched family-absent-everywhere collaborative control and a full-exposure reference, and that uses this to decompose collaboration gain into generic pooling and complementary family knowledge with own-domain and worst-client evaluation on Android malware. Locally missing classes, family-skewed Android malware FL, exposure sweeps and natural-versus-synthetic partitions each have precedent; our contribution is their combination into a measurement design and its empirical decomposition on one corpus, not a new learning algorithm.

The earlier list-style statement (which also named the peer-exposure dose analysis and the natural-scarcity check as part of what was not found together) is retained only in this combined form; dose and natural-scarcity are individually partially anticipated and are not presented as independent novelty.


### 29.7 Lost and gained differentiation after the deeper audit

- **Lost or weakened:** N5 (natural scarcity) and N6 (dose) are now PARTIAL COLLISION; "Android malware FL with families absent from clients" is not new (Bi et al.); disjoint malware classes across clients are not new (FedP3E); mechanism-level explanations of missing-class failure are not new.
- **More clearly differentiated:** N1 and N8. Seven full-text reads did not find a class-absent-everywhere control, a controlled per-client removal, or a decomposition, and the closest malware FL papers evaluate only global test metrics.


### 29.8 Limits

- Only seven papers were read in full. About 25 relevant papers were abstract-only; an abstract-only "n" is weak evidence of absence. FEDroid, Ciaramella et al., Otani et al., Taiwo et al. and Botacin et al. are the most important unread primary sources; Otani et al. and FedRS could not be retrieved from open sources.
- The security-conference proceedings (USENIX Security, CCS, S&P, ACSAC, DIMVA, NDSS) are not reliably indexed by the tools; the sweep cannot rule out relevant papers there.
- Forward citations were obtained only partially (Semantic Scholar rate limits; very recent papers have few citations).
- Fairness-in-FL (worst-client) and negative-transfer literatures were sampled, not audited in depth.
- Before any manuscript novelty claim: full-text reading of FEDroid, Ciaramella et al., Otani et al., FedRS, FedGELA and Taiwo et al.; a proceedings-level sweep of the security venues; forward-citation retrieval for FedVLS, FedRS, FedP3E and Bi et al.; and a re-run of this audit at submission time.


### 29.9 Closest ten papers

1. Exploring Vacant Classes in Label-Skewed FL (FedVLS), AAAI 2025 — PARTIAL, full text.
2. FL with Heterogeneous and Private Label Sets (Breitholtz et al.), 2025 — PARTIAL, full text.
3. Enabling Privacy-Preserving Cyber Threat Detection with FL (Bi et al.), 2024 — PARTIAL, full text (Android malware, family-skewed clients).
4. Objective Mismatch in FL under Missing Class Support (Otani et al.), 2026 — PARTIAL, abstract only.
5. MAP: Model Aggregation and Personalization in FL with Incomplete Classes, IEEE TKDE 2024 — ADJACENT, full text.
6. FedP3E, 2025 — ADJACENT, full text (disjoint malware classes across clients).
7. CELM, 2026 — ADJACENT, full text.
8. FedRS (KDD 2021) — ADJACENT, primary not read.
9. FEDroid, IEEE TIFS 2023 — ADJACENT, abstract only.
10. Federated Class-Incremental Learning (GLFC), CVPR 2022 — ADJACENT, full text.

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
| **Maloid-DS, OmniDroid, Ciaramella et al. dataset** | Maloid-DS 345 families (47,971 malware, about 139 per family), OmniDroid none usable, Ciaramella 71 families | unclear | none found | unclear | not obtained | no public download found | UNKNOWN / NEEDS ACCESS |

**Verdict on a second independent Android dataset: DO NOT RUN, DEFER.** No audited public corpus meets all requirements. The only one with an independent source, benign samples, a family column and a date axis that could be downloaded and inspected (KronoDroid) fails the unweakened gate for the 7+8 design and would test a different, era-confounded question. A poorly matched replication would be less informative than an explicit one-corpus limitation. Re-open only if a corpus with real market or source metadata, benign samples and at least 15 families with several hundred de-duplicated samples at three or more clients becomes available.

### 30.1 Can the CTK protocol be reused, per plausible candidate?


Plausible candidates after screening: KronoDroid (best on paper, unverified), CCCS-CIC-AndMal-2020 (support but no client axis), McNdroid and MH-1M (not independent; useful only for a representation or feature-extraction replication).

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
- **Decision: DEFER (not run in this pass).** Value: informs N7 only and is not external validation; engineering cost is substantial; existing evidence already supports representation limitation for hiddad and gappusin in two other model classes. It becomes worthwhile if a reviewer specifically demands a representation-level test.

## 33. New Scientific Extensions

Only literature-justified additions were considered. Each was assessed against what the stored evidence already answers.

| Experiment | Scientific weakness addressed | Literature justification | Existing evidence already sufficient? | Expected value | Cost | Decision |
|---|---|---|---|---|---|---|
| **EXT-1** own-domain / worst-client permutation control, fresh seeds 200 to 209 | own-domain null control unresolved in v1 (interval -0.004 to 0.036) | reviewers expect a clean negative control for every headline population (Otani et al. warn about misleading certificates; Breitholtz et al. and Zec et al. use 8 to 10 seeds with CIs) | no | high for the causal wording of the own-domain claim | 10 runs, about 45 s to 5 min each | **RUN** (completed, section 20.1) |
| Missing-class-aware FL baseline (FedRS, FedLC, FedVLS) | comparator gap | image-domain missing-class literature | not applicable | low: label-space methods are undefined for a family inside the positive class of a binary detector | high (new multi-class formulation and new mechanism) | DO NOT RUN; limitation stated |
| Real other-family placebo (equal-count coherent family added instead of the target) | "adds malware volume, not family knowledge" | not present in any paper read | largely: the permutation control already restores matched malware volume with family structure removed | low to medium | new arm construction, fresh seeds | DO NOT RUN; permutation control judged sufficient |
| External replication on KronoDroid | corpus dependence | none replicates a decomposition | no | would be high if feasible | high | DO NOT RUN: MARGINAL (section 31) |
| Representation replication on McNdroid | exposure versus representation (N7) | representation-side explanations exist (FedBN, similarity) | partly (linear and tree models) | medium; not external validation | high (new data-source adapter, 81% overlap) | DEFER (section 32) |
| Exact-effective-dose follow-up | saturation and dose thresholds | dose sweeps in the literature use classes or labels per client, not peer samples of one class | partly (requested and effective dose analysed) | medium, only if a saturation claim matters | medium | DEFER |
| Larger-family explanatory study (feature novelty) | why CTK varies | family relatedness is the literature's own confound (CELEST) | no (7 to 8 families) | medium | high | DEFER; needs a predeclared descriptor |
| Broader CTK-versus-pooling dominance study | model-general claim | none | no | low to medium | medium | DO NOT RUN unless a general claim is wanted |
| New federated mechanism | headroom | crowded literature | headroom below both triggers | none demonstrated | high | DO NOT RUN |

### 33.1 Feature-novelty mechanism reassessment

After full reading, the literature points to two other candidate mechanism variables: classifier-level margin/logit collapse for vacant classes (FedVLS, MAP, FedLC) and prototype or class-conditional representation distance (FedMR, FedP3E). The originally predeclared descriptor (nearest known-family distance) is the same family-relatedness idea that CELEST and CyberForce themselves invoke, so it remains the most appropriate training-only descriptor. Logit and margin variables need trained models on the hidden family and cannot be computed from training-only evidence without the arms already run, so they are proposed as future, separately frozen work and not retrofitted into H7. No additional descriptors were searched.

## 34. Remaining Evidence Gaps

- One dataset (LAMDA plus AndroZoo metadata), simulated market clients, four clients; no independent Android dataset. Natural scarcity is a within-dataset validation, not external.
- Feature novelty unresolved with 7 to 8 families.
- Dose: the criterion is reached only at the top levels, effective dose is far below requested dose, and no saturation region was observed, so the diminishing-returns half of H5 is unresolved.
- Own-domain permutation control unresolved; worst-client estimates unstable at 1% FPR.
- Per-client analysis is descriptive: two of four clients have fewer than 10 seeds, per-client intervals are exploratory small-n BCa intervals, four clients cannot support causal or gradient claims.
- Trees have no federated arm; cross-model checks cover the primary family set only.
- Ten seeds only; model-general CTK-versus-pooling dominance not established.
- Literature audit is deeper but still bounded (section 29): 19 retained notes are full text, four primary sources unavailable, proceedings-level security venues not reliably indexed.
- Independent-dataset replication: the dataset audit (sections 30 to 32) found no publicly verified independent corpus that meets all design requirements; see 35.1.

## 35. Possible Future Extensions and Decision Support [D]

No result exists for any item; none was run. Existing internal robustness is already extensive (families, model classes, supports, operating points, salts, grouping, natural exposure, negative controls), so further internal sensitivities add little; the main unaddressed validity threat is dependence on one corpus.

| Possible next step | Scientific gap addressed | Existing evidence | Literature collision status | Incremental value | Cost | Recommendation |
|---|---|---|---|---|---|---|
| No-new-run publication work (read the remaining primary sources, proceedings-level security-venue sweep, forward citations, per-client and family write-up) | Novelty positioning; interpretation | Complete stored artifacts | Deeper audit done; 0 direct, 4 partial | High per unit cost | Low | Do first |
| Independent Android dataset replication | External validity of the decomposition | Only internal replication (same corpus); no verified suitable public corpus | No prior design found that it would duplicate | Highest if a suitable corpus exists | High (client construction, family labels, per-family support; new fresh-seed protocol) | **OPTIONAL, feasibility-gated** (see 35.1) |
| Exact-effective-dose follow-up | Saturation and dose thresholds; H5 second half | Increase supported; effective exposure far below requested; no plateau | Dose over missing-class peer samples not found in prior work (partial collision with label-count sweeps) | Medium, only if a dose or saturation claim matters | Medium (new experiment, fresh seeds) | OPTIONAL |
| Larger-family feature-novelty study | Why CTK varies by family | rho 0.57 and 0.33 on 7 to 8 families; underpowered | Explanatory analyses not found | Medium | Medium to high (more families per set, predeclared descriptor) | OPTIONAL, only with predeclared descriptor and family count |
| Broader CTK-versus-pooling dominance study | Model-general dominance claim | Dominance for primary MLP controlled only; linear, low support and natural design differ | N1 differentiator unaffected | Low to medium | Medium | LOW VALUE unless a general claim is wanted |
| FedProx-focused confirmation | Deployment recommendation | Descriptive trade-off, paired FedProx-FedAvg CTK +0.018 and known-family +0.026 | Not novel | Low to medium | Medium | OPTIONAL, only if a recommendation is required |
| New federated mechanism | Residual headroom | Headroom below both triggers | Crowded literature (prototype, distillation, missing-class methods) | None demonstrated | High | **Do not pursue** |
| More internal sensitivities | Unspecified | Extensive | none | Low | Medium | **Do not pursue** unless a specific threat is named |
| Additional descriptor searches on the same families | Novelty explanation | Underpowered | none | Low (multiplicity risk) | Low | **Do not pursue** |

### 35.1 Is a second independent Android dataset worth it? Not with current public data

Updated after the direct KronoDroid audit (section 31) and the McNdroid overlap computation (section 32). KronoDroid is MARGINAL: it has families, benign samples and two timestamps, but no market or source axis, so clients would be era windows that confound family with time. McNdroid is not independent (81% of its apps are in LAMDA) and serves only as a representation check. CCCS-CIC-AndMal-2020, MH-1M, AndroTruth and the small legacy corpora fail on the client axis, benign samples or family labels. A poorly matched replication would be less informative than an explicit one-corpus limitation, so the study keeps a single-corpus scope. Re-open only if a corpus with real market or source metadata, benign samples and at least 15 families with several hundred de-duplicated samples at three or more clients appears; any such run needs a new frozen protocol, fresh seeds and class D labelling, and failure to replicate must be reported as readily as success.

## 36. Claims and Allowed Wording

| Claim | Class | Status | Allowed wording |
|---|---|---|---|
| Local absence lowers recall on the hidden family | A | supported | "A locally hidden family is detected less well than under full exposure (local deficit 0.201, CI 0.164 to 0.231)." |
| Collaboration recovers part of the deficit | A/C | supported with qualification | "Recovers most federation-wide but little own-domain (oracle-gap recovery 0.63 versus 0.23)." |
| For the primary MLP with controlled exposure the gain is mostly complementary family knowledge | A | supported | "CTK +0.117 versus pooling +0.014 (primary MLP, controlled exposure, one corpus)." |
| The decomposition is model- and design-general | A/B | **not supported** | Linear, low-support and natural-scarcity designs have pooling shares of about one half or more; state proportions as design-dependent. |
| CTK keeps sign and practical size across populations, models, supports, operating points, splits | B | supported for sign and magnitude | "Persists in sign and practical magnitude", never "identical". |
| Own-domain CTK is not a permutation artifact | A + D | resolved in the extension | "Unresolved in the original seeds (100 to 109); the own-domain permutation control is equivalent to zero in a separately frozen extension with fresh seeds 200 to 209 (EXT-1)." Never pool. |
| Natural scarcity confirms the effect | B | within-dataset only | "Within-dataset natural-exposure validation", never "external validation". |
| Dose saturates | A | **not supported** | "Gain increases with effective peer exposure; saturation was not observed." |
| Feature novelty explains CTK | A | unresolved | "Exploratory association on 7 to 8 families, underpowered." |
| Novel / first | D | **forbidden** | Use the bounded positioning sentence in section 29. |
| Generalizes beyond LAMDA | none | not supported | State the single-corpus limitation. |

The original gate counts (9 promoted, 0 narrowed, 3 rejected, section 25) are unchanged by any class C or D addition.

## 37. Publication Story and Next Actions

### 37.1 Publication-story audit

Candidate story, clause by clause:

| Clause | Verdict | Evidence |
|---|---|---|
| Local absence creates a measurable detection deficit | Supported [A] | Local deficit 0.201 (0.164, 0.231) federation-wide; 0.164 own-domain |
| Collaboration recovers part of it | Supported with qualification [A/C] | Oracle-gap recovery 0.63 federation-wide, only 0.23 own-domain; anzhi's net FedAvg gain is about zero |
| The mechanism depends on what peers contribute | Supported [A] | Pooling versus complementary decomposition |
| Under the primary MLP, pooling explains little and complementary knowledge is dominant | Supported for the primary MLP with controlled exposure, federation-wide [A]; own-domain pooling is negative | Pooling share 0.11 (-0.39, 0.35); CTK share 0.89 (0.65, 1.39) |
| The effect persists under natural scarcity | Supported as **within-dataset** validation [B]; decomposition differs (pooling share 0.47) | CTK 0.113 versus 0.117 |
| ... own-domain, worst-client | Supported with caveats [A, C] | Own-domain permutation control unresolved; worst-client weak at 1% FPR |
| ... model changes, family-set replication, support changes, split sensitivities | Effect sign and practical magnitude supported [B]; proportions not | Linear pooling share 0.66; replication CTK about half the primary; trees centralized only |
| Magnitude is strongly family dependent | Supported [A] | Family spread 0.362; some families near zero or negative |
| Some families remain poorly detected under full exposure, separating exposure from representation limits | Supported and bounded [A] | hiddad, gappusin (and revmob) poor in MLP and another model class; primary set only |

Reviewer-safe version:

> In a controlled-exposure design on one Android corpus, a locally hidden malware family lowers recall on that family. For the primary MLP, collaboration recovers part of this deficit, and most of the federation-wide gain comes from family-specific knowledge held by peers rather than from generic pooling; generic pooling is negligible or negative for the hidden families in own-domain evaluation. The complementary effect keeps its sign and a practical magnitude under naturally scarce exposure (within the same corpus), own-domain and worst-client evaluation, a disjoint family set, linear and tree models, different support and operating points and alternative splits, but the split between pooling and complementary knowledge is model- and design-dependent and the effect size varies strongly across families and clients. Some families stay poorly detected even with full exposure in several model classes, indicating representation limits that exposure alone does not repair. These findings are for one corpus and require independent-dataset replication.

### 37.2 Next actions

1. Report the study as a single-corpus, controlled-exposure decomposition with the class labels A/B/C/D kept visible; keep the extension result in its own paragraph.
2. Obtain the four unavailable primary sources (FedRS, FedLMD, FedCKD, FID-SPA) through a library or the authors before any submission and re-check section 29 against them.
3. Pursue independent-corpus replication only if a corpus meeting the section 35.1 criteria becomes available; otherwise keep the limitation explicit.
4. Do not add federated mechanisms, further internal sensitivities or new descriptor searches; none has a demonstrated value.

## 38. Warnings and Limitations

- Class C analyses are exploratory support and must not be presented as preregistered claims.
- The dose-gate outcome was changed by a bug correction; the original promotion recorded "narrowed". Both outcomes are documented and the change did not use favourable outcomes to choose the fix (an observation-level reading gives the same result).
- CTK is a counterfactual against family-absent pooling; where pooling is negative, CTK overstates the deployment gain (adwo, hiddad, gappusin). Use total gain for deployment statements.
- Micro-pooled and seed-paired estimands differ in magnitude and are labelled `micro_pooled_ctk_gain` and `paired-seed-macro` respectively.
- Selecting the worst client on the local baseline biases total and pooling gains upward.
- Static binary features, four simulated clients, ten seeds, wide BCa intervals; nothing generalizes beyond this representation and dataset without replication.
- PDF figures are not byte-deterministic.
- Natural scarcity is within-dataset validation on the same corpus, not external validation.
- Dose promotion supports an increase with effective exposure; it does not establish saturation.
- Per-client results are descriptive: play-late has 6 contributing seeds and only an exploratory small-n interval; four clients cannot support causal claims.
- The novelty audit is bounded and licenses no priority claim.

- The extension (class D) is a fresh-seed replication of one negative control; it does not change any original gate, seed, threshold or family set.
- Downloaded external datasets are kept outside the repository and `results/`; they are not redistributed.
- The literature audit is bounded: four primary sources were unavailable, several papers were read at targeted depth, and proceedings-level security venues are not reliably indexed.


## 39. Complete Artifact Index

`results/` (promoted, mode confirmatory; digests in `manifest.json`):

- Evidence parquet: `run-index`, `arm-metrics`, `collaboration-decomposition`, `family-rescue`, `peer-dose-response`, `feature-novelty`, `robustness`, `anchored-worst-client`, `anchored-client-selection`, `federated-arm-tradeoff`, `ctk-robustness-synthesis`, `family-mechanism-patterns`, `natural-scarcity-comparison`, `permutation-control-audit`, `mechanism-headroom`, `operating-point-fidelity`, `client-ctk-analysis`.
- Statistics: `paired-effects.parquet`, `cluster-bootstrap.parquet`.
- Gates: `claims.csv`, `seed-status.csv`.
- Tables (CSV, 20): client-ctk-analysis, dataset-client-audit, primary-arm-comparison, collaboration-decomposition, peer-dose-response, family-level, claim-gates, robustness, and the nine class B/C tables above.
- Figures (PDF and PNG, 11): collaboration-decomposition, mean-versus-worst-client, own-domain-versus-federation-wide, peer-dose-response, family-rescue-map, feature-novelty-versus-ctk-gain, known-versus-unseen-tradeoff, ctk-robustness-forest, federated-arm-tradeoff, natural-versus-controlled, client-ctk-analysis.
- Provenance: `code.json`, `protocol.json`, `source-data.json`, `environment.json`.
- Extension (class D, `results/extension/`): run index, paired effects, `permutation-control-audit.csv`, provenance; seeds 200 to 209.
- Additional class C evidence: `ctk-variance-components`, `family-associations`, `family-client-ctk` (parquet and CSV tables).
- Positioning and feasibility (class D): sections 29 to 33 of this document.
- Protocol and decisions: `docs/Roadmap.md` (31.3 post-confirmatory clarifications, 31.4 extension protocol), `docs/decisions/protocol-amendments.md`, `docs/decisions/implementation-decisions.md`.
