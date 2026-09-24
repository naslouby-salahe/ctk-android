import hashlib
import json
from pathlib import Path

import numpy as np
import polars as pl

from ctk_android.types import (
    ByteMatrix,
    Directory,
    File,
    Fingerprint,
    JsonDocument,
    Provenance,
)

MANIFEST_NAME = "provenance.json"
CHUNK_BYTES = 1 << 22


def fingerprint_file(path: File) -> Fingerprint:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def combine_fingerprints(*parts: Fingerprint) -> Fingerprint:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def fingerprint_document(document: JsonDocument) -> Fingerprint:
    return hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()


def fingerprint_source_tree(source_root: Directory) -> Fingerprint:
    files = sorted(source_root.rglob("*.py"))
    parts = [f"{path.relative_to(source_root)}:{fingerprint_file(path)}" for path in files]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def write_provenance(directory: Directory, provenance: Provenance) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / MANIFEST_NAME).write_text(provenance.model_dump_json(indent=2), encoding="utf-8")


def is_reusable(directory: Directory, expected: Provenance) -> bool:
    manifest = directory / MANIFEST_NAME
    if not manifest.is_file():
        return False
    return Provenance.model_validate_json(manifest.read_text(encoding="utf-8")) == expected


def save_features(path: File, features: ByteMatrix) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, features, allow_pickle=False)


def load_features(path: File) -> ByteMatrix:
    return np.load(path, mmap_mode="r", allow_pickle=False)


def write_json(path: File, document: JsonDocument) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> JsonDocument:
    return json.loads(path.read_text(encoding="utf-8"))


def write_table(frame: pl.DataFrame, path: File) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)
