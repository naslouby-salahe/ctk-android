import polars as pl

from ctk_android import logs
from ctk_android.analysis.large_family import (
    eligibility_stability_summary,
    eligibility_stability_table,
    large_family_summary,
    large_family_table,
    large_seed_effects,
    stability_seed_table,
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
    Stage,
)
from ctk_android.logs import Stopwatch
from ctk_android.paths import Paths
from ctk_android.reporting.promotion import promote_large_family
from ctk_android.reporting.records import collect_evidence
from ctk_android.types import (
    CtkError,
    PartitionKey,
    Promote,
    PromotionDecision,
    RunKey,
    SeedPairsTables,
    SupportCount,
)
from ctk_android.workflows.plan import planned_targets


def _planned_families(paths: Paths, config: Config, mode: ExecutionMode) -> SupportCount:
    return len(
        {
            pair.family
            for experiment in config.experiments.extension_b_experiments
            for seed in config.seeds_for(experiment, mode)
            for pair in planned_targets(
                paths, RunKey(mode=mode, experiment=experiment, seed=seed, salt=0)
            ).targets
        }
    )


def _fresh_seed_pairs(paths: Paths, config: Config, mode: ExecutionMode) -> SeedPairsTables:
    # Controlled pairs per fresh seed, as built by the partition stage for the frozen universe.
    pairs: SeedPairsTables = {}
    for experiment in config.experiments.extension_b_experiments:
        spec = config.experiments.experiments[experiment]
        for seed in config.seeds_for(experiment, mode):
            key = PartitionKey(seed=seed, salt=0, grouping=spec.grouping, profile=spec.eligibility)
            pairs[seed] = pl.read_parquet(
                paths.partition_file(key, Artifact.LARGE_CONTROLLED_PAIRS)
            )
    return pairs


def run_large_family(
    paths: Paths, config: Config, mode: ExecutionMode, promote_evidence: Promote
) -> PromotionDecision | None:
    evidence = collect_evidence(
        paths, config, mode, fairness=False, only=config.experiments.extension_b_experiments
    )
    if evidence.summary.height == 0:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, ErrorMessage.NO_EVIDENCE.format(mode=mode))
    watch = Stopwatch()
    seed_effects = large_seed_effects(evidence.families, config)
    table = large_family_table(seed_effects, evidence.novelty, config)
    write_table(evidence.index, paths.analysis_file(mode, Artifact.RUN_INDEX))
    write_table(seed_effects, paths.analysis_file(mode, Artifact.LARGE_FAMILY_SEED_CTK))
    write_table(table, paths.analysis_file(mode, Artifact.LARGE_FAMILY_CTK))
    write_table(
        large_family_summary(table, _planned_families(paths, config, mode), config, seed_effects),
        paths.analysis_file(mode, Artifact.LARGE_FAMILY_SUMMARY),
    )
    selection = pl.read_parquet(paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION))
    per_seed = stability_seed_table(_fresh_seed_pairs(paths, config, mode), selection)
    stability = eligibility_stability_table(per_seed, selection, seed_effects)
    write_table(per_seed, paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY_SEEDS))
    write_table(stability, paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY))
    write_table(
        eligibility_stability_summary(stability, table, config),
        paths.analysis_file(mode, Artifact.LARGE_FAMILY_STABILITY_SUMMARY),
    )
    logs.info(
        LogEvent.ANALYSIS_STAGE_FINISHED,
        {LogField.STAGE: AnalysisStage.LARGE_FAMILY, LogField.SECONDS: watch.seconds()},
    )
    return promote_large_family(paths, config, mode) if promote_evidence else None
