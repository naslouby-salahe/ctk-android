# Complementary Threat Knowledge in Federated Android Malware Detection: A Controlled-Exposure Decomposition

**Working title (chapter):** *How Much of Collaboration's Benefit on Unseen Android Malware Families Is Complementary Threat Knowledge, and How Much Is Generic Pooling?*

**Document role:** research protocol, written before the confirmatory experiment. Everything below is prospective: it fixes the design, the comparisons, the metrics, the gates and the claim wording before confirmatory results are inspected.

---

## 1. Motivation

Android malware detectors are trained by many organisations that see different slices of the ecosystem: an app market in one region sees different adware and SMS-fraud families than a global store. When such organisations collaborate without sharing apps, for example through federated learning (FL), the usual argument is that a client that has never seen a malware family benefits from peers that have. That argument mixes two separate effects:

1. **Generic pooling.** More training data, more regularisation and a better-conditioned model help every client, even for families nobody has seen.
2. **Complementary threat knowledge.** A peer holds labelled examples of a family that the client lacks, and that specific knowledge transfers.

Only the second effect is what collaboration is *for* in a threat-sharing setting. Existing Android FL work reports pooled accuracy or recall on families that are missing from some clients, without a control that removes the family from the whole federation. Without that control the two effects cannot be separated.

## 2. Problem Statement

Given K clients with different malware-family exposure, quantify, at a fixed false-positive rate per client:

- how much unseen-family recall a client gains from collaboration;
- how much of that gain disappears when the family is removed from every peer as well (the generic-pooling share);
- how much peer evidence (number of labelled peer samples of the family) is required;
- which families collaboration cannot rescue;
- what collaboration costs on families the client already knows;
- how the picture changes for the worst-off client rather than the average client.

## 3. Research Gap

FL and Android-malware literature covers non-IID partitions, drift, personalisation, prototype exchange for classes absent from some clients, and federated transfer for rare classes. What is not established is a controlled, reproducible **decomposition** of collaborative benefit on unseen families into pooling and complementary components on a large public Android benchmark, with dose-response, worst-client and irreducible-family views. This is an empirical measurement contribution. No new learning algorithm is claimed.

## 4. Research Questions

- **RQ1 (existence).** When a client has never observed a family that peers know, how much lower is its unseen-family recall than that of a client with full exposure, at a fixed FPR?
- **RQ2 (decomposition).** How much of the gain of collaborative training over local training on such families is (a) generic pooling and (b) complementary threat knowledge?
- **RQ3 (dose-response).** How does unseen-family recall change with the number of peer training samples of the family?
- **RQ4 (worst client and irreducible families).** Does the benefit hold for the worst-off client, and which families does collaboration fail to rescue even with full peer exposure?
- **RQ5 (cost and mechanism).** What does collaboration cost on known families, how do FL arms compare with pooled training, and is there residual headroom that a peer-selection mechanism could recover?
- **RQ6 (generality).** Does the decomposition survive a second model family, a second family set, a natural (uncontrolled) exposure axis, other FPR targets, and leakage-hardened splits?

## 5. Hypotheses

- **H1.** Local models have materially lower unseen-family recall than models trained with peer exposure (central, FedAvg, FedProx, FedAvg + fine-tuning), at matched FPR.
- **H2.** The complementary-knowledge component is positive but smaller than the generic-pooling component.
- **H3.** Complementary benefit grows with peer sample count and saturates; it is negligible below a small number of peer samples.
- **H4.** A non-trivial set of families stays poorly detected even with full peer exposure (feature-level, not exposure-level failure).
- **H5.** Collaboration has a small known-family cost or no cost; a local/global logit blend is not better than the best simple collaborative arm.

Hypotheses can fail. A failed hypothesis narrows the corresponding claim; it does not invalidate the study (Section 26).

## 6. Expected Contributions

1. A controlled-exposure protocol for Android malware families with a no-family-anywhere pooling control, a dose-response arm and oracle bounds.
2. A quantitative decomposition of collaborative benefit into generic pooling and complementary knowledge, with worst-client and per-family views.
3. A list of collaboration-irreducible families and the feature-level reason they fail.
4. A leakage-hardened split protocol for LAMDA (grouping by package **and** identical feature vector).
5. Negative or bounded findings on simple blending and peer-selection headroom.

## 7. Threat Model and Assumptions

- Honest-but-curious collaboration; clients do not share apps or raw features. The study measures utility only. No privacy or adversarial claims are made.
- A client's detector is a supervised classifier over static Drebin-style features; labels are AV-consensus labels (see Section 9).
- Family knowledge is exposure to labelled malware of that family in training. "Unseen" means zero training samples of the family at that client.
- The operating point is set per client from that client's own held-out **benign** validation scores (target FPR α). No malware labels are used to set thresholds.
- Simulated clients are deployment-motivated (Section 10). Results describe the simulated federation, not real organisations.

## 8. Datasets and Dataset Roles

| Role | Dataset | Use |
|---|---|---|
| Primary | LAMDA (1,008,381 APKs, 925 binary static features after variance filter, VirusTotal-count labels, AVClass2 families) joined with the AndroZoo catalogue for market and package identity | all experiments |
| Feature/label source | LAMDA `var_thresh_0.01` parquet files, `metadata.csv` | features, labels, families, year-month |
| Market/package source | AndroZoo `latest.csv.gz` (matched on SHA-256; all 1,008,381 hashes matched) | market, package name |

Licensing: LAMDA is MIT-licensed on Hugging Face; AndroZoo is available under its data-use terms (registration). Raw data are never committed. Only aggregate result files are versioned.

Dataset properties that shape the design:

- Family labels are AVClass2 tokens dominated by adware and SMS-fraud families. About 150,000 malware rows carry singleton labels; only families with adequate support are eligible.
- Nearly half of all rows share an identical feature vector with another row, and 2,418 identical-vector groups carry conflicting labels. Splits must group on the union of package name and feature vector.
- Family support per market is highly concentrated (for example most `dowgin` and `kuguo` samples come from Anzhi). Eligibility rules therefore use minimum peer and test support.

## 9. Label and Feature Semantics

- Malware label: VirusTotal detection count ≥ 4; benign: count 0. The grey zone (1–3) is absent, so the benign class has no natural contamination.
- Family: AVClass2 output, treated as a noisy grouping variable, never as ground truth for a taxonomy claim. Wording is "AVClass2-labelled family".
- Features: 925 binary static indicators (permissions, API calls, intents, and similar). Variance filtering was applied by the dataset authors over the whole corpus. This is global preprocessing by the dataset provider and is documented as a limitation. It cannot be undone.

## 10. Client Construction

Primary federation (K = 4), each client is a single-market population with a deployment reading as an independent security team that scans its own distribution channel:

| Client | Definition |
|---|---|
| play_e | apps whose only market is Google Play, dated ≤ 2018 |
| play_l | Google Play only, dated ≥ 2019 |
| anzhi | Anzhi only |
| appchina | AppChina only |

Apps present in more than one market are excluded from client construction. Clients are not shards of a single pool: they differ in prevalence (5%–87% malware), era, and family mix.

**Controlled exposure.** Sixteen eligible AVClass2 families are randomly divided (per seed) into four groups G_0..G_3. Client c deletes the training malware of every family in G_c from its own training data. Peers keep them. A family is eligible for evaluation at client c only if peers hold at least 150 training malware of it and the test partition holds at least 50.

A second, disjoint set of sixteen families is used for replication (Section 13). A third **natural-scarcity** axis uses no deletion: it evaluates (client, family) pairs in which the client holds at most 5% of the family's training malware, peers hold at least 150, and the client's own market has at least 15 test samples.

## 11. Identity and Grouping

- Row identity: SHA-256 (unique in LAMDA).
- **Split unit:** connected components of the bipartite graph linking rows to package names and to exact feature vectors. No component may straddle train, validation and test.
- Partition: 60% train / 20% validation / 20% test by component hash. Validation supplies benign scores for thresholding only. Test rows are never used to choose thresholds, arms or hyper-parameters.
- Unseen-family evaluation rows come from the test partition of all markets (cross-market) and, as a separate metric, from the client's own market only.

## 12. Train / Validation / Test Protocol

- Training set per client: sample of up to 6,000 rows at natural prevalence, drawn from the client's training partition after family deletion; every arm draws the same number of rows so sample size is not confounded.
- Threshold: the (1−α) quantile of the client's validation benign scores; α = 0.05 primary, 0.01 and 0.10 sensitivity.
- Ten confirmatory seeds (100–109). A seed fixes the family grouping, sampling and initialisation. These seeds are not used for any development decision.

## 13. Experimental Scenarios

1. **Main controlled exposure** (family set 1, MLP scorer).
2. **No-family-anywhere pooling control:** for each client c, train the pooled and FedAvg models on all clients with G_c removed from every client, re-drawn to the same size.
3. **Dose-response:** peers keep only m ∈ {0, 1, 10, 50, 100, 500, 1000, all} total training samples of each hidden family; effective counts are reported because per-client caps bind.
4. **Second scorer:** a linear model (all arms) and gradient boosting (local, pooled, no-family, oracle).
5. **Second family set** (families 17–32).
6. **Natural scarcity** (no deletion).
7. **Leakage sensitivity:** repeat scenario 1 with package-only grouping.
8. **Own-market evaluation** of scenario 1 (removes the cross-market confound).
9. **FPR targets** 0.01 / 0.05 / 0.10 on all scenarios.

## 14. Baselines and Arms

| Arm | Meaning |
|---|---|
| Local-only | per-client model trained on its own data |
| Central | pooled training over all clients' training data (upper reference for collaboration) |
| FedAvg | 30 rounds × 3 local epochs |
| FedProx | μ = 0.05 |
| FedAvg + local fine-tune | 3 epochs at half learning rate |
| Local/FedAvg and local/central logit blend | 50/50 (the "simple blend") |
| Oracle local | local model with own hidden families restored |
| Oracle central / FedAvg | nobody hides any family (full exposure) |
| No-family-anywhere central / FedAvg | pooling control (Section 13) |

Arms are fixed before the confirmatory seeds. No arm is added after seeing confirmatory results.

## 15. Proposed Analysis (no new method)

The contribution is an analysis. For unseen-family recall R (at α = 0.05) define per seed, for each pooled arm P ∈ {central, FedAvg}:

- total gain = R(P) − R(local)
- generic-pooling gain = R(P, no family anywhere) − R(local)
- **complementary-knowledge gain** = R(P) − R(P, no family anywhere)
- complementary share = complementary / total

Each is computed for the mean over clients and for the worst client. Oracle-gap recovery of an arm A is (R(A) − R(local)) / (R(oracle central) − R(local)).

**Conditional mechanism study.** A peer-selection or family-aware collaboration mechanism is investigated only if, in the confirmatory seeds, the best simple collaborative arm leaves a residual gap to oracle central of more than 0.10 absolute mean unseen-family recall, or more than 0.15 for the worst client. Any such mechanism must use deployment-available inputs, be tuned on validation data only, follow a predefined selection rule, and be evaluated once on untouched test data. Otherwise the chapter reports that no mechanism is justified.

## 16. Oracle / Upper Bounds

- Full-exposure oracles (local, FedAvg, central).
- Family-level ceiling: per-family recall of oracle central; a family whose oracle recall is below 0.6 is labelled **collaboration-irreducible** at α = 0.05.

## 17. Primary Metric

Unseen-family recall at α = 0.05: fraction of test malware belonging to the client's hidden eligible families that scores above the client's benign-validation threshold, averaged over clients (micro over the client's rows).

## 18. Secondary Metrics

- Family-macro unseen recall (mean over families).
- Known-family recall (client's own-market test malware outside the hidden set).
- Realised FPR on own-market test benign (validity check: within ±0.01 of α).
- AUROC of unseen-family malware against own-market benign.
- Oracle-gap recovery, complementary share, negative-transfer cost (known-family recall change versus local).

## 19. Worst-Client and Dispersion Metrics

- Worst-client unseen recall (minimum over clients, per seed).
- Client dispersion: standard deviation of unseen recall over clients.
- Family dispersion: standard deviation of per-family recall; count of irreducible families.

## 20. Statistical Analysis

- Replication unit: seed (10 confirmatory seeds). Paired differences between arms within seed; report mean difference, 95% t-interval (df = 9), number of seeds with positive difference, and Hedges g_z as effect size.
- Primary contrasts (three, Holm-adjusted at family-wise 0.05): central − local; no-family-anywhere central − local; central − no-family-anywhere central. Same three for FedAvg as secondary.
- Wilcoxon signed-rank as a robustness check on the seed differences.
- The complementary share is the ratio of the mean complementary gain to the mean total gain; its 95% interval is a seed bootstrap (10,000 draws) of that ratio. When the total gain interval includes 0 the share is not reported.
- Within a seed, uncertainty in per-family recall is reported with a component-cluster bootstrap over test components (1,000 draws).
- Multiplicity: exploratory contrasts (blends, dose points, α sensitivities) are reported with unadjusted intervals and labelled exploratory.

## 21. Ablations

- Model family (MLP, linear, gradient boosting).
- Family set (two disjoint sets).
- Training-set size per client (1,500, 6,000).
- Local training epochs (10, 20, 40) and local fine-tune epochs (0, 1, 3, 5), so that no arm is under-trained.
- FedProx μ ∈ {0.01, 0.05, 0.1}.

## 22. Sensitivity Analyses

- FPR target α ∈ {0.01, 0.05, 0.10}.
- Eligibility thresholds (peer support 100/150/300; test support 30/50/100).
- Cross-market versus own-market evaluation.
- Grouping rule (package-only versus package ∪ feature vector).

## 23. Negative Controls

- No-family-anywhere pooling control (isolates generic pooling).
- Dose 0 (peers hold none of the hidden families).
- Label-permutation check for family membership (`--permute-fam`): family labels are randomly re-assigned among malware rows with family sizes preserved; the complementary gain must vanish (interval covers 0).
- Automatic leakage assertions (Section 27).

## 24. Robustness Checks

- Component-hash re-salting (three alternative partitions).
- Reporting with and without families in the top-3 by support (dowgin, kuguo, airpush).
- Removing near-duplicate evaluation rows (identical feature vectors inside the test partition collapsed to one row).

## 25. External Replication

No second Android corpus with market-level clients and family labels is required. Replication is internal (second family set, second scorer, natural scarcity). The chapter states that external replication on McNdroid or another drift benchmark with family labels is future work and is not claimed.

## 26. Claims and Claim Promotion Gates

| Claim | Gate for promotion |
|---|---|
| C1. Local clients miss peer-known families | H1 contrast positive, 95% interval excludes 0 in ≥ 8/10 seeds |
| C2. Complementary knowledge is a distinct, positive part of the gain | complementary contrast ≥ 0.03 absolute, interval excludes 0, positive in ≥ 8/10 seeds, and the label-permutation control is null |
| C3. Generic pooling explains the majority of the gain | generic share > 50% with the interval on the share excluding 50% |
| C4. Dose-response | monotone-nondecreasing trend in the mean over seeds and dose ≥ 100 peer samples exceeds dose 0 by ≥ 0.03 |
| C5. Irreducible families exist | ≥ 3 families with oracle-central recall < 0.6 in ≥ 8/10 seeds |
| C6. Worst-client benefit | worst-client complementary contrast interval excludes 0; otherwise the claim is restricted to the mean |
| C7. Known-family cost is small | absolute known-family change versus local within ±0.02 for FedAvg |
| C8. Simple blends do not beat the best collaborative arm | blend − best arm ≤ 0 with interval excluding positive |

Gates are evaluated separately for validity and for effect size. **Structural failures** (leakage assertion fails, realised FPR outside α ± 0.01, eligibility not met) block the affected experiment. **Weak effects** narrow a claim (for example "mean only", "MLP only") and do not remove the chapter. Wording: "In this simulated four-client federation on LAMDA, …". Forbidden wording: "first", "novel", "state of the art", "zero-day detection", any statement about real organisations, any privacy guarantee.

## 27. Reproducibility

- All scripts take an explicit seed and write structured JSON to `out/`; no notebook state.
- `build_lamda_cache.py` builds the joined cache from raw files; `c1_common.py` builds groups and splits deterministically from SHA-256/package/feature-vector hashes.
- `run_all.sh` reproduces every experiment; `python c1_study.py check SEED` executes the automatic leakage assertions (hidden family absent from the client's training data, evaluation rows only from the test partition, thresholds from benign validation rows only, no component straddling partitions).
- Data paths come from environment variables `CASE_RAW` and `CASE_CACHE`.

## 28. Compute Plan

One seed of the main scenario takes about two minutes on one GPU (RTX-class, 16 GB); dose-response about eight minutes; gradient boosting about one minute on CPU. The cache needs about 170 MB and 3 GB of RAM. Ten confirmatory seeds for all scenarios fit in roughly six GPU-hours. No hardware beyond a single workstation GPU is required.

## 29. Expected Figures

1. Unseen-family recall by arm (mean and worst client) with seed intervals.
2. Decomposition bar chart: generic pooling versus complementary knowledge, mean and worst client.
3. Dose-response curves (central, FedAvg, fine-tune) against local and no-family lines.
4. Per-family recall: local, central, no-family, oracle, ordered by support; irreducible families marked.
5. Known-family versus unseen-family trade-off per arm.
6. Sensitivity panel: α, model family, family set, grouping rule.

## 30. Expected Tables

1. Dataset and client summary (rows, malware share, family support per client).
2. Arm comparison at α = 0.05 with all primary and secondary metrics.
3. Decomposition table with paired intervals and gate results.
4. Dose-response table with effective peer sample counts.
5. Irreducible-family table with support and a feature-level note.

## 31. Limitations

- Four simulated clients; family exposure is manipulated, not observed.
- AVClass2 family labels are noisy and adware-dominated; static features only.
- Unseen-family evaluation mixes family novelty with cross-market shift unless own-market evaluation is used; where own-market support is thin, only pooled results exist.
- Dataset-level variance filtering is global preprocessing by the provider.
- Concept drift is not modelled; Google Play clients are split by era only.

## 32. Threats to Validity

- **Construct:** "unseen family" is defined by training exposure of AVClass2 tokens; feature-space novelty may differ.
- **Internal:** duplicated feature vectors and package reuse leak information unless grouped; mitigated by component grouping and by the package-only sensitivity, which is expected to show inflated recall.
- **Statistical:** ten seeds, four clients; interval widths reflect seed variation, not client-population variation.
- **External:** one benchmark, one feature family.

## 33. Ethical and Security Considerations

Public datasets only; no malware is executed or distributed; APK files are not needed. Results identify which families are hard to detect but reveal no evasion technique. The chapter avoids publishing per-sample features.

## 34. Chapter Structure

1. Introduction and threat-sharing motivation.
2. Related work (FL for Android malware; non-IID and missing-class FL; rare-class transfer).
3. Dataset, clients and controlled-exposure protocol.
4. Arms, oracles and metrics.
5. Results: existence, decomposition, dose-response, irreducible families, worst client.
6. Generality checks and negative results.
7. Discussion, limitations, implications for federated threat-sharing design.

## 35. Execution Order

1. Freeze this protocol and the confirmatory seed list.
2. Run leakage assertions on all seeds.
3. Main scenario with controls, then dose-response, second scorer/family set, natural scarcity, sensitivities.
4. Evaluate gates; decide whether the conditional mechanism study is triggered.
5. Produce figures and tables; write the chapter.

## 36. Completion Criteria

- All experiments run for ten confirmatory seeds with passing assertions.
- Every gate in Section 26 has a recorded outcome.
- Every claim in the chapter maps to a promoted gate or is worded as exploratory.
- Result files, seeds and environment are archived so that `run_all.sh` regenerates every table and figure.
