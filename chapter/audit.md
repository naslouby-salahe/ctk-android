# CTK-Android publication-readiness audit

Audit date: 2026-10-20. Manuscript: `chapter/CTK-Android_Chapter.docx` (SHA-256 `b54193843b08a63bc2328c5a7affa98fc3a8f44f13e059dc16631d4119e972c2`). Repository HEAD: `6813f929968f141d3660ccfa28d37aaa0180d74f` (branch `paper`, 2026-10-12, "Progress Chapter"). Evidence revision recorded in `results/provenance/code.json`: `f6302f7906824945731dadbbeb44357f3d025aaf`. The blob of `src/ctk_android/analysis/statistics.py` is identical at that revision and at HEAD (`6c52c17640ab1dd71d19e74a9e9499e72557333e`). `git diff --stat` between those revisions is empty for `src/` and `configs/`.

**Revision history of this report.** Pass 1 (2026-10-20, earlier session) produced findings CTK-AUDIT-001 to 020. Pass 2 (2026-10-20, this session) re-ran the audit idempotently against the same manuscript hash and HEAD. Pass 2 kept every pass-1 identifier, re-verified the pass-1 numbers independently, closed CTK-AUDIT-012, withdrew CTK-AUDIT-016, revised CTK-AUDIT-002, 009, and 014 with new evidence, and added CTK-AUDIT-021 to 033; pass 3 added CTK-AUDIT-034. Pass-1 conclusions were not accepted on trust: each one cited below was either recomputed in pass 2 or is marked as carried forward. `chapter/verification.md` was not used as evidence.

**What pass 2 added that pass 1 could not.** (1) All extension BCa intervals (dose, placebo, robust aggregation) were re-bootstrapped from seed-level CSVs and reproduce the stored endpoints to five decimals. (2) The 16-attempt partition selection was re-executed in memory for seeds 100–109; the chosen attempt matches the stored manifest in 10/10 seeds, and the selection margin is now quantified. (3) The confirmatory configuration was diffed against the protocol-freeze commit `e079972` (2026-09-24 19:42 UTC); no confirmatory parameter changed. (4) The unit, architecture, and integration tests were executed in an isolated scratch copy: 476 passed, 14 skipped for absent raw data or outputs, 0 failed. (5) Full texts of AndroZoo (Allix 2016) and Ciaramella et al. (2026, CC BY version of record) were obtained and read. (6) The authors' own internal literature matrix (`docs/Research Evidence.md` §29) was read; it names closer neighbours than the chapter cites. (7) The sample-weighted (micro) CTK and the CTK on genuinely new expanded families were computed from existing artifacts.

**What pass 3 added (2026-10-20, same session, at the user's request).** (1) Every item pass 2 left unconfirmed was pursued; Section N lists the outcome of each. (2) The freeze is now proven mechanically: run fingerprints computed from the freeze commit equal the stored resolved configurations of all 140 confirmatory runs, and the hyperparameter selection re-derives from saved development evidence with zero drift (CTK-AUDIT-027). (3) The Spearman intervals, representation effects, client table, original dose supports, and extension permutation were recomputed and match exactly. (4) Twelve further tests passed (source schema against the raw data, and the CLI end-to-end tests that do not train). (5) Two pass-2 errors were corrected: FL-MalDrift is Scientific Reports 16 (2026), not 2025, and Shao et al.'s fifth author is "Wai Shiang, C." (6) One new finding, CTK-AUDIT-034. (7) Section O gives the surgical edit list, with every anchor string verified to occur exactly once. (8) The audit was re-run for idempotence; see Section N.

**Pass 4 (2026-10-20).** Independently recomputed the five headline quantities and their BCa intervals; verified all 215 manifest digests; recomputed all 840 representation target cells from saved scores and all 72 equal-test-FPR effect intervals, exactly matching the stored results; enumerated signed ranks for every zero/tie-containing secondary contrast and added CTK-AUDIT-035 for one unquoted p-value; added optional accessibility finding CTK-AUDIT-036; read Holm in full from a publicly reachable university-hosted scan without adding it to the distributable reference collection; and corrected overstatements in this audit’s own suggested wording. All previous IDs are preserved. Three separate reviewer agents were attempted, but returned service-limit/authentication errors and no findings; the three reviews in Section K remain simulated analytical perspectives, not independently completed agent reports.

The manuscript, source, configurations, and result files were not modified. No training was rerun. No commit was made.

The twelve questions in objective §28 are answered in their exact wording in Section A and developed in Sections B–M. Section O lists the exact edits.

## A. Executive Assessment

CTK-Android is a careful offline evaluation study. Its defensible contribution is a matched-budget, three-arm decomposition of Android unseen-family recall: local learning, collaborative learning with the selected families absent from every client, and collaborative learning with each selected family removed only from its assigned target. The primary FedAvg contrast at a nominal 5% false-positive rate (FPR) is large, positive in all ten confirmatory seeds, and independently recomputed from `results/evidence/arm-metrics.parquet`. The chapter already reports the costs that qualify that gain: a small and uncertain pooling term, a much smaller own-domain net gain, a known-family recall loss, family heterogeneity, and aggregate AUROC and average-precision declines.

**Publication-readiness score: 7.7 / 10.** This is a criteria score for the manuscript as it stands. It is not an acceptance probability. Pass 1 gave 7.8. Pass 2 found stronger numerical and provenance support, but also closer uncited prior work and two unreported weightings that a reviewer can compute from the public repository.

| Criterion | Score | Basis |
|---|---|---|
| Numerical traceability of the seeds-100–109 confirmatory claims | 9.5 | All five headline figures, their BCa intervals, exact Wilcoxon p-values, Holm adjustment, and positive-seed counts were recomputed independently in pass 2 with SciPy, without importing the project's statistics module. Extension intervals were also re-bootstrapped and match. |
| Design disclosure | 8.0 | Budgets, calibration, grouping, the 16-attempt selection, the schedule difference, and the multi-family exclusion rule match the code. Figure 1 does not show the multi-family exclusion (CTK-AUDIT-029). |
| Novelty precision | 6.5 | CyberForce, CELEST, and Ciaramella are described accurately. The authors' own literature matrix lists FLEKD-IDS (Shen et al., ICC 2024) and Shao et al. (IEICE 2026) as partial collisions, and neither is cited; two Android FL detectors (LiM, FL-MalDrift) are also absent (CTK-AUDIT-009). |
| Statistical modesty and negative results | 8.5 | Thresholds, Holm scope, and unfavourable results are reported. Two existing quantities that qualify the headline magnitude are not: the sample-weighted CTK of 6.58 points (CTK-AUDIT-021) and the 3.47-point CTK on the 18 never-before-studied expanded families (CTK-AUDIT-022). |
| Reproducibility and citation completeness | 8.0 | Manifest 90/90, frozen configs unchanged since the freeze commit, tests pass, all 14 cited works read in full; 13 have retained PDFs. The freeze commits are unreachable from any branch and repository documents describe superseded campaigns (CTK-AUDIT-026, 027). |
| Presentation and venue compliance | 7.0 | Figures and tables match the artifacts. IGI requires an AI-use statement above the references when AI assisted writing or analysis (CTK-AUDIT-028), and the review copy carries an identifying URL (CTK-AUDIT-006). |

**Strength of the central contribution.** High within its stated scope: an evaluation-design and empirical result about complementary family exposure, using FedAvg and FedProx, not a new optimizer, privacy accountant, or poisoning defense. The equations in the manuscript are `CTK(m) = R(m, P) − R(m, A)`, `Pooling(m) = R(m, A) − R(L, P)`, and `Total(m) = R(m, P) − R(L, P) = CTK(m) + Pooling(m)`. The identity holds exactly on the recomputed seed differences (maximum absolute residual 0).

**Strongest verified positive results.**

- FedAvg federation-wide unseen-family recall, seeds 100–109, nominal 5% FPR: CTK mean `0.1195575610` (+11.96 percentage points), BCa 95% interval `[0.0915477400, 0.1520988052]` (9.15 to 15.21), exact two-sided Wilcoxon `p = 0.001953125`, Holm-adjusted `p = 0.005859375`, 10/10 seeds positive, no zero differences and no absolute-rank ties.
- Total federation-wide gain `0.1346088107` (+13.46 points), interval 8.82 to 17.04, Holm `p = 0.00586`, 10/10 positive.
- CTK is positive in 10/10 confirmatory seeds for every collaborative learner, not only FedAvg: central 13.10, FedProx 13.20, fine-tuned FedAvg 8.20, blend 7.60 points (pass-2 recomputation; not stated in the chapter; CTK-AUDIT-025).
- The headline is stable across executions. The repository documents two earlier full executions of the same configuration fingerprint that gave FedAvg CTK +0.117 both times; the final deterministic campaign gives +0.1196 (CTK-AUDIT-026).
- Wrong-family placebo contrast, extension seeds: CTK minus placebo +10.04 points, interval 8.35 to 12.28, 10/10 positive; re-bootstrapped in pass 2 to the same endpoints. Class D.
- Exact peer dose, pooled family sets, FedAvg, federation-wide, 5% FPR: 2.92, 4.90, 7.83, 12.48, and 14.49 points at 10, 25, 50, 100, and 200 examples, each positive in 10/10 extension seeds. In the primary family set the 100-to-200 increment is still +4.23 points (2.53 to 6.55), so the dose response there has not flattened (CTK-AUDIT-023).

**Main publication risks.**

1. Closest prior work is uncited: FLEKD-IDS and Shao et al. (2026), which the authors' own audit classifies as partial collisions, plus LiM and FL-MalDrift (CTK-AUDIT-009).
2. The 11.96-point headline is client-macro on the support-ranked primary families. A reviewer with the repository can compute a 6.58-point sample-weighted CTK and a 3.47-point CTK on new expanded families. Both are positive in 10/10 seeds, but reporting them would make the magnitude’s dependence on weighting and family choice easier to assess; no inference about selective intent is warranted (CTK-AUDIT-021, 022).
3. IGI procedural items: the identifying GitHub URL under double-anonymized review (CTK-AUDIT-006) and the AI-use disclosure and AI-reference rules (CTK-AUDIT-028).
4. The abstract's shorthand for CTK is narrower than Figure 1's intervention; the placebo is the cleaner specificity contrast (CTK-AUDIT-002, 010, 029).

**Readiness classification.** Scientifically strong enough to submit after a targeted textual revision. No critical numerical correction and no new training experiment is required. The two weighting analyses in CTK-AUDIT-021 and 022 need no training; they are already computed in Section J.

**Highest-impact improvements.** (1) Cite FLEKD-IDS, Shao et al., LiM, and FL-MalDrift with the paragraph in CTK-AUDIT-009. (2) Report the sample-weighted CTK and the new-family CTK next to the headline, framed as evidence that the sign generalizes while the magnitude depends on weighting and family set. (3) Add the AI-use statement if applicable and remove the identifying URL from the review copy. (4) Point the 11.96-point sentence back to Figure 1 and to the placebo, and annotate Figure 1 for the multi-family exclusion.

### Answers to the twelve questions in objective §28

1. **What is already scientifically strong about CTK-Android?** The matched-budget three-arm design; a primary contrast that is positive in all ten seeds for each of the five collaborative learners and each of the three alternative partition salts, positive on average in every Table 5 sensitivity (the disjoint replication set is positive in 8/10 seeds), and stable across the three recorded executions; dose and placebo extensions whose intervals reproduce; a confirmatory configuration that is verifiably unchanged since its freeze commit; and an honest record of unfavourable results. See Section B.
2. **Are all principal results correct and reproducible?** Correct: yes. Every headline and secondary number checked in pass 2 matches the chapter after rounding. Reproducible from artifacts: yes. Reproducible from raw data: not re-executed; the pipeline is documented as deterministic and the tests pass. See Section J.
3. **Is the claimed novelty defensible against the closest prior work?** Yes for the matched-budget decomposition. No read paper, including the four partial collisions in the authors' own matrix, pairs a volume-matched absent-everywhere arm with peer-present and local arms. The chapter must cite those neighbours to make that claim credible (CTK-AUDIT-009).
4. **Do the citations accurately represent the original publications?** Yes for all 14 cited works read in full, including Holm in pass 4. Holm (1979) was read from an institution-hosted scan in pass 4; permission to redistribute that scan was not established. Several works were read as preprints or deposited manuscripts rather than the version of record; Section H identifies each version. See Section H.
5. **Are there any genuine methodological, statistical, or implementation problems?** No critical error affects the chapter’s principal conclusions. One unquoted secondary p-value uses a tie-inappropriate exact calculation (CTK-AUDIT-035); its sign and significance conclusion do not change. The principal code paths match the chapter. The substantive manuscript issues are reporting choices: an unreported weighting (CTK-AUDIT-021), an unquantified family-set dependence (022), and a dose summary that hides set heterogeneity (023).
6. **Are important positive results insufficiently emphasized?** Yes: the placebo, the dose pattern, CTK for every learner (025), stability across executions (026), and the fact that the sign survives sample weighting and new families (021, 022).
7. **Are limitations being interpreted proportionately?** Mostly. Several qualifications repeat (018–020), while two quantitative qualifiers are missing (021, 022). The fix is to swap repeated prose for those two numbers, not to add more caveats.
8. **Which sentences or paragraphs should be improved?** Section O lists 29 surgical actions (S-01 to S-29) keyed to paragraph numbers, with merged text where several findings touch one paragraph.
9. **Which reviewer objections are most likely and how can they be answered?** Missing neighbours; "this is just FedAvg"; magnitude depends on hand-picked families and weighting; multi-family composition; ten seeds; support-based partition selection; no privacy or poisoning test. Responses are in Sections K and M.
10. **Which additional analyses, if any, would materially strengthen the research?** Three existing-data analyses, all completed in this audit: leave-one-seed-out (015), sample-weighted CTK (021), and new-family CTK (022). No new training is needed.
11. **What should be corrected before submission?** Section O Tier 1 (S-01 to S-10): CTK-AUDIT-009, 021, 022, 028, 002, 010, 032 and, for IGI review, 006.
12. **What is optional and should not delay publication?** More seeds, a chronological split, a poisoning study, a privacy accountant, an external corpus, and the repository housekeeping in CTK-AUDIT-026 and 027.

## B. Verified Scientific Strengths

**The estimand is defined and implemented consistently.** `analysis/decomposition.py` `decompose()` builds CTK, pooling, and total for central and FedAvg. Within a paired seed the three quantities satisfy the displayed identity. Local recall in the pooling term is the local learner under the peer-present family definition, matching `Pooling(m) = R(m, A) − R(L, P)`. The chapter says so.

**The primary contrast is large and not a one-seed artifact.** Seed-level FedAvg federation-wide CTK differences, seeds 100–109, in percentage points, are 19.99, 13.22, 14.66, 7.31, 9.33, 18.65, 8.85, 6.47, 15.39, and 5.69. The smallest is about +5.69 points. Leave-one-seed-out means of these ten values span 11.06 to 12.65 points. Every such mean stays above the chapter's three-point practical threshold. This calculation uses only the already recomputed seed effects. It was not in the manuscript.

**The exposure rule matches Figure 1.** `experiment/design.py` `_excluded_families` removes every selected family from every client when the condition is family-absent-everywhere, and removes only each target's assigned family from that target when the condition is peer-present. `select_training` then drops excluded rows and caps the kept order at the matched budget. The chapter's Figure 1 paragraph states both rules. Sample-count weighting is `training[client].size` in `experiment/training.py` `train_federated`, normalized in `models.py` `average_states`.

**FedProx matches the cited objective shape.** `models.py` `fit_epochs` adds `0.5 * proximal.strength * ||w − w_anchor||^2` to mean binary cross-entropy with logits. The anchor is the round-start global state. Mu is 0.1 in the frozen confirmatory configuration. A new Adam optimizer is created on every local `fit_epochs` call, so optimizer state is not carried across rounds. The chapter states both facts.

**Calibration matches the stated rule.** `evaluation.py` `calibrate` sets the threshold at `np.quantile(benign_scores, 1 - alpha, method="higher")`. The operating point is marked insufficient when `benign_count * alpha < 10`. Realized FPR is evaluated on held-out benign test scores. Primary mean realized FPRs are 4.99% (local), 5.04% (absent), 5.09% (peer), and 5.04% (full exposure). The chapter also reports the peer-present worst-client FPR mean of 6.60% and the maximum of 9.89%.

**Negative and mixed results are real and are reported.** Own-domain FedAvg pooling is −7.60 points with an interval entirely below zero. Known-family FedAvg change is −3.61 points, 0/10 seeds positive. AUROC and average precision fall by 0.01166 and 0.02011. Replication families dnotua and zdtad have negative mean CTK. Report-JSON full-exposure recall is −14.54 points relative to aligned LAMDA. Five expanded-family point estimates are negative, including feiwo and baiduprotect, as the chapter says. These qualify the contribution. They do not reverse the federation-wide CTK result.

**Specificity controls do what the chapter claims.** On confirmatory seeds, family permutation drives FedAvg federation-wide CTK to +0.30 points, interval −0.36 to +1.02. On extension seeds 200–209, the stored audit row is −0.21 points federation-wide and −0.07 own-domain, both inside ±3 points. The wrong-family placebo is about −0.54 points, while CTK minus placebo is +10.04 points, 10/10. Exact dose is positive at every tested count and rises with dose. Dose zero minus absent is exactly 0 in the checked rows.

**Leakage controls that were checked are implemented, not merely described.** Identity grouping uses package or identical binary feature vector, connected components, and one role across clients. The 16 partition attempts in `data/partitions.py` `build_partition` keep the assignment with the largest count of eligible controlled plus natural-scarcity pairs. The score is support eligibility, not test recall. Feature discovery is not repeated inside the split: the study uses the frozen 925-column `var_thresh_0.01` matrix. Representation transformations for graph and report inputs are fit on the arm's fit rows. The aligned McNdroid overlap is 554,136 rows (170,256 malware and 383,880 benign), with widths 925, 2,390, 2,793, and 17,483 (`outputs/preprocessing/representation/overlap-manifest.json`). Primary family names in `outputs/preprocessing/families/primary-family-set.json` are dowgin, airpush, gappusin, adwo, leadbolt, revmob, frmy, and hiddad. The chapter correctly says eight candidates and seven eligible controlled families. The replication file has eight names: kuguo, dnotua, smsreg, inmobi, youmi, zdtad, domob, and utchi.

**Representation failure labels are correctly mapped.** `configs/experiments.yaml` sets representation-r0 to lamda-static, r1 to mcndroid-static, r2 to call-graph, and r3 to report-json. `diagnostic-fpr-exceptions.csv` contains exact-dose seed 317, representation-r0 seed 333, representation-r1 seed 333, and representation-r2 seed 334. The anzhi central peer-present call-graph client FPR on that last row is `0.153211` (15.32%). The chapter's four failure combinations match these rows.

**Class labels match the seed blocks in `configs/project.yaml`.** Confirmatory seeds 100–109 carry the original controlled-exposure analysis and the prespecified sensitivities. Permutation extension seeds are 200–209. Large-family seeds are 300–309. Exact dose is 310–319. Placebo and robust aggregation are 320–329. Representation seeds are 330–339. The chapter's A/B/C/D usage matches that provenance. The replication family set is a prespecified disjoint set on seeds 100–109 and is appropriately Class A. Extension analyses are not promoted to confirmatory discoveries in the prose.

**Corpus arithmetic matches Table 1.** Client counts 104,287 + 88,282 + 319,122 + 320,474 = 832,165. Malware 90,801 + 73,578 + 75,985 + 17,200 = 257,564. Benign 13,486 + 14,704 + 243,137 + 303,274 = 574,601. Malware shares 87.07%, 83.34%, 23.81%, and 5.37% match `results/tables/dataset-client-audit.csv`.

**Figures communicate the claimed numbers.** Figure 1 matches the exclusion code. Figure 2 prints 1.51 [−4.15, 6.10], 11.96 [9.15, 15.21], and 13.46 [8.82, 17.04]. Figure 3's means and worst-client markers match Table 4 (local 50.90/28.92, central 66.07/41.42, FedAvg 64.36/43.79, FedProx 64.55/37.90, fine-tune 62.16/40.35, blend 63.66/37.63). Figure 4's two-decimal proportions are the family-level recalls rounded from `family-level.csv`. Figure 5's FedAvg means match `exact-dose-effects.csv`, and the central series on the same figure matches that file at 4.12, 6.86, 10.74, 13.34, and 17.95 points. All five figures are readable in grayscale.

**Privacy and robust aggregation are not over-claimed.** The discussion states that there is no privacy accountant and that trimmed-mean and median aggregation are not a poisoning evaluation. `models.py` `_robust` uses `stack.median(dim=0)`, which in PyTorch returns the lower of the two middle values when the stack length is even. With four clients that is the chapter's "lower middle" median. This behavior was checked against the code and the PyTorch definition, not by re-executing training.

**The confirmatory artifact manifest is intact.** `results/manifest.json` lists 90 files. All 90 digests matched a fresh SHA-256 read on 2026-10-20.

**The confirmatory protocol is verifiably unchanged since its freeze (pass 2).** `docs/decisions/protocol-amendments.md` records the Stage F freeze at commit `e079972` (2026-09-24 19:42:42 UTC), before any confirmatory seed ran. That commit still exists in the local object store. `git diff e079972 HEAD -- configs/` shows only additions (extension seed blocks, the `dose` eligibility profile, extension experiments and their parameters) and the removal of the automated gate thresholds. Seeds 100–109, the primary/low/high eligibility profiles, budgets, the MLP, optimizer and schedule settings, FedProx mu, fine-tuning epochs, alphas, the 9,999 BCa resamples, statistics seed 20260924, and the 3-point and 2-point practical thresholds are byte-identical. The core exposure functions `_excluded_families`, `select_training`, `training_orders` and `calibrate` are textually identical between the freeze revision and the evidence revision `f6302f7`, although the surrounding modules were refactored. The chapter's sentence "Hyperparameters and statistical procedures were frozen before the confirmatory evaluation" is therefore supported for every confirmatory quantity the chapter reports. The development-grid selection rule used calibration-partition AUROC on development seeds 1–5, not test rows (same file, 2026-09-24 entry).

**The partition selection is reproducible and its margin is modest (pass 2).** Re-executing `assign_roles` and `evaluate_partition` in memory for all 16 attempts of seeds 100–109 reproduces the stored winning attempt in 10/10 seeds (`outputs/preprocessing/partitions/seed-1xx/manifest.json`: attempts 14, 7, 6, 1, 5, 9, 14, 2, 3, 0). The winning attempt has 57–60 eligible controlled-plus-natural pairs. The median attempt has 52.5–56 and the worst has 48–52. On average the chosen partition has 8.6% more eligible pairs than the median attempt (59.1 versus 54.45). Every one of the 160 candidate partitions had at least 48 eligible pairs. The selection therefore increases support modestly; it does not pick a rare partition, and it uses no prediction.

**The test suite passes (pass 2).** In an isolated scratch copy of `src/`, `tests/`, `configs/` and `.git` (with `PYTHONPATH` pointed at the copy and bytecode writing disabled), `pytest tests/unit tests/architecture tests/integration` gave 472 passed and 14 skipped; the one failure (`test_pyright_strict_passes`) disappeared when the copy could see the project virtual environment, giving 4/4 static-analysis passes. The 14 skips need raw data, development runs, or preprocessing outputs that were not linked into the copy. `tests/e2e` was not run. Unit tests cover the target-only and absent-everywhere exclusion rules, matched training sizes, dose-zero equivalence, nested dose draws, trimmed-mean and lower-median aggregation, FedProx anchoring, role assignment without splitting groups, and train-only transform fitting. No unit test calls `average_states` or `build_partition` directly; pass 2 checked the first by reading the code and the second by re-execution.

**The exposure manipulation is substantial but bounded (pass 2).** In seeds 100–109, FedAvg peer-present fit samples contain on average 2,073 rows of selected families across the four clients (8.6% of 24,000 fit rows); the absent-everywhere arm contains none and refills those rows from the seeded order. Per client the swapped rows average 1,244.8 at Anzhi (20.7% of 6,000), 620.3 at AppChina, 182.8 at play-early, and 25.4 at play-late. Run validations confirm, for every arm, zero hidden-family rows at the target, matched training sizes `[6000, 6000, 6000, 6000]`, fit-role-only training, and benign-calibration-only thresholds (`outputs/runs/confirmatory/controlled-exposure/seed-100/validation.json`).

## C. Critical Findings

No critical finding. No recomputed confirmatory headline number disagrees with the manuscript. No cited experimental claim was found to be invented. No result file required by the headline chain is missing. Inaccessible papers are recorded in Section H and are not treated as reviewed.

## D. Major Findings

**ID:** CTK-AUDIT-006

**Severity:** Major

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Reproducibility paragraph containing `https://github.com/naslouby-salahe/ctk-android`. Venue constraint: IGI Global call `https://www.igi-global.com/publish/call-for-papers/call-details/10325`, "Advances in Mobile Application Privacy and Security," editors Mohamed Lachgar and Omar Achbarou, checked in earlier passes on 2026-10-20; the call URL could not be fetched in pass 4, while the general contributor guide was accessible and independently confirms double-anonymized review. Proposals are due 24 October 2026. Full chapters of at least 10,000 words, including references, are due 16 January 2027. Review is double-anonymized. A pass-4 whitespace count over body paragraphs, table cells, and equation text gives approximately 11,800 words, comfortably above that floor; this is not Microsoft Word’s own counter. The 1,000–2,000-word proposal is a different document. Do not shorten this chapter to proposal length.

**Observed issue:** The repository URL contains the author name. That identifies the author in a double-anonymized review.

**Evidence:** The sentence is in the extracted chapter paragraph that begins "The associated CTK-Android repository contains the source code." The IGI call page says "All submitted chapters will be reviewed on a double-anonymized review basis."

**Why it matters:** For this venue, an identifying URL is a procedural defect before review begins. It is not a scientific defect, and it is not a rule of every journal. A camera-ready or named-author submission can keep the URL.

**Recommended correction:** In the review file only, replace the URL sentence with an anonymized availability statement. Restore the URL in the camera-ready file. Do not delete the provenance revision hash; it does not by itself name the author.

**Suggested replacement:** "The accompanying repository contains the source code, configurations, machine-readable results, and provenance records. The review copy omits the repository URL. The evidence package records execution and analysis revision f6302f7906824945731dadbbeb44357f3d025aaf, with matching revisions and clean analysis sources."

**Implementation requirement:** Text only

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-009

**Severity:** Major

**Confidence:** Confirmed

**Category:** Literature

**Location:** Related-work paragraphs on Ciaramella, CELEST, and CyberForce (paragraphs beginning "Recent Android-specific research addresses related but distinct questions", "The broader security literature already contains explicit examples", and "CyberForce provides an especially close conceptual comparison"); the synthesis paragraph beginning "Prior work establishes that collaboration can help detect threats missing locally"; and the external-validity paragraph that says grouped random partitions are not forward-in-time evaluation.

**Observed issue (revised in pass 2).** The chapter cites two missing-threat neighbours (CELEST, CyberForce). The authors' own literature matrix (`docs/Research Evidence.md` §29.2–29.3, 41 rows, final counts 0 DIRECT, 4 PARTIAL) names four partial collisions: CyberForce, CELEST, FLEKD-IDS, and Shao et al. (borderline). The chapter omits the latter two. It also omits the two Android federated detectors pass 1 identified (LiM, FL-MalDrift) and the most-cited "zero-day" federated paper that omits a class per partition (Popoola et al.). A specialist reviewer who knows any of these will read the synthesis sentence "Prior work establishes that collaboration can help detect threats missing locally" as resting on two citations when five or more exist. The novelty claim itself survives: none of these papers pairs a volume-matched absent-everywhere arm with peer-present and local arms.

**Evidence.** Each full text below was read in pass 1 or pass 2 and is saved in `chapter/references_pdf/`.

- Shen, Yang, Chu, Fan, Niyato, and Lam, "Effective Intrusion Detection in Heterogeneous Internet-of-Things Networks via Ensemble Knowledge Distillation-Based Federated Learning," ICC 2024, pp. 2034–2039, DOI `10.1109/ICC51166.2024.10622262` (Crossref). Local file is arXiv:2401.11968v1. Table IV ("Drop Label 0" to "Drop Label 6") removes one CICIDS2019 attack class from each of seven clients; the text says "all clients failed to detect the lacking attack," while the federated models detect it (UDPLag reaches 80.86% with FLEKD). This is a multiclass task in which a local model cannot emit the dropped label, so local recall on the dropped class is zero by construction. There is no absent-everywhere arm, no volume matching, and no seed-level inference.
- Shao, Otani, Yamakawa, Hirasuka, and Wai Shiang (resolved in pass 3: IEICE prints family names in capitals, and the byline is "Cheah WAI SHIANG"; the author's ORCID record 0000-0002-1647-6703 lists given name "Cheah" and family name "Wai Shiang"; Crossref's split "Cheah WAI" / "SHIANG" is a deposit artefact; APA form "Wai Shiang, C."), "Objective Mismatch in Federated Learning under Missing Class Support," IEICE Trans. Fundamentals, DOI `10.1587/transfun.2026EAP1060`, J-STAGE advance publication 2026-06-05. Withholds all fall windows from ⌈Kρ⌉ of 23 SisFall clients, ρ ∈ {0, 0.2, …, 0.8}, five seeds; proves that missing class support induces a bias that longer training cannot remove. The whole positive class is withheld, not a family inside it, and there is no absent-everywhere control.
- Popoola, Ande, Adebisi, Gui, Hammoudeh, and Jogunola, "Federated Deep Learning for Zero-Day Botnet Attack Detection in IoT-Edge Devices," IEEE IoT Journal 9(5), 3930–3944, 2022, DOI `10.1109/JIOT.2021.3100755`. Accepted manuscript from the Manchester Metropolitan University repository. One traffic class is omitted from each edge device; the paper reports that FDL outperforms centralized, localized, and distributed DL. The authors' matrix notes that its localized comparison reports aggregate metrics, not the omitted class.
- Gálvez, Moonsamy, and Diaz (2021), LiM, PoPETs 2021(4):96–116, DOI `10.2478/popets-2021-0062`: federated Android malware classification with poisoning and inference analyses; no exposure arms.
- Patel, Tomar, Pateriya, and Haripriya, FL-MalDrift, Scientific Reports 16, article 1821 (2026; the PDF prints "(2026) 16:1821"; Crossref's issued date is 2025-12-15, and pass 2 wrongly wrote 2025), DOI `10.1038/s41598-025-31592-z`: drift-aware FedAvg and FedSGD with Drebin, CICMalDroid 2020, and a chronological AndroZoo split; no recall decomposition.
- Optional, Android-specific: Bi, Li, Feng, and Mi (arXiv:2404.05130, 2024) assign k of 133 Drebin families per client and report that "there is no obvious pattern observed for the model performance" as k shrinks, using aggregate metrics only. This is the cleanest published example of the chapter's point that aggregate Android FL metrics can hide family exposure.

**Why it matters.** The two papers in the chapter make CTK-Android look like the third study of its kind. The full set shows a crowded "local versus federated on a missing class" literature and an empty "matched-budget decomposition" cell. Citing the crowded part makes the empty cell visible. Omitting it invites the objection that the novelty paragraph was written without a search.

**Recommended correction.** Insert one paragraph after the CyberForce paragraph, and one clause in the external-validity paragraph. Keep each description to what the cited PDF shows. Do not say that any of these papers "ignores" missing classes. IGI asks authors not to use AI to add or format references (CTK-AUDIT-028), so the author should check each entry against the PDF and type the reference personally.

**Suggested replacement (new paragraph after the CyberForce paragraph).** "Missing classes also appear in federated intrusion detection. Shen et al. (2024) remove one attack class from each of seven clients; the local models fail to detect the removed class, while the federated models detect it. Popoola et al. (2022) omit one botnet traffic class from each edge device and compare federated, centralized, and localized learning. Shao et al. (2026) withhold the positive class from a growing fraction of clients and show that the resulting bias on that class persists even when training appears to converge. In Android malware detection, Gálvez, Moonsamy, and Diaz (2021) and Patel et al. (2026) compare federated and local or drift-aware detection, and Bi et al. (2024) report that aggregate metrics change little as the number of families per client shrinks. These studies establish that collaboration can recover a class a client lacks. None of them removes the selected classes from every client under the same training budget, so none separates generic pooling from complementary exposure."

**Suggested replacement (external-validity clause).** After "Grouped random partitions and chronological partitions answer different questions": "Patel et al. (2026) evaluate a chronological AndroZoo split for federated detection; the present grouped partitions do not answer that deployment-time question."

**Implementation requirement:** Text only

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-021

**Severity:** Major

**Confidence:** Confirmed

**Category:** Statistical

**Location:** Paragraph beginning "Family-macro unseen recall averages the recall of the eligible target-family entries" (defines micro-pooled recall) and the secondary-population paragraph beginning "Family-macro CTK is 12.44 points".

**Observed issue.** The chapter defines micro-pooled recall ("divides pooled hits by pooled trials and weights entries according to support") and says weighting "can change the reported mean," but it never reports the micro-pooled CTK. That value is stored as metric `micro-unseen-recall` in `results/evidence/arm-metrics.parquet` and is roughly half the headline.

**Evidence.** Pass-2 recomputation, controlled-exposure, salt 0, alpha 0.05, FedAvg, seeds 100–109, SciPy BCa with 9,999 resamples and seed 20260924, exact Wilcoxon:

| Metric | Local | Absent | Peer | CTK (CI), positive seeds | Pooling (CI) | Total (CI) |
|---|---|---|---|---|---|---|
| Client-macro (headline) | 50.90 | 52.41 | 64.36 | 11.96 (9.15, 15.21), 10/10 | 1.51 (−4.15, 6.10) | 13.46 (8.82, 17.04) |
| Family-macro | 45.43 | 43.57 | 56.00 | 12.44 (10.09, 15.55), 10/10 | −1.87 (−6.41, 2.58), 4/10 | 10.57 (6.63, 14.20) |
| Micro-pooled (sample-weighted) | 56.57 | 60.57 | 67.15 | **6.58 (4.64, 8.65), 10/10**, p = 0.00195 | 4.00 (−2.04, 11.78), 6/10 | 10.58 (4.49, 18.11), 8/10 |

`experiment/evaluation.py` `summarize` computes micro recall as `hits.sum() / trials.sum()` over federation-wide target-family entries. Dowgin, whose CTK is 0.14 points, supplies 47.0% of all federation-wide hidden-family test trials across the ten seeds (59,107 of 125,825; `outputs/runs/confirmatory/controlled-exposure/seed-1xx/metrics/families.parquet`). Recomputing micro CTK without dowgin gives 12.24 points; without airpush (19.2% of trials) it gives 6.01. The gap between the weightings is therefore almost entirely one large, non-responsive family.

**Why it matters.** This is good evidence that is being left on the table. Under the weighting most practitioners would compute first, CTK is still positive in every seed and its interval lies entirely above the 3-point practical threshold. It is also the number a sceptical reviewer will compute from the repository. Finding it unreported, next to a definition of it, looks like weighting selection, even though the client-macro estimand was prespecified. Under micro weighting the CTK share of the total falls from about 89% to about 62%, which still supports "most of the total benefit" but should be visible.

**Recommended correction.** Add one sentence to the secondary-population paragraph. Keep client-macro as the prespecified headline.

**Suggested replacement.** After "…total gain of 14.88 points.": "Weighting each hidden-family test application equally instead of each client gives a smaller but still uniformly positive estimate: micro-pooled CTK is 6.58 points (interval 4.64–8.65, positive in all ten seeds), with pooling 4.00 points and total gain 10.58 points. Dowgin, which supplies almost half of the hidden-family test applications and shows almost no complementary gain, accounts for most of the difference: without it, the micro-pooled estimate is 12.24 points."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-022

**Severity:** Major

**Confidence:** Confirmed

**Category:** Scientific

**Location:** Paragraph beginning "The 32-family extension asks whether a distance-based novelty descriptor helps explain transfer variation"; paragraph beginning "Eligibility stability materially weakens that association" (sentence "The expanded set also overlaps previously studied families"); Table 5 row "Disjoint family set"; Discussion paragraph beginning "Generic pooling and complementary exposure are different".

**Observed issue.** The chapter says the expanded set "overlaps previously studied families" but does not say how much, and it does not report CTK on the families that are new. Fourteen of the 32 expanded families are primary or replication families (adwo, airpush, dnotua, domob, dowgin, gappusin, hiddad, inmobi, kuguo, leadbolt, revmob, smsreg, utchi, youmi). On the 18 new families, mean CTK is about one third of the overlapping families' value. Together with the replication set (5.08 points), this shows a consistent pattern: the sign generalizes, and the magnitude falls outside the support-ranked primary set.

**Evidence.** Pass-2 computation from `results/extension-b/large-family-ctk.csv` and `large-family-seed-ctk.csv` (FedAvg, seeds 300–309). This is a post hoc split of Class D data and is Class C-like descriptive evidence.

| Subset | Families | Family-level mean CTK | Seed-level family-macro CTK (BCa), positive seeds | Families with CTK ≥ 3 points |
|---|---|---|---|---|
| All 32 (chapter: 6.51) | 32 | 6.51 | — | 20 positive ≥ 3; 3 negative ≤ −3 |
| Overlapping with primary or replication sets | 14 | 10.75 | 10.67 (9.25, 12.84), 10/10 | — |
| New to the study | 18 | 3.22 (family bootstrap 0.92–5.55) | **3.47 (2.45, 4.45), 10/10** | 9 of 18 |

All five negative families named in the chapter (admogo, feiwo, baiduprotect, umpay, dnotua) are in the expanded set; four of them are new families.

**Why it matters.** A reviewer's strongest generalization objection is that 11.96 points reflects the seven families chosen by support rank. The chapter already concedes that the primary set is not a random sample. The existing data answer the objection better than the concession does: on fresh seeds and new families, CTK is positive in every seed, but its mean is near the practical threshold. Saying so turns a vulnerability into a calibrated generalization claim. Leaving it out lets a reviewer discover it.

**Interpretive risk.** The new families are lower-support by construction (the primary and replication sets took the 16 most supported eligible families), so support and novelty are confounded. The family-level interval treats families as exchangeable. Neither number is a confirmatory test.

**Recommended correction.** Add two sentences to the expanded-family paragraph and one clause to the discussion.

**Suggested replacement (expanded-family paragraph, after "…not 32 entirely new independent families.").** "Fourteen of the 32 families belong to the primary or replication sets. On the 18 families new to the study, family-macro CTK averages 3.47 points per seed (interval 2.45–4.45) and is positive in all ten fresh seeds, against 10.67 points on the 14 overlapping families. The direction of the exposure effect therefore extends to new families, while its size is closer to the three-point practical threshold than the primary estimate."

**Suggested replacement (discussion, after "…conditional on the chosen learner, families, budget, and population.").** "The replication set (5.08 points) and the newly examined expanded families (3.47 points) show the same direction with smaller magnitudes, so 11.96 points should be read as the effect for the support-ranked primary families rather than for Android families in general."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-028

**Severity:** Major

**Confidence:** Possible (depends on facts only the author knows)

**Category:** Formatting

**Location:** End of the chapter, between the Conclusion and the References heading; the reference list.

**Observed issue.** IGI's contributor page (`https://www.igi-global.com/publish/contributor-resources/before-you-write/`, read 2026-10-20) requires authors who use AI assistance to disclose the tool and its role immediately above References. It also advises authors against using AI to generate, format, add, or replace reference entries. The chapter has no disclosure statement. The repository's technical documentation contains an explicit rule against listing AI agents as authors (`docs/technical_docs.md` §47), which indicates that AI agents were used in the software workflow. This audit is itself AI-generated, and its suggested replacements, if adopted, are AI-assisted writing.

**Evidence.** IGI page above; `docs/technical_docs.md` §47; the absence of any disclosure paragraph in the extracted chapter text.

**Why it matters.** A missing required declaration is a procedural integrity defect that can stop a chapter at the editorial desk, independent of the science. Authorship rules and disclosure rules are different: not listing an AI as an author is correct, and it does not satisfy a disclosure requirement.

**Recommended correction.** The author should decide, from their own knowledge, whether AI tools assisted analysis, code, or writing of this chapter, including any wording adopted from this audit. If so, add the statement above the References heading. Enter and check every new reference from CTK-AUDIT-009 by hand against the PDF. Do not let an AI tool insert or reformat references.

**Suggested replacement (template only; the author must make it true).** "AI Disclosure Statement: The author used [tool name] to [describe tasks, for example support code development, check numerical results against stored artifacts, and suggest edits to wording]. The author reviewed all output, verified all reported numbers against the study artifacts, and entered and checked all references personally. The author takes full responsibility for the content."

**Implementation requirement:** Text only

**Priority:** P1

**Status:** Needs Verification

## E. Minor Findings

**ID:** CTK-AUDIT-001

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Statistical

**Location:** Abstract and Table 3 discussion: "+11.96", "+1.51", and "+13.46".

**Observed issue:** Rounded components sum to 13.47 displayed points. The unrounded means sum exactly: `0.1195575610 + 0.0150512497 = 0.1346088107`.

**Evidence:** Recomputation from `results/evidence/arm-metrics.parquet`, controlled-exposure, salt 0, alpha 0.05, federation-unseen recall, FedAvg, seeds 100–109. The stored `results/statistics/paired-effects.parquet` row matches this recomputation.

**Why it matters:** A reader who adds the two displayed components will see a 0.01-point gap. It is rounding, not an arithmetic error in the total.

**Recommended correction:** Add six words at the first display of the three numbers.

**Suggested replacement:** "The CTK mean is 11.96 percentage points and the pooling mean is 1.51 points. Their unrounded sum is the total of 13.46 points; the displayed components round in opposite directions."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-002

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Scientific

**Location:** Results paragraph beginning "The CTK mean is 11.96 percentage points," read against the Figure 1 paragraph.

**Observed issue (revised in pass 2):** Figure 1's paragraph already states the design fact: peer-present removes each selected family from its assigned target, while absent-everywhere removes all selected families from all clients. The results sentence then calls +11.96 points the gain "from complementary peer exposure" without pointing back to that second change. Under the code, the target's own fit sample also changes, because other selected families remain in it under peer-present and are removed under absent-everywhere. Replacement rows then fill the same budget. The +11.96-point contrast therefore includes own-sample composition, not only the peers' copy of the target family. For FedAvg, whose global model pools every client, the practical meaning is that the contrast adds all selected families' peer copies at once (on average 2,073 of 24,000 fit rows, 8.6%; 1,245 of Anzhi's 6,000 rows), so each target's estimate also contains exposure to the other selected families. Pass 1 described the placebo as keeping the peer-present exclusions; the code shows otherwise, and the correct description makes the placebo a stronger answer than pass 1 said (see Evidence).

**Evidence:** `experiment/design.py` `_excluded_families` and `select_training`. Chapter Figure 1 paragraph: "In the peer-present condition, every selected family is removed from its assigned target's fit data and may remain at other clients. In the family-absent-everywhere condition, all selected hidden families are removed from all clients' fit data." Placebo construction, `experiment/design.py` `_train_placebo`, `choose_placebos`, `placebo_extras`, `substitute`: the placebo sample starts from the absent-everywhere sample (every selected family removed from every client). For each target-family pair, `_counts` takes the number of hidden-family rows that the peer-present sample holds at each non-target client, and the same number of rows of an unselected named family with at least 400 malware rows and the closest peer fit support is substituted into the absent sample at the same clients (reallocated across peers only when a client lacks free rows). The placebo therefore reproduces the peer-present composition change, the same count of named-family malware rows at the same clients, while changing which family those rows belong to. Stored placebo effect (placebo minus absent) −0.54 points, interval −1.36 to 0.20; CTK minus placebo (peer minus placebo) +10.04 points, interval 8.35 to 12.28, 10/10 (`results/extension-b/controls-effects.csv`; re-bootstrapped in pass 2 to the same endpoints). That contrast is Class D.

**Why it matters:** The design is disclosed. The risk is that the abstract's shorthand is read as a narrower estimand than Figure 1. One sentence closes that reading. The placebo should be named there because it holds the composition change fixed and varies only family identity. It does not replace the confirmatory 11.96-point result, and it is matched on counts and support, not on every behavioural property, as the chapter already says.

**Recommended correction:** After the sentence that reports 11.96 points, add the replacement below. Do not delete the known-family or own-domain qualifications.

**Suggested replacement:** "As Figure 1 states, the absent-everywhere arm removes every selected family from every client, and replacement examples refill the matched budget; across seeds the two arms differ in about 2,100 of 24,000 fit rows. The confirmatory 11.96-point contrast includes that composition change. The wrong-family placebo, reported separately, substitutes the same total number of malware examples from an unselected family into the absent-everywhere sample, matching per-peer counts where feasible and reallocating them when necessary; peer-present recall exceeds it by 10.04 points (interval 8.35 to 12.28, all ten extension seeds), while the placebo itself changes recall by −0.54 points."

**Implementation requirement:** Text only

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-003

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Reproducibility

**Location:** Expanded-family association paragraph (P149): "Across all 32 families, the stored Spearman association is .408, with family-bootstrap interval .088–.662 and permutation p = .0214." Stable-eligibility sentence (P150): "ρ = .294, interval −.076 to .589, and p = .136."

**Observed issue (pass 1).** The manuscript interval matches `results/extension-b/large-family-summary.csv` (rho `0.407991`, interval `[0.08772, 0.66180]`) and `large-family-eligibility-stability-summary.csv` (rho `0.29426`, interval `[−0.07622, 0.58881]`), but `diagnostic-synthesis-large-family-associations.csv` stores `[0.07731, 0.65236]` and `diagnostic-large-family-stability.csv` stores `[0.08673, 0.65855]` and `[−0.07845, 0.58579]` for the same rho.

**Resolution of the cause (pass 3).** Re-running the frozen procedure (`analysis/extensions.py` `novelty_association`: percentile bootstrap over families, 9,999 resamples, generator seed 20260924, families in `large-family-ctk.csv` file order) reproduces the manuscript values exactly: rho 0.407991, p 0.02045, interval [0.08772, 0.66180]; stable subset of 27 families rho 0.29426, p 0.13625, interval [−0.07622, 0.58881]. Sorting the same 32 families alphabetically before resampling, with the same seed, gives [0.0889, 0.6521]. The diagnostic files differ only because they resample in a different order or with a different routine. The manuscript numbers are the canonical frozen-protocol values; there is no error.

**Evidence:** `large-family-summary.csv`, `large-family-eligibility-stability-summary.csv`, and the two diagnostic CSVs named above; `analysis/extensions.py`, `novelty_association`. The full-sample analytic Spearman p is `0.020448324954202974`; the distinct permutation p reported by the chapter is `0.0214`. They are separate rows in the same source table, not conflicting estimates.

**Why it matters.** A replicator who opens a diagnostic file will think the manuscript interval is wrong. One clause naming the source file prevents that.

**Recommended correction.** Name the source file. Do not change the numbers.

**Suggested replacement.** In P149, replace "the stored Spearman association is .408, with family-bootstrap interval .088–.662" with "the frozen Spearman association (large-family-summary.csv) is .408, with family-bootstrap interval .088–.662".

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open (cause resolved in pass 3)

---

**ID:** CTK-AUDIT-011

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Reproducibility

**Location:** Permutation paragraph that reports +0.30 points on the original seeds and −0.21 / −0.07 on the extension. Artifact: `results/extension/permutation-control-audit.csv`.

**Observed issue:** The chapter assigns the two numbers to the correct seed blocks. The extension CSV labels the seeds-200–209 federation-wide row with evidence class `A-original-confirmatory`. That string names the contrast family inside the extension analysis. A reader of the CSV alone can mix +0.30 (seeds 100–109, recomputed from `arm-metrics.parquet`) with −0.21 (seeds 200–209, stored mean `−0.00209394`).

**Evidence:** Polars read of `results/extension/run-index.parquet`: the only extension permutation experiment has seeds 200–209, status completed. Confirmatory recomputation: mean `0.0030203116`, interval `[−0.0036154393, 0.0101999574]`, p = 0.492, 6/10. Extension CSV federation-wide FedAvg 5%: mean `−0.00209394`, interval `[−0.00828, 0.00514]`, 4/10. Own-domain extension mean `−0.00072592`, 5/10.

**Why it matters:** The prose is correct. The artifact label is the hazard.

**Recommended correction:** One clause in the permutation paragraph. Do not change the CSV in this audit.

**Suggested replacement:** "The extension file permutation-control-audit.csv labels its federation-wide row A-original-confirmatory because that row is the primary contrast definition; the seeds in that file are 200–209, and the mean there is −0.21 points, not the original +0.30 points from seeds 100–109."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-012

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Literature

**Location:** Related-work paragraph beginning "Ciaramella et al. (2026) investigate federated malware detection using image representations derived from application code and convolutional architectures."

**Observed issue (pass 1).** The full text could not be obtained, so the three method claims were unverified.

**Resolution (pass 2).** The version of record was found already in the repository (`docs/temp/lit/pdf/1-s2.0-S0950584925002319-main.pdf`), confirmed by its PDF metadata ("Information and Software Technology, 189 (2026) 107892. doi:10.1016/j.infsof.2025.107892") and its licence line ("This is an open access article under the CC BY license"). A copy is now `chapter/references_pdf/Ciaramella2026-FedML-Android.pdf` (15 pages, SHA-256 `dd7bc489845a1cc559105e6e245ede45dc606b62ebb87eb8821e56bce358b368`). The text supports all three claims: APKs are converted into grayscale images from DEX code (Section 3.1, Fig. 2); the models are CNNs (custom MobileNet variants and InceptionV3, pretrained on CIFAR-10 or ImageNet); the paper compares IID ("Default") and non-IID (Dirichlet) distributions, compares federated with centralized training, and compares training with and without a Clipping Norm Aggregator. The dataset has more than 40,000 applications with malware from 71 families. The paper does not withhold families or define an absent-everywhere arm, so the chapter's contrast with CTK-Android is accurate. Author list, volume, article number, and DOI in the reference entry match the PDF.

**Evidence:** The identified version-of-record PDF, Section 3.1 and Figure 2, its CNN and partition comparisons, and the title/author/DOI metadata specified in the resolution above.

**Why it matters:** Full-text inspection resolves the original uncertainty and prevents an unnecessary correction to an accurate related-work paragraph.

**Recommended correction:** None.

**Suggested replacement:** None.

**Implementation requirement:** No action

**Priority:** P3

**Status:** Resolved by Existing Evidence

---

**ID:** CTK-AUDIT-013

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Figure 3 legend, "Mean client" and "Worst client."

**Observed issue:** The filled circles match Table 4's federation-wide unseen-recall means. The open squares match Table 4's worst-client column. The legend phrase "Mean client" can be read as a different estimand from the axis label "Federation-wide unseen-family recall."

**Evidence:** Visual inspection of `chapter/figures/Figure_3.tif` against `results/tables/primary-arm-comparison.csv`.

**Why it matters:** The plotted numbers are right. The legend invites a false distinction.

**Recommended correction:** Change the legend only.

**Suggested replacement:** Legend entries: "Mean across seeds" and "Mean of the within-seed worst client."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-014

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Figure 4. Example: adwo local recall `0.6734` is printed as 0.67, while the text says 67.34%.

**Observed issue:** The heatmap rounds proportions to two decimals. The text reports percentage points to two decimals, which is one more significant digit. Both are the same family-level means. Pass 2 found one place where the rounding hides a claim: for adwo the figure prints 0.67 for both local (0.6734) and peer-present (0.6660), while the text says the peer-present model "remains slightly below the local reference." A reader checking the text against the figure sees no difference.

**Evidence:** `results/tables/family-level.csv` controlled-exposure FedAvg rows: adwo local 0.6734, absent 0.5623, peer 0.6660, CTK 0.1037; airpush CTK 0.0871 and peer 0.7924; dowgin 0.6545 / 0.7668 / 0.7682 and CTK 0.0014; gappusin CTK 0.0346 and peer 0.3163, below local 0.3256; hiddad CTK 0.0325 and peer 0.2657, below local 0.2893; leadbolt local 0.3023, peer 0.5903, CTK 0.2775; revmob local 0.2720, peer 0.5212, CTK 0.3338, full FedAvg 0.5575. Central full-exposure recalls used in the text for gappusin and hiddad are 0.4238 and 0.2868. The figure's full-exposure column is FedAvg, and the chapter's note says so.

**Why it matters:** A spot check of 0.67 against 67.34% looks like a mismatch.

**Recommended correction:** Add a caption clause. Do not retune the heatmap unless the production script is rerun under an authorized change. This audit does not change the figure.

**Suggested replacement:** "Cell values are mean recall proportions rounded to two decimals. The text reports the same means as percentages to two decimals; for adwo, local and peer-present recall round to the same cell value (67.34% and 66.60%)."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-016

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Literature

**Location:** CyberForce reference entry, "Bovet, G."

**Observed issue (pass 1).** Pass 1 reported a missing accent because the arXiv preprint prints the given name "Gérôme Bovet."

**Resolution (pass 2).** The finding was wrong. The chapter uses APA initials for given names, so the entry is "Bovet, G."; the surname has no accent and the initial "G." cannot carry one. The pass-1 replacement ("Bovet, Gérôme") would break APA style. The rest of the pass-1 check stands: author order and the compound surnames Sánchez Sánchez and Martínez Pérez match the preprint, and volume 22, issue 4, pages 4398–4411, year 2025 match Crossref. The chapter's description of the missing-client experiment is supported by the preprint (missing-client ratio 10% to 100%; FedAvg, Krum, trimmed mean; local-model curves; IoT moving-target defense). The authors' own notes (`docs/Research Evidence.md` §29.3) warn that CyberForce's Table IX appears to contradict its prose and Table X; the chapter cites neither table, so no change is needed.

**Evidence:** `Feng2025-CyberForce-arxiv.pdf` byline, the chapter’s "Bovet, G." entry, and the Crossref record for `10.1109/TDSC.2025.3547005`, rechecked in pass 4.

**Why it matters:** Retaining the withdrawn finding would introduce an APA inconsistency into a correct author list.

**Recommended correction:** None.

**Suggested replacement:** None.

**Implementation requirement:** No action

**Priority:** P3

**Status:** Resolved by Existing Evidence

---

**ID:** CTK-AUDIT-018

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Writing

**Location:** Introduction paragraph beginning "The main result is that complementary exposure contributes substantially."

**Observed issue:** The paragraph states the result and then stacks family heterogeneity, client losses, alternative learners, and the confirmatory-versus-extension distinction before the reader has seen the design. Those qualifications are true and are repeated later. The stack makes the 11.96-point result sound less settled than the seed evidence is.

**Evidence:** The paragraph in the manuscript. Seed evidence in Section J. This is a writing diagnosis. No passage is labeled as machine-written. No detector was run.

**Why it matters:** Reviewers who skim the introduction meet the caveats before the design that makes the caveats interpretable.

**Recommended correction:** Keep the result and one cost sentence. Move the class-label sentence to the evidence-class section, where it already appears.

**Suggested replacement:** "Across ten confirmatory seeds, complementary peer exposure raises FedAvg federation-wide unseen-family recall by 11.96 percentage points (interval 9.15 to 15.21). Generic pooling contributes 1.51 points, and that interval includes zero. The own-domain total gain is 3.26 points, and known-family recall falls by 3.61 points. Family, client, and learner heterogeneity are reported with those averages."

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-019

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Writing

**Location:** Discussion subsection that begins "In the constructed LAMDA federation, FedAvg gains substantially from peer examples of locally withheld families."

**Observed issue:** The subsection restates the result, the matched budget, and the remaining composition change. The results section and Figure 1 already did that. The new content is the refusal to identify a responsible parameter or feature.

**Evidence:** The discussion paragraph. Figure 1 paragraph and Table 3.

**Why it matters:** A repeated result reads as uncertainty about the result.

**Recommended correction:** Delete the restatement of the magnitude. Keep the interpretation sentence.

**Suggested replacement:** "The confirmatory contrast in Table 3 is the fitted and calibrated response to the Figure 1 intervention, including the replacement examples that refill the matched budget. It does not identify which parameters or features carry the gain."

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-020

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Writing

**Location:** Conclusion paragraph beginning "Complementary peer exposure makes a measurable contribution."

**Observed issue:** The conclusion repeats the 11.96-point interval and the uncertain pooling term, which the abstract already states, and it does not mention the placebo or the exact-dose sign pattern. Those are the results that answer the specificity objection. They must stay labeled as extensions.

**Evidence:** Conclusion text. Placebo and dose files cited in Section J.

**Why it matters:** The last page is where a reviewer decides what the paper showed. Leaving specificity in the middle of the extensions section under-sells evidence the study already has.

**Recommended correction:** Add two sentences. Do not drop the own-domain or known-family sentences that follow.

**Suggested replacement:** "Two extensions, which are not part of the original three-contrast test, speak to specificity. At exact peer doses of 10, 25, 50, 100, and 200 examples, the FedAvg family-macro effect is positive in all ten seeds, and its mean increases with dose. The wrong-family placebo does not reproduce the gain: peer-present CTK exceeds the placebo by 10.04 points (interval 8.35 to 12.28)."

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-023

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Statistical

**Location:** Paragraph beginning "The mean curve increases, but the final increment does not establish a precise saturation boundary."

**Observed issue.** The paragraph reads the pooled 100-to-200 increment (2.01 points, −0.06 to 4.06) as "consistent with diminishing gains at the upper tested range." The pooled number averages two different patterns. In the primary family set CTK keeps rising between 100 and 200 examples; in the replication set it is flat.

**Evidence.** `results/extension-b/exact-dose-seed-effects.csv`, FedAvg, federation-wide, alpha 0.05, re-bootstrapped in pass 2 (SciPy BCa, 9,999 resamples, seed 20260924) and identical to `exact-dose-effects.csv`:

| Scope | CTK at 100 | CTK at 200 | Increment 50→100 | Increment 100→200 |
|---|---|---|---|---|
| Pooled | 12.48 (10.14, 14.91) | 14.49 (11.26, 17.57) | 4.65 (2.43, 7.09) | 2.01 (−0.06, 4.06) |
| Primary set | 15.70 (14.06, 17.66) | 19.92 (17.49, 23.56) | 3.42 (0.77, 4.36) | **4.23 (2.53, 6.55)** |
| Replication set | 9.45 (5.42, 14.11) | 9.48 (5.32, 14.30) | 5.67 (2.21, 9.84) | 0.03 (−3.91, 2.54) |

**Why it matters.** The primary-set rise to 200 examples is positive dose evidence that the current wording hides. The replication-set flattening is real heterogeneity. Neither supports a common plateau.

**Recommended correction.** Replace the sentence that begins "These estimates are consistent with diminishing gains".

**Suggested replacement.** "The pooled estimate combines two patterns. In the primary family set, CTK still rises by 4.23 points (interval 2.53–6.55) between 100 and 200 peer examples; in the replication set the same increment is 0.03 points (−3.91 to 2.54). The data therefore show neither a common plateau nor a universal minimum dose."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-024

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Scientific

**Location:** Paragraph beginning "Client-level decomposition is class C evidence."

**Observed issue.** The client paragraph reports federation-wide CTK and the Anzhi federation-wide total gain, but not the own-domain totals. Those are the numbers that explain the abstract's small own-domain gain of 3.26 points: the own-domain total is negative at two of the four clients.

**Evidence.** `results/tables/client-ctk-analysis.csv`, FedAvg, alpha 0.05, own-domain population (Class C, exploratory small-n BCa intervals as labelled in the file):

| Client | Own-domain total gain | Own-domain pooling | Own-domain CTK | Contributing seeds | Hidden-family test rows per seed |
|---|---|---|---|---|---|
| anzhi | −2.80 (−7.63, 3.57) | −5.00 | 2.21 | 8 | 2,393 |
| appchina | −0.40 (−4.59, 4.21) | −3.84 | 3.44 | 10 | 996 |
| play-early | 6.48 (3.04, 13.82) | −3.07 | 9.55 | 10 | 1,322 |
| play-late | 13.61 (4.43, 19.19) | −29.84 | 43.45 | 6 | 107 |

Federation-wide CTK is positive in 7 of 8 Anzhi seeds and 7 of 10 AppChina seeds, so client-level positivity is not uniform either.

**Why it matters.** The chapter says "some client-level benefits coexist with losses on known malware." The stronger, accurate statement is that the two Chinese-market clients gain nothing on their own hidden-family test applications on average, and the play-late gain rests on about 107 test applications per seed. This is what a deploying organization would ask first.

**Recommended correction.** Add two sentences after "Anzhi therefore illustrates the known-family cost of collaboration."

**Suggested replacement.** "On each client's own hidden-family test applications, the FedAvg total gain is −2.80 points at Anzhi and −0.40 at AppChina, against 6.48 at play-early and 13.61 at play-late; the first two intervals include zero. The positive own-domain average therefore comes from the two Google Play domains, and the play-late estimate rests on about 107 hidden-family test applications per seed."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-026

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Reproducibility

**Location:** Reproducibility paragraph beginning "The associated CTK-Android repository contains the source code"; repository files `docs/results.md` and `docs/Research Evidence.md`.

**Observed issue.** The confirmatory seeds were executed three times. `docs/Research Evidence.md` describes campaign 1 (2026-09-24, revision `e079972`); `docs/results.md` describes campaign 2 (2026-09-29, revision `1da371a` "plus uncommitted edits", `analysis_sources_clean: false`, explicitly "not bit-deterministic"). `docs/decisions/protocol-amendments.md` (2026-09-29 "Source freeze for the final clean campaign") then fixed unseeded CUDA dropout, enabled deterministic kernels, and superseded both. The chapter's numbers come from campaign 3 (`results/provenance/code.json`: execution and analysis revision `f6302f7`, sources clean). The two documents still present campaign-1 and campaign-2 numbers as current, for example FedAvg CTK +0.117 (0.091, 0.148), Spearman rho 0.454, stable-subset rho 0.349 with an interval excluding zero, and own-domain total +0.028. A replicator who opens them sees numbers that disagree with the chapter.

**Evidence.** `docs/results.md` lines 5–17 and Appendix A.1; `docs/Research Evidence.md` header; `results/provenance/code.json`; `results/provenance/protocol.json` (configuration fingerprint `8e2ecdf4…`, which `docs/results.md` reports as identical to campaign 1).

**Why it matters.** Two things. First, a reviewer who inspects the repository will find superseded numbers and may suspect re-running until results improved. The record shows the opposite: the headline was +0.117, +0.117, and +0.1196 across the three executions, and the reruns were for determinism, not for outcomes. Second, the fragile secondary results moved between campaigns exactly as the chapter's cautions predict: the stable-subset Spearman interval excluded zero in campaign 2 and includes zero in campaign 3. Stating this once strengthens the chapter's restraint about the novelty association.

**Recommended correction.** In the chapter, add one sentence to the reproducibility paragraph. In the repository (author action, outside this audit), mark the two documents as superseded at the top, or move them to an archive folder, so that `results/` is unambiguously the source of truth.

**Suggested replacement (chapter).** "The reported artifacts come from a final execution of the frozen configuration made after GPU dropout seeding and deterministic kernels were enabled. Two earlier executions of the same configuration were not bit-reproducible; they gave a FedAvg CTK of 11.7 points in both cases and are retained in the repository documentation but not pooled with the reported results."

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-027

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Reproducibility

**Location:** Table 2 note (P74), "Hyperparameters and statistical procedures were frozen before the confirmatory evaluation"; reproducibility paragraph (P89).

**Observed issue (pass 2).** The freeze commit `e079972` and the configuration commit `dccf996` are not reachable from any branch or tag (`git for-each-ref --contains e079972` is empty; `git fsck --unreachable --no-reflogs` lists 79 unreachable commits), and the freeze record's configuration fingerprint `84ec9a19…` differs from the evidence fingerprint `8e2ecdf4…`.

**Resolution of the fingerprint question (pass 3).** Loading the configuration from `git archive` copies of each revision gives `84ec9a19…` at `e079972` and `dccf996`, and `8e2ecdf4…` at `1da371a`, `f6302f7`, and HEAD; the whole-configuration fingerprint changed only because extension entries were added. The decisive check is the per-run fingerprint, which hashes exactly the configuration parts that affect a run (`Config.run_fingerprint`). Computed with the freeze-commit code and configuration, it equals the SHA-256 of the `resolved_configuration` stored in every one of the 140 confirmatory run manifests (`outputs/runs/confirmatory/*/seed-*/manifest.json`), for all 12 confirmatory experiments; for controlled-exposure the value is `584faeef853d432c13c08c73d66a7e27db1295a65a5379e5e9aa47560ed60ea6`. In addition, `select_hyperparameters` applied to the saved development evidence (`collect_evidence(…, DEVELOPMENT, fairness=True)`) re-selects local epochs 10, fine-tuning epochs 2, and FedProx mu 0.1 from calibration-partition AUROC, with `frozen_drift` = [] (mean calibration AUROC: mu 0.1 0.93134 versus 0.01 0.931135; local 10 0.929115 versus 20 0.921057; fine-tune 2 0.919388 versus 5 0.916771). The chapter's freeze sentence is therefore verified mechanically, not only by documentation.

**Remaining issue.** Only preservation. The proof depends on `e079972`, which a future `git gc` can delete because no ref points to it.

**Evidence:** Freeze and analysis revision objects, `Config.run_fingerprint`, and the 140 resolved-configuration manifests, with the specific controlled-exposure digest and development-selection values given above. This supports the freeze claim while leaving archival preservation as the only open action.

**Why it matters.** The strongest provenance evidence in the repository currently exists only on the author's machine.

**Recommended correction.** Repository action by the author, outside this audit: create and push a tag on `e079972` (for example `protocol-freeze-2026-09-24`), or attach a `git bundle` containing it to the archived artifact, and add a one-line note that maps freeze fingerprint `84ec9a19…` to evidence fingerprint `8e2ecdf4…` through identical run fingerprints. Chapter change optional.

**Suggested replacement (chapter, optional).** P74: "Hyperparameters and statistical procedures were frozen before the confirmatory evaluation; every confirmatory run's resolved configuration matches the frozen protocol record."

**Implementation requirement:** Text only (chapter, optional); repository action by the author

**Priority:** P2

**Status:** Open (fingerprint question resolved in pass 3; preservation remains)

---

**ID:** CTK-AUDIT-029

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Figure 1 and its note ("Schematic of the implemented exposure conditions. Several families can be assigned to different targets within a run.").

**Observed issue.** The schematic shows one target and one family. It does not show the feature of the design that CTK-AUDIT-002 is about: in the absent-everywhere arm every selected family is removed from every client, so each target also loses the families assigned to other targets, which it keeps in the peer-present arm.

**Evidence.** Visual inspection of `chapter/figures/Figure_1.tif` (2111 × 1220, 400 dpi, grayscale). `experiment/design.py` `_excluded_families`. Pass-2 counts of swapped rows in Section B.

**Why it matters.** The figure is the first place a reader forms the estimand. A single-family picture makes the narrower reading of "CTK" natural.

**Recommended correction.** Replace the note. Redrawing the figure is optional.

**Suggested replacement.** "Note. Schematic for one target-family pair. In each run several families are assigned to different targets. Peer present removes each family only from its own target, so a target keeps the families assigned to other targets; absent everywhere removes every selected family from every client. Replacement examples refill each client's budget of 6,000 fit rows. Full exposure lifts deliberate exclusions but remains budgeted."

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-030

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Implementation

**Location:** Paragraph beginning "FedAvg runs twenty rounds with two local epochs per round" ("return parameters for sample-count-weighted aggregation").

**Observed issue.** The aggregation weights are sample counts (`experiment/training.py`: `weights = np.array([training[client].size …])`; `models.py` `average_states` normalizes them). Because every client contributes exactly 6,000 fit rows in every arm (run validation `sample-size-matched`: `[[6000], [6000], [6000], [6000]]`), the weights are all 0.25. A reader who sees Table 1 (play-late has 320,474 applications, AppChina 88,282) may assume the large Google Play clients dominate aggregation.

**Evidence.** `src/ctk_android/experiment/training.py` line 201; `src/ctk_android/experiment/models.py` lines 172–179; `outputs/runs/confirmatory/controlled-exposure/seed-100/validation.json`.

**Why it matters.** It removes a plausible but wrong alternative explanation (aggregation dominated by large clients) at the cost of one clause.

**Recommended correction.** Add one clause to the FedAvg description.

**Suggested replacement.** "…and return parameters for sample-count-weighted aggregation. Because every client contributes exactly 6,000 fit rows, these weights are equal."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-032

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Writing

**Location:** Abstract, last two sentences: "Separate dose, placebo, and representation extensions examine effect heterogeneity and specificity. The findings support exposure-aware evaluation within the tested offline populations and operating conditions."

**Observed issue.** The abstract's first five sentences are concrete and numerical. The last two describe activity ("examine") rather than findings, and the closing sentence states a scope rather than a result. The strongest specificity finding, the placebo, is reduced to a list item.

**Evidence.** Chapter abstract (126 words; IGI limit 100–150). Placebo and dose numbers in Section J.

**Why it matters.** Abstract readers decide whether to read the chapter. The current close is the weakest part of an otherwise strong abstract.

**Recommended correction.** Replace the last two sentences. The revised abstract is 142 words by whitespace count.

**Suggested replacement.** "In fresh-seed extensions, a wrong-family placebo recovers almost none of the gain, and complementary gain rises with the exact number of peer examples. Local-versus-federated comparisons alone cannot show how much of a collaborative gain depends on which families peers hold."

**Meaning check.** "Almost none" is accurate (−0.54 points, CTK minus placebo +10.04). "Rises with" is accurate for the pooled means and both family sets up to 100 examples; it does not claim a dose law. The last sentence is a methodological statement, not a deployment claim.

**Implementation requirement:** Text only

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-033

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Writing

**Location:** Five sentences, listed below. This is a writing diagnosis; no passage is labelled as machine-written and no detector was run.

**Observed issue and suggested replacements.**

1. CELEST paragraph: "while examining Android applications, several recall populations, and frozen uncertainty estimates." "Frozen uncertainty estimates" is unclear. Replace with: "while examining Android applications, several recall populations, and seed-level uncertainty intervals."
2. Primary-results paragraph: "This interval neither establishes a positive pooling benefit nor establishes that pooling is exactly ineffective. It permits both modest benefit and modest harm." Two sentences for one idea. Replace with: "The interval includes both a modest benefit and a modest harm."
3. Construct-validity paragraph: "These distinctions limit the language used for both positive and negative results." Adds no information. Delete.
4. External-validity paragraph, last sentence: "These are substantive limits on application of the findings, even when the within-study numerical and provenance checks are satisfied." Repeats the paragraph's preceding sentence. Delete.
5. Dose paragraph, last sentence: "These extensions clarify the exposure manipulation without being pooled into the original confirmatory test." The class separation is already stated in the evidence-class paragraph and in the Figure 5 note. Delete, or replace with CTK-AUDIT-023's sentence.

**Evidence.** The quoted sentences in the extracted chapter text.

**Why it matters.** Each sentence is small, but together they are the pattern a reviewer reads as padding or hedging, and they spend words that CTK-AUDIT-021, 022, 024, and 025 need.

**Recommended correction.** Apply the five edits. Meaning and technical accuracy are unchanged; items 3–5 delete only restatements.

**Suggested replacement:** Use items 1–2’s exact replacement sentences and items 3–5’s specified deletions above; the merged implementation locations are S-02, S-13, and S-27.

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open

---

**ID:** CTK-AUDIT-034

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Key Terms and Definitions (P204): "Negative Transfer: A reduction in a specified target performance measure after a defined transfer or collaboration intervention, relative to its stated reference."

**Observed issue (pass 3).** "Negative transfer" is defined as a key term but the phrase does not occur anywhere in the chapter body (case-insensitive search of the extracted text finds it only in P204). The concept is present: own-domain pooling is −7.60 points and adwo falls from 67.34% to 56.23% under absence-everywhere pooling.

**Evidence.** Extracted chapter text, paragraphs P4–P181; P204.

**Why it matters.** Key terms are meant to index the chapter's vocabulary. A term that the body never uses looks like residue from an earlier draft.

**Recommended correction.** Use the term once where the chapter describes the phenomenon. Do not delete the key term.

**Suggested replacement.** P154: replace "The own-domain result is especially informative: negative pooling offsets much of a positive CTK effect." with "The own-domain result is especially informative: negative pooling, a form of negative transfer, offsets much of a positive CTK effect."

**Implementation requirement:** Text only

**Priority:** P3

**Status:** Open


**ID:** CTK-AUDIT-035

**Severity:** Minor

**Confidence:** Confirmed

**Category:** Statistical

**Location:** `src/ctk_android/analysis/statistics.py:74`, `exact_wilcoxon`; unquoted row in `results/statistics/paired-effects.parquet`: experiment `training-support-sensitivity`, salt 0, alpha 0.01, metric `worst-client-unseen-recall`, learner `central`, estimand `total-gain`. No manuscript table or sentence reports this p-value.

**Observed issue:** The helper always requests SciPy `method="exact"`. One exploratory group has tied absolute ranks (seeds 103 and 109 have opposite differences of equal magnitude), so the usual untied rank distribution is not its exact sign-permutation distribution.

**Evidence:** Independent enumeration of all 1,024 sign assignments to ranks `[7, 10, 5, 2.5, 4, 9, 1, 6, 8, 2.5]` gives two-sided p = `0.0078125`. The artifact and SciPy 1.18.1 with `method="exact"` give `0.009765625`. SciPy with `PermutationMethod(n_resamples=np.inf)` independently confirms `0.0078125`. The [official SciPy notes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html) explain that ties change the exact null distribution. The full scan covered 1,284 finite seed-effect groups: 24 with zero differences and 3 with tied absolute ranks, 26 distinct groups; the other 25 reproduce by exhaustive enumeration.

**Why it matters:** This is a bounded secondary-artifact accuracy issue. Both values are below .05 and .01; no sign, primary Holm result, interval, or published numerical claim changes. It does not warrant major revision or new training.

**Recommended correction:** In a separately authorized software/artifact maintenance change, use exhaustive sign permutations for small tied/zero-containing vectors, retain the declared zero convention, and regenerate only affected statistical summaries with provenance. Until then, describe this row as the stored untied-distribution calculation rather than an exact tied-rank p-value. Do not change the chapter's three primary p-values.

**Suggested replacement:** No manuscript replacement required; the affected p-value is not quoted. A maintenance note can state: "One exploratory tied-rank p-value is .0078125 under exhaustive sign enumeration, compared with .009765625 in the frozen summary; its significance classification is unchanged."

**Implementation requirement:** Existing data (no training; any helper or derived-artifact correction is outside this audit's permitted writes).

**Priority:** P3

**Status:** Open

---

## F. High-Value Enhancements

**ID:** CTK-AUDIT-010

**Severity:** Enhancement

**Confidence:** Confirmed

**Category:** Writing

**Location:** End of the primary-results subsection, before the learner table, and the conclusion (see CTK-AUDIT-020).

**Observed issue:** The placebo (+10.04 points, 10/10), the exact-dose sign pattern (10/10 at each of five doses), and the confirmatory permutation near zero are the most direct answers to "any extra malware would have done this" and "the label is arbitrary." They appear after a long robustness section. The primary 11.96-point result is Class A. These controls are not Class A, except the original permutation, and the text must keep that distinction. The original permutation's own-domain interval still reaches +3.04 points, and the chapter correctly calls that unresolved.

**Evidence:** Section J rows for permutation, placebo, and exact dose.

**Why it matters:** A reviewer who stops at Table 3 sees a strong contrast and a disclosed composition change. A reviewer who is shown the placebo and the dose curve sees family-specific, dose-ordered evidence.

**Recommended correction:** Insert a four-sentence bridge at the end of the primary FedAvg result. Use the replacement in CTK-AUDIT-020 in the conclusion. Do not move extension p-values into the Holm family.

**Suggested replacement:** "Specificity checks address the content of the exposure: the original family-permutation control uses confirmatory seeds, while the wrong-family placebo uses a separate extension seed block. Shuffling family labels on the original seeds reduces federation-wide CTK to 0.30 points (interval −0.36 to 1.02). Supplying a wrong family at the peers, instead of the target family, produces a CTK-minus-placebo difference of 10.04 points (interval 8.35 to 12.28), positive in all ten extension seeds. Exact doses from 10 to 200 peer examples are positive in all ten seeds, and their mean effects increase with dose."

**Implementation requirement:** Text only

**Priority:** P1

**Status:** Open

---

**ID:** CTK-AUDIT-015

**Severity:** Enhancement

**Confidence:** Confirmed

**Category:** Statistical

**Location:** Statistical-methods or primary-results paragraph on ten seeds.

**Observed issue:** The chapter correctly says ten seeds limit subgroup precision. It does not show whether the 11.96-point mean depends on the two largest seeds (about +20.0 and +18.7 points).

**Evidence:** The ten seed effects listed in Section B. Leave-one-seed-out means, in percentage points: 11.06, 11.82, 11.66, 12.47, 12.25, 11.21, 12.30, 12.57, 11.57, and 12.65. Minimum 11.06 (leaving out the +19.99 seed). Maximum 12.65 (leaving out the +5.69 seed).

**Why it matters:** This is the least expensive answer to "one seed carries the mean." It does not create a new confirmatory test and does not widen the BCa interval. Subgroup counts such as play-late's six seeds remain limited. The calculation can be wrong if the seed effects are mis-ordered; the audit used the recomputed differences in seed order 100–109. An editor should recompute from `arm-metrics.parquet` rather than type these digits from memory. The scientific question is whether every leave-one-seed-out mean of the primary FedAvg federation-wide CTK differences stays above 3 points. Required file: `results/evidence/arm-metrics.parquet`, filtered to controlled-exposure, salt 0, alpha 0.05, FedAvg, federation-unseen recall, seeds 100–109. Computation: paired peer-minus-absent difference per seed, then the mean of each nine-seed subset. Evidential value: shows the sign and the practical-threshold conclusion do not depend on a single seed. Interpretive risk: leave-one-seed-out is not a confidence interval and must not be substituted for the BCa interval. New training is not required. The result of this particular calculation is positive in the sense above; that statement is a completed audit calculation, not a prediction about an unrun analysis.

**Recommended correction:** Add one sentence next to the existing ten-seed limitation.

**Suggested replacement:** "Leaving out any one confirmatory seed leaves a mean CTK between 11.06 and 12.65 points, still above the three-point practical threshold. That range is a sensitivity check on the ten observed differences. It is not a replacement for the BCa interval."

**Implementation requirement:** Existing data

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-025

**Severity:** Enhancement

**Confidence:** Confirmed

**Category:** Statistical

**Location:** Learning-strategy paragraph beginning "Table 4 compares all six peer-present learning strategies"; operating-point sentence "At the stricter 1% nominal FPR, the FedAvg federation-wide CTK estimate is 7.85 points".

**Observed issue.** The chapter reports peer-present levels for every learner but CTK only for FedAvg (and linear and tree models in Table 5). It also reports 1% but not 10%, although Table 2 lists both as sensitivities. The unreported values are uniformly favourable.

**Evidence.** Pass-2 recomputation from `results/evidence/arm-metrics.parquet`, controlled-exposure, seeds 100–109, peer-present minus absent-everywhere, federation-wide, SciPy BCa:

| Learner or operating point | CTK (points) | 95% BCa | Positive seeds |
|---|---|---|---|
| Central | 13.10 | 10.29, 16.70 | 10/10 |
| FedProx | 13.20 | 10.57, 16.71 | 10/10 |
| Fine-tuned FedAvg | 8.20 | 5.59, 10.83 | 10/10 |
| Blend | 7.60 | 5.25, 10.41 | 10/10 |
| FedAvg at 1% FPR (in chapter) | 7.85 | 3.90, 12.87 | 9/10 |
| FedAvg at 10% FPR | 13.78 | 11.67, 17.01 | 10/10 |

None is in the Holm family. All three tests per row have no zero differences and no tied absolute ranks.

**Why it matters.** "Alternative learners change these tradeoffs" currently reads as if the exposure effect might vanish under another learner. It does not; only its size and its costs change.

**Recommended correction.** Add one sentence to the learner paragraph and one clause to the operating-point sentence. Label both as secondary, outside the Holm family.

**Suggested replacement (after "…both below the FedAvg mean.").** "Complementary exposure is positive for every collaborative learner: CTK is 13.10 points for central training, 13.20 for FedProx, 8.20 for fine-tuned FedAvg, and 7.60 for blending, each positive in all ten seeds. Learner choice changes the size and the cost of the exposure benefit, not its direction."

**Suggested replacement (operating point).** "At the stricter 1% nominal FPR the FedAvg federation-wide CTK estimate is 7.85 points, and at 10% it is 13.78 points."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P2

**Status:** Open

---

**ID:** CTK-AUDIT-031

**Severity:** Enhancement

**Confidence:** Confirmed

**Category:** Reproducibility

**Location:** Partition paragraph sentence "It nevertheless conditions the experiment on support-rich partitions, which is a selection feature relevant to external validity." and the threats paragraph beginning "Selecting the best-supported partition among 16 candidates".

**Observed issue.** The chapter discloses the selection correctly but gives no size. Pass 1 recorded the margin as unquantified because the attempt index was not in `run-provenance.json`. It is in `outputs/preprocessing/partitions/seed-*/manifest.json`, and pass 2 re-executed all 160 candidates (Section B).

**Evidence.** Winning attempts reproduce in 10/10 seeds. Eligible controlled-plus-natural pairs: chosen 57–60, median 52.5–56, minimum 48–52; mean ratio chosen/median 1.086.

**Why it matters.** "Best of 16" invites the question "how much better?" The answer, about 9% more eligible pairs, quantifies the eligibility benefit. It does not establish that the chosen partitions are typical on all outcome-relevant characteristics.

**Recommended correction.** Optional: add one sentence after the partition-selection sentence.

**Suggested replacement.** "In the confirmatory seeds the retained candidate has 57–60 eligible client-family pairs, against a median of 52.5–56 across its 16 candidates, so the rule raises the eligible-pair count by about 9% relative to the median candidate. This does not assess representativeness on other characteristics."

**Implementation requirement:** Existing data (already computed; text only to report)

**Priority:** P3

**Status:** Open


**ID:** CTK-AUDIT-036

**Severity:** Enhancement

**Confidence:** Confirmed

**Category:** Formatting

**Location:** Figures 1–5, `word/document.xml`, five `wp:docPr` nodes with names "Picture 1" through "Picture 5" and no `descr` attributes.

**Observed issue:** The embedded figures have captions but no alternative-text descriptions. Their raster labels are unavailable to a screen reader through the image metadata. This is an accessibility opportunity, not a demonstrated IGI rejection condition.

**Evidence:** Read-only OOXML inspection found no `descr` or `title` on any of the five drawing-property nodes. All five separate TIFFs are grayscale at 400 dpi, and the plotted content is readable; the issue concerns nonvisual access.

**Why it matters:** Readers using assistive technology need the diagram's relationships and each plot's principal message in text.

**Recommended correction:** Optionally add concise alternative text to each image in the authoring application, preserving the existing captions and all numerical evidence. Check the final publisher format retains the descriptions.

**Suggested replacement:** Figure 1: "Exposure schematic: a selected family is withheld at its target, retained at peers in the peer-present arm, absent at all clients in the absent arm, and allowed everywhere in full exposure; client training counts are matched." Figure 2: "FedAvg federation-wide recall effects: CTK 11.96 points, pooling 1.51, total 13.46; CTK and total intervals exclude zero, while pooling spans zero." Figure 3: "Across six learners, average unseen recall exceeds the average of each seed's lowest client recall; rankings differ between these summaries." Figure 4: "Family recall across four exposure conditions: complementary gains are largest for revmob and leadbolt, while dowgin gains chiefly through pooling and gappusin and hiddad retain low recall." Figure 5: "In the prospective exact-dose study, mean family-macro CTK rises from 10 to 200 peer examples for FedAvg and centralized learning; error bars show seed-bootstrap intervals."

**Implementation requirement:** Optional (text only; no figure data or retraining).

**Priority:** P3

**Status:** Open

---

## G. Claim-to-Evidence Matrix

Verification labels: **Recomputed** means this audit recalculated the statistic from seed-level `results/evidence/arm-metrics.parquet` with SciPy BCa (`n_resamples=9999`, seed 20260924) or from direct addition. **Matched CSV** means the manuscript number matches a frozen summary and the summary was not re-bootstrapped here. **Code** means the implementation was read and matches the claim. Headline rows are recomputed, not accepted only because a summary matched the chapter. The stored `paired-effects.parquet` agrees with the recomputation. In pass 2 the confirmatory rows were recomputed again with an independent script that does not import `ctk_android.analysis.statistics`, and the extension dose, placebo, and robust-aggregation rows were re-bootstrapped from their seed-level CSVs. Rows marked "pass 2" are new.

| Claim | Manuscript Location | Evidence Source | Verification | Action |
|---|---|---|---|---|
| FedAvg CTK +11.96 pp, CI 9.15–15.21, 10/10, Holm p = .00586 | Abstract; primary results | `arm-metrics.parquet`; `statistics.py` `bca_interval`, `exact_wilcoxon`, `holm_adjust`; `statistics.yaml` | Recomputed: mean 0.1195575610, CI [0.0915477400, 0.1520988052], p 0.001953125, Holm 0.005859375, 10/10, no zeros, no absolute ties | No number change. CTK-AUDIT-001, 002 |
| Total gain +13.46 pp, CI 8.82–17.04, 10/10 | Abstract; Table 3 | Same filter, peer minus local | Recomputed: 0.1346088107, CI [0.0881778015, 0.1704013706], Holm 0.005859375, 10/10 | No number change |
| Pooling +1.51 pp, CI −4.15 to 6.10, p = .32227, 7/10 | Abstract; Table 3 | Same filter, absent minus local | Recomputed: 0.0150512497, CI [−0.0414906894, 0.0609806470], p 0.322265625, 7/10 | No number change |
| Identity CTK + pooling = total | Methods equations | Recomputed seed differences | Recomputed: maximum absolute residual 0 | No action |
| Own-domain total +3.26 pp, CI 1.26–5.63 | Abstract; own-domain paragraph | Same artifacts, own-domain population | Recomputed: 0.0325631217, CI [0.01264, 0.05631], 8/10, p 0.02734375, not in the Holm family | No number change |
| Own-domain CTK +10.85; pooling −7.60 | Own-domain paragraph | Same | Recomputed: CTK 0.1085274487, CI [0.06974, 0.15249], 10/10; pooling −0.0759643270, CI [−0.11808, −0.04030], 1/10 positive | No number change. Keep visible |
| Known-family FedAvg −3.61 pp, CI −4.50 to −2.85, 0/10 | Abstract; learner tradeoff | `paired-effects` recomputed from arm metrics | Recomputed: −0.0360542944, CI [−0.04500, −0.02853], 0/10 | No number change. Do not soften |
| Levels: local 50.90, absent 52.41, peer 64.36, full 67.64 | Primary results; Table 4 | Arm means | Recomputed: 0.509013, 0.524064, 0.643622, 0.676353 | No number change |
| Table 4 six learners | Table 4 | `primary-arm-comparison.csv` | Matched CSV to two displayed decimals, including worst-client and FPR columns | No number change. CTK-AUDIT-013 |
| FedProx minus FedAvg +0.19, CI −1.12 to 2.94 | Learner paragraph | Paired effects | Recomputed: +0.001867, CI [−0.01124, 0.02936], p 0.492, 3/10 | No number change |
| Known-family fine-tune −3.74, FedProx −0.93, central −0.14, blend +1.70 | Learner tradeoff | Paired effects | Recomputed and matched to the displayed intervals in Section J | No number change |
| AUROC −0.01166; AUPRC −0.02011 | Discrimination paragraph | Paired effects | Recomputed: −0.0116644472 and −0.0201133641, both 0/10 | No number change |
| Family-macro CTK 12.44; total 10.57 | Secondary populations | Paired effects | Recomputed: 0.1243565726, CI [0.10092, 0.15550]; total 0.1056793490 | No number change |
| Worst-client CTK 18.49; total 14.88 | Secondary populations | Paired effects | Recomputed: 0.1849395218, CI [0.13883, 0.26288], 10/10; total 0.1487727724, 9/10 | No number change. Chapter already says the worst client can change across arms |
| Alpha 0.01 CTK 7.85, 9/10 | Operating point | Paired effects | Recomputed: 0.0785053870, 9/10 | No number change |
| FPR 5.04 / 5.09 / 5.04; worst-client mean 6.60; max 9.89 | Primary results | Arm metrics | Recomputed means 0.050411, 0.050921, 0.050357; worst-client mean 0.066025; max 0.098901 | No number change |
| Central peer/absent/full 66.07 / 52.97 / 70.19 | Table 4 discussion | Arm means | Recomputed: 0.660672, 0.529675, 0.701891 | No number change |
| Table 1 counts and malware shares | Dataset section | `dataset-client-audit.csv` | Recomputed by addition | No number change |
| 1,008,381 rows, 925 features, VT ≥ 4 malware and VT = 0 benign | Dataset section | LAMDA arXiv v1; frozen release used by the pipeline | Paper main text and overlap manifest agree on 925. The preprint appendix also prints 915 at threshold 0.01. The chapter correctly names the frozen 925-feature release | No action. Answer a reviewer with the frozen matrix, not the appendix cell |
| Aligned representation 554,136; 170,256 malware; 383,880 benign; widths 925 / 2,390 / 2,793 / 17,483 | Representation section | `overlap-manifest.json` and alignment audit | Matched artifact. SHA-256 of the JSON was not recorded | No number change |
| Eight primary names, seven eligible, frmy in the candidate set | Family selection | `primary-family-set.json`; family-level table has seven controlled families | Matched | No action |
| Family-level FedAvg recalls and CTKs in the primary-family paragraph | Family results | `family-level.csv` | Matched to displayed precision. See CTK-AUDIT-014 | Caption clause only |
| Replication family CTK: dnotua −8.24, zdtad −2.06, inmobi 13.63, domob 12.04; utchi and zdtad six seeds | Replication paragraph | `family-level.csv` | Matched | No number change |
| Client CTK 8.35 / 7.58 / 9.18 / 32.03; seeds 8 / 10 / 10 / 6; Anzhi total 1.34; known-family −6.93 | Client paragraph | `client-ctk-analysis.csv` | Recomputed pass 3 from run-level `metrics/clients.parquet` hits and trials (exact match, including own-domain totals −2.80, −0.40, 6.48, 13.61). Matched CSV: 0.083526, 0.075844, 0.09176, 0.320273; totals and −0.069328. Not re-bootstrapped | No number change |
| Original dose effective support 9.03, 79.39, 296.19; only all-available meets 100 | Dose paragraph | `peer-dose-response.csv` | Matched CSV; effective doses recomputed pass 3 from run `exposure.parquet` (0.09, 0.86, 4.49, 9.03, 43.1, 79.39, 296.19 over 70 family-seed observations) | No number change |
| Exact dose 2.92, 4.90, 7.83, 12.48, 14.49; intervals at 10 and 25; increments 4.65 and 2.01 | Exact-dose paragraph; Figure 5 | `exact-dose-effects.csv` | Matched CSV; re-bootstrapped in pass 2 with identical endpoints. Dose-zero minus absent is 0. Central series on Figure 5 matches the same file | No number change. CTK-AUDIT-010 |
| Permutation +0.30, CI −0.36 to 1.02; own-domain upper 3.04; extension −0.21 and −0.07 | Permutation paragraph | Arm metrics for seeds 100–109; extension CSV for 200–209 | Original recomputed. Extension recomputed pass 3 from run-level summaries: −0.00209394 (−0.008285, 0.005138), own-domain −0.00072592 (−0.007748, 0.006007), exact match. See CTK-AUDIT-011 | One clarifying clause |
| Placebo −0.54; CTK−placebo +10.04, CI 8.35–12.28, 10/10 | Placebo paragraph | `controls-effects.csv` | Matched CSV and re-bootstrapped in pass 2: −0.005390, CI [−0.01362, 0.00204]; difference 0.100372, CI [0.08348, 0.12280], 10/10 | Emphasize earlier. CTK-AUDIT-010 |
| Robust aggregation CTK 9.50 / 9.16 / 13.76 | Robustness paragraph | `controls-effects.csv` | Matched CSV and re-bootstrapped in pass 2: mean 0.094982, trimmed 0.091620, median 0.137618. Replication-set trimmed-mean CTK 4.69 (2.21, 6.88) has a lower bound below 3 | No number change. Not a poisoning result |
| Table 5 sensitivity CTKs | Table 5 | Arm metrics, seeds 100–109 | Recomputed and matched: replication 5.077 [2.28, 7.10] 8/10; natural scarcity 11.191 [9.46, 12.59]; linear 9.372 [7.54, 10.97]; trees 10.181 [7.59, 13.70]; low training support 10.988; low family support 14.006; high family support 11.588; package-only 11.319 | No number change. Replication mean is above 3 points and the interval lower bound 2.28 is not. The chapter already says this |
| Partition salts 12.90, 12.77, 11.20, all 10/10 | Table 5 prose, salts not all printed | `partition-salt-sensitivity` in arm metrics | Recomputed | Optional to print. Not required |
| Representation priority-macro differences | Representation section | `representation-effects.csv` | Matched CSV and re-bootstrapped pass 3 from `representation-seed-effects.csv` (108 rows, 0 mismatches): McNdroid-static full +7.57 [2.76, 12.85]; FedAvg CTK +8.01 [3.56, 10.54]; call-graph CTK +9.03 [5.53, 12.35]; call-graph full +2.52 [−0.86, 7.77]; report full −14.54 [−18.63, −8.66]; report CTK −6.12 [−9.91, −3.87] | No number change |
| Family representation examples | Same section | Representation family rows | Matched: gappusin +16.93, adwo +33.60, hiddad −6.21 [−18.02, 6.29] | No number change |
| Equal-FPR diagnostic +7.28, −14.27, call-graph interval includes 0; class D | Same section | `diagnostic-representation-equal-fpr-effects.csv` | Matched CSV. Evidence class column `D-post-hoc-diagnostic` | No number change. Keep the post-hoc label |
| Four macro-FPR failures and 15.32% client FPR | Same section | `diagnostic-fpr-exceptions.csv`; `experiments.yaml` r0/r1/r2 | Matched, including seed 317 macro FPR 0.0759 and anzhi r2 FPR 0.153211 | No number change |
| Spearman 0.408, interval 0.088–0.662, p = 0.0214; stable 0.294, p = 0.136 | Expanded families | `large-family-summary.csv`, stability summary; `extensions.py` `novelty_association` | Re-bootstrapped pass 3 with the frozen routine: exact match (0.407991, [0.08772, 0.66180]; 0.29426, [−0.07622, 0.58881]). Diagnostic files differ only by resampling order | Name the file. CTK-AUDIT-003 |
| Five negative expanded-family CTKs, including feiwo and baiduprotect | Same section | `diagnostic-synthesis-large-family-ctk.csv` | Matched: admogo −0.0016, feiwo −0.05894 (8 seeds, 0 positive), baiduprotect −0.04410, umpay −0.03514 (2 seeds), dnotua −0.00722 | Optional clause that umpay has 2 seeds. Do not drop the negatives |
| FedAvg sample-count weights; full participation of 4 clients; new Adam each local call | Methods | `training.py`, `models.py` | Code | No action |
| FedProx 0.5 mu ‖w − w^t‖², mu 0.1 | Methods | `models.py` `fit_epochs`; config | Code | No action |
| Quantile method higher; flag if score strictly exceeds; insufficient if count × alpha < 10 | Methods | `evaluation.py` `calibrate` | Code | No action |
| Blend is the equal average of local and FedAvg probabilities | Methods | `evaluation.py` `blend_scores` | Code | No action |
| 16 partition attempts maximize eligible-pair count, not test score | Methods | `partitions.py` `build_partition`; `outputs/preprocessing/partitions/seed-1xx/manifest.json` | Code, and re-executed in pass 2: winning attempt reproduced 10/10; chosen 57–60 pairs versus median 52.5–56 (pass 1 said the margin was unquantifiable; the attempt index is in the partition manifest) | Optional sentence, CTK-AUDIT-031. Do not call this test-set selection |
| Micro-pooled CTK (defined, not reported) | Metric-definition paragraph | `arm-metrics.parquet` metric `micro-unseen-recall`; `evaluation.py` `summarize` | Recomputed pass 2: 6.58 (4.64, 8.65), 10/10; pooling 4.00; total 10.58 | Report. CTK-AUDIT-021 |
| CTK for central, FedProx, fine-tune, blend; FedAvg at 10% FPR | Not reported | `arm-metrics.parquet` | Recomputed pass 2: 13.10, 13.20, 8.20, 7.60, all 10/10; 13.78 at 10% | Report. CTK-AUDIT-025 |
| Expanded-family overlap and new-family CTK | Expanded-family paragraphs | `large-family-ctk.csv`, `large-family-seed-ctk.csv` | Computed pass 2: 14/32 overlap; new 18 families 3.47 (2.45, 4.45), 10/10; overlapping 10.67 | Report. CTK-AUDIT-022 |
| Exact-dose increments by family set | Dose paragraph | `exact-dose-seed-effects.csv` | Re-bootstrapped pass 2: primary 100→200 +4.23 (2.53, 6.55); replication +0.03 (−3.91, 2.54) | Reword. CTK-AUDIT-023 |
| Per-client own-domain total gain | Client paragraph (not reported) | `client-ctk-analysis.csv` | Matched CSV: −2.80, −0.40, 6.48, 13.61 | Report. CTK-AUDIT-024 |
| Placebo is count-matched to peer-present on the absent sample | Placebo paragraph | `design.py` `_train_placebo`, `choose_placebos`, `substitute` | Code, pass 2. Pass-1 description corrected | Use in CTK-AUDIT-002 wording |
| Hyperparameters and statistical procedures frozen before confirmatory evaluation | Table 2 note | `git diff e079972 HEAD -- configs/`; `protocol-amendments.md` | Verified pass 2 (config diff) and pass 3 (run fingerprints from the freeze commit equal all 140 stored resolved configurations; hyperparameter selection re-derived from development evidence with zero drift); commit unreachable from branches | Preserve commit. CTK-AUDIT-027 |
| FedAvg sample-count weighting | FedAvg paragraph | `training.py`, `models.py`, run validation | Code: weights equal because every client has 6,000 rows | One clause. CTK-AUDIT-030 |
| AndroZoo supplies applications, antivirus results, and market metadata | Dataset quality paragraph | `Allix2016-AndroZoo-orbilu.pdf` | Read pass 2: more than three million apps, tens of AV products, crawlers per market including Anzhi and AppChina | No action |
| Ciaramella image/CNN/IID-non-IID/aggregator description | Related work | `Ciaramella2026-FedML-Android.pdf` (CC BY VoR) | Read pass 2: supported | No action. CTK-AUDIT-012 resolved |
| Grouped random split is not a forward-in-time evaluation | External validity | Design and the chapter's own limitation | Code and text agree | No action. Cite FL-MalDrift as the chronological neighbor. CTK-AUDIT-009 |
| No privacy accountant and no poisoning evaluation | Discussion | Chapter text; robust-aggregation experiment has no malicious updates | Code and text agree | No action |
| Holm covers only the three primary FedAvg federation-wide contrasts | Statistics | `statistics.py` `contrast_family`; chapter | Code and text agree. Headline contrasts have no ties, so `wilcoxon(method="exact")` is the exact permutation p. Pass 4 scanned all 1,284 finite seed-effect groups: 24 contain zeros and 3 contain absolute-rank ties (26 distinct groups); 25 p-values agree with exhaustive sign enumeration, with one discrepancy in CTK-AUDIT-035 | No action for Table 3. Use the bounded secondary-artifact correction in CTK-AUDIT-035 |
| Evidence classes A–D | Throughout | `project.yaml` seed blocks and experiment names | Matched, with CTK-AUDIT-011 for one CSV label | Clarifying clause only |
| CyberForce varies the fraction of clients missing malware, including all clients, with local references and several aggregators, on an IoT defense task | Related work | CyberForce arXiv v4, Section 4 and Table IX | Supported by the preprint. IEEE version of record not downloaded | No action (CTK-AUDIT-016 withdrawn) |
| CELEST evaluates families first seen in one network and represented at another, plus active learning and poisoning defense | Related work | CELEST arXiv v3, Section III-B and Table III | Supported by the preprint. IEEE TIFS PDF not downloaded | No scientific rewrite |
| LAMDA 2013–2025 excluding 2015, VT labels, concept drift, 1,008,381 samples | Dataset | LAMDA arXiv v1 | Supported. OpenReview PDF returned HTTP 403, so the ICLR version of record was not compared line by line | No action |
| McNdroid three aligned modalities, 2013–2025 excluding 2015, preprint | Related work | McNdroid arXiv PDF, 28 pages | Supported. DOI resolves to arXiv | No action |
| TESSERACT spatial and temporal bias; Arp et al. 2022 pitfalls | Evaluation design | USENIX PDFs, pages 729–746 and 3971–3988 printed in the files | Supported | No action |
| Repository revision f6302f7 and clean analysis sources | Reproducibility | `results/provenance/code.json`; git blob compare | Matched HEAD for `src/` and `configs/` | CTK-AUDIT-006 for the URL only |

## H. Complete Reference Audit

PDFs are under `chapter/references_pdf/`. SHA-256 values were computed on 2026-10-20. "VoR" means version of record. A preprint is not described as the journal PDF. No paywall was bypassed and no TLS verification was disabled. Pass 1 downloaded the NDSS and arXiv MaMaDroid files and reused the rest. Pass 2 reused all 14 existing files unchanged (hashes re-checked) and added 7: AndroZoo (ORBilu; the server omits its intermediate certificate, so the HARICA GEANT TLS RSA 1 intermediate was fetched from the certificate's own Authority Information Access URL and added to a scratch CA bundle, with full verification), Ciaramella (CC BY VoR copied from `docs/temp/lit/pdf/`), and five recommended additions (FLEKD-IDS, Shao et al., Popoola et al., Bi et al., Ishfaq et al.).

**Counts, matching the files on disk.** The chapter cites 14 works. The directory contains 21 PDF files. Thirteen cited works have at least one readable PDF, stored as 14 files (MaMaDroid has both the cited NDSS file and an extra arXiv file). One cited work has no retained PDF: Holm 1979. Pass 4 read the publicly reachable University of São Paulo-hosted JSTOR scan, but did not add it to this reference collection because redistribution permission was not established. Seven files are recommended additions, not citations: `Galvez2021-LiM.pdf`, `Patel2025-FL-MalDrift.pdf`, `Shen2024-FLEKD-IDS-arxiv.pdf`, `Shao2026-MissingClassSupport-jstage.pdf`, `Popoola2022-FDL-ZeroDay-aam.pdf`, `Bi2024-FL-CyberThreat-arxiv.pdf`, `Ishfaq2026-ZeroDay-FedEnsemble.pdf`. Fourteen cited-work files plus seven additions equal 21. Version-of-record gap: CyberForce, CELEST, LAMDA, and AVClass2 were read as preprints or author manuscripts; AndroZoo was read as the ORBilu deposit, which Unpaywall labels `submittedVersion` (4 pages, matching pp. 468–471). McNdroid is cited as a preprint, and the local file is that preprint.

**Pass-3 access attempts for versions of record.** No new file was needed or added; the 21 PDFs were re-hashed and are unchanged. Script downloads of the ACM PDFs for AndroZoo (`dl.acm.org/doi/pdf/10.1145/2901739.2903508`) and AVClass2 (`…/10.1145/3427228.3427261`) returned HTTP 403, and OpenReview (web and `api2.openreview.net`) returned a `ChallengeRequiredError`; these are bot protections, and they were not circumvented. Unpaywall lists only the submitted versions already held for AndroZoo, AVClass2, CELEST, and FLEKD-IDS, and no open copy for CyberForce or Popoola's IEEE version. arXiv has no later version of LAMDA (v1), CELEST (v3), CyberForce (v4), FLEKD-IDS (v1), AVClass2 (v2), Bi et al. (v1), or McNdroid (v1). Crossref has no journal version of Bi et al. A browser or library subscription may provide the remaining versions of record; the citing sentences do not depend on text that could differ between versions, because each cites the experimental design, not a number.

| Citation | Persistent identifier | Publication status | Local PDF | Source URL | Full text | Citation accuracy | Action |
|---|---|---|---|---|---|---|---|
| Allix, Bissyandé, Klein, and Le Traon 2016, AndroZoo | DOI `10.1145/2901739.2903508`. MSR 2016, pp. 468–471. No retraction relation in Crossref | Published conference paper. Local file is the ORBilu deposit (Unpaywall: submittedVersion) | `Allix2016-AndroZoo-orbilu.pdf`, 4 pages, SHA-256 `c451e2fb7788cbf71515f1556a80ee067da9293a304c0e3b00ae654f84318b5d` (pass 2) | `https://orbilu.uni.lu/bitstream/10993/27396/1/androzoo.pdf`; ACM `https://dl.acm.org/doi/10.1145/2901739.2903508` | Read in pass 2. Title and authors match the chapter entry. More than three million apps, each analysed by tens of antivirus products; dedicated crawlers per market, including Google Play, Anzhi, and AppChina; deduplication is local to each market | Supported. The chapter's statement that a market field is observational, not an organizational identity, is its own interpretation and is consistent with the paper's description of per-market crawling | None |
| Arp, Quiring, Pendlebury, Warnecke, Pierazzi, Wressnegger, Cavallaro, and Rieck 2022 | No DOI. Persistent URL `https://www.usenix.org/conference/usenixsecurity22/presentation/arp`. Printed pages 3971–3988 | USENIX Security 2022 | `Arp2022-Dos-and-Donts.pdf`, 19 pages, SHA-256 `fd71f39c2cd0f9532859c6bb5f2e3b94be97eec50b43f97aaa916e43f3f4acdb` | `https://www.usenix.org/system/files/sec22-arp.pdf` | Read. Pitfalls in collection, labeling, design, and interpretation, including snooping, are the paper's subject | Supported | None |
| Arp, Spreitzenbarth, Hübner, Gascon, and Rieck 2014, DREBIN | DOI `10.14722/ndss.2014.23247`. Crossref page field is null. Chapter gives no page range | NDSS 2014 | `Arp2014-DREBIN.pdf`, 12 pages, SHA-256 `95f3e6273ddf7854a6895e9648b016a30ed64e1d08dd2813823dffaf17bfbf7b` | `https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf` | Read. Static manifest and code features, including permissions and APIs, with explanations | Supported | None |
| Ciaramella, Martinelli, Peluso, Santone, and Mercaldo 2026 | DOI `10.1016/j.infsof.2025.107892`. Volume 189, article 107892. Crossref issued January 2026. No update or retraction relation | Published journal article, open access, CC BY 4.0 | `Ciaramella2026-FedML-Android.pdf`, 15 pages, SHA-256 `dd7bc489845a1cc559105e6e245ede45dc606b62ebb87eb8821e56bce358b368` (pass 2, VoR) | `https://doi.org/10.1016/j.infsof.2025.107892` (publisher landing page returned HTTP 403 to scripts; the VoR was already in `docs/temp/lit/pdf/`) | Read in pass 2. Grayscale images from DEX code; custom MobileNet and InceptionV3 CNNs pretrained on CIFAR-10 or ImageNet; IID versus Dirichlet non-IID; federated versus centralized; with and without a Clipping Norm Aggregator; more than 40,000 apps, 71 malware families | Supported. CTK-AUDIT-012 resolved | None |
| Feng, Huertas Celdrán, Sánchez Sánchez, Kreischer, von der Assen, Bovet, Martínez Pérez, and Stiller 2025, CyberForce | DOI `10.1109/TDSC.2025.3547005`. IEEE TDSC 22(4), 4398–4411. Unpaywall: not OA | Published. Local file is arXiv:2308.05978v4, 1 October 2024, 14 pages, with an IEEE TDSC running header. Not confirmed as the published PDF | `Feng2025-CyberForce-arxiv.pdf`, SHA-256 `ec7a21f0ff65295963d53d1dbb2649e11b8704e337b305cd2a7c3bfc0a18b97f` | `https://arxiv.org/pdf/2308.05978` | Read. Missing-client ratio 10% to 100%, a condition with all clients missing (Tables IX and X; the authors' notes warn that Table IX conflicts with the prose), FedAvg/Krum/trimmed mean, local-model curves, IoT moving-target defense | The chapter's comparison paragraph is supported by this preprint. Author list correct in APA initials (CTK-AUDIT-016 withdrawn) | None required for the scientific claim. Prefer the IEEE PDF if a legal copy becomes available, and re-check Table IX against it |
| Haque, Hossain, Kamol, Alam, Amalapuram, Talukder, and Rahman 2026, LAMDA | No DOI. OpenReview `https://openreview.net/forum?id=1FnCrZtBNQ`. arXiv:2505.18551v1, 24 May 2025 | ICLR 2026. Local file is the arXiv preprint, 31 pages. OpenReview PDF HTTP 403 | `Haque2025-LAMDA-arxiv.pdf`, SHA-256 `26df883d075156abfe69d4def70e2b27614f63a53ba08dc82d0a284f3f3ed129` | `https://arxiv.org/pdf/2505.18551` | Read. 2013–2025 excluding 2015; 1,008,381 samples; benign VT = 0; malware VT ≥ 4; AVClass2; VarianceThreshold 0.01 described as 925 features in the main text and 915 in one appendix table | Chapter claims match the main text and the frozen 925-column release. The chapter does not adopt the provider split | None. Pass 3 closed the 925-versus-915 question: the frozen source audit records `features=925` for the 1,008,381 rows (`outputs/preprocessing/source-audit/linkage/audit.json`), and the dataset's variant table (Hugging Face `IQSeC-Lab/LAMDA`) lists `var_thresh_0.01` with 925 binary features; the 915 is an inconsistency inside the preprint's appendix text. The ICLR camera-ready PDF on OpenReview sits behind a browser challenge and was not read |
| Holm 1979 | JSTOR `https://www.jstor.org/stable/4615733`. No DOI. Pass 3: OpenAlex lists `10.2307/4615733`, but `https://doi.org/10.2307/4615733` returns HTTP 404 and Crossref has no record, so that DOI is not registered and must not be added. Volume 6, number 2, pp. 65–70. Sture Holm | Published journal article. Paywalled | None | JSTOR URL above | Full text read in pass 4 from `https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf` (7 pages, including the JSTOR cover; printed pp. 65–70). Section 2, Scheme 1, and Theorem 1 support the step-down comparison and family-wise error control; Section 3 distinguishes test adjustment from simultaneous confidence sets. Pass 3 searched for a legal archival copy; the only full text found is a JSTOR-generated PDF re-hosted on a university course page (`ime.usp.br`), whose redistribution rights are unclear, so pass 3 neither downloaded nor read it; pass 4 inspected it in temporary external storage without retaining or redistributing it | The chapter uses Holm's step-down procedure on three tests; `analysis/statistics.py` `holm_adjust` implements the standard step-down rule, and pass 3 reproduced the adjusted values [0.005859375, 0.322265625, 0.005859375] independently. The statement does not depend on anything beyond the procedure's definition | None. Keep the JSTOR URL; do not add the OpenAlex DOI |
| Kamol, Lopez, Nowmi, Rivas, Haque, Raff, Piplai, and Rahman 2026, McNdroid | DOI `10.48550/arXiv.2605.06894` redirects to `https://arxiv.org/abs/2605.06894` (HTTP 302, then 200). Chapter correctly marks the work as a preprint | Preprint, 7 May 2026, 28 pages | `Kamol2026-McNdroid.pdf`, SHA-256 `a61619af595c8b97f0eeebb93488daff78c387d1060922731d05c36539f8da14` | `https://arxiv.org/pdf/2605.06894` | Read. Static manifests and smali, dynamic sandbox reports, function-call graphs; 2013–2025 excluding 2015 | Supported | None |
| Li, Sahu, Zaheer, Sanjabi, Talwalkar, and Smith 2020, FedProx | Proceedings URL in the chapter. Volume 2, pp. 429–450 is consistent with the 22-page PDF. Editor names were not printed on the extracted PDF pages | MLSys 2020 | `Li2020-FedProx.pdf`, SHA-256 `2c9e1c1ec91fc22dd8f04e52d9641a8797cdb82100936fceb63261f444194df8` | `https://proceedings.mlsys.org/paper_files/paper/2020/file/1f5fe83998a09396ebe6477d9475ba0c-Paper.pdf` (linked from the official proceedings page, verified pass 4) | Read. Proximal term as a generalization of FedAvg for heterogeneous networks | Supported | None |
| Mariconti, Onwuzurike, Andriotis, De Cristofaro, Ross, and Stringhini 2017, MaMaDroid | DOI `10.14722/ndss.2017.23353` | NDSS 2017 version of record. An arXiv v3 file was also saved and is not the cited version | Cited file: `Mariconti2017-MaMaDroid-ndss.pdf`, 15 pages, SHA-256 `91eba5927a1bc8d1f7663675f6d3c86f71316b923a29cb61d7e683e17242ef61`. Extra preprint: `Mariconti2017-MaMaDroid-arxiv.pdf`, 16 pages, SHA-256 `e5d14165d74aaf9b8e0e51281cc840d34342c8a050cd5d960f23e0a758d7f6a3` | NDSS `https://www.ndss-symposium.org/wp-content/uploads/2017/09/ndss2017_03B-3_Mariconti_paper.pdf` | Read. Markov chains on abstracted API calls, packages or families, aimed at API evolution | Supported. The chapter correctly separates API-family abstraction from malware-family withholding | None |
| McMahan, Moore, Ramage, Hampson, and Agüera y Arcas 2017 | PMLR volume 54. The PDF states volume 54 and lists all five authors, including Blaise Agüera y Arcas. Page span 1273–1282 matches the 10-page PDF. Editors Singh and Zhu were not re-read from the proceedings front matter | AISTATS 2017 | `McMahan2017-FedAvg.pdf`, SHA-256 `a7a8e2e3e437855c1efb53fe8f35f645eae7735fe9b6ac1f656a62004dbf5146` | `https://proceedings.mlr.press/v54/mcmahan17a/mcmahan17a.pdf` | Read. Iterative averaging of locally trained deep models | Supported | None |
| Ongun, Boboila, Oprea, Eliassi-Rad, Hiser, and Davidson 2025, CELEST | DOI `10.1109/TIFS.2025.3614442`. IEEE TIFS volume 20, pp. 10434–10448. Unpaywall OA location is the submitted arXiv version, not the journal PDF. Crossref gives Davidson as "Jack" without the middle initial the chapter includes | Published. Local file is arXiv:2205.11459v3, 17 March 2023, 15 pages | `Ongun2025-CELEST-arxiv.pdf`, SHA-256 `6a852ab2201fda686db9360085143f49b45548e519eb98979560c04f2ff0d2e7` | `https://arxiv.org/pdf/2205.11459` | Read. Section "Federated Models vs Local Models": a malware family previously detected in a collaborating network and seen locally for the first time. Table III. Active learning and DTrust poisoning defense are separate sections | The chapter's sentence is supported by this preprint. The journal PDF was not compared | None required unless the IEEE PDF is later found to differ. Do not describe the local file as the TIFS version of record |
| Pendlebury, Pierazzi, Jordaney, Kinder, and Cavallaro 2019, TESSERACT | USENIX URL in the chapter. Printed pages 729–746 | USENIX Security 2019 | `Pendlebury2019-TESSERACT.pdf`, 19 pages, SHA-256 `ec4de197f52e024d6e55a109053204ff1fe936dff11ab06ed01fa75f1d169218` | `https://www.usenix.org/system/files/sec19-pendlebury.pdf` | Read. Spatial and temporal bias | Supported | None |
| Sebastián and Caballero 2020, AVClass2 | DOI `10.1145/3427228.3427261`. ACSAC, pp. 42–53. Crossref stylizes the title "AVclass2"; the PDF and the chapter use AVClass2 | Published. Local file is arXiv:2006.10615v2, 28 October 2020, author manuscript, 12 pages, which matches the page span | `Sebastian2020-AVClass2-arxiv.pdf`, SHA-256 `73bea89b20207566db2b9752448b7f76f1915035f8a54afa7260ccd605e12c9f` | `https://arxiv.org/pdf/2006.10615` | Read. Taxonomy and rules for noisy AV labels; family tags are not independently verified behaviors | Supported | None. ACM VoR not downloaded |

### Recommended additions

These are not cited in the chapter. Their PDFs are in the same directory and are listed here so they are not confused with the cited set.

| Work | Identifier | PDF | Where it belongs | What it would support or challenge |
|---|---|---|---|---|
| Gálvez, Moonsamy, and Diaz 2021, Less is More, PoPETs 2021(4):96–116 | DOI `10.2478/popets-2021-0062`. SHA-256 `5e9a83337cf8548cb1ed690943db69ccea7ff9139c1cf41a6b527c0184a243aa`, 21 pages, version of record from `https://petsymposium.org/popets/2021/popets-2021-0062.pdf` | `Galvez2021-LiM.pdf` | Related work, after the Android FL paragraph | Supports the claim that prior Android FL detection estimates collaborative-versus-local performance and studies privacy and poisoning. It challenges a related-work section that skips that literature. It does not implement CTK's three arms. See CTK-AUDIT-009 |
| Patel, Tomar, Pateriya, and Haripriya 2026, FL-MalDrift, Scientific Reports 16, article 1821 (pass 3: the PDF prints "(2026) 16:1821"; cite as 2026; the local filename keeps the earlier "2025" label and is unchanged to preserve idempotence) | DOI `10.1038/s41598-025-31592-z`. SHA-256 `5ef9999384e32e7c3ca6fae08e9db7b89bc1543cd03966f99d71c8a7605a5c0e`, 26 pages, open-access publisher PDF | `Patel2025-FL-MalDrift.pdf` | Related work and the paragraph on non-chronological splits | Supports the chapter's limit that grouped random partitions are not forward-in-time evaluation, by giving a 2025 chronological AndroZoo FL comparison. It does not estimate CTK. See CTK-AUDIT-009 |
| Shen, Yang, Chu, Fan, Niyato, and Lam 2024, FLEKD-IDS, ICC 2024, pp. 2034–2039 | DOI `10.1109/ICC51166.2024.10622262` (Crossref). Local file arXiv:2401.11968v1, 6 pages, SHA-256 `4c501c8c617938d7979375e78816cc7f8506a4c554a5c5b7ba07d0584c73888a`. Preprint, not the IEEE VoR | `Shen2024-FLEKD-IDS-arxiv.pdf` | New paragraph after CyberForce (CTK-AUDIT-009) | Supports "collaboration recovers a class a client lacks": each of seven CICIDS2019 clients drops one attack class (Table IV) and local models detect it at 0%. Partial collision in the authors' own matrix. Challenges a two-citation synthesis; does not challenge the matched decomposition |
| Shao, Otani, Yamakawa, Hirasuka, and Wai Shiang 2026, IEICE Trans. Fundamentals (fifth author APA form "Wai Shiang, C.", pass 3) | DOI `10.1587/transfun.2026EAP1060` (Crossref; advance publication 2026-06-05; no volume yet). J-STAGE PDF, 11 pages, SHA-256 `438b8cbd16e397b9f30470344f3b309ef995d1af2e6c1c883e7fd33fb41840ed`. Advance-publication version, "content is final" | `Shao2026-MissingClassSupport-jstage.pdf` | Same paragraph; also the discussion of why aggregate metrics can hide hidden-family losses | Supports the chapter's argument that convergence and aggregate metrics can mask missing-class failure; provides a theoretical bias result. Borderline partial collision. Fifth-author surname resolved in pass 3 |
| Popoola, Ande, Adebisi, Gui, Hammoudeh, and Jogunola 2022, IEEE IoT Journal 9(5), 3930–3944 | DOI `10.1109/JIOT.2021.3100755`. Accepted manuscript from the MMU repository (figshare file 65029392), 15 pages, SHA-256 `fe0db81dd6bfb76152a011e1b43a9db13e7ad5ae36906745e11c85cf0bcd4e76`. In Copyright; saved for verification only | `Popoola2022-FDL-ZeroDay-aam.pdf` | Same paragraph | The widely cited "zero-day" federated paper: one class omitted per edge device; FDL compared with centralized, localized, and distributed DL. A reviewer searching "zero-day federated" will find it first. Does not identify class-specific local-versus-federated transfer |
| Bi, Li, Feng, and Mi 2024, arXiv:2404.05130 | arXiv identifier; no journal version found in Crossref. 21 pages, SHA-256 `9dc1092828ce527e9de269386b8c070b7c1d5c64ffda7e06da2f4fdaf41d324c` | `Bi2024-FL-CyberThreat-arxiv.pdf` | Optional: Android sentence in the same paragraph, or the discussion paragraph beginning "Aggregate discrimination and unseen-family recall answer different evaluation questions" | Android FL with k of 133 Drebin families per client; "no obvious pattern observed for the model performance" with aggregate metrics. Supports the chapter's claim that aggregate metrics can miss family exposure effects. Preprint only |
| Ishfaq, Shah, Saleem, and Afzal 2026, PLOS One 21(1), e0339907 | DOI `10.1371/journal.pone.0339907`. Publisher PDF (open access), 27 pages, SHA-256 `b74a196a43f8958933955ac36978b3f45bbebb4ada8076b6c88ceb98fba567d9` | `Ishfaq2026-ZeroDay-FedEnsemble.pdf` | Optional | Federated ensemble for Windows malware images with families excluded from every node (zero-day experiment, leave-one-family-out 94.6 ± 0.4% detection). An absent-everywhere number without a peer-present arm. Cite only if the "zero-day" vocabulary is used; the authors' matrix notes internal inconsistencies in node counts |

Pass 2 added FLEKD-IDS, Shao et al., and Popoola et al. as recommended citations because the authors' own literature matrix (`docs/Research Evidence.md` §29) classifies the first two as partial collisions and the third as the closest "zero-day" omitted-class design. Bi et al. and Ishfaq et al. are optional. A pass-2 extended web search (2026-10-20) for federated Android unseen-family work found Droidware (Engineering Applications of AI, 2026), FLANdroid, and a KIISC 2026 heterogeneity paper; none of their accessible descriptions reports held-out-family evaluation, and they were not downloaded. Popoola's file is an In Copyright accepted manuscript publicly deposited by the authors' institution; it is stored for verification and should not be redistributed with the chapter.

No other 2023–2026 paper examined in either pass was close enough to require a citation. DroidTTP and collusion-dataset papers address different tasks. Adding them would pad the bibliography.

## I. AI-Writing and Similarity Audit

No Turnitin, iThenticate, or commercial similarity service was available. No GPTZero or other authorship detector was run. No similarity percentage is reported. No sentence is labeled as machine-generated. The writing notes below are editorial. The similarity notes are limited to the PDFs that were read.

**Writing-quality problems.** CTK-AUDIT-018, 019, 020, 032, and 033 quote the passages and give replacements. The pattern is repetition of a true qualification: "not a deployment," "not a theoretical ceiling," "not independently confirmatory." Each phrase is accurate somewhere. Repeating all three in the introduction, the results, the discussion, and the conclusion makes a stable result sound provisional. Keep each qualification in the section that defines it. The abstract is dense and numerically accurate; it should not be expanded with more caveats.

**Potential similarity.** Definitions of FedAvg, FedProx, DREBIN, MaMaDroid, AVClass2, TESSERACT, and Holm are paraphrases placed next to the citation. They use standard technical terms (federated averaging, proximal term, static features, Markov chain, spatial and temporal bias, sequentially rejective). No extended unattributed passage from the read PDFs was found. Pass 2 extended the comparison to AndroZoo and Ciaramella, and to the five recommended additions; no extended unattributed passage was found. Coverage limit: Holm was unavailable during the earlier similarity review (its full text was read in pass 4), and CyberForce, CELEST, LAMDA, and AVClass2 were compared to preprints or author manuscripts rather than every journal version of record. Pass 4 added a local exact-overlap check: after case-folding, tokenizing words, and joining line-break hyphenation, no sequence of ten consecutive normalized words was shared between the main chapter text (11,822 normalized tokens, excluding references and key terms) and any of the 21 retained PDFs or the temporary Holm scan. These 22 files represent 21 distinct cited/recommended works. This checks the accessible extracted text, not close paraphrase, figures, inaccessible versions, or an external plagiarism corpus. IGI requires at least 80% new material and no more than 200 consecutive words repeated verbatim; nothing found approaches either limit, but only a publisher-side similarity check can confirm that.

**Confirmed attribution or citation errors.** None that change a scientific claim. CTK-AUDIT-012 is resolved: the Ciaramella sentences are supported. CTK-AUDIT-016 (an accent) was withdrawn in pass 2 because APA initials carry no accent. CTK-AUDIT-009 is an omission, not a misquotation.

**Automated-tool observations.** The bounded local word-sequence comparison above found no ten-word exact match; no proprietary similarity or authorship detector was used. The absence of a detector score is not evidence about authorship. Disclosure of AI assistance is a policy question, not a stylistic one, and is handled in CTK-AUDIT-028.

**Self-plagiarism.** The reference list does not cite an earlier CTK-Android paper. A web search on 2026-10-20 did not find a prior paper with this title or this decomposition. That search is not a corpus comparison. Figures 1–5 are original schematics and plots of this study's numbers. They do not reproduce a copyrighted figure from the cited papers.

## J. Results and Statistical Audit

### Headline confirmatory recomputation

Source: `results/evidence/arm-metrics.parquet`. Filter: experiment controlled-exposure, salt 0, alpha 0.05, metric federation unseen-family recall, learner FedAvg, seeds 100–109. Pairing is within seed. BCa uses SciPy `stats.bootstrap`, method BCa, 9,999 resamples, `numpy` Generator seed 20260924, matching `analysis/statistics.py` and `configs/statistics.yaml`. Wilcoxon uses `method="exact"`. Holm orders the three raw p-values, applies multipliers 3, 2, and 1, and takes the cumulative maximum before restoring their order. CTK and total share the minimum attainable two-sided p for n = 10 with no ties and no zeros, `2/1024 = 0.001953125`; both adjust to 0.005859375, while pooling remains 0.322265625.

| Quantity | Recomputed | Chapter | Verdict |
|---|---|---|---|
| Peer recall | 0.643622 | 64.36% | Match |
| Absent recall | 0.524064 | 52.41% | Match |
| Local recall | 0.509013 | 50.90% | Match |
| Full-exposure FedAvg recall | 0.676353 | 67.64% | Match |
| CTK | 0.1195575610; CI [0.0915477400, 0.1520988052]; p 0.001953125; Holm 0.005859375; 10/10 | +11.96; 9.15–15.21; Holm .00586 | Match |
| Pooling | 0.0150512497; CI [−0.0414906894, 0.0609806470]; p 0.322265625; 7/10 | +1.51; −4.15 to 6.10; .32227 | Match |
| Total | 0.1346088107; CI [0.0881778015, 0.1704013706]; Holm 0.005859375; 10/10 | +13.46; 8.82–17.04 | Match |
| CTK + pooling − total | 0 | Identity stated | Match |
| Displayed 11.96 + 1.51 versus 13.46 | Rounding | — | CTK-AUDIT-001 |

Seed CTK effects in percentage points, seeds 100 through 109: 19.9948, 13.2151, 14.656, 7.3101, 9.3319, 18.6535, 8.854, 6.4651, 15.3876, 5.6896. One total-gain seed is about +0.58 points while CTK on that seed stays positive. The mean is pulled upward by the two largest seeds. Leave-one-seed-out means remain between 11.06 and 12.65 points (CTK-AUDIT-015).

Own-domain FedAvg: CTK 0.1085274487 (10.85, CI 6.97 to 15.25, 10/10); pooling −0.0759643270 (−7.60, CI −11.81 to −4.03, 1/10 positive); total 0.0325631217 (3.26, CI 1.26 to 5.63, 8/10). The own-domain total p-value 0.02734375 is outside the Holm family. The chapter says so.

Known-family peer minus local: FedAvg −0.0360542944 (−3.61, CI −4.50 to −2.85, 0/10); fine-tune −0.037375 (−3.74); FedProx −0.009280 (−0.93, CI excludes 0, mean inside the 2-point tolerance); central −0.001442 (−0.14, CI includes 0); blend +0.017050 (+1.70, 10/10). The chapter correctly says the tolerance flag is not an equivalence test.

Other recomputed confirmatory quantities are in the claim matrix: family-macro, worst-client, alpha 0.01, AUROC, AUPRC, learner gap, Table 5 sensitivities, salts, and the original permutation. Stored `paired-effects.parquet` matched these recomputations at printed precision.

Wilcoxon with n = 10 cannot produce a two-sided exact p below 0.001953125. The chapter's Holm p of .00586 is three times that floor. BCa and the signed-rank test answer different questions. The chapter says so. The three headline contrasts have no zero differences and no absolute-rank ties, so the exact method is valid for Table 3. Pass 2 checked zeros and ties for every secondary confirmatory contrast it recomputed (own-domain, family-macro, worst-client, micro, known-family for five learners, AUROC, AUPRC, FedProx minus FedAvg, both alternative alphas, CTK for five learners, eight Table 5 sensitivities, the original permutation in both populations, and three salts): none has a zero difference or a tied absolute rank, so `method="exact"` is valid for all of them.

Ten seeds are enough to show that the primary federation-wide CTK interval lies entirely above the prespecified three-point threshold and that every seed is positive. They are not enough for precise client or family rankings. The chapter already limits play-late to six contributing seeds and Anzhi to eight. More seeds are not required to defend the primary claim.

### Extension and diagnostic checks

Pass 1 read these intervals from frozen CSVs. Pass 2 re-bootstrapped every alpha-0.05 dose, placebo, and robust-aggregation row from `exact-dose-seed-effects.csv` and `controls-seed-effects.csv` (42 control rows and 24 FedAvg federation-wide dose rows); means and BCa endpoints agree with the stored effect files to the fifth decimal. Stored dose p-values are one-sided (`alternative = greater`), which is why they are half the two-sided values.

- Exact dose, pooled family sets, FedAvg, federation-wide, alpha 0.05, contrast `ctk-at-dose`: 10 → 0.02923 [0.02310, 0.03638]; 25 → 0.04903 [0.03872, 0.05889]; 50 → 0.07827; 100 → 0.12478; 200 → 0.14487. All 10/10. Increment 50 to 100: 0.04651 [0.02434, 0.07093], 9/10. Increment 100 to 200: 0.02008 [−0.000589, 0.04060], 7/10. The chapter separates a positive effect from an effect whose interval lies above 3 points. The 10-example interval crosses 3 points. The 25-example interval lies above it.
- Central exact-dose means on Figure 5: 0.04116, 0.06855, 0.10738, 0.13336, 0.17951. The prose reports FedAvg. The figure's central curve is consistent with the CSV. The prose does not need a new claim about central dose unless the authors want one.
- Placebo and robust aggregation: see the claim matrix. Class D. Not a poisoning test.
- Representation and equal-FPR rows: see the claim matrix. Equal-FPR uses benign test scores and is labeled post hoc. The chapter says so.
- Spearman: manuscript matches `large-family-summary.csv` and reproduces exactly under the frozen routine (pass 3); other files resample in a different order. CTK-AUDIT-003.
- Permutation extension evidence-class string: CTK-AUDIT-011.

### Pass-2 additional computations from existing artifacts

All values below were computed in pass 2 with scripts kept outside the repository. No training was run.

**Independent recomputation of the confirmatory block.** An independent script (Polars plus SciPy, not importing `ctk_android.analysis`) reproduced every Table 3, Table 4, Table 5, own-domain, family-macro, worst-client, known-family, AUROC, AUPRC, salt, alpha-0.01, FedProx-minus-FedAvg, permutation, and FPR value in the chapter to the printed precision. Seed CTK effects and leave-one-seed-out means (11.06 to 12.65) match pass 1.

**Weightings of the primary contrast (CTK-AUDIT-021).** Client-macro 11.96 (9.15, 15.21); family-macro 12.44 (10.09, 15.55); micro-pooled 6.58 (4.64, 8.65); all 10/10. Pooling: 1.51, −1.87, and 4.00. Worst-client pooling −3.62 (−10.87, −0.55), 2/10 positive, which the chapter does not report and need not.

**Other learners and operating points (CTK-AUDIT-025).** CTK central 13.10, FedProx 13.20, fine-tune 8.20, blend 7.60, all 10/10; FedAvg 13.78 at alpha 0.10.

**New versus overlapping expanded families (CTK-AUDIT-022).** 14 of 32 overlap the primary or replication sets. Seed-level family-macro CTK: new 3.47 (2.45, 4.45), overlapping 10.67 (9.25, 12.84), both 10/10. Family-level means: 3.22 and 10.75. Twenty of 32 families have CTK ≥ 3 points; three have CTK ≤ −3 points (feiwo, baiduprotect, umpay; umpay has 2 seeds).

**Dose by family set (CTK-AUDIT-023).** Increment 100→200: primary +4.23 (2.53, 6.55), replication +0.03 (−3.91, 2.54), pooled +2.01 (−0.06, 4.06).

**Placebo by population and set.** Placebo minus absent, own-domain, pooled: −1.14 (−2.05, −0.34); replication set −2.12 (−4.13, −0.17). The wrong family slightly lowers own-domain recall instead of raising it. CTK minus placebo is positive in every scope: pooled 10.04 federation-wide and 8.33 own-domain; primary 14.45 and 10.85; replication 5.82 and 5.62. The chapter's placebo description is accurate; the own-domain row is an optional addition.

**Robust aggregation by set.** Replication-set trimmed-mean CTK 4.69 (2.21, 6.88): positive in sign but its lower bound is below 3 points. Median aggregation raises replication-set CTK to 12.52 (9.91, 15.84). The chapter's "survives these alternative aggregation rules" is accurate for the sign.

**Per-client own-domain decomposition (CTK-AUDIT-024).** See the table in that finding.

**Partition selection margin (CTK-AUDIT-031).** See Section B.

**Exposure size.** Mean 2,073 of 24,000 FedAvg fit rows differ between peer-present and absent-everywhere (Section B).

### What the negative results mean

Known-family loss and negative own-domain pooling qualify the decision to deploy FedAvg. They are not evidence that the federation-wide CTK contrast failed. Negative families show heterogeneity inside a positive average. Permutation and placebo are negative controls that make the positive CTK more specific. Report-JSON and the FPR tail show that the operating point and the representation matter. AUROC and average precision fall because they score the whole own-domain test distribution, not the hidden-family recall at one threshold. The chapter's distinction is correct and should stay.

### Causal alternatives

| Alternative | Status | Evidence |
|---|---|---|
| Extra training volume | Ruled out for the within-learner CTK contrast | `select_training` caps every client at the same budget. CTK compares two collaborative arms with the same schedule |
| FedAvg versus local optimization schedule | Ruled out for CTK; applies to pooling and total | Chapter states 20×2 versus 10 local epochs. Pooling's interval includes zero on the federation-wide metric and is negative on own-domain |
| Own-sample composition and replacement identity | Largely addressed (Class D) | Figure 1 and `design.py`. The primary CTK contrast includes a change of about 2,073 of 24,000 fit rows. The placebo reproduces that change in count and client location with an unselected family and recovers almost none of the gain (−0.54 points; CTK minus placebo +10.04). Residual: placebo families are matched on support, not behaviour. CTK-AUDIT-002 |
| Calibration differences | Part of the stated intervention | Each arm is calibrated on its own benign calibration scores. Mean realized FPR is near 5%. The worst-client tail is reported |
| Simultaneous families | Disclosed | Chapter and code. Family-level CTK is conditional on the other families in the same run |
| Target-selection and support-rich partitions | Disclosed; quantified in pass 2; not outcome-based | `build_partition` scores eligibility counts only. Re-execution: chosen attempt has about 9% more eligible pairs than the median attempt; all 160 candidates had at least 48 |
| One seed, one client, or one family | Not the source of the sign | 10/10 seeds, minimum seed about +5.69 points, leave-one-seed-out means above 11 points. Play-late's large client mean uses 6 seeds and is already described as conditional |
| Family-label noise | Partly addressed | Permutation reduces the effect to about zero on the federation-wide metric. Own-domain original permutation remains unresolved, as the chapter says |
| Support-ranked family selection inflates magnitude | Real, partly quantified | Replication set 5.08; new expanded families 3.47; both positive in most or all seeds. The sign generalizes; the 11.96-point magnitude is specific to the primary set. CTK-AUDIT-022 |
| Client-macro weighting inflates magnitude | Real, quantified | Micro-pooled CTK 6.58 (4.64, 8.65), 10/10. CTK-AUDIT-021 |
| Aggregation dominated by large clients | Not applicable | Weights equal: every client has 6,000 fit rows. CTK-AUDIT-030 |
| Rerun selection (executing until results look good) | Not supported by the record | Three executions of one configuration fingerprint gave 0.117, 0.117, 0.1196; reruns were for determinism fixes. CTK-AUDIT-026 |

## K. Three Reviewer Reports

These are simulated reviews grounded in the artifacts above. They are not editorial decisions.

### Reviewer 1 — Novelty and scientific contribution

The manuscript's best claim is methodological and empirical: a matched-budget decomposition of unseen-family recall for Android malware detection. That claim survives the two closest papers I can read.

CyberForce (arXiv v4, with the IEEE TDSC header) does vary the share of clients missing a malware type from 10% to 100%, plots local models, and compares FedAvg, Krum, and trimmed mean. The chapter says this and correctly limits the overlap. CyberForce selects moving-target defenses for IoT malware. It does not estimate Android recall at a client-calibrated FPR under a matched training budget. The chapter should keep that paragraph. Its reference entry is correct.

CELEST (arXiv v3) does evaluate a malware family seen for the first time in one network after another network has trained on it, and it reports active learning and a poisoning defense. The chapter's citation of that result is accurate. CELEST does not include an absent-everywhere arm with a matched budget. The chapter says it adds that arm. That sentence can stand.

The related-work gap is larger than two Android papers. The authors' own matrix lists FLEKD-IDS (each of seven clients drops one attack class; local models detect it at 0%, federated models detect it) and Shao et al. (2026; missing class support induces an irreducible bias) as partial collisions, and Popoola et al. (2022) is the paper a reviewer finds first under "zero-day federated". LiM and FL-MalDrift are the Android FL detectors. None preempts the matched decomposition; all of them should be cited so the distinction is explicit (CTK-AUDIT-009). Note that FLEKD-IDS's 0% local recall is a consequence of multiclass label absence; in CTK-Android's binary task the local model already detects 50.90% of hidden-family malware, which is why a pooling arm is needed at all. That contrast is a good sentence for the chapter.

I would not ask the authors to invent a new optimizer. The manuscript already refuses that claim. I would ask them to put the placebo and the dose curve next to the primary result, labeled as extensions (CTK-AUDIT-010).

**Likely objection.** "This is ordinary federated learning on a malware dataset."

**Response.** Ordinary FedAvg-versus-local comparisons change volume, benign mix, family exposure, and the optimization schedule together. CTK holds the collaborative schedule and the client budgets fixed and still finds +11.96 points, while the volume-and-schedule pooling term is +1.51 points with an interval that includes zero. LiM and FL-MalDrift are the ordinary comparisons. CELEST and CyberForce study missing threats without this decomposition.

### Reviewer 2 — Methodology and statistical validity

I checked the exclusion code, the budget cap, the FedAvg weights, the FedProx penalty, the calibration quantile, the 16-attempt partition score, and the primary arithmetic. They match the chapter. The headline interval lies above the prespecified 3-point margin, every seed is positive, and leave-one-seed-out means stay above 11 points. I would not require more seeds for the primary claim.

The serious interpretation point is already half-answered. Absent-everywhere removes every selected family from every client, so the target's own fit sample loses families assigned to other targets. Figure 1 says this. The results paragraph should say that the 11.96-point number includes that change (about 2,073 of 24,000 fit rows), and should point to the placebo, which substitutes the same total count of malware rows from a wrong family, with support-dependent allocation across peers, and recovers almost none of the gain (CTK-AUDIT-002). I do not think this invalidates the contrast. I think the current shorthand is cleaner than the design.

Pooling is not a pure data-volume effect, because local training uses 10 epochs and FedAvg uses 20 rounds of 2 local epochs. The chapter says this. The interval on federation-wide pooling includes zero. Own-domain pooling is negative. Those statements should stay.

The 16-attempt rule uses eligibility counts, not test recall. The attempt index is stored in the partition manifests, and re-execution shows the chosen partition has about 9% more eligible pairs than the median candidate. That is evidence of support-based feasibility selection rather than direct selection on model performance; representativeness on other characteristics remains conditional (CTK-AUDIT-031).

The support-rich family rule favors families with at least 600 applications in at least two clients. The chapter says the primary set is not a random sample of the taxonomy. Natural-scarcity and the replication set are the existing answers. Natural-scarcity CTK remains about +11.2 points. Replication CTK is +5.08 points with an interval that crosses 3 points. That is a narrower, still positive, generalization claim. It should not be described as identical to the primary result.

Leakage controls I could verify do not show a test-set selection or a fit/test identity crossing. I did not re-derive every near-duplicate path beyond the package-or-identical-vector components. Package-only grouping still shows a positive CTK. Shared-library near-duplicates that are not identical vectors remain a residual risk the chapter should keep in the limitations, which it does in substance by refusing to treat labels and features as pure family mechanisms.

The exact Wilcoxon calls are valid for the three headline contrasts because those differences have no ties. I would not let the manuscript say that every secondary p-value in the repository is exact under ties. The chapter does not make that blanket claim. The broader pass-4 scan found 26 secondary groups with zeros or tied absolute ranks; exhaustive sign enumeration matches 25 stored p-values and identifies one small discrepancy (CTK-AUDIT-035).

My main new objection is magnitude, not sign. The headline weights clients equally; weighting hidden-family test applications equally gives 6.58 points. The primary families were chosen by support rank; on the 18 expanded families the study had never used, CTK is 3.47 points. Both are positive in all ten seeds, so they strengthen the existence claim. Both should be in the chapter, because I can compute them from the repository and I would ask why they are missing (CTK-AUDIT-021, 022).

FPR control is at the mean, with a disclosed worst-client tail and four extension tolerance failures. The equal-FPR diagnostic is post hoc and uses test benign scores. The chapter says so. I would not ask for a new calibration study before submission.

**Likely objection.** "The gain is replacement malware, not the family's presence at peers."

**Response.** The placebo starts from the absent-everywhere sample and substitutes the same total number of malware rows from an unselected family. It matches per-peer counts where feasible and reallocates when that family lacks support at a peer. It changes recall by −0.54 points. CTK minus placebo is +10.04 points, 10/10 extension seeds. The family permutation drives the original federation-wide effect to +0.30 points. Exact dose increases from 10 to 200 examples. These are extensions, except the original permutation, and they are the right answer to the objection. The primary contrast remains the composition-including estimand defined in Figure 1.

### Reviewer 3 — Presentation, relevance, and publication quality

The chapter is numerically careful and longer than it needs to be in the places where it repeats limitations. The introduction should state the result and one cost, then stop (CTK-AUDIT-018). The discussion should not restate Table 3 (CTK-AUDIT-019). The conclusion should add the placebo and the dose pattern (CTK-AUDIT-020).

Figures 1 through 5 are the right figures. Figure 2 is the paper. Figure 3's legend should say "mean across seeds" (CTK-AUDIT-013). Figure 4 should say that cells are rounded to two decimals (CTK-AUDIT-014). Figure 5 already shows the dose result more clearly than the prose. I would not add a sixth figure before submission.

Table 1 through Table 5 agree with the files I could recompute or match. The 0.01-point display sum is worth one clause (CTK-AUDIT-001).

For IGI Global, the identifying GitHub URL has to leave the review file (CTK-AUDIT-006). The word count is already above 10,000. This is a book-chapter compliance item, not a journal template. A journal that allows identified code can keep the URL. I would not impose a two-column layout until a journal is chosen.

Figure 1 shows one family. The design removes every selected family from every client in the absent-everywhere arm. The note should say so (CTK-AUDIT-029). The abstract ends on a scope sentence rather than a finding (CTK-AUDIT-032). If AI tools assisted the analysis or writing, IGI requires a disclosure statement above the references, and IGI asks that references not be added or formatted by AI (CTK-AUDIT-028).

Practical implications are appropriately modest. The discussion tells an organization to choose the loss it will accept and not to treat the federation-wide number as the own-domain number. That is the right operational sentence. Privacy and poisoning are correctly marked as untested.

**Likely objection.** "The writing is defensive, so the result must be fragile."

**Response.** The result's interval is 9.15 to 15.21 points, with 10 positive seeds. The defensive sentences repeat limitations that belong once. Edit repetition. Do not delete the known-family loss, the own-domain pooling loss, or the representation failures.

## L. Associate Editor Assessment

The central contribution is established for the population and operating point that were tested. The confirmatory FedAvg federation-wide CTK gain is numerically correct, positive in every seed, above the prespecified practical threshold at both ends of its interval, positive for every collaborative learner, unchanged in sign under sample weighting, and stable across three executions of a configuration that is verifiably unchanged since its freeze. The paper is unusual in also showing where that gain shrinks or reverses. Those negative results are a reason to trust the paper. They should remain.

No correctness issue requires a new experiment before submission. The changes that most affect a reviewer's decision are textual or use numbers already computed:

1. Cite FLEKD-IDS, Shao et al., Popoola et al., LiM, and FL-MalDrift as neighbouring questions, not as failed versions of CTK (CTK-AUDIT-009).
2. Report the 6.58-point sample-weighted CTK and the 3.47-point CTK on new expanded families as evidence that the sign generalizes and the magnitude is family-set dependent (CTK-AUDIT-021, 022).
3. Point the 11.96-point sentence back to Figure 1 and to the placebo, and fix the Figure 1 note (CTK-AUDIT-002, 010, 029).
4. For IGI: remove the identifying URL from the review copy (CTK-AUDIT-006), and add an AI-use statement if AI assisted the work, entering references by hand (CTK-AUDIT-028).

Objections that are already answered, and that a response letter can quote rather than appease with new runs: the FedAvg-versus-local schedule confound of pooling; the eligibility-based partition search (now quantified); the ten-seed limit for the primary sign; aggregation dominated by large clients (weights are equal); rerunning until results improved (three executions, same answer); the absence of a privacy proof; the absence of a poisoning attack; the non-chronological split. FL-MalDrift is the citation that makes the last one scholarly rather than merely modest.

I would not ask the authors to weaken the 11.96-point claim. I would ask them to define it once, in the words Figure 1 already uses, to show the two other weightings beside it, and to let the placebo and the dose curve sit beside it as extensions.

## M. Prioritized Improvement Roadmap

| Rank | ID | Action | Requirement | Why this rank |
|---|---|---|---|---|
| 1 | CTK-AUDIT-009 | Add the neighbour paragraph and the external-validity clause | TEXT ONLY | Most likely novelty objection. PDFs are local. Enter references by hand (028) |
| 2 | CTK-AUDIT-021, 022 | Report micro-pooled CTK and new-family CTK | EXISTING DATA (computed) | The numbers a sceptical reviewer will compute first; both are favourable in sign |
| 3 | CTK-AUDIT-028 | Decide on and, if applicable, add the AI-use statement | TEXT ONLY | Desk-rejection risk under IGI policy; only the author knows the facts |
| 4 | CTK-AUDIT-002, 010, 029 | Composition sentence, placebo/dose bridge, Figure 1 note | TEXT ONLY | Makes the estimand and the specificity evidence hard to miss |
| 5 | CTK-AUDIT-006 | Anonymize the repository URL in an IGI review copy only | TEXT ONLY | Procedural, venue-specific |
| 6 | CTK-AUDIT-025, 023, 024 | CTK for all learners and alpha 0.10; dose by set; per-client own-domain totals | EXISTING DATA (computed) | Adds favourable and qualifying evidence in proportion |
| 7 | CTK-AUDIT-015, 031 | Leave-one-seed-out range; partition margin | EXISTING DATA (computed) | Cheap answers to "one seed" and "best of 16" |
| 8 | CTK-AUDIT-018, 019, 020, 032, 033 | Shorten repeated qualifications; sharpen the abstract close | TEXT ONLY | Frees words for items 2 and 6; keep every negative number |
| 9 | CTK-AUDIT-026, 027 | One provenance sentence in the chapter; mark superseded docs and preserve the freeze commit in the repository | TEXT ONLY (chapter); repository action by the author | Traceability; not a scientific defect |
| 10 | CTK-AUDIT-003, 011 | Name the Spearman source file and the permutation seed block | TEXT ONLY | Traceability for replicators |
| 11 | CTK-AUDIT-001, 013, 014, 030 | Rounding clause, Figure 3 legend, Figure 4 caption, equal FedAvg weights | TEXT ONLY | Local presentation |
| 11a | CTK-AUDIT-035, 036 | Correct one secondary p-value in separately authorized artifact maintenance; optionally add figure alternative text | EXISTING DATA; OPTIONAL | Neither changes a principal result or requires training |
| 12 | CTK-AUDIT-012, 016 and closed items below | Do not change | NO ACTION | Investigated and resolved |
| 13 | Chronological split, poisoning, privacy accountant, more seeds, external corpus | Do not start before submission | NEW EXPERIMENT, OPTIONAL | The chapter already limits its claim. New runs need separate authorization |

**Investigated and closed, not defects.**

- Headline arithmetic, Holm scope, and exact Wilcoxon validity for the three primary contrasts (no zeros, no ties). NO ACTION. The expanded secondary scan has the limited exception in CTK-AUDIT-035.
- Extension BCa intervals for dose, placebo, and robust aggregation: reproduce exactly. NO ACTION.
- Confirmatory configuration unchanged since the freeze commit; core exposure and calibration functions textually unchanged. NO ACTION (preservation of the commit is CTK-AUDIT-027).
- Representation overlap counts, the r0/r1/r2/r3 map, and the priority-macro and family representation effects (re-read in pass 2). NO ACTION.
- CyberForce, CELEST, Ciaramella, AndroZoo descriptions, and the CyberForce author list (pass-1 accent finding withdrawn). NO ACTION.
- frmy as a candidate that is not one of the seven eligible controlled families. NO ACTION.
- Support-based selection among 16 partition attempts: reproduced, margin about 9%. NO ACTION beyond optional CTK-AUDIT-031.
- Manifest digests 90/90; tests 476 passed, 0 failed. NO ACTION.
- Linkage audit (1,008,381 matched, 0 unmatched, unique links, VirusTotal counts agree) and the binarization of 6 non-binary cells. NO ACTION.
- Negative results. NO ACTION other than not hiding them.
- PyTorch even-length median. Code and unit test (`test_coordinate_median_is_robust_to_a_single_outlier_and_takes_the_lower_middle`) match the chapter. NO ACTION.

**Optional existing-data analysis.** No proposed training analysis is required. The Spearman re-bootstrap was completed in pass 3 and the equal-FPR diagnostic in pass 4. CTK-AUDIT-035 documents one secondary-artifact p-value correction; it needs no training and changes no manuscript number.

## N. Final Verification and Audit Coverage

**Files inspected.** Pass 1: the full chapter text from `chapter/CTK-Android_Chapter.docx` (equations read from OMML); Figures 1–5; the four configs; `analysis/statistics.py`, `analysis/decomposition.py`, `experiment/training.py`, `experiment/models.py`, `experiment/design.py`, `experiment/evaluation.py`, `data/partitions.py`, `data/preparation.py`, `enums.py`, `paths.py`; the result, extension, provenance, and preprocessing files listed in the claim matrix. Pass 2 additionally: the chapter re-extracted and read in full (complete text including table rows; pass 4 standardized the count to 11,043 whitespace-separated words before References and 11,766 across all body paragraphs, table cells, equations, references, and key terms; abstract 126 words; counts depend on tokenization and are not Word’s native counter); `docs/decisions/protocol-amendments.md`, `docs/decisions/implementation-decisions.md`, `docs/temp/extension-protocol/FREEZE.md`, `docs/results.md` (header and Appendix A.1), `docs/Research Evidence.md` §29, `docs/temp/lit/` notes on Shao/Otani, Bi, Ciaramella, and `docs/technical_docs.md` §47; `config.py` fingerprint functions; `experiment/design.py` placebo construction; `outputs/preprocessing/partitions/*/manifest.json` (123 partitions); `outputs/preprocessing/source-audit/linkage/audit.json`; `outputs/runs/confirmatory/controlled-exposure/seed-10x/{exposure.parquet,manifest.json,validation.json}`; `results/extension-b/{controls,exact-dose}-seed-effects.csv`, `large-family-ctk.csv`, `large-family-seed-ctk.csv`, `large-family-summary.csv`, `representation-effects.csv`; `results/tables/client-ctk-analysis.csv`; `results/provenance/{protocol,source-data,environment,run-provenance}.json`; git objects `e079972`, `dccf996`, `1da371a`.

**Results verified by recomputation.** Pass 1 and pass 2: the five headline figures, BCa intervals, exact p-values, Holm adjustment, positive-seed counts, identity, own-domain decomposition, known-family changes, AUROC and AUPRC, Table 4, Table 5, salts, alpha 0.01, original permutation, FPR means and maxima, Table 1 sums, leave-one-seed-out means. Pass 2 only: micro-pooled and family-macro decompositions, CTK for four further learners, alpha 0.10, extension dose/placebo/robust-aggregation intervals (re-bootstrapped), new-versus-overlapping expanded-family CTK, partition attempt scores, exposure row counts, tie and zero checks for all recomputed secondary contrasts.

**Results matched to frozen summaries and not re-bootstrapped.** No manuscript equal-FPR quantity remains in this category after pass 4. Pass 4 independently reconstructed all 840 target records from saved scores and all 72 equal-FPR effect means and BCa endpoints; maximum absolute error was 0. Pass 3 had already recomputed the representation effects, Spearman intervals, client-level table, extension permutation, and original dose supports.

**References checked.** All 14 cited works and 7 recommended additions. Metadata from Crossref, arXiv, publisher PDFs, J-STAGE, NDSS, USENIX, PMLR, MLSys, JSTOR, ORBilu, the MMU repository, and Unpaywall, as recorded in Section H.

**PDFs obtained.** 21 files in `chapter/references_pdf/`: 14 files for 13 cited works and 7 recommended additions. Pass 2 added 7 files and changed none of the 14 pass-1 files (all 14 SHA-256 values identical before and after pass 2). Each new file was opened with `pdfinfo` and `pdftotext`, and its first-page title and authors were checked against the citation. No duplicate content was found by hash.

**References unavailable as full text.** None among the 14 cited works after pass 4. Holm is not archived locally: a public institution-hosted scan was inspected in external scratch only, without assuming redistribution rights. Read as preprint or author manuscript rather than the version of record: CyberForce, CELEST, LAMDA, AVClass2, AndroZoo (submitted version), FLEKD-IDS, Popoola et al. (accepted manuscript), Bi et al. (preprint only).

**Tests or validations reviewed.** Pass 2 executed `pytest tests/unit tests/architecture tests/integration` in an isolated scratch copy (bytecode writing disabled; the repository's `outputs/`, `results/`, and `data/` were not linked into the copy): 472 passed, 14 skipped, 1 failed; the failure was `test_pyright_strict_passes`, which passed (4/4 static-analysis tests) once the copy could see the project virtual environment. Net: 476 passed, 14 skipped, 0 failed. `tests/e2e` was not run. Run-level validation records for seed 100 were read; all eight checks pass. `results/manifest.json`: 90/90 digests match. Pass 3 additionally ran, in a fresh scratch copy with the raw data and run directories linked read-only, `tests/architecture/test_source_schema.py` (3 passed against the real LAMDA and AndroZoo files) and `tests/e2e -k 'not smoke'` (9 passed); `outputs/` and `results/` were byte-identical afterwards. It also executed the logic of the skipped `test_frozen_hyperparameters_equal_the_selection_from_saved_development_evidence` read-only on the real development evidence: drift = []. All three results manifests verify: 90/90 (`results/`), 5/5 (`results/extension/`), 120/120 (`results/extension-b/`). Totals across passes: 488 tests passed and 0 failed. Thirteen were not run as tests: the 8 smoke tests and 3 report-workflow tests by design, the frozen-hyperparameter test (its logic was executed directly instead), and the smoke `--help` case, which the `not smoke` filter deselected.

**Checks not completed (after pass 4).** Re-execution of training or preprocessing from raw data, and therefore the hardware-independence of the documented determinism. The 8 smoke tests (7 integration, 1 end-to-end) and the 3 report-workflow tests, because the first train models and the second write into linked run directories. Line-by-line comparison against the versions of record listed in R-05 (blocked by bot challenges or paywalls, not circumvented). Commercial similarity and authorship detectors. A publisher-native word count. Full-page rendering and pagination, because the supplied renderer failed with `FileNotFoundError: LibreOffice soffice.exe was not found on PATH` and no bundled LibreOffice executable is available on this Windows host; structural checks do not prove the absence of clipping or page-break defects. Whether AI tools assisted the chapter (author knowledge).

**Open questions for the author.** R-01 to R-07 in Section O: the target venue, AI disclosure, preserving `e079972`, superseding the two stale documents, versions of record, restoring the URL in the camera-ready copy, and optional secondary-artifact maintenance. The Shao surname and the fingerprint mapping, open after pass 2, were resolved in pass 3.

**Repository integrity.** Before pass 2 began, SHA-256 values of all 372 tracked files, all 11,949 files under `results/` and `outputs/`, and the 14 existing reference PDFs were stored outside the repository. After pass 2: every tracked file except `chapter/audit.md` is byte-identical; every file under `results/` and `outputs/` is byte-identical; the 14 existing PDFs are identical and 7 PDFs were added; no file under `src/` or `tests/` is newer than the baseline. `git status --short` shows only ` M chapter/audit.md` and `?? chapter/references_pdf/`, as at the start. HEAD is still `6813f929968f141d3660ccfa28d37aaa0180d74f`. No commit, branch, tag, stash, or push was created. Scratch files (docx extraction, figure conversions, downloads, scripts, the test copy) were kept in the session scratch directory and deleted at the end of the pass. Pass 1 recorded restoring a pre-existing working-tree deletion of `chapter/verification.md` from HEAD; that file was present and unchanged throughout pass 2. Pass 3 repeated the check against a fresh baseline taken at its start: only `chapter/audit.md` changed among the 372 tracked files; all 11,949 files under `results/` and `outputs/` and all 21 reference PDFs are byte-identical; no file under `src/`, `tests/`, or `configs/` is newer than the baseline and no `__pycache__` was created; `git status --short` is unchanged; HEAD is still `6813f92…`; there are no stashes or tags. Pass-3 scratch files (git archives of five revisions, the test copy, downloads, scripts, and outputs) were deleted at the end.

**Remaining uncertainty.** Preprint-versus-version-of-record differences for the files listed above; whether the reported determinism holds on other hardware; final pagination and clipping in a native rendered document. None of these affects a recomputed CTK number.

### Pass-3 resolution of items left unconfirmed in pass 2

| Item (pass 2 status) | Pass-3 action | Outcome |
|---|---|---|
| Spearman intervals differ across files (CTK-AUDIT-003) | Re-ran `novelty_association` logic: family percentile bootstrap, 9,999 draws, seed 20260924, file order | Manuscript values reproduce exactly; other files differ by resampling order. Cause resolved |
| Freeze fingerprint 84ec9a19 versus evidence 8e2ecdf4 (CTK-AUDIT-027) | Loaded configs from `git archive` of five revisions; compared `run_fingerprint` with all 140 stored resolved configurations | Whole-config fingerprint changed only by extension additions; all 12 confirmatory run fingerprints identical to the freeze. Resolved |
| Skipped frozen-hyperparameter test | Ran its logic read-only on saved development evidence | Selection 10 / 2 / 0.1, drift [] . Resolved |
| Skipped source-schema tests; e2e not run | Ran in scratch copy | 12 passed. Resolved (smoke and report tests deliberately not run) |
| Representation, client table, original dose, extension permutation "matched CSV only" | Recomputed from seed-level or run-level files | All match exactly (108/108 representation rows; client table; effective doses; permutation). Resolved |
| Equal-FPR diagnostic | Not recomputed in pass 3; recomputed from saved scores in pass 4 | Resolved: 840 target cells and 72 effect rows exactly match; remains post hoc |
| Shao et al. fifth-author surname (CTK-AUDIT-009) | IEICE capitalization convention, ORCID 0000-0002-1647-6703, OpenAlex name variants | Family name "Wai Shiang"; APA "Wai Shiang, C." Resolved |
| FL-MalDrift year | Read PDF header | Scientific Reports 16:1821 (2026). Pass-2 "2025" corrected |
| LAMDA 925 versus 915 | Source audit and dataset variant table | 925 confirmed for the frozen release; 915 is a preprint-appendix inconsistency. Resolved |
| Holm full text and DOI | Pass 3 searched for archival copies; pass 4 inspected the public institution-hosted scan | Full text read; no redistributable PDF archived. DOI-resolution concern from pass 3 remains; keep the stable JSTOR URL |
| Versions of record (ACM, IEEE, OpenReview) | Script download, Unpaywall, arXiv versions | Blocked by bot challenges or paywalls; not circumvented. Remains open (R-05) |
| Bi et al. publication status | Crossref title search, arXiv | Preprint only. Resolved |
| Determinism on other hardware | Would require training | Not testable under the audit's constraints. Minimal procedure: rerun `ctk-android smoke` twice on a second GPU model and compare digests |
| AI assistance in the chapter | Not determinable from artifacts | Open (R-02) |

### Idempotence check (pass 3)

1. **Recomputation is deterministic.** A consolidated read-only script recomputed the audit's quantitative claims (headline decomposition for five weightings with BCa, exact Wilcoxon, and Holm; leave-one-seed-out means; CTK for five learners and three alphas; nine sensitivities; re-bootstraps of 42 control, 24 dose, and 108 representation rows; new versus overlapping expanded families; Spearman; dowgin share and micro CTK without dowgin; partition attempts; run fingerprints). Two consecutive runs produced byte-identical output (SHA-256 `54bca964b41ff5488692a18332bda74fd683c620417ffbe137347b5f3b05f5cc`), and every value equals the value stated in this report.
2. **Reference acquisition is idempotent.** Pass 3 re-hashed all 21 PDFs; none changed and none was added. Every attempted new download either failed by design (403 or challenge) or would have duplicated an existing file.
3. **Findings are stable.** All 29 finding identifiers from passes 1–3 keep their numbers, the five unused numbers (004, 005, 007, 008, 017) stay unused, no identifier is duplicated, and every finding appears in the index (checked mechanically). Pass 3 changed the status of 003 and 027, corrected two facts in 009, and added only 034.
4. **What a further pass should produce.** With the same manuscript hash (`b5419384…c2`), HEAD (`6813f92…`), and results digests, a subsequent pass should reproduce the headline and extension numbers; pass 4’s broader secondary-test scan shows that a previously unexamined quantity can still yield a bounded new finding. Add findings only when new evidence appears (a version of record, an author decision, or a changed manuscript). If the manuscript changes, re-check Section O anchors first; they are exact-string matches against this hash.

### Pass-4 final evidence and coverage record

**Independent arithmetic.** Using saved Parquet evidence, Polars 1.44.2, NumPy 2.5.3, and SciPy 1.18.1, without importing project analysis functions, this pass reproduced CTK `0.11955756103585227`, pooling `0.015051249691406244`, total `0.1346088107272585`, own-domain total `0.03256312168320418`, and known-family change `−0.03605429440533871`, with the exact intervals in Section J. The sample-weighted CTK also reproduces (`0.06581737228032934`). Independent rehashing verified 90 + 5 + 120 manifest entries. The complete secondary rank scan and its sole discrepancy are in CTK-AUDIT-035.

**Equal-test-FPR reconstruction.** Read `outputs/preprocessing/representation/{overlap.parquet,partitions/seed-330…339/assignments.parquet}`, each representation run's `manifest.json`, and 120 saved score files under `outputs/runs/extension-b/representation-r0…r3/seed-330…339/scores/`. For every target, select own-client benign test scores and federation-wide test scores of that target's withheld malware family. Compute the empirical ROC without dropping intermediate points and interpolate TPR at FPR .05 (`diagnostics.py:1470`). Reconstruct family means, then the configured priority/contrast macro means, pair by seed against aligned LAMDA, and use 9,999 BCa resamples with Generator seed 20260924. All 840 cells agree, including calibrated recall/FPR checks against their stored thresholds; all 72 equal-FPR effect means and interval endpoints agree exactly when the specified within-group aggregation order is preserved. An initial independent aggregation that changed floating-point summation order shifted one nonheadline BCa endpoint by about 0.00069 percentage points; restoring the specified order removed the difference. This is numerical resampling sensitivity at the last digits, not a changed inference.

For central full exposure on priority families, the independently reconstructed representation-minus-LAMDA differences are: McNdroid static `+7.28098` points (95% BCa `2.68869–13.12220`), call graph `+3.50259` (`−0.06560–10.33841`), and report JSON `−14.27122` (`−17.95656–−8.26553`). For priority-family FedAvg CTK, the differences are `+8.05446`, `+8.08422`, and `−5.71496` points, respectively. The chapter's +7.28/−14.27 summary and the call-graph interval crossing zero are correct. This sensitivity remains post hoc because it uses benign test scores; it does not replace calibration.

**Publication and layout checks.** The [current IGI contributor guide](https://www.igi-global.com/publish/contributor-resources/before-you-write/) independently supports the conditional anonymization and disclosure findings; the specific call page was inaccessible in this pass, so its dates and 10,000-word floor remain earlier-pass evidence. The general guide currently states an 8,000-word book-chapter minimum, which does not override a stricter call. The title has 69 characters, subtitle 27, and abstract 126 whitespace-separated words. There are ten key terms. Five tables have grid widths totaling 9,360 twips each, matching the 6.5-inch usable width on a letter page with one-inch margins. This structural fit is not proof of rendered cell fit. All five TIFFs are grayscale, 400 dpi: 2,111×1,220; 2,353×1,131; 2,722×1,285; 2,555×1,326; 2,433×1,377 pixels. The [IGI image guide](https://www.igi-global.com/publish/contributor-resources/image-guide/) uses a 300-dpi benchmark and requires readable print sizing. Embedded figure content was visually checked in grayscale. Figure captions and table notes are present; image alternative text is optional CTK-AUDIT-036. Core-property author and last-editor fields are empty, and no tracked insertions/deletions are present; the identifying repository URL remains the supported anonymization finding. The Word package's cached `Pages=1` and `Words=0` values are stale and were not used as page-count or word-count evidence. Rendering was attempted in external scratch and failed because LibreOffice is unavailable; no rendered page, overflow, blank-space, or pagination claim is marked VERIFIED. A native final-layout review therefore remains a coverage limit, not a fabricated formatting defect.

**Research-use and security scope.** The current provider cards identify [LAMDA as MIT](https://huggingface.co/datasets/IQSeC-Lab/LAMDA) and [McNdroid as CC BY 4.0](https://huggingface.co/datasets/IQSeC-Lab/McNdroid). The [AndroZoo access page](https://androzoo.uni.lu/access) states separate research-access and redistribution conditions for its collection. These are recorded as distinct source terms; the repository's MIT software license is not evidence of rights to redistribute underlying APKs. The chapter cites the sources and the README keeps raw data external. No unsupported privacy, secure-aggregation, poisoning-resilience, or deployment claim was found. Individual provenance/access agreements were not available for inspection, so this audit does not certify compliance with every institutional or third-party condition. No violation is inferred from that lack of records. The 21 reference PDFs are unchanged; Holm's institutional mirror was inspected only in scratch, then removed, and is not represented as openly licensed for redistribution.

**Bibliographic recheck.** All 21 retained PDFs reopen as PDFs, with page counts, first-page identities, and SHA-256 values matching Section H. Live Crossref calls rechecked metadata for ten DOI-bearing cited/recommended works; their `update-to` and relation fields contained no correction or retraction links. Three calls (AndroZoo, FLEKD-IDS, Popoola) returned HTTP 429, so their earlier verified publisher/PDF metadata were retained without claiming a new successful registry check. Registry silence is not an exhaustive retraction search. Non-DOI conference proceedings and preprints retain their authoritative proceedings/arXiv identifiers. Holm's full-text step-down procedure agrees with the implementation; the paper does not require independent primary hypotheses for the family-wise bound. No change to any cited scientific description was needed.

**Audit of recommendations.** Every Major finding was challenged against the manuscript's own qualifications. None establishes a false primary effect: 009 is novelty context; 021/022 are reporting of magnitude dependence, already defined and acknowledged qualitatively; 006 applies to the identified review venue; 028 is conditional on author-known AI assistance. There is no evidence of deliberate selective reporting. Two overstatements in this audit were removed: support-based partition selection does not prove a typical partition, and the placebo does not always preserve each peer's hidden-family count because `_allocate` (`design.py:400`) permits reallocation. Suggested wording now preserves those constraints. The Holm explanation now states the ordered 3/2/1 step-down calculation rather than multiplying every p-value by three. No manuscript edit was applied.

**Requirement coverage.** The requested workflow stages 1–9 are represented by the baseline/inventory, full chapter and equation review, code-to-result matrix and recomputations, complete reference inventory with version/access limits, writing/similarity and figure review, three simulated reviewer perspectives, prioritized roadmap, adversarial check of findings, and final integrity comparison. Scientific sections 4–7 map to B/D/G/J/K; numerical sections 8–12 to G/J; literature sections 13–15 to H and its cited primary sources; editorial sections 16–19 to E/I/O and the layout limits above; review sections 20–21 to K/L/M; provenance and integrity sections 22–23 to B/G/N. Each actionable finding has a stable ID, evidence, severity, confidence, minimal correction, implementation category, priority, and status. Unknowns are recorded rather than treated as false or as verified. The author-facing submission decisions in R-01–R-07 are recommendations, not actions required to finish this audit.

**Pass-4 integrity.** A fresh baseline of 12,755 existing files was kept outside the repository. At final rehash, every baseline file except the deliberately excluded `chapter/audit.md` is present and byte-identical, including all 11,949 files under `results/` and `outputs/` and all 21 reference PDFs. No PDF was added, overwritten, or renamed. The manuscript SHA-256 remains `b54193843b08a63bc2328c5a7affa98fc3a8f44f13e059dc16631d4119e972c2`; HEAD remains `6813f929968f141d3660ccfa28d37aaa0180d74f`; status remains only ` M chapter/audit.md` and `?? chapter/references_pdf/`, exactly as at the start. There was no model fitting, training, preprocessing execution, source/configuration/test/result edit, commit, branch creation, tag, stash, or push. All calculations and downloads for inspection used external temporary storage. Pass-4 scratch scripts, extraction text, the temporary Holm scan, and figure previews were removed after final checks. No agent returned external-review evidence, and none was attributed to one.

**Final report checks.** All 31 finding blocks have unique stable IDs and every mandatory field; all required sections A–N are present. Two consecutive independent headline/manifest recomputations produced identical bytes (SHA-256 `b3f6c58ba5c1a3e24841109db65eaf3fe097639e80f5d7c3a534650cbb07da8d`). The final text-hygiene inspection found zero suspicious invisible Unicode characters. Of the 371 tracked files other than this report, 370 are covered by the external hash baseline; `data/README.md` is additionally clean against HEAD and was clean in the initial Git status. It explicitly keeps raw data external and subject to their own licenses. No test-suite rerun is attributed to pass 4; the earlier 488-test evidence remains identified by pass.

### Finding index

| ID | Severity | Status | Requirement | Priority |
|---|---|---|---|---|
| CTK-AUDIT-001 | Minor | Open | Text only | P3 |
| CTK-AUDIT-002 | Minor | Open (revised pass 2) | Text only | P1 |
| CTK-AUDIT-003 | Minor | Open (cause resolved pass 3) | Text only | P3 |
| CTK-AUDIT-006 | Major | Open | Text only | P1 |
| CTK-AUDIT-009 | Major | Open (expanded pass 2) | Text only | P1 |
| CTK-AUDIT-010 | Enhancement | Open | Text only | P1 |
| CTK-AUDIT-011 | Minor | Open | Text only | P3 |
| CTK-AUDIT-012 | Minor | Resolved by Existing Evidence (pass 2) | No action | P3 |
| CTK-AUDIT-013 | Minor | Open | Text only | P3 |
| CTK-AUDIT-014 | Minor | Open (extended pass 2) | Text only | P3 |
| CTK-AUDIT-015 | Enhancement | Open | Existing data | P2 |
| CTK-AUDIT-016 | Minor | Resolved by Existing Evidence (pass 2: pass-1 finding withdrawn) | No action | P3 |
| CTK-AUDIT-018 | Minor | Open | Text only | P2 |
| CTK-AUDIT-019 | Minor | Open | Text only | P2 |
| CTK-AUDIT-020 | Minor | Open | Text only | P2 |
| CTK-AUDIT-021 | Major | Open (new pass 2) | Existing data | P1 |
| CTK-AUDIT-022 | Major | Open (new pass 2) | Existing data | P1 |
| CTK-AUDIT-023 | Minor | Open (new pass 2) | Existing data | P2 |
| CTK-AUDIT-024 | Minor | Open (new pass 2) | Existing data | P2 |
| CTK-AUDIT-025 | Enhancement | Open (new pass 2) | Existing data | P2 |
| CTK-AUDIT-026 | Minor | Open (new pass 2) | Text only | P2 |
| CTK-AUDIT-027 | Minor | Open (fingerprint resolved pass 3; preservation remains) | Repository action; chapter optional | P2 |
| CTK-AUDIT-028 | Major | Needs Verification (new pass 2) | Text only | P1 |
| CTK-AUDIT-029 | Minor | Open (new pass 2) | Text only | P2 |
| CTK-AUDIT-030 | Minor | Open (new pass 2) | Text only | P3 |
| CTK-AUDIT-031 | Enhancement | Open (new pass 2) | Existing data | P3 |
| CTK-AUDIT-032 | Minor | Open (new pass 2) | Text only | P2 |
| CTK-AUDIT-033 | Minor | Open (new pass 2) | Text only | P3 |
| CTK-AUDIT-034 | Minor | Open (new pass 3) | Text only | P3 |
| CTK-AUDIT-035 | Minor | Open (new pass 4; unquoted secondary p only) | Existing data; separately authorized maintenance | P3 |
| CTK-AUDIT-036 | Enhancement | Open (new pass 4) | Optional text only | P3 |

IDs 004, 005, 007, 008, and 017 are not open findings. Pass 1 reserved 004, 005, 007, and 008 for the CyberForce sentence, the CELEST sentence, the representation counts, and the headline Wilcoxon ties, and closed each in Sections B, H, and M. 017 was not used. No critical identifier was used in either pass. Pass 4 used CTK-AUDIT-035 and 036. A later pass should continue numbering at CTK-AUDIT-037.

## O. Surgical Action List (pass 3)

This section turns the open findings into exact, ordered edits that an editing agent can apply without repeating the investigation. It is a plan only; the chapter was not edited.

**How to read it.** Paragraph numbers (P*n*) are the 1-based positions of body elements in `word/document.xml` of `chapter/CTK-Android_Chapter.docx` (SHA-256 `b5419384…c2`), counting tables, as used throughout this report. Every "Find" string was checked to occur exactly once in the extracted text in pass 3. Where several findings touch one paragraph, the edits are merged into a single action so they cannot conflict. Numbers in replacement text were recomputed in pass 2 or 3 and are listed with their source.

**Rules for the editor.**

1. Apply edits with tracked changes in Word. Do not retype unchanged text.
2. Do not change any number except where an action says so. No action changes a reported result.
3. Do not let an AI tool insert or format reference-list entries (IGI policy, CTK-AUDIT-028). Action S-06 gives verified metadata for the author to check and enter. S-23 concerns a figure legend.
4. Keep all class labels (A–D) and all negative results.
5. After editing, recount the abstract (IGI limit 100–150 words; S-01 gives 142) and confirm in-text citations and the reference list match one to one.

### Tier 1 — before submission (P1)

**S-01 · Abstract close · CTK-AUDIT-032 · P4.** Replace "Separate dose, placebo, and representation extensions examine effect heterogeneity and specificity. The findings support exposure-aware evaluation within the tested offline populations and operating conditions." with "In fresh-seed extensions, a wrong-family placebo recovers almost none of the gain, and complementary gain rises with the exact number of peer examples. Local-versus-federated comparisons alone cannot show how much of a collaborative gain depends on which families peers hold." Check: abstract becomes 142 words.

**S-02 · Primary-results paragraph, merged · CTK-AUDIT-001, 002, 033(2) · P101.** Replace the whole paragraph with:

> The CTK mean is 11.96 percentage points, with a 95% BCa interval of 9.15–15.21 points. Every confirmatory seed has a positive difference. The total peer-versus-local gain is 13.46 points, with interval 8.82–17.04, also positive in all ten seeds. Both have Holm-adjusted p = .00586 across the three primary contrasts. Generic pooling contributes 1.51 points, with interval −4.15 to 6.10 and adjusted p = .32227. The interval includes both a modest benefit and a modest harm. The displayed components sum to 13.47 points only because of rounding; their unrounded sum is the 13.46-point total. As Figure 1 states, the absent-everywhere arm removes every selected family from every client, and replacement examples refill the matched budget; across seeds the two arms differ in about 2,100 of 24,000 fit rows. The confirmatory 11.96-point contrast includes that composition change. The evidence is strongest for the complementary exposure contrast and for the combined collaboration gain in this specified population.

Sources: Table 3 values unchanged; 2,073 of 24,000 rows from `outputs/runs/confirmatory/controlled-exposure/seed-10x/exposure.parquet` (pass 2).

**S-03 · New paragraph after P101 · CTK-AUDIT-002, 010.** Insert as a new paragraph between P101 and P102:

> Specificity checks address the content of the exposure: the original family-permutation control uses confirmatory seeds, while the wrong-family placebo uses a separate extension seed block. Shuffling family labels on the original seeds reduces federation-wide CTK to 0.30 points (interval −0.36 to 1.02). The wrong-family placebo substitutes the same total number of malware examples from an unselected family into the absent-everywhere sample, matching per-peer counts where support allows and reallocating them when necessary; it changes recall by −0.54 points, and peer-present recall exceeds it by 10.04 points (interval 8.35 to 12.28, all ten extension seeds). Exact doses from 10 to 200 peer examples are positive in all ten seeds, and the mean effect increases with dose.

Sources: `arm-metrics.parquet` (permutation); `controls-effects.csv`; `exact-dose-effects.csv`; placebo construction in `experiment/design.py` `_train_placebo`.

**S-04 · Secondary populations, merged · CTK-AUDIT-021, 025 · P104.**
(a) Find "and total gain of 14.88 points." Replace with "and total gain of 14.88 points. Weighting each hidden-family test application equally instead of each client gives a smaller but still uniformly positive estimate: micro-pooled CTK is 6.58 points (interval 4.64–8.65, positive in all ten seeds), with pooling 4.00 points and total gain 10.58 points. Dowgin, which supplies almost half of the hidden-family test applications and shows almost no complementary gain, accounts for most of the difference; without it, the micro-pooled estimate is 12.24 points."
(b) Find "the FedAvg federation-wide CTK estimate is 7.85 points, smaller than at 5%." Replace with "the FedAvg federation-wide CTK estimate is 7.85 points, smaller than at 5%, and at 10% it is 13.78 points."
Sources: pass-3 `verify_all` recomputation from `arm-metrics.parquet` (metric `micro-unseen-recall`) and run-level `families.parquet` (dowgin 46.98% of trials).

**S-05 · Neighbour paragraph after P23 · CTK-AUDIT-009.** Insert a new paragraph between P23 and P24:

> Missing classes also appear in federated intrusion detection. Shen et al. (2024) remove one attack class from each of seven clients; the local models fail to detect the removed class, while the federated models detect it. Popoola et al. (2022) omit one botnet traffic class from each edge device and compare federated, centralized, and localized learning. Shao et al. (2026) withhold the positive class from a growing fraction of clients and show that the resulting bias on that class persists even when training appears to converge. In Android malware detection, Gálvez, Moonsamy, and Diaz (2021) and Patel et al. (2026) compare federated and local or drift-aware detection, and Bi et al. (2024) report that aggregate metrics change little as the number of families per client shrinks. These studies establish that collaboration can recover a class a client lacks. None of them removes the selected classes from every client under the same training budget, so none separates generic pooling from complementary exposure.

The Bi et al. clause is optional; if omitted, drop "and Bi et al. (2024) report … shrinks" and the S-06 entry for Bi.

**S-06 · Reference list additions · CTK-AUDIT-009, 028 · between P183 and P196.** The author types these entries in APA 7 from the verified metadata below, in alphabetical position. Every field was checked against Crossref or the PDF in passes 2–3.

| Insert after | Authors | Year | Title | Venue, volume(issue), pages or article | DOI or URL |
|---|---|---|---|---|---|
| P185 (Arp 2014), optional | Bi, Y.; Li, Y.; Feng, X.; Mi, X. | 2024 | Enabling privacy-preserving cyber threat detection with federated learning | arXiv preprint arXiv:2404.05130 (no journal version found) | `https://doi.org/10.48550/arXiv.2404.05130` |
| P187 (Feng 2025) | Gálvez, R.; Moonsamy, V.; Diaz, C. | 2021 | Less is more: A privacy-respecting Android malware classifier using federated learning | Proceedings on Privacy Enhancing Technologies, 2021(4), 96–116 | `https://doi.org/10.2478/popets-2021-0062` |
| P194 (Ongun 2025) | Patel, A.; Tomar, D. S.; Pateriya, R. K.; Haripriya, R. | 2026 | FL-MalDrift: A federated learning framework for malware detection under local concept drift | Scientific Reports, 16, Article 1821 | `https://doi.org/10.1038/s41598-025-31592-z` |
| Patel (new) | Popoola, S. I.; Ande, R.; Adebisi, B.; Gui, G.; Hammoudeh, M.; Jogunola, O. | 2022 | Federated deep learning for zero-day botnet attack detection in IoT-edge devices | IEEE Internet of Things Journal, 9(5), 3930–3944 | `https://doi.org/10.1109/JIOT.2021.3100755` |
| P196 (Sebastián 2020) | Shao, X.; Otani, A.; Yamakawa, K.; Hirasuka, Y.; Wai Shiang, C. | 2026 | Objective mismatch in federated learning under missing class support | IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences, advance publication 2026EAP1060 | `https://doi.org/10.1587/transfun.2026EAP1060` |
| Shao (new) | Shen, J.; Yang, W.; Chu, Z.; Fan, J.; Niyato, D.; Lam, K.-Y. | 2024 | Effective intrusion detection in heterogeneous Internet-of-Things networks via ensemble knowledge distillation-based federated learning | ICC 2024 – IEEE International Conference on Communications, 2034–2039 | `https://doi.org/10.1109/ICC51166.2024.10622262` |

Note: Popoola's version of record is dated 2022 (volume 9, issue 5), although its DOI string contains 2021.

**S-07 · External-validity clause · CTK-AUDIT-009 · P27.** Find "Grouped random partitions and chronological partitions answer different questions; neither should be described as the other." Append: " Patel et al. (2026) evaluate a chronological AndroZoo split for federated detection; the present grouped partitions do not answer that deployment-time question."

**S-08 · New-family generalization, merged · CTK-AUDIT-022 · P150, P154, P179.**
(a) P150: find "not 32 entirely new independent families." Replace with "not 32 entirely new independent families. Fourteen of the 32 families belong to the primary or replication sets. On the 18 families new to the study, family-macro CTK averages 3.47 points per seed (interval 2.45–4.45) and is positive in all ten fresh seeds, against 10.67 points on the 14 overlapping families. The direction of the exposure effect therefore extends to new families, while its size is closer to the three-point practical threshold than the primary estimate."
(b) P154: find "but the conclusion is conditional on the chosen learner, families, budget, and population." Replace with "but the conclusion is conditional on the chosen learner, families, budget, and population. The replication set (5.08 points) and the newly examined expanded families (3.47 points) show the same direction with smaller magnitudes, so 11.96 points should be read as the effect for the support-ranked primary families rather than for Android families in general."
(c) P179: find "The benefit varies by family and client." Replace with "The benefit varies by family and client, and it is smaller outside the support-ranked primary families: 5.08 points for the disjoint replication set and 3.47 points for families new to the expanded analysis."
Sources: `large-family-seed-ctk.csv` (pass 2–3, Class C-style post hoc split of Class D data); Table 5.

**S-09 · Repository URL · CTK-AUDIT-006 · P89 (review copy only).** Find "The associated CTK-Android repository contains the source code, configurations, machine-readable results, and provenance records: https://github.com/naslouby-salahe/ctk-android." Replace with "The accompanying repository contains the source code, configurations, machine-readable results, and provenance records. The review copy omits the repository URL." Restore the URL in the camera-ready file. Combine with S-15 in the same paragraph.

**S-10 · AI-use statement · CTK-AUDIT-028 · before P182 ("References").** Only if AI tools assisted the analysis, code, or writing, including wording adopted from this audit: insert a paragraph headed "AI Disclosure Statement" stating the tool, the tasks, and that the author verified all output and entered all references personally. Template in CTK-AUDIT-028. The author must make the statement true; no agent should decide it.

### Tier 2 — strongly recommended (P2)

**S-11 · Learner CTK · CTK-AUDIT-025 · P106.** Find "both below the FedAvg mean." Replace with "both below the FedAvg mean. Complementary exposure is positive for every collaborative learner: CTK is 13.10 points for central training, 13.20 for FedProx, 8.20 for fine-tuned FedAvg, and 7.60 for blending, each positive in all ten seeds. Learner choice changes the size and the cost of the exposure benefit, not its direction."

**S-12 · Client own-domain totals · CTK-AUDIT-024 · P127.** Find "Anzhi therefore illustrates the known-family cost of collaboration." Replace with "Anzhi therefore illustrates the known-family cost of collaboration. On each client's own hidden-family test applications, the FedAvg total gain is −2.80 points at Anzhi and −0.40 at AppChina, against 6.48 at play-early and 13.61 at play-late; the first two intervals include zero. The positive own-domain average therefore comes from the two Google Play domains, and the play-late estimate rests on about 107 hidden-family test applications per seed."
Source: recomputed in pass 3 from run-level `metrics/clients.parquet`; matches `client-ctk-analysis.csv`.

**S-13 · Dose paragraph, merged · CTK-AUDIT-023, 033(5) · P135.**
(a) Find "These estimates are consistent with diminishing gains at the upper tested range, but neither prove a plateau nor justify a universal minimum dose." Replace with "The pooled estimate combines two patterns. In the primary family set, CTK still rises by 4.23 points (interval 2.53–6.55) between 100 and 200 peer examples; in the replication set the same increment is 0.03 points (−3.91 to 2.54). The data therefore show neither a common plateau nor a universal minimum dose."
(b) Delete the final sentence "These extensions clarify the exposure manipulation without being pooled into the original confirmatory test."

**S-14 · Figure 1 note · CTK-AUDIT-029 · P61.** Replace the whole note with "Note. Schematic for one target-family pair. In each run several families are assigned to different targets. Peer present removes each family only from its own target, so a target keeps the families assigned to other targets; absent everywhere removes every selected family from every client. Replacement examples refill each client's budget of 6,000 fit rows. Full exposure lifts deliberate exclusions but remains budgeted."

**S-15 · Provenance sentence · CTK-AUDIT-026 · P89.** After "with matching revisions and clean analysis sources." insert "The reported artifacts come from a final execution of the frozen configuration made after GPU dropout seeding and deterministic kernels were enabled. Two earlier executions of the same configuration were not bit-reproducible; they gave a FedAvg CTK of 11.7 points in both cases and are retained in the repository documentation but not pooled with the reported results."

**S-16 · Introduction result paragraph · CTK-AUDIT-018 · P11.** Replace the whole paragraph with "Across ten confirmatory seeds, complementary peer exposure raises FedAvg federation-wide unseen-family recall by 11.96 percentage points (interval 9.15 to 15.21). Generic pooling contributes 1.51 points, and that interval includes zero. The own-domain total gain is 3.26 points, and known-family recall falls by 3.61 points. Family, client, and learner heterogeneity are reported with those averages."

**S-17 · Discussion restatement · CTK-AUDIT-019 · P153.** Replace the whole paragraph with "The confirmatory contrast in Table 3 is the fitted and calibrated response to the Figure 1 intervention, including the replacement examples that refill the matched budget. Matching client sample counts and the collaborative training schedule narrows the explanation compared with a local-versus-federated comparison alone. The result does not identify which parameters or features carry the gain." (This keeps pass 1's replacement and restores the matching sentence, which carries information not stated elsewhere in the discussion.)

**S-18 · Conclusion specificity · CTK-AUDIT-020 · P180.** Find "Exact-dose results clarify the role of realized peer support, while permutation and placebo controls strengthen the family-specific interpretation." Replace with "Two extensions, which are not part of the original three-contrast test, speak to specificity. At exact peer doses of 10, 25, 50, 100, and 200 examples, the FedAvg family-macro effect is positive in all ten seeds, and its mean increases with dose. The wrong-family placebo does not reproduce the gain: peer-present CTK exceeds the placebo by 10.04 points (interval 8.35 to 12.28)."

**S-19 · Seed-sensitivity sentence · CTK-AUDIT-015 · P172.** Find "They provide limited precision for subgroup inference and do not constitute ten independent external datasets." Append: " Leaving out any one confirmatory seed leaves a mean CTK between 11.06 and 12.65 points, still above the three-point practical threshold; that range is a sensitivity check on the ten observed differences, not a replacement for the BCa interval."

### Tier 3 — polish (P3)

**S-20 · Partition margin · CTK-AUDIT-031 · P50.** Append to the paragraph: " In the confirmatory seeds the retained candidate has 57–60 eligible client-family pairs, against a median of 52.5–56 across its 16 candidates, so the rule raises the eligible-pair count by about 9% relative to the median candidate. This does not assess representativeness on other characteristics."

**S-21 · Equal FedAvg weights · CTK-AUDIT-030 · P75.** Find "and return parameters for sample-count-weighted aggregation." Replace with "and return parameters for sample-count-weighted aggregation; because every client contributes exactly 6,000 fit rows, these weights are equal."

**S-22 · Figure 4 caption · CTK-AUDIT-014 · P123.** Replace with "Note. Entries are mean recall proportions rounded to two decimals, nominal 5% FPR, seeds 100–109; the text reports the same means as percentages to two decimals, so adwo's local and peer-present recall (67.34% and 66.60%) share one cell value. Full exposure refers to FedAvg here; it is not a theoretical ceiling."

**S-23 · Figure 3 legend · CTK-AUDIT-013 · `chapter/figures/Figure_3.tif`.** Regenerate the figure with legend entries "Mean across seeds" and "Mean of within-seed worst client". This is a figure-file change, not a text change; the plotted values stay the same.

**S-24 · Spearman source · CTK-AUDIT-003 · P149.** Find "the stored Spearman association is .408" and replace with "the frozen Spearman association (large-family-summary.csv) is .408".

**S-25 · Permutation file label · CTK-AUDIT-011 · P137.** Append to the paragraph: " The extension file permutation-control-audit.csv labels its federation-wide row A-original-confirmatory because that row uses the primary contrast definition; its seeds are 200–209 and its mean is the −0.21 points reported here."

**S-26 · Key term usage · CTK-AUDIT-034 · P154.** Find "negative pooling offsets much of a positive CTK effect." Replace with "negative pooling, a form of negative transfer, offsets much of a positive CTK effect."

**S-27 · Sentence trims · CTK-AUDIT-033(1, 3, 4).** P22: replace "frozen uncertainty estimates" with "seed-level uncertainty intervals". P168: delete "These distinctions limit the language used for both positive and negative results." P176: delete "These are substantive limits on application of the findings, even when the within-study numerical and provenance checks are satisfied."

**S-28 · Freeze record (optional) · CTK-AUDIT-027 · P74.** Find "Hyperparameters and statistical procedures were frozen before the confirmatory evaluation." Replace with "Hyperparameters and statistical procedures were frozen before the confirmatory evaluation; every confirmatory run's resolved configuration matches the frozen protocol record."

**S-29 · Optional alternative text · CTK-AUDIT-036 · Figures 1–5.** Add the five descriptions in CTK-AUDIT-036 to the embedded images. No raster values change.

### Author decisions and repository actions (not chapter edits)

| ID | Action | Finding | Who |
|---|---|---|---|
| R-01 | Decide whether the submission targets the IGI double-anonymized call; if yes, prepare a review copy with S-09 | 006 | Author |
| R-02 | Decide whether AI assistance must be disclosed; if yes, apply S-10 | 028 | Author |
| R-03 | Tag and push `e079972` (and optionally `dccf996`), or archive a `git bundle` with the artifact | 027 | Author |
| R-04 | Mark `docs/results.md` and `docs/Research Evidence.md` as superseded by `results/`, or move them to an archive folder | 026 | Author |
| R-05 | Obtain versions of record by browser or library for CyberForce, CELEST, LAMDA (ICLR), AVClass2 and AndroZoo (ACM), FLEKD-IDS and Popoola (IEEE), and Holm (JSTOR), and spot-check the cited sentences | Section H | Author |
| R-06 | In the camera-ready file, restore the repository URL removed by S-09 | 006 | Author |
| R-07 | If maintaining derived artifacts, address the single tied-rank p-value using the exact procedure in CTK-AUDIT-035; preserve the original frozen artifact and record provenance | 035 | Separately authorized maintenance |

### Investigated and requiring no action

Headline numbers; Holm adjustment; Wilcoxon validity for the three primary contrasts (secondary exception: 035); extension intervals; representation effects; client table; original dose supports; partition selection; frozen configuration and hyperparameters; manifests (90 + 5 + 120 digests); Ciaramella and AndroZoo descriptions; the CyberForce author list (CTK-AUDIT-016 withdrawn); the 925-feature statement; the Holm reference (keep the JSTOR URL; the OpenAlex DOI is unregistered).

### Expected effect

S-01 to S-10 answer the four objections most likely to change a reviewer's decision: closest prior work, magnitude and weighting, estimand definition, and venue compliance. S-11 to S-19 add favourable and qualifying evidence in proportion. The estimated net addition is roughly 650 words. The current chapter exceeds the verified minimum; no maximum length is inferred from that minimum. No action requires new training.
