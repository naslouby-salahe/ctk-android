from ctk_android import logs
from ctk_android.analysis.hidden_family import (
    aggregate_metric_masking,
    ctk_heterogeneity_components,
    hidden_cells,
    negative_transfer_decomposition,
)
from ctk_android.config import Config
from ctk_android.data.cache import write_table
from ctk_android.enums import (
    AnalysisStage,
    Artifact,
    ErrorMessage,
    ExecutionMode,
    FailureReason,
    LogEvent,
    LogField,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.promotion import promote_hidden_family
from ctk_android.reporting.records import collect_evidence
from ctk_android.types import CtkError, Promote, PromotionDecision


def run_posthoc(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    evidence = collect_evidence(paths, config, mode, fairness=False)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    cells = hidden_cells(evidence.families, config.experiments.operating.primary_alpha)
    write_table(
        ctk_heterogeneity_components(cells, config),
        paths.analysis_file(mode, Artifact.HETEROGENEITY_COMPONENTS),
    )
    write_table(
        aggregate_metric_masking(evidence.summary, config),
        paths.analysis_file(mode, Artifact.AGGREGATE_MASKING),
    )
    write_table(
        negative_transfer_decomposition(cells, config),
        paths.analysis_file(mode, Artifact.NEGATIVE_TRANSFER),
    )
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.HIDDEN_FAMILY, LogField.SECONDS: watch.seconds()},
    )
    return promote_hidden_family(paths, mode, evidence.index) if promote_evidence else None
