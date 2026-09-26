import hashlib
from pathlib import Path
from typing import NamedTuple

import numpy as np
import polars as pl
import scipy.sparse as sp

from ctk_android.data import cache, preparation
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    DatasetName,
    FamilySetName,
    McNdroidDirectory,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import FamilySetDocument, Provenance

STATIC_WIDTH = 5
GRAPH_WIDTH = 4
REPORT_WIDTH = 6


def sha(index: int) -> str:
    return f"{index:064x}"


def _base(root: Path, directory: McNdroidDirectory) -> Path:
    return (
        Paths(root).raw_data(DatasetName.MCNDROID)
        / directory
        / McNdroidDirectory.PROCESSED
        / McNdroidDirectory.BASELINE_YEAR
        / "2013"
    )


def _write_sparse(path: Path, matrix: np.ndarray) -> None:
    csr = sp.csr_matrix(matrix)
    np.savez(path, data=csr.data, indices=csr.indices, indptr=csr.indptr, shape=np.array(csr.shape))


class Written(NamedTuple):
    static: dict[int, np.ndarray]
    graph: dict[int, np.ndarray]
    report: dict[int, np.ndarray]


def write_mcndroid(root: Path, splits: dict[str, list[int]]) -> Written:
    """Write three tiny McNdroid representations; returns the dense rows by sample index."""
    rng = np.random.default_rng(3)
    written = Written({}, {}, {})
    for split, members in splits.items():
        hashes = np.array([sha(index) for index in members], dtype=object)
        static = (rng.random((len(members), STATIC_WIDTH)) < 0.5).astype(np.float32)
        graph = (rng.random((len(members), GRAPH_WIDTH)) * 4).astype(np.float32)
        values = np.round(rng.normal(size=(len(members), REPORT_WIDTH)) * 5) * (
            rng.random((len(members), REPORT_WIDTH)) < 0.7
        )
        for position, index in enumerate(members):
            written.static[index] = static[position]
            written.graph[index] = graph[position]
            written.report[index] = values[position]
        static_dir = _base(root, McNdroidDirectory.STATIC)
        report_dir = _base(root, McNdroidDirectory.REPORT_JSON) / "2013"
        graph_dir = _base(root, McNdroidDirectory.CALL_GRAPH)
        for directory in (static_dir, report_dir, graph_dir):
            directory.mkdir(parents=True, exist_ok=True)
        _write_sparse(static_dir / f"{split}_X.npz", static)
        np.savez(static_dir / f"{split}_meta.npz", y=np.zeros(len(members)), hash=hashes)
        _write_sparse(report_dir / f"{split}_X.npz", values)
        np.savez(report_dir / f"{split}_meta.npz", y=np.zeros(len(members)), hashes=hashes)
        np.savez(graph_dir / f"{split}_X_y.npz", X=graph, y=np.zeros(len(members)), hash=hashes)
    return written


PRIMARY = ("f0", "f1")
REPLICATION = ("f2",)


def write_lamda(root: Path, rows: int, width: int) -> np.ndarray:
    """Write the LAMDA-side preprocessing outputs (clients, identity, features, family sets)."""
    paths = Paths(root)
    clients = list(ClientId)
    families = [*PRIMARY, *REPLICATION]
    draw = np.random.default_rng(11)
    client_of = draw.integers(0, len(clients), size=rows)
    family_of = draw.integers(0, len(families), size=rows)
    columns = [
        pl.Series(Column.SHA256, [sha(index) for index in range(rows)]),
        pl.Series(Column.PACKAGE, [f"pkg{index}" for index in range(rows)]),
        pl.Series(Column.LABEL, [index % 2 for index in range(rows)]),
        pl.Series(
            Column.FAMILY,
            [families[family_of[index]] if index % 2 else "benign" for index in range(rows)],
        ),
        pl.Series(Column.VT_COUNT, [5] * rows),
        pl.Series(Column.YEAR_MONTH, ["2020-01"] * rows),
        pl.Series(Column.CLIENT, [clients[client_of[index]] for index in range(rows)]),
    ]
    assignments = pl.DataFrame(columns).with_row_index(Column.ROW)
    features = (np.random.default_rng(5).random((rows, width)) < 0.5).astype(np.uint8)
    cache.write_table(assignments, paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    cache.write_table(
        preparation.build_identities(assignments, features),
        paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS),
    )
    cache.save_features(paths.cache_file(Artifact.FEATURES), features)
    for stage in (Stage.CLIENTS, Stage.IDENTITY, Stage.FAMILIES):
        digest = hashlib.sha256(stage.encode()).hexdigest()
        cache.write_provenance(
            paths.provenance_file(paths.stage_dir(stage)), Provenance(stage=stage, inputs=digest)
        )
    for name, members in (
        (FamilySetName.PRIMARY, PRIMARY),
        (FamilySetName.REPLICATION, REPLICATION),
    ):
        cache.write_record(paths.family_set_file(name), FamilySetDocument(families=members))
    return features
