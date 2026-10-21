# CTK-Android revision and verification report

Verified 21 October 2026. Canonical manuscript: `CTK-Android_Chapter.docx`. The repository already established this filename; no competing `_Final` document was created. The requested `(9)` file was absent. The starting master included earlier scientific and bibliography corrections, which were retained. A pre-existing original backup remains outside the repository; the exact starting master was also retained in the temporary verification workspace.

## Length and structure

| Measure | Starting master | Final |
|---|---:|---:|
| Complete manuscript, reproducible count | 12,830 | 10,757 |
| Excluding References section | 12,169 | 10,045 |
| References section, including heading | 661 | 712 |
| Native Microsoft Word count | 12,882 | 10,804 |
| Native Word pages | 52 | 45 |
| Tables / figures / editable equations | 5 / 5 / 3 | 5 / 5 / 3 |
| Bibliographic entries | 19 | 21 |
| Key-term definitions | 10 | 10 |

The reproducible reduction is 2,073 words (16.2%). Both counting methods meet the preferred 10,700–10,900 range and exceed the applicable 10,000-word minimum. Substantive sections from Introduction through Conclusion contain 9,615 words, including their headings, tables, and captions. The unchanged abstract has 142 words, excluding its heading.

| Section, including headings and associated tables/captions | Before | After | Change |
|---|---:|---:|---:|
| Front matter | 58 | 58 | 0 |
| Abstract | 143 | 143 | 0 |
| Introduction | 809 | 519 | −290 |
| Background and Related Work | 1,307 | 1,062 | −245 |
| Research Problem and Questions | 507 | 434 | −73 |
| Controlled-Exposure Study Design | 1,833 | 1,641 | −192 |
| Learning and Evaluation Protocol | 1,666 | 1,539 | −127 |
| Experimental Results | 3,503 | 2,945 | −558 |
| Discussion and Practical Implications | 1,061 | 764 | −297 |
| Threats to Validity | 706 | 504 | −202 |
| Conclusion | 347 | 207 | −140 |
| References | 661 | 712 | +51 |
| Key Terms and Definitions | 229 | 229 | 0 |

**Counting rule:** Unzip the DOCX and enumerate every `w:p` under the document body, including table cells and text boxes. For each paragraph, concatenate its own `w:t` and `m:t` contents in order, replace tab/line-break elements with spaces, and count non-whitespace sequences using `\S+`. Exclude descendants belonging to another paragraph to prevent nested-container duplication. Group by Heading1; recognize the original unheaded Introduction by its first paragraph. Include title, author block, headings, equations, tables, captions, references, and definitions. Exclude repeated page headers/numbers, XML instructions/properties, alt text, and rasterized figure labels. No footnote/endnote/comment parts were present. Native Word independently opened and repaginated both files and supplied its own word statistics; tokenization explains the small count difference.

## Applied revision

Added the Introduction heading, tightened the opening and three-condition explanation, and made the controlled empirical contribution explicit. Condensed repeated distinctions across related work while retaining CELEST and CyberForce as precedents. Added two verified sources with limited, relevant claims.

Revised 54 existing paragraphs. Consolidated explanations of composition changes, calibration, constructed domains, grouped partitions, finite full-exposure references, and optimization differences. Preserved the four research questions, metric denominators, eligibility rules, training settings, inference procedures, evidence classes, and execution provenance. Retained useful methodological detail where a larger cut would impair reproducibility.

Shortened Results primarily by removing repeated narration of displayed values. Discussion now develops the interpretation and operational tradeoffs without reproducing the results catalogue. Threats and Conclusion were tightened while retaining adverse findings and limits. Conclusion body: 206 words. Figure 4 now displays validated recall percentages to one decimal place; its caption distinguishes percentage labels from the unchanged proportion color scale.

Kept table rows, titles, and complete notes together; repaired a split table note and sparse end-of-conclusion pagination. Preserved existing styles and the full author block, including order, affiliations, correspondence, and ORCID. No disclosure statement appears, following the author's explicit instruction.

## References

All 19 existing entries were checked against DOI registration, publisher/proceedings records, accessible original papers, or author-hosted records; all remain cited. Author order, title, year/status, venue, volume/issue, pagination or article ID, and identifiers were reviewed. No existing source was removed or replaced. The reference list is alphabetical; all 21 entries have corresponding text citations.

| Reference | Verification source and outcome |
|---|---|
| Allix et al. (2016), AndroZoo | [ACM DOI](https://doi.org/10.1145/2901739.2903508), original paper; pp. 468–471. |
| Arp et al. (2014), Drebin | [NDSS DOI](https://doi.org/10.14722/ndss.2014.23247), original paper; retained. |
| Arp et al. (2022), Dos and don'ts | [USENIX record](https://www.usenix.org/conference/usenixsecurity22/presentation/arp); author order and pp. 3971–3988 confirmed. |
| Ciaramella et al. (2026) | [Publisher DOI](https://doi.org/10.1016/j.infsof.2025.107892), version of record; volume 189, article 107892. |
| Feng et al. (2025), CyberForce | [IEEE DOI](https://doi.org/10.1109/TDSC.2025.3547005), original text; 22(4), 4398–4411. Compound author names preserved. |
| Gálvez et al. (2021) | [PoPETs DOI](https://doi.org/10.2478/popets-2021-0062), original paper; 2021(4), 96–116. |
| Haque et al. (2026), LAMDA | [Author project](https://iqsec-lab.github.io/LAMDA/) confirms ICLR 2026 and author order; local paper supports dataset claims. OpenReview access was restricted. |
| Holm (1979) | [JSTOR issue](https://www.jstor.org/stable/i412579) confirms author, title, 6(2), 65–70. Stable article link retained. |
| Kamol et al. (2026), McNdroid | [arXiv original](https://arxiv.org/abs/2605.06894); retained explicitly as a preprint. |
| Li et al. (2020), FedProx | [MLSys proceedings](https://proceedings.mlsys.org/paper/2020/hash/1f5fe83998a09396ebe6477d9475ba0c-Abstract.html), original paper; volume 2, 429–450. |
| Mariconti et al. (2017), MaMaDroid | [NDSS DOI](https://doi.org/10.14722/ndss.2017.23353), original paper; retained. |
| McMahan et al. (2017), FedAvg | [PMLR record](https://proceedings.mlr.press/v54/mcmahan17a.html); volume 54, 1273–1282. |
| Ongun et al. (2025), CELEST | [IEEE DOI](https://doi.org/10.1109/TIFS.2025.3614442), original text; volume 20, 10434–10448. |
| Patel et al. (2026), FL-MalDrift | [Publisher PDF](https://www.nature.com/articles/s41598-025-31592-z.pdf); final volume 16, article 1821 supports 2026 despite earlier online publication. |
| Pendlebury et al. (2019), TESSERACT | [USENIX record](https://www.usenix.org/conference/usenixsecurity19/presentation/pendlebury), original paper; 729–746. |
| Popoola et al. (2022) | [IEEE DOI](https://doi.org/10.1109/JIOT.2021.3100755), original paper; 9(5), 3930–3944. |
| Sebastián and Caballero (2020), AVClass2 | [ACM DOI](https://doi.org/10.1145/3427228.3427261), original paper; 42–53. |
| Shao et al. (2026) | [IEICE DOI](https://doi.org/10.1587/transfun.2026EAP1060), advance-publication PDF; advance online status retained without invented volume/pages. |
| Shen et al. (2024) | [IEEE DOI](https://doi.org/10.1109/ICC51166.2024.10622262), original paper; 2034–2039. |
| **Added: Augello et al. (2025), M2FD** | [Publisher DOI](https://doi.org/10.1016/j.cose.2025.104361); Computers & Security 152, article 104361. Accessible abstract supports drift monitoring and selective retraining on KronoDroid. Full-text retrieval was restricted; no stronger claim added. |
| **Added: Prasad and Kumar (2026), Droidware** | [Publisher DOI](https://doi.org/10.1016/j.engappai.2026.115638); Engineering Applications of Artificial Intelligence 181, article 115638. Accessible abstract/introduction supports the stated security mechanisms; no performance comparison inferred. |

**Evaluated, not added:** Zheng et al., [TIF](https://doi.org/10.1109/TSE.2026.3698484), IEEE TSE 52(8), 2463–2474 (2026). DOI metadata and the [original manuscript](https://arxiv.org/html/2502.05098v2) establish temporal-invariance learning using proxy environments and invariant representations. Its temporal-drift contribution is relevant but less directly connected to the matched-exposure question; existing drift/evaluation sources and M2FD supply sufficient context. No new bibliography entry was necessary. No bibliographic discrepancy remains knowingly unresolved; full-text access limits are stated above.

## Scientific checks

Read-only checks against frozen result tables support CTK 11.955756 points, pooling 1.505125, and total 13.460881. Their unrounded identity holds; the manuscript explicitly explains why displayed 11.96 + 1.51 yields 13.47 rather than 13.46. The 9.15–15.21 CTK interval, exact/adjusted tests, and seed counts remain intact.

Checks also support own-domain total +3.26, pooling −7.60, known-family −3.61, AUROC −0.01166, average precision −0.02011, and disjoint-family CTK +5.08. The 18 new-family seed vector was independently matched to the earlier verified vector: mean +3.46656, saved BCa interval 2.45249–4.44852, 10/10 positive; 14 overlapping families average +10.666. The interval was checked against saved verification, not regenerated as a new analysis.

Wrong-family placebo −0.54 and CTK-minus-placebo +10.04 remain reported. Exact-dose means 2.92, 4.90, 7.83, 12.48, and 14.49 retain their intervals and non-universal dose interpretation. Negative replication/expanded families, low absolute hiddad/gappusin recall, report-JSON losses, uncertain call-graph full-exposure improvement, and realized-FPR deviations remain visible. The novelty association weakens from .408 to .294 under stable eligibility, with the latter interval crossing zero. The original and later seed blocks remain distinct.

The final critical-review pass checked the contribution against existing missing-threat work, the full fitted/calibrated intervention, matched volume versus changed composition, optimization confounding in pooling, distinct evaluation populations, inference scope, and restricted external validity. No editorially resolvable contradiction was found after correction. Independent organizations, chronological deployment, formal privacy, adversarial resilience, and universal dose thresholds are not claimed.

All five table texts are identical to the starting master; all three equation XML objects are identical. Only document text/layout, two hyperlink relationships, and Figure 4's annotations changed inside the DOCX. All other package parts are byte-identical. SHA-256 checks covered 376 existing files in source, configuration, results, scripts, tests, and chapter directories: only the authorized canonical manuscript changed. Pre-existing changes were preserved. No datasets, models, configurations, scripts, or experimental results were written; no training, experiments, or Git commit occurred.

## Publisher and production checks

Official sources checked: [writing guide](https://www.igi-global.com/publish/contributor-resources/before-you-write/), [edited-book checklist](https://www.igi-global.com/publish/contributor-resources/edited-book-author-checklist/), [editorial policy](https://www.igi-global.com/publish/contributor-resources/book-editorial-policy/), and [image guide](https://www.igi-global.com/publish/contributor-resources/image-guide/). The format-specific checklist supplies the 10,000-word threshold and MathType requirement where the general guide differs.

| Requirement | Status | Evidence / limitation |
|---|---|---|
| English DOCX; minimum 10,000 words | PASS | Native Word opens successfully; both counts exceed minimum. |
| Title ≤100 characters; subtitle ≤50; title case | PASS | 69 / 27 characters; original titles retained. |
| Third-person abstract, 100–150 words | PASS | 142 words; no first-person framing. |
| APA citation/reference and heading conventions | PASS | Alphabetical entries, author–date citations, hanging indents, appropriate italics; centered Level 1 and left-aligned Level 2 headings. |
| Sequential figures/tables, captions, callouts | PASS | Five each, numbered 1–5; all called out in prose. Genuine editable tables. |
| TIFF, grayscale, ≥300 effective DPI, <100 MB each | PASS | Five native-resolution LZW grayscale TIFFs; no upscaling. See dimensions below. |
| Accurate editable equations | PASS | Three unchanged OMML equations, visually checked. |
| MathType final-submission format | UNRESOLVED | Compatible MathType software/converter unavailable; editable Word equations retained, never rasterized. |
| At least seven original key-term definitions after References | PASS | Ten retained definitions; no unnecessary Additional Reading section. |
| Page layout and file validity | PASS | Word export and Poppler rendering; every page 1–45 visually inspected; no blank pages, clipped content, orphan headings, or split tables/notes. |
| Hyperlinks and text hygiene | PASS | Relationship integrity checked; both new DOI links survive PDF export. Zero suspicious invisible characters; deterministic cleanup changed nothing. |
| Publisher AI-use disclosure | FAIL — author instruction | Publisher requires disclosure before References. Author explicitly instructed omission. No statement was added; full compliance cannot be claimed. |
| Specific book call and any additional conditions | UNVERIFIED | [Call 10325](https://www.igi-global.com/publish/call-for-papers/call-details/10325) could not be retrieved. Android malware, federated learning, datasets, and reproducibility fit the supplied book scope; call-specific conditions remain unconfirmed. |
| Originality, permissions, author agreement, bios, submission/anonymization stage | UNVERIFIED | Requires author/editor confirmation; no unsupported declarations or submission actions performed. Existing author metadata retained as requested. |
| Checklist's professional copyediting-provider requirement | UNVERIFIED | This revision is not evidence of a separate provider's certification. |

| Submission figure | Pixels | Width in manuscript | Effective DPI |
|---|---:|---:|---:|
| `figures_tif/Figure_1.tif` | 2111 × 1220 | 6.5 in | 324.8 |
| `figures_tif/Figure_2.tif` | 2353 × 1131 | 6.5 in | 362.0 |
| `figures_tif/Figure_3.tif` | 2722 × 1285 | 6.5 in | 418.8 |
| `figures_tif/Figure_4.tif` | 2555 × 1326 | 6.5 in | 393.1 |
| `figures_tif/Figure_5.tif` | 2433 × 1377 | 6.5 in | 374.3 |

TIFF pixels were verified identical to the final embedded figures after lossless grayscale conversion. Axes, plot geometry, and legend meaning are preserved. Files are 0.06–0.16 MB. DPI above derives from pixel dimensions and actual Word extents, not the 400-DPI metadata tag. Use `figures_tif/` for submission; older `figures/` assets were preserved.

The bundled DOCX renderer could not run because LibreOffice was unavailable. Native Microsoft Word successfully supplied the PDF render instead; Poppler generated the inspected pages. Temporary scripts, reference metadata, page PNGs, PDF, counts, and validation records remain outside the repository in `C:\Users\naslo\AppData\Local\Temp\ctk-editorial`.

Final manuscript SHA-256: `f0ae560c2b1be2e2d0309cefc2ad3f60911082cac60bb642e869ef06a544b2d4`.

The manuscript revision and figure package are complete. Submission compliance remains conditional on the explicitly unresolved requirements above.
