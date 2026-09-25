import shutil
from datetime import UTC, datetime
from pathlib import Path

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
    EvidenceClass,
    ExecutionMode,
    ExtensionStudy,
    FileSuffix,
    PromotionBlock,
    PromotionState,
    ProtocolDocument,
    ReportFigure,
    ReportTable,
    ResultsDirectory,
    ResultsFile,
    RunStatus,
    Stage,
    SupersededFile,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CodeProvenance,
    DataFingerprints,
    DesignPromotion,
    ExperimentScope,
    ExtensionProvenance,
    File,
    FileDigest,
    ManifestEntry,
    Moment,
    PromotedOutput,
    PromotionDecision,
    ProtocolProvenance,
    ResultsManifest,
    RunConfigFingerprint,
    RunIndexTable,
    RunKey,
    RunManifest,
    SourceFingerprint,
    SourceProvenance,
    Stale,
    StudyProvenance,
    StudyRequest,
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


def hidden_family_files() -> list[Artifact]:
    return [
        Artifact.HETEROGENEITY_COMPONENTS,
        Artifact.AGGREGATE_MASKING,
        Artifact.NEGATIVE_TRANSFER,
    ]


def statistics_files() -> list[Artifact]:
    return [Artifact.PAIRED_EFFECTS, Artifact.CLUSTER_BOOTSTRAP]


def _stale_runs(
    paths: Paths, config: Config, mode: ExecutionMode, only: ExperimentScope = None
) -> Stale:
    for experiment in experiments_for(config, mode):
        if only is not None and experiment not in only:
            continue
        for seed in config.seeds_for(experiment, mode):
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


def _entry(target: File, evidence: EvidenceClass) -> ManifestEntry:
    return ManifestEntry(
        name=f"{target.relative_to(target.parents[1])}",
        digest=fingerprint_file(target),
        evidence_class=evidence,
    )


def _copy(source: File, target: File, evidence: EvidenceClass) -> ManifestEntry:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return _entry(target, evidence)


def _write_csv(frame: Table, target: File, evidence: EvidenceClass) -> ManifestEntry:
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.write_csv(target)
    return _entry(target, evidence)


# Every promoted file is listed with its digest and evidence class in the manifest of the
# directory tree it belongs to; a later promotion replaces entries of the same name only.
def _merge_manifest(target: File, mode: ExecutionMode, added: list[ManifestEntry]) -> None:
    names = {entry.name for entry in added}
    kept = read_record(target, ResultsManifest).files if target.is_file() else ()
    write_record(
        target,
        ResultsManifest(
            mode=mode, files=(*(entry for entry in kept if entry.name not in names), *added)
        ),
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
    paths: Paths,
    config: Config,
    mode: ExecutionMode,
    only: ExperimentScope = None,
    index_artifact: Artifact = Artifact.RUN_INDEX,
) -> tuple[PromotionBlock, ...]:
    index = pl.read_parquet(paths.analysis_file(mode, index_artifact))
    blocks: list[PromotionBlock] = []
    if index.filter(pl.col(Column.STATUS) == RunStatus.FAILED_VALIDATION).height:
        blocks.append(PromotionBlock.VALIDATION_FAILED)
    if index.filter(pl.col(Column.STATUS) != RunStatus.COMPLETED).height:
        blocks.append(PromotionBlock.RUNS_INCOMPLETE)
    if _stale_runs(paths, config, mode, only):
        blocks.append(PromotionBlock.PROVENANCE_STALE)
    return tuple(blocks)


def _promote_extension(paths: Paths, config: Config, mode: ExecutionMode) -> PromotionDecision:
    blocks = _extension_blocks(paths, config, mode)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    added: list[ManifestEntry] = []
    for artifact, source in (
        (Artifact.RUN_INDEX, paths.analysis_file(mode, Artifact.RUN_INDEX)),
        (Artifact.PERMUTATION_AUDIT, paths.analysis_file(mode, Artifact.PERMUTATION_AUDIT)),
        (Artifact.PAIRED_EFFECTS, paths.statistics_file(mode, Artifact.PAIRED_EFFECTS)),
    ):
        added.append(
            _copy(
                source,
                paths.results_file(ResultsDirectory.EXTENSION, artifact),
                EvidenceClass.PROSPECTIVE_EXTENSION,
            )
        )
    audit = pl.read_parquet(paths.analysis_file(mode, Artifact.PERMUTATION_AUDIT))
    added.append(
        _write_csv(
            audit,
            paths.results_file(ResultsDirectory.EXTENSION, ResultsFile.EXTENSION_AUDIT),
            EvidenceClass.PROSPECTIVE_EXTENSION,
        )
    )
    _merge_manifest(
        paths.results_file(ResultsDirectory.EXTENSION, ResultsFile.MANIFEST), mode, added
    )
    code = _code(paths, index, mode)
    write_record(paths.results_file(ResultsDirectory.EXTENSION, ResultsFile.CODE), code)
    record_study(
        paths,
        config,
        StudyRequest(
            study=ExtensionStudy.EXT_1,
            mode=mode,
            experiments=config.experiments.extension_experiments,
            evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION,
            code=code,
            artifacts=tuple(added),
        ),
    )
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())


def promote_hidden_family(
    paths: Paths, mode: ExecutionMode, index: RunIndexTable
) -> PromotionDecision:
    manifest_file = paths.results_root_file(ResultsFile.MANIFEST)
    if mode is not ExecutionMode.CONFIRMATORY or not manifest_file.is_file():
        return PromotionDecision(
            state=PromotionState.BLOCKED, blocks=(PromotionBlock.NOT_CONFIRMATORY,)
        )
    if index.filter(pl.col(Column.STATUS) != RunStatus.COMPLETED).height:
        return PromotionDecision(
            state=PromotionState.BLOCKED, blocks=(PromotionBlock.RUNS_INCOMPLETE,)
        )
    added: list[ManifestEntry] = []
    for artifact in hidden_family_files():
        source = paths.analysis_file(mode, artifact)
        added.append(
            _copy(
                source,
                paths.results_file(ResultsDirectory.EVIDENCE, artifact),
                EvidenceClass.POST_CONFIRMATORY,
            )
        )
        added.append(
            _write_csv(
                pl.read_parquet(source),
                paths.results_file(
                    ResultsDirectory.TABLES, f"{Path(artifact).stem}{FileSuffix.CSV}"
                ),
                EvidenceClass.POST_CONFIRMATORY,
            )
        )
    _merge_manifest(manifest_file, mode, added)
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())


def promote_large_family(paths: Paths, config: Config, mode: ExecutionMode) -> PromotionDecision:
    if mode is not ExecutionMode.EXTENSION_B:
        return PromotionDecision(
            state=PromotionState.BLOCKED, blocks=(PromotionBlock.NOT_EXTENSION_B,)
        )
    blocks = _extension_blocks(paths, config, mode, config.experiments.extension_b_experiments)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    added: list[ManifestEntry] = []
    for artifact, source in (
        (Artifact.RUN_INDEX, paths.analysis_file(mode, Artifact.RUN_INDEX)),
        (Artifact.LARGE_FAMILY_CTK, paths.analysis_file(mode, Artifact.LARGE_FAMILY_CTK)),
        (Artifact.LARGE_FAMILY_SEED_CTK, paths.analysis_file(mode, Artifact.LARGE_FAMILY_SEED_CTK)),
        (Artifact.LARGE_FAMILY_SUMMARY, paths.analysis_file(mode, Artifact.LARGE_FAMILY_SUMMARY)),
        (Artifact.LARGE_SELECTION, paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION)),
        *(
            (artifact, paths.analysis_file(mode, artifact))
            for artifact in (
                Artifact.LARGE_FAMILY_STABILITY,
                Artifact.LARGE_FAMILY_STABILITY_SEEDS,
                Artifact.LARGE_FAMILY_STABILITY_SUMMARY,
            )
        ),
    ):
        added.append(
            _copy(
                source,
                paths.results_file(ResultsDirectory.EXTENSION_B, artifact),
                EvidenceClass.PROSPECTIVE_EXTENSION,
            )
        )
        added.append(
            _write_csv(
                pl.read_parquet(source),
                paths.results_file(
                    ResultsDirectory.EXTENSION_B, f"{Path(artifact).stem}{FileSuffix.CSV}"
                ),
                EvidenceClass.PROSPECTIVE_EXTENSION,
            )
        )
    _merge_manifest(
        paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.MANIFEST), mode, added
    )
    code = _code(paths, index, mode)
    write_record(paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.CODE), code)
    record_study(
        paths,
        config,
        StudyRequest(
            study=ExtensionStudy.LARGE_FAMILY,
            mode=mode,
            experiments=config.experiments.extension_b_experiments,
            evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION,
            code=code,
            artifacts=tuple(added),
        ),
    )
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())


def _promote_pair(paths: Paths, mode: ExecutionMode, output: PromotedOutput) -> list[ManifestEntry]:
    source = paths.analysis_file(mode, output.artifact)
    return [
        _copy(
            source,
            paths.results_file(ResultsDirectory.EXTENSION_B, output.artifact),
            output.evidence_class,
        ),
        _write_csv(
            pl.read_parquet(source),
            paths.results_file(
                ResultsDirectory.EXTENSION_B, f"{Path(output.artifact).stem}{FileSuffix.CSV}"
            ),
            output.evidence_class,
        ),
    ]


def promote_extension_design(
    paths: Paths, config: Config, mode: ExecutionMode, request: DesignPromotion
) -> PromotionDecision:
    if mode is not ExecutionMode.EXTENSION_B:
        return PromotionDecision(
            state=PromotionState.BLOCKED, blocks=(PromotionBlock.NOT_EXTENSION_B,)
        )
    blocks = _extension_blocks(paths, config, mode, request.experiments, request.index_artifact)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    index = pl.read_parquet(paths.analysis_file(mode, request.index_artifact))
    added: list[ManifestEntry] = []
    for artifact in (request.index_artifact, *request.artifacts):
        added += _promote_pair(
            paths,
            mode,
            PromotedOutput(artifact=artifact, evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION),
        )
    _merge_manifest(
        paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.MANIFEST), mode, added
    )
    code = _code(paths, index, mode)
    write_record(paths.results_file(ResultsDirectory.EXTENSION_B, request.code_file), code)
    record_study(
        paths,
        config,
        StudyRequest(
            study=request.study,
            mode=mode,
            experiments=request.experiments,
            evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION,
            code=code,
            artifacts=tuple(added),
        ),
    )
    return PromotionDecision(state=PromotionState.PROMOTED, blocks=())


def _protocol(paths: Paths, study: ExtensionStudy) -> FileDigest | None:
    documents = {
        ExtensionStudy.EXT_1: ProtocolDocument.EXT_1,
        ExtensionStudy.LARGE_FAMILY: ProtocolDocument.LARGE_FAMILY,
        ExtensionStudy.DOSE: ProtocolDocument.DOSE,
        ExtensionStudy.CONTROLS: ProtocolDocument.CONTROLS,
        ExtensionStudy.REPRESENTATION: ProtocolDocument.REPRESENTATION,
    }
    document = documents.get(study)
    if document is None:
        return None
    return FileDigest(name=document, sha256=fingerprint_file(paths.protocol_file(document)))


def _data_fingerprints(paths: Paths, study: ExtensionStudy) -> DataFingerprints:
    reads_mcndroid = study in (ExtensionStudy.REPRESENTATION, ExtensionStudy.DIAGNOSTICS)
    return DataFingerprints(
        lamda=read_record(
            paths.source_file(DatasetName.LAMDA, Artifact.FINGERPRINT), SourceFingerprint
        ).fingerprint,
        androzoo=read_record(
            paths.source_file(DatasetName.ANDROZOO, Artifact.FINGERPRINT), SourceFingerprint
        ).fingerprint,
        mcndroid_inventory=read_record(
            paths.representation_file(Artifact.FINGERPRINT), SourceFingerprint
        ).fingerprint
        if reads_mcndroid
        else None,
    )


def _superseded(paths: Paths, study: ExtensionStudy) -> tuple[FileDigest, ...]:
    if study is not ExtensionStudy.REPRESENTATION:
        return ()
    name = SupersededFile.EXT_REP_TRANSDUCTIVE
    return (
        FileDigest(
            name=name,
            sha256=fingerprint_file(paths.results_file(ResultsDirectory.EXTENSION_B, name)),
        ),
    )


# One entry per extension study in results/extension-provenance.json, replaced on each
# promotion of that study; the original confirmatory provenance records are never touched.
def record_study(paths: Paths, config: Config, request: StudyRequest) -> None:
    target = paths.results_root_file(ResultsFile.EXTENSION_PROVENANCE)
    kept = read_record(target, ExtensionProvenance).studies if target.is_file() else ()
    experiments = config.experiments.experiments
    entry = StudyProvenance(
        name=request.study,
        mode=request.mode,
        seeds=tuple(
            sorted(
                {
                    seed
                    for experiment in request.experiments
                    for seed in config.seeds_for(experiment, request.mode)
                }
            )
        ),
        evidence_class=request.evidence_class,
        protocol=_protocol(paths, request.study),
        config_fingerprint=config.fingerprint(),
        run_fingerprints=tuple(
            RunConfigFingerprint(
                experiment=experiment,
                fingerprint=config.run_fingerprint(experiments[experiment], request.mode),
            )
            for experiment in request.experiments
        ),
        data=_data_fingerprints(paths, request.study),
        code=request.code,
        artifacts=request.artifacts,
        superseded=_superseded(paths, request.study),
    )
    order = list(ExtensionStudy)
    studies = sorted(
        [*(study for study in kept if study.name is not request.study), entry],
        key=lambda study: order.index(study.name),
    )
    write_record(target, ExtensionProvenance(studies=tuple(studies)))


def _code(paths: Paths, index: RunIndexTable, mode: ExecutionMode) -> CodeProvenance:
    return CodeProvenance(
        execution_revision=revision_at_or_before(paths, _first_run_written(paths, index, mode)),
        analysis_revision=git_revision(paths).detail,
        analysis_sources_clean=sources_are_clean(paths),
    )


def promote_diagnostics(
    paths: Paths, config: Config, mode: ExecutionMode, request: DesignPromotion
) -> PromotionDecision:
    # Post-hoc diagnostics: each table keeps its own evidence class (C for analyses of the
    # confirmatory runs, D-post-hoc-diagnostic for anything reading extension runs).
    if mode is not ExecutionMode.EXTENSION_B:
        return PromotionDecision(
            state=PromotionState.BLOCKED, blocks=(PromotionBlock.NOT_EXTENSION_B,)
        )
    blocks = _extension_blocks(paths, config, mode, request.experiments, request.index_artifact)
    if blocks:
        return PromotionDecision(state=PromotionState.BLOCKED, blocks=blocks)
    index = pl.read_parquet(paths.analysis_file(mode, request.index_artifact))
    added: list[ManifestEntry] = []
    for output in request.outputs:
        added += _promote_pair(paths, mode, output)
    _merge_manifest(
        paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.MANIFEST), mode, added
    )
    code = _code(paths, index, mode)
    write_record(paths.results_file(ResultsDirectory.EXTENSION_B, request.code_file), code)
    record_study(
        paths,
        config,
        StudyRequest(
            study=request.study,
            mode=mode,
            experiments=request.experiments,
            evidence_class=EvidenceClass.POST_HOC_DIAGNOSTIC,
            code=code,
            artifacts=tuple(added),
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
                EvidenceClass.CONFIRMATORY_SEEDS,
            )
        )
    for artifact in statistics_files():
        entries.append(
            _copy(
                paths.statistics_file(mode, artifact),
                paths.results_file(ResultsDirectory.STATISTICS, artifact),
                EvidenceClass.CONFIRMATORY_SEEDS,
            )
        )
    claims = pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))
    index = pl.read_parquet(paths.analysis_file(mode, Artifact.RUN_INDEX))
    entries.append(
        _write_csv(
            claims,
            paths.results_file(ResultsDirectory.GATES, ResultsFile.CLAIMS),
            EvidenceClass.CONFIRMATORY_SEEDS,
        )
    )
    entries.append(
        _write_csv(
            index,
            paths.results_file(ResultsDirectory.GATES, ResultsFile.SEED_STATUS),
            EvidenceClass.CONFIRMATORY_SEEDS,
        )
    )
    for table in ReportTable:
        entries.append(
            _copy(
                paths.report_table_file(mode, table),
                paths.results_file(
                    ResultsDirectory.TABLES, paths.report_table_file(mode, table).name
                ),
                EvidenceClass.CONFIRMATORY_SEEDS,
            )
        )
    for figure in ReportFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            source = paths.report_figure_file(mode, figure, suffix)
            entries.append(
                _copy(
                    source,
                    paths.results_file(ResultsDirectory.FIGURES, source.name),
                    EvidenceClass.CONFIRMATORY_SEEDS,
                )
            )
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
