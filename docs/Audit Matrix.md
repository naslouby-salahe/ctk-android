# Audit Matrix

Status legend: PASS, PARTIAL, MISSING, BLOCKED. Last updated at the lint/architecture checkpoint.

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
| Graphify before/after reachability | MISSING | not yet run |

## Scientific pipeline

| Area | Status | Note |
|---|---|---|
| Source audit, fingerprints, linkage, label rule | PASS | real data: 1,008,381 rows, 925 features, complete linkage |
| Identity components, clients, deterministic support-constrained partitions | PASS | unit tests + real run |
| Family sets, controlled and natural pairs, deterministic target assignment | PASS | |
| Controlled exposure, no-family, full exposure, dose, sample-size matching | PASS | `test_exposure.py` |
| Local, central, FedAvg, FedProx, fine-tune, blend, MLP/linear/trees | PARTIAL | implemented; only local/central/FedAvg exercised end to end so far |
| Thresholds, own-domain / federation-wide / known-family metrics | PASS | `test_thresholds.py`, `test_metrics.py` |
| Feature-novelty descriptors | PARTIAL | computed per run; association analysis not written |
| Decomposition, dose response, natural-scarcity, robustness analysis | MISSING | |
| BCa, exact Wilcoxon, cluster bootstrap, Holm, claim gates | MISSING | statistics config removed until implemented |
| Reporting, tables, figures, controlled promotion to `results/`, `report` command | MISSING | |
| Development baseline-fairness grids | MISSING | |
| Doctor / preprocess / plan / smoke / run / status | PASS | e2e smoke idempotency test |
