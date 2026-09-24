import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import is_one_of
from ctk_android.enums import (
    Artifact,
    ClaimName,
    Column,
    Estimand,
    ExecutionMode,
    ExperimentName,
    FamilyOutcome,
    LibraryOption,
    Metric,
    ReportTable,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    ArmComparisonTable,
    ClaimsTable,
    ClientAuditTable,
    DecompositionReportTable,
    DoseReportTable,
    FamilyLevelTable,
    ReportTables,
    RobustnessTable,
)


def _primary_metrics() -> list[Metric]:
    return [
        Metric.OWN_DOMAIN_UNSEEN_RECALL,
        Metric.FEDERATION_UNSEEN_RECALL,
        Metric.FAMILY_MACRO_UNSEEN_RECALL,
        Metric.WORST_CLIENT_UNSEEN_RECALL,
        Metric.KNOWN_FAMILY_RECALL,
        Metric.REALISED_FPR,
        Metric.WORST_CLIENT_FPR,
    ]


def dataset_client_audit(paths: Paths) -> ClientAuditTable:
    support = pl.read_parquet(paths.stage_file(Stage.CLIENTS, Artifact.SUPPORT))
    families = pl.read_parquet(paths.stage_file(Stage.FAMILIES, Artifact.SUPPORT))
    per_client = families.group_by(Column.CLIENT).agg(
        pl.col(Column.FAMILY).n_unique().alias(Column.FAMILY_SET)
    )
    return support.join(per_client, on=Column.CLIENT, how=LibraryOption.JOIN_LEFT).sort(
        Column.CLIENT
    )


def primary_arm_comparison(paths: Paths, config: Config, mode: ExecutionMode) -> ArmComparisonTable:
    summary = pl.read_parquet(paths.analysis_file(mode, Artifact.ARM_METRICS)).filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & pl.col(Column.DOSE).is_null()
        & is_one_of(Column.METRIC, _primary_metrics())
    )
    return (
        summary.group_by(Column.LEARNER, Column.CONDITION, Column.METRIC)
        .agg(pl.col(Column.VALUE).mean())
        .pivot(on=Column.METRIC, index=[Column.LEARNER, Column.CONDITION], values=Column.VALUE)
        .sort(Column.LEARNER, Column.CONDITION)
    )


def collaboration_decomposition(paths: Paths, mode: ExecutionMode) -> DecompositionReportTable:
    effects = pl.read_parquet(paths.statistics_file(mode, Artifact.PAIRED_EFFECTS))
    claims = pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))
    return (
        effects.filter(
            (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
            & is_one_of(
                Column.ESTIMAND,
                [Estimand.TOTAL_GAIN, Estimand.POOLING_GAIN, Estimand.CTK_GAIN, Estimand.CTK_SHARE],
            )
        )
        .join(
            claims.filter(pl.col(Column.CLAIM) == ClaimName.COMPLEMENTARY_KNOWLEDGE).select(
                Column.CLAIM_STATUS
            ),
            how=LibraryOption.JOIN_CROSS,
        )
        .select(
            Column.EXPERIMENT,
            Column.ALPHA,
            Column.LEARNER,
            Column.METRIC,
            Column.ESTIMAND,
            Column.CONTRAST_FAMILY,
            Column.MEAN_DIFFERENCE,
            Column.MEDIAN_DIFFERENCE,
            Column.CI_LOW,
            Column.CI_HIGH,
            Column.P_VALUE,
            Column.P_HOLM,
            Column.POSITIVE_SEEDS,
            Column.SEED_COUNT,
            Column.EFFECT_SIZE,
            Column.CLAIM_STATUS,
        )
        .sort(Column.ALPHA, Column.LEARNER, Column.METRIC, Column.ESTIMAND)
    )


def peer_dose_response(paths: Paths, mode: ExecutionMode) -> DoseReportTable:
    return (
        pl.read_parquet(paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE))
        .group_by(Column.LEARNER, Column.DOSE)
        .agg(
            pl.col(Column.EFFECTIVE_DOSE).mean(),
            pl.col(Column.RECALL).mean(),
            pl.col(Column.RECALL).std().alias(Column.RECALL_STD),
            pl.col(Column.CTK_GAIN).mean(),
        )
        .sort(Column.LEARNER, Column.DOSE, nulls_last=True)
    )


def family_level(paths: Paths, config: Config, mode: ExecutionMode) -> FamilyLevelTable:
    poor = config.statistics.gates.poor_full_recall
    return (
        pl.read_parquet(paths.analysis_file(mode, Artifact.FAMILY_RESCUE))
        .with_columns(
            pl.when(pl.col(Column.FULL_RECALL) < poor)
            .then(pl.lit(FamilyOutcome.POORLY_RESCUED))
            .otherwise(pl.lit(FamilyOutcome.RESCUED))
            .alias(Column.CLASSIFICATION)
        )
        .sort(Column.EXPERIMENT, Column.LEARNER, Column.FAMILY)
    )


def claim_gates(paths: Paths, mode: ExecutionMode) -> ClaimsTable:
    return pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))


def robustness(paths: Paths, mode: ExecutionMode) -> RobustnessTable:
    return pl.read_parquet(paths.analysis_file(mode, Artifact.ROBUSTNESS)).sort(
        Column.EXPERIMENT, Column.SENSITIVITY
    )


def build_tables(paths: Paths, config: Config, mode: ExecutionMode) -> ReportTables:
    return {
        ReportTable.DATASET_CLIENT_AUDIT: dataset_client_audit(paths),
        ReportTable.PRIMARY_ARM_COMPARISON: primary_arm_comparison(paths, config, mode),
        ReportTable.COLLABORATION_DECOMPOSITION: collaboration_decomposition(paths, mode),
        ReportTable.PEER_DOSE_RESPONSE: peer_dose_response(paths, mode),
        ReportTable.FAMILY_LEVEL: family_level(paths, config, mode),
        ReportTable.CLAIM_GATES: claim_gates(paths, mode),
        ReportTable.ROBUSTNESS: robustness(paths, mode),
    }
