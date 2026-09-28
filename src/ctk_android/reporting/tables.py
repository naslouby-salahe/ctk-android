import polars as pl

from ctk_android.analysis.decomposition import dose_levels
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of
from ctk_android.enums import (
    Artifact,
    Column,
    Estimand,
    ExecutionMode,
    ExperimentName,
    FamilyOutcome,
    LibraryOption,
    Metric,
    OptimizationStatus,
    ReportTable,
    RunStatus,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    ArmComparisonTable,
    CalibrationTable,
    ClientAuditTable,
    ConvergenceTable,
    DecompositionReportTable,
    DoseReportTable,
    FamilyLevelTable,
    FamilyRescueTable,
    Fraction,
    ReportTables,
    RobustnessTable,
    RunIndexTable,
    RunKey,
    Table,
)


def _arm_columns() -> list[Column]:
    return [Column.LEARNER, Column.CONDITION, Column.DOSE, Column.PARAMETER, Column.TUNING_VALUE]


def _tagged(frame: Table, key: RunKey) -> Table:
    return frame.with_columns(
        pl.lit(key.experiment).alias(Column.EXPERIMENT),
        pl.lit(key.seed).alias(Column.SEED),
        pl.lit(key.salt).alias(Column.SALT),
    )


def _completed(index: RunIndexTable) -> Table:
    return index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED)


def _keys(index: RunIndexTable, mode: ExecutionMode) -> list[RunKey]:
    return [
        RunKey(
            mode=mode,
            experiment=row[Column.EXPERIMENT],
            seed=row[Column.SEED],
            salt=row[Column.SALT],
        )
        for row in _completed(index).iter_rows(named=True)
    ]


def operating_calibration(
    paths: Paths, config: Config, mode: ExecutionMode, index: RunIndexTable
) -> CalibrationTable:
    tolerance = config.experiments.operating.realised_fpr_tolerance
    frames = [
        _tagged(pl.read_parquet(paths.run_metric_file(key, Artifact.OPERATING_POINTS)), key)
        for key in _keys(index, mode)
    ]
    if not frames:
        return pl.DataFrame()
    table = pl.concat(frames)
    deviation = pl.col(Column.VALUE) - pl.col(Column.ALPHA)
    return table.select(
        Column.EXPERIMENT,
        Column.SEED,
        Column.SALT,
        *_arm_columns(),
        Column.CLIENT,
        pl.col(Column.ALPHA).alias(Column.REQUESTED_ALPHA),
        Column.THRESHOLD,
        Column.CALIBRATION_BENIGN,
        pl.col(Column.TRIALS).alias(Column.BENIGN_TEST),
        Column.HITS,
        pl.col(Column.VALUE).alias(Column.CLIENT_REALISED_FPR),
        deviation.alias(Column.CLIENT_FPR_DEVIATION),
        (deviation.abs() > tolerance).alias(Column.FPR_BREACH),
        Column.OPERATING_STATUS,
    )


def client_fpr_summary(calibration: CalibrationTable) -> CalibrationTable:
    if calibration.height == 0:
        return pl.DataFrame()
    return (
        calibration.group_by(
            Column.EXPERIMENT, Column.CLIENT, Column.REQUESTED_ALPHA, maintain_order=True
        )
        .agg(
            pl.len().alias(Column.ROWS),
            pl.col(Column.CALIBRATION_BENIGN).mean().alias(Column.CALIBRATION_BENIGN),
            pl.col(Column.BENIGN_TEST).mean().alias(Column.BENIGN_TEST),
            pl.col(Column.CLIENT_REALISED_FPR).mean().alias(Column.CLIENT_REALISED_FPR),
            pl.col(Column.CLIENT_FPR_DEVIATION).mean().alias(Column.CLIENT_FPR_DEVIATION),
            pl.col(Column.CLIENT_FPR_DEVIATION).abs().max().alias(Column.MAX_FPR_DEVIATION),
            pl.col(Column.FPR_BREACH).sum().alias(Column.BREACHES),
        )
        .sort(Column.EXPERIMENT, Column.CLIENT, Column.REQUESTED_ALPHA)
    )


def _calibration_auroc(paths: Paths, key: RunKey) -> Table:
    return (
        pl.read_parquet(paths.run_metric_file(key, Artifact.SUMMARY))
        .filter(pl.col(Column.METRIC) == Metric.CALIBRATION_AUROC)
        .group_by(*_arm_columns(), maintain_order=True)
        .agg(pl.col(Column.VALUE).mean().alias(Column.CALIBRATION_AUROC))
    )


def training_convergence(
    paths: Paths, mode: ExecutionMode, index: RunIndexTable
) -> ConvergenceTable:
    frames = [
        _tagged(pl.read_parquet(paths.run_file(key, Artifact.TRAINING)), key).join(
            _calibration_auroc(paths, key),
            on=_arm_columns(),
            how=LibraryOption.JOIN_LEFT,
            nulls_equal=True,
        )
        for key in _keys(index, mode)
        if paths.run_file(key, Artifact.TRAINING).is_file()
    ]
    frames = [frame for frame in frames if frame.height]
    if not frames:
        return pl.DataFrame()
    stacked = pl.concat(frames, how=LibraryOption.CONCAT_DIAGONAL_RELAXED)
    return (
        stacked.group_by(
            Column.EXPERIMENT,
            Column.SEED,
            Column.SALT,
            *_arm_columns(),
            Column.PHASE,
            Column.CLIENT,
            maintain_order=True,
        )
        .agg(
            pl.len().alias(Column.RECORDS),
            pl.col(Column.LOSS).drop_nulls().first().alias(Column.FIRST_LOSS),
            pl.col(Column.LOSS).drop_nulls().last().alias(Column.FINAL_LOSS),
            pl.col(Column.NONFINITE_BATCHES).sum().alias(Column.NONFINITE_BATCHES),
            pl.col(Column.PARAMETERS_FINITE).all().alias(Column.PARAMETERS_FINITE),
            (pl.col(Column.STATUS) != OptimizationStatus.COMPLETED).any().alias(Column.FLAGGED),
            pl.col(Column.CALIBRATION_AUROC).first().alias(Column.CALIBRATION_AUROC),
        )
        .sort(Column.EXPERIMENT, Column.SEED, Column.SALT, Column.LEARNER, Column.PHASE)
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
    per_client = families.group_by(Column.CLIENT, maintain_order=True).agg(
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
        summary.group_by(Column.LEARNER, Column.CONDITION, Column.METRIC, maintain_order=True)
        .agg(pl.col(Column.VALUE).mean())
        .pivot(on=Column.METRIC, index=[Column.LEARNER, Column.CONDITION], values=Column.VALUE)
    )
    ordered = [metric for metric in _primary_metrics() if metric in wide.columns]
    return wide.select(Column.LEARNER, Column.CONDITION, *ordered).sort(
        Column.LEARNER, Column.CONDITION
    )


def collaboration_decomposition(paths: Paths, mode: ExecutionMode) -> DecompositionReportTable:
    effects = pl.read_parquet(paths.statistics_file(mode, Artifact.PAIRED_EFFECTS))
    return (
        effects.filter(
            (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
            & is_one_of(
                Column.ESTIMAND,
                [Estimand.TOTAL_GAIN, Estimand.POOLING_GAIN, Estimand.CTK_GAIN, Estimand.CTK_SHARE],
            )
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
        )
        .sort(Column.ALPHA, Column.LEARNER, Column.METRIC, Column.ESTIMAND)
    )


def peer_dose_response(paths: Paths, config: Config, mode: ExecutionMode) -> DoseReportTable:
    return dose_levels(
        pl.read_parquet(paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE)),
        config.statistics.thresholds.dose_min_peers,
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
        config.statistics.thresholds.poor_full_recall,
    )


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
        ReportTable.ROBUSTNESS: robustness(paths, mode),
        ReportTable.FAMILY_CLIENT_CTK: _analysis(paths, mode, Artifact.FAMILY_CLIENT_CTK),
        ReportTable.CTK_VARIANCE: _analysis(paths, mode, Artifact.CTK_VARIANCE),
        ReportTable.FAMILY_ASSOCIATIONS: _analysis(paths, mode, Artifact.FAMILY_ASSOCIATIONS),
        ReportTable.CLIENT_CTK: _analysis(paths, mode, Artifact.CLIENT_CTK),
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
