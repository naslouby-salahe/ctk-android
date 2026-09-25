import polars as pl

from ctk_android import logs
from ctk_android.analysis.dose_extension import (
    dose_consistency,
    dose_effects,
    dose_experiments,
    dose_family_curves,
    dose_verdicts,
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
from ctk_android.reporting.records import collect_evidence
from ctk_android.types import CtkError, DesignPromotion, Promote, PromotionDecision


def run_dose_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = dose_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    effects = dose_effects(evidence.families, config, experiments)
    outputs = (
        (Artifact.DOSE_RUN_INDEX, evidence.index),
        (Artifact.DOSE_SEED_EFFECTS, effects.seeds),
        (Artifact.DOSE_EFFECTS, records_to_frame(list(effects.rows))),
        (Artifact.DOSE_FAMILY_CURVES, dose_family_curves(evidence.families, experiments)),
        (
            Artifact.DOSE_CONSISTENCY,
            dose_consistency(evidence.exposure, evidence.families, experiments),
        ),
        (Artifact.DOSE_VERDICTS, dose_verdicts(effects.rows, config)),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.DOSE_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.DOSE,
            experiments=experiments,
            index_artifact=Artifact.DOSE_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.DOSE_CODE,
        ),
    )
