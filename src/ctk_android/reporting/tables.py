import polars as pl

from ctk_android.analysis.dose_response import dose_levels
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
    FamilyRescueTable,
    Fraction,
    ReportTables,
    RobustnessTable,
    Table,
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
    wide = (
        summary.group_by(Column.LEARNER, Column.CONDITION, Column.METRIC)
        .agg(pl.col(Column.VALUE).mean())
        .pivot(on=Column.METRIC, index=[Column.LEARNER, Column.CONDITION], values=Column.VALUE)
    )
    ordered = [metric for metric in _primary_metrics() if metric in wide.columns]
    return wide.select(Column.LEARNER, Column.CONDITION, *ordered).sort(
        Column.LEARNER, Column.CONDITION
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


def peer_dose_response(paths: Paths, config: Config, mode: ExecutionMode) -> DoseReportTable:
    return dose_levels(
        pl.read_parquet(paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE)),
        config.statistics.gates.dose_min_peers,
    ).select(
        Column.LEARNER,
        Column.DOSE_LEVEL,
        Column.DOSE,
        Column.EFFECTIVE_DOSE,
        Column.RECALL,
        Column.RECALL_STD,
        Column.CTK_GAIN,
        Column.OBSERVATIONS,
        Column.OBSERVATIONS_MET,
        Column.MEETS_DOSE_CRITERION,
    )


def classify_families(rescue: FamilyRescueTable, poor: Fraction) -> FamilyLevelTable:
    return rescue.with_columns(
        pl.when(pl.col(Column.FULL_RECALL).is_null())
        .then(pl.lit(FamilyOutcome.NOT_CLASSIFIABLE))
        .when(pl.col(Column.FULL_RECALL) < poor)
        .then(pl.lit(FamilyOutcome.POORLY_RESCUED))
        .otherwise(pl.lit(FamilyOutcome.RESCUED))
        .alias(Column.CLASSIFICATION)
    ).sort(Column.EXPERIMENT, Column.LEARNER, Column.FAMILY)


def family_level(paths: Paths, config: Config, mode: ExecutionMode) -> FamilyLevelTable:
    return classify_families(
        pl.read_parquet(paths.analysis_file(mode, Artifact.FAMILY_RESCUE)),
        config.statistics.gates.poor_full_recall,
    )


def claim_gates(paths: Paths, mode: ExecutionMode) -> ClaimsTable:
    return pl.read_parquet(paths.statistics_file(mode, Artifact.CLAIM_GATES))


def robustness(paths: Paths, mode: ExecutionMode) -> RobustnessTable:
    return pl.read_parquet(paths.analysis_file(mode, Artifact.ROBUSTNESS)).sort(
        Column.EXPERIMENT, Column.SALT, Column.SENSITIVITY
    )


def _analysis(paths: Paths, mode: ExecutionMode, artifact: Artifact) -> Table:
    return pl.read_parquet(paths.analysis_file(mode, artifact))


def build_tables(paths: Paths, config: Config, mode: ExecutionMode) -> ReportTables:
    return {
        ReportTable.DATASET_CLIENT_AUDIT: dataset_client_audit(paths),
        ReportTable.PRIMARY_ARM_COMPARISON: primary_arm_comparison(paths, config, mode),
        ReportTable.COLLABORATION_DECOMPOSITION: collaboration_decomposition(paths, mode),
        ReportTable.PEER_DOSE_RESPONSE: peer_dose_response(paths, config, mode),
        ReportTable.FAMILY_LEVEL: family_level(paths, config, mode),
        ReportTable.CLAIM_GATES: claim_gates(paths, mode),
        ReportTable.ROBUSTNESS: robustness(paths, mode),
        ReportTable.ANCHORED_WORST_CLIENT: _analysis(paths, mode, Artifact.ANCHORED_WORST_CLIENT),
        ReportTable.ANCHORED_CLIENT_SELECTION: _analysis(
            paths, mode, Artifact.ANCHORED_CLIENT_SELECTION
        ),
        ReportTable.ARM_TRADEOFF: _analysis(paths, mode, Artifact.ARM_TRADEOFF),
        ReportTable.ROBUSTNESS_SYNTHESIS: _analysis(paths, mode, Artifact.ROBUSTNESS_SYNTHESIS),
        ReportTable.FAMILY_PATTERNS: _analysis(paths, mode, Artifact.FAMILY_PATTERNS),
        ReportTable.NATURAL_COMPARISON: _analysis(paths, mode, Artifact.NATURAL_COMPARISON),
        ReportTable.PERMUTATION_AUDIT: _analysis(paths, mode, Artifact.PERMUTATION_AUDIT),
        ReportTable.MECHANISM_HEADROOM: _analysis(paths, mode, Artifact.MECHANISM_HEADROOM),
        ReportTable.OPERATING_FIDELITY: _analysis(paths, mode, Artifact.OPERATING_FIDELITY),
    }
