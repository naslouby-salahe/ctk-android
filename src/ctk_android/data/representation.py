import numpy as np
import polars as pl
import scipy.sparse as sp

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data import cache, families, identity, mcndroid, partitions
from ctk_android.enums import (
    Artifact,
    Column,
    DetailMessage,
    ErrorMessage,
    FailureReason,
    LibraryOption,
    LogEvent,
    LogField,
    Representation,
    RowBlock,
    Stage,
    ValidationCheck,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.types import (
    AssignmentsTable,
    BinaryMatrix,
    CsrFiles,
    CsrMatrix,
    CtkError,
    ExperimentSpec,
    FamilyName,
    FeatureCount,
    FeatureMatrix,
    File,
    HalfPrecision,
    IdentitiesTable,
    OverlapManifest,
    PartitionKey,
    PartitionResult,
    PositionArray,
    ShaSeries,
    StudyData,
    TransformRule,
    ValidationRecord,
)


def overlap_table(assignments: AssignmentsTable, hashes: list[ShaSeries]) -> AssignmentsTable:
    present = assignments[Column.SHA256]
    for shas in hashes:
        present = present.filter(present.is_in(shas.implode()))
    return (
        assignments.filter(pl.col(Column.SHA256).is_in(present.implode()))
        .rename({Column.ROW: Column.SOURCE_ROW})
        .with_row_index(Column.ROW)
    )


def restrict_identities(identities: IdentitiesTable, overlap: AssignmentsTable) -> IdentitiesTable:
    kept = identities.filter(pl.col(Column.ROW).is_in(overlap[Column.SOURCE_ROW].implode())).drop(
        Column.ROW
    )
    dense = [
        (pl.col(column).rank(LibraryOption.RANK_DENSE).cast(pl.Int64) - 1).alias(column)
        for column in (Column.PACKAGE_ID, Column.FEATURE_ID, Column.COMPONENT)
    ]
    return kept.with_columns(*dense).with_row_index(Column.ROW)


def binary_rows(matrix: CsrMatrix, positions: PositionArray) -> BinaryMatrix:
    out = np.empty((positions.size, matrix.shape[1]), dtype=np.uint8)
    for start in range(0, positions.size, RowBlock.STANDARDISATION):
        stop = start + RowBlock.STANDARDISATION
        out[start:stop] = matrix[positions[start:stop]].toarray()
    return out


def csr_files(paths: Paths, representation: Representation) -> CsrFiles:
    if representation is Representation.CALL_GRAPH:
        return CsrFiles(
            data=paths.representation_file(Artifact.GRAPH_DATA),
            indices=paths.representation_file(Artifact.GRAPH_INDICES),
            indptr=paths.representation_file(Artifact.GRAPH_INDPTR),
        )
    return CsrFiles(
        data=paths.representation_file(Artifact.JSON_DATA),
        indices=paths.representation_file(Artifact.JSON_INDICES),
        indptr=paths.representation_file(Artifact.JSON_INDPTR),
    )


def save_csr(files: CsrFiles, matrix: CsrMatrix, half: HalfPrecision) -> None:
    files.data.parent.mkdir(parents=True, exist_ok=True)
    np.save(files.data, matrix.data.astype(np.float16 if half else np.float32))
    np.save(files.indices, matrix.indices.astype(np.int32))
    np.save(files.indptr, matrix.indptr.astype(np.int64))


def load_csr(files: CsrFiles, width: FeatureCount) -> CsrMatrix:
    indptr = np.load(files.indptr)
    return sp.csr_matrix(
        (np.load(files.data).astype(np.float32), np.load(files.indices), indptr),
        shape=(indptr.size - 1, width),
    )


def signed_log(matrix: CsrMatrix) -> CsrMatrix:
    transformed = matrix.copy()
    transformed.data = np.sign(matrix.data) * np.log1p(np.abs(matrix.data))
    return transformed


def build_namespace(paths: Paths) -> OverlapManifest:
    watch = Stopwatch()
    assignments = pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.ASSIGNMENTS))
    overlap = overlap_table(
        assignments, [mcndroid.kind_hashes(paths, kind) for kind in mcndroid.kinds()]
    )
    if overlap.height == 0:
        raise CtkError(FailureReason.NO_ELIGIBLE_TARGETS, ErrorMessage.OVERLAP_EMPTY)
    order = overlap[Column.SHA256]
    identities = restrict_identities(
        pl.read_parquet(paths.stage_file(Stage.IDENTITY, Artifact.COMPONENTS)), overlap
    )
    cache.write_table(overlap, paths.representation_file(Artifact.OVERLAP))
    cache.write_table(identities, paths.representation_file(Artifact.COMPONENTS))
    lamda = cache.load_features(paths.cache_file(Artifact.FEATURES))
    cache.save_features(
        paths.representation_file(Artifact.LAMDA_R0_FEATURES),
        np.ascontiguousarray(lamda[overlap[Column.SOURCE_ROW].to_numpy()]),
    )
    static = mcndroid.load_wanted(paths, Representation.MCNDROID_STATIC, order)
    cache.save_features(
        paths.representation_file(Artifact.MCNDROID_R1_FEATURES),
        binary_rows(
            static.matrix,
            mcndroid.alignment(static, order, Representation.MCNDROID_STATIC),
        ),
    )
    graph = mcndroid.load_wanted(paths, Representation.CALL_GRAPH, order)
    graph_rows = graph.matrix[mcndroid.alignment(graph, order, Representation.CALL_GRAPH)]
    save_csr(csr_files(paths, Representation.CALL_GRAPH), graph_rows, half=False)
    report = mcndroid.load_wanted(paths, Representation.REPORT_JSON, order)
    report_rows = signed_log(
        report.matrix[mcndroid.alignment(report, order, Representation.REPORT_JSON)]
    )
    save_csr(csr_files(paths, Representation.REPORT_JSON), report_rows, half=True)
    manifest = OverlapManifest(
        lamda_rows=assignments.height,
        rows=overlap.height,
        malware_rows=overlap.filter(pl.col(Column.LABEL) == 1).height,
        benign_rows=overlap.filter(pl.col(Column.LABEL) == 0).height,
        lamda_features=lamda.shape[1],
        static_features=static.matrix.shape[1],
        graph_features=graph.matrix.shape[1],
        json_columns_total=report.matrix.shape[1],
    )
    cache.write_record(paths.representation_file(Artifact.OVERLAP_MANIFEST), manifest)
    logs.info(
        LogEvent.REPRESENTATION_BUILT,
        {
            LogField.ROWS: manifest.rows,
            LogField.FEATURES: manifest.json_columns_total,
            LogField.SECONDS: watch.seconds(),
        },
    )
    return manifest


def build_seed_partition(
    paths: Paths,
    config: Config,
    key: PartitionKey,
    universe: tuple[FamilyName, ...],
) -> PartitionResult:
    overlap = pl.read_parquet(paths.representation_file(Artifact.OVERLAP))
    identities = pl.read_parquet(paths.representation_file(Artifact.COMPONENTS))
    return partitions.build_partition(
        families.classify_labels(overlap, config.data),
        identities,
        identity.grouping_ids(identities, key.grouping),
        universe,
        key,
        config.data,
    )


def write_seed_partition(paths: Paths, key: PartitionKey, result: PartitionResult) -> None:
    def target(artifact: Artifact) -> File:
        return paths.representation_partition_file(key, artifact)

    rows = pl.read_parquet(paths.representation_file(Artifact.COMPONENTS))[Column.ROW]
    cache.write_table(
        pl.DataFrame({Column.ROW: rows, Column.ROLE: result.roles}),
        target(Artifact.ASSIGNMENTS),
    )
    cache.write_table(result.controlled, target(Artifact.CONTROLLED_PAIRS))
    cache.write_table(result.natural, target(Artifact.NATURAL_PAIRS))


# R2 and R3 are returned raw (sparse, R3 signed-log); every scaler and column selection is fitted
# per trained model from its own training rows (`experiment.models.fit_transform`).
def load_features(paths: Paths, representation: Representation) -> FeatureMatrix:
    if representation is Representation.LAMDA_STATIC:
        return cache.load_features(paths.representation_file(Artifact.LAMDA_R0_FEATURES))
    if representation is Representation.MCNDROID_STATIC:
        return cache.load_features(paths.representation_file(Artifact.MCNDROID_R1_FEATURES))
    manifest = cache.read_record(
        paths.representation_file(Artifact.OVERLAP_MANIFEST), OverlapManifest
    )
    width = (
        manifest.graph_features
        if representation is Representation.CALL_GRAPH
        else manifest.json_columns_total
    )
    return load_csr(csr_files(paths, representation), width)


def transform_rule(representation: Representation | None, config: Config) -> TransformRule | None:
    if representation is Representation.CALL_GRAPH:
        return TransformRule(min_prevalence=None)
    if representation is Representation.REPORT_JSON:
        return TransformRule(min_prevalence=config.experiments.representation_min_prevalence)
    return None


def load_study(paths: Paths, config: Config, spec: ExperimentSpec, key: PartitionKey) -> StudyData:
    offset = config.experiments.permutation_seed_offset
    if spec.representation is None:
        return partitions.load_study(paths, key, config.data, spec.family_labels, offset)
    if not paths.representation_file(Artifact.OVERLAP).is_file():
        raise CtkError(
            FailureReason.SCHEMA_MISMATCH,
            ErrorMessage.REPRESENTATION_MISSING.format(path=paths.representation_dir),
        )
    table = partitions.study_table(
        pl.read_parquet(paths.representation_file(Artifact.OVERLAP)),
        pl.read_parquet(paths.representation_file(Artifact.COMPONENTS)),
        pl.read_parquet(paths.representation_partition_file(key, Artifact.ASSIGNMENTS)),
        key,
        config.data,
        spec.family_labels,
        offset,
    )
    return StudyData(table=table, features=load_features(paths, spec.representation))


def namespace_validations(paths: Paths, manifest: OverlapManifest) -> list[ValidationRecord]:
    counts = [
        cache.load_features(paths.representation_file(Artifact.LAMDA_R0_FEATURES)).shape[0],
        cache.load_features(paths.representation_file(Artifact.MCNDROID_R1_FEATURES)).shape[0],
        *(
            np.load(csr_files(paths, kind).indptr).size - 1
            for kind in (Representation.CALL_GRAPH, Representation.REPORT_JSON)
        ),
    ]
    overlap = pl.read_parquet(paths.representation_file(Artifact.OVERLAP))
    identities = pl.read_parquet(paths.representation_file(Artifact.COMPONENTS))
    unique = overlap[Column.SHA256].n_unique()
    aligned = (
        all(count == manifest.rows for count in counts)
        and unique == manifest.rows
        and identities[Column.SHA256].equals(overlap[Column.SHA256])
    )
    return [
        ValidationRecord(
            check=ValidationCheck.REPRESENTATION_ROWS_ALIGNED,
            passed=aligned,
            detail=DetailMessage.REPRESENTATION_ALIGNED.format(
                representations=len(counts), rows=manifest.rows, unique=unique
            ),
        )
    ]
