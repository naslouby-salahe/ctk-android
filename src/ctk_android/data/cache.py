import hashlib
from collections.abc import Sequence

import numpy as np
import polars as pl
from pydantic import BaseModel

from ctk_android.config import Config
from ctk_android.enums import ByteBlock, LibraryOption, Separator, SourceFile, Stage, TextEncoding
from ctk_android.paths import Paths
from ctk_android.types import (
    ByteMatrix,
    Directory,
    File,
    Fingerprint,
    FrozenRecord,
    PartitionKey,
    Provenance,
    RunInputs,
    RunKey,
    TargetPair,
)


def fingerprint_file(path: File) -> Fingerprint:
    digest = hashlib.sha256()
    with path.open(LibraryOption.READ_BINARY) as handle:
        while chunk := handle.read(ByteBlock.HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def combine_fingerprints(*parts: Fingerprint) -> Fingerprint:
    return hashlib.sha256(Separator.NEWLINE.join(parts).encode()).hexdigest()


def fingerprint_model(model: BaseModel) -> Fingerprint:
    return hashlib.sha256(model.model_dump_json().encode()).hexdigest()


def fingerprint_source_tree(source_root: Directory) -> Fingerprint:
    files = sorted(source_root.rglob(SourceFile.PYTHON_GLOB))
    parts = [
        Separator.COLON.join((f"{path.relative_to(source_root)}", fingerprint_file(path)))
        for path in files
    ]
    return hashlib.sha256(Separator.NEWLINE.join(parts).encode()).hexdigest()


def write_provenance(file: File, provenance: Provenance) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(provenance.model_dump_json(indent=2), encoding=TextEncoding.UTF8)


def is_reusable(file: File, expected: Provenance) -> bool:
    if not file.is_file():
        return False
    return Provenance.model_validate_json(file.read_text(encoding=TextEncoding.UTF8)) == expected


def save_features(path: File, features: ByteMatrix) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, features, allow_pickle=False)


def load_features(path: File) -> ByteMatrix:
    return np.load(path, mmap_mode=LibraryOption.MMAP_READ, allow_pickle=False)


def write_record(path: File, record: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding=TextEncoding.UTF8)


def read_record[Record: BaseModel](path: File, model: type[Record]) -> Record:
    return model.model_validate_json(path.read_text(encoding=TextEncoding.UTF8))


def write_table(frame: pl.DataFrame, path: File) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)


def records_to_frame(rows: Sequence[FrozenRecord]) -> pl.DataFrame:
    return pl.DataFrame([row.model_dump() for row in rows]) if rows else pl.DataFrame()


def run_provenance(
    paths: Paths, config: Config, key: RunKey, targets: tuple[TargetPair, ...]
) -> Provenance:
    spec = config.experiments.experiments[key.experiment]
    partition_key = PartitionKey(
        seed=key.seed, salt=key.salt, grouping=spec.grouping, profile=spec.eligibility
    )
    inputs = RunInputs(
        key=key,
        partition=read_record(
            paths.provenance_file(paths.partition_dir(partition_key)), Provenance
        ),
        config=config.fingerprint(),
        targets=targets,
    )
    return Provenance(
        stage=Stage.RUNS,
        inputs=fingerprint_model(inputs),
        code=fingerprint_source_tree(paths.source_root),
    )
