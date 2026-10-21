# CTK-Android revision and independent verification

Date: 2026-10-20. Named master: `chapter/CTK-Android_Chapter.docx`. Existing `chapter/audit.md` preserved.

## A. Executive verdict

**Manuscript-content correction and verification complete within the authorized scope.** No critical or major scientific/numerical defect remains from this review. All 26 surgical edits, supplied author information and the five missing bibliography entries are present and validated. The bibliography now contains 19 unique entries, all cited. No manuscript-content correction remains. AI disclosure is explicitly EXCLUDED_BY_USER; publisher compliance on that issue is not certified. The author reports independent peer-review arrangements addressed externally; no further manuscript or administrative action was requested.

There are **39 logical manuscript modification operations across the two stages**: the initial 34 (27 text operations, one author block, one legend update and five image descriptions), followed by five bibliography insertions. The final bibliography pass wrote only the manuscript and this existing report. The earlier standalone Figure 3 change is preserved. No experimental algorithm, source/configuration, dataset, training output, frozen statistic, seed assignment or evidence class changed. No training/experiment, commit or push was performed. An unrelated pre-existing modification to `proposal/build-proposal.sh` was present at the start of this pass and was preserved, as confirmed by its unchanged SHA-256.

The starting manuscript exactly matched SHA-256 `b54193843b08a63bc2328c5a7affa98fc3a8f44f13e059dc16631d4119e972c2`. Current HEAD is `9645979560aff27852533031d9c212ff198c1714` (“Audit”), one commit after the audit’s recorded `6813f92`; this only preserved the audit/reference collection. The manuscript was unchanged by that commit; `src/` and `configs/` remain identical to execution revision `f6302f7`. No newer manuscript edit was overwritten.

## B. Exact modifications

Every operation below was checked against the saved, reopened final file. The full original anchor/replacement record at the end makes these changes reversible.

| Edit | Location | Action | Verification | Status |
|---|---|---|---|---|
| 1 | Abstract | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 2 | Introduction | Replace anchored paragraph | Exact replacement once; second pass zero changes | FIXED |
| 3 | After CyberForce | Insert one new paragraph | Exact replacement once; second pass zero changes | FIXED |
| 4 | Grouped/chronological comparison | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 5 | Figure 1 note | Replace anchored paragraph | Exact replacement once; second pass zero changes | FIXED |
| 6 | FedAvg methods | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 7 | Principal results | Replace anchored paragraph | Exact replacement once; second pass zero changes | FIXED |
| 8 | After principal result | Insert one new paragraph | Exact replacement once; second pass zero changes | FIXED |
| 9 | Secondary populations | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 10 | Operating-point sensitivity | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 11 | Learner comparisons | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 12 | Client heterogeneity | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 13 | Dose interpretation | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 14 | Expanded families | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 15 | Discussion generalization | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 16 | Conclusion | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 17 | Discussion intervention | Replace anchored paragraph | Exact replacement once; second pass zero changes | FIXED |
| 18 | Statistical validity | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 19 | Partition construction | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| 21 | Figure 4 note | Replace anchored paragraph | Exact replacement once; second pass zero changes | FIXED |
| 22A | Edit 22 localized prose | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 22C | Edit 22 localized prose | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 22D | Edit 22 localized prose | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 22E | Edit 22 localized prose | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 23 | Discussion pooling | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 24 | Table 2 note | Replace exact fragment | Exact replacement once; second pass zero changes | FIXED |
| 25 | Reproducibility | Insert after exact sentence | Exact replacement once; second pass zero changes | FIXED |
| AUTHOR | Author block before Abstract | Insert supplied metadata | Exact names/emails/affiliations; superscripts; live ORCID name match; page 1 | FIXED |
| 26.1 | Figure 1 metadata | Embed image description | Nonempty drawing-property descr; extents unchanged | FIXED |
| 26.2 | Figure 2 metadata | Embed image description | Nonempty drawing-property descr; extents unchanged | FIXED |
| 26.3 | Figure 3 metadata | Embed image description | Nonempty drawing-property descr; extents unchanged | FIXED |
| 26.4 | Figure 4 metadata | Embed image description | Nonempty drawing-property descr; extents unchanged | FIXED |
| 26.5 | Figure 5 metadata | Embed image description | Nonempty drawing-property descr; extents unchanged | FIXED |
| 20 | Figure 3 | Replace legend text only | Changed pixels confined to legend; embedded/standalone match | FIXED |
| BIB-1 | References, after Feng/before Haque | Insert Gálvez (2021) | Exact entry once; APA italics, matching hanging indent, functional DOI; page 49 | FIXED |
| BIB-2 | References, after Ongun/before Pendlebury | Insert Patel (2026) | Exact entry once; volume-year 2026 verified; functional DOI; page 50 | FIXED |
| BIB-3 | References, after Pendlebury/before Sebastián | Insert Popoola (2022) | Exact entry once; final volume/issue/pages verified; functional DOI; page 50 | FIXED |
| BIB-4 | References, after Sebastián/before Shen | Insert Shao (2026) | Exact entry once; publisher surname/status verified; functional DOI; page 51 | FIXED |
| BIB-5 | References, after Shao | Insert Shen (2024) | Exact entry once; final ICC proceedings/pages verified; functional DOI; page 51 | FIXED |

Across the initial revision and bibliography completion, only three DOCX package members differ from the original audited manuscript: `word/document.xml`, its relationship file, and `word/media/image3.png`. The bibliography completion alone changes only the first two, adding five reference paragraphs and five external DOI relationships. Removing those five new paragraphs reproduces the complete preceding document XML tree exactly; removing their five relationships reproduces the preceding relationship tree exactly. Every other package member is byte-identical to the pre-bibliography master. All 14 original reference paragraphs, tables, equations, headings, abstract/body text, styles, drawing extents, author information, ORCID/email links and the GitHub URL are unchanged. New paragraphs copy the existing reference paragraph properties (0.5-inch hanging indent and keep-lines setting), inherit the same font/line/paragraph spacing, retain black text and italicize only the journal/volume or proceedings title. Tracked changes were not used. The original audited manuscript remains recoverable from commit `6813f929968f141d3660ccfa28d37aaa0180d74f`; exact external backups and the change records below preserve both stages.

## C. Complete original audit reconciliation

The audit contains 31 actual finding blocks: **23 FIXED, 4 ALREADY_CORRECT, 3 EXCLUDED_BY_USER, 1 PENDING_AUTHOR_ACTION**. Finding 009 is now FIXED after insertion and final-file validation. Finding 028 is author-excluded, without a publisher-compliance claim. For 027 the manuscript/protocol proof and requested preservation assessment are complete; only the previously deferred, optional preservation action remains author-owned. No finding was reopened and no unverified item is marked fixed.

| Audit ID | Original concern | Final status | Evidence in revised manuscript | Explanation |
|---|---|---|---|---|
| CTK-AUDIT-001 | Rounded component sum | FIXED | Primary CTK paragraph explains displayed 13.47 versus unrounded 13.46. | Independent paired identity; Table 3 unchanged. |
| CTK-AUDIT-002 | Narrow interpretation of exposure contrast | FIXED | Primary CTK paragraph explicitly includes approximately 2,073/24,000 changed fit examples. | Figure 1 and specificity bridge agree with exclusion/replacement code. |
| CTK-AUDIT-003 | Spearman diagnostic differences | ALREADY_CORRECT | Expanded-family paragraph retains .408 [.088,.662] and stable .294 [−.076,.589]. | Independent file-order bootstrap reproduces both; analytic p=.020448 and permutation p=.0214 are distinct. No internal filename added. |
| CTK-AUDIT-006 | Identifying repository URL | EXCLUDED_BY_USER | Exact existing URL retained in named master. | URL handling deferred; no anonymous copy created. |
| CTK-AUDIT-009 | Closest related studies omitted | FIXED | Five-study paragraph, Patel chronological comparison and all five matching References entries are present. | Primary-source metadata/full texts verified; 19 unique, alphabetically ordered entries; all citations match. See E and H. |
| CTK-AUDIT-010 | Specificity evidence buried | FIXED | New “Control experiments help establish…” paragraph. | Original permutation separated from fresh-seed placebo/dose; original result sections retained. |
| CTK-AUDIT-011 | Permutation CSV evidence label | ALREADY_CORRECT | Original +0.30 versus extension −0.21/−0.07 remains clear. | Original arm vectors and extension run index confirm seeds 100–109 versus 200–209. No CSV-label explanation added. |
| CTK-AUDIT-012 | Ciaramella description unverified | ALREADY_CORRECT | Ciaramella paragraph unchanged. | Local version-of-record supports DEX grayscale images, CNNs, IID/non-IID and aggregator comparisons. |
| CTK-AUDIT-013 | Figure 3 legend ambiguity | FIXED | Figure 3, rendered page 31. | Requested legend labels present; standalone TIFF and embedded image pixels match. |
| CTK-AUDIT-014 | Figure 4 rounding | FIXED | Figure 4 note, page 32. | Explains 67.34% and 66.60% both appearing as 0.67; heatmap unchanged. |
| CTK-AUDIT-015 | One-seed sensitivity omitted | FIXED | Statistical and Dataset Validity: leave-one-seed-out sentence. | Recomputed nine-seed means span 11.06–12.65; not called a confidence interval. |
| CTK-AUDIT-016 | Bovet initial allegation | ALREADY_CORRECT | “Bovet, G.” retained. | Withdrawn finding remains closed; PDF/byline and APA initials support current entry. |
| CTK-AUDIT-018 | Introduction qualification stack | FIXED | “Across ten confirmatory seeds…” replaces the anchored paragraph. | Headline, own-domain gain and known-family cost retained. |
| CTK-AUDIT-019 | Discussion result repetition | FIXED | “The confirmatory contrast measures…” replaces the anchored paragraph. | Intervention interpretation retained without another numerical summary. |
| CTK-AUDIT-020 | Conclusion specificity understated | FIXED | Exact-dose/control sentences in Conclusion. | Verified 2.92→14.49 dose means and 10.04-point placebo contrast; negative/mixed findings retained. |
| CTK-AUDIT-021 | Micro-pooled effect unreported | FIXED | Secondary populations: sample-weighted paragraph. | 6.58 [4.64,8.65], 10/10; pooling 4.00; total 10.58; dowgin 46.98% of trials; exclusion gives 12.24. |
| CTK-AUDIT-022 | Expanded-family overlap/magnitude | FIXED | Expanded eligibility paragraph and Discussion. | 14 overlapping/18 new families; seed-macro 3.47 [2.45,4.45] versus 10.67; explicitly post hoc descriptive. |
| CTK-AUDIT-023 | Common dose flattening implied | FIXED | “The pooled increment combines different family-set responses.” | Primary 4.23 [2.53,6.55] versus replication 0.03 [−3.91,2.54]; Figure 5 unchanged. |
| CTK-AUDIT-024 | Own-domain client totals absent | FIXED | After “Anzhi therefore illustrates…” | Raw hits/trials reproduce −2.80,−0.40,6.48,13.61; first two intervals cross zero; play-late has 6 seeds and 107 trials/seed. |
| CTK-AUDIT-025 | Alternative learners/10% understated | FIXED | Learner and operating-point paragraphs. | 13.10/13.20/8.20/7.60 all 10/10; 1% 7.85 and 10% 13.78 remain secondary. |
| CTK-AUDIT-026 | Final-campaign provenance | FIXED | Reproducibility distinguishes final deterministic execution. | Current clean provenance and historical campaign records support wording. Private docs housekeeping EXCLUDED_BY_USER; no private file changed. |
| CTK-AUDIT-027 | Freeze archival preservation | PENDING_AUTHOR_ACTION | Table 2 now states resolved-config agreement. | Fresh proof matches all 140 freeze/run digests. Commit exists without containing ref; optional preservation remains author-owned, not a manuscript blocker. |
| CTK-AUDIT-028 | AI disclosure/reference policy | EXCLUDED_BY_USER | No AI disclosure inserted, as explicitly instructed by the author. | Five reference insertions separately completed under explicit authorization; disclosure exclusion is not certified publisher compliance. |
| CTK-AUDIT-029 | Single-family schematic interpretation | FIXED | Expanded Figure 1 note, page 17. | One schematic pair distinguished from simultaneous assignments/all-family removal; 6,000/client retained. |
| CTK-AUDIT-030 | Unequal corpus sizes imply unequal weights | FIXED | FedAvg methods now states equal aggregation weights. | Selected fit counts are 6,000/client; normalized weights are 0.25 each. |
| CTK-AUDIT-031 | Partition advantage unquantified | FIXED | Partition paragraph reports 57–60 versus median 52.5–56. | All 160 candidates evaluated read-only; 10/10 winners match; mean ratio advantage 8.58%. |
| CTK-AUDIT-032 | Abstract activity-only close | FIXED | Requested final two sentences appear once. | 142 whitespace-separated words; headline values intact. |
| CTK-AUDIT-033 | Five repetitive passages | FIXED | CELEST, principal result, dose and two validity paragraphs. | All five localized changes verified; substantive qualifications preserved. |
| CTK-AUDIT-034 | Negative Transfer unused in body | FIXED | Discussion now uses “a form of negative transfer.” | Key term retained. |
| CTK-AUDIT-035 | Unquoted secondary tied-rank p-value | EXCLUDED_BY_USER | Affected p-value is absent from manuscript. | No statistical source or frozen output changed; untied primary contrasts unaffected. |
| CTK-AUDIT-036 | Missing alternative descriptions | FIXED | Five wp:docPr descr attributes. | Descriptions embedded in image metadata; figure extents/resolution preserved. |

Reserved/closed concerns 004 (CyberForce), 005 (CELEST), 007 (representation counts) and 008 (primary ties) remain closed: primary texts, the overlap manifest and paired vectors support the unchanged descriptions/counts and untied tests. ID 017 was never used; no finding was invented for it.

**Section O coverage:** S-01→Edit 01; S-02→07; S-03→08; S-04→09/10; S-05→03; S-06→manual entries pending in E; S-07→04; S-08→14/15 (extra conclusion repetition superseded by the user’s instruction); S-09 excluded; S-10 declined/pending compliance; S-11→11; S-12→12; S-13→13/22; S-14→05; S-15→25; S-16→02; S-17→17; S-18→16; S-19→18; S-20→19; S-21→06; S-22→21; S-23→20; S-24/S-25 superseded by explicit user instructions against filename/CSV-label additions; S-26→23; S-27→22; S-28→24; S-29→26.

The Major/Minor/Enhancement findings, reference/statistical/implementation reviews and simulated reviewer objections in K–M were reconciled through these items. Novelty is answered by the five-study comparison; estimand objections by composition and controls; magnitude objections by micro weighting/new families; seed/partition objections by quantified sensitivity; practical objections by preserved own-domain, known-family and FPR costs. No new chronology, privacy, poisoning, external-corpus or extra-seed experiment is required. Private-docs housekeeping, optional extra citations and excluded unquoted-p-value maintenance are not publication blockers.

## D. Scientific and statistical consistency

Independent read-only calculations used Polars/NumPy/SciPy and frozen seed-level or raw hit/trial evidence. Primary inference was reconstructed without importing the project statistics module: 9,999 BCa resamples with Generator seed 20260924; exact two-sided signed ranks; Holm step-down restricted to the three primary FedAvg federation-wide contrasts. The declared methodology was verified, not replaced.

| Quantity | Independently verified result | Evidence |
|---|---|---|
| Primary FedAvg CTK | 11.9557561 pp; 95% BCa 9.1547740–15.2098805; positive 10/10 | `arm-metrics.parquet`, controlled exposure, salt 0, alpha .05, seeds 100–109 |
| Pooling | 1.5051250 pp; BCa −4.1490689–6.0980647; positive 7/10 | Same paired arms |
| Total | 13.4608811 pp; BCa 8.8177801–17.0401371; positive 10/10 | Same; unrounded CTK + pooling = total |
| Primary p-values | Raw .001953125/.322265625/.001953125; Holm .005859375/.322265625/.005859375 | Untied, nonzero original paired vectors |
| Own-domain total; CTK; pooling | 3.2563122; 10.8527449; −7.5964327 pp | Same evidence, distinct own-domain metric |
| Known-family change | −3.6054294 pp; BCa −4.50015–−2.85294 | Peer FedAvg minus local |
| Micro CTK; pooling; total | 6.5817372 [4.6433172,8.6452828]; 4.00155; 10.58328 pp | Micro metric; CTK positive 10/10 |
| Dowgin support/exclusion | 59,107/125,825 trials = 46.9756%; micro CTK without it 12.2366132 pp | Original `metrics/families.parquet` |
| Other learner CTKs | Central 13.09966; FedProx 13.19849; fine-tune 8.19751; blend 7.59783 pp; all 10/10 | Original paired arms |
| Alternative FPR targets | 1%:7.85054 pp (9/10 positive); 10%:13.78419 (10/10) | Secondary operating-point comparisons |
| Placebo; peer-minus-placebo | −0.5389518; 10.0371719 [8.3480860,12.2803673] pp, 10/10 | `controls-seed-effects.csv`, pooled sets, federation-wide, seeds 320–329 |
| Exact-dose pooled means | 2.92,4.90,7.83,12.48,14.49 pp at 10,25,50,100,200; all 10/10 | `exact-dose-seed-effects.csv`, seeds 310–319 |
| Dose 100→200 by set | Primary 4.22898 [2.53282,6.54648]; replication .02977 [−3.91348,2.53768] pp | Paired extension increments |
| New expanded families | 18 families; seed-macro 3.46656 [2.45249,4.44852] pp,10/10; overlap 14 families,10.666 pp | `large-family-seed-ctk.csv`, seeds 300–309; post hoc descriptive split |
| Leave-one-seed-out | 11.06–12.65 pp, every estimate >3 | Ten original CTK effects |
| Exposure and budget | Mean 2,073.3 selected-family fit rows; 6,000/client; 24,000 total | Original `exposure.parquet`; same seeded replacement order |
| Partition selection | Chosen 57–60 versus median 52.5–56;8.58% average ratio gain | Read-only 160-candidate evaluation;10/10 stored winners match |

The four own-domain client totals were reconstructed from hits/trials, retaining eligibility and 8/10/10/6 contributing seeds. Table 1 totals match the frozen client audit. Every Table 4 measurement and all eight original sensitivity rows of Table 5 were re-derived; Table 3 and Figure 2 remain numerically unchanged. All 108 representation means/BCa endpoints reproduce from their seed table. Canonical Spearman rho/intervals reproduce for all 32 and stable 27 families; permutation p=.0214 independently reproduces using seed 993. The separate permutation run index confirms 200–209. Existing equal-test-FPR summaries were checked as frozen descriptive diagnostics; the earlier audit’s complete score-level reconstruction was not repeated in this pass.

All 215 manifest digests match (90 original,5 extension,120 extension-b). All 140 confirmatory resolved-configuration digests match current configurations and run fingerprints produced by code/configs extracted from freeze commit `e079972`. Whole-config fingerprint changes reflect later extension entries, not confirmatory run-protocol changes. No new hyperparameter selection or training was performed.

Code inspection confirms target-only versus all-client exclusions; seeded replacement with matched budgets; normalized selected-count weights; group-based roles and support-only best-of 16 selection; benign calibration with the higher quantile and strict exceedance; FedAvg 20×2 versus local 10/central 20 epochs; FedProx mu=.1 and fresh local Adam state; fit-only representation transforms; and distinct client/family/micro/own-domain populations. The representation overlap manifest independently confirms 554,136 applications (170,256 malware/383,880 benign), widths 925/2,390/2,793/17,483.

Known-family losses, negative own-domain pooling/client totals, negative replication/expanded-family estimates, report-JSON deterioration, no hiddad rescue, AUROC/AP declines, the unresolved original own-domain permutation interval and FPR exceptions remain present. No exploratory comparison entered the primary Holm family. No new unsupported numerical claim was found. This pass did not repeat the audit’s test suite, raw preprocessing or training; its verification addresses editorial changes and independent evidence calculations.

## E. Literature and reference verification

All five essential studies were examined in their retained local full texts. During this final bibliography pass, their bylines and bibliographic fields were rechecked against the PDFs and authoritative publication records before insertion. Current Crossref records were retrieved for Patel, Popoola, Shao and Shen; the original PoPETs publisher record/PDF reconfirmed Gálvez after a Crossref rate-limit response. All five bibliography entries are now **FIXED**, each present exactly once. All 19 entries are cited in the body, and every body author-year citation has a matching entry. Patel is cited twice (related work and chronology); the other four additions are each cited once. Existing citations were not changed.

| Study | Identifier/metadata verification | Full-text/setup verification | Citation / entry |
|---|---|---|---|
| Gálvez, Moonsamy & Diaz (2021), LiM | [Publisher PDF](https://petsymposium.org/popets/2021/popets-2021-0062.pdf); DOI 10.2478/popets-2021-0062; PoPETs 2021(4),96–116 | Version of record; privacy-respecting Android federated classification and federation/security evaluation; no matched CTK decomposition | Present / FIXED |
| Patel, Tomar, Pateriya & Haripriya (2026), FL-MalDrift | [Publisher](https://www.nature.com/articles/s41598-025-31592-z); DOI 10.1038/s41598-025-31592-z; Scientific Reports 16,1821 | Publisher PDF explicitly prints 2026,16:1821 despite 2025 online/DOI metadata; chronological AndroZoo evaluation and drift adaptation | Present twice / FIXED |
| Popoola, Ande, Adebisi, Gui, Hammoudeh & Jogunola (2022) | [DOI](https://doi.org/10.1109/JIOT.2021.3100755); IEEE IoT Journal 9(5),3930–3944; publication 2022-03-01 | Institutional accepted manuscript; Bot-IoT/N-BaIoT classes omitted per edge device; federated/localized/centralized comparisons | Present / FIXED |
| Shao, Otani, Yamakawa, Hirasuka & Wai Shiang (2026) | [J-STAGE](https://www.jstage.jst.go.jp/article/transfun/advpub/0/advpub_2026EAP1060/_article/-char/en); DOI 10.1587/transfun.2026EAP1060; advance publication June 5,2026; article 2026EAP1060 | Accepted advance text; missing positive-class support and persistent bias;23 SisFall clients/five seeds; byline “Cheah WAI SHIANG” supports “Wai Shiang, C.” | Present / FIXED |
| Shen, Yang, Chu, Fan, Niyato & Lam (2024), FLEKD-IDS | [DOI](https://doi.org/10.1109/ICC51166.2024.10622262); ICC 2024,2034–2039 | Author preprint; seven classes/clients, one attack class missing per client, Table IV; local versus FL/distillation comparisons | Present / FIXED |

The paragraph does not describe these papers as ignoring missing threats. CyberForce explicitly includes missing-client fractions through all-client absence and local references; CELEST covers locally new HTTP threat families. Retained author texts support those distinctions. Ciaramella’s supported version-of-record description remains unchanged. CTK-Android’s contribution is the matched-budget local/absent-everywhere/peer-present Android decomposition and empirical evidence, not invention of missing-threat FL. Targeted 2024–2026 searches did not establish a closer work implementing that measurement design. No claim of an exhaustive literature search or absence of prior research was added; no optional reference was added to inflate count.

The 14 existing entries were preserved and checked against retained PDFs and live metadata/proceedings where accessible: Allix 2016; Arp 2014/2022; Ciaramella 2026; Feng 2025; Haque 2026; Holm 1979; Kamol 2026; Li 2020; Mariconti 2017; McMahan 2017; Ongun 2025; Pendlebury 2019; Sebastián 2020. [PMLR](https://proceedings.mlr.press/v54/mcmahan17a.html) confirms volume 54,1273–1282 and editors Singh/Zhu; [MLSys](https://proceedings.mlsys.org/paper_files/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html) confirms FedProx’s authors/year/volume. [Holm’s institutional scan](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf) confirms 6(2),65–70 and the step-down method; the stable JSTOR URL was retained, with no invented DOI. OpenReview still presents a browser challenge for the ICLR version; LAMDA’s retained preprint supports the cited scientific statements. CyberForce/CELEST/AVClass 2 and some institutional deposits were examined as author versions, not silently called publisher PDFs. No uncertainty requiring correction of an existing entry was identified.

### Five completed bibliography insertions

**FIXED for all five.** The following verified entries are present in the saved Word manuscript with the indicated alphabetical neighbors, matching reference formatting and functional DOI hyperlinks. No manual author entry remains. **S-06’s Popoola insertion location was corrected:** Popoola follows Pendlebury, not Patel.

1. After Feng, before Haque: Gálvez, R., Moonsamy, V., & Diaz, C. (2021). Less is more: A privacy-respecting Android malware classifier using federated learning. *Proceedings on Privacy Enhancing Technologies, 2021*(4), 96–116. https://doi.org/10.2478/popets-2021-0062
2. After Ongun, before Pendlebury: Patel, A., Tomar, D. S., Pateriya, R. K., & Haripriya, R. (2026). FL-MalDrift: A federated learning framework for malware detection under local concept drift. *Scientific Reports, 16*, Article 1821. https://doi.org/10.1038/s41598-025-31592-z
3. After Pendlebury, before Sebastián: Popoola, S. I., Ande, R., Adebisi, B., Gui, G., Hammoudeh, M., & Jogunola, O. (2022). Federated deep learning for zero-day botnet attack detection in IoT-edge devices. *IEEE Internet of Things Journal, 9*(5), 3930–3944. https://doi.org/10.1109/JIOT.2021.3100755
4. After Sebastián, before Shen: Shao, X., Otani, A., Yamakawa, K., Hirasuka, Y., & Wai Shiang, C. (2026). Objective mismatch in federated learning under missing class support. *IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences*. Advance online publication. https://doi.org/10.1587/transfun.2026EAP1060
5. After Shao: Shen, J., Yang, W., Chu, Z., Fan, J., Niyato, D., & Lam, K.-Y. (2024). Effective intrusion detection in heterogeneous Internet-of-Things networks via ensemble knowledge distillation-based federated learning. In *ICC 2024 – IEEE International Conference on Communications* (pp. 2034–2039). IEEE. https://doi.org/10.1109/ICC51166.2024.10622262

No volume/issue/pages were invented for Shao’s advance publication (article ID 2026EAP1060). The current [J-STAGE publisher byline and publication status](https://www.jstage.jst.go.jp/article/transfun/advpub/0/advpub_2026EAP1060/_article/-char/en) explicitly identify “Cheah WAI SHIANG” and advance online publication dated June 5, 2026. Its surname capitalization and retained PDF take precedence over Crossref’s incorrectly split given/family fields. [Patel’s publisher record](https://www.nature.com/articles/s41598-025-31592-z) identifies volume 16, Article 1821 (2026), with version of record January 14, 2026, despite initial online publication December 15, 2025. Popoola uses the final March 2022 volume year, 9(5), 3930–3944; Shen uses the final ICC 2024 proceedings, 2034–2039. All authors, title words, venues, page spans and DOI strings above were checked. No supplied candidate required a bibliographic change. The final list has 19 unique entries in APA alphabetical order; the two Arp entries retain their correct ordering by subsequent author. All 14 original entries remain intact and retain the previous source verification. Existing reference PDFs remain verification material; no submitted package or copyrighted-PDF redistribution was produced.

A normalized 10-consecutive-word comparison of the final body against all 21 retained PDFs found no exact match. The new related-work paragraph is an attributed paraphrase. This limited extracted-text check cannot certify corpus-wide originality or close-paraphrase similarity. No commercial similarity service or authorship detector was available/run; no percentage was invented.

## F. Formatting and publisher compliance

- Abstract: **142 whitespace-separated words**, within the verified 100–150 requirement; headline values intact.
- Total: **12,882 words by Microsoft Word’s native counter**; independent whitespace count including tables/equations 12,830. Tokenization differs. This is the full chapter, not a proposal. The abstract and all non-reference text are unchanged from the preceding revised master.
- Key terms:10, including Negative Transfer. Title/subtitle unchanged at 69/27 characters.
- Native Word export: **52 pages**, versus 51 immediately before bibliography completion (49 in the original audited manuscript). References occupy pages 48–51; Key Terms remains on a separate page, now 52. All four References pages and the following Key Terms page were visually inspected as 150-dpi Poppler PNGs. No clipping, overlap, unwanted blank page, split reference paragraph, orphan heading or inconsistent reference formatting was found. Pages 1–47 are pixel-identical to the previously inspected render; the Key Terms page body is also pixel-identical, with only its page number changed. Figures 1–5 remain on pages 17,26,31,32,35; tables 1–5 remain on 13,20,26,30,37. All five new DOI links are valid external Word relationships and survive PDF export as the exact intended URI annotations.
- Figure 3 retains 2722×1285 grayscale pixels at 400dpi. Outside the legend text rectangle, axes, plotted markers, connector lines and grid are preserved pixel-for-pixel. The four other embedded images are byte-identical. All five standalone TIFFs retain 400dpi and original dimensions. Five alternative descriptions are embedded.
- Five complete table structures, three editable OMML equations, styles and section hierarchy remain intact. No accidental paragraph/table duplication was found. ZIP/XML/relationship checks pass; Word opens/exports without repair.
- Author order/mapping is exact: Naslouby 1 (corresponding), Lachgar 2, Hrimech 1. Both affiliations and all three emails match the supplied text. The [public ORCID record](https://orcid.org/0009-0002-7295-7816), independently queried through its public API, gives Salaheddine Naslouby. Only his supplied ORCID is included. Superscripts and email/ORCID relationship targets were checked.
- **AI disclosure: EXCLUDED_BY_USER.** No disclosure statement was inserted. The prior verification of [contributor guidance](https://www.igi-global.com/publish/contributor-resources/before-you-write/) remains recorded; the author’s exclusion is not a claim of compliance with that requirement. No further disclosure action is requested in this bibliography task.
- That guide independently confirms Word format, APA 7, abstract 100–150, at least 7 key terms, a general 8,000-word chapter minimum, separate TIFFs and double-anonymized review. The [image guide](https://www.igi-global.com/publish/contributor-resources/image-guide/) gives a 300dpi benchmark/readability guidance. The specific call page was inaccessible; historical dates/10,000-word floor were not claimed freshly verified. The chapter exceeds either floor.
- This is the named master. No anonymous copy was created. A future review copy requires separate handling of author/affiliation/contact/ORCID and identifying metadata; the repository URL remains untouched and explicitly author-deferred.

The packaged `render_docx.py` was attempted again and failed because LibreOffice `soffice.exe` is unavailable. Native Microsoft Word successfully opened an external read-only copy and exported the final 52-page PDF; bundled Poppler produced all 52 page PNGs. The final file opens and renders without repair. No renderer saved over the master, and no runtime was installed. Temporary render artifacts remain outside the project.

## G. Remaining author decisions

No manuscript-content correction or bibliography-entry action remains from this task.

- AI disclosure remains explicitly EXCLUDED_BY_USER, without certification of publisher compliance.
- The author reports independent peer-review arrangements addressed externally. This is recorded as an author statement; no editorial safeguard is claimed independently verified and no manuscript or administrative change was made.
- The previously assessed optional preservation of commit `e079972095dbfd852e1a1ffb887be0e959cdc91f` remains author-owned and deferred. The unused local tag name `protocol-freeze-2026-09-24` was previously found safe; no tag, push or history change was made. This is not a manuscript blocker and is not reopened here.

The repository URL, private docs and unreported secondary-p-value maintenance retain their explicit exclusions. No new experiment or optional enhancement is requested.

## H. Final idempotency result

- Initial revision: 34 logical operations, including all 26 surgical edits and author metadata; its second application required zero modifications. Those changes are preserved.
- Bibliography completion: **five insertions**, adding Gálvez, Patel, Popoola, Shao and Shen once each. Combined manuscript change count: 39 logical operations.
- Baseline for this surgical bibliography pass: SHA-256 **`805af4f204507ed91290926194a5cdd7c67ab057b095ce7874e0d340c70b790d`**, reconciled before editing; an exact external backup was retained.
- Second execution of the bibliography procedure against the saved/reopened master: **zero modifications**. The DOCX SHA-256 remained unchanged. Exact existing entries and link targets were checked before skipping each insertion.
- Final bibliography: **19 unique, alphabetically ordered entries**, including all 14 unchanged original reference paragraphs. All 19 are cited; every body author-year citation matches a reference. Patel appears twice; the other four additions appear once each in body text. No in-text citation changed.
- Structural validation: ZIP integrity and parsing of every XML/rels part pass; all relationship IDs resolve. The only changed package members in this pass are `word/document.xml` and `word/_rels/document.xml.rels`. Five new external DOI relationships resolve to the verified identifiers. All existing relationships are unchanged. Removing only the five new reference paragraphs exactly reproduces the preceding complete document XML tree, proving preservation of abstract, body, headings, tables, figures, equations, key terms, formatting, metadata links and URL. The file reopens successfully through python-docx and native Word. Counts: 214 top-level paragraphs, 5 tables, 5 drawings, 3 editable OMML equations and 5 image descriptions.
- Visual validation: native Word exports 52 pages. References pages 48–51 and Key Terms page 52 were inspected; no visual defect was found. All 47 earlier pages are pixel-identical to the preceding verified render; the Key Terms body is pixel-identical after repagination. All 5 new DOI targets survive as PDF link annotations. No unwanted blank page or split reference paragraph was introduced.
- The preceding full integrity check covered 12,295 files (12,262 hashes and 33 large-data inventories); it remains historical evidence for the initial revision. In this pass, the audit, 21 reference PDFs, figure files and unrelated pre-existing proposal edit retain their recorded baseline SHA-256 values. Only the manuscript and this existing report were written in the project; no research code, configuration, dataset, result or private-docs write was performed. The earlier Figure 3 edit is preserved.
- No commit, push, tag, branch, stash or history rewrite was performed. HEAD remains 9645979.
- Final manuscript SHA-256: **`c3a5a090e193da7733acb9104d4502ce7fa57a8daf098b06d690214fce9a1764`**.

### Exact reversible change record

Each anchor is exact original paragraph text for a paragraph replacement, exact replaced text for an inline edit, or the locating paragraph for an insertion. Replacement text is complete. Empty original means insertion. Superscripts/line breaks/links and image metadata were also validated structurally; the readable metadata text below does not substitute for those checks.

<details>
<summary>Expand the initial 34 exact anchors and replacements</summary>

**Operation 1 — replace**

Anchor: Separate dose, placebo, and representation extensions examine effect heterogeneity and specificity. The findings support exposure-aware evaluation within the tested offline populations and operating conditions.

Original: Separate dose, placebo, and representation extensions examine effect heterogeneity and specificity. The findings support exposure-aware evaluation within the tested offline populations and operating conditions.

Replacement: In fresh-seed extensions, a wrong-family placebo recovers almost none of the gain, and complementary gain rises with the exact number of peer examples. Local-versus-federated comparisons alone cannot show how much of a collaborative gain depends on which families peers hold.

**Operation 2 — paragraph**

Anchor: The main result is that complementary exposure contributes substantially to the average federation-wide unseen-family recall of the tested FedAvg model. Across ten confirmatory seeds, the CTK gain is 11.96 percentage points, whereas the pooling estimate is 1.51 points and its interval includes both loss and benefit. These averages are accompanied by important qualifications. The total own-domain benefit is much smaller because the pooling component is negative. Some families respond strongly, others barely respond, and some client-level benefits coexist with losses on known malware. Alternative learners change these tradeoffs. Fresh-seed extensions establish useful exposure and representation patterns without converting those later analyses into original confirmatory discoveries.

Original: The main result is that complementary exposure contributes substantially to the average federation-wide unseen-family recall of the tested FedAvg model. Across ten confirmatory seeds, the CTK gain is 11.96 percentage points, whereas the pooling estimate is 1.51 points and its interval includes both loss and benefit. These averages are accompanied by important qualifications. The total own-domain benefit is much smaller because the pooling component is negative. Some families respond strongly, others barely respond, and some client-level benefits coexist with losses on known malware. Alternative learners change these tradeoffs. Fresh-seed extensions establish useful exposure and representation patterns without converting those later analyses into original confirmatory discoveries.

Replacement: Across ten confirmatory seeds, complementary peer exposure raises FedAvg federation-wide unseen-family recall by 11.96 percentage points (95% BCa interval 9.15–15.21). Generic pooling contributes 1.51 points, with uncertainty spanning both positive and negative effects. The own-domain total gain is 3.26 points, while known-family recall falls by 3.61 points. The study examines these benefits and costs across families, clients, and alternative learners.

**Operation 3 — insert_after**

Anchor: CyberForce provides an especially close conceptual comparison. Feng et al. (2025) vary the fraction of clients missing particular malware and evaluate mitigation of that malware using federated reinforcement learning. Their study includes a condition in which all clients lack the malware, local references, and different aggregators. It therefore cannot fairly be characterized as ignoring missing threats or relying exclusively on aggregate accuracy. Its task is selecting moving-target defenses for Internet of Things (IoT) malware, however, and its missing-client sweep does not implement the matched-budget Android recall decomposition examined here. The present study also tests exact peer sample doses and a wrong-family placebo. The Android exposure controls and recall decomposition extend this earlier work on missing threats.

Original: [insertion; no original text removed]

Replacement: Missing-class support has also been examined in federated intrusion detection. Shen et al. (2024) evaluate knowledge distillation when an attack class is missing from individual clients, while Popoola et al. (2022) study federated detection of previously unseen botnet traffic. Shao et al. (2026) show that missing positive-class support can leave a persistent bias despite apparent training convergence. In Android malware detection, Gálvez et al. (2021) investigate privacy-respecting federated classification, and Patel et al. (2026) address concept drift through federated adaptation. These studies demonstrate the relevance of collaboration under incomplete or changing threat coverage. CTK-Android addresses a different measurement question: it compares peer-present and family-absent-everywhere conditions under matched training budgets, alongside a local reference, to separate complementary exposure from the residual collaboration gain.

**Operation 4 — append**

Anchor: Grouped random partitions and chronological partitions answer different questions; neither should be described as the other.

Original: Grouped random partitions and chronological partitions answer different questions; neither should be described as the other.

Replacement: Grouped random partitions and chronological partitions answer different questions; neither should be described as the other. Patel et al. (2026) additionally evaluate chronological Android malware data under federated learning. CTK-Android instead isolates family-exposure effects within group-aware partitions and does not claim forward-in-time detection performance.

**Operation 5 — paragraph**

Anchor: Note. Schematic of the implemented exposure conditions. Several families can be assigned to different targets within a run. Full exposure lifts deliberate exclusions but remains budgeted.

Original: Note. Schematic of the implemented exposure conditions. Several families can be assigned to different targets within a run. Full exposure lifts deliberate exclusions but remains budgeted.

Replacement: Note. The schematic illustrates one target-family pair. Each run can assign several families to different targets. In the peer-present condition, a selected family is withheld only from its assigned target, which may retain other selected families. In the absent-everywhere condition, all selected families are withheld from every client. Replacement examples preserve the 6,000-sample training budget per client. Full exposure removes the deliberate exclusions but retains the budget.

**Operation 6 — replace**

Anchor: Clients start each round from the global parameters, fit locally, and return parameters for sample-count-weighted aggregation.

Original: Clients start each round from the global parameters, fit locally, and return parameters for sample-count-weighted aggregation.

Replacement: Clients start each round from the global parameters, fit locally, and return parameters for sample-count-weighted aggregation. Because all four clients contribute exactly 6,000 fit examples, each client receives equal aggregation weight.

**Operation 7 — paragraph**

Anchor: The CTK mean is 11.96 percentage points, with a 95% BCa interval of 9.15–15.21 points. Every confirmatory seed has a positive difference. The total peer-versus-local gain is 13.46 points, with interval 8.82–17.04, also positive in all ten seeds. Both have Holm-adjusted p = .00586 across the three primary contrasts. Generic pooling contributes 1.51 points, with interval −4.15 to 6.10 and adjusted p = .32227. This interval neither establishes a positive pooling benefit nor establishes that pooling is exactly ineffective. It permits both modest benefit and modest harm. The evidence is strongest for the complementary exposure contrast and for the combined collaboration gain in this specified population.

Original: The CTK mean is 11.96 percentage points, with a 95% BCa interval of 9.15–15.21 points. Every confirmatory seed has a positive difference. The total peer-versus-local gain is 13.46 points, with interval 8.82–17.04, also positive in all ten seeds. Both have Holm-adjusted p = .00586 across the three primary contrasts. Generic pooling contributes 1.51 points, with interval −4.15 to 6.10 and adjusted p = .32227. This interval neither establishes a positive pooling benefit nor establishes that pooling is exactly ineffective. It permits both modest benefit and modest harm. The evidence is strongest for the complementary exposure contrast and for the combined collaboration gain in this specified population.

Replacement: The CTK mean is 11.96 percentage points (95% BCa interval 9.15–15.21), positive in every confirmatory seed. The total peer-versus-local gain is 13.46 points (8.82–17.04), also positive in all ten seeds. Both contrasts have Holm-adjusted p = .00586. Generic pooling contributes 1.51 points (−4.15 to 6.10; adjusted p = .32227), an estimate compatible with either a modest benefit or harm. The displayed CTK and pooling estimates sum to 13.47 points because of rounding; their unrounded sum equals the 13.46-point total. The CTK contrast includes the training-composition change described in Figure 1: across seeds, approximately 2,073 of the 24,000 fitted examples differ between the peer-present and absent-everywhere arms. The result therefore estimates the full controlled-exposure intervention rather than an isolated family-specific parameter effect.

**Operation 8 — insert_after**

Anchor: The CTK mean is 11.96 percentage points (95% BCa interval 9.15–15.21), positive in every confirmatory seed. The total peer-versus-local gain is 13.46 points (8.82–17.04), also positive in all ten seeds. Both contrasts have Holm-adjusted p = .00586. Generic pooling contributes 1.51 points (−4.15 to 6.10; adjusted p = .32227), an estimate compatible with either a modest benefit or harm. The displayed CTK and pooling estimates sum to 13.47 points because of rounding; their unrounded sum equals the 13.46-point total. The CTK contrast includes the training-composition change described in Figure 1: across seeds, approximately 2,073 of the 24,000 fitted examples differ between the peer-present and absent-everywhere arms. The result therefore estimates the full controlled-exposure intervention rather than an isolated family-specific parameter effect.

Original: [insertion; no original text removed]

Replacement: Control experiments help establish that the gain depends on the supplied family information rather than merely the presence of additional malware examples. In the original confirmatory seeds, family-label permutation reduces mean CTK to 0.30 points (interval −0.36 to 1.02). In a separate fresh-seed extension, substituting a different malware family under support-matched exposure produces a placebo effect of −0.54 points, whereas peer-present exposure exceeds that placebo by 10.04 points (8.35–12.28), positive in all ten extension seeds. A further extension finds positive CTK at every tested exact peer dose from 10 to 200 examples. These checks support the family-specific interpretation without being combined with the original confirmatory tests.

**Operation 9 — append**

Anchor: and total gain of 14.88 points.

Original: and total gain of 14.88 points.

Replacement: and total gain of 14.88 points. Weighting every hidden-family test application equally produces a smaller but still positive effect: micro-pooled CTK is 6.58 points (interval 4.64–8.65), positive across all ten confirmatory seeds. Under this weighting, pooling contributes 4.00 points and the total gain is 10.58 points. Much of the difference from the client-macro estimate comes from dowgin, which contributes approximately 47% of the hidden-family test applications but has almost no CTK gain. Excluding dowgin raises micro-pooled CTK to 12.24 points.

**Operation 10 — replace**

Anchor: At the stricter 1% nominal FPR, the FedAvg federation-wide CTK estimate is 7.85 points, smaller than at 5%.

Original: At the stricter 1% nominal FPR, the FedAvg federation-wide CTK estimate is 7.85 points, smaller than at 5%.

Replacement: FedAvg federation-wide CTK remains positive at both alternative operating points, reaching 7.85 points at 1% nominal FPR and 13.78 points at 10%, compared with 11.96 points at the primary 5% operating point.

**Operation 11 — append**

Anchor: Fine-tuning reaches 62.16%, and blending reaches 63.66%, both below the FedAvg mean.

Original: Fine-tuning reaches 62.16%, and blending reaches 63.66%, both below the FedAvg mean.

Replacement: Fine-tuning reaches 62.16%, and blending reaches 63.66%, both below the FedAvg mean. The complementary-exposure contrast remains positive across the alternative collaborative learners. Mean federation-wide CTK is 13.10 points for centralized training, 13.20 for FedProx, 8.20 for fine-tuned FedAvg, and 7.60 for blending, with positive differences in all ten seeds for each learner. These secondary comparisons indicate that learner choice changes the magnitude of CTK, without reversing its direction in the tested configurations.

**Operation 12 — append**

Anchor: Anzhi therefore illustrates the known-family cost of collaboration.

Original: Anzhi therefore illustrates the known-family cost of collaboration.

Replacement: Anzhi therefore illustrates the known-family cost of collaboration. The own-domain total gain also differs substantially across clients: −2.80 points for Anzhi, −0.40 for AppChina, 6.48 for play-early, and 13.61 for play-late. The first two estimates have intervals spanning zero. The positive own-domain aggregate is therefore not shared uniformly across the four domains, and the play-late estimate is based on approximately 107 hidden-family test applications per contributing seed.

**Operation 13 — replace**

Anchor: These estimates are consistent with diminishing gains at the upper tested range, but neither prove a plateau nor justify a universal minimum dose.

Original: These estimates are consistent with diminishing gains at the upper tested range, but neither prove a plateau nor justify a universal minimum dose.

Replacement: The pooled increment combines different family-set responses. Between 100 and 200 peer examples, CTK increases by 4.23 points (interval 2.53–6.55) in the primary set, compared with 0.03 points (−3.91 to 2.54) in the replication set. The primary-set gain therefore continues across the tested range, while the replication-set response is approximately flat. The evidence does not establish a common saturation point or universal minimum dose.

**Operation 14 — append**

Anchor: The expanded set also overlaps previously studied families, so it should be described as a broader family analysis on fresh seeds, not 32 entirely new independent families.

Original: The expanded set also overlaps previously studied families, so it should be described as a broader family analysis on fresh seeds, not 32 entirely new independent families.

Replacement: The expanded set also overlaps previously studied families, so it should be described as a broader family analysis on fresh seeds, not 32 entirely new independent families. Fourteen of the 32 families overlap the primary or replication sets. For the 18 newly examined families, seed-level family-macro CTK averages 3.47 points (interval 2.45–4.45), compared with 10.67 points for the overlapping families. The newly examined subset has a positive mean in all ten fresh seeds, although its magnitude is considerably smaller than the primary estimate. This post hoc subdivision is descriptive and does not represent an additional confirmatory test.

**Operation 15 — append**

Anchor: The primary point estimates place most of the total benefit in the latter component, but the conclusion is conditional on the chosen learner, families, budget, and population.

Original: The primary point estimates place most of the total benefit in the latter component, but the conclusion is conditional on the chosen learner, families, budget, and population.

Replacement: The primary point estimates place most of the total benefit in the latter component, but the conclusion is conditional on the chosen learner, families, budget, and population. The disjoint replication families produce a mean CTK of 5.08 points, while the 18 newly examined families in the expanded analysis yield 3.47 points. Both estimates support a positive complementary-exposure effect, but the 11.96-point primary estimate should not be presented as the expected gain for arbitrary Android malware families.

**Operation 16 — replace**

Anchor: Exact-dose results clarify the role of realized peer support, while permutation and placebo controls strengthen the family-specific interpretation.

Original: Exact-dose results clarify the role of realized peer support, while permutation and placebo controls strengthen the family-specific interpretation.

Replacement: The exact-dose extension produces positive CTK at every tested peer dose, with mean gains increasing from 2.92 points at 10 examples to 14.49 points at 200. Family-permutation controls yield near-zero effects, and the wrong-family placebo does not reproduce the benefit of supplying the selected families: peer-present CTK exceeds the placebo by 10.04 points (interval 8.35–12.28). These separately evaluated controls strengthen the interpretation that the composition of peer threat exposure matters, rather than additional malware quantity alone.

**Operation 17 — paragraph**

Anchor: In the constructed LAMDA federation, FedAvg gains substantially from peer examples of locally withheld families relative to its performance when those families are absent everywhere. Matching client sample counts and the collaborative training schedule narrows the explanation compared with a local-versus-federated comparison alone. The intervention still changes sample composition and recalibrates the fitted model. The result supports the usefulness of complementary exposure under those conditions; it does not identify the model parameters or features responsible for the gain.

Original: In the constructed LAMDA federation, FedAvg gains substantially from peer examples of locally withheld families relative to its performance when those families are absent everywhere. Matching client sample counts and the collaborative training schedule narrows the explanation compared with a local-versus-federated comparison alone. The intervention still changes sample composition and recalibrates the fitted model. The result supports the usefulness of complementary exposure under those conditions; it does not identify the model parameters or features responsible for the gain.

Replacement: The confirmatory contrast measures the response to the controlled exposure intervention shown in Figure 1. Matched client training budgets and identical collaborative training schedules make this comparison more informative than a local-versus-federated result alone. However, replacing withheld examples changes training composition, and each fitted model is calibrated separately. The estimated gain therefore reflects the complete intervention rather than identifying which features or model parameters account for it.

**Operation 18 — append**

Anchor: They provide limited precision for subgroup inference and do not constitute ten independent external datasets.

Original: They provide limited precision for subgroup inference and do not constitute ten independent external datasets.

Replacement: They provide limited precision for subgroup inference and do not constitute ten independent external datasets. A leave-one-seed-out sensitivity check gives mean CTK estimates between 11.06 and 12.65 points, with every estimate remaining above the prespecified three-point practical threshold. This indicates that the primary mean is not driven by a single seed, although it does not replace the reported confidence interval.

**Operation 19 — append**

Anchor: This selection uses support and eligibility information rather than learned prediction quality.

Original: This selection uses support and eligibility information rather than learned prediction quality.

Replacement: This selection uses support and eligibility information rather than learned prediction quality. Across confirmatory seeds, the selected partitions contain 57–60 eligible client-family pairs, compared with a median of 52.5–56 across their candidate partitions. Selection increases the mean eligible-pair count by approximately 9% relative to the candidate median without using test performance.

**Operation 21 — paragraph**

Anchor: Note. Entries are mean recall proportions, nominal 5% FPR, seeds 100–109. Full exposure refers to FedAvg here; it is not a theoretical ceiling.

Original: Note. Entries are mean recall proportions, nominal 5% FPR, seeds 100–109. Full exposure refers to FedAvg here; it is not a theoretical ceiling.

Replacement: Note. Cells show mean recall proportions rounded to two decimals, at nominal 5% FPR across seeds 100–109. The text reports the underlying values as percentages. For adwo, local and peer-present recalls of 67.34% and 66.60% both appear as 0.67 in the figure. Full exposure refers to FedAvg and is not a theoretical performance ceiling.

**Operation 22A — replace**

Anchor: frozen uncertainty estimates

Original: frozen uncertainty estimates

Replacement: seed-level uncertainty intervals

**Operation 22C — replace**

Anchor:  These extensions clarify the exposure manipulation without being pooled into the original confirmatory test.

Original:  These extensions clarify the exposure manipulation without being pooled into the original confirmatory test.

Replacement: [deleted]

**Operation 22D — replace**

Anchor:  These distinctions limit the language used for both positive and negative results.

Original:  These distinctions limit the language used for both positive and negative results.

Replacement: [deleted]

**Operation 22E — replace**

Anchor:  These are substantive limits on application of the findings, even when the within-study numerical and provenance checks are satisfied.

Original:  These are substantive limits on application of the findings, even when the within-study numerical and provenance checks are satisfied.

Replacement: [deleted]

**Operation 23 — replace**

Anchor: The own-domain result is especially informative: negative pooling offsets much of a positive CTK effect.

Original: The own-domain result is especially informative: negative pooling offsets much of a positive CTK effect.

Replacement: In the own-domain evaluation, negative pooling represents a form of negative transfer that offsets much of the positive complementary-exposure effect.

**Operation 24 — replace**

Anchor: Hyperparameters and statistical procedures were frozen before the confirmatory evaluation.

Original: Hyperparameters and statistical procedures were frozen before the confirmatory evaluation.

Replacement: Hyperparameters and statistical procedures were frozen before confirmatory evaluation. The stored resolved configurations of all confirmatory runs match the frozen run-level protocol.

**Operation 25 — append**

Anchor: The evidence package records execution and analysis revision f6302f7906824945731dadbbeb44357f3d025aaf, with matching revisions and clean analysis sources.

Original: The evidence package records execution and analysis revision f6302f7906824945731dadbbeb44357f3d025aaf, with matching revisions and clean analysis sources.

Replacement: The evidence package records execution and analysis revision f6302f7906824945731dadbbeb44357f3d025aaf, with matching revisions and clean analysis sources. The reported results come from the final deterministic execution, after GPU dropout seeding and deterministic kernels were enabled. Two earlier executions used the same confirmatory configuration but were not bit-reproducible; both produced a FedAvg CTK estimate of approximately 11.7 points. These earlier executions are not pooled into the final reported statistics.

**Operation AUTHOR — insert_before**

Anchor: Abstract

Original: [insertion; no original text removed]

Replacement: Salaheddine Naslouby1,*, Mohamed Lachgar2, Hamid Hrimech1
1 Hassan First UniversityNational School of Applied Sciences (ENSA), LAMSAD LaboratoryBerrechid, Morocco
2 Cadi Ayyad UniversityHigher Normal School (ENS), L2IS LaboratoryMarrakech, Morocco
* Corresponding author: Salaheddine NasloubyEmail: naslouby.salahe@gmail.com; ORCID: 0009-0002-7295-7816
Mohamed Lachgar: m.lachgar@uca.ac.maHamid Hrimech: hamid.hrimech@uhp.ac.ma

**Operation 26.1 — image_alt**

Anchor: Picture 1

Original: [insertion; no original text removed]

Replacement: Exposure schematic: a selected family is withheld at its target, retained at peers in the peer-present arm, absent at all clients in the absent arm, and allowed everywhere in full exposure; client training counts are matched.

**Operation 26.2 — image_alt**

Anchor: Picture 2

Original: [insertion; no original text removed]

Replacement: FedAvg federation-wide recall effects: CTK 11.96 points, pooling 1.51, total 13.46; CTK and total intervals exclude zero, while pooling spans zero.

**Operation 26.3 — image_alt**

Anchor: Picture 3

Original: [insertion; no original text removed]

Replacement: Across six learners, average unseen recall exceeds the average of each seed's lowest client recall; rankings differ between these summaries.

**Operation 26.4 — image_alt**

Anchor: Picture 4

Original: [insertion; no original text removed]

Replacement: Family recall across four exposure conditions: complementary gains are largest for revmob and leadbolt, while dowgin gains chiefly through pooling and gappusin and hiddad retain low recall.

**Operation 26.5 — image_alt**

Anchor: Picture 5

Original: [insertion; no original text removed]

Replacement: In the prospective exact-dose study, mean family-macro CTK rises from 10 to 200 peer examples for FedAvg and centralized learning; error bars show seed-bootstrap intervals.

**Operation 20 — image_legend**

Anchor: word/media/image3.png

Original: 35f65d06a96db0aa9ff3d6b502f03f481b573cf0f72f0a951cfb6d01fb621eaf

Replacement: 4ef537ca4ab5e24be9aa4cfdbb89a6024979c9c880a11ac708311d175e3ac083

</details>


### Exact bibliography completion record

The five operations below follow the initial 34. Original text is empty because each operation inserts one paragraph immediately after its exact anchor; no existing paragraph is replaced. APA italic spans are identified explicitly.

**Operation 35 — insert reference**

Anchor: Feng, C., Huertas Celdrán, A., Sánchez Sánchez, P. M., Kreischer, J., von der Assen, J., Bovet, G., Martínez Pérez, G., & Stiller, B. (2025). CyberForce: A federated reinforcement learning framework for malware mitigation. IEEE Transactions on Dependable and Secure Computing, 22(4), 4398–4411. https://doi.org/10.1109/TDSC.2025.3547005

Original: [insertion; no original text removed]

Replacement: Gálvez, R., Moonsamy, V., & Diaz, C. (2021). Less is more: A privacy-respecting Android malware classifier using federated learning. Proceedings on Privacy Enhancing Technologies, 2021(4), 96–116. https://doi.org/10.2478/popets-2021-0062

Italic span: Proceedings on Privacy Enhancing Technologies, 2021

Functional DOI target: https://doi.org/10.2478/popets-2021-0062

**Operation 36 — insert reference**

Anchor: Ongun, T., Boboila, S., Oprea, A., Eliassi-Rad, T., Hiser, J., & Davidson, J. (2025). CELEST: Federated learning for globally coordinated threat detection. IEEE Transactions on Information Forensics and Security, 20, 10434–10448. https://doi.org/10.1109/TIFS.2025.3614442

Original: [insertion; no original text removed]

Replacement: Patel, A., Tomar, D. S., Pateriya, R. K., & Haripriya, R. (2026). FL-MalDrift: A federated learning framework for malware detection under local concept drift. Scientific Reports, 16, Article 1821. https://doi.org/10.1038/s41598-025-31592-z

Italic span: Scientific Reports, 16

Functional DOI target: https://doi.org/10.1038/s41598-025-31592-z

**Operation 37 — insert reference**

Anchor: Pendlebury, F., Pierazzi, F., Jordaney, R., Kinder, J., & Cavallaro, L. (2019). TESSERACT: Eliminating experimental bias in malware classification across space and time. In 28th USENIX Security Symposium (pp. 729–746). USENIX Association. https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury

Original: [insertion; no original text removed]

Replacement: Popoola, S. I., Ande, R., Adebisi, B., Gui, G., Hammoudeh, M., & Jogunola, O. (2022). Federated deep learning for zero-day botnet attack detection in IoT-edge devices. IEEE Internet of Things Journal, 9(5), 3930–3944. https://doi.org/10.1109/JIOT.2021.3100755

Italic span: IEEE Internet of Things Journal, 9

Functional DOI target: https://doi.org/10.1109/JIOT.2021.3100755

**Operation 38 — insert reference**

Anchor: Sebastián, S., & Caballero, J. (2020). AVClass2: Massive malware tag extraction from AV labels. In Annual Computer Security Applications Conference (pp. 42–53). ACM. https://doi.org/10.1145/3427228.3427261

Original: [insertion; no original text removed]

Replacement: Shao, X., Otani, A., Yamakawa, K., Hirasuka, Y., & Wai Shiang, C. (2026). Objective mismatch in federated learning under missing class support. IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences. Advance online publication. https://doi.org/10.1587/transfun.2026EAP1060

Italic span: IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences

Functional DOI target: https://doi.org/10.1587/transfun.2026EAP1060

**Operation 39 — insert reference**

Anchor: Shao, X., Otani, A., Yamakawa, K., Hirasuka, Y., & Wai Shiang, C. (2026). Objective mismatch in federated learning under missing class support. IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences. Advance online publication. https://doi.org/10.1587/transfun.2026EAP1060

Original: [insertion; no original text removed]

Replacement: Shen, J., Yang, W., Chu, Z., Fan, J., Niyato, D., & Lam, K.-Y. (2024). Effective intrusion detection in heterogeneous Internet-of-Things networks via ensemble knowledge distillation-based federated learning. In ICC 2024 – IEEE International Conference on Communications (pp. 2034–2039). IEEE. https://doi.org/10.1109/ICC51166.2024.10622262

Italic span: ICC 2024 – IEEE International Conference on Communications

Functional DOI target: https://doi.org/10.1109/ICC51166.2024.10622262

