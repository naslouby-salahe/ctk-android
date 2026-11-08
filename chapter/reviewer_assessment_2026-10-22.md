# Reviewer assessment of CTK Android

Reviewed 22 October 2026. Source: `chapter/CTK-Android_Chapter.docx`.

## Scope and overall assessment

I read the complete manuscript and inspected a fresh 45-page Microsoft Word PDF export. I surveyed the layout of every page and inspected all five figures and the main methods/results tables at larger scale. This is an editorial and presentation review, with methodological questions based on the manuscript. It is not a new experiment audit or an independent verification of the cited literature. The manuscript has not been changed.

The work has a clear empirical contribution: the absence-everywhere comparison helps separate the contribution of selected peer-held families from the remaining local-to-collaborative difference. The negative controls, exact-dose experiment, adverse family results, and distinction between own-domain and federation-wide evaluation strengthen the account. The paper also reports uncertainty and limitations unusually explicitly.

My recommendation is a focused revision before submission. The largest problem is that the manuscript often reads like a record of how earlier criticisms were resolved. Repeated qualifications, protocol-status language, and numerous metric names compete with the scientific argument. Strengthening it means making the reader's route through the evidence simpler while retaining the substantive qualifications.

Wording cannot establish AI authorship. The relevant editorial issue is formulaic or overprocessed prose. A deterministic scan of the extracted manuscript text found zero suspicious invisible/format characters under the tool's rules; that result says nothing about authorship or statistical watermarking.

## Highest priority revisions

### 1. Make the main result and its practical limitation equally visible

Locations: abstract, pp. 1 and 22–25; Discussion, pp. 35–36; Conclusion, p. 40.

The headline +11.96 points is the peer-present versus absence-everywhere effect on federation-wide unseen recall. The +3.26-point result is the peer-present versus local effect on own-domain unseen recall. These differ in both comparison and evaluation population. The abstract states both, but a reader can still mistake the first for the improvement experienced by a participating client.

Recommended presentation: give both full decompositions together, with the population stated in each row or panel:

| Evaluation population | CTK (pp) | Residual collaboration effect (pp) | Total versus local (pp) |
|---|---:|---:|---:|
| Federation-wide unseen malware | +11.96 | +1.51 | +13.46 |
| Own-domain unseen malware | +10.85 | −7.60 | +3.26 |

Use the existing paired intervals in the final display. Explain once that separately rounded components can differ from the rounded total by 0.01 point. The own-domain row is secondary evidence and must remain identified as such.

A useful interpretation sentence is: “For own-domain unseen malware, the 10.85-point exposure effect offsets a 7.60-point loss in the absence-everywhere condition, leaving a 3.26-point gain over local learning.”

Do not subtract the 3.61-point nonhidden-malware loss from the 3.26-point unseen-malware gain: they have different denominators and cannot be combined into a net detection effect without population weights.

### 2. Align the names of the measures with what they measure

Locations: pp. 8–9, 19–20, 26, and 45.

**“Generic pooling.”** The manuscript correctly says this contrast includes different optimization schedules. The label still encourages a data-volume interpretation, particularly in the abstract and figures. Prefer “residual collaboration effect,” initially defined as the quantity called generic pooling in the protocol. Preserve the existing result identifiers if those are needed for reproducibility. “Contributes 1.51 points” also sounds more firmly beneficial than the interval supports; “is estimated at 1.51 points, with an interval spanning zero” is more precise.

**“Known-family recall.”** The methods explicitly allow the complement of hidden-family malware to include malware without an eligible family annotation. Thus “known” is not guaranteed. Prefer “nonhidden-malware recall,” with an initial cross-reference to the stored metric name. Apply the change to the abstract, Table 4, discussion, and definitions. If genuinely verified seen-family recall is desired, that requires a new calculation rather than relabeling the current result.

**“Worst client.”** In Table 4 and Figure 3, use “mean minimum-client recall” or an equally explicit short label, with the note defining the minimum within each seed. It is not a fixed client's longitudinal result and not a confidence bound.

**“Absent everywhere” versus “absence-everywhere.”** Use one form consistently for condition names. The current alternation adds small but avoidable reading friction.

### 3. Consolidate repeated qualifications

Locations: Introduction, pp. 3–4; Related Work, pp. 5–8; intervention explanation, pp. 9 and 15; Results, pp. 23–24; Discussion, pp. 35–37; Threats to Validity, pp. 38–40.

The repeated themes are legitimate: constructed clients, nonchronological splits, joint family interventions, replacement composition, separate calibration, finite full exposure, and no deployment/privacy claim. The problem is their recurrence, often in the same negative sentence pattern.

State each defining qualification where the method is introduced. Keep a short reminder beside a result only when it changes that result's interpretation. Use Threats to Validity to explain consequences and remaining uncertainty, rather than repeating the definition. Keep the distinction between evidence categories visible; compress repeated announcements that a finding is not another confirmatory discovery.

For example, the intervention qualification appears around the equations, after Figure 1, after Table 3/Figure 2, at the start of Discussion, and in Threats to Validity. The reader needs the full definition once and targeted reminders thereafter.

Do not impose a blanket shortening percentage. Existing project notes record a chapter word-count constraint; check the applicable limit before cutting. Recovered space could instead support the worked example below.

### 4. Make the study easier to understand before expanding the protocol

Locations: research questions, pp. 8–10; first design figure, p. 14; primary results begin p. 22.

The research questions are embedded in one long paragraph. Set out four concise, numbered questions and map the results subsections to them. This preserves content while making the logic scannable.

Move or briefly preview the exposure schematic near the equations. Add a short worked example based on a reported family: adwo illustrates recovery of a pooling loss, whereas revmob illustrates improvement beyond the local baseline. Explain the comparisons before introducing all the averaging schemes.

Add a compact metric guide beside the metric definitions: evaluation population, averaging unit, and the practical question each measure answers. Federation-wide client-macro, own-domain client-macro, family-macro, micro-pooled, and minimum-client summaries are difficult to retain from successive prose paragraphs alone.

### 5. Sharpen the contribution without overstating novelty

Locations: final introduction paragraph, pp. 3–4; related-work conclusion, p. 8; conclusion, p. 40.

The contribution is sometimes expressed as a broad “reproducible empirical framework.” Replace at least one occurrence with the actual design and finding:

“This study compares local learning with two collaborative conditions that differ in access to selected malware families. Matching client training budgets separates the peer-exposure effect from the remaining collaboration effect; the resulting decomposition shows when exposure adds detection capability and when it mainly repairs negative transfer.”

Preserve the existing acknowledgement of CELEST and CyberForce. The manuscript already treats them as close precedents. The revision should emphasize the specific Android, budget-matched decomposition and supporting controls, rather than imply that missing-threat collaboration is itself new.

## Visual and table review

No obvious clipping, overlapping elements, missing figure content, blank pages, or detached captions appeared in the inspected render. Tables are editable and use a consistent 10-point body size. Figures are legible in grayscale. The improvements below concern interpretation and reading effort, not a broken document.

| Location | Finding | Recommended change |
|---|---|---|
| Figure 1, p. 14 | Shows peer present, absent everywhere, and full exposure, but omits local learning, one of the three terms in the main decomposition. | Add the local reference and labeled contrasts for CTK, residual collaboration, and total gain. Visually distinguish full exposure as an additional reference. Keep the note that the drawing illustrates one pair within a joint intervention. |
| Table 3 and Figure 2, p. 23 | Repeat the same three estimates and intervals. Their order also differs: the table begins with CTK, the plot with pooling. | Keep the inferential details in the table and use the figure for paired federation-wide/own-domain panels. If both current displays remain, align the ordering. |
| Table 4, p. 26 | The short headings require the reader to reconstruct whether a column contains recall, which population it uses, and whether FPR is nominal or observed. | Use explicit headings such as “Federation-wide unseen recall,” “Own-domain unseen recall,” “Minimum-client recall,” “Nonhidden recall,” and “Realized FPR.” State percentage units in the title/header or a clear note. |
| Figure 3, p. 27 | The connected square and dot are two summaries, not an uncertainty interval. The note explains this, but a quick scan can still suggest an interval or range. “Mean across seeds” also fails to identify the client aggregation in the dot label. | Label the series “Mean client-macro recall” and “Mean minimum-client recall.” Direct labels or separate markers can make the distinction clearer. If inferential learner comparisons are important, provide paired uncertainty separately using existing results; do not reinterpret the connecting line. |
| Figure 4, p. 28 | Cells show percentages while the legend runs from 0 to 1. The note explains the conversion, but it creates unnecessary mental work. | Set the legend to 0–100 and label it “Recall (%)”. Remove the sentence explaining mixed units. Preserve the existing numerical cell values and contrast-aware text colors. |
| Figure 5, p. 30 | Clear grayscale markers, intervals, and linear dose spacing. However, only positive doses appear despite a defined zero-dose condition. | Consider showing the verified zero-dose reference and explain whether any zero interval is structural. This would make the baseline explicit. Keep the current uncertainty and avoid calling the upper end a universal saturation point. |
| Table 5, p. 32 | One uninterrupted table combines client-macro effects on original seeds with family-macro effects on extension seeds. The distinction is confined to the note. | Divide into labeled panels or row groups with metric and seed block visible. Keep the existing evidence classes. This is more important than cosmetic formatting. |
| Figure/table notes | Dense notes mix definitions, study scope, statistical qualifications, and interpretive cautions. | Keep the information needed to decode each display; move general limitations to their established location. Add a little space below table bottom rules if the publication template allows it. |

Do not reduce line spacing or margins merely to make the 45-page manuscript look shorter. Its double-spaced review format is coherent. Preserve the required submission template.

## Wording examples

These are localized editorial suggestions. They do not authorize deletion of necessary qualifications elsewhere.

| Location | Current wording | Suggested wording |
|---|---|---|
| Abstract, p. 1 | “Generic pooling, a residual contrast between training procedures, contributes 1.51 points, with uncertainty spanning zero.” | “The residual collaboration effect is estimated at 1.51 points, with a confidence interval spanning zero.” |
| Introduction, p. 3 | “The study uses completed experiments on LAMDA features linked to AndroZoo metadata.” | “The study uses LAMDA features linked to AndroZoo metadata.” |
| Related Work, p. 7 | “These broader benchmark capabilities should not be attributed to the narrower experiment reported here.” | After the specific explanation of the overlap and benchmark scope, delete this repetitive closing sentence. |
| Methods, p. 15 | “This comparison tests whether the exposure effect persists in a less absolute form of local deprivation.” | “This comparison tests whether peer exposure helps when the family is scarce locally.” |
| Results, p. 24 | “The remaining gap to a full-exposure reference shows that access to peers does not reproduce every advantage of allowing examples at the target.” | “Peer-present recall remains below the full-exposure mean under the tested training procedure.” Follow with the existing finite-reference qualification. This avoids attributing the entire difference to target access when composition also changes. |
| Results, p. 26 | “FedAvg has the highest descriptive mean of within-seed minima” | “FedAvg has the highest mean minimum-client recall.” Keep the definition in the figure/table note. |
| Figure 4 note, p. 28 | “Labels use validated underlying means” | Remove this audit-status phrase; the preceding sentence already explains the displayed means. |
| Dose results, p. 30 | “it alone meets the displayed mean effective-dose criterion of at least 100” | “Only the all-available condition averages at least 100 fitted peer examples per family.” Clarify why 100 is an analytical cutoff; it is not the three-point practical-effect threshold. The current paragraph does not identify the display it references. |
| Dose results, p. 30 | “Figure 5 presents those means and the frozen intervals.” | “Figure 5 shows the means and 95% BCa confidence intervals.” Freezing concerns the protocol; it is unnecessary as a routine adjective for reported intervals. |
| Representation results, p. 33 | “Report-JSON performs unfavorably on the same priority summary.” | “Report-JSON reduces both full-exposure recall and CTK on the priority-family summary.” Retain the numerical results that follow. |
| Representation results, p. 33 | “There is no demonstrated hiddad rescue.” | “The hiddad interval includes both a decrease and an increase in recall.” This is more precise and avoids the informal, undefined “rescue.” |
| Validity, p. 38 | “These constraints narrow interpretation without invalidating the paired comparison.” | “The paired comparison estimates the combined exposure, replacement, and calibration intervention.” This describes the estimand rather than pronouncing the analysis valid. |
| Conclusion, p. 40 | “Permutation and wrong-family placebo controls strengthen the family-specific interpretation.” | “Permutation and wrong-family placebo controls support the importance of the selected families' exposure under this intervention.” This avoids suggesting an isolated causal effect for each family. |

The style to reduce is a repeated paragraph pattern: report a finding, assert that it “supports” something, then explain what it “does not establish.” Individually, many such sentences are sound. Repetition across almost every section makes the voice mechanical. Use the concrete result as the subject and reserve interpretation for places where it advances the argument.

Do not mechanically remove technical terms, change sentence lengths for their own sake, or introduce informal language to appear less AI-written.

## Questions a skeptical scientific reviewer may still ask

These are questions to address or optional follow-up analyses, not findings that the existing experiment is invalid.

1. **Why were the three-point benefit margin and two-point loss tolerance chosen?** The chapter explains how they are used but gives little substantive justification for their sizes. State whether they were pragmatic benchmark choices or based on a particular external requirement. Do not invent an operational rationale after the fact.
2. **How much of the exposure response depends on replacement composition?** The manuscript acknowledges composition changes and reports approximately 2,073 changed examples. A class-matched replacement sensitivity could narrow interpretation if available or if additional experiments are feasible. The existing placebo is useful but does not eliminate every composition difference. This is an optional strengthening experiment, not a prerequisite for describing the current complete intervention.
3. **How transferable is the magnitude?** The disjoint-family mean of +5.08 and newly examined-family mean of +3.47 are important contextual results. Bring them into the discussion of generalization near the +11.96 headline. State their distinct metrics and evidence status; do not treat the three numbers as a directly matched trend.
4. **How does practical performance change at lower FPR?** The manuscript reports +7.85 CTK at 1% nominal FPR, but the same passage does not give an equally compact view of own-domain total gain, nonhidden recall, and realized client FPR at that operating point. If existing artifacts support it, a small supplementary operating-point table would strengthen the practical discussion without requiring a deployment claim.
5. **Can the reader distinguish prespecified decisions from later diagnostics quickly?** A short evidence map would be easier to use than repeatedly describing class A/B/C/D status in narrative. Retain seeds and protocol timing in that map or in an appendix; keep enough detail in the methods for the primary inference to be understood without external files.

## Recommended revision order

1. Correct metric terminology and make the two main decompositions visible together.
2. Repair Figure 1's missing local reference and Table 5's hidden metric change.
3. Consolidate repeated qualifications and replace the audit-like phrases listed above.
4. Make the research questions and metric definitions easier to scan.
5. Improve the figure legends and caption economy; then re-render the complete manuscript.

The most persuasive feature of the paper is its explanation of when complementary exposure adds capability and when it mainly repairs collaboration losses. Let that result organize the narrative. Preserve negative findings, uncertainty, and the narrow scope: those make the paper more credible when stated clearly and economically.
