import hashlib

import numpy as np
import polars as pl
from pydantic import BaseModel, ValidationError

from ctk_android.config import Config
from ctk_android.enums import (
    ByteBlock,
    Column,
    ErrorMessage,
    FailureReason,
    LibraryOption,
    Separator,
    Stage,
    TextEncoding,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CtkError,
    FeatureMatrix,
    File,
    Fingerprint,
    LabelValues,
    PartitionKey,
    Predicate,
    Provenance,
    Records,
    Reusable,
    RunInputs,
    RunKey,
    Table,
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


def write_provenance(file: File, provenance: Provenance) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(provenance.model_dump_json(indent=2), encoding=TextEncoding.UTF8)


def is_reusable(file: File, expected: Provenance) -> Reusable:
    if not file.is_file():
        return False
    try:
        stored = Provenance.model_validate_json(file.read_text(encoding=TextEncoding.UTF8))
    except ValidationError:
        return False
    return stored == expected


def save_features(path: File, features: FeatureMatrix) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, features, allow_pickle=False)


def load_features(path: File) -> FeatureMatrix:
    return np.load(path, mmap_mode=LibraryOption.MMAP_READ, allow_pickle=False)


def write_record(path: File, record: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding=TextEncoding.UTF8)


def read_record[Record: BaseModel](path: File, model: type[Record]) -> Record:
    return model.model_validate_json(path.read_text(encoding=TextEncoding.UTF8))


def write_table(frame: Table, path: File) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)


def normalise_dose(frame: Table) -> Table:
    return frame.cast({Column.DOSE: pl.Int64}) if Column.DOSE in frame.columns else frame


def records_to_frame(rows: Records) -> Table:
    if not rows:
        return pl.DataFrame()
    return normalise_dose(pl.DataFrame([row.model_dump() for row in rows]))


def run_provenance(
    paths: Paths, config: Config, key: RunKey, targets: tuple[TargetPair, ...]
) -> Provenance:
    spec = config.experiments.experiments[key.experiment]
    partition_key = PartitionKey(
        seed=key.seed, salt=key.salt, grouping=spec.grouping, profile=spec.eligibility
    )
    partition_file = paths.provenance_file(paths.partition_dir(partition_key))
    try:
        partition = read_record(partition_file, Provenance)
    except (ValidationError, FileNotFoundError) as error:
        raise CtkError(
            FailureReason.SCHEMA_MISMATCH,
            ErrorMessage.STALE_PREPROCESSING.format(path=partition_file),
        ) from error
    inputs = RunInputs(
        key=key,
        partition=partition,
        config=config.fingerprint(),
        targets=targets,
    )
    return Provenance(stage=Stage.RUNS, inputs=fingerprint_model(inputs))


def is_one_of(column: Column, values: LabelValues) -> Predicate:
    return pl.col(column).is_in(pl.Series(values, dtype=pl.String).implode())
