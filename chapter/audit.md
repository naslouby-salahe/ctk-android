# Chapter audit and revision

12 October 2026

**Editorial assessment: 84/100 before revision; 90/100 after the chapter corrections.** These are reviewer-style judgments of the chapter's clarity, scientific reporting, and defensibility, not publisher scores or probabilities of acceptance. The original was technically substantial and unusually candid about negative findings. Its main weaknesses were omitted FPR exceptions, several imprecise method descriptions, repetition, and incomplete directions for locating the evidence. The revised chapter is stronger, but an offline study on one underlying corpus cannot become universally conclusive through editing.

The review covered the entire chapter text and tables, the main data-partitioning, exposure, training, evaluation, decomposition, and inference paths in `src/`, and the frozen evidence in `results/`. It did not retrain the confirmatory campaign or independently reconstruct the raw datasets. Selected literature and method definitions were checked against primary sources; this was not a new exhaustive literature search or a commercial similarity scan.

**Findings corrected in the chapter**

1. **False-positive exceptions were too easy to miss.** The original reported the primary mean FPR accurately, but discussed client variation only in general terms. The revision reports primary peer-present FedAvg mean worst-client FPR of 6.60% and a maximum across seeds of 9.89%. It also names the four extension experiment/seed combinations with recorded macro-FPR tolerance failures and the 15.32% client FPR in the call-graph central peer-present arm. These are observed exceptions, not hypothetical limitations. Sources: `results/tables/operating-point-fidelity.csv`, `results/evidence/arm-metrics.parquet`, and `results/extension-b/diagnostic-fpr-exceptions.csv`.

2. **The tolerance's scope needed to be explicit.** `workflows/run.py::_operating_validation` checks client-macro FPR at the primary alpha. It does not enforce the tolerance separately for every client. The revised calibration section distinguishes calibration support, macro-level fidelity, and individual-client FPR. It does not claim that every recorded run passes the FPR check.

3. **Average precision needed its actual estimator named.** `experiment/evaluation.py:148` calls `average_precision_score`, although the result column is named `auprc`. The revision names average precision, explains its recall-increment weighting, and identifies the legacy artifact label. Existing numerical results are preserved. This estimator differs from trapezoidal PR-curve integration; see the [scikit-learn definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

4. **Pooling is not an isolated data-volume effect.** The exposure conditions match the collaborative learner and its training schedule, but the residual pooling contrast compares FedAvg with a local model trained under a different schedule. The revision makes that distinction explicit beside the decomposition. It does not undermine the within-FedAvg CTK comparison. Sources: `configs/experiments.yaml`, `experiment/training.py`, and `analysis/decomposition.py`.

5. **Optimizer state was an omitted reproducibility detail.** The code initializes a new Adam optimizer for each client's local training call. The revision states that its state is not carried across communication rounds. This clarifies the implemented algorithm without changing it. Sources: `experiment/models.py::_optimizer`, `fit_epochs`, and `experiment/training.py::train_federated`.

6. **The inferential target needed sharper wording.** Seed bootstrap intervals describe variation under the implemented experiment on this corpus. They do not describe ten independent organizations or datasets. The revised text also distinguishes BCa intervals for the mean from the signed-rank null and limits the exact-test statement to the verified, untied primary contrasts. The three primary contrasts contain neither zeros nor tied absolute differences.

7. **The chapter described provenance without giving readers a concrete route to it.** The revision adds the repository location, recorded execution/analysis revision, external-data requirement, and pointer to the reproduction instructions. This is not a certification that every reviewer already has access to the repository or data. Access should be checked before submission.

8. **The abstract underrepresented the tradeoff.** It now includes the 3.26-point own-domain total gain and the 3.61-point known-family loss, alongside the 11.96-point federation-wide CTK contrast. Those quantities concern different estimands and are labeled accordingly.

9. **Some prose repeated conclusions or used misplaced language.** The revision tightens the introduction, estimand discussion, negative-control explanation, discussion, and conclusion. References to a “biological” mechanism or classes of malware were removed. Necessary qualifications remain, including the unresolved original own-domain permutation control, negative families, fixed budgets, overlapping representation data, and the weak stable-family association.

10. **The representation results needed a direct operating-point sensitivity.** The revision reports the existing post-hoc equal-test-FPR diagnostic: priority-macro full-exposure differences remain positive for McNdroid static (+7.28 points) and negative for report-JSON (−14.27 points); the call-graph interval still spans zero. It explicitly identifies use of benign test scores, so this cannot be mistaken for independently calibrated deployment evidence. Source: `results/extension-b/diagnostic-representation-equal-fpr-effects.csv`.

**Evidence checks**

All 215 manifest-listed artifact digests matched when independently checked. The primary means, BCa intervals, exact signed-rank p values, and Holm correction were recomputed from the stored seed differences, without changing the result files:

| Contrast | Mean percentage points | 95% BCa interval | Holm p |
|---|---:|---:|---:|
| CTK | 11.955756 | 9.154774 to 15.209881 | .005859375 |
| Pooling | 1.505125 | −4.149069 to 6.098065 | .322265625 |
| Total | 13.460881 | 8.817780 to 17.040137 | .005859375 |

These reproduce the chapter's rounded values. The apparent 0.01-point discrepancy when adding the displayed CTK and pooling means is rounding, not an arithmetic error. The three differences add exactly before rounding.

Dataset counts, learner settings, metric denominators, priority representation effects, expanded-family association, and stable-family sensitivity were checked against the corresponding configurations, implementation, and stored tables. In particular, the chapter correctly reports the full-family association of approximately .408 and the weaker stable-family association of approximately .294. Neither warrants a general partner-selection rule.

The review found no basis for replacing the chapter's central positive finding with a null conclusion. It also found no basis for claiming that all clients benefit, that the models are deployment-ready, or that privacy and poisoning robustness were demonstrated. The chapter's existing restrictions on those claims were retained.

**Source-code issue left unchanged at the author's request**

`src/ctk_android/analysis/statistics.py:74` always passes `method='exact'` to SciPy's Wilcoxon calculation for nonzero arrays. With tied absolute ranks, this is not generally the exact permutation distribution. The [SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html) makes this distinction explicit.

For the stored central-model total gain in worst-client recall under `training-support-sensitivity`, salt 0, alpha .01, the helper returns .009765625; exhaustive permutation gives .0078125. Both remain below .05. Among the 26 nonconstant zero/tied groups identified in the stored original decomposition, this was the observed disagreement in that check. The three primary headline contrasts are unaffected. This is a secondary statistical correctness issue, not evidence that the headline CTK finding is false. No code or frozen statistical output was altered, and this secondary p value is not reported in the chapter.

The architecture/static-analysis test run completed with 117 passing tests, including the repository's lint, format, strict typing, and configured Semgrep checks. The separate unit/integration/end-to-end run completed with **380 passed and one failed** (292.51 seconds). Thus 497 tests passed across the two runs, but the full test set is not green.

The failing test is `tests/integration/test_smoke_workflow.py::test_analysis_handles_single_seed_smoke_evidence_from_every_experiment`. Its error is that `replication-family-set` seed 0 is missing from the smoke plan. The preceding `test_smoke_run_logs_its_full_lifecycle_with_counts_and_timings` narrows the configuration to `end-to-end` and runs with `overwrite=True` in the same module-scoped workspace. The later analysis then expects the complete plan. This explains the observed test-order/fixture contamination; it does not show that the frozen confirmatory experiment is invalid. This test issue was also left unchanged as requested. No isolated rerun was used to claim that the full sequence passes.

**Writing and AI assessment**

The original's clearest editorial weakness was repetitive qualification: many paragraphs introduced a result and then repeated a familiar restriction already established elsewhere. This can sound formulaic, but it is not evidence of machine authorship. The revisions target readability and precision rather than trying to manipulate a detector.

The deterministic audit found zero suspicious invisible Unicode characters in both the original extracted prose and the revised extracted prose. That result says nothing about statistical text watermarks or authorship. No Turnitin, iThenticate, GPTZero, or other commercial AI/similarity score was obtained. An “AI percentage” would not be justified by this review. As one documented example of the reliability problem, OpenAI withdrew its classifier because of low accuracy; see its [classifier notice](https://openai.com/index/new-ai-classifier-for-indicating-ai-written-text/).

An AI-use statement was not added, following the author's explicit instruction to supply it later. This remains an author submission task. IGI's [published AI-use policy](https://www.igi-global.com/newsroom/archive/publish-perish-don-let-write/6596/) calls for disclosure of the tool and its use in the manuscript. This audit does not certify compliance with that policy or determine the full history of AI use.

**Remaining limits**

The study still uses constructed clients, support-selected family tasks, a fixed underlying corpus, a limited number of seeds, and a nonchronological partition. Those are research-design boundaries, not copyediting defects. The strongest next scientific evidence would come from a prospectively defined temporal or independent-domain evaluation; it is not supplied by this revision.

The source and result files were preserved. The contents of the five editable tables, three editable equations, and five embedded figure files are unchanged from the original DOCX. Table pagination was adjusted to keep the short tables together. Microsoft Word reports 11,808 words and 49 pages; all rendered pages were visually checked. All 257 source/result files included in the pre-edit protection snapshot matched afterward. The revised chapter should be read as a more precise account of the existing study, not a new experiment or a guarantee of acceptance.
