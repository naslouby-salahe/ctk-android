from pathlib import Path

import numpy as np
import polars as pl
import pytest

from ctk_android.data import mcndroid
from ctk_android.enums import Representation
from ctk_android.paths import Paths
from ctk_android.types import CtkError, ShaBlock, SourceInventory
from tests.unit.data.mcndroid_fixture import (
    GRAPH_WIDTH,
    REPORT_WIDTH,
    STATIC_WIDTH,
    sha,
    write_mcndroid,
)

SPLITS = {"train": [10, 11, 12, 13], "test": [14, 15]}


def _paths(tmp_path: Path) -> Paths:
    write_mcndroid(tmp_path, SPLITS)
    return Paths(tmp_path)


def test_shards_cover_every_split_of_every_representation(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    for kind in mcndroid.kinds():
        assert len(mcndroid.shards(paths, kind)) == len(SPLITS)
    assert len(mcndroid.source_files(paths)) == 2 * len(SPLITS) * 2 + len(SPLITS)


def test_missing_source_files_are_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        mcndroid.shards(Paths(tmp_path), Representation.MCNDROID_STATIC)
    (tmp_path / "data/mcndroid/raw/data_feature/processed_data/init_2013").mkdir(parents=True)
    with pytest.raises(CtkError):
        mcndroid.shards(Paths(tmp_path), Representation.MCNDROID_STATIC)


def test_hashes_follow_shard_order_for_every_key_spelling(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    expected = [sha(index) for split in ("train", "test") for index in SPLITS[split]]
    for kind in mcndroid.kinds():
        assert mcndroid.kind_hashes(paths, kind).to_list() == expected


def test_only_wanted_rows_are_loaded_and_alignment_restores_the_requested_order(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    wanted = pl.Series([sha(15), sha(10), sha(13)], dtype=pl.String)
    widths = {
        Representation.MCNDROID_STATIC: STATIC_WIDTH,
        Representation.CALL_GRAPH: GRAPH_WIDTH,
        Representation.REPORT_JSON: REPORT_WIDTH,
    }
    for kind, width in widths.items():
        block = mcndroid.load_wanted(paths, kind, wanted)
        assert block.matrix.shape == (3, width)
        assert set(block.shas.to_list()) == set(wanted.to_list())
        positions = mcndroid.alignment(block, wanted, kind)
        assert block.shas.gather(positions).to_list() == wanted.to_list()


def test_alignment_rejects_rows_missing_from_the_shards(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    block = mcndroid.load_wanted(
        paths, Representation.MCNDROID_STATIC, pl.Series([sha(10)], dtype=pl.String)
    )
    assert isinstance(block, ShaBlock)
    with pytest.raises(CtkError):
        mcndroid.alignment(
            block, pl.Series([sha(10), sha(99)], dtype=pl.String), Representation.MCNDROID_STATIC
        )


def test_source_fingerprint_hashes_every_file_and_changes_with_content(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    scan = mcndroid.fingerprint_sources(paths, SourceInventory(entries=()))
    assert scan.fingerprint.file_count == len(mcndroid.source_files(paths))
    assert scan.fingerprint == mcndroid.fingerprint_sources(paths, scan.inventory).fingerprint
    target = mcndroid.source_files(paths)[0]
    target.write_bytes(target.read_bytes() + np.zeros(1, dtype=np.uint8).tobytes())
    changed = mcndroid.fingerprint_sources(paths, scan.inventory)
    assert changed.fingerprint.fingerprint != scan.fingerprint.fingerprint
