from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import numpy as np
import polars as pl
import pytest

import ctk_android.workflows.preprocess as preprocess
from ctk_android.config import Config, load_config
from ctk_android.data.cache import combine_fingerprints, write_table
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    DatasetName,
    FailureReason,
    FamilySetName,
    Stage,
    ValidationCheck,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    JoinResult,
    LamdaTable,
    LargeFamilySelection,
    Provenance,
    SourceFingerprint,
    SourceInventory,
    SourceScan,
    StageReport,
    ValidationRecord,
)
from tests.architecture.source_index import REPO_ROOT


def _typed_callback(callback: Callable[..., Any]) -> Callable[..., Any]:
    return callback


CONFIG = load_config(Paths(REPO_ROOT))


def _report(tmp_path: Path, stage: Stage, reused: bool = True) -> StageReport:
    return StageReport(
        stage=stage,
        directory=tmp_path / stage,
        reused=reused,
        fingerprint="a" * 64,
    )


def test_validation_records_are_persisted_and_failed_checks_stop_the_stage(
    tmp_path: Path,
) -> None:
    paths = Paths(tmp_path)
    directory = tmp_path / "outputs" / "stage"
    passed = ValidationRecord(check=ValidationCheck.FEATURE_CONTRACT, passed=True, detail="valid")
    preprocess.record_validations(paths, [passed], directory, Stage.CLIENTS)
    assert paths.audit_file(directory).is_file()

    failed = ValidationRecord(check=ValidationCheck.LABEL_RULE, passed=False, detail="bad labels")
    with pytest.raises(CtkError, match="bad labels") as raised:
        preprocess.record_validations(paths, [passed, failed], directory, Stage.CLIENTS)
    assert raised.value.reason is FailureReason.SCHEMA_MISMATCH


def test_reuse_stage_skips_validation_when_overwrite_is_requested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(
        preprocess, "is_reusable", _typed_callback(lambda *_args: calls.append(True) or True)
    )
    paths = Paths(tmp_path)
    provenance = Provenance(stage=Stage.CLIENTS, inputs="b" * 64)

    assert preprocess.reuse_stage(paths, tmp_path / "clients", provenance, False)
    assert not preprocess.reuse_stage(paths, tmp_path / "clients", provenance, True)
    assert calls == [True]


def test_run_preprocess_preserves_stage_order_and_reuse_provenance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    audit = _report(tmp_path, Stage.SOURCE_AUDIT)
    joined = _report(tmp_path, Stage.JOINED)
    clients = _report(tmp_path, Stage.CLIENTS)
    identities = _report(tmp_path, Stage.IDENTITY)
    families = _report(tmp_path, Stage.FAMILIES, reused=False)
    partitions = _report(tmp_path, Stage.PARTITIONS)
    selection = _report(tmp_path, Stage.FAMILIES)
    large = _report(tmp_path, Stage.PARTITIONS, reused=False)
    captured_partition: list[StageReport] = []
    captured_selection: list[StageReport] = []
    captured_large_selection: list[StageReport] = []

    monkeypatch.setattr(preprocess, "source_audit", _typed_callback(lambda *_args: audit))
    monkeypatch.setattr(preprocess, "join_stage", _typed_callback(lambda *_args: joined))
    monkeypatch.setattr(preprocess, "clients_stage", _typed_callback(lambda *_args: clients))
    monkeypatch.setattr(preprocess, "identity_stage", _typed_callback(lambda *_args: identities))
    monkeypatch.setattr(preprocess, "families_stage", _typed_callback(lambda *_args: families))

    def partition_stage(
        _paths: Paths,
        _config: Config,
        upstream: StageReport,
        _overwrite: bool,
    ) -> list[StageReport]:
        captured_partition.append(upstream)
        return [partitions]

    def large_selection_stage(
        _paths: Paths, _config: Config, upstream: StageReport, _overwrite: bool
    ) -> StageReport:
        captured_selection.append(upstream)
        return selection

    def large_pairs_stage(
        _paths: Paths,
        _config: Config,
        selected: StageReport,
        _overwrite: bool,
    ) -> list[StageReport]:
        captured_large_selection.append(selected)
        return [large]

    monkeypatch.setattr(preprocess, "partition_stage", partition_stage)
    monkeypatch.setattr(preprocess, "large_selection_stage", large_selection_stage)
    monkeypatch.setattr(preprocess, "large_pairs_stage", large_pairs_stage)
    represented = [_report(tmp_path, Stage.REPRESENTATION)]
    monkeypatch.setattr(
        preprocess, "representation_stages", _typed_callback(lambda *_args: represented)
    )
    reports = preprocess.run_preprocess(paths, CONFIG, False)

    upstream = captured_partition[0]
    assert upstream.reused is False
    assert upstream.fingerprint == combine_fingerprints(
        identities.fingerprint, families.fingerprint
    )
    assert captured_selection[0].reused is False
    assert captured_large_selection == [selection]
    assert reports == [
        audit,
        joined,
        clients,
        identities,
        families,
        partitions,
        selection,
        large,
        *represented,
    ]


def test_preprocess_reaches_representation_preprocessing_only_when_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = [_report(tmp_path, Stage.SOURCE_AUDIT)]
    represented = [_report(tmp_path, Stage.REPRESENTATION)]
    monkeypatch.setattr(preprocess, "base_stages", _typed_callback(lambda *_args: list(base)))
    monkeypatch.setattr(
        preprocess, "representation_stages", _typed_callback(lambda *_args: list(represented))
    )
    paths = Paths(tmp_path)
    assert CONFIG.experiments.needs_representations()
    assert preprocess.run_preprocess(paths, CONFIG, False) == [*base, *represented]

    without = CONFIG.model_copy(
        update={
            "experiments": CONFIG.experiments.model_copy(
                update={
                    "experiments": {
                        name: spec
                        for name, spec in CONFIG.experiments.experiments.items()
                        if spec.representation is None
                    }
                }
            )
        }
    )
    assert not without.experiments.needs_representations()
    assert preprocess.run_preprocess(paths, without, False) == base


def test_required_partitions_cover_every_mode_of_every_configured_experiment() -> None:
    expected = {
        (run.seed, run.salt)
        for name, spec in CONFIG.experiments.experiments.items()
        if spec.representation is None
        for run in CONFIG.experiment_keys(name)
    }
    keys = preprocess.required_partition_keys(CONFIG)
    assert {(key.seed, key.salt) for key in keys} == expected
    representation = preprocess.representation_keys(CONFIG)
    assert {key.seed for key in representation} == {
        run.seed
        for name, spec in CONFIG.experiments.experiments.items()
        if spec.representation is not None
        for run in CONFIG.experiment_keys(name)
    }


def test_finish_stage_writes_the_provenance_and_reports_a_fresh_build(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    directory = paths.stage_dir(Stage.CLIENTS)
    provenance = Provenance(stage=Stage.CLIENTS, inputs="c" * 64)

    report = preprocess.finish_stage(paths, directory, provenance, Stopwatch())

    assert report.reused is False
    assert report.fingerprint == provenance.inputs
    assert paths.provenance_file(directory).is_file()


def test_missing_inventory_is_an_empty_inventory(tmp_path: Path) -> None:
    inventory_function_name = "_known_inventory"
    inventory = getattr(preprocess, inventory_function_name)(Paths(tmp_path), DatasetName.LAMDA)
    assert inventory == SourceInventory(entries=())


def test_source_audit_writes_fingerprints_schemas_counts_and_linkage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    scans = {
        DatasetName.LAMDA: SourceScan(
            fingerprint=SourceFingerprint(
                dataset=DatasetName.LAMDA, fingerprint="a" * 64, file_count=1, total_bytes=10
            ),
            inventory=SourceInventory(entries=()),
        ),
        DatasetName.ANDROZOO: SourceScan(
            fingerprint=SourceFingerprint(
                dataset=DatasetName.ANDROZOO, fingerprint="b" * 64, file_count=1, total_bytes=20
            ),
            inventory=SourceInventory(entries=()),
        ),
    }
    metadata = pl.DataFrame(
        {Column.SHA256: ["a", "b"], Column.LABEL: [1, 0]},
        schema={Column.SHA256: pl.String, Column.LABEL: pl.Int8},
    )
    lamda = LamdaTable(
        metadata=metadata,
        features=np.zeros((2, 3), dtype=np.uint8),
        non_binary_cells=1,
        negative_cells=0,
    )
    linkage = pl.DataFrame({Column.SHA256: ["a"]})
    joined = JoinResult(joined=linkage, unmatched=pl.DataFrame(), validations=())
    monkeypatch.setattr(
        preprocess.sources, "fingerprint_lamda", Mock(return_value=scans[DatasetName.LAMDA])
    )
    monkeypatch.setattr(
        preprocess.sources,
        "fingerprint_androzoo",
        Mock(return_value=scans[DatasetName.ANDROZOO]),
    )
    monkeypatch.setattr(preprocess.sources, "load_lamda", Mock(return_value=lamda))
    monkeypatch.setattr(preprocess.sources, "scan_androzoo", Mock(return_value=linkage))
    monkeypatch.setattr(preprocess.sources, "validate_lamda", Mock(return_value=[]))
    monkeypatch.setattr(preprocess.preparation, "join_sources", Mock(return_value=joined))
    monkeypatch.setattr(preprocess, "reuse_stage", Mock(return_value=False))

    report = preprocess.source_audit(paths, CONFIG, False)

    assert report.stage is Stage.SOURCE_AUDIT
    assert paths.source_file(DatasetName.LAMDA, Artifact.FINGERPRINT).is_file()
    assert paths.source_file(DatasetName.ANDROZOO, Artifact.INVENTORY).is_file()
    assert paths.source_file(DatasetName.LAMDA, Artifact.SCHEMA).is_file()
    assert paths.source_file(DatasetName.LAMDA, Artifact.COUNTS).is_file()
    assert paths.source_file(DatasetName.ANDROZOO, Artifact.SCHEMA).is_file()
    assert paths.source_file(DatasetName.ANDROZOO, Artifact.COUNTS).is_file()
    assert paths.source_file(DatasetName.LAMDA, Artifact.METADATA).is_file()
    assert paths.linkage_file(Artifact.HASH_LINKAGE).is_file()
    assert paths.linkage_file(Artifact.UNMATCHED).is_file()


def test_join_stage_reads_linkage_writes_joined_data_and_finishes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    metadata = pl.DataFrame({Column.SHA256: ["a"]})
    linkage = pl.DataFrame({Column.SHA256: ["a"]})
    write_table(metadata, paths.source_file(DatasetName.LAMDA, Artifact.METADATA))
    write_table(linkage, paths.linkage_file(Artifact.HASH_LINKAGE))
    joined_table = pl.DataFrame({Column.SHA256: ["a"], Column.LABEL: [1]})
    result = JoinResult(joined=joined_table, unmatched=pl.DataFrame(), validations=())
    monkeypatch.setattr(preprocess.preparation, "join_sources", Mock(return_value=result))
    monkeypatch.setattr(preprocess, "reuse_stage", Mock(return_value=False))
    monkeypatch.setattr(preprocess, "record_validations", Mock())

    report = preprocess.join_stage(paths, _report(tmp_path, Stage.SOURCE_AUDIT), False)

    assert report.stage is Stage.JOINED
    assert pl.read_parquet(paths.stage_file(Stage.JOINED, Artifact.DATASET)).equals(joined_table)


def test_families_stage_writes_support_eligibility_and_disjoint_sets(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    labelled = pl.DataFrame({Column.FAMILY: ["fam-a", "fam-b"]})
    support = pl.DataFrame({Column.FAMILY: ["fam-a", "fam-b"]})
    eligibility = pl.DataFrame({Column.FAMILY: ["fam-a", "fam-b"]})
    family_sets = {
        FamilySetName.PRIMARY: ("fam-a",),
        FamilySetName.REPLICATION: ("fam-b",),
    }
    write_table(labelled, paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    monkeypatch.setattr(preprocess, "reuse_stage", Mock(return_value=False))
    monkeypatch.setattr(preprocess.preparation, "classify_labels", Mock(return_value=labelled))
    monkeypatch.setattr(preprocess.preparation, "corpus_support", Mock(return_value=support))
    monkeypatch.setattr(
        preprocess.preparation, "select_family_sets", Mock(return_value=family_sets)
    )
    monkeypatch.setattr(preprocess.preparation, "label_eligibility", Mock(return_value=eligibility))
    monkeypatch.setattr(preprocess, "record_validations", Mock())

    report = preprocess.families_stage(paths, CONFIG, _report(tmp_path, Stage.CLIENTS), False)

    assert report.stage is Stage.FAMILIES
    assert paths.stage_file(Stage.FAMILIES, Artifact.SUPPORT).is_file()
    assert paths.stage_file(Stage.FAMILIES, Artifact.ELIGIBILITY).is_file()
    assert paths.family_set_file(FamilySetName.PRIMARY).is_file()
    assert paths.family_set_file(FamilySetName.REPLICATION).is_file()
    assert preprocess.preparation.read_family_set(paths, FamilySetName.PRIMARY) == ("fam-a",)


def test_large_selection_stage_writes_selection_and_each_family_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    labelled = pl.DataFrame({Column.FAMILY: ["fam-a", "fam-b"]})
    table = pl.DataFrame({Column.FAMILY: ["fam-a", "fam-b"]})
    family_sets = {
        name: (f"family-{index}",)
        for index, name in enumerate(preprocess.preparation.large_family_sets())
    }
    selection = LargeFamilySelection(table=table, sets=family_sets)
    write_table(labelled, paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    monkeypatch.setattr(preprocess, "fingerprint_file", Mock(return_value="c" * 64))
    monkeypatch.setattr(preprocess, "is_reusable", Mock(return_value=False))
    monkeypatch.setattr(preprocess.preparation, "classify_labels", Mock(return_value=labelled))
    monkeypatch.setattr(preprocess, "_aligned_roles", Mock(return_value=pl.Series(["fit", "test"])))
    monkeypatch.setattr(preprocess.partitions, "client_fit_rows", Mock(return_value=pl.DataFrame()))
    monkeypatch.setattr(
        preprocess.preparation, "select_large_family_sets", Mock(return_value=selection)
    )

    report = preprocess.large_selection_stage(
        paths, CONFIG, _report(tmp_path, Stage.PARTITIONS), False
    )

    assert report.stage is Stage.FAMILIES
    assert paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION).is_file()
    assert paths.stage_file(Stage.FAMILIES, Artifact.LARGE_PROVENANCE).is_file()
    for name in family_sets:
        assert preprocess.preparation.read_family_set(paths, name) == family_sets[name]


def test_identity_stage_writes_component_and_package_views(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    assignments = pl.DataFrame(
        {Column.ROW: [0, 1], Column.SHA256: ["a", "b"], Column.PACKAGE: ["p.a", "p.b"]}
    )
    identities = pl.DataFrame(
        {Column.ROW: [0, 1], Column.SHA256: ["a", "b"], Column.FEATURE_ID: [1, 2]}
    )
    summary = pl.DataFrame({Column.ROWS: [1, 1]})
    write_table(assignments, paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    monkeypatch.setattr(preprocess, "reuse_stage", Mock(return_value=False))
    monkeypatch.setattr(preprocess, "load_features", Mock(return_value=np.zeros((2, 2))))
    monkeypatch.setattr(preprocess.preparation, "build_identities", Mock(return_value=identities))
    monkeypatch.setattr(preprocess.preparation, "component_summary", Mock(return_value=summary))

    report = preprocess.identity_stage(paths, _report(tmp_path, Stage.CLIENTS), False)

    assert report.stage is Stage.IDENTITY
    assert paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS).is_file()
    assert paths.stage_file(Stage.IDENTITY, Artifact.FEATURE_IDENTITIES).is_file()
    assert paths.stage_file(Stage.IDENTITY, Artifact.PACKAGE_IDENTITIES).is_file()
    assert paths.stage_file(Stage.IDENTITY, Artifact.COMPONENT_SUMMARY).is_file()


def test_clients_stage_saves_aligned_features_and_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    client_names = list(ClientId)
    hashes = [f"sha-{index}" for index in range(len(client_names))]
    assignments = pl.DataFrame(
        {
            Column.SHA256: hashes,
            Column.CLIENT: [name.value for name in client_names],
            Column.LABEL: [1] * len(client_names),
            Column.PACKAGE: [f"package-{index}" for index in range(len(client_names))],
        }
    )
    metadata = pl.DataFrame({Column.SHA256: hashes, Column.LABEL: [1] * len(hashes)})
    lamda = LamdaTable(
        metadata=metadata,
        features=np.ones((len(hashes), 2), dtype=np.uint8),
        non_binary_cells=0,
        negative_cells=0,
    )
    support = pl.DataFrame(
        {
            Column.CLIENT: [name.value for name in client_names],
            Column.ROWS: [1] * len(client_names),
            Column.MALWARE_ROWS: [1] * len(client_names),
        }
    )
    write_table(pl.DataFrame(), paths.stage_file(Stage.JOINED, Artifact.DATASET))
    save_features = Mock()
    monkeypatch.setattr(preprocess, "reuse_stage", Mock(return_value=False))
    monkeypatch.setattr(preprocess.preparation, "assign_clients", Mock(return_value=assignments))
    monkeypatch.setattr(preprocess.sources, "load_lamda", Mock(return_value=lamda))
    monkeypatch.setattr(preprocess, "save_features", save_features)
    monkeypatch.setattr(preprocess.preparation, "client_support", Mock(return_value=support))
    monkeypatch.setattr(preprocess, "record_validations", Mock())

    report = preprocess.clients_stage(paths, CONFIG, _report(tmp_path, Stage.JOINED), False)

    assert report.stage is Stage.CLIENTS
    assert paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS).is_file()
    assert paths.stage_file(Stage.CLIENTS, Artifact.SUPPORT).is_file()
    save_features.assert_called_once()
