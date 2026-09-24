import shutil

import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import (
    fingerprint_file,
    fingerprint_source_tree,
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
    PromotionDecision,
    ProtocolProvenance,
    ResultsManifest,
    RunKey,
    RunManifest,
    SourceFingerprint,
    SourceProvenance,
)
from ctk_android.workflows.doctor import git_revision
from ctk_android.workflows.plan import experiments_for, planned_targets


def row_level_columns() -> tuple[Column, Column]:
    return (Column.SHA256, Column.ROW)


def evidence_files() -> list[Artifact]:
    return [
        Artifact.RUN_INDEX,
        Artifact.ARM_METRICS,
        Artifact.COLLABORATION_DECOMPOSITION,
        Artifact.FAMILY_RESCUE,
        Artifact.PEER_DOSE_RESPONSE,
        Artifact.FEATURE_NOVELTY,
        Artifact.ROBUSTNESS,
    ]


def statistics_files() -> list[Artifact]:
    return [Artifact.PAIRED_EFFECTS, Artifact.CLUSTER_BOOTSTRAP]


def _stale_runs(paths: Paths, config: Config, mode: ExecutionMode) -> bool:
    for experiment in experiments_for(config, mode):
        for seed in config.project.seeds.for_mode(mode):
            for salt in config.experiments.experiments[experiment].salts:
                key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
                _, targets = planned_targets(paths, key)
                current = run_provenance(paths, config, key, targets)
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


def _write_csv(frame: pl.DataFrame, target: File) -> ManifestEntry:
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_csv(target)
    return ManifestEntry(
        name=f"{target.relative_to(target.parents[1])}", digest=fingerprint_file(target)
    )


def promote(paths: Paths, config: Config, mode: ExecutionMode) -> PromotionDecision:
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
                paths.report_table_file(table),
                paths.results_file(ResultsDirectory.TABLES, paths.report_table_file(table).name),
            )
        )
    for figure in ReportFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            source = paths.report_figure_file(figure, suffix)
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
            revision=git_revision(paths).detail,
            fingerprint=fingerprint_source_tree(paths.source_root),
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
