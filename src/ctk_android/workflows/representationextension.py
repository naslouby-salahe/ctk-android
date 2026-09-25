import polars as pl

from ctk_android import logs
from ctk_android.analysis.representation_extension import (
    eligibility_table,
    representation_experiments,
    representation_tables,
    representation_verdicts,
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
    FamilySetName,
    LogEvent,
    LogField,
    ResultsFile,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.promotion import promote_extension_design
from ctk_android.reporting.records import collect_evidence
from ctk_android.types import (
    CtkError,
    DesignPromotion,
    PlannedTargetsBySeed,
    Promote,
    PromotionDecision,
    RunKey,
)
from ctk_android.workflows.plan import planned_targets
from ctk_android.workflows.preprocess import read_family_set


def run_representation_extension(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    experiments = representation_experiments(config, mode)
    evidence = collect_evidence(paths, config, mode, fairness=False, only=experiments)
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    reference = experiments[0]
    planned: PlannedTargetsBySeed = {
        seed: planned_targets(
            paths, RunKey(mode=mode, experiment=reference, seed=seed, salt=0)
        ).targets
        for seed in config.seeds_for(reference, mode)
    }
    tables = representation_tables(evidence.families, config, experiments)
    outputs = (
        (Artifact.REPRESENTATION_RUN_INDEX, evidence.index),
        (Artifact.REPRESENTATION_SEED_EFFECTS, tables.seeds),
        (Artifact.REPRESENTATION_EFFECTS, records_to_frame(list(tables.effects))),
        (Artifact.REPRESENTATION_LEVELS, records_to_frame(list(tables.levels))),
        (Artifact.REPRESENTATION_VERDICTS, representation_verdicts(tables.effects, config)),
        (
            Artifact.REPRESENTATION_ELIGIBILITY,
            eligibility_table(planned, read_family_set(paths, FamilySetName.PRIMARY)),
        ),
    )
    for artifact, table in outputs:
        write_table(table if table.height else pl.DataFrame(), paths.analysis_file(mode, artifact))
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.REPRESENTATION_EXTENSION, LogField.SECONDS: watch.seconds()},
    )
    if not promote_evidence:
        return None
    return promote_extension_design(
        paths,
        config,
        mode,
        DesignPromotion(
            study=ExtensionStudy.REPRESENTATION,
            experiments=experiments,
            index_artifact=Artifact.REPRESENTATION_RUN_INDEX,
            artifacts=tuple(artifact for artifact, _ in outputs[1:]),
            code_file=ResultsFile.REPRESENTATION_CODE,
        ),
    )
