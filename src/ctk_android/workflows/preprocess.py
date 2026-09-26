import numpy as np
import polars as pl

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data import partitions, preparation, representations, sources
from ctk_android.data.cache import (
    combine_fingerprints,
    fingerprint_file,
    is_reusable,
    load_features,
    read_record,
    save_features,
    write_provenance,
    write_record,
    write_table,
)
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    DatasetName,
    DetailMessage,
    EligibilityProfile,
    ErrorMessage,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    FailureReason,
    FamilySetName,
    Grouping,
    LibraryOption,
    LogEvent,
    LogField,
    Stage,
    ValidationCheck,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    Directory,
    ExperimentSpec,
    FamilySetDocument,
    File,
    Fingerprint,
    IdentitiesTable,
    IncludeDesigns,
    LabelledTable,
    LamdaCounts,
    LamdaSchema,
    LargeFamilySelection,
    LinkageCounts,
    LinkageSchema,
    ModeSelection,
    Overwrite,
    PartitionKey,
    PartitionManifest,
    Provenance,
    Reusable,
    Reused,
    RoleSeries,
    SourceInventory,
    StageReport,
    ValidationDocument,
    ValidationRecord,
)


def required_partition_keys(
    config: Config,
    modes: ModeSelection = tuple(ExecutionMode),
    include_designs: IncludeDesigns = True,
) -> list[PartitionKey]:
    keys: list[PartitionKey] = []
    for name, spec in config.experiments.experiments.items():
        if spec.representation is not None:
            continue
        if spec.design is not ExperimentDesign.STANDARD and not include_designs:
            continue
        _keys_for_experiment(config, name, spec, modes, keys)
    return sorted(keys, key=lambda key: (key.seed, key.salt, key.grouping, key.profile))


def _keys_for_experiment(
    config: Config,
    name: ExperimentName,
    spec: ExperimentSpec,
    modes: ModeSelection,
    keys: list[PartitionKey],
) -> None:
    for mode in modes:
        if config.experiments.runs_in(name, mode):
            for seed in config.seeds_for(name, mode):
                for salt in spec.salts:
                    key = PartitionKey(
                        seed=seed, salt=salt, grouping=spec.grouping, profile=spec.eligibility
                    )
                    if key not in keys:
                        keys.append(key)


def record_validations(
    paths: Paths, records: list[ValidationRecord], directory: Directory, stage: Stage
) -> None:
    write_record(paths.audit_file(directory), ValidationDocument(validations=tuple(records)))
    failed = [record for record in records if not record.passed]
    for record in records:
        report = logs.info if record.passed else logs.warning
        report(
            LogEvent.VALIDATION_PASSED if record.passed else LogEvent.VALIDATION_FAILED,
            {
                LogField.STAGE: stage,
                LogField.CHECK: record.check,
                LogField.PASSED: record.passed,
                LogField.DETAIL: record.detail,
            },
        )
    if failed:
        logs.error(
            LogEvent.STAGE_FAILED,
            {
                LogField.STAGE: stage,
                LogField.CHECK: failed[0].check,
                LogField.DETAIL: failed[0].detail,
                LogField.FAILED: len(failed),
            },
        )
        raise CtkError(
            FailureReason.SCHEMA_MISMATCH,
            ErrorMessage.STAGE_VALIDATION.format(
                stage=stage, check=failed[0].check, detail=failed[0].detail
            ),
        )


def reuse_stage(
    paths: Paths, directory: Directory, provenance: Provenance, overwrite: Overwrite
) -> Reusable:
    reusable = not overwrite and is_reusable(paths.provenance_file(directory), provenance)
    if reusable:
        logs.info(
            LogEvent.STAGE_REUSED,
            {
                LogField.STAGE: provenance.stage,
                LogField.PATH: f"{directory}",
                LogField.REUSED: True,
            },
        )
    return reusable


def stage_report(directory: Directory, provenance: Provenance, reused: Reused) -> StageReport:
    return StageReport(
        stage=provenance.stage,
        directory=directory,
        reused=reused,
        fingerprint=provenance.inputs,
    )


def finish_stage(
    paths: Paths, directory: Directory, provenance: Provenance, watch: Stopwatch
) -> StageReport:
    write_provenance(paths.provenance_file(directory), provenance)
    logs.info(
        LogEvent.STAGE_BUILT,
        {
            LogField.STAGE: provenance.stage,
            LogField.PATH: f"{directory}",
            LogField.REUSED: False,
            LogField.SECONDS: watch.seconds(),
        },
    )
    return stage_report(directory, provenance, reused=False)


def _known_inventory(paths: Paths, dataset: DatasetName) -> SourceInventory:
    path = paths.source_file(dataset, Artifact.INVENTORY)
    return read_record(path, SourceInventory) if path.is_file() else SourceInventory(entries=())


def source_audit(paths: Paths, config: Config, overwrite: Overwrite) -> StageReport:
    watch = Stopwatch()
    lamda_scan = sources.fingerprint_lamda(
        paths, config.data, _known_inventory(paths, DatasetName.LAMDA)
    )
    az_scan = sources.fingerprint_androzoo(paths, _known_inventory(paths, DatasetName.ANDROZOO))
    lamda_fp, az_fp = lamda_scan.fingerprint, az_scan.fingerprint
    config_fp = config.data.stable_fingerprint()
    provenance = Provenance(
        stage=Stage.SOURCE_AUDIT,
        inputs=combine_fingerprints(sources.sources_fingerprint(lamda_fp, az_fp), config_fp),
    )
    if reuse_stage(paths, paths.linkage_dir, provenance, overwrite):
        return stage_report(paths.linkage_dir, provenance, reused=True)

    lamda = sources.load_lamda(paths, config.data)
    azoo = sources.scan_androzoo(paths, lamda.metadata[Column.SHA256])
    result = preparation.join_sources(lamda.metadata, azoo)
    validations = [*sources.validate_lamda(lamda, config.data), *result.validations]

    for dataset, scan in ((DatasetName.LAMDA, lamda_scan), (DatasetName.ANDROZOO, az_scan)):
        write_record(paths.source_file(dataset, Artifact.FINGERPRINT), scan.fingerprint)
        write_record(paths.source_file(dataset, Artifact.INVENTORY), scan.inventory)
    write_record(
        paths.source_file(DatasetName.LAMDA, Artifact.SCHEMA),
        LamdaSchema(
            release=config.data.lamda_release,
            feature_count=lamda.features.shape[1],
            metadata_columns=tuple(Column(name) for name in lamda.metadata.columns),
            non_binary_cells_binarized=lamda.non_binary_cells,
            negative_cells=lamda.negative_cells,
        ),
    )
    write_record(
        paths.source_file(DatasetName.LAMDA, Artifact.COUNTS),
        LamdaCounts(
            rows=lamda.metadata.height,
            malware=lamda.metadata.filter(pl.col(Column.LABEL) == 1).height,
            benign=lamda.metadata.filter(pl.col(Column.LABEL) == 0).height,
        ),
    )
    write_record(
        paths.source_file(DatasetName.ANDROZOO, Artifact.SCHEMA),
        LinkageSchema(columns=tuple(Column(name) for name in azoo.columns)),
    )
    write_record(
        paths.source_file(DatasetName.ANDROZOO, Artifact.COUNTS),
        LinkageCounts(linked_rows=azoo.height),
    )
    write_table(lamda.metadata, paths.source_file(DatasetName.LAMDA, Artifact.METADATA))
    write_table(azoo, paths.linkage_file(Artifact.HASH_LINKAGE))
    write_table(result.unmatched, paths.linkage_file(Artifact.UNMATCHED))
    record_validations(paths, validations, paths.linkage_dir, Stage.SOURCE_AUDIT)
    return finish_stage(paths, paths.linkage_dir, provenance, watch)


def join_stage(paths: Paths, upstream: StageReport, overwrite: Overwrite) -> StageReport:
    watch = Stopwatch()
    directory = paths.stage_dir(Stage.JOINED)
    provenance = Provenance(stage=Stage.JOINED, inputs=upstream.fingerprint)
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    metadata = pl.read_parquet(paths.source_file(DatasetName.LAMDA, Artifact.METADATA))
    linked = pl.read_parquet(paths.linkage_file(Artifact.HASH_LINKAGE))
    result = preparation.join_sources(metadata, linked)
    write_table(result.joined, paths.stage_file(Stage.JOINED, Artifact.DATASET))
    record_validations(paths, list(result.validations), directory, Stage.JOINED)
    return finish_stage(paths, directory, provenance, watch)


def clients_stage(
    paths: Paths, config: Config, upstream: StageReport, overwrite: Overwrite
) -> StageReport:
    watch = Stopwatch()
    directory = paths.stage_dir(Stage.CLIENTS)
    provenance = Provenance(stage=Stage.CLIENTS, inputs=upstream.fingerprint)
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    joined = pl.read_parquet(paths.stage_file(Stage.JOINED, Artifact.DATASET))
    assignments = preparation.assign_clients(joined, config.data)
    lamda = sources.load_lamda(paths, config.data)
    positions = (
        lamda.metadata.select(Column.SHA256)
        .with_row_index(Column.ROW)
        .join(assignments.select(Column.SHA256), on=Column.SHA256)[Column.ROW]
        .to_numpy()
    )
    save_features(paths.cache_file(Artifact.FEATURES), lamda.features[positions])
    write_table(
        assignments.with_row_index(Column.ROW),
        paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS),
    )
    support = preparation.client_support(assignments)
    for row in support.iter_rows(named=True):
        logs.info(
            LogEvent.CLIENTS_ASSIGNED,
            {
                LogField.CLIENT: row[Column.CLIENT],
                LogField.ROWS: row[Column.ROWS],
                LogField.COUNT: row[Column.MALWARE_ROWS],
            },
        )
    write_table(support, paths.stage_file(Stage.CLIENTS, Artifact.SUPPORT))
    present = {ClientId(name) for name in support[Column.CLIENT].to_list()}
    record_validations(
        paths,
        [
            ValidationRecord(
                check=ValidationCheck.CLIENTS_COMPLETE,
                passed=present == set(ClientId),
                detail=DetailMessage.CLIENTS_PRESENT.format(clients=sorted(present)),
            )
        ],
        directory,
        Stage.CLIENTS,
    )
    return finish_stage(paths, directory, provenance, watch)


def identity_stage(paths: Paths, upstream: StageReport, overwrite: Overwrite) -> StageReport:
    watch = Stopwatch()
    directory = paths.stage_dir(Stage.IDENTITY)
    provenance = Provenance(stage=Stage.IDENTITY, inputs=upstream.fingerprint)
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    assignments = pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    features = load_features(paths.cache_file(Artifact.FEATURES))
    identities = preparation.build_identities(assignments, np.asarray(features))
    summary = preparation.component_summary(identities, assignments)
    logs.info(
        LogEvent.IDENTITIES_BUILT,
        {
            LogField.ROWS: identities.height,
            LogField.COMPONENTS: summary.height,
            LogField.LARGEST: summary[Column.ROWS].to_numpy().max().item(),
        },
    )
    write_table(identities, paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS))
    write_table(
        identities.select(Column.ROW, Column.SHA256, Column.FEATURE_ID),
        paths.stage_file(Stage.IDENTITY, Artifact.FEATURE_IDENTITIES),
    )
    write_table(
        assignments.select(Column.PACKAGE).unique().sort(Column.PACKAGE),
        paths.stage_file(Stage.IDENTITY, Artifact.PACKAGE_IDENTITIES),
    )
    write_table(
        summary,
        paths.stage_file(Stage.IDENTITY, Artifact.COMPONENT_SUMMARY),
    )
    return finish_stage(paths, directory, provenance, watch)


def families_stage(
    paths: Paths, config: Config, upstream: StageReport, overwrite: Overwrite
) -> StageReport:
    watch = Stopwatch()
    directory = paths.stage_dir(Stage.FAMILIES)
    provenance = Provenance(stage=Stage.FAMILIES, inputs=upstream.fingerprint)
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    labelled = preparation.classify_labels(
        pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS)), config.data
    )
    support = preparation.corpus_support(labelled)
    sets = preparation.select_family_sets(
        support, config.data, config.data.family_selection.set_size
    )
    write_table(support, paths.stage_file(Stage.FAMILIES, Artifact.SUPPORT))
    write_table(
        preparation.label_eligibility(labelled),
        paths.stage_file(Stage.FAMILIES, Artifact.ELIGIBILITY),
    )
    for name, members in sets.items():
        write_record(paths.family_set_file(name), FamilySetDocument(families=members))
        logs.info(
            LogEvent.FAMILIES_SELECTED,
            {LogField.FAMILY_SET: name, LogField.COUNT: len(members)},
        )
    overlap = set(sets[FamilySetName.PRIMARY]) & set(sets[FamilySetName.REPLICATION])
    record_validations(
        paths,
        [
            ValidationRecord(
                check=ValidationCheck.FAMILY_SETS_DISJOINT,
                passed=not overlap and all(len(members) > 0 for members in sets.values()),
                detail=DetailMessage.FAMILY_SETS.format(overlap=sorted(overlap)),
            )
        ],
        directory,
        Stage.FAMILIES,
    )
    return finish_stage(paths, directory, provenance, watch)


def partition_stage(
    paths: Paths,
    config: Config,
    upstream: StageReport,
    overwrite: Overwrite,
    modes: ModeSelection,
) -> list[StageReport]:
    labelled = preparation.classify_labels(
        pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS)), config.data
    )
    identities: IdentitiesTable | None = None
    universe = (
        *preparation.read_family_set(paths, FamilySetName.PRIMARY),
        *preparation.read_family_set(paths, FamilySetName.REPLICATION),
    )
    reports: list[StageReport] = []
    for key in required_partition_keys(config, modes):
        directory = paths.partition_dir(key)
        watch = Stopwatch()
        provenance = Provenance(
            stage=Stage.PARTITIONS,
            inputs=combine_fingerprints(upstream.fingerprint, key.model_dump_json()),
        )
        if reuse_stage(paths, directory, provenance, overwrite):
            reports.append(stage_report(directory, provenance, reused=True))
            continue
        if identities is None:
            identities = pl.read_parquet(paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS))
        result = partitions.build_partition(
            labelled,
            identities,
            preparation.grouping_ids(identities, key.grouping),
            universe,
            key,
            config.data,
        )
        write_table(
            pl.DataFrame({Column.ROW: identities[Column.ROW], Column.ROLE: result.roles}),
            paths.partition_file(key, Artifact.ASSIGNMENTS),
        )
        write_table(result.controlled, paths.partition_file(key, Artifact.CONTROLLED_PAIRS))
        write_table(result.natural, paths.partition_file(key, Artifact.NATURAL_PAIRS))
        write_record(
            paths.partition_file(key, Artifact.MANIFEST),
            PartitionManifest(
                key=key,
                attempt=result.attempt,
                eligible_controlled_pairs=result.controlled.filter(pl.col(Column.ELIGIBLE)).height,
                eligible_natural_pairs=result.natural.filter(pl.col(Column.ELIGIBLE)).height,
            ),
        )
        logs.info(
            LogEvent.PARTITION_BUILT,
            {
                LogField.SEED: key.seed,
                LogField.SALT: key.salt,
                LogField.ATTEMPT: result.attempt,
                LogField.ELIGIBLE: result.controlled.filter(pl.col(Column.ELIGIBLE)).height,
                LogField.COUNT: result.natural.filter(pl.col(Column.ELIGIBLE)).height,
            },
        )
        record_validations(paths, list(result.validations), directory, Stage.PARTITIONS)
        reports.append(finish_stage(paths, directory, provenance, watch))
    return reports


def large_partition_keys(config: Config, modes: ModeSelection) -> list[PartitionKey]:
    large = set(preparation.large_family_sets())
    wanted = {
        (spec.grouping, spec.eligibility)
        for spec in config.experiments.experiments.values()
        if spec.family_set in large
    }
    return [
        key
        for key in required_partition_keys(config, modes, include_designs=False)
        if (key.grouping, key.profile) in wanted and key.salt == 0
    ]


def _read_selection(paths: Paths) -> LargeFamilySelection:
    return LargeFamilySelection(
        table=pl.read_parquet(paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION)),
        sets={
            name: preparation.read_family_set(paths, name)
            for name in preparation.large_family_sets()
        },
    )


def large_selection_stage(
    paths: Paths, config: Config, upstream: StageReport, overwrite: Overwrite
) -> StageReport:
    watch = Stopwatch()
    directory = paths.stage_dir(Stage.FAMILIES)
    key = PartitionKey(
        seed=config.project.seeds.smoke[0],
        salt=0,
        grouping=Grouping.COMPONENT,
        profile=EligibilityProfile.PRIMARY,
    )
    roles_file = paths.partition_file(key, Artifact.ASSIGNMENTS)
    rule = config.data.eligibility[key.profile]
    provenance = Provenance(
        stage=Stage.FAMILIES,
        inputs=combine_fingerprints(
            upstream.fingerprint,
            key.model_dump_json(),
            rule.model_dump_json(),
            fingerprint_file(roles_file),
        ),
    )
    provenance_file = paths.stage_file(Stage.FAMILIES, Artifact.LARGE_PROVENANCE)
    if not overwrite and is_reusable(provenance_file, provenance):
        return stage_report(directory, provenance, reused=True)
    labelled = preparation.classify_labels(
        pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS)), config.data
    )
    roles = _aligned_roles(labelled, roles_file)
    selection = preparation.select_large_family_sets(
        labelled, roles, partitions.client_fit_rows(labelled, roles), rule
    )
    write_table(selection.table, paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION))
    for name, members in selection.sets.items():
        write_record(paths.family_set_file(name), FamilySetDocument(families=members))
        logs.info(
            LogEvent.FAMILIES_SELECTED, {LogField.FAMILY_SET: name, LogField.COUNT: len(members)}
        )
    write_provenance(provenance_file, provenance)
    logs.info(
        LogEvent.STAGE_BUILT,
        {
            LogField.STAGE: provenance.stage,
            LogField.PATH: f"{directory}",
            LogField.REUSED: False,
            LogField.SECONDS: watch.seconds(),
        },
    )
    return stage_report(directory, provenance, reused=False)


def _aligned_roles(labelled: LabelledTable, roles_file: File) -> RoleSeries:
    return (
        labelled.select(Column.ROW)
        .join(pl.read_parquet(roles_file), on=Column.ROW, how=LibraryOption.JOIN_LEFT)[Column.ROLE]
        .alias(Column.ROLE)
    )


def large_pairs_stage(
    paths: Paths,
    config: Config,
    selection: StageReport,
    modes: ModeSelection,
    overwrite: Overwrite,
) -> list[StageReport]:
    keys = large_partition_keys(config, modes)
    chosen = _read_selection(paths)
    universe = tuple(family for members in chosen.sets.values() for family in members)
    labelled: LabelledTable | None = None
    reports: list[StageReport] = []
    for key in keys:
        directory = paths.partition_dir(key)
        provenance = Provenance(
            stage=Stage.PARTITIONS,
            inputs=combine_fingerprints(
                selection.fingerprint,
                key.model_dump_json(),
                fingerprint_file(paths.partition_file(key, Artifact.ASSIGNMENTS)),
            ),
        )
        provenance_file = paths.partition_file(key, Artifact.LARGE_PROVENANCE)
        if not overwrite and is_reusable(provenance_file, provenance):
            reports.append(stage_report(directory, provenance, reused=True))
            continue
        if labelled is None:
            labelled = preparation.classify_labels(
                pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS)), config.data
            )
        roles = _aligned_roles(labelled, paths.partition_file(key, Artifact.ASSIGNMENTS))
        tables = partitions.evaluate_partition(labelled, roles, universe, config.data, key)
        write_table(tables.controlled, paths.partition_file(key, Artifact.LARGE_CONTROLLED_PAIRS))
        write_table(tables.natural, paths.partition_file(key, Artifact.LARGE_NATURAL_PAIRS))
        write_provenance(provenance_file, provenance)
        logs.info(
            LogEvent.PARTITION_BUILT,
            {
                LogField.SEED: key.seed,
                LogField.SALT: key.salt,
                LogField.ATTEMPT: 0,
                LogField.ELIGIBLE: tables.controlled.filter(pl.col(Column.ELIGIBLE)).height,
                LogField.COUNT: tables.natural.filter(pl.col(Column.ELIGIBLE)).height,
            },
        )
        reports.append(stage_report(directory, provenance, reused=False))
    return reports


def run_preprocess(
    paths: Paths,
    config: Config,
    overwrite: Overwrite,
    modes: ModeSelection = tuple(ExecutionMode),
) -> list[StageReport]:
    audit = source_audit(paths, config, overwrite)
    joined = join_stage(paths, audit, overwrite)
    assigned = clients_stage(paths, config, joined, overwrite)
    identified = identity_stage(paths, assigned, overwrite)
    family_report = families_stage(paths, config, assigned, overwrite)
    upstream = StageReport(
        stage=Stage.PARTITIONS,
        directory=paths.stage_dir(Stage.PARTITIONS),
        reused=identified.reused and family_report.reused,
        fingerprint=combine_fingerprints(identified.fingerprint, family_report.fingerprint),
    )
    partition_reports = partition_stage(paths, config, upstream, overwrite, modes)
    selection = large_selection_stage(
        paths,
        config,
        StageReport(
            stage=Stage.PARTITIONS,
            directory=paths.stage_dir(Stage.PARTITIONS),
            reused=upstream.reused,
            fingerprint=upstream.fingerprint,
        ),
        overwrite,
    )
    return [
        audit,
        joined,
        assigned,
        identified,
        family_report,
        *partition_reports,
        selection,
        *large_pairs_stage(paths, config, selection, modes, overwrite),
    ]


def representation_keys(config: Config, modes: ModeSelection) -> list[PartitionKey]:
    keys: list[PartitionKey] = []
    for name, spec in config.experiments.experiments.items():
        if spec.representation is None:
            continue
        _keys_for_experiment(config, name, spec, modes, keys)
    return sorted(keys, key=lambda key: (key.seed, key.salt))


def _upstream(paths: Paths, config: Config, sources: Fingerprint) -> Fingerprint:
    lamda = [
        read_record(paths.provenance_file(paths.stage_dir(stage)), Provenance).inputs
        for stage in (Stage.CLIENTS, Stage.IDENTITY, Stage.FAMILIES)
    ]
    return combine_fingerprints(*lamda, sources, config.data.stable_fingerprint())


def _inventory(paths: Paths) -> SourceInventory:
    file = paths.representation_file(Artifact.INVENTORY)
    return read_record(file, SourceInventory) if file.is_file() else SourceInventory(entries=())


def _namespace_stage(paths: Paths, config: Config, overwrite: Overwrite) -> StageReport:
    watch = Stopwatch()
    directory = paths.representation_dir
    scan = representations.fingerprint_sources(paths, _inventory(paths))
    provenance = Provenance(
        stage=Stage.REPRESENTATION,
        inputs=_upstream(paths, config, scan.fingerprint.fingerprint),
    )
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    manifest = representations.build_namespace(paths)
    write_record(paths.representation_file(Artifact.INVENTORY), scan.inventory)
    write_record(paths.representation_file(Artifact.FINGERPRINT), scan.fingerprint)
    record_validations(
        paths,
        representations.namespace_validations(paths, manifest),
        directory,
        Stage.REPRESENTATION,
    )
    return finish_stage(paths, directory, provenance, watch)


def _partition_provenance(
    paths: Paths, config: Config, namespace: StageReport, key: PartitionKey
) -> Provenance:
    universe = (
        *preparation.read_family_set(paths, FamilySetName.PRIMARY),
        *preparation.read_family_set(paths, FamilySetName.REPLICATION),
    )
    minimum = config.experiments.representation_min_prevalence
    return Provenance(
        stage=Stage.PARTITIONS,
        inputs=combine_fingerprints(
            namespace.fingerprint, key.model_dump_json(), f"{minimum}", f"{universe}"
        ),
    )


def _seed_partition(
    paths: Paths,
    config: Config,
    provenance: Provenance,
    key: PartitionKey,
) -> StageReport:
    watch = Stopwatch()
    directory = paths.representation_partition_dir(key)
    universe = (
        *preparation.read_family_set(paths, FamilySetName.PRIMARY),
        *preparation.read_family_set(paths, FamilySetName.REPLICATION),
    )
    result = representations.build_seed_partition(paths, config, key, universe)
    representations.write_seed_partition(paths, key, result)
    eligible = result.controlled.filter(pl.col(Column.ELIGIBLE)).height
    write_record(
        paths.representation_partition_file(key, Artifact.MANIFEST),
        PartitionManifest(
            key=key,
            attempt=result.attempt,
            eligible_controlled_pairs=eligible,
            eligible_natural_pairs=result.natural.filter(pl.col(Column.ELIGIBLE)).height,
        ),
    )
    logs.info(
        LogEvent.PARTITION_BUILT,
        {
            LogField.SEED: key.seed,
            LogField.SALT: key.salt,
            LogField.ATTEMPT: result.attempt,
            LogField.ELIGIBLE: eligible,
        },
    )
    record_validations(paths, list(result.validations), directory, Stage.PARTITIONS)
    return finish_stage(paths, directory, provenance, watch)


def run_representation_preprocess(
    paths: Paths, config: Config, overwrite: Overwrite, modes: ModeSelection
) -> list[StageReport]:
    for stage in (Stage.CLIENTS, Stage.IDENTITY, Stage.FAMILIES):
        if not paths.provenance_file(paths.stage_dir(stage)).is_file():
            raise CtkError(
                FailureReason.SCHEMA_MISMATCH,
                ErrorMessage.STALE_PREPROCESSING.format(path=paths.stage_dir(stage)),
            )
    namespace = _namespace_stage(paths, config, overwrite)
    reports = [namespace]
    for key in representation_keys(config, modes):
        directory = paths.representation_partition_dir(key)
        provenance = _partition_provenance(paths, config, namespace, key)
        if reuse_stage(paths, directory, provenance, overwrite):
            reports.append(stage_report(directory, provenance, reused=True))
            continue
        reports.append(_seed_partition(paths, config, provenance, key))
    return reports
