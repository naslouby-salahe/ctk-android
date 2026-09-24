# Audit Matrix

Status at first pass: repository contained only `docs/`, README, license. Everything below is MISSING unless marked.

| Area | Status | Note |
|---|---|---|
| Enums (`enums.py`) | PARTIAL | first version written, unwired |
| Config files (4 YAML) | PARTIAL | written, no validating loader yet |
| pyproject/ruff/pyright | PARTIAL | written, `uv sync` OK |
| Data pipeline (sources, joins, identity, clients, partitions, families, cache) | MISSING | real-data facts verified, see decisions |
| Experiment (exposure, models, training, thresholds, evaluation, metrics) | MISSING | |
| Analysis and statistics | MISSING | |
| Reporting and promotion | MISSING | |
| CLI and workflows | MISSING | |
| Architecture tests, Semgrep | MISSING | FedIEC patterns identified for porting |
| Graphify reachability | MISSING | nothing to graph yet |
