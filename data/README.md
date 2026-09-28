# Data

Source datasets, kept separate and never modified in place:

| Folder | Source | Used for |
|---|---|---|
| `data/lamda/raw/` | LAMDA release `var_thresh_0.01` (Parquet files under `<release>/`, plus `feature_mapping.csv`) | features, labels, families |
| `data/androzoo/raw/` | AndroZoo metadata (`latest.csv.gz`) | market and era for client assignment |
| `data/mcndroid/raw/` | McNdroid representation sources (`data_feature/`, `gml_feature/`, `json_feature/`); only needed by the representation experiments | representation experiments `representation-r0` to `representation-r3` |

Every `raw/` folder is Git-ignored; symlink them to your local copies (see the root `README.md`). Nothing derived is written here: joins, partitions, identity components and caches go to `outputs/preprocessing/`, and `ctk-android preprocess` records source fingerprints in its provenance files.

Raw datasets are not redistributed. Their own licences apply.
