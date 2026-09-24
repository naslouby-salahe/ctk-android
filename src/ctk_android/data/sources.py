import hashlib

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.csv as pacsv

from ctk_android.config import DataConfig
from ctk_android.data.cache import combine_fingerprints, fingerprint_file
from ctk_android.enums import (
    AndroZooColumn,
    Column,
    DatasetName,
    FailureReason,
    LamdaColumn,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    ByteMatrix,
    CtkError,
    Directory,
    FeatureColumn,
    FeatureCount,
    File,
    Fingerprint,
    InventoryEntry,
    LamdaTable,
    SourceFingerprint,
    SourceInventory,
    StatKey,
    ValidationRecord,
)

FEATURE_PREFIX = "feat_"
ANDROZOO_BLOCK_BYTES = 1 << 26


def _stat_key(path: File) -> StatKey:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def fingerprint_files(
    dataset: DatasetName, root: Directory, files: list[File], known: SourceInventory
) -> tuple[SourceFingerprint, SourceInventory]:
    previous = {entry.name: entry for entry in known.entries}
    entries: list[InventoryEntry] = []
    for path in files:
        name = f"{path.relative_to(root)}"
        stat_key = _stat_key(path)
        entry = previous.get(name)
        digest = (
            entry.digest if entry is not None and entry.stat == stat_key else fingerprint_file(path)
        )
        entries.append(InventoryEntry(name=name, stat=stat_key, digest=digest))
    listing = "\n".join(f"{entry.name}:{entry.digest}" for entry in entries)
    fingerprint = SourceFingerprint(
        dataset=dataset,
        fingerprint=hashlib.sha256(listing.encode()).hexdigest(),
        file_count=len(files),
        total_bytes=sum(path.stat().st_size for path in files),
    )
    return fingerprint, SourceInventory(entries=tuple(entries))


def fingerprint_lamda(
    paths: Paths, config: DataConfig, known: SourceInventory
) -> tuple[SourceFingerprint, SourceInventory]:
    files = paths.lamda_release_files(config.lamda_release)
    return fingerprint_files(DatasetName.LAMDA, paths.raw_data(DatasetName.LAMDA), files, known)


def fingerprint_androzoo(
    paths: Paths, known: SourceInventory
) -> tuple[SourceFingerprint, SourceInventory]:
    return fingerprint_files(
        DatasetName.ANDROZOO,
        paths.raw_data(DatasetName.ANDROZOO),
        [paths.androzoo_archive()],
        known,
    )


def sources_fingerprint(lamda: SourceFingerprint, androzoo: SourceFingerprint) -> Fingerprint:
    return combine_fingerprints(lamda.fingerprint, androzoo.fingerprint)


def _feature_columns(count: FeatureCount) -> list[FeatureColumn]:
    return [f"{FEATURE_PREFIX}{index}" for index in range(count)]


def load_lamda(paths: Paths, config: DataConfig) -> LamdaTable:
    files = paths.lamda_release_files(config.lamda_release)[:-1]
    if not files:
        raise CtkError(FailureReason.SCHEMA_MISMATCH, "no LAMDA parquet files found")
    feature_names = _feature_columns(config.expected_features)
    frames: list[pl.DataFrame] = []
    blocks: list[ByteMatrix] = []
    non_binary = 0
    negative = 0
    for path in files:
        frame = pl.read_parquet(path)
        missing = set(feature_names) - set(frame.columns)
        extra = {c for c in frame.columns if c.startswith(FEATURE_PREFIX)} - set(feature_names)
        if missing or extra:
            raise CtkError(FailureReason.SCHEMA_MISMATCH, f"{path.name}: feature columns differ")
        raw = frame.select(feature_names).to_numpy()
        non_binary += (raw > 1).sum().item()
        negative += (raw < 0).sum().item()
        blocks.append((raw > 0).astype(np.uint8))
        frames.append(
            frame.select(
                pl.col(LamdaColumn.HASH).str.to_lowercase().alias(Column.SHA256),
                pl.col(LamdaColumn.LABEL).alias(Column.LABEL),
                pl.col(LamdaColumn.FAMILY).alias(Column.FAMILY),
                pl.col(LamdaColumn.VT_COUNT).alias(Column.VT_COUNT),
                pl.col(LamdaColumn.YEAR_MONTH).alias(Column.YEAR_MONTH),
            )
        )
    metadata = pl.concat(frames)
    features = np.concatenate(blocks)
    order = np.argsort(metadata[Column.SHA256].to_numpy(), kind="stable")
    return LamdaTable(
        metadata=metadata[order],
        features=features[order],
        non_binary_cells=non_binary,
        negative_cells=negative,
    )


def validate_lamda(table: LamdaTable, config: DataConfig) -> list[ValidationRecord]:
    metadata = table.metadata
    label = pl.col(Column.LABEL)
    vt = pl.col(Column.VT_COUNT)
    malware_ok = metadata.filter(label == 1).select((vt >= config.malware_min_vt).all()).item()
    benign_ok = metadata.filter(label == 0).select((vt == config.benign_vt).all()).item()
    rows = table.features.shape[0]
    return [
        ValidationRecord(
            check=ValidationCheck.FEATURE_CONTRACT,
            passed=table.features.shape[1] == config.expected_features
            and rows == config.expected_rows
            and table.negative_cells == 0,
            detail=(
                f"rows={rows} features={table.features.shape[1]} "
                f"non_binary_cells_binarized={table.non_binary_cells}"
            ),
        ),
        ValidationRecord(
            check=ValidationCheck.SHA_UNIQUENESS,
            passed=metadata[Column.SHA256].n_unique() == metadata.height,
            detail=f"unique={metadata[Column.SHA256].n_unique()} of {metadata.height}",
        ),
        ValidationRecord(
            check=ValidationCheck.LABEL_RULE,
            passed=malware_ok and benign_ok,
            detail=(
                f"malware>={config.malware_min_vt}={malware_ok} "
                f"benign=={config.benign_vt}={benign_ok}"
            ),
        ),
    ]


def scan_androzoo(paths: Paths, wanted: pl.Series) -> pl.DataFrame:
    wanted_upper = wanted.str.to_uppercase()
    reader = pacsv.open_csv(
        paths.androzoo_archive(),
        read_options=pacsv.ReadOptions(block_size=ANDROZOO_BLOCK_BYTES),
        convert_options=pacsv.ConvertOptions(
            include_columns=[column for column in AndroZooColumn],
            column_types={
                AndroZooColumn.SHA256: pa.string(),
                AndroZooColumn.PACKAGE: pa.string(),
                AndroZooColumn.MARKETS: pa.string(),
                AndroZooColumn.VT_DETECTION: pa.float64(),
            },
        ),
    )
    frame = pl.concat(
        [
            pl.DataFrame(pa.Table.from_batches([batch])).filter(
                pl.col(AndroZooColumn.SHA256).is_in(wanted_upper.implode())
            )
            for batch in reader
        ]
    )
    return frame.select(
        pl.col(AndroZooColumn.SHA256).str.to_lowercase().alias(Column.SHA256),
        pl.col(AndroZooColumn.PACKAGE).alias(Column.PACKAGE),
        pl.col(AndroZooColumn.MARKETS).alias(Column.MARKETS),
        pl.col(AndroZooColumn.VT_DETECTION).alias(Column.VT_COUNT),
    )
