import gzip

import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import AndroZooColumn, DatasetName, FeatureNaming, LamdaColumn
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)
CONFIG = load_config(PATHS)


def _require(available: bool) -> None:
    if not available:
        pytest.skip("raw data is not available in this checkout")


def test_lamda_parquet_schema_matches_the_source_contract() -> None:
    _require(PATHS.raw_data(DatasetName.LAMDA).is_dir())
    first = PATHS.lamda_release_files(CONFIG.data.lamda_release)[0]
    schema = pl.read_parquet_schema(first)
    features = [name for name in schema if name.startswith(FeatureNaming.PREFIX)]
    assert len(features) == CONFIG.data.expected_features
    assert set(LamdaColumn) <= set(schema)
    assert all(schema[name] == pl.Int8 for name in features)


def test_lamda_feature_mapping_lists_every_feature() -> None:
    _require(PATHS.raw_data(DatasetName.LAMDA).is_dir())
    mapping = pl.read_csv(PATHS.lamda_release_files(CONFIG.data.lamda_release)[-1])
    assert mapping.height == CONFIG.data.expected_features


def test_androzoo_header_contains_the_mapped_columns() -> None:
    _require(PATHS.androzoo_archive().is_file())
    with gzip.open(PATHS.androzoo_archive(), "rt", encoding="utf-8") as handle:
        header = handle.readline().strip().split(",")
    assert set(AndroZooColumn) <= set(header)
