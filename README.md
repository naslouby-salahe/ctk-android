# CTK-Android

**Complementary Threat Knowledge in Federated Android Malware Detection**

CTK-Android studies whether federated collaboration helps detect malware families that are unseen locally but observed by peer clients, separating generic pooling gain from complementary threat-knowledge gain.

## Setup

Requires Python 3.12+ and `uv`.

```bash
git clone https://github.com/naslouby-salahe/ctk-android.git
cd ctk-android
uv sync
```

## Datasets

Raw data are external and are not committed.

### LAMDA

`data/lamda/raw/` must contain the configured `var_thresh_0.01` release:

```text
data/lamda/raw/
└── var_thresh_0.01/
    ├── *.parquet
    └── feature_mapping.csv
```

### AndroZoo

```text
data/androzoo/raw/
└── latest.csv.gz
```

The easiest setup is with symlinks:

```bash
mkdir -p data/lamda data/androzoo
ln -s /path/to/LAMDA data/lamda/raw
ln -s /path/to/AndroZoo data/androzoo/raw
```

### McNdroid — representation experiments only

The representation experiments (`representation-r0` to `representation-r3`) require the McNdroid representation sources:

```bash
mkdir -p data/mcndroid
ln -s /path/to/McNdroid data/mcndroid/raw
```

The linked directory must contain the provider's `data_feature/`, `gml_feature/`, and `json_feature/` trees under `processed_data/init_2013/`.

## Run

Everything scientific — execution scopes, seeds, partition salts, family sets, representations, models, thresholds, doses — is fixed in `configs/*.yaml` and resolved from there. The command line only chooses what to do.

```bash
uv run ctk-android doctor                # validate runtime, configuration, raw data, compute and git state
uv run ctk-android preprocess            # build or reuse every preprocessing stage the configuration needs
uv run ctk-android plan <mode>           # enumerate and validate the configured runs of one scope
uv run ctk-android smoke                 # small end-to-end wiring and reproducibility check
uv run ctk-android run <experiment>      # run the experiment's complete configured matrix
uv run ctk-android status                # read-only completion summary of the whole configured matrix
uv run ctk-android report                # build the final evidence package
```

`<mode>` is one of `smoke`, `development`, `confirmatory`, `extension` or `extension-b`; `plan` is the only command that takes it. `preprocess` also builds the McNdroid representation stages (`representation-r0` to `representation-r3`) because the configuration contains those experiments. `preprocess` and `smoke` accept `--overwrite`, and so does `run`, to rebuild instead of reusing.

A complete campaign:

```bash
uv run ctk-android doctor
uv run ctk-android preprocess
for mode in development confirmatory extension extension-b; do uv run ctk-android plan $mode; done

uv run ctk-android run controlled-exposure    # every configured scope and seed of this experiment
uv run ctk-android run peer-dose-response
# ... one `run` per experiment ID listed by `uv run ctk-android run --help`

uv run ctk-android status
uv run ctk-android report
```

`run` never builds a shared report, so different experiments can run concurrently. `report` refuses to build evidence from missing, failed or stale runs, or from uncommitted sources.

Use `uv run ctk-android --help` and `uv run ctk-android <command> --help` for the option lists.

## Outputs

* `outputs/` is the experiment workspace: preprocessing, plans, one directory per run (`outputs/runs/<mode>/<experiment>/seed-<n>`), logs and the report's intermediate analyses. It is not committed.
* `results/` is written only by `report`: the manuscript-ready tables, figures, statistics, diagnostics, manifests with file digests, and the provenance of the code, configuration and data that produced them.

The project has 7 CLI commands and 26 configured experiment IDs (`end-to-end` runs through `smoke` only).
