# Audit Matrix

Status legend: PASS, PARTIAL, MISSING, BLOCKED. Updated 2026-09-25 after the EXT-REP corrected rerun (Amendment A3) and final convergence review. Each row states the evidence checked and any remaining limit.

## Tooling and architecture

| Area | Status | Evidence |
|---|---|---|
| Ruff (lint + format) | PASS | `ruff check .` and `ruff format --check .` clean after the last edit; also `tests/architecture/test_static_analysis.py` |
| Pyright strict (src + tests) | PASS | same; `pyright` reports 0 errors |
| Semgrep (project config) | PASS | `quality/semgrep.yml`, 8 rules, 0 findings on `src/` after the last edit; each rule has a regression case (`test_semgrep_rules.py`) |
| SonarQube | BLOCKED | MCP `analyze_code_snippet` returned 0 issues even on a deliberately smelly probe file, so it is not analysing; server project has no analysis of this code. Needs a scanner run or a working SonarQube for IDE connection |
| Primitive boundary / raw dict / `Any` / `object` / bare containers | PASS | `test_no_primitive_leaks.py` |
| `.value` escapes, `float()/int()/str()/cast`, type suppressions | PASS | same |
| Aliases and constrained scalars only in `types.py`; enums only in `enums.py`; no duplicate enums; no categorical literals | PASS | `test_types_and_enums.py` |
| Config: one YAML parser, YAML surface, no hidden defaults, every field consumed | PASS | `test_config_and_paths.py` |
| Path ownership (`paths.py` only; artifact names are the `Artifact` enum) | PASS | same |
| Magic numbers, dead/duplicate constants, TODO/FIXME, shims, dumping grounds, Docker, claim infra | PASS | `test_magic_values_and_hygiene.py` |
| Duplicate function bodies, wrapper-only functions/classes | PASS | same + `test_no_primitive_leaks.py` |
| CLI delegation, no scientific imports in CLI, every function reachable from the CLI | PASS | `test_wiring.py` |
| Training never reads test/calibration; thresholds only from benign calibration; reporting never trains | PASS | `test_scientific_isolation.py` |
| Real-source schema (LAMDA parquet, feature map, AndroZoo header) | PASS | `test_source_schema.py` |
| No string literal, module constant or magic number outside `enums.py` (messages are `ErrorMessage`/`DetailMessage`/`CliMessage` templates; numbers are `IntEnum`/float `Enum`) | PASS | `test_magic_values_and_hygiene.py` |
| Third-party `Literal`-typed option strings | PASS | grouped in `enums.LibraryOption` (enum members cannot satisfy `Literal[...]` parameters); documented boundary, nothing else is allowed |
| Every enum member is used by code or config; config-selectable enums are exempt | PASS | `test_types_and_enums.py`; unused members and the claim/contrast/estimand enums were removed and return with the analysis code |
| Novelty descriptors read only fit rows | PASS | `test_scientific_isolation.py` |
| Semantic aliases only: no bool, inline dict, ndarray, anonymous tuple, raw DataFrame/Series, or generic array alias in signatures/fields | PASS | `test_no_primitive_leaks.py` (14 tests); Semgrep rule also flags `bool` |
| Structured logging: enum events and keys, single logging module, console + JSONL sink, every CLI entry point and preprocessing stage logs | PASS | `test_logging.py`, `tests/unit/test_logging.py`, smoke-run lifecycle test, CLI log-file test |
| Source-code fingerprint / dirty-tree checks | PASS | Fingerprinting was removed by recorded user decision; extension provenance explicitly records `analysis_sources_clean: false` for this uncommitted checkout. |
| Development runs: controlled-exposure, peer-dose-response, natural-scarcity, family-permutation-control, baseline-fairness x 5 development seeds (25 runs) | PASS | all completed, all structural validations passed; FedProx, fine-tune and blend exercised on real data |
| Statistics, decomposition, dose response, novelty association, robustness (top-family removal, de-duplicated test; FedAvg micro CTK gain per experiment), claim gates, tables, figures, `report` command | PASS | run on real development evidence (`test_report_workflow.py`: outputs regenerate, claims deterministic, all 12 claims get an outcome) |
| Promotion to `results/` | PASS | confirmatory, class C (`posthoc`), EXT-1 (`report --mode extension`) and extension-b promotions each write a manifest entry with digest and evidence class (`A-B-C-confirmatory-seeds-row-labelled`, `C-post-confirmatory-evidence-preserving`, `D-prospective-extension`); `results/extension/manifest.json` and `results/extension-b/manifest.json` exist; blocked for incomplete or stale runs |
| Deduplication sensitivity (Roadmap 28) | PASS | family counts carry `unique_hits`/`unique_trials` (each identical feature vector once per family and scope); `robustness` table and report CSV; development CTK gain 0.081 (controlled) vs 0.093 raw; `test_robustness.py`, `test_evaluation.py` |
| Baseline-fairness grids (Roadmap 16.3, Stage D) | PASS | 10 arms per development seed; selection by mean own-domain calibration-partition AUROC (test never used), ties to smaller; frozen: local epochs 10, fine-tune epochs 2, FedProx 0.1; all on grid edges (recorded); `test_fairness.py`, `test_frozen_hyperparameters.py` |
| Run provenance granularity | PASS | fingerprints only data, resolved training config, budget, operating, novelty and the experiment spec (`test_run_fingerprint.py`); stale runs are excluded from analysis and logged |
| Calibration-set discrimination and hidden-row validation on evaluated rows | PASS | `test_evaluation.py` |
| Permutation-control null definition | PASS | frozen: 95% BCa interval within +/-ctk_min_gain (0.03); development control -0.0075 (CI -0.013 to -0.001) is equivalent; tests in `test_gates.py` |
| Graphify and current workflow reachability | PASS | Fresh callgraph covers 719 definitions and all 14 CLI workflows, including diagnostics. Only two Pydantic validators are outside CLI reachability; no scientific method is reachable only from tests. Strict callable, leaf and depth counts are recorded in the final verification report and `docs/temp/wiring/`; `test_wiring` passes. |

## Scientific pipeline

| Area | Status | Note |
|---|---|---|
| Source audit, fingerprints, linkage, label rule | PASS | real data: 1,008,381 rows, 925 features, complete linkage |
| Identity components, clients, deterministic support-constrained partitions | PASS | unit tests + real run |
| Family sets, controlled and natural pairs, deterministic target assignment | PASS | |
| Controlled exposure, no-family, full exposure, dose, sample-size matching | PASS | `test_exposure.py` |
| Local, central, FedAvg, FedProx, fine-tune, blend, MLP/linear/trees | PASS | all exercised end to end in development (baseline-fairness grid runs all learners; linear, MLP and trees separate a synthetic rule in `test_models.py`) |
| Thresholds, own-domain / federation-wide / known-family metrics | PASS | `test_thresholds.py`, `test_metrics.py` |
| Feature-novelty descriptors | PASS | computed per run; Spearman association in `analysis/novelty.py`, tested |
| Development baseline-fairness grids | PASS | frozen in Roadmap 16.3; see Stage D row |
| Doctor / preprocess / plan / smoke / run / status | PASS | e2e smoke idempotency test |
| Clean-snapshot verification | PASS | Current snapshot installs with `uv sync --locked --all-groups`; doctor, config, CLI, plan, collection, all report/extension entry points, and 337 tests pass. Raw data and run evidence are read-only references; `.git` and `.venv` are excluded, with commit history supplied through read-only `GIT_DIR`/`GIT_WORK_TREE`. This verifies current code/report reproducibility, not a raw-data-to-final-evidence rerun. |
| Graphify semantic code graph | PASS | Fresh `graphify update .`: 2,730 nodes, 11,570 edges, 148 communities; 45/45 supported code files re-extracted. Docs are not semantically extracted and community names were not LLM-refreshed. |
| All confirmatory-only experiments executable | PASS | replication set, linear, trees, support sensitivity, salts, low/high family support and package-only grouping were never run before; now each completes at smoke scale (`test_every_smoke_planned_experiment_executes_and_passes_validation`). They list `smoke` in `modes` for this; no confirmatory seed was run |
| Confirmatory evidence (Stages F to K) | PASS | Stage F freeze recorded in `protocol-amendments.md`; 140/140 confirmatory runs completed (seeds 100 to 109, 12 experiments), no infeasible, no stale; all structural validations passed. Two non-structural `operating-point-realised` warnings (seed 106 in family-support-sensitivity-low and -high, max FPR gap 0.025 and 0.020). Claim gates after the post-confirmatory dose-gate correction: 9 promoted (representation-limited-family with scoped wording), generic-pooling-majority, feature-novelty-explanation and new-mechanism-trigger rejected; the original promotion recorded dose-response as narrowed (see `protocol-amendments.md`). Stage K promotion wrote `results/` with zero blocks |
| Analysis on degenerate and single-seed evidence | PASS | smoke evidence from all 11 experiments now flows through statistics, gates and figures; fixed NaN share when total gain is zero, BCa on constant data, bar plots with missing learners (`test_paired_effect_table.py`, `test_smoke_workflow.py`) |
| Tables, figures and report generated when an experiment finishes | PASS | `run` and `smoke` regenerate analysis, tables and figures for the mode from all evidence so far (`run_and_report`); report outputs are now mode-scoped under `outputs/report/<mode>/` so smoke never overwrites development; `test_cli.py` |
| Representation-limited claim wording | PASS | promoted per family; when only some primary families are confirmed by an independent model the wording is the scoped one (`test_gates.py`); confirmatory: 3 of 4 families |

## Extensions, class C and final verification pass (2026-09-25)

| Area | Status | Evidence |
|---|---|---|
| Final validation after the last edit | PASS | Final wording review: 337 tests passed (27 warnings), Ruff check/format passed, Pyright 0 errors, Semgrep 0 findings, wiring 5/5, fresh Graphify, confirmatory/extension/extension-b reports regenerated, 72/4/108 manifest entries hash-verified, section-reference/stale-term/evidence-class scans passed, and `git diff --check` passed. |
| Seed ranges disjoint and matching config | PASS | 100-109 confirmatory; 200-209 EXT-1; 300-309 EXT-LFAM; 310-319 EXT-DOSE; 320-329 EXT-CTRL; 330-339 EXT-REP (`configs/project.yaml`; every run index checked) |
| Original confirmatory evidence untouched | PASS | `results/gates/`, `results/statistics/` unchanged; 9 promoted, 0 narrowed, 3 rejected; manifest digests of original files unchanged (only an evidence-class field added) |
| `results/provenance/protocol.json` currency | PARTIAL | records config and Roadmap fingerprints at the last confirmatory promotion (cfe8a3c); configs and Roadmap were edited afterwards for extensions and documentation, so it is a snapshot, not the current fingerprint. The frozen original protocol fingerprint is in the Stage F entry of `protocol-amendments.md`. Not regenerated to avoid rewriting original provenance |
| Extension provenance | PASS | per-study `*-code.json` (execution and analysis revision) plus per-directory manifests with digests; `analysis_sources_clean` is false because the tree is uncommitted |
| Superseded artefacts | PASS | leaky EXT-REP R2/R3 runs, partition scales and promoted tables in `outputs/superseded/ext-rep-transductive-transform/` and `results/extension-b/superseded/ext-rep-transductive-transform/` (`SHA256SUMS`) |
| External data excluded from Git and `results/` | PASS | `data/` (McNdroid, KronoDroid, others, about 11 GB) gitignored, not tracked or staged |
| EXT-1 workflow (`run`/`report --mode extension`) | PASS | own-domain permutation CTK +0.006 (-0.004, 0.014); protocol hash and file time precede the first run |
| EXT-LFAM workflow (`large-family`) | PASS | 32-family rho 0.392 (0.062, 0.654) reproduced independently; frozen permutation p (0.026) and seed-level rho now produced; eligibility-stability sensitivity wired and promoted |
| EXT-DOSE workflow (`dose-extension`) | PASS | exact dose reproduced from raw metrics; structural checks 0 mismatches; monotonicity rule corrected to the frozen definition (one secondary cell changed) |
| EXT-CTRL workflow (`controls-extension`) | PASS | placebo -0.001 (-0.008, 0.006) and aggregator effects reproduced; mean, trimmed mean and lower median verified on a 4-client toy tensor |
| EXT-REP workflows (`representation-preprocess`, `representation-extension`) | PASS | per-arm training-only R2/R3 transforms (A3); corrected rerun with seeds 330-339; H-REP-2 three-way interpretation; headline numbers reproduced independently from raw run metrics |
| Representation preprocessing isolation | PASS | `fit_transform` sees only the rows a model trains on (`test_models.py`: rows outside the training set cannot change the transform; selection fitted on training rows) |
| Class C workflow (`posthoc`) | PASS | all three tables reproduced from raw runs; wording narrowed to descriptive and accounting language |
| Dataset adapters (`src/ctk_android/data/mcndroid.py`, `src/ctk_android/data/representation.py`) | PASS | `tests/unit/data/test_mcndroid*.py`, `tests/unit/data/test_representation.py` (alignment, raw loading, transform rules) |
| Operating-point fidelity in extensions | PARTIAL | non-blocking realised-FPR warnings: dose-primary seed 317 (0.024) and every EXT-REP R2/R3 run (up to 0.029) exceed the 0.02 tolerance; reported, not a structural failure |
| Literature and document consistency | PASS | Primary-source recheck reclassified Popoola et al. from PARTIAL to ADJACENT. Research Evidence, Roadmap and amendment history agree on 41 rows, 0/4/34/3. Numeric section-reference scan found no missing headings; 115 inline paths were checked, with only three intentionally historical deleted-document references remaining. No stale active source paths or evidence-class mismatches were found. |
| FEDroid and FID-SPA full text | BLOCKED | paywalled, no preprint; unresolved coverage limitation |
| Independent external dataset replication | MISSING | no suitable corpus (Research Evidence 30 to 32) |

Matrix totals: **61 PASS, 2 PARTIAL, 1 MISSING, 2 BLOCKED**.
