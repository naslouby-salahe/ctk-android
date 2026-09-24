# Complementary Threat Knowledge in Federated Android Malware Detection: A Controlled-Exposure Decomposition

**Short title:** *Complementary Threat Knowledge in Federated Android Malware Detection*  
**Acronym:** **CTK-Android**

> **Protocol status.** This document is the authoritative, implementation-ready research protocol for CTK-Android. It defines the scientific question, audited data assumptions, experimental design, controls, baselines, metrics, statistical procedures, promotion gates, failure handling, reproducibility requirements, execution order, and completion criteria before confirmatory results are inspected.

---

## 1. Project Identity and Research Thesis

CTK-Android studies a precise question in collaborative Android malware detection:

> **When a client has little or no local exposure to a malware family, how much of the benefit of collaboration comes from peers actually knowing that family, and how much would have been obtained from generic pooling of additional data anyway?**

The distinction is central. Better collaborative performance can arise for at least two different reasons:

1. **Generic pooling benefit:** a larger and more diverse training population improves representation, regularisation, prevalence coverage, or optimisation even when nobody in the federation has the target family.
2. **Complementary threat-knowledge benefit:** one or more peers possess labelled examples of a family that the target client lacks, and those examples specifically improve the target client's detection of that family.

CTK-Android isolates these effects with controlled family exposure, matched no-family controls, full-exposure upper bounds, dose-response experiments, natural-scarcity validation, worst-client analysis, and feature-space explanations of why some nominally unseen families benefit while others do not.

The project is primarily an **empirical and measurement contribution**. It does not assume that a new federated-learning algorithm is necessary. A new mechanism is considered only if the confirmatory evidence demonstrates meaningful residual headroom after strong simple baselines.

---

## 2. Relation to the Doctoral Research Programme

The doctoral research focuses on **collaborative/federated malware detection in heterogeneous IoT environments**, including non-IID clients, personalization, reliability of local evidence, calibration, worst-client behavior, scarce local evidence, robustness, and the question of when collaboration is genuinely beneficial.

CTK-Android contributes directly to that broader programme through a second security domain:

- clients have heterogeneous malware-family exposure;
- collaboration is compared with remaining local;
- a client's locally missing threat knowledge may be supplied by peers;
- worst-client outcomes are treated as first-class evidence;
- collaboration can help, fail to help, or provide only generic pooling benefit;
- some apparently unseen threats may already be represented through behavior shared with known malware;
- some threats remain poorly detectable even under full exposure;
- the study explicitly separates **collaboration value** from **data-volume value**.

The Android setting is not presented as an IoT experiment. Its value to the PhD lies in testing a central collaborative-malware-detection question under a different but closely related heterogeneous-client setting.

---

## 3. Scientific Scope

### 3.1 In scope

The study covers:

- supervised Android malware detection from static binary features;
- heterogeneous market/era client domains;
- locally unseen or locally scarce AVClass2-labelled malware families;
- controlled removal of family exposure from selected clients;
- federated and centralized collaboration baselines;
- client-specific operating points at fixed benign false-positive targets;
- total collaboration gain;
- generic pooling gain;
- complementary threat-knowledge gain;
- peer-sample dose-response;
- own-domain and cross-domain evaluation;
- worst-client and family-level performance;
- families that are not rescued under the tested representation and model family;
- feature-space novelty as a possible explanation of complementary benefit;
- strong leakage, identity, support, and negative controls;
- internal replication across family sets and model families.

### 3.2 Explicitly out of scope

The study does **not** claim to evaluate:

- globally novel or zero-day malware families;
- real organizations or deployed app-market security teams;
- dynamic Android behavior;
- causal effects of market or year;
- concept drift as a primary research question;
- privacy guarantees from FL alone;
- secure aggregation, differential privacy, membership inference, or cryptographic protection;
- malicious federated clients or poisoning;
- IoT devices;
- malware-family taxonomy ground truth;
- a new federated optimizer unless a predeclared mechanism gate is triggered.

“Unseen family” always means **locally unseen in the training data of the evaluated client**, not globally unseen to the federation and not a real-world zero-day.

---

## 4. Operational Definitions

### 4.1 Client

A client is a deployment-motivated **market/era domain** derived from a single-market Android app population. It is a simulated federated participant, not a claim of independent organizational ownership.

### 4.2 Locally unseen family

For client \(c\) and family \(f\), family \(f\) is locally unseen when the training partition available to client \(c\) contains **zero** malware samples labelled as \(f\), while peer clients retain eligible samples of \(f\).

### 4.3 Locally scarce family

A family is locally scarce when the target client contains only a very small fraction of the federation's available training exposure to that family while peers contain substantial exposure.

### 4.4 Known family

A malware family represented in the target client's training data and not intentionally hidden for that client.

### 4.5 Generic pooling

Improvement caused by collaborative access to additional training data **when the target family is absent everywhere in the collaborative training population**.

### 4.6 Complementary threat knowledge

The incremental improvement obtained when peer exposure to the target family is restored, relative to an otherwise matched collaborative model in which the family is absent everywhere.

### 4.7 Full-exposure upper bound

Training in which the hidden family exposure is restored. This is an empirical upper reference for the chosen data, representation, model family, and operating point. It is not a theoretical Bayes optimum.

### 4.8 Exposure-limited versus representation-limited failure

- **Exposure-limited:** performance improves substantially when peers receive target-family examples.
- **Representation-limited under the tested setup:** performance remains poor even with full family exposure, indicating that lack of exposure alone does not explain failure.

The latter wording is preferred to an absolute statement that collaboration “cannot” help.

---

## 5. Research Questions

### RQ1 — Local exposure failure

At a fixed client-specific false-positive target, how poorly do clients detect malware families that are absent from their own training data?

### RQ2 — Collaboration decomposition

How much of the improvement from collaborative training is attributable to generic pooling and how much is attributable specifically to complementary threat knowledge held by peers?

### RQ3 — Dose-response

How does locally unseen-family recall change as the number of peer training examples of the family increases from none to full exposure?

### RQ4 — Deployment-domain effect

Does the complementary-knowledge effect remain when evaluation is restricted to the target client's own market/era domain rather than malware pooled from all domains?

### RQ5 — Worst-client and family heterogeneity

Does collaboration improve the worst-off client, how variable is the benefit across clients and families, and which families remain poorly detected under full exposure?

### RQ6 — Why does complementary knowledge help some families but not others?

Can training-only feature-space novelty or similarity between a target family and malware already known by a client explain the magnitude of complementary-knowledge gain?

### RQ7 — Security cost

Does improving locally unseen-family recall reduce detection of known families or increase client false-positive rates?

### RQ8 — Generality and robustness

Do the central conclusions persist across a disjoint family set, multiple model classes, training-support levels, operating points, partition salts, and leakage-hardening choices?

### RQ9 — Residual mechanism headroom

After centralized pooling, FedAvg, FedProx, local fine-tuning, and simple local/global blending, is enough deployment-realistic headroom left to justify a new collaboration mechanism?

---

## 6. Hypotheses

The hypotheses are prospective and are allowed to fail. Failure narrows the corresponding claim rather than invalidating the entire study.

### H1 — Local deficit

Clients with zero local exposure to eligible families have materially lower recall on those families than full-exposure references at the same false-positive target.

### H2 — Collaboration benefit

Collaborative models improve locally unseen-family recall relative to local-only training.

### H3 — Decomposed benefit

Generic pooling explains a substantial fraction of the total collaboration benefit, while complementary threat knowledge contributes a separate positive component for at least a subset of families and clients.

### H4 — Family dependence

The complementary component is heterogeneous across malware families rather than a universal property of family absence.

### H5 — Dose-response

Complementary benefit increases with effective peer exposure and shows diminishing returns after sufficient target-family support.

H5 is compound. The dose-response gate (31.2) tests only the first part (benefit grows with effective peer exposure); it does not test diminishing returns. The confirmatory evidence supports the increase; a saturation or diminishing-returns regime was not observed within the tested exposure range, so that part is unresolved (see 31.3 M).

### H6 — Worst-client benefit

Complementary threat knowledge improves the worst-client outcome in at least some controlled-exposure settings, even when generic pooling alone does not.

### H7 — Feature-space explanation

Families that are more dissimilar to malware already represented in a client's training distribution obtain larger complementary-knowledge gains than families whose static behavior is already represented by known malware.

### H8 — Limited known-family cost

The strongest collaborative baseline does not materially reduce known-family recall at the primary operating point.

### H9 — Limited mechanism headroom

Strong simple collaborative baselines recover most of the available full-exposure gap, so a new mechanism is justified only if confirmatory evidence demonstrates substantial residual headroom.

---

## 7. Expected Contributions

The chapter is designed to support the following contribution package if the relevant gates pass:

1. **Controlled-exposure decomposition.** A protocol that separates generic pooling benefit from complementary threat-knowledge benefit for locally unseen malware families.
2. **Deployment-relevant own-domain evaluation.** A distinction between federation-wide family evaluation and the security benefit observed in the target client's own deployment domain.
3. **Peer-exposure dose-response.** Quantification of how much peer family evidence is required before measurable benefit appears.
4. **Family-dependent collaboration value.** Evidence that nominal family novelty alone is insufficient to predict benefit.
5. **Feature-space explanation.** A training-only analysis of whether representational novelty predicts when complementary knowledge matters.
6. **Worst-client evidence.** Client-level analysis rather than average-only collaboration claims.
7. **Representation-limited families.** Identification of families that remain poorly detected under full exposure in the tested feature/model setting.
8. **Leakage-hardened evaluation.** Grouping that prevents package reuse and identical feature-vector reuse across experimental partitions.
9. **Bounded negative findings.** Evidence on when simple fine-tuning, blending, peer selection, or additional FL complexity is unnecessary.

A new learning algorithm is **not** an expected contribution unless the mechanism trigger defined later is satisfied.

---

## 8. Dataset and Provenance

### 8.1 Primary feature and label source

The primary corpus is **LAMDA**, using the released variance-thresholded static feature representation.

Audited properties relevant to the protocol:

- 1,008,381 rows;
- SHA-256 is unique at row level;
- 925 binary static features in the selected variance-threshold configuration;
- malware label is consistent with VirusTotal detection count ≥ 4;
- benign label is VirusTotal detection count = 0;
- the 1–3 detection grey zone is absent;
- family labels are AVClass2-derived;
- many malware rows carry singleton family labels and are not eligible for family-level experiments;
- provider-side variance filtering was performed globally across the released corpus and cannot be reconstructed from unfiltered features;
- the year/month field corresponds to the dataset metadata's “added” field and is not treated as execution time, build time, or a verified first-seen date.

### 8.2 Market and package metadata

AndroZoo metadata supplies market membership and package identity after exact SHA-256 linkage.

The joined audit established complete hash matching for the LAMDA rows used in the study.

### 8.3 Licensing and redistribution

LAMDA and AndroZoo remain external data sources governed by their own terms. Raw applications, raw metadata exports, and row-level datasets are not redistributed by CTK-Android. The project releases only code, aggregate statistics, derived experimental summaries, and publication artifacts allowed by source terms.

### 8.4 Dataset freeze

Before confirmatory execution:

- source versions and checksums are frozen;
- row counts and schema are revalidated;
- the 925-feature contract is asserted;
- label-rule consistency is rechecked;
- market/package joins are rechecked;
- family support statistics are regenerated;
- all eligibility decisions are frozen before confirmatory results are inspected.

Any material source-data change requires a protocol amendment and a new confirmatory seed set.

---

## 9. Dataset Risks Already Incorporated into the Design

### 9.1 Duplicate static representations

A large fraction of rows share an identical 925-feature vector with at least one other row. Identical representations can cross package identities and may carry conflicting labels.

Therefore package-only grouping is insufficient for the primary evaluation.

### 9.2 Package reuse

The same package may occur across multiple APK rows and across markets. Package identity must not leak between fit, calibration, and test partitions.

### 9.3 Market overlap

Apps associated with multiple markets are excluded from client construction. The client populations use single-market rows to retain an interpretable domain definition.

### 9.4 Family-label noise

AVClass2 labels are treated as noisy malware grouping metadata, not biological-style ground truth. Singleton labels and insufficiently supported families are excluded from controlled family analyses.

### 9.5 Cross-market confounding

A hidden family's test examples may be concentrated in the peer market that owns most examples of that family. Cross-market evaluation can therefore mix family novelty with market-domain shift.

This is addressed by:

- target-client own-domain evaluation;
- natural-scarcity analysis;
- feature-space explanation;
- separate reporting of federation-wide and own-domain effects.

### 9.6 Global provider preprocessing

The released feature representation has already undergone global variance filtering. This is explicitly acknowledged as a dataset limitation and is not described as train-only feature selection.

---

## 10. Client Construction

The primary federation contains four deployment-motivated **market/era domains**:

- earlier Google Play apps;
- later Google Play apps;
- Anzhi apps;
- AppChina apps.

Only rows associated with exactly one market enter these client populations.

The Google Play split uses the audited metadata field only as a coarse era partition. It is not used to support a temporal-drift claim.

These four clients provide strong heterogeneity in:

- malware prevalence;
- family mixture;
- dataset size;
- static feature distribution;
- target-family exposure.

The clients are described as simulated market/era security domains, **not four independent organizations**.

---

## 11. Identity-Safe Partitioning

### 11.1 Primary split unit

The primary partition unit is the connected component induced by two equivalence relations:

1. rows sharing the same package name;
2. rows sharing the exact same 925-feature vector.

If two rows are connected through either relation, directly or transitively, they belong to the same partition component.

### 11.2 Partition proportions

Components are deterministically assigned to:

- 60% fit/training population;
- 20% calibration/validation population;
- 20% final test population.

### 11.3 Required invariants

Before any model is trained, automated checks must establish:

- no SHA-256 appears in more than one partition;
- no package component crosses partitions;
- no identical feature vector crosses partitions;
- all hidden-family removal happens **after** the base split is fixed;
- no test row influences family eligibility, model hyperparameters, thresholds, family grouping, or arm selection; eligibility is decided before the split from corpus-wide support and component structure only (Section 12.2);
- client-specific thresholds use only that client's benign calibration data;
- all experimental arms for one seed use matched underlying partitions.

A failure of any invariant invalidates the affected run.

### 11.4 Leakage sensitivity

Package-only grouping is retained only as an explicit sensitivity experiment quantifying how much an easier split would inflate performance. It is never used as evidence for the primary claims.

---

## 12. Family Eligibility and Freeze Rules

### 12.1 Eligible labels

Only named AVClass2 families with sufficient support are eligible. Singleton-per-hash labels, empty labels, and unsupported family tokens are excluded.

### 12.2 Controlled-exposure support

For client \(c\) and family \(f\), controlled hiding is eligible only when:

- peers collectively contain at least 150 training samples of \(f\) after the base split;
- the relevant test population contains at least 50 samples of \(f\) for federation-wide evaluation, guaranteed by the partitioner rather than checked afterwards (see the pre-split rule below);
- the hidden family can be removed from the target client's training data without making the target training population invalid.

Support thresholds of 100 and 300 peer samples and 30 and 100 test samples are sensitivity analyses.

**Pre-split eligibility rule.** Family eligibility is determined before the fit/calibration/test split, using corpus-wide support and identity-safe component structure only. The deterministic partitioner then constructs the 60/20/20 split so that every predeclared eligible client-family combination meets its minimum fit and test support. Only combinations for which such a valid identity-safe partition is feasible are materialized into the experiment plan. Final-test rows never add, remove, or replace eligible families after the split, so executed experiments contain only valid, fully supported combinations.

### 12.3 Family sets

Two disjoint predefined family sets are retained:

- a primary controlled-exposure family set;
- a disjoint replication family set.

Membership is frozen before confirmatory execution. Families are not replaced because they produce weak or inconvenient results.

A third additional family set may be examined **only as exploratory evidence** if needed to understand disagreement between the first two sets. It cannot retroactively change the primary claims or promotion gates.

### 12.4 Natural-scarcity eligibility

For a target client/family pair in the natural-scarcity analysis:

- the target client holds at most 5% of the federation's training exposure to the family;
- peers hold at least 150 family samples;
- the target client's own test domain contains at least 15 family samples.

No family is artificially deleted in this analysis.

---

## 13. Controlled Exposure Construction

For every confirmatory seed:

1. the base identity-safe data split is fixed;
2. eligible families are assigned to target clients according to the frozen family-set rule;
3. the target client's training examples of its assigned hidden families are removed;
4. peer clients retain those families in the complementary-knowledge condition;
5. an otherwise matched no-family condition removes the same families from all clients;
6. sample counts are replenished from eligible non-hidden training rows so collaborative conditions are size matched;
7. full-exposure references restore the hidden family examples.

The controlled intervention changes **family exposure**, not the test set, client identity, feature representation, or operating-point protocol.

---

## 14. Evaluation Populations

### 14.1 Primary deployment population — own-domain unseen families

For client \(c\), evaluate hidden-family malware drawn from client \(c\)'s own market/era test population whenever support is sufficient.

This is the clearest deployment interpretation: how well does the client's detector identify locally unseen malware appearing in its own domain?

### 14.2 Primary decomposition population — federation-wide hidden-family test set

Evaluate hidden-family test samples across all eligible client domains.

This population gives higher support and is used for the most precise pooling-versus-complementary decomposition, while being reported explicitly as a broader cross-domain evaluation.

### 14.3 Known-family population

Target client's own-domain malware test samples excluding hidden families.

### 14.4 Benign operating-point population

Target client's own-domain benign calibration and test rows.

The calibration subset chooses the decision threshold; the test benign subset estimates realised FPR.

---

## 15. Training Support

The primary training budget is up to 6,000 rows per client sampled at the client's natural class prevalence after controlled family removal.

The same client-level training budget is used across matched arms for a seed so that the no-family control does not accidentally become a smaller-data control.

A 1,500-row client training budget is retained as a lower-support sensitivity.

No result may be attributed to complementary family knowledge if the compared arms differ materially in total training size for reasons other than the intended peer-family dose intervention.

---

## 16. Model Family and Training Protocol

### 16.1 Primary model

A supervised multilayer perceptron over the 925 binary static features is the primary scorer.

The architecture and optimization settings are fixed using development evidence only and are not tuned on confirmatory seeds.

### 16.2 Mandatory comparators

The study includes:

- linear classifier;
- gradient-boosted tree model;
- local-only training;
- centralized pooled training;
- FedAvg;
- FedProx;
- FedAvg followed by local fine-tuning;
- simple local/collaborative score blending;
- no-family collaborative controls;
- full-exposure references.

### 16.3 Fair-training audit

Before confirmatory runs, development-only ablations must verify that major conclusions are not an artifact of under-training one arm. At minimum:

- local training duration is checked over a small predefined grid;
- fine-tuning duration is checked over a small predefined grid;
- FedProx regularization strength is checked over a small predefined grid;
- FedAvg round/local-epoch settings are fixed afterward.

Hyperparameters are frozen before confirmatory seeds are run.

**Stage D grids and selection rule (frozen).** The predeclared grids are local training epochs {10, 20, 40}, fine-tuning epochs {2, 5, 10}, and FedProx proximal strength {0.001, 0.01, 0.1}, each evaluated on the development seeds with every other setting fixed and all grid points sharing seeds and partitions. For each grid the value with the highest mean own-domain **calibration-partition** AUROC across development seeds and clients is selected; ties go to the smaller value. Test rows never enter this selection, and no tolerance or additional threshold is used. The selected values are written to the validated configuration and are the only values used by confirmatory runs. The grids are not extended after their results are seen.

Selected on development seeds 1-5 (mean calibration AUROC of the selected value): local epochs 10 (0.929), fine-tuning epochs 2 (0.918), FedProx strength 0.1 (0.931). Longer local or fine-tuning training lowered calibration AUROC, so no arm is under-trained; all three selected values lie on a grid edge, and the FedProx differences are small (0.9307 at 0.01 versus 0.9314 at 0.1). FedAvg rounds (20) and local epochs (2) are fixed at their configured values, and pooled centralized training keeps its configured 20 epochs; neither was searched.

### 16.4 No test-driven arm creation

No new arm, hybrid, mixture, gate, threshold rule, or peer-selection rule may be introduced because it looks favorable on confirmatory test outcomes.

Any future mechanism must be designed on development evidence, frozen, and evaluated on a fresh untouched confirmatory seed set.

---

## 17. Operating-Point Protocol

Each detector produces a continuous malware score.

For each client, the primary threshold is chosen as the empirical \((1-\alpha)\)-quantile of the client's own benign calibration scores.

Primary operating point:

- \(\alpha = 0.05\).

Sensitivity operating points:

- \(\alpha = 0.01\);
- \(\alpha = 0.10\).

The 1% target is treated as a tail-resolution sensitivity. If benign calibration support is insufficient to estimate the 99th percentile with acceptable stability, the result is labelled **INSUFFICIENT_EVIDENCE** rather than interpreted as a strong security comparison.

Malware labels are never used to choose the client threshold.

---

## 18. Core Experimental Comparisons

### Local-only baseline

Each client trains only on its own available training data after the controlled exposure intervention.

### Centralized collaboration

All client training rows are pooled centrally. This is an information-rich collaboration reference, not the deployable privacy-preserving target.

### FedAvg

Standard full-model federated averaging over the four simulated clients.

### FedProx

Federated optimization baseline for client heterogeneity.

### FedAvg with local fine-tuning

Shared training followed by local adaptation using only the client's own training data.

### Simple local/global blends

Simple score-level mixtures establish whether a cheap personalization baseline already captures remaining local/global trade-offs.

### No-family-anywhere collaborative controls

Matched central and federated models trained with the target family removed from every client. These isolate generic pooling.

### Full-exposure references

Matched models trained with the target families restored everywhere they naturally occur. These quantify available exposure headroom under the selected representation and model family.

---

## 19. Decomposition Estimands

For recall \(R\) under a fixed operating point and collaborative arm \(P\):

### Total collaboration gain

\[
\Delta_{\text{total}} = R(P_{\text{peer-family-present}}) - R(\text{local})
\]

### Generic pooling gain

\[
\Delta_{\text{pool}} = R(P_{\text{family-absent-everywhere}}) - R(\text{local})
\]

### Complementary threat-knowledge gain

\[
\Delta_{\text{CTK}} = R(P_{\text{peer-family-present}}) - R(P_{\text{family-absent-everywhere}})
\]

### Complementary share

When \(\Delta_{\text{total}}\) is positive and sufficiently resolved:

\[
S_{\text{CTK}} = \frac{\Delta_{\text{CTK}}}{\Delta_{\text{total}}}
\]

### Oracle-gap recovery

For arm \(A\):

\[
G(A) = \frac{R(A)-R(\text{local})}{R(\text{full-exposure central})-R(\text{local})}
\]

Ratios are not interpreted when the denominator is effectively zero or its uncertainty includes no meaningful headroom.

The decomposition is computed separately for:

- central collaboration;
- FedAvg;
- mean client;
- worst client;
- federation-wide hidden-family population;
- own-domain hidden-family population where support permits.

---

## 20. Peer-Exposure Dose-Response

Peer exposure is manipulated while the target client remains at zero local exposure.

Requested peer-family sample levels:

- 0;
- 1;
- 10;
- 50;
- 100;
- 500;
- 1,000;
- all available.

The actual effective peer count is reported because client-level training caps and family availability may prevent some requested doses from being realized exactly.

**Dose semantics (clarified after confirmatory analysis; see 31.3).** The *requested dose* is the design level; the *effective dose* is the number of the family's peer training rows actually present. The `all available` level has no requested dose but has an effective dose like any other level, and it is evaluated whenever that effective dose satisfies the criterion. Claims that refer to "at least 100 effective peer samples" are evaluated on effective, not requested, exposure.

Primary questions:

- At what peer support does recall begin to increase measurably?
- Is the curve monotone in expectation?
- Where does the gain saturate?
- Does the dose threshold differ across families?
- Does centralized pooling require less family support than FedAvg to obtain the same gain?

No statement such as “N samples are enough” is made unless supported across confirmatory seeds and multiple families.

---

## 21. Natural-Scarcity Validation

The controlled intervention is necessary for causal decomposition but is artificial.

A separate natural-scarcity experiment therefore evaluates client/family pairs where:

- the target client naturally contains very little training exposure;
- peers naturally contain substantial exposure;
- no training examples are deleted.

For each eligible pair, compare:

- local-only;
- collaborative training with peer family exposure;
- matched no-family control where the family is removed from the collaborative pool.

This analysis validates whether the controlled-exposure phenomenon appears in naturally imbalanced market-family distributions.

Its effect magnitude is **not** numerically pooled with the controlled-exposure effect because the estimands differ.

Natural scarcity is nevertheless the principal within-dataset (ecological) validation of the controlled-exposure phenomenon; it uses the same LAMDA/AndroZoo corpus and is not independent-dataset or external validation: agreement in sign, practical magnitude and seed consistency of the complementary component under naturally imbalanced exposure supports the view that the controlled intervention is not an artefact of artificial removal. It is reported side by side with, never merged into, the controlled estimate, and it is not a confirmatory gate unless a gate says so.

---

## 22. Feature-Space Novelty Analysis

A central risk is that “unseen family” at the AVClass2 label level does not imply unseen behavior in the static feature space. A family may be absent by name while its malicious feature patterns are already represented by other known families.

This analysis is therefore mandatory.

### 22.1 Training-only family representation

For every target client and eligible hidden family, construct family descriptors from **training data only**.

Candidate descriptors include:

- binary feature prevalence vector of the hidden family using peer training rows;
- centroid distance to the target client's known-malware population;
- nearest known-family centroid distance;
- maximum Jaccard similarity to known-family feature prevalence;
- fraction of frequently active hidden-family features already represented among known malware;
- distance to the target client's benign centroid;
- model-independent feature overlap statistics.

No descriptor may use target test outcomes.

### 22.2 Association with complementary gain

Test whether training-only novelty measures predict per-family complementary-knowledge gain.

Primary analysis:

- Spearman association between a predeclared novelty score and \(\Delta_{\text{CTK}}\);
- paired family-level visualization of novelty versus gain;
- comparison of high- and low-novelty families using thresholds defined without outcome optimization.

### 22.3 Interpretation

If novelty predicts gain, the chapter may claim that **behavioral representation overlap helps explain why some nominally unseen families benefit little from explicit peer exposure**.

If it does not, the study reports the null result and does not invent a family-routing mechanism.

This analysis is explanatory, not a mechanism unless the mechanism gate is separately satisfied.

---

## 23. Family-Level Failure Analysis

For every eligible family, report:

- local recall;
- no-family collaborative recall;
- collaborative recall with peer exposure;
- full-exposure recall;
- known support counts;
- effective peer dose;
- feature-space novelty descriptors;
- operating-point validity.

A family is labelled **poorly rescued under full exposure** when its full-exposure recall remains below a predeclared threshold of 0.60 at \(\alpha=0.05\) in the primary model.

The stronger phrase **representation-limited under the tested setup** requires the family also to remain poor in at least one non-neural comparator or in a second model family.

The chapter must not claim that such a family is fundamentally undetectable.

---

## 24. Primary Outcomes

### 24.1 Primary deployment outcome

**Own-domain unseen-family recall at \(\alpha=0.05\)**, macro-averaged across eligible clients with sufficient own-domain support.

### 24.2 Primary decomposition outcome

**Federation-wide unseen-family recall at \(\alpha=0.05\)** under local, no-family collaborative, peer-family collaborative, and full-exposure conditions.

### 24.3 Primary federated effect

Paired FedAvg complementary-knowledge gain:

\[
R(\text{FedAvg, peer family present}) - R(\text{FedAvg, family absent everywhere})
\]

### 24.4 Primary reference effect

The same decomposition under centralized pooled training.

Central training is reported as an information-sharing reference; the federated effect remains central to the chapter identity.

---

## 25. Secondary Outcomes

Report:

- family-macro unseen-family recall;
- micro unseen-family recall;
- known-family recall;
- client-macro recall;
- worst-client unseen-family recall;
- client recall dispersion;
- family recall dispersion;
- realised client FPR;
- worst-client FPR;
- FPR dispersion;
- AUROC as a threshold-independent diagnostic;
- AUPRC where prevalence makes it informative;
- total collaboration gain;
- generic pooling gain;
- complementary-knowledge gain;
- complementary share;
- oracle-gap recovery;
- negative-transfer cost on known families;
- per-family full-exposure ceiling;
- effective peer sample count.

Accuracy alone is never a primary metric.

---

## 26. Worst-Client and Fairness View

For each seed and arm:

- compute the minimum client unseen-family recall;
- compute the maximum client FNR on eligible unseen families;
- compute worst-client FPR on benign test data;
- report dispersion of recall and FPR across clients.

Worst-client metrics are reported alongside mean-client metrics rather than as a post-hoc fairness section.

A gain in average recall that materially worsens the worst client must be discussed as a trade-off, not an unconditional improvement.

---

## 27. Negative Controls

The following controls are mandatory.

### Family absent everywhere

Separates generic pooling from complementary family knowledge.

### Zero-dose peer exposure

Checks that the dose-response baseline agrees with the no-family condition.

### Family-label permutation

Randomly permute eligible malware-family labels while preserving family-size distribution. Complementary gain should collapse toward zero if the measured effect genuinely depends on family-specific exposure. The decision rule is an equivalence criterion, frozen in Section 31.2: the 95% BCa paired interval of the permutation-control complementary gain must lie within \(\pm 0.03\) absolute recall.

### Broken grouping sensitivity

Repeat a limited primary comparison using package-only grouping to quantify how much weaker leakage protection inflates results. This is a sensitivity, not evidence.

### Sample-size matching

Matched collaborative conditions must contain comparable total training counts so that family restoration is not silently a training-volume intervention.

### Target-independence assertions

No family eligibility, threshold, hyperparameter, or mechanism decision may depend on final test outcomes.

---

## 28. Model and Protocol Robustness

The main conclusions are stress-tested across:

- primary MLP;
- linear model;
- gradient-boosted trees;
- primary family set;
- disjoint replication family set;
- 1,500 versus 6,000 training rows per client;
- \(\alpha=0.01, 0.05, 0.10\);
- multiple partition salts;
- multiple support eligibility thresholds;
- own-domain versus federation-wide evaluation;
- primary component grouping versus package-only sensitivity;
- results with and without the three highest-support families;
- de-duplicated test representations in a sensitivity where each identical feature vector contributes once.

A conclusion is described as **robust** only when it survives the predeclared relevant robustness checks. Otherwise wording is explicitly scoped.

Robustness of the complementary-knowledge effect means persistence of the effect's **sign and practical magnitude**. It does not mean identical decomposition proportions: the split between generic pooling and complementary knowledge may differ by model class, training support and exposure design.

---

## 29. Development and Confirmatory Separation

### Development evidence

Previously used development seeds and exploratory results may be used for:

- debugging;
- feasibility;
- choosing fixed hyperparameters;
- selecting the predefined model ladder;
- defining gates;
- estimating compute burden.

They are not confirmatory evidence.

### Confirmatory seeds

Use ten untouched confirmatory seeds:

**100–109**.

A seed fixes:

- component split salt;
- family assignment where randomized;
- training subsampling;
- model initialization;
- dose sampling.

### Freeze rule

Before the first confirmatory result is inspected, freeze:

- family sets;
- client definitions;
- eligibility rules;
- model hyperparameters;
- thresholds and calibration rules;
- primary and secondary metrics;
- statistical tests;
- claim gates;
- figure/table definitions;
- mechanism trigger.

If a material design error is discovered afterward, the affected confirmatory results are invalidated, the protocol is amended transparently, and a fresh unused confirmatory seed range is selected.

---

## 30. Statistical Analysis

### 30.1 Paired design

All arm comparisons are paired by confirmatory seed using identical partitions and exposure assignments wherever logically possible.

### 30.2 Effect reporting

For each primary paired contrast report:

- mean paired difference;
- median paired difference;
- 95% BCa paired bootstrap confidence interval;
- exact two-sided Wilcoxon signed-rank test where assumptions permit;
- number of seeds with positive difference;
- standardized paired effect size as descriptive context.

Statistical significance never replaces the predeclared practical-effect gate.

### 30.3 Cluster uncertainty within seed

For family-level and row-level rates, use cluster bootstrap over the primary split component rather than treating rows as independent.

For family-level explanatory analyses, families—not individual APK rows—are the unit of inference.

### 30.4 Multiple comparisons

Holm adjustment is used for the predefined primary contrast family.

The principal confirmatory contrast family at \(\alpha=0.05\) is:

1. FedAvg peer-family present versus local;
2. FedAvg family absent everywhere versus local;
3. FedAvg peer-family present versus FedAvg family absent everywhere.

The analogous centralized contrasts are reported as a reference family.

Other sensitivity and ablation contrasts are explicitly labelled exploratory unless separately predeclared.

### 30.5 Complementary share

The complementary share uses a BCa bootstrap of the ratio of seed-level mean effects. It is not reported when total gain is not reliably positive or the denominator is numerically unstable.

### 30.6 Small-sample discipline

With ten seeds, exact tests and effect intervals are preferred over asymptotic claims. Results that remain too uncertain are labelled **INSUFFICIENT_EVIDENCE**.

---

## 31. Scientific Gates

Gates are divided into **structural validity gates**, which can invalidate an experiment, and **claim gates**, which determine allowable wording.

### 31.1 Structural validity gates

#### Data-integrity gate

Pass only if:

- expected source rows and schema are present;
- label rule is consistent;
- client keys resolve;
- family labels meet eligibility semantics;
- dataset checksums match the frozen data release.

#### Identity/leakage gate

Pass only if no connected component crosses fit, calibration, and test partitions.

#### Controlled-exposure gate

Pass only if:

- target client training exposure is exactly zero for hidden families;
- peers contain the required family support in the peer-present condition;
- family exposure is zero everywhere in the no-family condition;
- evaluated hidden-family rows belong only to the final test partition;
- sample-size matching is respected.

#### Operating-point gate

For the primary 5% target, realised benign test FPR must be sufficiently close to the intended operating point to support fair recall comparison. Large deviations are reported and the affected comparison is not interpreted as equal-FPR evidence.

### 31.2 Claim promotion gates

#### Local-deficit claim

Promote if local unseen-family recall is materially below the full-exposure reference with a positive paired interval in at least 8 of 10 confirmatory seeds.

#### Collaboration-benefit claim

Promote if FedAvg improves unseen-family recall over local training with positive practical effect and a paired interval excluding zero.

#### Complementary-knowledge claim

Promote only if all are true:

- \(\Delta_{\text{CTK}} \ge 0.03\) absolute recall in the primary decomposition;
- 95% BCa paired interval excludes zero;
- effect is positive in at least 8/10 seeds;
- family-label permutation produces a null-compatible complementary effect, defined as the 95% BCa paired interval of the permutation-control \(\Delta_{\text{CTK}}\) lying entirely within \(\pm 0.03\) absolute recall (the same practical-effect threshold as above). An interval entirely outside that band rejects the claim; an interval that straddles a band edge, or is unavailable, leaves it INSUFFICIENT_EVIDENCE;
- sample-size matching passes.

If the effect passes only in one family set or only in federation-wide evaluation, wording is restricted accordingly.

#### Generic-pooling-majority claim

Promote only if the generic-pooling share exceeds 50% and the interval excludes 50% for the specified evaluation population.

Otherwise state the measured components without a majority claim.

#### Dose-response claim

Promote if:

- mean dose-response is non-decreasing apart from sampling noise;
- exposure of at least 100 effective peer samples improves recall by at least 0.03 over zero dose;
- the pattern is not driven exclusively by one family.

#### Own-domain benefit claim

Promote only if the own-domain complementary effect has a positive interval and passes support requirements. If unresolved, cross-domain results must not be presented as direct deployment-domain evidence.

#### Worst-client benefit claim

Promote only if the paired worst-client complementary effect has a positive interval. Otherwise report worst-client results descriptively.

#### Known-family safety claim

Promote “no material known-family cost” when the strongest federated arm changes known-family recall by no more than ±0.02 relative to local and does not materially worsen FPR.

#### Family-dependence claim

Promote if complementary gain varies materially across the two frozen family sets or across families with family-level intervals/heterogeneity analysis supporting the distinction.

#### Representation-limited-family claim

Promote only for families whose full-exposure recall remains poor across the primary model and at least one independent model family. Wording remains “under the tested static representation and models.”

#### Feature-novelty explanation claim

Promote if a predeclared training-only novelty score shows a practically meaningful association with complementary gain, with uncertainty excluding a negligible relationship and consistent direction across relevant sensitivity analyses.

#### New-mechanism trigger

A new peer-selection or family-aware collaboration mechanism is allowed only if the best strong simple collaborative baseline leaves more than:

- 0.10 absolute mean unseen-family recall to the full-exposure central reference; or
- 0.15 absolute worst-client recall;

and there is a deployment-available predictor of that residual gain.

If the trigger fails, the mechanism line is closed and the empirical decomposition remains the contribution.

---

### 31.3 Post-Confirmatory Evidence-Preserving Analyses and Interpretation Clarifications

Added after the confirmatory campaign and recorded in `docs/decisions/protocol-amendments.md`. No original confirmatory arm, threshold, seed, family set, hyperparameter, or gate was changed, and no fresh seeds are required. Analyses below use only already-generated confirmatory evidence and do not modify original gates or claim outcomes unless they correct a documented implementation bug.

Every reported result is labelled as exactly one of: **A** original confirmatory evidence, **B** predeclared confirmatory robustness or sensitivity evidence, **C** post-confirmatory evidence-preserving analysis, **D** proposed future work.

**A. Dose-response clarification.** The 100-effective-peer-sample, +0.03 gain, monotonicity and not-one-family criteria are unchanged. Levels are ordered by effective exposure; the `all available` level is a level whose effective exposure is compared with the 100-sample criterion; the family-robustness criterion uses the levels that satisfy the criterion. Where a level mean is used, an observation-level sensitivity (rows with at least 100 effective samples) is reported alongside. Because caps and availability make effective exposure much smaller than requested exposure, low requested doses may never reach the criterion.

**B. Evidence-preserving analyses.** Local-baseline-anchored worst-client robustness (the worst client under the local baseline is frozen per seed and followed through every arm; this does not replace the predeclared worst-client gate, and total and pooling gains against local are subject to selection on the local baseline, so the complementary gain is the cleaner contrast); federated-arm trade-off analysis (descriptive; no composite score or winner is defined); a canonical complementary-knowledge robustness synthesis; and family-level mechanism patterns (descriptive, no rigid taxonomy).

**C. Natural scarcity** is elevated as within-dataset (natural-exposure) validation of the controlled-exposure phenomenon, as described in 21. It reproduces the effect under naturally imbalanced family exposure in the same corpus; it is not external validation and does not replace independent-dataset replication. Estimands are not merged.

**D. Robustness** is as clarified in 28.

**E. Known-family safety.** The gate evaluates the strongest federated arm, as written. Wording must be arm-specific: an arm that satisfies the tolerance does not certify other arms, and any arm outside the tolerance is reported as such.

**F. Feature novelty.** The gate outcome is preserved as stored. Gate non-passage with very few families and wide intervals is unresolved evidence, not a demonstrated absence of an association; prose must not say novelty is disproven or proven. Other descriptors are exploratory only.

**G. Representation-limited findings.** Exposure alone does not explain all family-level failures; the bounded statement applies to the tested static representation and models.

**H. Generic pooling.** The rejected generic-pooling-majority gate stands. For the primary MLP decomposition the measured shares may support the bounded statement that generic pooling is not the dominant component; this is not extended to the linear model or other designs unless their own intervals support it, and no retrospective dominance gate is created.

**I. Own-domain caveat.** The federation-wide permutation control is the gated negative control. Own-domain and worst-client permutation behaviour is reported separately; where its interval is not inside the equivalence band, causal wording for that population is limited. No own-domain permutation gate is added retrospectively.

**J. Family-dependence scope.** The family-dependence claim is evaluated on the two frozen family sets only (primary and replication), not on arbitrary experiment pooling.

**L. Per-client CTK analysis (class C).** For each of the four clients, the decomposition (local, no-family, peer-family and same-arm full-exposure recall; total, pooling and CTK gain; known-family change; realised FPR; support; contributing seeds; eligible family pairs) is computed from stored client-level metrics for FedAvg, FedProx and centralized arms at the primary operating point, federation-wide and own-domain. It uses existing results only, creates no gate, is descriptive and exploratory, and does not alter any original confirmatory outcome. A BCa interval is reported only when the client contributes at least as many seeds as the existing complementary-knowledge positive-seed requirement (8); otherwise the row is labelled descriptive and has no interval. With four clients, associations with client properties are descriptive and not causal.

**M. Dose interpretation.** The promoted dose gate supports that recall improves as effective peer exposure increases. It does not establish saturation or diminishing returns: recall is still rising at the largest effective exposure. Both statements must be kept apart wherever H5 is cited.

**N. Novelty positioning.** After the bounded literature audit in `docs/Novelty Audit.md`, the residual contribution is stated as a measurement design and empirical decomposition on one corpus, with "no closely matching study found in the audited literature" wording. The audit is limited (no forward citation search, mostly abstract-level reading) and does not license priority language.

**K. Aggregation naming.** The seed-paired macro complementary gain and the micro-pooled hits/trials complementary gain are different estimands and carry different names in every artifact; partition salts are reported separately, never as extra seeds.

---

## 32. Claim Outcomes and Allowed Failure Modes

The study is designed so that a failed hypothesis does not force a false “no contribution” conclusion.

Possible scientifically valid outcomes include:

### Complementary knowledge is strong

The chapter emphasizes peer-held family knowledge and dose-response.

### Complementary knowledge is small but nonzero

The chapter emphasizes decomposition: much apparent collaborative value comes from pooling, while a bounded family-specific component remains.

### Complementary knowledge is family dependent

The chapter emphasizes **when** peer knowledge helps rather than assuming a universal benefit.

### Complementary knowledge vanishes for some family sets

The chapter reports that family-label absence alone is insufficient to identify a collaboration need and investigates representation overlap.

### Pooling dominates

The chapter reports that much of the supposed “knowledge transfer” explanation is actually generic collaborative data benefit.

### Full exposure still fails

The chapter identifies representation/model limitations rather than incorrectly attributing failure to lack of collaboration.

### No mechanism headroom remains

The chapter explicitly reports that standard pooled/FedAvg/fine-tuned approaches capture the available benefit, so additional collaboration complexity is not justified.

These are all valid outcomes if supported by the frozen protocol.

---

## 33. Novelty and Positioning Rules

The project does not claim novelty for:

- applying FL to Android malware detection;
- non-IID Android FL;
- rare-class transfer in FL;
- clients missing classes;
- FedAvg, FedProx, or local fine-tuning;
- the general observation that peers can sometimes help a client detect a class it lacks.

The defensible residual contribution is the combination of:

- controlled family exposure;
- a matched family-absent-everywhere pooling control;
- explicit pooling-versus-complementary decomposition;
- client and worst-client analysis at fixed FPR;
- peer-exposure dose-response;
- own-domain evaluation;
- family-level rescue/failure characterization;
- feature-space explanation of family-dependent collaboration value.

The strongest neighboring bodies of work include federated rare-class transfer, class-incremental intrusion detection, prototype exchange for disjoint/rare classes, and Android malware FL under non-IID or drift. A bounded collision audit (`docs/Novelty Audit.md`) found no direct collision and three partial ones (vacant-class evaluation in label-skewed FL, label-set-size manipulation with fixed sample counts, a theory of missing class support); it does not replace the pre-submission citation-chaining audit.

Before submission, perform a final citation-chaining audit of the closest works published through the submission date.

Forbidden priority language unless independently proven:

- “first”;
- “novel”;
- “unprecedented”;
- “state of the art.”

---

## 34. Reporting Rules

### Always report

- exact client construction;
- whether evaluation is own-domain or federation-wide;
- family support counts;
- actual effective peer dose;
- realised FPR;
- mean and worst-client results;
- no-family control;
- full-exposure reference;
- known-family trade-off;
- uncertainty intervals;
- failed gates;
- family-set disagreement;
- negative controls.

### Never collapse

Do not collapse:

- generic pooling and complementary knowledge into one “federation gain” number;
- own-domain and cross-domain evaluation;
- micro and family-macro recall;
- development and confirmatory evidence;
- central and federated training;
- family-label novelty and feature-space novelty.

### Language discipline

Use:

- “locally unseen family”;
- “AVClass2-labelled family”;
- “simulated market/era clients”;
- “complementary threat-knowledge gain”;
- “generic pooling gain”;
- “under the tested static representation.”

Avoid:

- “zero-day”;
- “unknown malware” unless defined narrowly;
- “real organizations”;
- “privacy preserving” merely because FL is used;
- “collaboration transfers knowledge” when only total pooled gain was measured;
- “undetectable family” from one model/representation.

---

## 35. Reproducibility Contract

The implementation must satisfy the following before confirmatory evidence is accepted.

### Determinism

- every run has an explicit seed;
- data partitions are deterministic given the frozen data and seed;
- family assignments are deterministic given the seed;
- stochastic model initialization is seeded;
- result records contain all parameters needed to reproduce the run.

### Configuration discipline

- scientific parameters are centralized rather than scattered as magic numbers;
- no hidden defaults differ between arms;
- the same parameter source drives execution and reporting;
- invalid combinations fail early.

### Idempotency

Re-running preprocessing or an experiment with the same frozen inputs and seed produces the same derived data contract and equivalent metrics within deterministic-library tolerance.

### Data provenance

Every confirmatory result records:

- source-data fingerprint;
- client support counts;
- family eligibility counts;
- split seed;
- model/scenario parameters;
- software environment information;
- result status.

### No hidden manual intervention

No confirmatory result may depend on manually deleting rows, selecting a favorable family after results, editing generated metrics, or choosing a threshold by looking at test labels.

### Clean-environment check

Before manuscript evidence is frozen, the complete confirmatory workflow must be rerun from a clean environment using only documented dependencies and external raw-data access.

---

## 36. Implementation Quality Contract

The implementation should be built for auditability rather than breadth.

### Required characteristics

- typed domain objects for experiment concepts rather than unstructured dictionaries at core boundaries;
- enumerations for finite scientific choices;
- centralized validated configuration;
- no duplicated metric or split logic;
- no silent coercion of invalid values;
- deterministic preprocessing;
- immutable raw data;
- cached expensive deterministic preprocessing;
- machine-readable experiment outputs;
- publication tables and figures derived from those machine-readable outputs;
- descriptive experiment identities rather than opaque numbered regimes;
- clear separation between exploratory and confirmatory execution;
- no test-data access in training, calibration, eligibility, or mechanism selection.

### Testing requirements

At minimum implement automated tests for:

- dataset schema and feature count;
- SHA uniqueness assumptions;
- market/client eligibility;
- component construction;
- partition disjointness;
- hidden-family removal;
- peer-family presence;
- no-family control correctness;
- sample-size matching;
- threshold calibration source;
- metric definitions;
- decomposition identities;
- deterministic reruns;
- result completeness;
- figure/table regeneration from saved metrics.

Integration tests must cover the full path from audited data through one small training run to final metrics.

A lightweight end-to-end smoke workflow must complete quickly enough to run routinely before larger experiments.

### Code-quality constraints

- no unnecessary compatibility shims;
- no dead experimental branches retained in the main implementation;
- no result-dependent hardcoded exceptions;
- no AI-authorship metadata;
- no Docker requirement;
- no generated narrative reports required for scientific execution.

---

## 37. Pre-Confirmatory Audit Checklist

The confirmatory campaign must not start until all of the following are PASS.

### Data

- raw sources accessible;
- expected versions/checksums frozen;
- row counts reproduced;
- 925-feature schema reproduced;
- label rule reproduced;
- market join reproduced;
- package identity present;
- family semantics documented;
- eligible family support regenerated.

### Leakage

- component construction validated;
- zero components cross partitions;
- multi-market rows excluded from client construction;
- hidden families absent from target training;
- peers retain required family support;
- no-family control removes target family everywhere;
- test rows untouched by development decisions.

### Baselines

- local model converges adequately;
- centralized model implemented;
- FedAvg implemented;
- FedProx implemented;
- local fine-tuning implemented;
- simple blend implemented;
- no-family controls implemented;
- full-exposure references implemented.

### Metrics

- recall definitions validated;
- own-domain and federation-wide populations validated;
- known-family population validated;
- FPR and thresholding validated;
- worst-client calculation validated;
- family-macro calculation validated;
- decomposition arithmetic validated.

### Statistics

- seed pairing validated;
- BCa paired intervals validated;
- exact Wilcoxon implementation validated;
- cluster bootstrap validated;
- Holm correction validated.

### Reproducibility

- smoke run passes;
- development rerun is stable;
- confirmatory seeds remain untouched;
- software environment captured;
- resource budget confirmed.

Any unresolved structural item blocks confirmatory execution.

---

## 38. Execution Plan

### Stage A — Environment and data verification

Reproduce the dataset audit from raw sources and freeze data fingerprints.

**Exit condition:** every dataset and schema gate passes.

### Stage B — Identity-safe preprocessing

Construct client populations, connected partition components, family support tables, and deterministic partitions.

**Exit condition:** zero identity/vector leakage and all client-support assertions pass.

### Stage C — Fast smoke execution

Run a minimal single-seed, reduced-support path through local, centralized, FedAvg, no-family, full-exposure, thresholding, decomposition, and reporting.

**Exit condition:** complete metrics with no manual repair.

### Stage D — Development baseline audit

On development seeds only:

- verify training convergence;
- check local epoch sensitivity;
- check FedProx strength;
- check fine-tuning duration;
- verify simple blends;
- verify equal sample counts;
- verify operating-point stability.

Freeze all hyperparameters afterward.

**Exit condition:** strong simple baselines are fairly implemented and frozen.

### Stage E — Explanatory development analyses

Using development data only:

- verify feature-space novelty descriptors;
- verify family-label permutation control;
- verify second-family-set construction;
- verify dose implementation;
- verify natural-scarcity pair construction.

No new mechanism is created unless the mechanism trigger is already supported by development headroom and can be specified without confirmatory outcomes.

**Exit condition:** all confirmatory analyses are executable without design decisions remaining.

### Stage F — Protocol freeze

Freeze:

- data version;
- client definitions;
- family sets;
- metrics;
- statistical plan;
- gates;
- hyperparameters;
- expected figures/tables;
- confirmatory seed range.

**Exit condition:** no scientific degree of freedom remains that could be changed after seeing confirmatory outcomes.

### Stage G — Confirmatory main experiment

Run all ten confirmatory seeds for:

- local;
- central;
- FedAvg;
- FedProx;
- FedAvg + fine-tuning;
- simple blends;
- no-family controls;
- full-exposure references.

Run validation assertions before accepting each seed.

**Exit condition:** all ten valid paired seeds complete.

### Stage H — Confirmatory decomposition and own-domain analysis

Compute:

- total gain;
- generic pooling gain;
- complementary gain;
- complementary share where stable;
- own-domain effect;
- worst-client effect;
- known-family cost.

**Exit condition:** principal claim gates have explicit outcomes.

### Stage I — Confirmatory dose-response and family analysis

Run dose-response, family-macro analysis, full-exposure failure analysis, and family-level feature-novelty association.

**Exit condition:** every family-level claim has support and uncertainty.

### Stage J — Robustness and replication

Run:

- second family set;
- linear model;
- gradient boosting;
- lower support;
- alternative FPR targets;
- partition-resalting sensitivity;
- support-threshold sensitivity;
- top-family removal;
- representation de-duplication sensitivity.

**Exit condition:** robustness scope for every promoted claim is known.

### Stage K — Statistical lock and evidence promotion

Apply the frozen statistical plan and claim gates exactly once to the full confirmatory evidence.

Classify each planned claim as:

- **PROMOTED**;
- **NARROWED**;
- **INSUFFICIENT_EVIDENCE**;
- **REJECTED**.

Do not modify thresholds to rescue failed claims.

### Stage L — Publication evidence

Generate final tables, figures, effect summaries, limitations, and chapter text only from frozen confirmatory outputs and explicitly labelled exploratory analyses. The post-confirmatory tables and figures of 31.3 are included and labelled as class C evidence.

---

## 39. Expected Figures

### Collaboration decomposition

For central and FedAvg, show local baseline, generic pooling component, complementary component, and full-exposure ceiling.

### Mean versus worst client

Side-by-side unseen-family recall and FNR for mean and worst client.

### Own-domain versus federation-wide benefit

Show whether the complementary effect survives removal of the cross-market evaluation advantage.

### Peer-dose curves

Recall against effective peer family exposure for centralized, FedAvg, and fine-tuned models.

### Family rescue map

Per-family local, no-family, peer-family, and full-exposure recall.

### Feature novelty versus complementary gain

Family-level scatter/interval view of training-only feature novelty and measured CTK gain.

### Known versus unseen trade-off

Known-family recall/FPR versus unseen-family benefit.

### Robustness summary

Family set, model family, operating point, support, and grouping sensitivities, drawn as a forest plot that keeps the seed-paired macro estimand and the micro-pooled hits/trials estimand visibly separate.

### Post-confirmatory figures (31.3)

Federated-arm trade-off panels and controlled-versus-natural-scarcity decomposition. These are labelled as post-confirmatory, evidence-preserving views.

---

## 40. Expected Tables

### Dataset and client audit

Report:

- rows;
- malware prevalence;
- client support;
- family support;
- benign calibration support;
- eligible family counts;
- excluded singleton/unsupported family counts.

### Primary arm comparison

At \(\alpha=0.05\):

- own-domain unseen recall;
- federation-wide unseen recall;
- family-macro recall;
- worst-client recall;
- known-family recall;
- realised FPR;
- worst-client FPR.

### Decomposition table

For central and FedAvg:

- total gain;
- generic pooling gain;
- CTK gain;
- complementary share;
- BCa intervals;
- exact Wilcoxon result;
- promotion-gate status.

### Dose-response table

Requested and effective peer sample counts with recall and uncertainty.

### Family-level table

For each eligible family:

- support;
- local recall;
- no-family recall;
- peer-family recall;
- full-exposure recall;
- CTK gain;
- novelty descriptors;
- rescue/failure classification.

### Gate table

Every planned claim with final status and allowed wording.

---

## 41. Compute and Resource Plan

The full project must be executable on a single workstation.

No phones, emulators, Raspberry Pis, new malware collection, or external compute service are required.

Expected resource profile based on development evidence:

- preprocessing and cache construction: minutes rather than hours once raw sources are local;
- main neural training: GPU-preferred but CPU fallback possible;
- gradient boosting: CPU;
- memory requirement within a normal research workstation range;
- confirmatory campaign: hours, not multi-day cluster-scale computation.

Long deterministic preprocessing should be cacheable and resumable. Expensive tasks must not be rerun unnecessarily when the frozen inputs have not changed.

---

## 42. Limitations

The chapter must discuss at least the following.

### Simulated clients

The clients are market/era domains derived from public data, not independently operated organizations.

### Manipulated exposure

The primary missing-family condition is experimentally created. Natural scarcity is therefore included as complementary evidence.

### AVClass2 semantics

Family labels are noisy operational groupings and are particularly influenced by adware/PUP naming.

### Static representation

The 925 features capture static characteristics only. A family that is poorly detected may require dynamic or richer representation.

### Cross-market shift

Federation-wide unseen-family evaluation can mix family exposure and market-domain differences. Own-domain evaluation is required to bound this threat.

### Provider-side global variance filtering

The released representation includes global preprocessing that cannot be reconstructed train-only.

### Limited number of clients

Four simulated clients are sufficient for the controlled question but do not represent the range of real federated deployments.

### Limited external replication

The confirmatory design relies primarily on one Android benchmark. Internal replication across family sets, model classes, natural scarcity (a within-dataset validation on the same corpus), and split choices does not replace independent external validation.

### Family support

Some client/family combinations cannot support reliable own-domain analysis and are excluded by predeclared rules.

### Tail calibration

Very low FPR targets may be limited by benign calibration support.

---

## 43. Threats to Validity

### Construct validity

- family absence by AVClass2 label does not imply feature-space novelty;
- collaboration value may reflect shared malicious behavior rather than explicit family identity;
- static family labels may aggregate heterogeneous malware.

### Internal validity

- package and feature-vector leakage;
- unequal training size;
- accidental family presence after hiding;
- test-dependent thresholding;
- target-family support differences;
- model under-training.

These are controlled through component grouping, matched sampling, exposure assertions, calibration-only thresholds, support gates, and baseline tuning on development evidence.

### Statistical validity

- only ten confirmatory seeds;
- four clients;
- heterogeneous family support;
- correlated APKs within representation components;
- many exploratory family-level comparisons.

Exact paired tests, BCa intervals, cluster bootstrap, Holm adjustment for primary contrasts, and careful exploratory labeling are required.

### External validity

- one primary Android corpus;
- market/era clients may not reflect enterprise silos or end-user devices;
- static features may not transfer to dynamic malware detection;
- AVClass2 family distribution is not the complete Android threat landscape.

---

## 44. Ethical and Security Considerations

CTK-Android uses public, previously collected research data.

The implementation does not require executing malware, collecting new APKs, instrumenting user devices, or interacting with live malicious infrastructure.

The project should not redistribute raw APKs or row-level data beyond source permissions.

Family-level failure results are reported at scientific aggregate level and should not be framed as operational evasion instructions.

Federated learning is not described as privacy-preserving by default. The study evaluates collaboration utility, not formal privacy.

---

## 45. Chapter Structure

### Introduction

Motivate complementary threat knowledge and explain why total collaboration gain conflates two effects.

### Related Work

Cover:

- Android malware detection;
- federated Android malware detection;
- missing/rare-class FL;
- federated transfer and prototype exchange;
- non-IID collaboration;
- negative transfer and collaboration value.

### Data and Client Construction

Explain:

- audited LAMDA/AndroZoo data;
- market/era clients;
- family semantics;
- component grouping;
- leakage risks.

### Controlled-Exposure Methodology

Define:

- locally unseen families;
- no-family controls;
- full-exposure references;
- dose-response;
- own-domain evaluation;
- decomposition estimands.

### Results: Does Collaboration Help?

Present local deficit, total collaboration gain, central/FedAvg comparison, and worst-client behavior.

### Results: What Part Is Complementary Knowledge?

Present generic pooling versus CTK decomposition and permutation control.

### Results: When Does Complementary Knowledge Matter?

Present dose-response, family heterogeneity, natural scarcity, and feature-space novelty.

### Results: What Collaboration Does Not Fix

Present full-exposure failures, known-family cost, and mechanism headroom.

### Robustness

Present second family set, model-class replication, FPR sensitivities, support sensitivities, and split hardening.

### Discussion

Interpret implications for federated threat sharing and the broader PhD question of when collaboration is worth using.

### Limitations and Conclusion

State bounded claims and avoid generalization beyond the tested data and representations.

---

## 46. Completion Criteria

CTK-Android is complete only when all of the following are satisfied.

### Data and protocol

- frozen data fingerprints verified;
- all structural gates PASS;
- client and family support tables finalized;
- confirmatory protocol frozen before result inspection.

### Implementation

- full smoke workflow passes;
- baseline fairness checks pass;
- leakage and exposure tests pass;
- all primary arms implemented;
- all metrics and decomposition identities validated;
- clean-environment execution demonstrated.

### Confirmatory evidence

- all ten confirmatory seeds complete or a documented structural reason excludes a seed before outcome inspection;
- no seed is dropped for poor performance;
- primary own-domain and decomposition outcomes are available;
- dose-response complete;
- natural-scarcity analysis complete;
- feature-space novelty analysis complete;
- second family set complete;
- model-family replication complete;
- sensitivity analyses complete.

### Statistics and claims

- every predeclared claim has a gate outcome;
- every promoted claim has uncertainty and practical-effect support;
- failed claims are retained as failed/narrowed rather than silently removed;
- exploratory evidence is clearly distinguished from confirmatory evidence;
- no post-hoc mechanism is promoted.

### Publication artifacts

- final figures regenerate from frozen results;
- final tables regenerate from frozen results;
- chapter claims match gate outcomes exactly;
- novelty wording passes a final current-literature collision audit;
- limitations and negative evidence are included.

---

## 47. Protocol Amendment Rule

Once confirmatory execution begins, this roadmap is frozen.

A change is permitted only for a demonstrated correctness problem such as:

- invalid data assumption;
- leakage;
- implementation bug;
- impossible support requirement;
- mathematically incorrect metric;
- newly discovered direct literature collision that invalidates a claim.

For any material amendment:

1. document the problem before rerunning;
2. state exactly which prior results are invalidated;
3. update the protocol without using favorable test outcomes to choose the fix;
4. select a fresh unused confirmatory seed range if the change affects scientific degrees of freedom;
5. retain the failed/superseded evidence for auditability.

Convenience, weak results, or a failed hypothesis are **not** reasons to change the protocol.

---

## 48. Final Research Decision Logic

The project does not require every hypothesis to succeed.

The final chapter remains scientifically worthwhile if the confirmatory study can establish a rigorous answer to the core question:

> **How much of the apparent benefit of federated Android malware collaboration on locally unseen families is actually complementary threat knowledge, when does that component appear, and when is ordinary pooling or representational overlap enough?**

A strong final contribution may therefore be:

- a positive complementary-knowledge result;
- a small but precisely bounded complementary component;
- a family-dependent collaboration result;
- a result showing generic pooling dominates;
- a result showing exposure is not the main limitation for several families;
- a result showing standard collaborative baselines already exhaust useful headroom.

What is not acceptable is an unsupported success narrative created by changing clients, families, metrics, mechanisms, thresholds, or claims after observing the confirmatory results.

The scientific priority is **correct decomposition, strong controls, bounded claims, and reproducible evidence**.
