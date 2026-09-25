from pathlib import Path

import numpy as np
import polars as pl
import pytest
import scipy.sparse as sp

from ctk_android.config import load_config
from ctk_android.data import cache, families, identity, representation
from ctk_android.enums import (
    Artifact,
    Column,
    EligibilityProfile,
    ExperimentName,
    Grouping,
    Representation,
)
from ctk_android.paths import Paths
from ctk_android.types import OverlapManifest, PartitionKey
from tests.architecture.source_index import REPO_ROOT
from tests.unit.data.mcndroid_fixture import (
    GRAPH_WIDTH,
    REPORT_WIDTH,
    sha,
    write_lamda,
    write_mcndroid,
)

CONFIG = load_config(Paths(REPO_ROOT))
LAMDA_ROWS = 80
OVERLAP = list(range(10, 60))
SPLITS = {"train": OVERLAP[:35], "test": OVERLAP[35:], "extra": [200, 201]}
UNIVERSE = ("f0", "f1")
KEY = PartitionKey(seed=1, salt=0, grouping=Grouping.COMPONENT, profile=EligibilityProfile.PRIMARY)


def _workspace(root: Path) -> tuple[Paths, np.ndarray]:
    features = write_lamda(root, LAMDA_ROWS, 12)
    write_mcndroid(root, {"train": SPLITS["train"], "test": SPLITS["test"]})
    return Paths(root), features


def test_overlap_keeps_rows_present_in_every_source_in_lamda_order() -> None:
    assignments = pl.DataFrame(
        {Column.SHA256: [sha(3), sha(1), sha(2), sha(0)], Column.ROW: [0, 1, 2, 3]}
    )
    both = [pl.Series([sha(2), sha(1), sha(9)]), pl.Series([sha(1), sha(2), sha(0)])]
    kept = representation.overlap_table(assignments, both)
    assert kept[Column.SHA256].to_list() == [sha(1), sha(2)]
    assert kept[Column.SOURCE_ROW].to_list() == [1, 2]
    assert kept[Column.ROW].to_list() == [0, 1]


def test_restricted_identities_keep_component_membership_with_dense_ids() -> None:
    assignments = pl.DataFrame({Column.SHA256: [sha(index) for index in range(6)]}).with_row_index(
        Column.ROW
    )
    features = np.array([[1, 0], [1, 0], [0, 1], [0, 1], [1, 1], [0, 0]], dtype=np.uint8)
    packages = pl.DataFrame({Column.PACKAGE: ["a", "b", "b", "c", "d", "e"]})
    full = identity.build_identities(assignments.with_columns(packages), features)
    overlap = representation.overlap_table(assignments, [pl.Series([sha(1), sha(3), sha(4)])])
    restricted = representation.restrict_identities(full, overlap)
    assert restricted[Column.ROW].to_list() == [0, 1, 2]
    assert restricted[Column.SHA256].to_list() == [sha(1), sha(3), sha(4)]
    assert restricted[Column.COMPONENT].to_list() == [0, 0, 1]
    for column in (Column.PACKAGE_ID, Column.FEATURE_ID, Column.COMPONENT):
        assert restricted[column].max() == restricted[column].n_unique() - 1


def test_signed_log_keeps_sign_and_compresses_magnitude() -> None:
    dense = np.array([[3.0, -2.0, 0.0], [1.0, -5.0, 0.0], [0.0, -1.0, 4.0], [0.0, 0.0, 0.0]])
    transformed = representation.signed_log(sp.csr_matrix(dense.astype(np.float32))).toarray()
    np.testing.assert_allclose(transformed, np.sign(dense) * np.log1p(np.abs(dense)), rtol=1e-6)


def test_csr_round_trip_preserves_structure_and_precision(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    dense = np.array([[0.0, 1.5, 0.0], [2.25, 0.0, -3.0]], dtype=np.float32)
    for kind, half in ((Representation.CALL_GRAPH, False), (Representation.REPORT_JSON, True)):
        files = representation.csr_files(paths, kind)
        representation.save_csr(files, sp.csr_matrix(dense), half=half)
        restored = representation.load_csr(files, 3)
        np.testing.assert_array_equal(restored.toarray(), dense)
    assert (
        np.load(representation.csr_files(paths, Representation.REPORT_JSON).data).dtype
        == np.float16
    )
    assert (
        np.load(representation.csr_files(paths, Representation.CALL_GRAPH).data).dtype == np.float32
    )


def test_binary_rows_reads_the_requested_positions_as_bytes() -> None:
    matrix = sp.csr_matrix(np.array([[1, 0], [0, 1], [1, 1]], dtype=np.float32))
    rows = representation.binary_rows(matrix, np.array([2, 0]))
    assert rows.dtype == np.uint8
    assert rows.tolist() == [[1, 1], [1, 0]]


def test_namespace_aligns_every_representation_to_the_overlap_rows(tmp_path: Path) -> None:
    paths, lamda = _workspace(tmp_path)
    written = write_mcndroid(tmp_path, {"train": SPLITS["train"], "test": SPLITS["test"]})
    manifest = representation.build_namespace(paths)
    assert manifest.rows == len(OVERLAP) and manifest.lamda_rows == LAMDA_ROWS
    assert manifest.malware_rows + manifest.benign_rows == manifest.rows
    overlap = pl.read_parquet(paths.representation_file(Artifact.OVERLAP))
    assert overlap[Column.SOURCE_ROW].to_list() == OVERLAP
    r0 = cache.load_features(paths.representation_file(Artifact.LAMDA_R0_FEATURES))
    np.testing.assert_array_equal(r0, lamda[OVERLAP])
    r1 = cache.load_features(paths.representation_file(Artifact.MCNDROID_R1_FEATURES))
    np.testing.assert_array_equal(r1, np.stack([written.static[index] for index in OVERLAP]))
    graph = representation.load_csr(
        representation.csr_files(paths, Representation.CALL_GRAPH), manifest.graph_features
    )
    np.testing.assert_allclose(
        graph.toarray(), np.stack([written.graph[index] for index in OVERLAP])
    )
    assert all(record.passed for record in representation.namespace_validations(paths, manifest))
    assert (
        cache.read_record(paths.representation_file(Artifact.OVERLAP_MANIFEST), OverlapManifest)
        == manifest
    )
    report = representation.load_csr(
        representation.csr_files(paths, Representation.REPORT_JSON), manifest.json_columns_total
    )
    raw = np.stack([written.report[index] for index in OVERLAP])
    np.testing.assert_allclose(
        report.toarray(), np.sign(raw) * np.log1p(np.abs(raw)), rtol=1e-2, atol=1e-2
    )
    assert manifest.json_columns_total == REPORT_WIDTH and manifest.graph_features == GRAPH_WIDTH


def test_studies_load_raw_representations_and_leave_fitting_to_training(
    tmp_path: Path,
) -> None:
    paths, _ = _workspace(tmp_path)
    representation.build_namespace(paths)
    result = representation.build_seed_partition(paths, CONFIG, KEY, UNIVERSE)
    assert result.roles.len() == len(OVERLAP)
    assert all(validation.passed for validation in result.validations)
    representation.write_seed_partition(paths, KEY, result)
    assert paths.representation_partition_file(KEY, Artifact.CONTROLLED_PAIRS).is_file()
    expected_widths = {
        ExperimentName.REPRESENTATION_R0: 12,
        ExperimentName.REPRESENTATION_R1: 5,
        ExperimentName.REPRESENTATION_R2: GRAPH_WIDTH,
        ExperimentName.REPRESENTATION_R3: REPORT_WIDTH,
    }
    for name, width in expected_widths.items():
        spec = CONFIG.experiments.experiments[name]
        study = representation.load_study(paths, CONFIG, spec, KEY)
        assert study.features.shape == (len(OVERLAP), width)
        assert study.table.height == len(OVERLAP)
        assert study.table[Column.ROW].to_list() == list(range(len(OVERLAP)))
        rule = representation.transform_rule(spec.representation, CONFIG)
        fitted = spec.representation in (Representation.CALL_GRAPH, Representation.REPORT_JSON)
        assert (rule is not None) == fitted
    json_rule = representation.transform_rule(Representation.REPORT_JSON, CONFIG)
    assert json_rule is not None
    assert json_rule.min_prevalence == CONFIG.experiments.representation_min_prevalence


def test_a_missing_namespace_is_reported_when_a_study_is_loaded(tmp_path: Path) -> None:
    spec = CONFIG.experiments.experiments[ExperimentName.REPRESENTATION_R1]
    with pytest.raises(Exception, match="representation-preprocess"):
        representation.load_study(Paths(tmp_path), CONFIG, spec, KEY)


def test_the_partition_grouping_never_splits_a_component(tmp_path: Path) -> None:
    paths, _ = _workspace(tmp_path)
    representation.build_namespace(paths)
    result = representation.build_seed_partition(paths, CONFIG, KEY, UNIVERSE)
    identities = pl.read_parquet(paths.representation_file(Artifact.COMPONENTS))
    per_component = (
        identities.with_columns(result.roles.alias(Column.ROLE))
        .group_by(Column.COMPONENT)
        .agg(pl.col(Column.ROLE).n_unique().alias("roles"))
    )
    assert per_component["roles"].max() == 1
    labelled = families.classify_labels(
        pl.read_parquet(paths.representation_file(Artifact.OVERLAP)), CONFIG.data
    )
    assert labelled.height == len(OVERLAP)
