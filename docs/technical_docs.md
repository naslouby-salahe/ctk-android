# CTK-Android Technical Engineering Contract

> **Document role:** Authoritative technical and software-engineering contract for this repository.
>
> **Location:** `docs/technical_docs.md`
>
> This document defines how the repository is structured, implemented, audited, executed, tested, and maintained. It intentionally does **not** duplicate the scientific protocol. Scientific methodology belongs in `docs/Roadmap.md`.

---

## 1. Authority and Source-of-Truth Hierarchy

The repository uses the following authority order.

### 1.1 Scientific authority

`docs/Roadmap.md` is the authoritative source for:

- research questions;
- hypotheses;
- datasets and dataset roles;
- scientific definitions;
- client definitions;
- exposure rules;
- baselines and comparators;
- experiment conditions;
- metrics;
- statistical procedures;
- seed roles;
- operating points;
- claim gates;
- failure/downscope semantics;
- expected publication evidence;
- scientific limitations.

Code must implement the roadmap. Code must not silently redefine it.

### 1.2 Technical authority

`docs/technical_docs.md` is the authoritative source for:

- repository architecture;
- configuration ownership;
- typing and enum rules;
- path rules;
- code-quality constraints;
- workflow wiring;
- artifact layout;
- output/result separation;
- testing;
- Graphify;
- audits;
- Git discipline;
- execution discipline;
- reproducibility engineering.

### 1.3 Runtime authority

Validated configuration is the runtime source of truth for configurable scientific and execution parameters.

Do not scatter run-affecting values through implementation code.

### 1.4 Empirical authority

When the real source data disagrees with an assumed count, support level, schema detail, available family, client count, or other empirically discoverable property, inspect the data and record the evidence.

Do not force reality to match an expected number from prose.

---

## 2. Interpretation Rules

Every requirement encountered during implementation or audit must be classified correctly.

### 2.1 Scientifically authoritative

Treat the following as binding unless the roadmap itself explicitly permits variation:

- formulas;
- algorithmic semantics;
- information restrictions;
- leakage rules;
- experimental design;
- comparators;
- thresholds and operating-point definitions;
- metrics;
- statistical units;
- statistical procedures;
- multiplicity logic;
- seed roles;
- claim gates;
- failure semantics.

### 2.2 Empirically amendable

The following may legitimately differ from expectations when real data proves otherwise:

- row counts;
- available clients;
- eligible families;
- support counts;
- usable timestamps;
- source file layouts;
- observed schema variants;
- measured runtime;
- measured memory/resource behavior;
- source availability.

Such differences are evidence-backed empirical findings, not automatic implementation defects.

### 2.3 Implementation-flexible

Equivalent implementations are allowed for:

- helper placement;
- internal class names;
- module boundaries;
- library selection;
- caching strategy;
- parallelization;
- internal orchestration.

Audit semantics and wiring, not cosmetic similarity to an old implementation.

---

## 3. Engineering Philosophy

The repository must remain:

- small;
- explicit;
- typed;
- deterministic;
- reproducible;
- auditable;
- well wired;
- easy to delete and rebuild;
- difficult to misuse accidentally.

Prefer the smallest architecture that fully expresses the scientific protocol.

Do not build infrastructure merely because it looks architecturally sophisticated.

Do not introduce abstractions before they solve a real repeated problem.

Do not preserve complexity for hypothetical future use.

---

## 4. Full Repository Tree

This tree is the preferred repository structure for CTK-Android.

It is intentionally compact in `src/`, explicit in `outputs/`, strict in `results/`, and keeps the two source datasets separated.

```text
ctk-android/
│
├── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .pre-commit-config.yaml
│
├── configs/
│   ├── project.yaml
│   ├── data.yaml
│   ├── experiments.yaml
│   └── statistics.yaml
│
├── data/
│   ├── README.md
│   │
│   ├── lamda/
│   │   └── raw/
│   │       └── ...
│   │
│   └── androzoo/
│       └── raw/
│           └── ...
│
├── docs/
│   ├── Roadmap.md
│   ├── technical_docs.md
│   ├── Audit Matrix.md
│   │
│   ├── decisions/
│   │   ├── protocol-amendments.md
│   │   └── implementation-decisions.md
│   │
│   └── temp/
│       ├── audit-notes/
│       ├── investigations/
│       └── graphify/
│
├── src/
│   └── ctk_android/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── enums.py
│       ├── types.py
│       ├── paths.py
│       ├── logs.py
│       ├── provenance.py
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── sources.py
│       │   ├── preparation.py
│       │   ├── representations.py
│       │   ├── partitions.py
│       │   └── cache.py
│       │
│       ├── experiment/
│       │   ├── __init__.py
│       │   ├── planning.py
│       │   ├── design.py
│       │   ├── models.py
│       │   ├── training.py
│       │   └── evaluation.py
│       │
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── decomposition.py
│       │   ├── diagnostics.py
│       │   ├── diagnostic_synthesis.py
│       │   ├── extensions.py
│       │   ├── post_confirmatory.py
│       │   └── statistics.py
│       │
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── artifacts.py
│       │   ├── tables.py
│       │   └── figures.py
│       │
│       └── workflows/
│           ├── __init__.py
│           ├── maintenance.py
│           ├── preprocess.py
│           ├── run.py
│           └── report.py
│
├── tests/
│   ├── conftest.py
│   │
│   ├── unit/
│   │   ├── data/
│   │   │   ├── test_sources.py
│   │   │   ├── test_joins.py
│   │   │   ├── test_identity.py
│   │   │   ├── test_clients.py
│   │   │   ├── test_partitions.py
│   │   │   ├── test_families.py
│   │   │   └── test_cache.py
│   │   │
│   │   ├── experiment/
│   │   │   ├── test_exposure.py
│   │   │   ├── test_models.py
│   │   │   ├── test_training.py
│   │   │   ├── test_substitution.py
│   │   │   ├── test_designs.py
│   │   │   ├── test_thresholds.py
│   │   │   ├── test_evaluation.py
│   │   │   └── test_metrics.py
│   │   │
│   │   ├── analysis/
│   │   │   ├── test_decomposition.py
│   │   │   ├── test_dose_response.py
│   │   │   ├── test_novelty.py
│   │   │   ├── test_hidden_family.py
│   │   │   ├── test_large_family.py
│   │   │   ├── test_extension_effects.py
│   │   │   ├── test_dose_extension.py
│   │   │   ├── test_controls_extension.py
│   │   │   ├── test_robustness.py
│   │   │   ├── test_statistics.py
│   │   │   └── test_gates.py
│   │   │
│   │   ├── reporting/
│   │   │   ├── test_records.py
│   │   │   ├── test_tables.py
│   │   │   ├── test_figures.py
│   │   │   └── test_promotion.py
│   │   │
│   │   └── workflows/
│   │       ├── test_doctor.py
│   │       ├── test_preprocess.py
│   │       ├── test_plan.py
│   │       ├── test_smoke.py
│   │       ├── test_run.py
│   │       ├── test_status.py
│   │       └── test_report.py
│   │
│   ├── integration/
│   │   ├── test_preprocessing_pipeline.py
│   │   ├── test_controlled_exposure_pipeline.py
│   │   ├── test_training_pipeline.py
│   │   ├── test_evaluation_pipeline.py
│   │   ├── test_analysis_pipeline.py
│   │   └── test_reporting_pipeline.py
│   │
│   ├── e2e/
│   │   └── test_smoke_workflow.py
│   │
│   └── architecture/
│       ├── test_cli_reachability.py
│       ├── test_config_drift.py
│       ├── test_no_primitive_leaks.py
│       ├── test_no_unstructured_core_io.py
│       ├── test_no_magic_scientific_values.py
│       ├── test_no_test_data_access.py
│       ├── test_no_duplicate_scientific_logic.py
│       ├── test_no_dead_experiment_paths.py
│       └── test_publication_from_saved_evidence.py
│
├── quality/
│   └── semgrep.yml
│
├── outputs/
│   │
│   ├── preprocessing/
│   │   │
│   │   ├── source-audit/
│   │   │   ├── lamda/
│   │   │   │   ├── fingerprint.json
│   │   │   │   ├── schema.json
│   │   │   │   ├── inventory.json
│   │   │   │   └── counts.json
│   │   │   │
│   │   │   ├── androzoo/
│   │   │   │   ├── fingerprint.json
│   │   │   │   ├── schema.json
│   │   │   │   ├── inventory.json
│   │   │   │   └── counts.json
│   │   │   │
│   │   │   └── linkage/
│   │   │       ├── hash-linkage.parquet
│   │   │       ├── unmatched.parquet
│   │   │       └── audit.json
│   │   │
│   │   ├── joined/
│   │   │   ├── dataset.parquet
│   │   │   └── audit.json
│   │   │
│   │   ├── identity/
│   │   │   ├── feature-identities.parquet
│   │   │   ├── package-identities.parquet
│   │   │   ├── components.parquet
│   │   │   └── component-summary.parquet
│   │   │
│   │   ├── clients/
│   │   │   ├── assignments.parquet
│   │   │   ├── support.parquet
│   │   │   └── audit.json
│   │   │
│   │   ├── families/
│   │   │   ├── support.parquet
│   │   │   ├── eligibility.parquet
│   │   │   ├── primary-family-set.json
│   │   │   ├── replication-family-set.json
│   │   │   ├── natural-scarcity-pairs.parquet
│   │   │   └── audit.json
│   │   │
│   │   ├── partitions/
│   │   │   ├── seed-000/
│   │   │   │   ├── assignments.parquet
│   │   │   │   └── manifest.json
│   │   │   ├── seed-001/
│   │   │   │   ├── assignments.parquet
│   │   │   │   └── manifest.json
│   │   │   └── ...
│   │   │
│   │   └── cache/
│   │       └── ...
│   │
│   ├── plans/
│   │   ├── smoke/
│   │   │   └── plan.json
│   │   │
│   │   ├── development/
│   │   │   ├── run-matrix.parquet
│   │   │   ├── family-assignments.parquet
│   │   │   └── plan.json
│   │   │
│   │   └── confirmatory/
│   │       ├── run-matrix.parquet
│   │       ├── family-assignments.parquet
│   │       ├── seed-plan.json
│   │       └── plan.json
│   │
│   ├── runs/
│   │   │
│   │   ├── smoke/
│   │   │   └── end-to-end/
│   │   │       └── seed-000/
│   │   │           ├── manifest.json
│   │   │           ├── status.json
│   │   │           ├── validation.json
│   │   │           ├── exposure.parquet
│   │   │           ├── thresholds.parquet
│   │   │           ├── metrics/
│   │   │           │   ├── summary.parquet
│   │   │           │   ├── clients.parquet
│   │   │           │   ├── families.parquet
│   │   │           │   └── operating-points.parquet
│   │   │           ├── scores/
│   │   │           ├── models/
│   │   │           └── logs/
│   │   │
│   │   ├── development/
│   │   │   ├── baseline-fairness/
│   │   │   ├── feature-novelty/
│   │   │   ├── family-permutation-control/
│   │   │   ├── dose-implementation/
│   │   │   └── natural-scarcity-construction/
│   │   │
│   │   ├── confirmatory/
│   │   │   ├── controlled-exposure/
│   │   │   ├── peer-dose-response/
│   │   │   ├── natural-scarcity/
│   │   │   ├── replication-family-set/
│   │   │   ├── model-family-replication/
│   │   │   ├── operating-point-sensitivity/
│   │   │   ├── training-support-sensitivity/
│   │   │   ├── partition-salt-sensitivity/
│   │   │   ├── family-support-sensitivity/
│   │   │   ├── top-family-removal/
│   │   │   ├── package-only-grouping/
│   │   │   └── representation-deduplication/
│   │   │
│   │   └── exploratory/
│   │       └── ...
│   │
│   ├── analysis/
│   │   ├── development/
│   │   │   └── ...
│   │   │
│   │   └── confirmatory/
│   │       ├── collaboration-decomposition.parquet
│   │       ├── own-domain-effects.parquet
│   │       ├── worst-client-effects.parquet
│   │       ├── peer-dose-response.parquet
│   │       ├── family-rescue.parquet
│   │       ├── natural-scarcity.parquet
│   │       ├── feature-novelty.parquet
│   │       ├── representation-limits.parquet
│   │       ├── known-family-cost.parquet
│   │       └── robustness.parquet
│   │
│   ├── statistics/
│   │   └── confirmatory/
│   │       ├── paired-effects.parquet
│   │       ├── bca-intervals.parquet
│   │       ├── wilcoxon.parquet
│   │       ├── cluster-bootstrap.parquet
│   │       ├── holm.parquet
│   │       ├── support-status.parquet
│   │       └── claim-gates.parquet
│   │
│   ├── report/
│   │   ├── tables/
│   │   │   └── ...
│   │   └── figures/
│   │       └── ...
│   │
│   ├── audit/
│   │   ├── data/
│   │   ├── leakage/
│   │   ├── baselines/
│   │   ├── metrics/
│   │   ├── statistics/
│   │   ├── reproducibility/
│   │   ├── graphify/
│   │   ├── call-graphs/
│   │   └── clean-environment/
│   │
│   ├── archive/
│   │   └── superseded/
│   │       └── ...
│   │
│   ├── logs/
│   └── temp/
│
└── results/
    │
    ├── README.md
    ├── manifest.json
    │
    ├── provenance/
    │   ├── source-data.json
    │   ├── code.json
    │   ├── environment.json
    │   └── protocol.json
    │
    ├── evidence/
    │   ├── run-index.parquet
    │   ├── arm-metrics.parquet
    │   ├── client-metrics.parquet
    │   ├── family-metrics.parquet
    │   ├── operating-points.parquet
    │   ├── exposure-support.parquet
    │   ├── collaboration-decomposition.parquet
    │   ├── peer-dose-response.parquet
    │   ├── natural-scarcity.parquet
    │   ├── feature-novelty.parquet
    │   ├── known-family-cost.parquet
    │   ├── representation-limits.parquet
    │   ├── robustness.parquet
    │   ├── ctk-heterogeneity-components.parquet
    │   ├── aggregate-metric-masking.parquet
    │   └── negative-transfer-decomposition.parquet
    │
    ├── statistics/
    │   ├── paired-effects.parquet
    │   ├── bca-intervals.parquet
    │   ├── wilcoxon.parquet
    │   ├── cluster-bootstrap.parquet
    │   └── holm.parquet
    │
    ├── gates/
    │   ├── seed-status.csv
    │   ├── support-status.csv
    │   └── claims.csv
    │
    ├── tables/
    │   ├── dataset-client-audit.csv
    │   ├── primary-arm-comparison.csv
    │   ├── collaboration-decomposition.csv
    │   ├── peer-dose-response.csv
    │   ├── family-level.csv
    │   ├── claim-gates.csv
    │   ├── robustness.csv                  (micro-pooled aggregation, per salt)
    │   ├── ctk-robustness-synthesis.csv    (seed-paired and micro-pooled, labelled)
    │   ├── client-ctk-analysis.csv         (class C, per-client, descriptive)
    │   ├── anchored-worst-client.csv       (class C, post-confirmatory)
    │   ├── anchored-client-selection.csv   (class C)
    │   ├── federated-arm-tradeoff.csv      (class C, descriptive)
    │   ├── family-mechanism-patterns.csv   (class C, descriptive)
    │   ├── natural-scarcity-comparison.csv
    │   ├── permutation-control-audit.csv
    │   ├── mechanism-headroom.csv
    │   ├── ctk-heterogeneity-components.csv   (class C, post-confirmatory)
    │   ├── aggregate-metric-masking.csv       (class C, post-confirmatory)
    │   ├── negative-transfer-decomposition.csv (class C, post-confirmatory)
    │   └── operating-point-fidelity.csv
    │
    ├── extension-b/                        (separate prospective extension, never pooled)
    │   ├── code.json, controls-code.json, dose-code.json
    │   ├── run-index, large-family-{selection,ctk,seed-ctk,summary}
    │   ├── exact-dose-{run-index,seed-effects,effects,family-curves,consistency,verdicts}
    │   ├── controls-{run-index,seed-effects,effects,placebo-pairs,verdicts}
    │   ├── representation-code.json
    │   └── representation-{run-index,seed-effects,effects,levels,verdicts,eligibility}
    │       (each as .parquet and .csv)
    │
    └── figures/
        ├── collaboration-decomposition.pdf
        ├── collaboration-decomposition.png
        │
        ├── mean-versus-worst-client.pdf
        ├── mean-versus-worst-client.png
        │
        ├── own-domain-versus-federation-wide.pdf
        ├── own-domain-versus-federation-wide.png
        │
        ├── peer-dose-response.pdf
        ├── peer-dose-response.png
        │
        ├── family-rescue-map.pdf
        ├── family-rescue-map.png
        │
        ├── feature-novelty-versus-ctk-gain.pdf
        ├── feature-novelty-versus-ctk-gain.png
        │
        ├── known-versus-unseen-tradeoff.pdf
        ├── known-versus-unseen-tradeoff.png
        │
        ├── ctk-robustness-forest.pdf
        ├── ctk-robustness-forest.png
        │
        ├── federated-arm-tradeoff.pdf
        ├── federated-arm-tradeoff.png
        │
        ├── natural-versus-controlled.pdf
        ├── natural-versus-controlled.png
        │
        ├── client-ctk-analysis.pdf
        └── client-ctk-analysis.png
```

### 4.1 Tree interpretation

The tree is a target architecture, not permission to create empty placeholders.

Rules:

- do not create a directory until the repository actually needs it;
- do not create empty modules merely to match this document;
- do not create placeholder tests with no meaningful assertion;
- do not create empty `outputs/` experiment subfolders before an experiment exists;
- do not create publication files before evidence exists;
- do not create every optional robustness experiment if the roadmap later removes it;
- remove obsolete folders if the final roadmap no longer requires them.

The tree expresses ownership and intended placement.

It must not become ceremonial scaffolding.

### 4.2 Compact `src/` rule

The preferred source architecture intentionally keeps only five substantive areas:

```text
data/
experiment/
analysis/
reporting/
workflows/
```

plus the project-level core modules:

```text
cli.py
config.py
enums.py
types.py
paths.py
logs.py
provenance.py
```

Do not split these into many one-file packages without evidence that the separation materially improves maintainability.

### 4.3 Dataset separation

LAMDA and AndroZoo remain separate first-class source trees:

```text
data/lamda/raw/
data/androzoo/raw/
```

Joined or transformed data does not return to `data/`.

It belongs under:

```text
outputs/preprocessing/
```

### 4.4 Output/result flow

The intended evidence flow is:

```text
data/
  ↓
outputs/preprocessing/
  ↓
outputs/plans/
  ↓
outputs/runs/
  ↓
outputs/analysis/
  ↓
outputs/statistics/
  ↓
outputs/report/
  ↓
validation + statistical lock + claim gates
  ↓
results/
```

`results/` is the final promoted evidence surface.
## 5. Source-Code Structure

Keep `src/` compact.

### 5.1 Approved responsibilities

`data/`

- `sources.py` owns source scanning, fingerprints, and source loading;
- `preparation.py` owns identity, client, family-set loading, and joined-table preparation;
- `representations.py` owns representation alignment and feature preparation;
- `partitions.py` and `cache.py` own deterministic splits and reusable preprocessing.

`experiment/`

- `planning.py` owns planned runs and target resolution; `design.py` owns experiment arms, exposure, and substitution design;
- `models.py` and `training.py` own fitting and training;
- `evaluation.py` owns calibration, thresholding, and metric computation.

`analysis/`

- `decomposition.py` owns decomposition and dose estimands;
- `diagnostics.py` owns scientific diagnostic tables and checks, while `diagnostic_synthesis.py` owns cross-diagnostic associations and synthesis;
- `extensions.py` owns extension effects, novelty, and family-level extension analyses;
- `post_confirmatory.py` owns post-confirmatory analyses, robustness/fairness selection, and scientific claim gates;
- `statistics.py` owns shared statistical primitives.

`reporting/`

- structured result records;
- tables;
- figures;
- evidence promotion.

The project-level `provenance.py` owns Git revision and source-cleanliness checks shared by doctor and evidence promotion.

`workflows/`

- CLI-facing orchestration only.

Extension and representation behavior remains unchanged; those responsibilities now live in the shared modules above. Four workflow modules serve all 14 CLI commands: `maintenance.py` handles doctor, plan, and status; `preprocess.py` handles preprocessing commands; `run.py` handles run and smoke; and `report.py` handles report, posthoc, large-family, dose, controls, representation, and diagnostics commands. Tests remain grouped by behavior rather than mirroring the consolidated production modules.

### 5.2 Avoid package proliferation

Do not create a new package for every scientific concept.

A concept deserves its own module or package only when it has a coherent independent responsibility.

Prefer:

```text
experiment/training.py
analysis/statistics.py
```

over unnecessary trees containing one tiny file per concept.

### 5.3 Forbidden generic dumping grounds

Do not introduce generic modules such as:

```text
utils.py
helpers.py
common.py
misc.py
core.py
```

unless the module has a genuinely narrow, obvious, single responsibility.

Code belongs with the domain that owns it.

---

## 6. Dataset Rules

### 6.1 Two first-class source folders

The project keeps the two primary external sources separate:

```text
data/
├── lamda/
│   └── raw/
└── androzoo/
    └── raw/
```

Do not merge them into one opaque raw-data directory.

### 6.2 Raw data is immutable

Raw data must never be modified in place.

Derived data must never be written under `data/*/raw/`.

### 6.3 Derived data belongs in `outputs/`

Joined data, partitions, components, support tables, cached transformations, and other derived artifacts belong under `outputs/preprocessing/`.

### 6.4 External datasets

Prefer external dataset storage or symlinks when appropriate.

Do not duplicate large datasets into the repository.

Do not commit raw datasets unless repository policy explicitly says otherwise.

### 6.5 Provenance

For each source, retain where applicable:

- source identity;
- version/release;
- checksum/fingerprint;
- file inventory;
- schema;
- row count;
- feature count;
- relevant label rules;
- acquisition/download provenance.

### 6.6 Large downloads

Do not casually start exceptionally large downloads.

For an individual download expected to exceed roughly 50 GB, obtain explicit approval before starting unless the user has already explicitly authorized that acquisition.

### 6.7 Never fabricate missing metadata

If source metadata is unavailable, record it as unavailable or unresolved.

Never manufacture:

- timestamps;
- package identity;
- client identity;
- family labels;
- source provenance;
- missing support.

---

## 7. Configuration Contract

Configuration must be centralized, validated, explicit, and small.

### 7.1 Approved configuration surface

The intended committed configuration surface is:

```text
configs/project.yaml
configs/data.yaml
configs/experiments.yaml
configs/statistics.yaml
```

Do not add configuration files casually.

Keep the total YAML/YML surface at five files or fewer unless explicitly approved.

### 7.2 Central parsing

All committed YAML configuration must be loaded through the centralized configuration layer.

Scientific modules must not parse YAML directly.

### 7.3 No hidden defaults

Do not hide research-affecting defaults in:

- function signatures;
- constructors;
- helper functions;
- CLI code;
- environment variables;
- fallback branches.

A value that can change scientific behavior belongs in validated configuration.

### 7.4 No YAML inheritance tricks

Avoid:

- YAML anchors for semantic inheritance;
- implicit cascading configuration;
- hidden environment override chains;
- undocumented merging.

Configuration resolution must remain easy to inspect.

### 7.5 No CLI scientific overrides

The CLI should not become an alternative scientific configuration system.

Scientific values should come from the validated config.

CLI flags may control operational behavior where appropriate, for example:

- overwrite;
- verbosity;
- execution target;
- safe resume behavior.

They must not silently redefine the scientific protocol.

---

## 8. Constants and Magic Values

No run-affecting magic numbers or scattered constants.

Scientific parameters belong in config.

Intrinsic technical or mathematical constants that are truly not configurable must:

- have one owner;
- be named;
- be documented;
- not be duplicated.

Known categorical values belong in enums rather than string constants.

---

## 9. Strong Typing Contract

Strong typing is an architectural requirement, not decoration.

### 9.1 Central type ownership

`src/ctk_android/types.py` is the canonical home for reusable:

- semantic identifiers;
- constrained scalar types;
- domain records;
- reusable aliases;
- typed value objects.

Before defining a new type, search for an existing canonical owner.

### 9.2 Primitive boundary ban

Outside `types.py`, do not use raw primitive types as domain/service/scientific boundary contracts when a semantic project type exists or is required.

The recurring banned primitive boundary types are:

```text
float
int
str
object
Any
raw dict
```

Narrow third-party/local temporaries may exist inside adapters, but they must be converted at the boundary and must not leak through the repository.

### 9.3 Primitive bundles are not domain models

Do not pass scientific state as:

```text
tuple[int, float, str]
list[float]
dict[str, object]
```

when the values represent a real domain concept.

Use a typed record.

### 9.4 Reusable constrained aliases

Reusable constrained scalar aliases belong only in `types.py`.

Do not reproduce equivalents elsewhere.

This applies to patterns such as:

```text
NonNegativeInt
PositiveInt
NonNegativeFloat
PositiveFloat
UnitInterval
OpenUnitInterval
FiniteFloat
SignedInt
```

or project-specific equivalents.

### 9.5 Prefer typed records over wrapper-only classes

Do not create classes that exist only to wrap one primitive without adding meaningful semantics or validation.

Use aliases, frozen dataclasses, Pydantic models, or another justified typed record form as appropriate.

---

## 10. Enum Contract

Finite scientific and workflow choices must be represented by one canonical enum.

Examples include:

- dataset identities;
- client roles;
- split roles;
- experiment identities;
- model families;
- training regimes;
- exposure conditions;
- result states;
- failure/ineligibility reasons;
- promotion states.

Rules:

- never define two enums for the same concept;
- never scatter known categories as raw strings;
- map external/source-specific strings into canonical enums at boundaries;
- domain code operates on enums;
- use descriptive enum members.

### 10.1 `.value` restriction

Do not use repeated `.value` calls to escape the type system.

`.value` is allowed only at a real external serialization/interface boundary where a primitive representation is actually required.

Keep that boundary centralized.

---

## 11. No Type-Hiding Workarounds

Never make typing or architecture checks pass by hiding the problem.

Avoid:

```text
float(...)
int(...)
str(...)
cast(...)
Any
object
raw dict
```

when they are being used only to silence or bypass a type problem.

Fix the source type instead.

Broad casts are not architecture.

---

## 12. Paths

Repository paths must be centrally owned.

Do not scatter:

- hardcoded repository-relative strings;
- duplicated path construction;
- manual string concatenation;
- independently reconstructed output paths.

Use one path-resolution layer.

The same experiment identity must resolve to the same location everywhere.

---

## 13. CLI Contract

Keep the public CLI small.

The intended workflow surface is:

```text
doctor
preprocess
plan
smoke
run <experiment>
status
report
```

Post-hoc and extension analyses have their own commands (`posthoc`, `large-family`, `dose-extension`, `controls-extension`, `representation-extension`); each takes `--mode` and `--promote`, and `preprocess` takes repeatable `--mode` to restrict which modes' partitions are built (default: all).

Do not create one CLI command per scientific condition.

Do not duplicate experiment implementation behind separate commands.

### 13.1 CLI responsibilities

The CLI:

- parses user intent;
- loads validated configuration;
- invokes the correct workflow;
- reports status/errors.

The CLI must not contain scientific implementation logic.

### 13.2 Idempotency

Commands must be idempotent where practical.

Re-running the same command with the same frozen inputs must either:

- reuse provenance-valid artifacts;
- reproduce equivalent outputs;
- fail clearly because overwrite is required.

Never silently create inconsistent duplicate state.

### 13.3 Resume behavior

Long deterministic work should be resumable.

Reuse only artifacts whose provenance matches the requested computation.

Stale or incompatible artifacts must be invalidated or rebuilt safely.

---

## 14. Workflow Wiring

A feature is not implemented merely because a function exists.

Required functionality must be reachable from the real workflow.

For each public command, the path from CLI to the final scientific leaf must be inspectable.

Tests and Graphify must prove wiring.

Uncalled required code is incomplete.

---

## 15. Restore and Wire Before Deleting

Never delete code merely because one static analysis tool says it is unused.

Before deleting apparently unused functionality:

1. inspect the roadmap;
2. inspect the intended architecture;
3. search call sites;
4. inspect tests;
5. inspect the CLI/workflow path;
6. inspect fresh Graphify output;
7. determine whether the functionality is required but unwired;
8. determine whether it is genuinely obsolete or superseded.

**Required-but-unwired functionality must be restored/wired before considering deletion.**

Delete only when the functionality is genuinely:

- obsolete;
- duplicated;
- superseded;
- unreachable by design;
- outside the current roadmap.

---

## 16. Duplication and Dead Code

Continuously audit for:

- duplicate functions;
- duplicate enums;
- duplicate aliases;
- duplicate constants;
- duplicate scientific logic;
- duplicate configuration;
- duplicate path logic;
- old/new implementations side by side;
- dead redirect modules;
- compatibility wrappers;
- wrapper-only classes/modules;
- stale aliases;
- stale experiment names;
- TODO/FIXME markers representing unfinished required work.

Prefer one canonical implementation.

Do not keep legacy code “just in case.”

---

## 17. Compatibility Shims and Aliases

Do not introduce compatibility shims unless real compatibility is explicitly required.

Avoid:

- redirect modules;
- old-name aliases;
- duplicate APIs;
- temporary wrappers that become permanent;
- silent fallback to legacy behavior.

Migrate callers to the canonical implementation and remove the obsolete path.

---

## 18. Use Libraries Instead of Reimplementing Them

Prefer established libraries when they provide the needed behavior clearly and correctly.

Do not maintain custom implementations of standard functionality without a reason.

Before writing significant infrastructure, check whether an existing dependency already provides:

- statistics;
- validation;
- serialization;
- dataframe operations;
- metrics;
- plotting;
- graph analysis;
- CLI support;
- configuration validation.

A preferred library is not an excuse to add unnecessary dependencies. Use the simplest correct solution.

---

## 19. Scientific Isolation and Leakage

Implementation convenience never overrides the roadmap's information restrictions.

No test information may enter:

- training;
- scaling;
- calibration selection;
- eligibility;
- family selection;
- mechanism selection;
- hyperparameter selection.

Do not repair an infeasible scientific condition using information that would not have been available at that point in the real protocol.

Any leakage bug invalidates affected evidence.

---

## 20. Development, Confirmatory, and Exploratory Separation

These execution modes must remain visibly distinct.

Do not allow:

- development tuning on confirmatory outcomes;
- exploratory analyses to silently become confirmatory;
- confirmatory seeds to be reused casually for development;
- failed confirmatory results to be replaced with more favorable conditions.

If a result is exploratory, label it exploratory.

If a confirmatory requirement fails, record the failure or narrow the claim.

---

## 21. No Cherry-Picking

Never choose favorable:

- seeds;
- clients;
- families;
- datasets;
- thresholds;
- metrics;
- baselines;
- hyperparameters;
- experiment conditions;
- support cutoffs;
- statistical procedures

after seeing the result.

Negative results remain valid scientific evidence.

---

## 22. `outputs/` Contract

`outputs/` is the reproducible working-evidence workspace.

It may contain large, intermediate, diagnostic, invalidated, or non-publication artifacts.

Recommended structure:

```text
outputs/
├── preprocessing/
│   ├── source-audit/
│   ├── joined/
│   ├── identity/
│   ├── clients/
│   ├── families/
│   ├── partitions/
│   ├── cache/
│   └── representation/                 (EXT-REP feature caches and partitions, see 23.2)
│
├── plans/
│   ├── smoke/
│   ├── development/
│   └── confirmatory/
│
├── runs/
│   ├── smoke/
│   ├── development/
│   ├── confirmatory/
│   └── exploratory/
│
├── analysis/
│   ├── development/
│   └── confirmatory/
│
├── statistics/
│   └── confirmatory/
│
├── report/
│   ├── tables/
│   └── figures/
│
├── audit/
├── archive/
│   └── superseded/
├── logs/
└── temp/
```

### 22.1 What belongs in `outputs/`

Examples:

- preprocessing caches;
- joined row-level data;
- partition assignments;
- models/checkpoints needed for reproducibility;
- predictions/scores;
- smoke artifacts;
- development artifacts;
- exploratory artifacts;
- confirmatory raw run artifacts;
- logs;
- Graphify output;
- audit diagnostics;
- temporary report previews;
- invalidated/superseded evidence.

### 22.2 `outputs/` is not automatically disposable

Valid working evidence may be needed for:

- provenance;
- debugging;
- reproducibility;
- protocol amendments;
- preservation of superseded results.

Do not delete evidence merely because it is not manuscript evidence.

---

## 23. Standard Run Contract

Each experiment run should follow one consistent artifact contract.

A typical run:

```text
seed-000/
├── manifest.json
├── status.json
├── validation.json
├── exposure.parquet
├── thresholds.parquet
├── metrics/
│   ├── summary.parquet
│   ├── clients.parquet
│   ├── families.parquet
│   └── operating-points.parquet
├── scores/
├── models/
└── logs/
```

Do not invent a completely different layout for each experiment.

### 23.1 Manifest

The run manifest should contain enough information to reproduce and audit the run, including as applicable:

- experiment identity;
- execution mode;
- seed;
- source-data fingerprints;
- partition identity;
- client support;
- family support/eligibility;
- model/scenario parameters;
- relevant configuration fingerprints;
- code revision;
- software environment;
- artifact paths;
- completion/result status.

---

## 24. `results/` Contract

`results/` contains **frozen manuscript/chapter evidence only**.

It is not a generic output directory.

Recommended structure:

```text
results/
├── README.md
├── manifest.json
├── provenance/
├── evidence/
├── statistics/
├── gates/
├── tables/
├── extension-b/
└── figures/
```

### 23.2 Extension-b mode

`ExecutionMode.EXTENSION_B` (`extension-b`) is a second prospective extension, separate from `extension` (seeds 200 to 209, unchanged). Seeds (`configs/project.yaml`) are 300 to 309 (large-family), 310 to 319 (exact dose), 320 to 329 (controls) and 330 to 339 (EXT-REP, `extension_representation`); `ProjectSeeds.for_design` and `Config.seeds_for(experiment, mode)` select them by experiment design. Seed roles must stay disjoint.

Experiments (`configs/experiments.yaml`):

- `large-family-set-1..4` (family sets `large-1..4`, standard design; listed in `extension_b_experiments`, so they run in `extension-b`);
- `exact-effective-dose-primary` / `-replication` (`design: exact-dose`, eligibility profile `dose`: peer_min_fit 200, federation_min_test 50);
- `placebo-robust-primary` / `-replication` (`design: placebo-robust`, learner `fedavg` only);
- `representation-r0..r3` (`design: representation`, primary family set, salt 0, learners local/central/fedavg, conditions peer-present, family-absent-everywhere, full-exposure; also listed for `development`): R0 `lamda-static` restricted to the overlap, R1 `mcndroid-static`, R2 `call-graph`, R3 `report-json`.

Arm definitions:

- exact dose: `exact-dose` arms replace rows so each target pair's peers hold exactly `d` fit rows of the hidden family (`exact_dose_levels: [0, 10, 25, 50, 100, 200]`), zero at the target, total training volume unchanged; dose 0 must equal the family-absent rows. Learners: central and fedavg.
- placebo: for each hidden family a distinct unhidden placebo family (at least `placebo_min_malware_rows`=400 malware rows, closest peer fit count, ties by name) supplies the same per-client row counts as the hidden family had in the peer-present arm (reallocated across clients when a client lacks rows); the hidden family stays absent everywhere.
- robust aggregation (fedavg, placebo-robust only): `Aggregation.TRIMMED_MEAN` (drop `robust_trim_per_side`=1 lowest and highest per coordinate) and `COORDINATE_MEDIAN` replace the weighted average of client states, alongside the plain fedavg arm.
- each design records validation checks (`exact-dose-realised-at-peers`, `exact-dose-zero-at-target`, `dose-zero-rows-equal-absent-rows`, `placebo-counts-match-hidden-family`, `placebo-family-unhidden-and-unique`, `placebo-arm-hidden-family-absent`).

Determinism: exact-dose draws use `SeedSequence([seed, salt, 991])` (`DrawStream.DOSE`); placebo row draws use stream 992 (`DrawStream.PLACEBO`). `DataConfig.stable_json` excludes the `dose` profile, so adding these designs does not change existing partition fingerprints; design fingerprints add the profile and design parameters only for non-standard designs.

Commands and outputs (written to `outputs/analysis/<mode>/`, promoted only with `--promote`):

- `posthoc [--mode confirmatory] --promote` writes `ctk-heterogeneity-components`, `aggregate-metric-masking`, `negative-transfer-decomposition` (parquet) and copies them, plus CSV, into `results/evidence/` and `results/tables/`, appending to the manifest. Promotion is blocked unless the mode is confirmatory and all runs completed.
- `large-family`, `dose-extension`, `controls-extension` (each `--mode extension-b --promote`) write the tables listed under `results/extension-b/` (parquet and CSV) with a `code.json` / `dose-code.json` / `controls-code.json` provenance record. Promotion is blocked for other modes and for incomplete or stale runs.

EXT-REP (representation replication, seeds 330 to 339): asks whether the family-specific limits seen with LAMDA static features persist under other representations of the same apps. All four experiments use only the rows present in LAMDA and in all three McNdroid representations (matched by sha256), so R0 to R3 differ in features alone. Priority (hiddad, gappusin, revmob), contrast (leadbolt, airpush, dowgin) and separate (adwo) families, the focus family (hiddad) and the minimum prevalence 0.01 are set in `configs/experiments.yaml`. Verdicts: H-REP-1 (R1 CTK lower bound above `ctk_min_gain`), H-REP-2 (hiddad), and an interpretation (`rep1-met-rep2-met`, `rep1-met-rep2-not-met`, `rep1-not-met`, `undetermined`).

- `representation-preprocess [--mode ...]` (default modes: development and extension-b) must run before `plan extension-b`: it builds `outputs/preprocessing/representation/` (overlap table and manifest, aligned row identities, source inventory and fingerprint, `features-r0.npy` and `features-r1.npy`, call-graph and report-JSON as CSR files `graph-*`/`json-*`, all 17,483 report-JSON columns) and per-seed `partitions/<run>/` (assignments, controlled and natural pairs). Compact dtypes: R0/R1 feature caches as saved by `cache.save_features`; call-graph CSR data float32; report-JSON CSR data float16 (signed log), int32 indices, int64 indptr. Planning and runs fail with `representation namespace missing` if it was not run. Stages are fingerprinted and reused unless `--overwrite`.
- `representation-extension --mode extension-b [--promote]` writes `outputs/analysis/extension-b/representation-{run-index,seed-effects,effects,levels,verdicts,eligibility}.parquet`; `--promote` copies them (parquet and CSV) to `results/extension-b/` with `representation-code.json`, blocked for incomplete or stale runs.
- Run order: `doctor`, `preprocess`, `representation-preprocess`, `plan extension-b`, `run representation-r0..r3 --mode extension-b`, `representation-extension --mode extension-b --promote`. Timings are not measured yet.

Determinism and limitations (Amendment A3): R2 and R3 are standardised, and R3 columns are selected (share of positive values at least 0.01), by each trained model from exactly its own training rows: a local model from its client's rows, a central or FedAvg model from the pooled rows of its arm (the federated sufficient statistics); fine-tuning keeps the parent model's transform. The transform is applied unchanged to calibration and test rows; no statistic uses rows a model is not trained on, and there is no whole-overlap pre-filter. R0 and R1 use the cached static features as they are (no transform). McNdroid features are the provider's processed `init_2013` data, so provider-side feature selection is outside our control and representations differ in dimensionality as well as content; the overlap is smaller than the LAMDA population.

Original-artefact guarantee: these commands (including `representation-preprocess`, which writes only under `outputs/preprocessing/representation/`) only add files; they never rewrite existing confirmatory or `extension` evidence (the manifest gains entries only), and `results/extension-b/` is never pooled with the original campaign.

### 24.1 Allowed content

`results/` may contain:

- aggregate structured evidence;
- final effect estimates;
- confidence intervals;
- frozen statistical outputs;
- claim/gate status;
- publication tables;
- publication figures;
- compact provenance required to regenerate/verify them.

### 24.2 Forbidden content

Do not put the following in `results/`:

- raw datasets;
- joined row-level datasets;
- row-level predictions;
- ordinary training checkpoints;
- development runs;
- smoke runs;
- temporary analysis;
- debug logs;
- Graphify output;
- Semgrep output;
- caches;
- profiler artifacts;
- exploratory junk;
- manually edited numerical artifacts.

### 24.3 Promotion-only writing

Normal workflows write to `outputs/`.

Writing into `results/` must occur only through the controlled evidence-promotion path after:

- run validation;
- confirmatory completion;
- frozen statistical analysis;
- gate evaluation;
- provenance checks.

Do not allow individual experiment code to write directly into `results/`.

### 24.4 Publication regeneration

Final tables and figures must regenerate from the frozen structured evidence.

Do not hand-edit numbers in publication tables or figures.

---

## 25. No Claims Infrastructure

Do not create a software claim registry.

Forbidden examples include:

```text
claim_registry
claims/
claim-gates/
claim database
claim service
```

Scientific claim logic belongs in the roadmap and in lightweight evidence/gate outputs where required.

Do not turn scientific prose into an application subsystem.

---

## 26. No Generated Narrative Markdown Reports

Code must not generate long narrative Markdown research reports.

The `report` workflow should generate machine-readable evidence and publication artifacts such as:

- Parquet;
- CSV;
- JSON;
- figures;
- tables.

Human scientific writing remains human-authored in the appropriate document.

---

## 27. No Docker Requirement

Do not introduce Docker, Docker Compose, or container orchestration as a repository requirement.

The project must remain runnable in the normal supported development environment without containerization.

Do not add Docker merely for perceived reproducibility.

---

## 28. Testing Strategy

Tests are part of the architecture.

Use the following layers as appropriate:

### 28.1 Unit tests

Validate small isolated behavior.

### 28.2 Integration tests

Validate real module interactions and artifact boundaries.

### 28.3 Protocol/scientific invariant tests

These may live in a dedicated test area or the relevant integration/architecture area, but they must directly test scientific invariants.

### 28.4 Architecture tests

Enforce repository contracts that ordinary behavior tests will not catch.

### 28.5 End-to-end tests

A lightweight real smoke path must verify the full workflow.

### 28.6 Real-data compatibility

A loader is not correct merely because synthetic fixtures pass.

Where data is available, adapters must be checked against actual source schema/sample metadata.

---

## 29. Mandatory Architecture Checks

Tests/Semgrep should fail on applicable violations including:

- primitive function/method boundary annotations outside `types.py`;
- primitive domain fields outside `types.py`;
- `Any`;
- `object`;
- raw `dict` domain IO;
- duplicate aliases;
- aliases outside `types.py`;
- duplicate enums;
- `.value` leakage;
- pointless primitive wrappers;
- broad casts;
- hardcoded known categorical strings;
- hardcoded repository paths;
- duplicate path construction;
- unauthorized extra YAML/YML;
- direct YAML parsing outside the config layer;
- magic scientific numbers;
- duplicated constants;
- stale compatibility shims;
- stale aliases;
- wrapper-only classes/modules;
- generic dumping-ground modules;
- unfinished required TODO/FIXME;
- forbidden claim infrastructure;
- Docker;
- CLI/workflow disconnections;
- Graphify reachability regressions;
- dataset schema drift;
- invalid source mappings;
- test-data leakage.

Do not satisfy these checks with broad allowlists.

---

## 30. Static Analysis

Use the project static-analysis stack consistently:

- Ruff;
- Pyright;
- Semgrep.

Do not weaken a checker because it identifies a real problem.

Do not add broad:

- ignores;
- suppressions;
- exclusions;
- allowlists.

Fix the implementation.

A narrow exception is acceptable only when it represents a genuine unavoidable boundary and is documented precisely.

---

## 31. Test Runtime

Keep the normal development verification suite around five minutes or less where practical.

Improve runtime through:

- better fixtures;
- caching;
- parallelism;
- smaller deterministic integration samples;
- efficient setup reuse.

Do not achieve speed by removing meaningful verification.

Long confirmatory experiments are not part of the normal test suite.

---

## 32. Graphify Contract

Graphify is mandatory for significant architecture/wiring audits.

### 32.1 Always generate fresh output

Do not rely on old Graphify artifacts when auditing the current working tree.

### 32.2 Audit every CLI workflow

For each public CLI command, record at least:

```text
CLI command
→ workflow
→ major modules
→ reachable callable count
→ reachable leaf count
→ maximum depth
→ CLI-to-leaf paths
```

Also inspect:

- unexpected disconnected code;
- duplicate paths;
- stale routes;
- unreachable required functionality;
- accidental alternative implementations.

### 32.3 Count comparison

Compare callable/reachable/leaf counts before and after substantial architecture changes when useful.

Unexpected loss of reachability must be investigated.

Do not celebrate lower counts if functionality was accidentally disconnected.

### 32.4 Wiring proof

Graphify is not a replacement for tests.

Use both:

- Graphify for structural reachability;
- tests for behavioral correctness.

---

## 33. Audit Matrix Contract

`docs/Audit Matrix.md` is the main human-readable implementation audit.

Use statuses such as:

```text
PASS
PARTIAL
MISSING
BLOCKED
```

### 33.1 Fix findings

`PARTIAL`, `MISSING`, and fixable `BLOCKED` items are not merely documentation outcomes.

Fix them when the required behavior is clear.

Do not leave an issue unfixed simply because the matrix successfully identified it.

### 33.2 Ambiguity

If genuine user/scientific confirmation is required:

- record the issue;
- continue all independent audit work;
- defer only the ambiguous decision;
- do not block unrelated audit progress.

### 33.3 Command-by-command wiring

For every public CLI command, the audit must document the actual downstream call path and what the major methods do.

Count methods/callables from the CLI entry point through final leaves where practical.

---

## 34. Repeated Audit Passes

Substantial work requires repeated verification, not a one-pass check.

### Pass A — Source and architecture

Inspect:

- repository tree;
- types;
- enums;
- config ownership;
- paths;
- primitive leaks;
- `.value`;
- casts;
- magic values;
- duplication;
- TODO/FIXME;
- shims;
- generic modules;
- dead code;
- wiring.

### Pass B — Tools and tests

Run the applicable:

- Ruff;
- Pyright;
- Semgrep;
- unit tests;
- integration tests;
- architecture/protocol tests;
- E2E smoke;
- fresh Graphify;
- dependency/call-path inspection.

### Pass C — Independent re-audit

After fixes:

- repeat searches;
- repeat critical checks;
- compare Graphify state;
- inspect Git diff;
- inspect repository tree;
- check for accidental drift caused by the fixes.

Repeat again if findings remain.

Do not stop because one edited test passes.

---

## 35. Fix Problems at the Source

Never hide a real issue using:

- casts;
- wrappers;
- ignores;
- suppressions;
- broad allowlists;
- disabled checks;
- weakened Pyright;
- weakened Ruff;
- weakened Semgrep;
- skipped tests;
- fake mocks;
- compatibility shims;
- silent fallbacks.

If a validator detects a real implementation defect, fix the implementation.

---

## 36. Relevant Pre-Existing Problems

Do not dismiss a relevant defect merely because it predates the current change.

Fix pre-existing issues when they materially affect:

- the workflow being modified;
- its dependency path;
- architecture consistency;
- typing boundaries;
- wiring;
- scientific correctness;
- reproducibility;
- configuration;
- tests;
- maintainability;
- unnecessary code volume.

Do not turn every task into an unlimited repository-wide refactor.

Unrelated non-blocking imperfections remain out of scope.

---

## 37. Long-Running Work

Safe deterministic long-running work should run in the background when possible.

Examples:

- preprocessing;
- large source scans;
- deterministic cache construction;
- long experiment stages.

While such work runs:

- continue independent audit/implementation work;
- do not stare at the process;
- do not repeatedly poll without reason.

Return to the process when its result is actually needed.

---

## 38. Performance and Resource Discipline

Avoid unnecessary recomputation.

Use:

- deterministic caching;
- resumable stages;
- efficient dataframe operations;
- vectorized/library implementations;
- controlled parallelism.

Do not trade scientific correctness for speed.

Do not load entire datasets unnecessarily when streaming/scanning is sufficient.

GPU use is allowed where appropriate, but code must not silently assume CUDA unless the project explicitly requires it.

---

## 39. Logging and Observability

Use meaningful structured logging.

Where relevant, expose:

- workflow;
- stage;
- dataset;
- client/domain;
- family;
- seed;
- experiment;
- configuration identity;
- compute device;
- worker count;
- counts;
- cache reuse;
- progress;
- timings;
- throughput;
- artifact path;
- warnings;
- failures;
- final status.

Do not produce row-level log noise.

Never silently:

- swallow errors;
- change configuration;
- repair invalid scientific state;
- substitute missing evidence;
- manufacture success.

---

## 40. Failure Semantics

Failure must be explicit.

Do not convert:

- missing data;
- invalid schema;
- insufficient support;
- failed validation;
- leakage;
- infeasible experiment state

into an empty “successful” artifact.

Use typed status/failure reasons.

A failed scientific condition can still be a valid recorded outcome.

---

## 41. Reproducibility

Every important run must be reproducible from frozen inputs.

Record as applicable:

- source fingerprints;
- config fingerprints;
- seed;
- partition identity;
- experiment identity;
- model/scenario parameters;
- software environment;
- code revision;
- artifact lineage;
- result status.

Re-running deterministic preprocessing with identical inputs should reproduce the same data contract.

Re-running stochastic experiments with the same seeds should reproduce equivalent metrics within the expected deterministic-library tolerance.

---

## 42. Clean-Environment Verification

Before final manuscript evidence is considered frozen, verify the complete workflow from a clean environment using:

- documented dependencies;
- the committed configuration;
- the external raw data;
- documented commands.

The final evidence must not depend on hidden local state.

---

## 43. Artifact Reuse

Reuse an artifact only when its provenance proves compatibility.

Do not reuse an artifact merely because:

- the filename matches;
- it is recent;
- it exists;
- it came from a similar experiment.

Compatibility must include the relevant source/config/code/seed/experiment identity.

When compatibility fails, rebuild safely.

---

## 44. Scientific Methodology Changes

When implementation or data inspection reveals a real scientific ambiguity or defect:

1. inspect the real evidence;
2. inspect relevant literature if needed;
3. check established implementations/libraries;
4. determine the strongest scientifically defensible correction;
5. do not choose a method because it produces nicer results;
6. update code/config/tests/reporting consistently;
7. update `docs/Roadmap.md` surgically if the scientific protocol changes;
8. record the engineering/scientific decision where appropriate.

Do not silently resolve methodology inside code.

---

## 45. Comments and Docstrings

Comments and docstrings must add useful information.

Do not add:

- filler commentary;
- obvious restatements of code;
- conversational AI-style explanations;
- “generated” language;
- excessive section banners;
- speculative future notes.

Explain only:

- non-obvious invariants;
- scientific restrictions;
- boundary assumptions;
- important implementation reasoning.

Code should remain readable without narration.

---

## 46. Git Discipline

Use Git throughout development.

### 46.1 Commits

Prefer multiple coherent commits rather than one enormous mixed commit.

Each commit should represent a meaningful unit of work where practical.

### 46.2 Preserve unrelated work

Before modifying a repository with existing local changes:

- inspect `git status`;
- inspect the diff;
- identify user-owned changes;
- preserve unrelated edits.

Do not wipe or overwrite local work to simplify the task.

### 46.3 No destructive blanket repair

Do not use broad checkout/reset/revert operations as a substitute for carefully fixing changed files.

Edit surgically.

If restoring content is necessary, preserve intentional local modifications.

### 46.4 Encoding and line endings

Do not rewrite a file in a way that changes its encoding or line endings without need.

For large mechanical changes, inspect each affected file for accidental corruption.

### 46.5 Final Git audit

Before finishing substantial work, inspect:

```text
git status
git diff
recent commit history
```

Confirm that:

- only intended files changed;
- no unrelated content changed;
- no generated junk is tracked;
- no local user work was lost.

---

## 47. No AI Authorship

Never add AI/agent authorship.

Do not add:

- ChatGPT;
- Claude;
- Copilot;
- OpenAI;
- Anthropic;
- an agent;
- automated-system authorship

as an author or co-author.

Never add AI `Co-authored-by` trailers.

Do not add:

- AI attribution trailers;
- “generated by” metadata;
- automated co-author metadata.

The human repository author remains the author.

---

## 48. `.gitignore` Is Part of Definition of Done

Whenever a change introduces new:

- outputs;
- caches;
- logs;
- model artifacts;
- profiling data;
- temporary files;
- Graphify data;
- Semgrep output;
- local environments;
- machine-specific state;
- downloaded archives;
- raw data;

audit `.gitignore`.

It should exclude applicable:

- virtual environments;
- Python caches;
- test/tool caches;
- local secrets;
- machine configuration;
- temporary static-analysis output;
- temporary Graphify output;
- generated workspace artifacts according to repository policy;
- raw/private datasets where appropriate;
- runtime/model caches;
- editor/OS files.

Do not accidentally ignore:

- required source;
- required documentation;
- small reproducibility manifests;
- final manuscript evidence that is intentionally versioned.

Do not use `.gitignore` to conceal an architectural problem.

---

## 49. Files That Must Not Be Committed

Do not commit:

- secrets;
- API keys;
- credentials;
- personal machine configuration;
- Python/tool caches;
- temporary Graphify output;
- temporary Semgrep output;
- duplicated raw datasets;
- unnecessary checkpoints;
- profiler junk;
- debug output;
- unrelated generated archives;
- AI authorship metadata.

Repository-specific policy decides which `outputs/` and `results/` artifacts are tracked.

---

## 50. Experiment Naming

Use descriptive experiment identities.

Prefer lowercase kebab-case.

Examples:

```text
controlled-exposure
peer-dose-response
natural-scarcity
model-family-replication
operating-point-sensitivity
```

Avoid opaque identifiers such as:

```text
exp1
e2
b1
regime-a
test-final-v3
```

Names should describe the scientific condition without requiring a lookup table.

---

## 51. No Experiment-Specific Copy-Paste Pipelines

Experiments should be configuration-driven through shared implementation.

Do not implement:

```text
run_experiment_a()
run_experiment_b()
run_experiment_c()
```

when the only difference is scientific configuration.

Shared code should execute validated experiment definitions.

---

## 52. Report Generation

The `report` workflow must operate from saved structured evidence.

It must not retrain models.

It must not silently rerun experiments.

It should regenerate:

- tables;
- figures;
- compact evidence summaries.

Publication outputs must trace back to saved structured parents.

---

## 53. Agent/Automation Rules

When a coding agent works in this repository, it must:

1. read `docs/Roadmap.md`;
2. read `docs/technical_docs.md`;
3. inspect the actual repository before proposing architecture;
4. inspect current Git state;
5. preserve existing intentional changes;
6. avoid inventing new architecture;
7. avoid adding folders merely “for cleanliness”;
8. avoid Docker;
9. avoid claim infrastructure;
10. avoid generated narrative Markdown reports;
11. avoid extra configuration files;
12. avoid duplicate implementations;
13. verify real workflow wiring;
14. use tests and fresh Graphify;
15. fix partial/missing implementation when the requirement is clear;
16. avoid weakening tests/checkers;
17. keep changes within scope;
18. avoid many agents independently implementing the same area;
19. never add AI attribution/authorship.

If the repository is already compliant, re-audit and prove compliance without unnecessary churn.

---

## 54. Audit-Only Tasks

When a task is explicitly audit-only:

- inspect;
- measure;
- classify;
- report.

Do not modify implementation until modification is authorized.

When the task is audit-and-fix:

- audit first;
- fix all clear `PARTIAL`, `MISSING`, or broken items;
- re-run the audit after fixes.

Do not confuse audit evidence with implementation.

---

## 55. Experiment Safety During Engineering Audits

Do not run expensive or confirmatory experiments during a code-quality audit unless the task explicitly requires them.

Allowed when relevant:

- static inspection;
- preprocessing validation;
- tiny smoke tests;
- minimal deterministic integration runs;
- schema checks;
- real-data compatibility checks.

Confirmatory execution must remain controlled by the scientific execution plan.

---

## 56. Forbidden Pattern Summary

The following should be treated as repository smells and should fail review or automated checks where practical:

```text
unnecessary extra YAML/YML
generic utils/helpers/common/misc/core dumping ground
claim_registry or claims subsystem
top-level audit framework
Dockerfile/docker-compose requirement
generated narrative Markdown reports
hardcoded experiment categories scattered through code
hardcoded research values outside config
hardcoded repository paths
raw dict domain IO
Any/object used to avoid typing
primitive boundary leakage outside types.py
duplicate aliases/enums/constants
repeated enum .value escapes
pointless float()/int()/str() wrappers
broad casts masking bad types
duplicate old/new implementations
unnecessary compatibility shims
dead redirect modules
wrapper-only modules/classes
required but unwired functionality
deleting code solely because a static tool says unused
test/calibration leakage
post-hoc scientific rule changes
successful-seed selection
performance-based condition selection
row-level/raw data promoted into results/
logs in results/
smoke outputs in results/
development artifacts in results/
hand-edited numerical evidence
AI-style filler comments/docstrings
AI/agent co-authorship
destructive Git cleanup of user changes
silent fallback behavior
validation failure converted into success
```

---

## 57. Definition of Done for a Code Change

A change is not complete because one test passes.

As applicable, definition of done requires:

- requested behavior implemented;
- roadmap semantics preserved;
- technical contract preserved;
- no primitive/type violations;
- enums remain canonical;
- config remains centralized;
- no new magic values;
- paths remain centralized;
- required code is actually wired;
- no accidental duplicate implementation;
- relevant unit tests pass;
- relevant integration tests pass;
- relevant architecture/protocol tests pass;
- E2E smoke passes where applicable;
- Ruff passes;
- Pyright passes;
- Semgrep passes;
- fresh Graphify shows expected reachability;
- no relevant TODO/FIXME remains;
- output/result boundaries are respected;
- `.gitignore` is still correct;
- Git diff/status are intentional;
- repeated audit passes find no unresolved relevant issue.

---

## 58. Definition of Done for an Experiment Workflow

An experiment workflow is not complete until:

- the experiment is planned deterministically;
- inputs are provenance-valid;
- the run is reproducible;
- the expected artifact contract is complete;
- validation passes;
- failures are explicit;
- metrics derive from saved evidence;
- statistical analysis uses the declared statistical unit;
- report artifacts regenerate from saved outputs;
- no manual numerical edits are required.

For confirmatory evidence additionally require:

- frozen protocol/config;
- untouched confirmatory seed roles;
- no post-hoc condition changes;
- all planned valid seeds completed or structurally excluded before outcome inspection;
- frozen statistical analysis;
- gate status;
- controlled promotion into `results/`.

---

## 59. Final Engineering Priority Order

When trade-offs arise, use this priority:

1. scientific correctness;
2. leakage prevention;
3. reproducibility;
4. explicit provenance;
5. correct workflow wiring;
6. strong typing;
7. deterministic behavior;
8. testability;
9. simplicity;
10. performance;
11. convenience.

Never sacrifice a higher-priority item to make a lower-priority item easier.

---

## 60. Final Rule

When uncertain whether to add more architecture, configuration, wrappers, helpers, registries, compatibility layers, reports, or infrastructure:

**default to not adding it.**

First prove that the current compact architecture cannot express the required behavior cleanly.

The project should grow only when the scientific or engineering requirement actually demands it.
