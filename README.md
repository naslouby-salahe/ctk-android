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

Raw data are expected under `data/raw`, which is Git-ignored. Create your own symlink (or directory) to wherever you keep the datasets:

```bash
mkdir -p data
ln -s /path/to/your/datasets data/raw
```

Optional local example: `ln -s ~/Projects/datp-shared-data/raw data/raw`.

## Research protocol

[`docs/Roadmap.md`](docs/Roadmap.md) is the authoritative experimental protocol.

## Status

Under active research and development. Confirmatory results have not been produced; nothing in exploratory or local working material should be read as a confirmed finding.

## Reproducibility

- Random seeds are explicit.
- Raw data stay external to the repository.
- Exploratory proof-of-concept work lives in a local, Git-ignored workspace.
- Final implementation and results will follow the frozen roadmap.

## Citation

See [`CITATION.cff`](CITATION.cff).

## License

Code and documentation in this repository are released under the [MIT License](LICENSE). This does not grant or alter any rights over LAMDA, AndroZoo or other external datasets, whose own licences and terms of use apply.
