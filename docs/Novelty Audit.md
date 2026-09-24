# Novelty Audit

Status: literature collision audit performed 2026-09-24 with the paper-search tools available in this session. It is a **bounded** audit, not an exhaustive systematic review; its limits are stated in section 7. No sentence in this repository may claim "first", "novel", "unprecedented" or "state of the art" on the strength of this document. Everything here is class D (positioning), not an experimental result.

## 1. Search log

Fourteen search or discovery calls in this task (plus two earlier general web searches) were made across two indexes (a general academic-paper search over Semantic Scholar/Scopus/arXiv-style sources and an arXiv/alphaXiv discovery tool). Topics, one call each unless noted:

1. federated Android malware detection, unseen family, missing classes (×2, plus a follow-up on client-held families with Drebin/AndroZoo);
2. federated malware detection with novel family and clients lacking the family;
3. missing / absent / vacant / incomplete classes in FL (×2);
4. contribution valuation, decomposition and data-quantity versus class knowledge (×2);
5. leave-one-class-out, controlled class removal, target class absent from clients;
6. rare-class, long-tail and prototype-based knowledge transfer in FL;
7. worst-client and per-client evaluation in federated malware detection;
8. per-class benefit of collaboration for classes a client has never seen;
9. peer-sample dose (class support sweep) and negative transfer versus class coverage (×2);
10. cross-silo / collaborative malware threat-intelligence FL with unseen families;
11. the LAMDA benchmark and Android family/concept-drift literature.

Roughly 100 distinct records were screened by title and abstract. Twenty-two were retained as potentially close and are in the matrix. One paper was read in full (Breitholtz et al., label-set heterogeneity, including its related-work section and references); two (FedP3E, CELM) were read through the abstract and introduction; every other retained paper was assessed from its abstract only (marked "abstract"). Backward citation chaining was limited to the reference list and related work of the Breitholtz paper and the related work quoted in retrieved abstracts; forward citation search (cited-by) was **not** available.

## 2. Collision matrix

Columns: FL = federated setting; Miss = missing or rare classes; Rem = controlled target-class removal; Abs = matched class-absent-everywhere control; Dec = separates generic pooling from complementary class knowledge; Dose = manipulates peer samples of the missing class; Own = own-domain evaluation of the missing class at the target client; Wst = worst-client analysis; Nat = natural-scarcity validation of an artificial intervention; Full = full-exposure ceiling; ExpRep = exposure-versus-representation analysis. "n" = not found in what was read; "p" = partial; "y" = present. Reading depth in the last column.

| Paper | Year | Domain | FL | Miss | Rem | Abs | Dec | Dose | Own | Wst | Nat | Full | ExpRep | Collision | Read |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Exploring Vacant Classes in Label-Skewed FL (FedVLS), Guo et al. | 2024 | image classification | yes | y (vacant classes) | n (label-skew splits) | n | n | n | p (local-vs-global on vacant classes) | n | n | n | n | PARTIAL | abstract |
| FL with Heterogeneous and Private Label Sets, Breitholtz, Listo Zec, Johansson | 2025 | image classification | yes | y (labels per client swept, sample count fixed) | p (label-set size manipulated) | n | n | p (labels per client, not peer samples of a class) | n | n | n | n | n | PARTIAL | full text |
| Objective Mismatch in FL under Missing Class Support, Otani et al. | 2026 | fall detection / synthetic | yes | y (rare class absent at most clients) | n | n | n (proves irreducible bias) | n | n | n | n | n | n | PARTIAL | abstract |
| MAP: Model Aggregation and Personalization in FL with Incomplete Classes, Li et al. | 2024 | image classification | yes | y | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| FedExIT, Saha et al. | 2025 | image / medical | yes | y | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| FedP3E: prototype exchange for non-IID IoT malware detection, Darwish et al. | 2025 | IoT malware (N-BaIoT) | yes | y (rare/disjoint malware classes) | n | n | n | n | n | n | n | n | n | ADJACENT | abstract + intro |
| FEDroid: comprehensive Android malware detection with FL, Fang et al. | 2023 | Android malware | yes | n (variants via evolution) | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| A method for real-world privacy-preserving Android malware detection through Federated ML, Ciaramella et al. | 2025 | Android malware, 71 families | yes | n (IID vs non-IID) | n | n | n | n | n | n | n | p (centralized reference) | n | ADJACENT | abstract |
| FL for Malware Image Classification under Data Heterogeneity, Taiwo et al. | 2026 | malware images | yes | p (class entropy per round) | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| Class-wise Contribution Estimation via Logit Maximization (CELM), Ukaye et al. | 2026 | image classification | yes | p (class coverage) | n | n | n (weights by class evidence) | n | n | n | n | n | n | ADJACENT | abstract + intro |
| Contribution estimation and data valuation in FL (Wei et al. 2020; Zhu et al. 2021; Chen et al., VLDB 2024; Li et al. 2023) | 2020–24 | generic | yes | n | n | n | n | n | n | n | n | n | n | ADJACENT | abstracts |
| Federated Class-Incremental Learning (Dong et al. 2022; TPAMI 2023) | 2022–23 | image classification | yes | y (new classes at some clients) | n | n | n | n | n | n | n | n | n | ADJACENT | abstracts |
| FedProto and prototype-based FL (Tan et al. 2021; FedSA; FedHCL) | 2021–25 | generic | yes | p | n | n | n | n | n | n | n | n | n | ADJACENT | abstracts |
| FedCollab: optimizing the collaboration structure (negative transfer), Bao et al. | 2023 | generic | yes | n | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| Who to Trust? Aggregating client predictions in federated distillation (class mismatch) | 2025 | image classification | yes | y | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| FL-MalDrift; M2FD (concept drift, Android malware FL) | 2025 | Android malware | yes | n | n | n | n | n | n | n | n | n | n | ADJACENT | abstracts |
| Non-IID Android malware FL feasibility study, Lee | 2023 | Android malware | yes | n | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| FAMCF few-shot Android malware family classification, Zhou et al. | 2024 | Android malware (not FL) | no | y (few-shot families) | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| Federated Attack Campaign Detection via Contrastive Encoding of Threat Indicators | 2026 | threat intelligence | yes | n | n | n | n | n | n | n | n | n | n | ADJACENT | abstract |
| LAMDA: longitudinal Android malware benchmark, Haque et al. | 2025 | Android malware dataset | no | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NONE (data source) | abstract |
| Dynamic-weighted FL for Android malware (Chaudhuri et al.; Wajahat et al.) | 2022–25 | Android malware | yes | n | n | n | n | n | n | n | n | n | n | NONE | abstracts |
| Fair comparison of Android malware detectors (Molina-Coronado et al.) | 2022 | Android malware (not FL) | no | n | n | n | n | n | n | n | n | n | n | NONE | abstract |

Totals over the 22 rows (a row may group several closely related papers): **0 DIRECT, 3 PARTIAL, 16 ADJACENT, 3 NONE**.

Explanation of the PARTIAL collisions:

- **FedVLS (Guo et al.)** evaluates vacant classes (absent at a client) and compares local models with the global model on them, which is the same evaluation motif as our local-versus-collaborative comparison on locally unseen classes. It is not a controlled decomposition: label skew is generated by partitioning, vacant classes remain present at peers by construction, there is no class-absent-everywhere control, no pooling-versus-class-knowledge split, no dose, no own-domain or worst-client analysis.
- **Breitholtz et al.** manipulates the number of labels each client has while holding samples per client fixed. This is conceptually close to our matched-size control (exposure changes, data volume does not) and to a dose over label-set size. It measures global accuracy, not a locally hidden family, and does not isolate a class-specific component.
- **Otani et al.** proves that a class absent from most clients leaves an irreducible bias under FedAvg-type objectives. It is a theoretical statement about missing class support, consistent with our finding that plain FedAvg has a known-family/unseen-family trade-off, but it has no matched-control decomposition or malware evaluation.

## 3. What the closest designs do and do not cover

Two design families are closest: (a) label-skew and label-set-heterogeneity studies (FedVLS, Breitholtz, MAP, FedRS-type methods, Otani), which create locally missing classes and measure accuracy; (b) Android and IoT malware FL papers (FEDroid, Ciaramella, FedP3E, Taiwo, Lee), which apply FL to malware under non-IID partitions. The first group has the missing-class evaluation but not the causal decomposition or malware families; the second group has malware data but treats heterogeneity as a nuisance to be mitigated and reports aggregate accuracy, not per-hidden-family counterfactuals. Contribution-valuation work (Shapley-based, CELM) attributes value to clients or class evidence for weighting, not the marginal effect of a class held by peers on a target client's recall for that class.

Coverage of the eleven ingredients of the measurement design:

| Ingredient | Found in audited literature? |
|---|---|
| 1. locally missing family/class at one client | yes (label-skew and incomplete-class papers) |
| 2. otherwise matched collaborative training | not found as a designed matched control |
| 3. target family present at peers | implicit in every missing-class setting |
| 4. target family absent from all clients as matched control | **not found** |
| 5. full-exposure reference | partly (centralized reference in some papers) |
| 6. decomposition into total, generic pooling, complementary class knowledge | **not found** |
| 7. own-domain evaluation of the hidden class | not found |
| 8. worst-client evaluation | standard fairness idea; not combined with class-specific decomposition in what was read |
| 9. peer-sample dose response for the missing class | not found (label-count sweeps exist) |
| 10. natural-scarcity validation of the artificial intervention | not found |
| 11. exposure-versus-representation failure analysis | not found |

## 4. Independent verdicts

Verdict scale: STRONG DIFFERENTIATOR, PLAUSIBLE DIFFERENTIATOR, PARTIAL COLLISION, DIRECT COLLISION, NOT ENOUGH EVIDENCE. Because the search was bounded, no candidate is rated STRONG.

| Candidate | Verdict | Reason |
|---|---|---|
| N1 controlled-exposure decomposition (matched family-absent-everywhere control separating pooling from complementary knowledge) | PLAUSIBLE DIFFERENTIATOR | No audited paper implements the class-absent-everywhere counterfactual; nearest are FedVLS/Breitholtz (missing-class evaluation, label-set manipulation). |
| N2 malware-family CTK in Android FL | PLAUSIBLE DIFFERENTIATOR | Android FL papers report aggregate accuracy under non-IID splits; none found isolating family-specific complementary knowledge. |
| N3 own-domain decomposition | PLAUSIBLE DIFFERENTIATOR | Own-domain versus federation-wide evaluation of a hidden class was not found; the idea is a specific evaluation choice rather than a method. |
| N4 worst-client CTK | PLAUSIBLE DIFFERENTIATOR (weak) | Worst-client reporting is standard fairness practice; the differentiation is only its combination with the class-specific decomposition. |
| N5 natural-scarcity validation | PLAUSIBLE DIFFERENTIATOR | An artificial-removal design validated against natural scarcity under the same decomposition was not found. It is within-dataset (same corpus), not external. |
| N6 dose-response over peer samples of the missing class | PARTIAL COLLISION | Exposure manipulation exists (label-count sweeps, data-size studies); linking peer-sample count of the missing class to the incremental benefit was not found. |
| N7 exposure-versus-representation diagnosis | PLAUSIBLE DIFFERENTIATOR | Full exposure plus independent model classes to separate exposure-limited from representation-limited families was not found in the audited papers. |
| N8 combined framework | PLAUSIBLE DIFFERENTIATOR | No paper found providing essentially the same complete measurement framework; individual ingredients are known. |

## 5. Strongest defensible positioning

Allowed wording, given this audit:

> In the audited literature we found no closely matching study that combines a controlled hidden-family design, a matched family-absent-everywhere collaborative control, a full-exposure reference, a decomposition into total, generic-pooling and complementary family-knowledge components, own-domain and worst-client evaluation, a peer-exposure dose analysis and a natural-scarcity check on Android malware families. Individual ingredients (locally missing classes, malware FL under non-IID splits, per-client fairness reporting, exposure sweeps) are established. The contribution is the measurement design and its empirical decomposition on one corpus, not a new learning algorithm.

Not allowed: "first", "novel", "the only", "state of the art", or any claim that generalizes beyond the LAMDA/AndroZoo corpus.

## 6. Already covered by prior work versus differentiated

Already covered (do not present as new): federated Android malware detection under non-IID data; the observation that classes absent from a client are poorly recognized (FedVLS, Otani); missing-class-aware aggregation and personalization (FedRS, MAP); prototype exchange for rare malware classes (FedP3E); contribution valuation; per-client and worst-client reporting; concept-drift benchmarks (LAMDA) as the data source; FedProx and fine-tuning baselines.

Differentiated (subject to the search limits): the matched absent-everywhere counterfactual and the resulting pooling-versus-complementary decomposition; its application to labelled malware families with own-domain and worst-client views; the natural-scarcity validation of the intervention; the effective-exposure dose analysis; the exposure-versus-representation diagnosis with full-exposure and cross-model checks.

## 7. Limits of this audit

- Search tools index mainly arXiv/Semantic Scholar/Scopus-style sources. Venue-specific sources for security (USENIX Security, CCS, NDSS, RAID, DIMVA), ACM/IEEE proceedings not indexed by these tools, and Google Scholar cited-by were not searched.
- Only one paper was read in full and two through abstract and introduction; the others were assessed from abstracts. A paper whose method section contains a hidden-class control could have been missed.
- Terminology gaps: synonyms (label deficiency, semantic heterogeneity, class complementarity) were included in queries, but semantic search can miss exact experimental designs described in unusual words.
- Recommended before any novelty claim in a manuscript: a second pass with forward-citation search on FedVLS, Breitholtz et al., FedRS/MAP, FedP3E, the Android FL papers above and LAMDA; a targeted security-venue sweep; and full-text reading of all PARTIAL and the top ADJACENT papers (FedVLS, Otani, FedP3E, CELM, FEDroid, MAP).

## 8. Closest five papers

1. Exploring Vacant Classes in Label-Skewed Federated Learning (FedVLS), 2024.
2. Federated Learning with Heterogeneous and Private Label Sets, 2025.
3. Objective Mismatch in Federated Learning under Missing Class Support, 2026.
4. FedP3E: Privacy-Preserving Prototype Exchange for Non-IID IoT Malware Detection, 2025.
5. Comprehensive Android Malware Detection Based on Federated Learning Architecture (FEDroid), 2023 (nearest Android-specific FL paper, with a real-variants evaluation but no missing-family decomposition); MAP/FedRS (incomplete classes) are the next.
