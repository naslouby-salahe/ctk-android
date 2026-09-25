import polars as pl

from ctk_android import logs
from ctk_android.analysis.controls_extension import (
    controls_effects,
    controls_experiments,
    controls_verdicts,
    placebo_table,
)
from ctk_android.config import Config
from ctk_android.data.cache import records_to_frame, write_table
from ctk_android.enums import (
    AnalysisStage,
    Artifact,
    ErrorMessage,
    ExecutionMode,
    ExtensionStudy,
    FailureReason,
    LogEvent,
    LogField,
    ResultsFile,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.promotion import promote_extension_design
from ctk_android.reporting.records import collect_evidence, collect_placebo_pairs
from ctk_android.types import CtkError, DesignPromotion, Promote, PromotionDecision


def run_controls_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = controls_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    effects = controls_effects(evidence.families, config, experiments)
    outputs = (
        (Artifact.CONTROLS_RUN_INDEX, evidence.index),
        (Artifact.CONTROLS_SEED_EFFECTS, effects.seeds),
        (Artifact.CONTROLS_EFFECTS, records_to_frame(list(effects.rows))),
        (
            Artifact.CONTROLS_PLACEBO_PAIRS,
            placebo_table(collect_placebo_pairs(paths, evidence.index, mode)),
        ),
        (Artifact.CONTROLS_VERDICTS, controls_verdicts(effects.rows, config)),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.CONTROLS_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.CONTROLS,
            experiments=experiments,
            index_artifact=Artifact.CONTROLS_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.CONTROLS_CODE,
        ),
    )
