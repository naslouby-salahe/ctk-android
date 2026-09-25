# CTK-Android

**Complementary Threat Knowledge in Federated Android Malware Detection: A Controlled-Exposure Decomposition**

## Overview

CTK-Android is an empirical study of federated / collaborative Android malware detection when clients have *complementary* malware-family exposure: a peer knows a family that the local client has never observed.

The central distinction is:

```text
total collaboration gain
=
generic pooling contribution
+
complementary threat-knowledge contribution
```

The project measures how much of the benefit of collaboration on locally unseen families comes from simply pooling more data, and how much comes from peers actually holding the missing family. It is **not** a proposal for a new federated-learning algorithm.

## Research questions

The authoritative list is in [`docs/Roadmap.md`](docs/Roadmap.md). In brief:

- Does collaboration help on malware families a client has never observed?
- How much of that gain is generic pooling, and how much is complementary family knowledge held by peers?
- How does recall change with the amount of peer exposure to a family (dose-response)?
- Do the effects hold for the worst-off client, not only on average?
- Which families are collaboration-irreducible even with full peer exposure?
- What does collaboration cost on families a client already knows?

## Data

Public datasets only, primarily **LAMDA** and **AndroZoo** metadata. Raw datasets are not redistributed and are never committed.

Raw data are expected under `data/lamda/raw` and `data/androzoo/raw`, which are Git-ignored. Create your own symlinks (or directories) to wherever you keep the datasets:

```bash
mkdir -p data/lamda data/androzoo
ln -s /path/to/LAMDA data/lamda/raw
ln -s /path/to/AndroZoo data/androzoo/raw
```

## Research protocol

[`docs/Roadmap.md`](docs/Roadmap.md) is the authoritative experimental protocol.

## Status

The protocol is frozen (see `docs/decisions/protocol-amendments.md`) and the 140 confirmatory runs (seeds 100 to 109) are complete. Claim outcomes are in `results/gates/claims.csv` (9 promoted, 3 rejected after the post-confirmatory dose-gate correction recorded in `docs/decisions/protocol-amendments.md`). The interpreted evidence, literature audit and feasibility assessments are consolidated in `docs/Research Evidence.md`. Exploratory or local working material should not be read as a confirmed finding.

## Commands and durations

Setup, then one command per experiment. Every `run` regenerates the analysis, tables and figures for its mode under `outputs/report/<mode>/`; `report` rebuilds them from saved evidence and `report --mode confirmatory --promote` copies confirmatory evidence into `results/`.

| Command | Purpose | Duration |
|---|---|---|
| `uv run ctk-android doctor` | check environment, config, sources | 0.1 s |
| `uv run ctk-android preprocess` | audit sources, build identities, clients, families, partitions | 293 s first run, 23 s when reused |
| `uv run ctk-android plan <mode>` | write the run matrix | 0.1 s (6 s for the confirmatory plan) |
| `uv run ctk-android smoke` | end-to-end smoke run | 13 s |
| `uv run ctk-android status --mode <mode>` | summarise run status | under 0.1 s |
| `uv run ctk-android report --mode <mode>` | analysis, claim gates, post-confirmatory analyses, 20 tables, 11 figures | 9 s development, 18 s confirmatory (21 s with `--promote`) |

Experiments (`--seed N` runs a single seed; durations are wall-clock per run on one RTX 5060 Ti, measured from the run logs):

| Experiment | Command | Duration |
|---|---|---|
| `end-to-end` | `uv run ctk-android smoke` | smoke: 1 run, 13 s |
| `baseline-fairness` | `uv run ctk-android run baseline-fairness --mode development` | development: 5 runs, 78 s each, 6.5 min total |
| `controlled-exposure` | `uv run ctk-android run controlled-exposure --mode development`<br>`uv run ctk-android run controlled-exposure --mode confirmatory` | development: 5 runs, 91 s each, 7.6 min total<br>confirmatory: 10 runs, 86 s each, 14.4 min total |
| `peer-dose-response` | `uv run ctk-android run peer-dose-response --mode development`<br>`uv run ctk-android run peer-dose-response --mode confirmatory` | development: 5 runs, 101 s each, 8.4 min total<br>confirmatory: 10 runs, 93 s each, 15.5 min total |
| `natural-scarcity` | `uv run ctk-android run natural-scarcity --mode development`<br>`uv run ctk-android run natural-scarcity --mode confirmatory` | development: 5 runs, 46 s each, 3.9 min total<br>confirmatory: 10 runs, 43 s each, 7.2 min total |
| `family-permutation-control` | `uv run ctk-android run family-permutation-control --mode development`<br>`uv run ctk-android run family-permutation-control --mode confirmatory`<br>`uv run ctk-android run family-permutation-control --mode extension` | development: 5 runs, 46 s each, 3.8 min total<br>confirmatory: 10 runs, 45 s each, 7.5 min total<br>extension (EXT-1, seeds 200 to 209): 10 runs, 58 s each while sharing the GPU, about 10 min total |
| `replication-family-set` | `uv run ctk-android run replication-family-set --mode confirmatory` | confirmatory: 10 runs, 118 s each, 19.7 min total |
| `model-family-replication-linear` | `uv run ctk-android run model-family-replication-linear --mode confirmatory` | confirmatory: 10 runs, 63 s each, 10.6 min total |
| `model-family-replication-trees` | `uv run ctk-android run model-family-replication-trees --mode confirmatory` | confirmatory: 10 runs, 103 s each, 17.2 min total |
| `training-support-sensitivity` | `uv run ctk-android run training-support-sensitivity --mode confirmatory` | confirmatory: 10 runs, 47 s each, 7.8 min total |
| `partition-salt-sensitivity` | `uv run ctk-android run partition-salt-sensitivity --mode confirmatory` | confirmatory: 30 runs, 83 s each, 41.7 min total |
| `family-support-sensitivity-low` | `uv run ctk-android run family-support-sensitivity-low --mode confirmatory` | confirmatory: 10 runs, 78 s each, 12.9 min total |
| `family-support-sensitivity-high` | `uv run ctk-android run family-support-sensitivity-high --mode confirmatory` | confirmatory: 10 runs, 62 s each, 10.4 min total |
| `package-only-grouping` | `uv run ctk-android run package-only-grouping --mode confirmatory` | confirmatory: 10 runs, 87 s each, 14.5 min total |

Development uses seeds 1 to 5, confirmatory uses seeds 100 to 109, and seeds 200 to 209 (`--mode extension`) are reserved for separately frozen prospective extensions that are never pooled with the original campaign. `partition-salt-sensitivity` runs 3 salts per seed. The first four confirmatory experiments ran one at a time; the remaining eight ran as five parallel workers, so their per-run times include contention for CPU and GPU and their totals are not sequential wall time. Whole confirmatory stage: about 140 runs in roughly 2.5 hours.

## Reproducibility

- Random seeds are explicit.
- Raw data stay external to the repository.
- Exploratory proof-of-concept work lives in a local, Git-ignored workspace.
- Final implementation and results will follow the frozen roadmap.

## Citation

See [`CITATION.cff`](CITATION.cff).

## License

Code and documentation in this repository are released under the [MIT License](LICENSE). This does not grant or alter any rights over LAMDA, AndroZoo or other external datasets, whose own licences and terms of use apply.
