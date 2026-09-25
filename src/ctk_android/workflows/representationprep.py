import polars as pl

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data import mcndroid, representation
from ctk_android.data.cache import (
    combine_fingerprints,
    read_record,
    write_record,
)
from ctk_android.enums import (
    Artifact,
    Column,
    ErrorMessage,
    FailureReason,
    FamilySetName,
    LogEvent,
    LogField,
    Stage,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    Fingerprint,
    ModeSelection,
    Overwrite,
    PartitionKey,
    PartitionManifest,
    Provenance,
    SourceInventory,
    StageReport,
)
from ctk_android.workflows.preprocess import (
    finish_stage,
    read_family_set,
    record_validations,
    reuse_stage,
    stage_report,
)


def representation_keys(config: Config, modes: ModeSelection) -> list[PartitionKey]:
    keys: list[PartitionKey] = []
    for name, spec in config.experiments.experiments.items():
        if spec.representation is None:
            continue
        for mode in modes:
            if not config.experiments.runs_in(name, mode):
                continue
            for seed in config.seeds_for(name, mode):
                for salt in spec.salts:
                    key = PartitionKey(
                        seed=seed, salt=salt, grouping=spec.grouping, profile=spec.eligibility
                    )
                    if key not in keys:
                        keys.append(key)
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
    scan = mcndroid.fingerprint_sources(paths, _inventory(paths))
    provenance = Provenance(
        stage=Stage.REPRESENTATION,
        inputs=_upstream(paths, config, scan.fingerprint.fingerprint),
    )
    if reuse_stage(paths, directory, provenance, overwrite):
        return stage_report(directory, provenance, reused=True)
    manifest = representation.build_namespace(paths)
    write_record(paths.representation_file(Artifact.INVENTORY), scan.inventory)
    write_record(paths.representation_file(Artifact.FINGERPRINT), scan.fingerprint)
    record_validations(
        paths,
        representation.namespace_validations(paths, manifest),
        directory,
        Stage.REPRESENTATION,
    )
    return finish_stage(paths, directory, provenance, watch)


def _partition_provenance(
    paths: Paths, config: Config, namespace: StageReport, key: PartitionKey
) -> Provenance:
    universe = (
        *read_family_set(paths, FamilySetName.PRIMARY),
        *read_family_set(paths, FamilySetName.REPLICATION),
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
        *read_family_set(paths, FamilySetName.PRIMARY),
        *read_family_set(paths, FamilySetName.REPLICATION),
    )
    result = representation.build_seed_partition(paths, config, key, universe)
    representation.write_seed_partition(paths, key, result)
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
