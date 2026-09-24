# Data

Two source datasets, kept separate and never modified in place:

| Folder | Source | Used for |
|---|---|---|
| `data/lamda/raw/` | LAMDA release `var_thresh_0.01` (Parquet files under `<release>/`, plus `feature_mapping.csv`) | features, labels, families |
| `data/androzoo/raw/` | AndroZoo metadata (`latest.csv.gz`) | market and era for client assignment |

Both `raw/` folders are Git-ignored; symlink them to your local copies (see the root `README.md`). Nothing derived is written here: joins, partitions, identity components and caches go to `outputs/preprocessing/`, and `ctk-android preprocess` records source fingerprints in its provenance files.

Raw datasets are not redistributed. Their own licences apply.
