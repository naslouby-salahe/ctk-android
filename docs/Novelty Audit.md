# Novelty Audit

Status: second, deeper literature collision audit, 2026-09-25 (first bounded audit 2026-09-24, superseded by this document). The goal is to determine whether the CTK-Android design materially overlaps prior work, not to prove novelty. This is positioning material (class D), not an experimental result. No sentence in this repository may claim "first", "novel", "unprecedented" or "state of the art" on the strength of this audit. Limits are in section 8.

## 1. What was done

- **Search:** about 25 search or discovery calls across a general academic index (Semantic Scholar/Scopus/arXiv-style) and an arXiv/alphaXiv discovery tool, plus four arXiv API title lookups to obtain full-text access, and six Semantic Scholar citation-graph requests (four returned data, two were rate-limited). Across both audits roughly 200 distinct records were screened by title and abstract; 35 matrix rows resulted.
- **Reading depth (reported per paper below):** seven papers were read in full, extracted text, by structured checklist (FedVLS, Breitholtz et al., MAP, Bi et al., GLFC, CELM, FedP3E); every other paper was assessed from its abstract only, and where the primary source was not read at all this is stated. Three dataset papers (MH-1M, AndroTruth, McNdroid) were read for dataset facts only; they are not collision candidates.
- **Checklist applied to each full-text paper:** problem definition; how client labels are created; whether classes are absent by design or incidentally; whether absence is controlled (one class removed from one client with the rest matched); sample-count matching; class removed from all clients as a control; whether the effect of peers holding the class is isolated for the client lacking it; evaluation population; dose or support sweep; worst-client or per-client analysis; full-exposure reference; natural versus artificial scarcity; representation-level explanation; decomposition of collaboration benefit into generic pooling versus class-specific knowledge.
- **Backward chaining:** reference lists and related work of the full-text papers (FedRS, FedAwS, FedGELA/FedMR partially class-disjoint data, FedROD, class-imbalance FL, FEDroid, DW-FedAvg, FedCRI/others cited by Bi et al.).
- **Forward chaining (citations of the close papers):** MAP: 16 citing papers, none on malware or a controlled absent-class design. LAMDA: 12 citing papers, one federated (a drift-aware federated continual-learning Android malware paper, 2026, abstract-level only, drift focus). Breitholtz et al. and FedP3E: no citing papers indexed (recent). FedVLS: request rate-limited, not retrieved. CELM, FedRS, FEDroid, Otani et al.: not retrievable.
- **Synonym coverage:** vacant / missing / absent / incomplete / class-deficient / disjoint / partially class-disjoint / label-set heterogeneity / label-skew / rare / minority / long-tail / class coverage / class-specific contribution / locally unseen. Different terminology found: partially class-disjoint data (FedGELA, FedMR), positive-labels-only (FedAwS), "Maverick" rare classes (CELM).
- **Security-venue sweep:** USENIX Security, CCS, NDSS, RAID, DIMVA, ACSAC, IEEE S&P, DSN, Computers & Security, TDSC, TIFS and TOPS were queried by name in combination with federated/collaborative malware terms and, for Computers & Security, with a journal filter. The indexes do not expose conference proceedings reliably: the sweep surfaced one RAID 2024 paper (cross-regional malware detection, Botacin et al.), FEDroid (TIFS 2023), M2FD (Computers & Security 2025), and an NDSS 2022 federated-intrusion paper cited by Bi et al. (not read). No proceedings from USENIX Security, CCS, S&P, ACSAC, DIMVA or TDSC/TOPS were retrieved by these queries; absence from the search results is not evidence of absence from those venues.

## 2. Collision matrix

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

## 3. Explanation of every PARTIAL collision

- **FedVLS (full text).** Vacant classes (absent from a client's Dirichlet or shard draw) are its subject; it compares class-wise accuracy of the initial global model and of the locally updated model on vacant classes (Fig. 1, Table 12), and explains the local decay at the logit/loss level. It is not a controlled design: absence is "incidental" to the partition, there is no matched removal, no matched sample count, no class-absent-everywhere control, no peer dose, no own-domain population, and headline evaluation is global test accuracy. Overlap: the evaluation motif (locally absent classes, local versus global recall) and a mechanism-level explanation.
- **Breitholtz et al. (full text).** Manipulates the number of labels each client holds while fixing samples per client (2,000), which is close to our matched-size principle, and sweeps label-set size (a coarse dose over label diversity). It measures global accuracy of aggregation methods, not recall on a locally hidden class, and has no absent-everywhere control or decomposition. Overlap: exposure manipulated at fixed sample volume.
- **Otani et al. (abstract only).** Proves an irreducible bias for rare classes absent from most clients under FedAvg-type objectives. Consistent with our FedAvg known-family/unseen-family trade-off. Because only the abstract was accessible, its experimental design (synthetic and one real fall-detection dataset) is unverified; classified PARTIAL on stated topic, with high uncertainty.
- **Bi et al. (full text).** Android malware FL on Drebin (179 families, 133 after filtering) and AndroZoo benign, with a "family-based non-IID" setting where each client holds only k families (k in {1..4} cross-device, {5..30} cross-silo), and a centralized reference. It finds unstable training as k shrinks and no clear performance pattern. Overlap: same domain, families absent from clients by design, centralized reference. Non-overlap: only a global held-out test set (no per-family or per-client recall), no controlled removal, no matched control, no decomposition, no dose (only skew parameters), binary detection task.

## 4. What the closest full-text designs do not do

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

## 5. Reassessed candidate contributions

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

## 6. Strongest defensible positioning (narrowed)

Prior work already establishes that classes absent from a client are poorly recognized (FedVLS, MAP, Otani et al.), studies Android and IoT malware FL under non-IID partitions including families held by only some clients (Bi et al., FedP3E, FEDroid, Ciaramella et al.), and reports natural and synthetic partitions side by side (MAP, CELM). Wording supported by the audit:

> In the audited literature we found no closely matching study that isolates, for a client that lacks a malware family, the effect of peers holding that family by combining a controlled hidden-family design with a matched family-absent-everywhere collaborative control and a full-exposure reference, and that uses this to decompose collaboration gain into generic pooling and complementary family knowledge with own-domain and worst-client evaluation on Android malware. Locally missing classes, family-skewed Android malware FL, exposure sweeps and natural-versus-synthetic partitions each have precedent; our contribution is their combination into a measurement design and its empirical decomposition on one corpus, not a new learning algorithm.

The earlier list-style statement (which also named the peer-exposure dose analysis and the natural-scarcity check as part of what was not found together) is retained only in this combined form; dose and natural-scarcity are individually partially anticipated and are not presented as independent novelty.

## 7. Lost and gained differentiation after the deeper audit

- **Lost or weakened:** N5 (natural scarcity) and N6 (dose) are now PARTIAL COLLISION; "Android malware FL with families absent from clients" is not new (Bi et al.); disjoint malware classes across clients are not new (FedP3E); mechanism-level explanations of missing-class failure are not new.
- **More clearly differentiated:** N1 and N8. Seven full-text reads did not find a class-absent-everywhere control, a controlled per-client removal, or a decomposition, and the closest malware FL papers evaluate only global test metrics.

## 8. Limits

- Only seven papers were read in full. About 25 relevant papers were abstract-only; an abstract-only "n" is weak evidence of absence. FEDroid, Ciaramella et al., Otani et al., Taiwo et al. and Botacin et al. are the most important unread primary sources; Otani et al. and FedRS could not be retrieved from open sources.
- The security-conference proceedings (USENIX Security, CCS, S&P, ACSAC, DIMVA, NDSS) are not reliably indexed by the tools; the sweep cannot rule out relevant papers there.
- Forward citations were obtained only partially (Semantic Scholar rate limits; very recent papers have few citations).
- Fairness-in-FL (worst-client) and negative-transfer literatures were sampled, not audited in depth.
- Before any manuscript novelty claim: full-text reading of FEDroid, Ciaramella et al., Otani et al., FedRS, FedGELA and Taiwo et al.; a proceedings-level sweep of the security venues; forward-citation retrieval for FedVLS, FedRS, FedP3E and Bi et al.; and a re-run of this audit at submission time.

## 9. Closest ten papers

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
