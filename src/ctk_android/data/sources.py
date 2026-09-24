import hashlib

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

from ctk_android.config import DataConfig
from ctk_android.data.cache import combine_fingerprints, fingerprint_file
from ctk_android.enums import Column, DatasetName, FailureReason, ValidationCheck
from ctk_android.types import (
    ByteMatrix,
    CtkError,
    Directory,
    File,
    FeatureColumn,
    FeatureCount,
    Fingerprint,
    InventoryDocument,
    LamdaTable,
    ReleaseName,
    StatKey,
    SourceFingerprint,
    ValidationRecord,
)

FEATURE_PREFIX = "feat_"
LAMDA_HASH_COLUMN = "hash"
LAMDA_VT_COLUMN = "vt_count"
ANDROZOO_ARCHIVE = "latest.csv.gz"
ANDROZOO_BLOCK_BYTES = 1 << 26
ANDROZOO_SHA = "sha256"
ANDROZOO_PACKAGE = "pkg_name"
ANDROZOO_MARKETS = "markets"
ANDROZOO_VT = "vt_detection"
LAMDA_FEATURE_MAPPING = "feature_mapping.csv"


def lamda_files(root: Directory, release: ReleaseName) -> list[File]:
    release_dir = root / release
    parquets = sorted(release_dir.glob("*/*.parquet"))
    if not parquets:
        raise CtkError(FailureReason.SCHEMA_MISMATCH, f"no LAMDA parquet files under {release_dir}")
    return [*parquets, release_dir / LAMDA_FEATURE_MAPPING]


def _stat_key(path: File) -> StatKey:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def fingerprint_files(
    dataset: DatasetName, root: Directory, files: list[File], known: InventoryDocument
) -> tuple[SourceFingerprint, InventoryDocument]:
    inventory: InventoryDocument = {}
    parts: list[Fingerprint] = []
    for path in files:
        name = str(path.relative_to(root))
        entry = known.get(name)
        stat_key = _stat_key(path)
        digest = entry[1] if entry is not None and entry[0] == stat_key else fingerprint_file(path)
        inventory[name] = (stat_key, digest)
        parts.append(f"{name}:{digest}")
    fingerprint = SourceFingerprint(
        dataset=dataset,
        fingerprint=hashlib.sha256("\n".join(parts).encode()).hexdigest(),
        file_count=len(files),
        total_bytes=sum(path.stat().st_size for path in files),
    )
    return fingerprint, inventory


def fingerprint_lamda(
    root: Directory, config: DataConfig, known: InventoryDocument
) -> tuple[SourceFingerprint, InventoryDocument]:
    return fingerprint_files(DatasetName.LAMDA, root, lamda_files(root, config.lamda_release), known)


def fingerprint_androzoo(
    root: Directory, known: InventoryDocument
) -> tuple[SourceFingerprint, InventoryDocument]:
    return fingerprint_files(DatasetName.ANDROZOO, root, [root / ANDROZOO_ARCHIVE], known)


def sources_fingerprint(lamda: SourceFingerprint, androzoo: SourceFingerprint) -> Fingerprint:
    return combine_fingerprints(lamda.fingerprint, androzoo.fingerprint)


def _feature_columns(count: FeatureCount) -> list[FeatureColumn]:
    return [f"{FEATURE_PREFIX}{index}" for index in range(count)]


def load_lamda(root: Directory, config: DataConfig) -> LamdaTable:
    feature_names = _feature_columns(config.expected_features)
    frames: list[pl.DataFrame] = []
    blocks: list[ByteMatrix] = []
    non_binary = 0
    negative = 0
    for path in lamda_files(root, config.lamda_release)[:-1]:
        frame = pl.read_parquet(path)
        missing = set(feature_names) - set(frame.columns)
        extra = {c for c in frame.columns if c.startswith(FEATURE_PREFIX)} - set(feature_names)
        if missing or extra:
            raise CtkError(FailureReason.SCHEMA_MISMATCH, f"{path.name}: feature columns differ")
        raw = frame.select(feature_names).to_numpy()
        non_binary += int((raw > 1).sum())
        negative += int((raw < 0).sum())
        blocks.append((raw > 0).astype(np.uint8))
        frames.append(
            frame.select(
                pl.col(LAMDA_HASH_COLUMN).str.to_lowercase().alias(Column.SHA256),
                pl.col(Column.LABEL),
                pl.col(Column.FAMILY),
                pl.col(LAMDA_VT_COLUMN).alias(Column.VT_COUNT),
                pl.col(Column.YEAR_MONTH),
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
            passed=bool(malware_ok and benign_ok),
            detail=f"malware>={config.malware_min_vt}={malware_ok} benign=={config.benign_vt}={benign_ok}",
        ),
    ]


def scan_androzoo(root: Directory, wanted: pl.Series) -> pl.DataFrame:
    wanted_upper = pa.array(wanted.str.to_uppercase().to_list(), type=pa.string())
    reader = pacsv.open_csv(
        root / ANDROZOO_ARCHIVE,
        read_options=pacsv.ReadOptions(block_size=ANDROZOO_BLOCK_BYTES),
        convert_options=pacsv.ConvertOptions(
            include_columns=[ANDROZOO_SHA, ANDROZOO_PACKAGE, ANDROZOO_MARKETS, ANDROZOO_VT],
            column_types={
                ANDROZOO_SHA: pa.string(),
                ANDROZOO_PACKAGE: pa.string(),
                ANDROZOO_MARKETS: pa.string(),
                ANDROZOO_VT: pa.float64(),
            },
        ),
    )
    matched = [
        pa.Table.from_batches([batch.filter(pc.is_in(batch[ANDROZOO_SHA], value_set=wanted_upper))])
        for batch in reader
    ]
    frame = pl.from_arrow(pa.concat_tables(matched))
    if not isinstance(frame, pl.DataFrame):
        raise CtkError(FailureReason.SCHEMA_MISMATCH, "AndroZoo scan produced no table")
    return frame.select(
        pl.col(ANDROZOO_SHA).str.to_lowercase().alias(Column.SHA256),
        pl.col(ANDROZOO_PACKAGE).alias(Column.PACKAGE),
        pl.col(ANDROZOO_MARKETS).alias(Column.MARKETS),
        pl.col(ANDROZOO_VT).alias(Column.VT_COUNT),
    )


