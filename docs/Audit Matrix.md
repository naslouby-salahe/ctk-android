# Audit Matrix

Status legend: PASS, PARTIAL, MISSING, BLOCKED. Last updated after Stage D and the de-duplication sensitivity.

## Tooling and architecture

| Area | Status | Evidence |
|---|---|---|
| Ruff (lint + format) | PASS | `tests/architecture/test_static_analysis.py` |
| Pyright strict (src + tests) | PASS | same; `pyright` reports 0 errors |
| Semgrep | PASS | `quality/semgrep.yml`, 8 rules, each with a regression case (`test_semgrep_rules.py`) |
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
| Source-code fingerprint / dirty-tree checks | REMOVED | user decision, see implementation-decisions.md |
| Development runs: controlled-exposure, peer-dose-response, natural-scarcity, family-permutation-control, baseline-fairness x 5 development seeds (25 runs) | PASS | all completed, all structural validations passed; FedProx, fine-tune and blend exercised on real data |
| Statistics, decomposition, dose response, novelty association, robustness (top-family removal, de-duplicated test; FedAvg micro CTK gain per experiment), claim gates, tables, figures, `report` command | PASS | run on real development evidence (`test_report_workflow.py`: outputs regenerate, claims deterministic, all 12 claims get an outcome) |
| Promotion to `results/` | PASS | blocked outside confirmatory mode and writes nothing (tested); confirmatory path untested by design |
| Deduplication sensitivity (Roadmap 28) | PASS | family counts carry `unique_hits`/`unique_trials` (each identical feature vector once per family and scope); `robustness` table and report CSV; development CTK gain 0.081 (controlled) vs 0.093 raw; `test_robustness.py`, `test_evaluation.py` |
| Baseline-fairness grids (Roadmap 16.3, Stage D) | PASS | 10 arms per development seed; selection by mean own-domain calibration-partition AUROC (test never used), ties to smaller; frozen: local epochs 10, fine-tune epochs 2, FedProx 0.1; all on grid edges (recorded); `test_fairness.py`, `test_frozen_hyperparameters.py` |
| Run provenance granularity | PASS | fingerprints only data, resolved training config, budget, operating, novelty and the experiment spec (`test_run_fingerprint.py`); stale runs are excluded from analysis and logged |
| Calibration-set discrimination and hidden-row validation on evaluated rows | PASS | `test_evaluation.py` |
| Permutation-control null definition | PASS | frozen: 95% BCa interval within +/-ctk_min_gain (0.03); development control -0.0075 (CI -0.013 to -0.001) is equivalent; tests in `test_gates.py` |
| Graphify before/after reachability | PARTIAL | one final graph produced (no earlier baseline graph existed); architecture reachability is enforced by `test_wiring` instead |

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
| Clean-clone verification | PASS | fresh clone + `uv sync`: Ruff, Pyright strict, Semgrep (8 rules, 0 findings) clean; 164 passed, 10 skipped (tests needing local data/dev runs skip explicitly) |
| Graphify | PASS (code only) | AST graph of `src/`: 829 nodes, 3830 edges, 24 communities, no import cycles; docs not semantically extracted |
| All confirmatory-only experiments executable | PASS | replication set, linear, trees, support sensitivity, salts, low/high family support and package-only grouping were never run before; now each completes at smoke scale (`test_every_smoke_planned_experiment_executes_and_passes_validation`). They list `smoke` in `modes` for this; no confirmatory seed was run |
| Confirmatory evidence (Stages F to K) | PASS | Stage F freeze recorded in `protocol-amendments.md`; 140/140 confirmatory runs completed (seeds 100 to 109, 12 experiments), no infeasible, no stale; all structural validations passed. Two non-structural `operating-point-realised` warnings (seed 106 in family-support-sensitivity-low and -high, max FPR gap 0.025 and 0.020). Claim gates: 8 promoted, dose-response narrowed, generic-pooling-majority, feature-novelty-explanation and new-mechanism-trigger rejected. Stage K promotion wrote `results/` with zero blocks |
| Analysis on degenerate and single-seed evidence | PASS | smoke evidence from all 11 experiments now flows through statistics, gates and figures; fixed NaN share when total gain is zero, BCa on constant data, bar plots with missing learners (`test_paired_effect_table.py`, `test_smoke_workflow.py`) |
| Tables, figures and report generated when an experiment finishes | PASS | `run` and `smoke` regenerate analysis, tables and figures for the mode from all evidence so far (`run_and_report`); report outputs are now mode-scoped under `outputs/report/<mode>/` so smoke never overwrites development; `test_cli.py` |
| Representation-limited claim wording | PASS | promoted per family; when only some primary families are confirmed by an independent model the wording is the scoped one (`test_gates.py`); confirmatory: 3 of 4 families |
