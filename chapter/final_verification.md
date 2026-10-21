# CTK-Android final verification

Verified 21 October 2026. Final manuscript: `chapter/CTK-Android_Chapter.docx`. The timestamped filename in the request was absent; the sole DOCX was the established canonical master, with starting SHA-256 `f0ae560c2b1be2e2d0309cefc2ad3f60911082cac60bb642e869ef06a544b2d4`. This pass preserves that filename and introduces no competing manuscript or duplicate TIFFs. This report describes the current final state; earlier revision reports describe their respective earlier states.

## Validation and counts

**PASS:** the final DOCX opens in Microsoft Word, contains five editable tables, five figures, three editable equations, 21 references, and ten key-term definitions. Word exports it correctly as a 45-page PDF.

| Count | Final |
|---|---:|
| Microsoft Word complete manuscript | 10,779 |
| Reproducible complete manuscript | 10,734 |
| Reproducible count excluding References section | 10,022 |
| References section, including heading | 712 |
| Abstract, excluding heading | 148 reproducible / 149 Word |

The manuscript exceeds 10,000 words. The prompt's approximate 11,234 was not used. The reproducible total decreased by only 23 words in this pass.

Counting enumerates each Word paragraph under the document body, including table cells and text boxes, exactly once; concatenates its own text/math text; treats tabs and line breaks as spaces; and counts non-whitespace sequences. It includes front matter, headings, tables, captions, equations, references, and definitions. It excludes repeated page headers, properties, alt text, field instructions, and raster figure labels. There are no footnote/endnote/comment parts. Word's own statistics provide the independent cross-check; different tokenization accounts for the small discrepancy.

## Applied corrections — two paragraphs only

1. **Abstract, page 1:** the generic-pooling sentence now reads: “Generic pooling, a residual contrast between training procedures, contributes 1.51 points, with uncertainty spanning zero.” This addresses possible interpretation as an isolated data-volume effect while keeping the abstract within 100–150 words.
2. **Primary Controlled-Exposure Results, pages 23–24, paragraph immediately after Figure 2:** replaced the repeated effect/interval/significance recital with: “Table 3 and Figure 2 show a positive CTK effect and total gain in all ten confirmatory seeds, whereas generic pooling remains compatible with either a modest benefit or harm.” The rest of the paragraph is unchanged: it retains the 13.47-versus-13.46 rounding explanation, approximately 2,073 of 24,000 differing fitted examples, and the complete controlled-exposure interpretation. All primary estimates, intervals, adjusted significance values, and seed counts remain in Table 3 and Figure 2.

**Verified and left unchanged:** page 9 already distinguishes pooling's optimization schedules and residual interpretation. CTK's definition, replacement composition, simultaneous family interventions, and arm-specific calibration are explained adequately. No general rewrite, broad shortening, new section, bibliography change, or aesthetic layout change was performed.

## Reference audit

All 21 entries were checked for authors/order, title, year/status, venue, available volume/issue/pages/article identifier, DOI or stable URL, APA formatting, citation matching, and support for adjacent claims. Sources included current official pages, the same-day Crossref records, and accessible original papers retained in the verification workspace. **No bibliographic correction was justified; all entries were retained unchanged.** All 21 have corresponding in-text citations.

| Reference | Evidence checked; supported use |
|---|---|
| Allix et al. (2016) | [ACM DOI](https://doi.org/10.1145/2901739.2903508), original paper; AndroZoo collection/metadata, pp. 468–471. |
| Arp et al. (2014) | [NDSS record](https://doi.org/10.14722/ndss.2014.23247), original paper; Drebin static features and explainability. |
| Arp et al. (2022) | [USENIX](https://www.usenix.org/conference/usenixsecurity22/presentation/arp); evaluation pitfalls, pp. 3971–3988. |
| Augello et al. (2025) | [M2FD publisher page](https://www.sciencedirect.com/science/article/pii/S0167404825000501), Crossref; correct three authors, Computers & Security 152, article 104361. Abstract supports drift detection/selective retraining on KronoDroid; no stronger claim made. |
| Ciaramella et al. (2026) | [Publisher DOI](https://doi.org/10.1016/j.infsof.2025.107892), original paper; application-code images/CNN comparison; volume 189, article 107892. |
| Feng et al. (2025) | [IEEE DOI](https://doi.org/10.1109/TDSC.2025.3547005), original text; CyberForce missing-client experiments, including all-clients-missing; 22(4), 4398–4411. |
| Gálvez et al. (2021) | [PoPETs](https://doi.org/10.2478/popets-2021-0062), original paper; privacy-respecting Android FL; 2021(4), 96–116. |
| Haque et al. (2026) | [Author project bibliography](https://iqsec-lab.github.io/LAMDA/), original manuscript; LAMDA title/authors and ICLR 2026 status. OpenReview requires a challenge. |
| Holm (1979) | [JSTOR issue record](https://www.jstor.org/stable/i412579); multiplicity procedure, 6(2), 65–70. |
| Kamol et al. (2026) | [arXiv](https://arxiv.org/abs/2605.06894); McNdroid aligned modalities; correctly identified as a preprint. |
| Li et al. (2020) | [MLSys](https://proceedings.mlsys.org/paper_files/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html), original paper; FedProx; volume 2, 429–450. |
| Mariconti et al. (2017) | [NDSS](https://doi.org/10.14722/ndss.2017.23353), original paper; MaMaDroid API abstractions and Markov models. |
| McMahan et al. (2017) | [PMLR](https://proceedings.mlr.press/v54/mcmahan17a.html); FedAvg; volume 54, 1273–1282. |
| Ongun et al. (2025) | [IEEE DOI](https://doi.org/10.1109/TIFS.2025.3614442), original text; CELEST missing-threat collaboration; volume 20, 10434–10448. |
| Patel et al. (2026) | [Publisher](https://www.nature.com/articles/s41598-025-31592-z), final PDF; local drift. Final volume 16, article 1821 uses 2026 despite 2025 online publication. |
| Pendlebury et al. (2019) | [USENIX](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury); spatial/temporal evaluation bias; pp. 729–746. |
| Popoola et al. (2022) | [IEEE DOI](https://doi.org/10.1109/JIOT.2021.3100755), original paper; unseen botnet detection; 9(5), 3930–3944. |
| Prasad and Kumar (2026) | [Droidware publisher page](https://www.sciencedirect.com/science/article/pii/S0952197626019226), Crossref; correct author order, volume 181, article 115638. Accessible abstract supports static features, authenticated updates, anomaly filtering, and robust aggregation. No comparative accuracy claim introduced. |
| Sebastián and Caballero (2020) | [ACM DOI](https://doi.org/10.1145/3427228.3427261), original paper; AVClass2 taxonomy/tag extraction; pp. 42–53. |
| Shao et al. (2026) | [J-STAGE/IEICE](https://doi.org/10.1587/transfun.2026EAP1060), advance PDF; missing-class bias. Advance-online status and original author byline preserved; no invented pagination. |
| Shen et al. (2024) | [IEEE DOI](https://doi.org/10.1109/ICC51166.2024.10622262), original paper; missing attack classes and distillation; pp. 2034–2039. |

All DOI identifiers resolve to the expected publisher destinations. Direct content access sometimes returned publisher anti-bot responses; Elsevier redirects were checked separately after a local certificate-chain error. These access limits are distinct from identifier validity. Publisher/Crossref metadata and accessible original text supply verification; resolution alone was not treated as proof of bibliographic accuracy. No claim of unrestricted full-text access is made.

## Figures, equations, and pages

Existing `chapter/figures_tif/Figure_1.tif` through `Figure_5.tif` were verified, **not regenerated**. All are grayscale LZW TIFFs, under 0.2 MB, losslessly pixel-equivalent to the final embedded images. At their 6.5-inch manuscript width:

| Figure | Native pixels | Effective DPI |
|---|---:|---:|
| 1 | 2111 × 1220 | 324.8 |
| 2 | 2353 × 1131 | 362.0 |
| 3 | 2722 × 1285 | 418.8 |
| 4 | 2555 × 1326 | 393.1 |
| 5 | 2433 × 1377 | 374.3 |

All captions/callouts remain sequential. Figures appear on pages 14, 23, 27, 28, and 30. Figure 2 agrees with Table 3; Figure 3 distinguishes mean from within-seed worst-client recall without implying confidence intervals. Figure 4's 28 one-decimal percentage labels match the frozen full-precision `family-level.csv` values; the color scale remains in proportions. Figure 5 retains exact effective dose, uncertainty intervals, and the practical-threshold distinction. Grayscale labels, axes, legends, geometry, and placement were visually checked; no visual change was needed.

The three equations on page 8 retain the exact identities CTK = peer present − absent everywhere, pooling = absent everywhere − local, and total = CTK + pooling. Their OMML objects are byte-identical; Word and exported-PDF rendering are correct. No rasterization occurred.

All 45 final pages were rendered with Word and Poppler. Pages 1 and 23–26 were directly reviewed after reflow. The other 40 pages are pixel-identical to the pages already visually reviewed in this conversation; that comparison confirms their complete visual preservation. Equations and all five figures were also directly rechecked in the current render. No clipped text, detached caption, split table, orphan heading, malformed symbol, unexpected blank page, or new layout defect was found. All external link relationships are intact.

## Scientific preservation

The final consistency review retains +11.96 CTK [9.15, 15.21], +1.51 pooling [−4.15, 6.10], +13.46 total [8.82, 17.04], own-domain total +3.26 [1.26, 5.63], known-family −3.61 [−4.50, −2.85], replication +5.08 [2.28, 7.10], new-family +3.47 [2.45, 4.45], placebo −0.54 [−1.36, 0.20], and CTK-minus-placebo +10.04 [8.35, 12.28] points, with the original population and evidence-class distinctions. Rounding is explicitly explained.

Exact-dose means and intervals, primary/replication differences, FPR qualifications, adverse family cases, learner tradeoffs, representation losses and uncertain improvements, and the weakened stable-eligibility novelty association remain unchanged. Constructed domains are not represented as independent organizations; grouped partitions are not represented as chronological deployment. No privacy guarantee, poisoning resilience, universal dose, or operational validation is asserted. Confirmatory, prespecified sensitivity, post-confirmatory, and prospective evidence remain distinct.

Only two paragraph objects differ from the starting DOCX. Every table, equation, figure, reference, other paragraph, style, and author-metadata object is unchanged. File hashes verify preservation of existing source, configuration, results, scripts, tests, and other chapter files. No algorithms, datasets, experiments, numerical results, or analyses were changed or newly run. No Git commit was made.

## IGI compliance and genuine remaining issues

Current sources: [writing guide](https://www.igi-global.com/publish/contributor-resources/before-you-write/), [edited-book checklist](https://www.igi-global.com/publish/contributor-resources/edited-book-author-checklist/), [editorial policy](https://www.igi-global.com/publish/contributor-resources/book-editorial-policy/), [image guide](https://www.igi-global.com/publish/contributor-resources/image-guide/).

| Requirement | Status and evidence |
|---|---|
| English Word manuscript; ≥10,000 words including references | PASS — native Word and reproducible counts; format-specific checklist used over the general 8,000-word guidance. |
| Abstract 100–150 words, third person | PASS — 148 reproducible / 149 Word. |
| Main title ≤100 characters; subtitle ≤50; title case | PASS — 69 and 27 characters. |
| Heading hierarchy, APA references/citations, document structure | PASS — existing Level 1/2 hierarchy, hanging indents, italics, author–date citations; no correction necessary. |
| At least seven original definitions after References | PASS — ten; no unnecessary Additional Reading section. |
| Sequential tables/figures, captions and callouts | PASS — five each, genuine Word tables, all referenced. |
| TIFF, ≥300 effective DPI, grayscale clarity, maximum 100 MB | PASS — verified existing files and actual print dimensions above. |
| Correct editable equations | PASS — exact identities and rendering preserved. |
| MathType format | UNRESOLVED — checklist requires MathType, while general guide allows directly typed Word equations. Applicable checklist takes priority. Compatible MathType installation/conversion is unavailable; editable OMML retained as instructed. |
| Specific book scope/call conditions | PARTLY VERIFIED — chapter fits the supplied mobile-security/Android/FL scope; [call 10325](https://www.igi-global.com/publish/call-for-papers/call-details/10325) remains inaccessible, so independent verification of call-specific conditions is unavailable. |
| Publisher AI disclosure | NOT MET — omitted under the author's explicit instruction. The writing guide requires a tool/use statement before References; no statement was inserted. |
| Originality, permissions, author forms/bios, submission stage, professional copyediting-provider requirement | UNVERIFIED — these require author/editor evidence or submission-system completion; no unsupported declaration was added. Author details were preserved. |

Final DOCX SHA-256: `c0a666dd735323db015d7e7aeb63ff691f544cab35e131c58639177caf5fef64`.

The requested surgical correction and verification pass is complete. The remaining submission issues are explicitly recorded above; full publisher compliance is not claimed.
