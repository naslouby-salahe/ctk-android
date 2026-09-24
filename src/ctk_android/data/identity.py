import numpy as np
import polars as pl
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from ctk_android.enums import Column, Grouping
from ctk_android.types import ByteMatrix, IntArray


def _first_occurrence_ids(labels: IntArray) -> IntArray:
    _, first_index, inverse = np.unique(labels, return_index=True, return_inverse=True)
    rank = np.empty(first_index.size, dtype=np.int64)
    rank[np.argsort(first_index, kind="stable")] = np.arange(first_index.size)
    return rank[inverse.reshape(-1)]


def feature_identities(features: ByteMatrix) -> IntArray:
    packed = np.ascontiguousarray(np.packbits(features, axis=1))
    voids = packed.view(np.dtype((np.void, packed.shape[1]))).reshape(-1)
    _, inverse = np.unique(voids, return_inverse=True)
    return _first_occurrence_ids(inverse.reshape(-1).astype(np.int64))


def package_identities(packages: pl.Series) -> IntArray:
    return _first_occurrence_ids(packages.rank("dense").to_numpy().astype(np.int64))


def connected_component_ids(package_ids: IntArray, feature_ids: IntArray) -> IntArray:
    rows = package_ids.size
    package_count = int(package_ids.max(initial=-1)) + 1
    feature_count = int(feature_ids.max(initial=-1)) + 1
    row_index = np.arange(rows)
    sources = np.concatenate([row_index, row_index])
    targets = np.concatenate([rows + package_ids, rows + package_count + feature_ids])
    nodes = rows + package_count + feature_count
    graph = coo_matrix((np.ones(sources.size, dtype=np.int8), (sources, targets)), shape=(nodes, nodes))
    _, labels = connected_components(graph, directed=False)
    return _first_occurrence_ids(labels[:rows].astype(np.int64))


def build_identities(assignments: pl.DataFrame, features: ByteMatrix) -> pl.DataFrame:
    package_ids = package_identities(assignments[Column.PACKAGE])
    feature_ids = feature_identities(features)
    return pl.DataFrame(
        {
            Column.SHA256: assignments[Column.SHA256],
            Column.PACKAGE_ID: package_ids,
            Column.FEATURE_ID: feature_ids,
            Column.COMPONENT: connected_component_ids(package_ids, feature_ids),
        }
    ).with_row_index(Column.ROW)


def grouping_ids(identities: pl.DataFrame, grouping: Grouping) -> IntArray:
    column = Column.COMPONENT if grouping is Grouping.COMPONENT else Column.PACKAGE_ID
    return identities[column].to_numpy().astype(np.int64)


def component_summary(identities: pl.DataFrame, assignments: pl.DataFrame) -> pl.DataFrame:
    return (
        identities.with_columns(assignments[Column.LABEL])
        .group_by(Column.COMPONENT)
        .agg(
            pl.len().alias(Column.ROWS),
            (pl.col(Column.LABEL) == 1).sum().alias(Column.MALWARE_ROWS),
            pl.col(Column.PACKAGE_ID).n_unique().alias(Column.PACKAGES),
        )
        .sort(Column.COMPONENT)
    )
