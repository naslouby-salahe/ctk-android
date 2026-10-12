# Chapter verification

## Current revision: 12 October 2026

The revised `CTK-Android_Chapter.docx` contains **11,808 words and 49 pages**, as measured and rendered by Microsoft Word. All rendered pages were visually checked. The five tables remain editable and are kept together; table contents, three equations, and five embedded figures are unchanged. No AI-use statement was added.

The independent audit reproduced the primary means, BCa intervals, and signed-rank/Holm results from stored seed differences and verified all 215 manifest-listed artifact digests. All 257 source/result files in the protection snapshot remained unchanged. No training campaign was rerun. Tests: **497 passed and one failed** across architecture and behavioral runs. The test-isolation failure and a secondary tied-rank Wilcoxon issue are documented in [audit.md](audit.md), along with the revisions and assessment of **84/100 before revision and 90/100 afterward**. These are editorial judgments, not acceptance guarantees.

The current document supersedes the counts and no-inference-rerun statement in the historical report below. That report records the earlier preparation pass; its broader literature and file-baseline checks were not all repeated during this revision. The current audit is the authoritative account of this revision's scope and remaining issues.

## Historical verification: 11 October 2026

Verified 11 October 2026.

- Manuscript: `CTK-Android_Chapter.docx`; Microsoft Word reports **11,949 words**, including references, captions, table text, and definitions; **49 rendered pages**. Text inside raster figures is not relied upon for the minimum.
- Contents: **5 figures, 5 editable tables, 3 editable equations, 14 references, and 10 key terms**. Abstract: **128 words**. Title/subtitle: **69/27 characters**. No disclosure section, placeholder, or comment was inserted, as instructed.

## Requirements checked

The [book-specific call](https://www.igi-global.com/publish/call-for-papers/call-details/10325) requires at least 10,000 words, including references and related reading. The manuscript exceeds that minimum. The [manuscript instructions](https://www.igi-global.com/publish/contributor-resources/before-you-write/), [image guide](https://www.igi-global.com/publish/contributor-resources/image-guide/), and [citation instructions](https://www.igi-global.com/publish/contributor-resources/apa-citation-guidelines/) were consulted directly. The document uses English, APA-style unnumbered headings, double-spaced 12-point Times New Roman body text, one-inch margins, numbered captions and prose callouts, hanging reference indents, and definitions after references. Optional additional reading was omitted. The 17-item Books checklist was reviewed separately from the Journals checklist: this is a research chapter, so no whole-book front matter or case-study teaching notes are required. Abstract, references, and key terms have appropriate page breaks. Title and subtitle remain below the 100/50-character limits. Originality, revised-publication restrictions, copyright agreements, review service, and final proof approval depend on author/editor actions; these are not certified by document formatting.

## Scientific and numerical audit

Methods were checked against frozen configurations and implementation; reported numbers were checked against machine-readable result tables rather than superseded narrative documents. Primary FedAvg CTK is **11.96 percentage points**, 95% BCa interval **9.15–15.21**, Holm-adjusted p **.00586**. Pooling is **1.51**, interval **−4.15–6.10**; total gain is **13.46**, interval **8.82–17.04**. Arm means, paired contrasts, units, denominators, operating points, and evidence categories are distinguished.

The chapter retains negative pooling on the own-domain population, known-family losses, unfavorable families, the unresolved original own-domain permutation control, effective versus nominal dose, unsuccessful representation outcomes, and the weaker stable-family novelty association. It does not claim a new optimizer, formal privacy, adversarial robustness, universal dose threshold, or deployment validation. Prospective extensions are separated from original confirmatory evidence. No experiments, training, or inferential statistics were rerun.

All **215 manifest-listed artifact digests** matched. A final comparison of **1,091 existing files** against the pre-work SHA-256 baseline found **zero changes**. No commits or pushes were made. A later status check also showed an unrelated change in `proposal/build-proposal.sh`; this task did not edit that file and leaves it untouched.

## Literature and document audit

All 14 references were checked against publisher/proceedings, DOI metadata, or author-hosted primary records. Claims and novelty positioning were reviewed against the cited work; CELEST and CyberForce are explicitly credited for prior missing-threat evaluations. Every reference is cited, and every in-text author-year citation has an entry. The McNdroid reference is identified as a preprint. No official similarity-service report was obtained.

The supplied renderer failed because its required LibreOffice executable was unavailable. Installed Microsoft Word successfully exported the final DOCX to PDF; all 49 pages were rasterized and visually inspected. Corrections addressed literal heading markers, inherited title styling, split equations, reference pagination, heatmap contrast, and misencoded symbols in table/figure notes. All explicit document and style text colors are black; no highlights remain. Repetitive transitions and production commentary in captions were edited without changing numerical findings. Final checks found no clipped content, orphaned headings, broken tables, unresolved drafting markers, comments, or missing figure callouts. The deterministic prose Unicode audit found zero suspicious characters.

All five final TIFFs are grayscale, losslessly compressed, and tagged at **400 dpi**. Widths are 2,111–2,722 pixels, providing at least 324 dpi at the manuscript's 6.5-inch display width. Figures were prepared from frozen table values without recomputing findings; the exposure schematic describes the implemented design.


### Reference-by-reference recheck

Authors, year, title, venue, and available volume/pages or article numbers were matched to primary publication records. All eight DOI identifiers returned registered DOI handles for the intended work. The other six entries retain authoritative source URLs; no DOI was invented or borrowed from a different version.

| Reference | Verified DOI or authoritative record |
|---|---|
| Allix et al. (2016), AndroZoo | 10.1145/2901739.2903508; ACM, pp. 468–471 |
| Arp et al. (2022), Dos and don'ts | USENIX Security 22 official proceedings, pp. 3971–3988; no DOI in publisher citation |
| Arp et al. (2014), Drebin | 10.14722/ndss.2014.23247; NDSS paper and DOI record |
| Ciaramella et al. (2026) | 10.1016/j.infsof.2025.107892; volume 189, article 107892; publication year 2026 |
| Feng et al. (2025), CyberForce | 10.1109/TDSC.2025.3547005; 22(4), 4398–4411 |
| Haque et al. (2026), LAMDA | Author-hosted ICLR 2026 BibTeX and OpenReview identifier; conference-proceedings formatting corrected |
| Holm (1979) | Scandinavian Journal of Statistics 6(2), 65–70; JSTOR stable 4615733; purported 10.2307/4615733 is unregistered and was not added |
| Kamol et al. (2026), McNdroid | 10.48550/arXiv.2605.06894; explicitly identified as a preprint |
| Li et al. (2020), FedProx | Official MLSys BibTeX, volume 2, 429–450; editors and proceedings formatting corrected |
| Mariconti et al. (2017), MaMaDroid | 10.14722/ndss.2017.23353; NDSS paper and DOI record |
| McMahan et al. (2017), FedAvg | Official PMLR proceedings, volume 54, 1273–1282; final proceedings URL retained |
| Ongun et al. (2025), CELEST | 10.1109/TIFS.2025.3614442; volume 20, 10434–10448 |
| Pendlebury et al. (2019), TESSERACT | Official USENIX paper, 729–746; proceedings URL retained |
| Sebastián and Caballero (2020), AVClass2 | 10.1145/3427228.3427261; ACM, 42–53 |

## External matters

The author will handle the publisher's disclosure requirement separately, as explicitly requested. Publisher acceptance under its AI-generation policy is **not certified**. Independent professional copyediting, official similarity screening, authorship/originality and rights declarations, and submission-system acceptance were not performed or independently verified. No submission was made. These matters do not represent completed checks.

Temporary cleanup exception: automatic approval review blocked removal of the verified task-specific temporary directory, C:\Users\naslo\AppData\Local\Temp\ctk-chapter-work. Build scripts, render images/PDF, source-check downloads, and temporary dependencies remain there; they are outside the repository. The chapter directory contains only the seven final deliverable files.
