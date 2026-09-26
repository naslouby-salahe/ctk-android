import numpy as np
import polars as pl
import scipy.sparse as sp

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data import cache, partitions, preparation, sources
from ctk_android.enums import (
    Artifact,
    Column,
    DatasetName,
    DetailMessage,
    ErrorMessage,
    FailureReason,
    LibraryOption,
    LogEvent,
    LogField,
    McNdroidDirectory,
    McNdroidFile,
    McNdroidKey,
    McNdroidSplit,
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
    Directory,
    ExperimentSpec,
    FamilyName,
    FeatureCount,
    FeatureMatrix,
    File,
    HalfPrecision,
    IdentitiesTable,
    McNdroidShard,
    OverlapManifest,
    PartitionKey,
    PartitionResult,
    PositionArray,
    ShaBlock,
    ShaSeries,
    SourceInventory,
    SourceScan,
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
    overlap = overlap_table(assignments, [kind_hashes(paths, kind) for kind in kinds()])
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
    static = load_wanted(paths, Representation.MCNDROID_STATIC, order)
    cache.save_features(
        paths.representation_file(Artifact.MCNDROID_R1_FEATURES),
        binary_rows(
            static.matrix,
            alignment(static, order, Representation.MCNDROID_STATIC),
        ),
    )
    graph = load_wanted(paths, Representation.CALL_GRAPH, order)
    graph_rows = graph.matrix[alignment(graph, order, Representation.CALL_GRAPH)]
    save_csr(csr_files(paths, Representation.CALL_GRAPH), graph_rows, half=False)
    report = load_wanted(paths, Representation.REPORT_JSON, order)
    report_rows = signed_log(report.matrix[alignment(report, order, Representation.REPORT_JSON)])
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
        preparation.classify_labels(overlap, config.data),
        identities,
        preparation.grouping_ids(identities, key.grouping),
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
