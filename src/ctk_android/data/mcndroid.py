import numpy as np
import polars as pl
import scipy.sparse as sp

from ctk_android.data import sources
from ctk_android.enums import (
    Column,
    DatasetName,
    ErrorMessage,
    FailureReason,
    LibraryOption,
    McNdroidDirectory,
    McNdroidFile,
    McNdroidKey,
    McNdroidSplit,
    Representation,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CsrMatrix,
    CtkError,
    Directory,
    File,
    McNdroidShard,
    PositionArray,
    ShaBlock,
    ShaSeries,
    SourceInventory,
    SourceScan,
)


def kinds() -> tuple[Representation, ...]:
    return (
        Representation.MCNDROID_STATIC,
        Representation.REPORT_JSON,
        Representation.CALL_GRAPH,
    )


def _kind_directory(kind: Representation) -> McNdroidDirectory:
    if kind is Representation.MCNDROID_STATIC:
        return McNdroidDirectory.STATIC
    if kind is Representation.REPORT_JSON:
        return McNdroidDirectory.REPORT_JSON
    if kind is Representation.CALL_GRAPH:
        return McNdroidDirectory.CALL_GRAPH
    raise CtkError(
        FailureReason.SCHEMA_MISMATCH,
        ErrorMessage.UNKNOWN_REPRESENTATION.format(representation=kind),
    )


def _base(paths: Paths, kind: Representation) -> Directory:
    return (
        paths.raw_data(DatasetName.MCNDROID)
        / _kind_directory(kind)
        / McNdroidDirectory.PROCESSED
        / McNdroidDirectory.BASELINE_YEAR
    )


def shards(paths: Paths, kind: Representation) -> list[McNdroidShard]:
    base = _base(paths, kind)
    found: list[McNdroidShard] = []
    for year in sorted(entry for entry in base.iterdir() if entry.is_dir()):
        directory = year / year.name if kind is Representation.REPORT_JSON else year
        for split in McNdroidSplit:
            if kind is Representation.CALL_GRAPH:
                matrix = directory / McNdroidFile.GRAPH_MATRIX.format(split=split)
                meta = matrix
            else:
                matrix = directory / McNdroidFile.SPARSE_MATRIX.format(split=split)
                meta = directory / McNdroidFile.SPARSE_META.format(split=split)
            if matrix.is_file() and meta.is_file():
                found.append(McNdroidShard(matrix=matrix, meta=meta))
    if not found:
        raise CtkError(
            FailureReason.SCHEMA_MISMATCH,
            ErrorMessage.NO_MCNDROID_FILES.format(kind=kind, path=base),
        )
    return found


def source_files(paths: Paths) -> list[File]:
    return sorted(
        path
        for kind in kinds()
        for shard in shards(paths, kind)
        for path in {shard.matrix, shard.meta}
    )


def fingerprint_sources(paths: Paths, known: SourceInventory) -> SourceScan:
    return sources.fingerprint_files(
        DatasetName.MCNDROID, paths.raw_data(DatasetName.MCNDROID), source_files(paths), known
    )


def _hashes(shard: McNdroidShard) -> ShaSeries:
    with np.load(shard.meta, allow_pickle=True) as archive:
        key = McNdroidKey.HASH if McNdroidKey.HASH in archive.files else McNdroidKey.HASHES
        return pl.Series(archive[key].astype(str).tolist(), dtype=pl.String)


def kind_hashes(paths: Paths, kind: Representation) -> ShaSeries:
    return pl.concat([_hashes(shard) for shard in shards(paths, kind)])


def _sparse_rows(shard: McNdroidShard, kind: Representation) -> CsrMatrix:
    with np.load(shard.matrix, allow_pickle=True) as archive:
        if kind is Representation.CALL_GRAPH:
            return sp.csr_matrix(archive[McNdroidKey.GRAPH_X].astype(np.float32))
        return sp.csr_matrix(
            (
                archive[McNdroidKey.DATA].astype(np.float32),
                archive[McNdroidKey.INDICES],
                archive[McNdroidKey.INDPTR],
            ),
            shape=tuple(archive[McNdroidKey.SHAPE]),
        )


def load_wanted(paths: Paths, kind: Representation, wanted: ShaSeries) -> ShaBlock:
    blocks: list[CsrMatrix] = []
    kept: list[ShaSeries] = []
    for shard in shards(paths, kind):
        hashes = _hashes(shard)
        mask = hashes.is_in(wanted.implode()).to_numpy()
        if mask.any():
            blocks.append(_sparse_rows(shard, kind)[np.flatnonzero(mask)])
            kept.append(hashes.filter(pl.Series(mask)))
    return ShaBlock(shas=pl.concat(kept), matrix=sp.vstack(blocks, format=LibraryOption.SPARSE_CSR))


def alignment(block: ShaBlock, order: ShaSeries, kind: Representation) -> PositionArray:
    index = pl.DataFrame(
        {Column.SHA256: block.shas, Column.ROW_POSITION: np.arange(block.shas.len())}
    )
    positions = pl.DataFrame({Column.SHA256: order}).join(
        index, on=Column.SHA256, how=LibraryOption.JOIN_LEFT
    )[Column.ROW_POSITION]
    if positions.null_count():
        raise CtkError(
            FailureReason.SCHEMA_MISMATCH,
            ErrorMessage.ALIGNMENT_MISSING.format(count=positions.null_count(), kind=kind),
        )
    return positions.to_numpy()
