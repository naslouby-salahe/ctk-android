import gzip
from pathlib import Path

import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.data.sources import (
    fingerprint_files,
    load_lamda,
    scan_androzoo,
    validate_lamda,
)
from ctk_android.enums import (
    AndroZooColumn,
    Column,
    DatasetName,
    ErrorMessage,
    FailureReason,
    FeatureNaming,
    LamdaColumn,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import CtkError, SourceInventory
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))


def _lamda_paths(root: Path, frame: pl.DataFrame) -> Paths:
    paths = Paths(root)
    release = paths.raw_data(DatasetName.LAMDA) / CONFIG.data.lamda_release
    shard = release / "shard"
    shard.mkdir(parents=True)
    frame.write_parquet(shard / "part.parquet")
    return paths


def _lamda_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            LamdaColumn.HASH: ["B", "a"],
            LamdaColumn.LABEL: [1, 0],
            LamdaColumn.FAMILY: ["malware", "benign"],
            LamdaColumn.VT_COUNT: [CONFIG.data.malware_min_vt, CONFIG.data.benign_vt],
            LamdaColumn.YEAR_MONTH: ["2018-01", "2019-01"],
            f"{FeatureNaming.PREFIX}0": [2, 0],
            f"{FeatureNaming.PREFIX}1": [-1, 1],
        }
    )


def test_fingerprint_files_reuses_unchanged_entries_and_refreshes_changed_files(
    tmp_path: Path,
) -> None:
    root = tmp_path / "raw"
    root.mkdir()
    file = root / "one.csv"
    file.write_text("first", encoding="utf-8")
    initial = fingerprint_files(DatasetName.LAMDA, root, [file], SourceInventory(entries=()))

    cached = fingerprint_files(DatasetName.LAMDA, root, [file], initial.inventory)
    assert cached.fingerprint == initial.fingerprint
    assert cached.inventory == initial.inventory

    file.write_text("changed content", encoding="utf-8")
    changed = fingerprint_files(DatasetName.LAMDA, root, [file], initial.inventory)
    assert changed.fingerprint.fingerprint != initial.fingerprint.fingerprint
    assert changed.fingerprint.total_bytes == len("changed content")


def test_load_lamda_binarizes_and_sorts_metadata_then_validates_contract(tmp_path: Path) -> None:
    config = CONFIG.data.model_copy(update={"expected_rows": 2, "expected_features": 2})
    paths = _lamda_paths(tmp_path, _lamda_frame())

    table = load_lamda(paths, config)

    assert table.metadata[Column.SHA256].to_list() == ["a", "b"]
    assert table.features.tolist() == [[0, 1], [1, 0]]
    assert table.non_binary_cells == 1
    assert table.negative_cells == 1
    records = {record.check: record.passed for record in validate_lamda(table, config)}
    assert records == {
        ValidationCheck.FEATURE_CONTRACT: False,
        ValidationCheck.SHA_UNIQUENESS: True,
        ValidationCheck.LABEL_RULE: True,
    }


def test_lamda_loader_rejects_missing_files_and_feature_columns(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    config = CONFIG.data.model_copy(update={"expected_features": 2})
    release = paths.raw_data(DatasetName.LAMDA) / config.lamda_release
    shard = release / "shard"
    shard.mkdir(parents=True)
    with pytest.raises(CtkError) as no_files:
        load_lamda(paths, config)
    assert no_files.value.reason is FailureReason.SCHEMA_MISMATCH
    assert str(no_files.value) == ErrorMessage.NO_LAMDA_FILES

    invalid = _lamda_frame().drop(f"{FeatureNaming.PREFIX}1")
    invalid.write_parquet(shard / "part.parquet")
    with pytest.raises(CtkError, match="feature columns"):
        load_lamda(paths, config)


def test_lamda_validation_reports_duplicate_hashes_and_invalid_label_counts(
    tmp_path: Path,
) -> None:
    config = CONFIG.data.model_copy(update={"expected_rows": 2, "expected_features": 2})
    frame = _lamda_frame().with_columns(
        pl.lit("same").alias(LamdaColumn.HASH),
        pl.lit(0).alias(LamdaColumn.VT_COUNT),
    )
    table = load_lamda(_lamda_paths(tmp_path, frame), config)
    records = {record.check: record.passed for record in validate_lamda(table, config)}
    assert records[ValidationCheck.SHA_UNIQUENESS] is False
    assert records[ValidationCheck.LABEL_RULE] is False


def test_scan_androzoo_filters_requested_hashes_and_normalizes_case(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    archive = paths.androzoo_archive()
    archive.parent.mkdir(parents=True)
    with gzip.open(archive, "wt", encoding="utf-8") as stream:
        stream.write(
            f"{AndroZooColumn.SHA256},{AndroZooColumn.PACKAGE},{AndroZooColumn.MARKETS},{AndroZooColumn.VT_DETECTION}\n"
            "A1,first,play,12\nB2,second,anzhi,3\n"
        )

    table = scan_androzoo(paths, pl.Series(["a1"]))

    assert table.height == 1
    assert table[Column.SHA256].to_list() == ["a1"]
    assert table[Column.PACKAGE].to_list() == ["first"]
    assert table[Column.VT_COUNT].to_list() == [12.0]


def test_fingerprint_tracks_empty_input_with_empty_listing(tmp_path: Path) -> None:
    scan = fingerprint_files(DatasetName.ANDROZOO, tmp_path, [], SourceInventory(entries=()))
    assert scan.fingerprint.file_count == 0
    assert scan.fingerprint.total_bytes == 0
    assert scan.inventory.entries == ()
