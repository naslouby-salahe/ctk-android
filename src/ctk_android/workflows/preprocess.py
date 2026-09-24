import json

import numpy as np
import polars as pl
import structlog

from ctk_android.config import Config
from ctk_android.data import clients, families, identity, joins, partitions, sources
from ctk_android.data.cache import (
    combine_fingerprints,
    fingerprint_document,
    fingerprint_file,
    fingerprint_source_tree,
    is_reusable,
    load_features,
    read_json,
    save_features,
    write_json,
    write_provenance,
)
from ctk_android.enums import (
    Column,
    DatasetName,
    FailureReason,
    FamilySetName,
    LogEvent,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    Directory,
    Fingerprint,
    InventoryDocument,
    PartitionKey,
    Provenance,
    StageReport,
    ValidationRecord,
)

log = structlog.get_logger()
FEATURES_FILE = "features.npy"
DATASET_FILE = "dataset.parquet"
ASSIGNMENTS_FILE = "assignments.parquet"
INVENTORY_FILE = "inventory.json"
CORE_MODULES = ("types.py", "enums.py", "config.py", "paths.py")


def code_fingerprint(paths: Paths) -> Fingerprint:
    package = paths.root / "src" / "ctk_android"
    return combine_fingerprints(
        fingerprint_source_tree(package / "data"),
        *(fingerprint_file(package / name) for name in CORE_MODULES),
    )


def required_partition_keys(config: Config) -> list[PartitionKey]:
    keys: list[PartitionKey] = []
    for spec in config.experiments.experiments.values():
        for mode in spec.modes:
            for seed in config.project.seeds.for_mode(mode):
                for salt in spec.salts:
                    key = PartitionKey(
                        seed=seed, salt=salt, grouping=spec.grouping, profile=spec.eligibility
                    )
                    if key not in keys:
                        keys.append(key)
    return sorted(keys, key=lambda key: (key.seed, key.salt, key.grouping, key.profile))


def _record(records: list[ValidationRecord], directory: Directory, stage: Stage) -> None:
    write_json(
        directory / "audit.json",
        {"validations": [record.model_dump(mode="json") for record in records]},
    )
    failed = [record for record in records if not record.passed]
    if failed:
        log.error(LogEvent.STAGE_FAILED, stage=stage, check=failed[0].check)
        raise CtkError(FailureReason.SCHEMA_MISMATCH, f"{stage}: {failed[0].check} {failed[0].detail}")


def _reuse(directory: Directory, provenance: Provenance, overwrite: bool) -> bool:
    reusable = not overwrite and is_reusable(directory, provenance)
    if reusable:
        log.info(LogEvent.STAGE_REUSED, stage=provenance.stage)
    return reusable


def _finish(directory: Directory, provenance: Provenance) -> StageReport:
    write_provenance(directory, provenance)
    log.info(LogEvent.STAGE_BUILT, stage=provenance.stage)
    return StageReport(
        stage=provenance.stage,
        directory=directory,
        reused=False,
        fingerprint=combine_fingerprints(provenance.inputs, provenance.code),
    )


def _report(directory: Directory, provenance: Provenance) -> StageReport:
    return StageReport(
        stage=provenance.stage,
        directory=directory,
        reused=True,
        fingerprint=combine_fingerprints(provenance.inputs, provenance.code),
    )


def _known_inventory(directory: Directory) -> InventoryDocument:
    path = directory / INVENTORY_FILE
    if not path.is_file():
        return {}
    stored = read_json(path)
    return {name: (entry[0], entry[1]) for name, entry in stored.items()}


def source_audit(paths: Paths, config: Config, code: Fingerprint, overwrite: bool) -> StageReport:
    lamda_dir = paths.source_audit(DatasetName.LAMDA)
    az_dir = paths.source_audit(DatasetName.ANDROZOO)
    lamda_fp, lamda_inventory = sources.fingerprint_lamda(
        paths.raw_data(DatasetName.LAMDA), config.data, _known_inventory(lamda_dir)
    )
    az_fp, az_inventory = sources.fingerprint_androzoo(
        paths.raw_data(DatasetName.ANDROZOO), _known_inventory(az_dir)
    )
    config_fp = fingerprint_document(config.data.model_dump(mode="json"))
    provenance = Provenance(
        stage=Stage.SOURCE_AUDIT,
        inputs=combine_fingerprints(sources.sources_fingerprint(lamda_fp, az_fp), config_fp),
        code=code,
    )
    if _reuse(paths.linkage, provenance, overwrite):
        return _report(paths.linkage, provenance)

    lamda = sources.load_lamda(paths.raw_data(DatasetName.LAMDA), config.data)
    azoo = sources.scan_androzoo(paths.raw_data(DatasetName.ANDROZOO), lamda.metadata[Column.SHA256])
    result = joins.join_sources(lamda.metadata, azoo)
    validations = [*sources.validate_lamda(lamda, config.data), *result.validations]

    lamda_dir.mkdir(parents=True, exist_ok=True)
    az_dir.mkdir(parents=True, exist_ok=True)
    paths.linkage.mkdir(parents=True, exist_ok=True)
    write_json(lamda_dir / "fingerprint.json", lamda_fp.model_dump(mode="json"))
    write_json(az_dir / "fingerprint.json", az_fp.model_dump(mode="json"))
    write_json(lamda_dir / INVENTORY_FILE, dict(lamda_inventory))
    write_json(az_dir / INVENTORY_FILE, dict(az_inventory))
    write_json(
        lamda_dir / "schema.json",
        {
            "release": config.data.lamda_release,
            "feature_count": lamda.features.shape[1],
            "metadata_columns": lamda.metadata.columns,
            "non_binary_cells_binarized": lamda.non_binary_cells,
            "negative_cells": lamda.negative_cells,
        },
    )
    write_json(
        lamda_dir / "counts.json",
        {
            "rows": lamda.metadata.height,
            "malware": int((lamda.metadata[Column.LABEL] == 1).sum()),
            "benign": int((lamda.metadata[Column.LABEL] == 0).sum()),
        },
    )
    write_json(az_dir / "schema.json", {"columns": azoo.columns})
    write_json(az_dir / "counts.json", {"linked_rows": azoo.height})
    lamda.metadata.write_parquet(lamda_dir / "metadata.parquet")
    azoo.write_parquet(paths.linkage / "hash-linkage.parquet")
    result.unmatched.write_parquet(paths.linkage / "unmatched.parquet")
    _record(validations, paths.linkage, Stage.SOURCE_AUDIT)
    return _finish(paths.linkage, provenance)


def join_stage(paths: Paths, config: Config, upstream: StageReport, code: Fingerprint, overwrite: bool) -> StageReport:
    provenance = Provenance(stage=Stage.JOIN, inputs=upstream.fingerprint, code=code)
    if _reuse(paths.joined, provenance, overwrite):
        return _report(paths.joined, provenance)
    metadata = pl.read_parquet(paths.source_audit(DatasetName.LAMDA) / "metadata.parquet")
    linked = pl.read_parquet(paths.linkage / "hash-linkage.parquet")
    result = joins.join_sources(metadata, linked)
    paths.joined.mkdir(parents=True, exist_ok=True)
    result.joined.write_parquet(paths.joined / DATASET_FILE)
    _record(list(result.validations), paths.joined, Stage.JOIN)
    return _finish(paths.joined, provenance)


def clients_stage(paths: Paths, config: Config, upstream: StageReport, code: Fingerprint, overwrite: bool) -> StageReport:
    provenance = Provenance(stage=Stage.CLIENTS, inputs=upstream.fingerprint, code=code)
    if _reuse(paths.clients, provenance, overwrite):
        return _report(paths.clients, provenance)
    joined = pl.read_parquet(paths.joined / DATASET_FILE)
    assignments = clients.assign_clients(joined, config.data)
    lamda = sources.load_lamda(paths.raw_data(DatasetName.LAMDA), config.data)
    positions = (
        lamda.metadata.select(Column.SHA256)
        .with_row_index(Column.ROW)
        .join(assignments.select(Column.SHA256), on=Column.SHA256)[Column.ROW]
        .to_numpy()
    )
    save_features(paths.cache / FEATURES_FILE, lamda.features[positions])
    paths.clients.mkdir(parents=True, exist_ok=True)
    assignments.with_row_index(Column.ROW).write_parquet(paths.clients / ASSIGNMENTS_FILE)
    support = clients.client_support(assignments)
    support.write_parquet(paths.clients / "support.parquet")
    clients_present = set(support[Column.CLIENT].to_list())
    from ctk_android.enums import ClientId, ValidationCheck

    _record(
        [
            ValidationRecord(
                check=ValidationCheck.LINKAGE_COMPLETE,
                passed=clients_present == {client.value for client in ClientId},
                detail=f"clients={sorted(clients_present)}",
            )
        ],
        paths.clients,
        Stage.CLIENTS,
    )
    return _finish(paths.clients, provenance)


def identity_stage(paths: Paths, upstream: StageReport, code: Fingerprint, overwrite: bool) -> StageReport:
    provenance = Provenance(stage=Stage.IDENTITY, inputs=upstream.fingerprint, code=code)
    if _reuse(paths.identity, provenance, overwrite):
        return _report(paths.identity, provenance)
    assignments = pl.read_parquet(paths.clients / ASSIGNMENTS_FILE)
    features = load_features(paths.cache / FEATURES_FILE)
    identities = identity.build_identities(assignments, np.asarray(features))
    paths.identity.mkdir(parents=True, exist_ok=True)
    identities.write_parquet(paths.identity / "components.parquet")
    identities.select(Column.ROW, Column.SHA256, Column.FEATURE_ID).write_parquet(
        paths.identity / "feature-identities.parquet"
    )
    assignments.select(Column.PACKAGE).unique().sort(Column.PACKAGE).write_parquet(
        paths.identity / "package-identities.parquet"
    )
    identity.component_summary(identities, assignments).write_parquet(
        paths.identity / "component-summary.parquet"
    )
    return _finish(paths.identity, provenance)


def families_stage(paths: Paths, config: Config, upstream: StageReport, code: Fingerprint, overwrite: bool) -> StageReport:
    provenance = Provenance(stage=Stage.FAMILIES, inputs=upstream.fingerprint, code=code)
    if _reuse(paths.families, provenance, overwrite):
        return _report(paths.families, provenance)
    labelled = families.classify_labels(pl.read_parquet(paths.clients / ASSIGNMENTS_FILE), config.data)
    support = families.corpus_support(labelled)
    sets = families.select_family_sets(support, config.data, config.data.family_selection.set_size)
    paths.families.mkdir(parents=True, exist_ok=True)
    support.write_parquet(paths.families / "support.parquet")
    families.label_eligibility(labelled).write_parquet(paths.families / "eligibility.parquet")
    for name, members in sets.items():
        write_json(paths.family_set_file(name), {"families": list(members)})
    overlap = set(sets[FamilySetName.PRIMARY]) & set(sets[FamilySetName.REPLICATION])
    from ctk_android.enums import ValidationCheck

    _record(
        [
            ValidationRecord(
                check=ValidationCheck.LINKAGE_COMPLETE,
                passed=not overlap and all(len(members) > 0 for members in sets.values()),
                detail=f"disjoint family sets, overlap={sorted(overlap)}",
            )
        ],
        paths.families,
        Stage.FAMILIES,
    )
    return _finish(paths.families, provenance)


def read_family_set(paths: Paths, name: FamilySetName) -> tuple[str, ...]:
    return tuple(json.loads(paths.family_set_file(name).read_text(encoding="utf-8"))["families"])


def partition_stage(paths: Paths, config: Config, upstream: StageReport, code: Fingerprint, overwrite: bool) -> list[StageReport]:
    labelled = families.classify_labels(pl.read_parquet(paths.clients / ASSIGNMENTS_FILE), config.data)
    identities: pl.DataFrame | None = None
    universe = (*read_family_set(paths, FamilySetName.PRIMARY), *read_family_set(paths, FamilySetName.REPLICATION))
    reports: list[StageReport] = []
    for key in required_partition_keys(config):
        directory = paths.partition(key)
        provenance = Provenance(
            stage=Stage.PARTITION,
            inputs=combine_fingerprints(upstream.fingerprint, key.model_dump_json()),
            code=code,
        )
        if _reuse(directory, provenance, overwrite):
            reports.append(_report(directory, provenance))
            continue
        if identities is None:
            identities = pl.read_parquet(paths.identity / "components.parquet")
        result = partitions.build_partition(
            labelled, identities, identity.grouping_ids(identities, key.grouping), universe, key, config.data
        )
        directory.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({Column.ROW: identities[Column.ROW], Column.ROLE: result.roles}).write_parquet(
            directory / ASSIGNMENTS_FILE
        )
        result.controlled.write_parquet(directory / "controlled-pairs.parquet")
        result.natural.write_parquet(directory / "natural-pairs.parquet")
        write_json(
            directory / "manifest.json",
            {
                "key": key.model_dump(mode="json"),
                "attempt": result.attempt,
                "eligible_controlled_pairs": int(result.controlled[Column.ELIGIBLE].sum()),
                "eligible_natural_pairs": int(result.natural[Column.ELIGIBLE].sum()),
            },
        )
        _record(list(result.validations), directory, Stage.PARTITION)
        reports.append(_finish(directory, provenance))
    return reports


def run_preprocess(paths: Paths, config: Config, overwrite: bool) -> list[StageReport]:
    code = code_fingerprint(paths)
    audit = source_audit(paths, config, code, overwrite)
    joined = join_stage(paths, config, audit, code, overwrite)
    assigned = clients_stage(paths, config, joined, code, overwrite)
    identified = identity_stage(paths, assigned, code, overwrite)
    family_report = families_stage(paths, config, assigned, code, overwrite)
    upstream = StageReport(
        stage=Stage.PARTITION,
        directory=paths.partitions,
        reused=identified.reused and family_report.reused,
        fingerprint=combine_fingerprints(identified.fingerprint, family_report.fingerprint),
    )
    return [audit, joined, assigned, identified, family_report, *partition_stage(paths, config, upstream, code, overwrite)]
