import shutil
from datetime import UTC, datetime

import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import (
    fingerprint_file,
    is_reusable,
    read_record,
    run_provenance,
    write_record,
)
from ctk_android.enums import (
    Artifact,
    ClaimName,
    Column,
    DatasetName,
    ExecutionMode,
    FileSuffix,
    PromotionBlock,
    PromotionState,
    ReportFigure,
    ReportTable,
    ResultsDirectory,
    ResultsFile,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CodeProvenance,
    File,
    ManifestEntry,
    Moment,
    PromotionDecision,
    ProtocolProvenance,
    ResultsManifest,
    RunIndexTable,
    RunKey,
    RunManifest,
    SourceFingerprint,
    SourceProvenance,
    Stale,
    Table,
)
from ctk_android.workflows.doctor import git_revision, revision_at_or_before, sources_are_clean
from ctk_android.workflows.plan import experiments_for, planned_targets


def row_level_columns() -> list[Column]:
    return [Column.SHA256, Column.ROW]


def evidence_files() -> list[Artifact]:
    return [
        Artifact.RUN_INDEX,
        Artifact.ARM_METRICS,
        Artifact.COLLABORATION_DECOMPOSITION,
        Artifact.FAMILY_RESCUE,
        Artifact.PEER_DOSE_RESPONSE,
        Artifact.FEATURE_NOVELTY,
        Artifact.ROBUSTNESS,
        Artifact.CLIENT_CTK,
        Artifact.FAMILY_CLIENT_CTK,
        Artifact.CTK_VARIANCE,
        Artifact.FAMILY_ASSOCIATIONS,
        Artifact.ANCHORED_WORST_CLIENT,
        Artifact.ANCHORED_CLIENT_SELECTION,
        Artifact.ARM_TRADEOFF,
        Artifact.ROBUSTNESS_SYNTHESIS,
        Artifact.FAMILY_PATTERNS,
        Artifact.NATURAL_COMPARISON,
        Artifact.PERMUTATION_AUDIT,
        Artifact.MECHANISM_HEADROOM,
        Artifact.OPERATING_FIDELITY,
    ]


def statistics_files() -> list[Artifact]:
    return [Artifact.PAIRED_EFFECTS, Artifact.CLUSTER_BOOTSTRAP]


def _stale_runs(paths: Paths, config: Config, mode: ExecutionMode) -> Stale:
    for experiment in experiments_for(config, mode):
        for seed in config.project.seeds.for_mode(mode):
            for salt in config.experiments.experiments[experiment].salts:
                key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
                current = run_provenance(paths, config, key, planned_targets(paths, key).targets)
                if not is_reusable(paths.provenance_file(paths.run_dir(key)), current):
                    return True
    return False


def promotion_blocks(
    paths: Paths, config: Config, mode: ExecutionMode
) -> tuple[PromotionBlock, ...]:
    if mode is not ExecutionMode.CONFIRMATORY:
        return (PromotionBlock.NOT_CONFIRMATORY,)
    blocks: list[PromotionBlock] = []
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    if index.filter(pl.col(Column.STATUS) == RunStatus.FAILED_VALIDATION).height:
        blocks.append(PromotionBlock.VALIDATION_FAILED)
    if index.filter(pl.col(Column.STATUS) != RunStatus.COMPLETED).height:
        blocks.append(PromotionBlock.RUNS_INCOMPLETE)
    claims = pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))
    if set(claims[Column.CLAIM].to_list()) != set(ClaimName):
        blocks.append(PromotionBlock.CLAIMS_INCOMPLETE)
    if _stale_runs(paths, config, mode):
        blocks.append(PromotionBlock.PROVENANCE_STALE)
    for artifact in evidence_files() + statistics_files():
        source = paths.analysis_file(mode, artifact)
        if not source.is_file():
            source = paths.statistics_file(mode, artifact)
        if set(row_level_columns()) & set(pl.read_parquet(source).columns):
            blocks.append(PromotionBlock.ROW_LEVEL_DATA)
            break
    return tuple(blocks)


def _copy(source: File, target: File) -> ManifestEntry:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return ManifestEntry(
        name=f"{target.relative_to(target.parents[1])}", digest=fingerprint_file(target)
    )


def _write_csv(frame: Table, target: File) -> ManifestEntry:
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_csv(target)
    return ManifestEntry(
        name=f"{target.relative_to(target.parents[1])}", digest=fingerprint_file(target)
    )


def _first_run_written(paths: Paths, index: RunIndexTable, mode: ExecutionMode) -> Moment:
    written = [
        paths.run_file(
            RunKey(
                mode=mode,
                experiment=row[Column.EXPERIMENT],
                seed=row[Column.SEED],
                salt=row[Column.SALT],
            ),
            Artifact.STATUS,
        )
        .stat()
        .st_mtime
        for row in index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED).iter_rows(named=True)
    ]
    return datetime.fromtimestamp(min(written), tz=UTC)


def _extension_blocks(
    paths: Paths, config: Config, mode: ExecutionMode
) -> tuple[PromotionBlock, ...]:
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    blocks: list[PromotionBlock] = []
    if index.filter(pl.col(Column.STATUS) == RunStatus.FAILED_VALIDATION).height:
        blocks.append(PromotionBlock.VALIDATION_FAILED)
    if index.filter(pl.col(Column.STATUS) != RunStatus.COMPLETED).height:
        blocks.append(PromotionBlock.RUNS_INCOMPLETE)
    if _stale_runs(paths, config, mode):
        blocks.append(PromotionBlock.PROVENANCE_STALE)
    return tuple(blocks)


def _promote_extension(paths: Paths, config: Config, mode: ExecutionMode) -> PromotionDecision:
    blocks = _extension_blocks(paths, config, mode)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    for artifact, source in (
        (Artifact.RUN_INDEX, paths.analysis_file(mode, Artifact.RUN_INDEX)),
        (Artifact.PERMUTATION_AUDIT, paths.analysis_file(mode, Artifact.PERMUTATION_AUDIT)),
        (Artifact.PAIRED_EFFECTS, paths.statistics_file(mode, Artifact.PAIRED_EFFECTS)),
    ):
        _copy(source, paths.results_file(ResultsDirectory.EXTENSION, artifact))
    audit = pl.read_parquet(paths.analysis_file(mode, Artifact.PERMUTATION_AUDIT))
    _write_csv(audit, paths.results_file(ResultsDirectory.EXTENSION, ResultsFile.EXTENSION_AUDIT))
    write_record(
        paths.results_file(ResultsDirectory.EXTENSION, ResultsFile.CODE),
        CodeProvenance(
            execution_revision=revision_at_or_before(paths, _first_run_written(paths, index, mode)),
            analysis_revision=git_revision(paths).detail,
            analysis_sources_clean=sources_are_clean(paths),
        ),
    )
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())


def promote(paths: Paths, config: Config, mode: ExecutionMode) -> PromotionDecision:
    if mode is ExecutionMode.EXTENSION:
        return _promote_extension(paths, config, mode)
    blocks = promotion_blocks(paths, config, mode)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    entries: list[ManifestEntry] = []
    for artifact in evidence_files():
        entries.append(
            _copy(
                paths.analysis_file(mode, artifact),
                paths.results_file(ResultsDirectory.EVIDENCE, artifact),
            )
        )
    for artifact in statistics_files():
        entries.append(
            _copy(
                paths.statistics_file(mode, artifact),
                paths.results_file(ResultsDirectory.STATISTICS, artifact),
            )
        )
    claims = pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    entries.append(
        _write_csv(claims, paths.results_file(ResultsDirectory.GATES, ResultsFile.CLAIMS))
    )
    entries.append(
        _write_csv(index, paths.results_file(ResultsDirectory.GATES, ResultsFile.SEED_STATUS))
    )
    for table in ReportTable:
        entries.append(
            _copy(
                paths.report_table_file(mode, table),
                paths.results_file(
                    ResultsDirectory.TABLES, paths.report_table_file(mode, table).name
                ),
            )
        )
    for figure in ReportFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            source = paths.report_figure_file(mode, figure, suffix)
            entries.append(_copy(source, paths.results_file(ResultsDirectory.FIGURES, source.name)))
    write_record(
        paths.results_file(ResultsDirectory.PROVENANCE, ResultsFile.SOURCE_DATA),
        SourceProvenance(
            lamda=read_record(
                paths.source_file(DatasetName.LAMDA, Artifact.FINGERPRINT), SourceFingerprint
            ).fingerprint,
            androzoo=read_record(
                paths.source_file(DatasetName.ANDROZOO, Artifact.FINGERPRINT), SourceFingerprint
            ).fingerprint,
        ),
    )
    write_record(
        paths.results_file(ResultsDirectory.PROVENANCE, ResultsFile.CODE),
        CodeProvenance(
            execution_revision=revision_at_or_before(paths, _first_run_written(paths, index, mode)),
            analysis_revision=git_revision(paths).detail,
            analysis_sources_clean=sources_are_clean(paths),
        ),
    )
    write_record(
        paths.results_file(ResultsDirectory.PROVENANCE, ResultsFile.PROTOCOL),
        ProtocolProvenance(
            config=config.fingerprint(), roadmap=fingerprint_file(paths.roadmap_file)
        ),
    )
    first = index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED).row(0, named=True)
    manifest = read_record(
        paths.run_file(
            RunKey(
                mode=mode,
                experiment=first[Column.EXPERIMENT],
                seed=first[Column.SEED],
                salt=first[Column.SALT],
            ),
            Artifact.MANIFEST,
        ),
        RunManifest,
    )
    write_record(
        paths.results_file(ResultsDirectory.PROVENANCE, ResultsFile.ENVIRONMENT),
        manifest.environment,
    )
    write_record(
        paths.results_root_file(ResultsFile.MANIFEST),
        ResultsManifest(mode=mode, files=tuple(entries)),
    )
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())
