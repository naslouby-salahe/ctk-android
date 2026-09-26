import numpy as np
import polars as pl
from scipy import linalg, optimize, stats
from threadpoolctl import threadpool_limits

from ctk_android.analysis.decomposition import decomposed_learners, dose_levels, with_level_exposure
from ctk_android.analysis.statistics import paired_effect
from ctk_android.config import Config, StatisticsConfig, TrainingConfig
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    AllowedWording,
    ClaimName,
    ClaimStatus,
    ClientId,
    Column,
    CtkAggregation,
    EligibilityProfile,
    Estimand,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    FamilyOutcomeMeasure,
    FamilyPredictor,
    IntervalStatus,
    IntervalVerdict,
    Learner,
    LibraryOption,
    MaskingContrast,
    Metric,
    OperatingPointStatus,
    PermutationOutcome,
    RobustnessScope,
    Sensitivity,
    StatisticsLimit,
    Tolerance,
    TradeoffComparison,
    TradeoffMeasure,
    TransferScope,
    TunedParameter,
    VarianceComponent,
    VarianceSource,
)
from ctk_android.types import (
    Alpha,
    AnchoredEffectRow,
    AnchoredSelectionRow,
    AnchoredTable,
    ArmPair,
    ArmSeries,
    ArmSpec,
    AssociationTable,
    AuditTable,
    CellTable,
    ClaimResult,
    ClaimsTable,
    ClientCountsTable,
    ClientCtkRow,
    ClientCtkTable,
    ComparisonTable,
    Confidence,
    ContrastSpec,
    Correlation,
    DevianceAndGradient,
    Effect,
    EffectRow,
    EffectsTable,
    FamilyAssociationRow,
    FamilyClientRow,
    FamilyClientTable,
    FamilyCountsTable,
    FamilyEffectsTable,
    FamilyGainsTable,
    FamilyName,
    FamilySeedTable,
    FidelityTable,
    Fraction,
    FrozenHyperparameters,
    GateEvidence,
    GroupCodes,
    HeadroomRow,
    HeadroomTable,
    HeterogeneityRow,
    HeterogeneityTable,
    Interval,
    MaskingRow,
    MaskingTable,
    MetricPair,
    MicroGainTable,
    Passed,
    PatternTable,
    PermutationAuditRow,
    PooledRecallTable,
    Positive,
    RandomEffectsDesign,
    RatesTable,
    Refuted,
    ResampleCount,
    RobustnessRow,
    RobustnessTable,
    RowCount,
    ScopeMap,
    SeedEffects,
    SeedMatrix,
    SeedMeansTable,
    SeedSummary,
    SelectionTable,
    SummaryTable,
    SupportCount,
    SynthesisRow,
    SynthesisTable,
    Table,
    TradeoffRow,
    TradeoffTable,
    TransferRow,
    TransferScopeSpec,
    TransferTable,
    TuningValue,
    ValueSeries,
    VarianceEstimate,
    VarianceRow,
    VarianceTable,
    VarianceVector,
)


def _ordered(frame: Table, *columns: Column) -> Table:
    return frame.sort(*columns) if frame.height else frame


def summarize_seeds(values: SeedEffects, config: StatisticsConfig) -> SeedSummary | None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    effect = paired_effect(finite, config)
    return SeedSummary(
        mean_difference=effect.mean,
        median_difference=effect.median,
        ci_low=effect.interval.low if effect.interval else None,
        ci_high=effect.interval.high if effect.interval else None,
        positive_seeds=effect.positive_seeds,
        seed_count=effect.seeds,
    )


def _federation_client_recalls(clients: ClientCountsTable, alpha: Alpha) -> RatesTable:
    return (
        clients.filter(
            (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
            & (pl.col(Column.ALPHA) == alpha)
            & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
            & pl.col(Column.DOSE).is_null()
            & (pl.col(Column.TRIALS) >= 1)
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .select(
            Column.SEED,
            Column.SALT,
            Column.LEARNER,
            Column.CONDITION,
            Column.CLIENT,
            Column.RECALL,
        )
    )


def _client_arm(
    recalls: RatesTable, learner: Learner, condition: ExposureCondition, name: Column
) -> RatesTable:
    return recalls.filter(
        (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
    ).select(Column.SEED, Column.SALT, Column.CLIENT, pl.col(Column.RECALL).alias(name))


def _local_worst_clients(recalls: RatesTable) -> RatesTable:
    local = _client_arm(recalls, Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL)
    return (
        local.sort(Column.SEED, Column.SALT, Column.LOCAL_RECALL, Column.CLIENT)
        .group_by(Column.SEED, Column.SALT, maintain_order=True)
        .first()
    )


def anchored_worst_client(clients: ClientCountsTable, config: Config) -> AnchoredTable:
    recalls = _federation_client_recalls(clients, config.experiments.operating.primary_alpha)
    keys = [Column.SEED, Column.SALT, Column.CLIENT]
    worst = _local_worst_clients(recalls)
    full = _client_arm(
        recalls, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE, Column.FULL_RECALL
    )
    rows: list[AnchoredEffectRow] = []
    for learner in decomposed_learners():
        followed = (
            worst.join(
                _client_arm(recalls, learner, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL),
                on=keys,
            )
            .join(
                _client_arm(
                    recalls,
                    learner,
                    ExposureCondition.FAMILY_ABSENT_EVERYWHERE,
                    Column.ABSENT_RECALL,
                ),
                on=keys,
            )
            .join(full, on=keys)
            .sort(Column.SEED)
        )
        local_recall = followed[Column.LOCAL_RECALL].to_numpy()
        peer = followed[Column.PEER_RECALL].to_numpy()
        absent = followed[Column.ABSENT_RECALL].to_numpy()
        estimands = {
            Estimand.TOTAL_GAIN: peer - local_recall,
            Estimand.POOLING_GAIN: absent - local_recall,
            Estimand.CTK_GAIN: peer - absent,
        }
        if learner is Learner.CENTRAL:
            estimands[Estimand.LOCAL_DEFICIT] = (
                followed[Column.FULL_RECALL].to_numpy() - local_recall
            )
        for estimand, values in estimands.items():
            summary = summarize_seeds(values, config.statistics)
            if summary is not None:
                rows.append(
                    AnchoredEffectRow(
                        evidence_class=EvidenceClass.POST_CONFIRMATORY,
                        learner=learner,
                        estimand=estimand,
                        **summary.model_dump(),
                    )
                )
    return records_to_frame(rows)


def anchored_client_selection(clients: ClientCountsTable, config: Config) -> SelectionTable:
    recalls = _federation_client_recalls(clients, config.experiments.operating.primary_alpha)
    selection = (
        _local_worst_clients(recalls)
        .group_by(Column.CLIENT)
        .agg(
            pl.len().alias(Column.SEEDS_SELECTED),
            pl.col(Column.LOCAL_RECALL).mean().alias(Column.MEAN_LOCAL_RECALL),
        )
        .sort(Column.CLIENT)
    )
    return records_to_frame(
        [
            AnchoredSelectionRow(
                evidence_class=EvidenceClass.POST_CONFIRMATORY,
                client=row[Column.CLIENT],
                seeds_selected=row[Column.SEEDS_SELECTED],
                mean_local_recall=row[Column.MEAN_LOCAL_RECALL],
            )
            for row in selection.iter_rows(named=True)
        ]
    )


def _series(
    summary: SummaryTable,
    learner: Learner,
    condition: ExposureCondition,
    metric: Metric,
    alpha: Alpha,
) -> SeedEffects | None:
    rows = summary.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.CONDITION) == condition)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ALPHA) == alpha)
    ).sort(Column.SEED)
    return rows[Column.VALUE].to_numpy() if rows.height else None


def _change(
    summary: SummaryTable, learner: Learner, metric: Metric, alpha: Alpha
) -> SeedEffects | None:
    peer = _series(summary, learner, ExposureCondition.PEER_PRESENT, metric, alpha)
    local = _series(summary, Learner.LOCAL, ExposureCondition.PEER_PRESENT, metric, alpha)
    return None if peer is None or local is None else peer - local


def _measure(
    summary: SummaryTable, learner: Learner, measure: TradeoffMeasure, alpha: Alpha
) -> SeedEffects | None:
    federation = Metric.FEDERATION_UNSEEN_RECALL
    peer = _series(summary, learner, ExposureCondition.PEER_PRESENT, federation, alpha)
    absent = _series(
        summary, learner, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, federation, alpha
    )
    local = _series(summary, Learner.LOCAL, ExposureCondition.PEER_PRESENT, federation, alpha)
    full = _series(summary, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE, federation, alpha)
    match measure:
        case TradeoffMeasure.FEDERATION_UNSEEN_RECALL_CHANGE:
            return _change(summary, learner, federation, alpha)
        case TradeoffMeasure.OWN_DOMAIN_UNSEEN_RECALL_CHANGE:
            return _change(summary, learner, Metric.OWN_DOMAIN_UNSEEN_RECALL, alpha)
        case TradeoffMeasure.WORST_CLIENT_UNSEEN_RECALL_CHANGE:
            return _change(summary, learner, Metric.WORST_CLIENT_UNSEEN_RECALL, alpha)
        case TradeoffMeasure.KNOWN_FAMILY_RECALL_CHANGE:
            return _change(summary, learner, Metric.KNOWN_FAMILY_RECALL, alpha)
        case TradeoffMeasure.REALISED_FPR_CHANGE:
            return _change(summary, learner, Metric.REALISED_FPR, alpha)
        case TradeoffMeasure.CTK_GAIN:
            return None if peer is None or absent is None else peer - absent
        case TradeoffMeasure.POOLING_GAIN:
            return None if absent is None or local is None else absent - local
        case TradeoffMeasure.FULL_EXPOSURE_GAP:
            return None if full is None or peer is None else full - peer
        case TradeoffMeasure.ORACLE_GAP_RECOVERY:
            return _oracle_recovery(peer, local, full)


def _oracle_recovery(
    peer: SeedEffects | None, local: SeedEffects | None, full: SeedEffects | None
) -> SeedEffects | None:
    if peer is None or local is None or full is None:
        return None
    headroom = full - local
    resolved = headroom != 0
    return np.where(resolved, (peer - local) / np.where(resolved, headroom, 1.0), np.nan)


def _within_tolerance(measure: TradeoffMeasure, mean: Effect, config: Config) -> Passed | None:
    gates = config.statistics.gates
    if measure is TradeoffMeasure.KNOWN_FAMILY_RECALL_CHANGE:
        return abs(mean) <= gates.known_family_tolerance
    if measure is TradeoffMeasure.REALISED_FPR_CHANGE:
        return mean <= gates.fpr_tolerance
    return None


def _tradeoff_rows_for_learner(
    summary: SummaryTable,
    measure: TradeoffMeasure,
    learner: Learner,
    reference: SeedEffects | None,
    alpha: Alpha,
    config: Config,
) -> list[TradeoffRow]:
    values = _measure(summary, learner, measure, alpha)
    if values is None:
        return []
    versus_local = summarize_seeds(values, config.statistics)
    if versus_local is None:
        return []
    rows = [
        TradeoffRow(
            evidence_class=EvidenceClass.POST_CONFIRMATORY,
            learner=learner,
            comparison=TradeoffComparison.VERSUS_LOCAL,
            measure=measure,
            within_tolerance=_within_tolerance(measure, versus_local.mean_difference, config),
            **versus_local.model_dump(),
        )
    ]
    if learner is Learner.FEDAVG or reference is None:
        return rows
    difference = summarize_seeds(values - reference, config.statistics)
    if difference is not None:
        rows.append(
            TradeoffRow(
                evidence_class=EvidenceClass.POST_CONFIRMATORY,
                learner=learner,
                comparison=TradeoffComparison.VERSUS_FEDAVG,
                measure=measure,
                within_tolerance=None,
                **difference.model_dump(),
            )
        )
    return rows


def federated_arm_tradeoff(summary: SummaryTable, config: Config) -> TradeoffTable:
    alpha = config.experiments.operating.primary_alpha
    arms = (*federated_arms(), Learner.BLEND, Learner.CENTRAL)
    rows: list[TradeoffRow] = []
    for measure in TradeoffMeasure:
        reference = _measure(summary, Learner.FEDAVG, measure, alpha)
        for learner in arms:
            rows.extend(
                _tradeoff_rows_for_learner(summary, measure, learner, reference, alpha, config)
            )
    return records_to_frame(rows)


def robustness_scopes() -> ScopeMap:
    return {
        ExperimentName.CONTROLLED_EXPOSURE: RobustnessScope.PRIMARY_FAMILY_SET,
        ExperimentName.REPLICATION_FAMILY_SET: RobustnessScope.REPLICATION_FAMILY_SET,
        ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR: RobustnessScope.LINEAR_MODEL,
        ExperimentName.MODEL_FAMILY_REPLICATION_TREES: RobustnessScope.TREE_MODEL,
        ExperimentName.TRAINING_SUPPORT_SENSITIVITY: RobustnessScope.LOWER_TRAINING_SUPPORT,
        ExperimentName.FAMILY_SUPPORT_SENSITIVITY_LOW: RobustnessScope.LOW_FAMILY_SUPPORT,
        ExperimentName.FAMILY_SUPPORT_SENSITIVITY_HIGH: RobustnessScope.HIGH_FAMILY_SUPPORT,
        ExperimentName.PARTITION_SALT_SENSITIVITY: RobustnessScope.PARTITION_SALT,
        ExperimentName.PACKAGE_ONLY_GROUPING: RobustnessScope.PACKAGE_ONLY_GROUPING,
        ExperimentName.NATURAL_SCARCITY: RobustnessScope.NATURAL_SCARCITY,
        ExperimentName.FAMILY_PERMUTATION_CONTROL: RobustnessScope.PERMUTATION_CONTROL,
    }


def _feeds_a_gate(experiment: ExperimentName, learner: Learner, metric: Metric | None) -> Passed:
    if learner is not Learner.FEDAVG:
        return False
    if experiment is ExperimentName.CONTROLLED_EXPOSURE:
        return metric in (
            Metric.FEDERATION_UNSEEN_RECALL,
            Metric.OWN_DOMAIN_UNSEEN_RECALL,
            Metric.WORST_CLIENT_UNSEEN_RECALL,
        )
    return (
        experiment
        in (ExperimentName.REPLICATION_FAMILY_SET, ExperimentName.FAMILY_PERMUTATION_CONTROL)
        and metric is Metric.FEDERATION_UNSEEN_RECALL
    )


def ctk_robustness_synthesis(
    effects: EffectsTable, robustness: RobustnessTable, config: Config
) -> SynthesisTable:
    minimum = config.statistics.gates.ctk_min_gain
    primary = config.experiments.operating.primary_alpha
    scopes = robustness_scopes()
    rows: list[SynthesisRow] = []
    paired = (
        effects.filter(
            (pl.col(Column.ESTIMAND) == Estimand.CTK_GAIN)
            & is_one_of(Column.EXPERIMENT, list(scopes))
            & is_one_of(Column.LEARNER, [Learner.FEDAVG, Learner.CENTRAL])
        )
        if effects.height
        else effects
    )
    for record in paired.iter_rows(named=True):
        row = EffectRow.model_validate(record)
        gate_input = _feeds_a_gate(row.experiment, row.learner, row.metric) and row.alpha == primary
        rows.append(
            SynthesisRow(
                evidence_class=EvidenceClass.ORIGINAL_CONFIRMATORY
                if gate_input
                else EvidenceClass.CONFIRMATORY_SENSITIVITY,
                scope=scopes[row.experiment],
                experiment=row.experiment,
                salt=row.salt,
                alpha=row.alpha,
                metric=row.metric,
                learner=row.learner,
                aggregation=CtkAggregation.PAIRED_SEED_MACRO,
                sensitivity=None,
                mean_difference=row.mean_difference,
                median_difference=row.median_difference or row.mean_difference,
                ci_low=row.ci_low,
                ci_high=row.ci_high,
                positive_seeds=row.positive_seeds or 0,
                seed_count=row.seed_count,
                exceeds_practical_threshold=row.mean_difference >= minimum,
                ci_excludes_zero=None if row.ci_low is None else row.ci_low > 0,
            )
        )
    for record in robustness.filter(is_one_of(Column.EXPERIMENT, list(scopes))).iter_rows(
        named=True
    ):
        gain = record[Column.MICRO_POOLED_CTK_GAIN]
        low = record[Column.CI_LOW]
        rows.append(
            SynthesisRow(
                evidence_class=EvidenceClass.CONFIRMATORY_SENSITIVITY,
                scope=scopes[record[Column.EXPERIMENT]],
                experiment=record[Column.EXPERIMENT],
                salt=record[Column.SALT],
                alpha=record[Column.ALPHA],
                metric=None,
                learner=Learner.FEDAVG,
                aggregation=CtkAggregation.MICRO_POOLED,
                sensitivity=record[Column.SENSITIVITY],
                mean_difference=gain,
                median_difference=record[Column.MEDIAN_DIFFERENCE],
                ci_low=low,
                ci_high=record[Column.CI_HIGH],
                positive_seeds=record[Column.POSITIVE_SEEDS],
                seed_count=record[Column.SEED_COUNT],
                exceeds_practical_threshold=gain >= minimum,
                ci_excludes_zero=None if low is None else low > 0,
            )
        )
    return _ordered(
        records_to_frame(rows),
        Column.SCOPE,
        Column.AGGREGATION,
        Column.ALPHA,
        Column.SALT,
        Column.LEARNER,
        Column.METRIC,
        Column.SENSITIVITY,
        Column.EXPERIMENT,
    )


def permutation_control_audit(effects: EffectsTable, config: Config) -> AuditTable:
    band = config.statistics.gates.ctk_min_gain
    primary = config.experiments.operating.primary_alpha
    control = effects.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.FAMILY_PERMUTATION_CONTROL)
        & (pl.col(Column.ESTIMAND) == Estimand.CTK_GAIN)
        & is_one_of(Column.LEARNER, [Learner.FEDAVG, Learner.CENTRAL])
    )
    rows: list[PermutationAuditRow] = []
    for record in control.iter_rows(named=True):
        row = EffectRow.model_validate(record)
        gate_input = (
            row.learner is Learner.FEDAVG
            and row.alpha == primary
            and row.metric is Metric.FEDERATION_UNSEEN_RECALL
        )
        rows.append(
            PermutationAuditRow(
                evidence_class=EvidenceClass.ORIGINAL_CONFIRMATORY
                if gate_input
                else EvidenceClass.POST_CONFIRMATORY,
                experiment=row.experiment,
                alpha=row.alpha,
                metric=row.metric,
                learner=row.learner,
                outcome=permutation_outcome(row, band),
                mean_difference=row.mean_difference,
                median_difference=row.median_difference or row.mean_difference,
                ci_low=row.ci_low,
                ci_high=row.ci_high,
                positive_seeds=row.positive_seeds or 0,
                seed_count=row.seed_count,
            )
        )
    return _ordered(records_to_frame(rows), Column.LEARNER, Column.METRIC, Column.ALPHA)


def mechanism_headroom(summary: SummaryTable, config: Config) -> HeadroomTable:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha
    thresholds = {
        Metric.FEDERATION_UNSEEN_RECALL: gates.mechanism_mean_gap,
        Metric.WORST_CLIENT_UNSEEN_RECALL: gates.mechanism_worst_gap,
    }
    rows: list[HeadroomRow] = []
    for metric, threshold in thresholds.items():
        full = _series(summary, Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE, metric, alpha)
        for learner in simple_baselines():
            peer = _series(summary, learner, ExposureCondition.PEER_PRESENT, metric, alpha)
            if full is None or peer is None:
                continue
            gap = summarize_seeds(full - peer, config.statistics)
            if gap is None:
                continue
            rows.append(
                HeadroomRow(
                    evidence_class=EvidenceClass.ORIGINAL_CONFIRMATORY,
                    learner=learner,
                    metric=metric,
                    gate_threshold=threshold,
                    exceeds_gate_threshold=gap.mean_difference > threshold,
                    **gap.model_dump(),
                )
            )
    return _ordered(records_to_frame(rows), Column.METRIC, Column.LEARNER)


def family_mechanism_patterns(family_effects: FamilyEffectsTable) -> PatternTable:
    frozen = list(frozen_family_set_experiments())
    fedavg = family_effects.filter(
        is_one_of(Column.EXPERIMENT, frozen) & (pl.col(Column.LEARNER) == Learner.FEDAVG)
    ).select(
        Column.EXPERIMENT,
        Column.FAMILY,
        Column.TRIALS,
        Column.SEED_COUNT,
        Column.LOCAL_RECALL,
        Column.ABSENT_RECALL,
        Column.PEER_RECALL,
        Column.CTK_GAIN,
    )
    central_full = family_effects.filter(
        is_one_of(Column.EXPERIMENT, frozen) & (pl.col(Column.LEARNER) == Learner.CENTRAL)
    ).select(Column.EXPERIMENT, Column.FAMILY, Column.FULL_RECALL)

    def other_model(experiment: ExperimentName, name: Column) -> PatternTable:
        return family_effects.filter(
            (pl.col(Column.EXPERIMENT) == experiment) & (pl.col(Column.LEARNER) == Learner.CENTRAL)
        ).select(Column.FAMILY, pl.col(Column.FULL_RECALL).alias(name))

    return (
        fedavg.join(
            central_full, on=[Column.EXPERIMENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT
        )
        .join(
            other_model(ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR, Column.LINEAR_FULL_RECALL),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        )
        .join(
            other_model(ExperimentName.MODEL_FAMILY_REPLICATION_TREES, Column.TREES_FULL_RECALL),
            on=Column.FAMILY,
            how=LibraryOption.JOIN_LEFT,
        )
        .with_columns(
            (pl.col(Column.ABSENT_RECALL) - pl.col(Column.LOCAL_RECALL)).alias(Column.POOLING_GAIN),
            (pl.col(Column.PEER_RECALL) - pl.col(Column.LOCAL_RECALL)).alias(Column.TOTAL_GAIN),
            pl.lit(EvidenceClass.POST_CONFIRMATORY).alias(Column.EVIDENCE_CLASS),
        )
        .sort(Column.EXPERIMENT, Column.CTK_GAIN, descending=[False, True])
    )


def natural_scarcity_comparison(
    effects: EffectsTable, family_seed: FamilySeedTable, config: Config
) -> ComparisonTable:
    alpha = config.experiments.operating.primary_alpha
    experiments = [ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.NATURAL_SCARCITY]
    coverage = (
        family_seed.filter(is_one_of(Column.EXPERIMENT, experiments))
        .group_by(Column.EXPERIMENT)
        .agg(
            pl.col(Column.FAMILY).n_unique().alias(Column.FAMILIES),
            pl.col(Column.CLIENT).n_unique().alias(Column.CLIENTS),
        )
    )
    return (
        effects.filter(
            is_one_of(Column.EXPERIMENT, experiments)
            & (pl.col(Column.ALPHA) == alpha)
            & is_one_of(Column.LEARNER, [Learner.FEDAVG, Learner.CENTRAL])
            & is_one_of(
                Column.ESTIMAND,
                [
                    Estimand.TOTAL_GAIN,
                    Estimand.POOLING_GAIN,
                    Estimand.CTK_GAIN,
                    Estimand.CTK_SHARE,
                    Estimand.POOLING_SHARE,
                ],
            )
        )
        .join(coverage, on=Column.EXPERIMENT, how=LibraryOption.JOIN_LEFT)
        .with_columns(pl.lit(EvidenceClass.CONFIRMATORY_SENSITIVITY).alias(Column.EVIDENCE_CLASS))
        .select(
            Column.EVIDENCE_CLASS,
            Column.EXPERIMENT,
            Column.LEARNER,
            Column.METRIC,
            Column.ESTIMAND,
            Column.MEAN_DIFFERENCE,
            Column.CI_LOW,
            Column.CI_HIGH,
            Column.POSITIVE_SEEDS,
            Column.SEED_COUNT,
            Column.FAMILIES,
            Column.CLIENTS,
        )
        .sort(Column.LEARNER, Column.METRIC, Column.ESTIMAND, Column.EXPERIMENT)
    )


def operating_point_fidelity(summary: SummaryTable) -> FidelityTable:
    return (
        summary.filter(
            pl.col(Column.DOSE).is_null()
            & is_one_of(Column.METRIC, [Metric.REALISED_FPR, Metric.WORST_CLIENT_FPR])
        )
        .group_by(Column.EXPERIMENT, Column.LEARNER, Column.CONDITION, Column.ALPHA)
        .agg(
            pl.col(Column.VALUE)
            .filter(pl.col(Column.METRIC) == Metric.REALISED_FPR)
            .mean()
            .alias(Column.MEAN_FPR),
            pl.col(Column.VALUE)
            .filter(pl.col(Column.METRIC) == Metric.WORST_CLIENT_FPR)
            .mean()
            .alias(Column.WORST_FPR),
            pl.col(Column.SEED).n_unique().alias(Column.RUNS),
            (
                (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.VALID)
                & (pl.col(Column.METRIC) == Metric.REALISED_FPR)
            )
            .sum()
            .alias(Column.VALID_RUNS),
        )
        .with_columns(
            (pl.col(Column.MEAN_FPR) - pl.col(Column.ALPHA)).alias(Column.FPR_DEVIATION),
            pl.lit(EvidenceClass.CONFIRMATORY_SENSITIVITY).alias(Column.EVIDENCE_CLASS),
        )
        .sort(Column.EXPERIMENT, Column.LEARNER, Column.CONDITION, Column.ALPHA)
    )


def _arm_series(
    clients: ClientCountsTable,
    client: ClientId,
    arm: ArmSpec,
    population: EvaluationPopulation,
    alpha: Alpha,
    minimum: SupportCount,
    name: Column,
) -> ArmSeries:
    return (
        clients.filter(
            (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
            & (pl.col(Column.ALPHA) == alpha)
            & (pl.col(Column.CLIENT) == client)
            & (pl.col(Column.LEARNER) == arm.learner)
            & (pl.col(Column.CONDITION) == arm.condition)
            & (pl.col(Column.POPULATION) == population)
            & pl.col(Column.DOSE).is_null()
            & (pl.col(Column.TRIALS) >= max(minimum, 1))
        )
        .select(
            Column.SEED,
            Column.TRIALS,
            (pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(name),
        )
        .sort(Column.SEED)
    )


def _client_change(
    clients: ClientCountsTable,
    client: ClientId,
    learner: Learner,
    population: EvaluationPopulation,
    alpha: Alpha,
    local_name: Column,
    peer_name: Column,
) -> ArmSeries:
    local = _arm_series(
        clients,
        client,
        ArmSpec(learner=Learner.LOCAL, condition=ExposureCondition.PEER_PRESENT),
        population,
        alpha,
        1,
        local_name,
    ).drop(Column.TRIALS)
    peer = _arm_series(
        clients,
        client,
        ArmSpec(learner=learner, condition=ExposureCondition.PEER_PRESENT),
        population,
        alpha,
        1,
        peer_name,
    ).drop(Column.TRIALS)
    return local.join(peer, on=Column.SEED)


def _pair_count(
    families: FamilyCountsTable, client: ClientId, population: EvaluationPopulation, alpha: Alpha
) -> SupportCount:
    return (
        families.filter(
            (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
            & (pl.col(Column.ALPHA) == alpha)
            & (pl.col(Column.CLIENT) == client)
            & (pl.col(Column.POPULATION) == population)
            & (pl.col(Column.LEARNER) == Learner.LOCAL)
            & pl.col(Column.DOSE).is_null()
            & (pl.col(Column.TRIALS) > 0)
        )
        .select(Column.SEED, Column.FAMILY)
        .unique()
        .height
    )


def _client_wide(
    clients: ClientCountsTable,
    client: ClientId,
    learner: Learner,
    population: EvaluationPopulation,
    alpha: Alpha,
    minimum: SupportCount,
) -> ArmSeries:
    def arm(arm_learner: Learner, condition: ExposureCondition, name: Column) -> ArmSeries:
        return _arm_series(
            clients,
            client,
            ArmSpec(learner=arm_learner, condition=condition),
            population,
            alpha,
            minimum,
            name,
        )

    return (
        arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL)
        .join(
            arm(learner, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL).drop(Column.TRIALS),
            on=Column.SEED,
        )
        .join(
            arm(learner, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL).drop(
                Column.TRIALS
            ),
            on=Column.SEED,
        )
        .join(
            arm(learner, ExposureCondition.FULL_EXPOSURE, Column.FULL_RECALL).drop(Column.TRIALS),
            on=Column.SEED,
            how=LibraryOption.JOIN_LEFT,
        )
    )


def _column_mean(frame: ArmSeries, column: Column) -> Effect | None:
    present = frame[column].drop_nulls().to_numpy()
    return present.mean().item() if present.size else None


def _interval(summary: SeedSummary) -> Interval | None:
    if summary.ci_low is None or summary.ci_high is None:
        return None
    return Interval(low=summary.ci_low, high=summary.ci_high)


def _low(interval: Interval | None) -> Effect | None:
    return None if interval is None else interval.low


def _high(interval: Interval | None) -> Effect | None:
    return None if interval is None else interval.high


def _client_ctk_rows(
    clients: ClientCountsTable,
    families: FamilyCountsTable,
    config: Config,
    client: ClientId,
    learner: Learner,
    alpha: Alpha,
    own_minimum: SupportCount,
) -> list[ClientCtkRow]:
    known = _client_change(
        clients,
        client,
        learner,
        EvaluationPopulation.KNOWN_FAMILY,
        alpha,
        Column.KNOWN_LOCAL_RECALL,
        Column.KNOWN_PEER_RECALL,
    )
    benign = _arm_series(
        clients,
        client,
        ArmSpec(learner=learner, condition=ExposureCondition.PEER_PRESENT),
        EvaluationPopulation.BENIGN,
        alpha,
        1,
        Column.BENIGN_FPR,
    )
    known_change = summarize_seeds(
        (known[Column.KNOWN_PEER_RECALL] - known[Column.KNOWN_LOCAL_RECALL]).to_numpy(),
        config.statistics,
    )
    rows: list[ClientCtkRow] = []
    populations = (
        (EvaluationPopulation.FEDERATION_WIDE, 1),
        (EvaluationPopulation.OWN_DOMAIN, own_minimum),
    )
    for population, minimum in populations:
        wide = _client_wide(clients, client, learner, population, alpha, minimum)
        if wide.height == 0:
            continue
        peer = wide[Column.PEER_RECALL].to_numpy()
        absent = wide[Column.ABSENT_RECALL].to_numpy()
        base = wide[Column.LOCAL_RECALL].to_numpy()
        total = summarize_seeds(peer - base, config.statistics)
        pooling = summarize_seeds(absent - base, config.statistics)
        ctk = summarize_seeds(peer - absent, config.statistics)
        if total is None or pooling is None or ctk is None:
            continue
        total_ci, pooling_ci, ctk_ci = _interval(total), _interval(pooling), _interval(ctk)
        known_ci = None if known_change is None else _interval(known_change)
        rows.append(
            ClientCtkRow(
                evidence_class=EvidenceClass.POST_CONFIRMATORY,
                client=client,
                learner=learner,
                alpha=alpha,
                population=population,
                local_recall=base.mean().item(),
                absent_recall=absent.mean().item(),
                peer_recall=peer.mean().item(),
                full_recall=_column_mean(wide, Column.FULL_RECALL),
                total_gain=total.mean_difference,
                total_ci_low=_low(total_ci),
                total_ci_high=_high(total_ci),
                pooling_gain=pooling.mean_difference,
                pooling_ci_low=_low(pooling_ci),
                pooling_ci_high=_high(pooling_ci),
                ctk_gain=ctk.mean_difference,
                ctk_ci_low=_low(ctk_ci),
                ctk_ci_high=_high(ctk_ci),
                ctk_positive_seeds=ctk.positive_seeds,
                known_family_recall_local=_column_mean(known, Column.KNOWN_LOCAL_RECALL),
                known_family_recall_collaborative=_column_mean(known, Column.KNOWN_PEER_RECALL),
                known_family_change=None if known_change is None else known_change.mean_difference,
                known_family_change_ci_low=_low(known_ci),
                known_family_change_ci_high=_high(known_ci),
                realised_fpr=_column_mean(benign, Column.BENIGN_FPR),
                hidden_family_trials_per_seed=_column_mean(wide, Column.TRIALS) or 0.0,
                contributing_seeds=wide.height,
                eligible_pairs=_pair_count(families, client, population, alpha),
                interval_status=IntervalStatus.OMITTED_NOT_COMPUTABLE
                if ctk_ci is None
                else IntervalStatus.EXPLORATORY_BCA,
            )
        )
    return rows


def client_ctk_analysis(
    clients: ClientCountsTable, families: FamilyCountsTable, config: Config
) -> ClientCtkTable:
    alpha = config.experiments.operating.primary_alpha
    own_minimum = config.data.eligibility[EligibilityProfile.PRIMARY].own_domain_min_test
    rows = [
        row
        for client in ClientId
        for learner in (Learner.FEDAVG, Learner.FEDPROX, Learner.CENTRAL)
        for row in _client_ctk_rows(clients, families, config, client, learner, alpha, own_minimum)
    ]
    return _ordered(records_to_frame(rows), Column.CLIENT, Column.POPULATION, Column.LEARNER)


def federated_arms() -> tuple[Learner, ...]:
    return (Learner.FEDAVG, Learner.FEDPROX, Learner.FEDAVG_FINETUNE)


def simple_baselines() -> list[Learner]:
    return [Learner.CENTRAL, *federated_arms(), Learner.BLEND]


def _mean(values: ValueSeries) -> Effect | None:
    present = values.drop_nulls().to_numpy()
    return present.mean().item() if present.size else None


def _effect(
    effects: EffectsTable,
    experiment: ExperimentName,
    learner: Learner,
    estimand: Estimand,
    metric: Metric,
    alpha: Alpha,
) -> EffectRow | None:
    rows = effects.filter(
        (pl.col(Column.EXPERIMENT) == experiment)
        & (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.ESTIMAND) == estimand)
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ALPHA) == alpha)
        & (pl.col(Column.SALT) == 0)
    )
    return EffectRow.model_validate(rows.row(0, named=True)) if rows.height else None


def _passes(row: EffectRow | None, minimum: Effect, positive_seeds: SupportCount) -> Passed:
    return (
        row is not None
        and row.mean_difference >= minimum
        and row.ci_low is not None
        and row.ci_low > 0
        and (row.positive_seeds or 0) >= positive_seeds
    )


def _refuted(row: EffectRow | None, minimum: Effect) -> Refuted:
    return row is not None and row.ci_high is not None and row.ci_high < minimum


def _decide(passed: list[Passed], refuted: list[Refuted]) -> ClaimStatus:
    if passed and all(passed):
        return ClaimStatus.PROMOTED
    if any(passed):
        return ClaimStatus.NARROWED
    if refuted and all(refuted):
        return ClaimStatus.REJECTED
    return ClaimStatus.INSUFFICIENT_EVIDENCE


def _result(
    claim: ClaimName,
    status: ClaimStatus,
    passed: RowCount,
    total: RowCount,
    wording: AllowedWording | None = None,
) -> ClaimResult:
    return ClaimResult(
        claim=claim,
        claim_status=status,
        scopes_passed=passed,
        scopes_total=total,
        wording=AllowedWording[status.name] if wording is None else wording,
    )


def _scoped(
    claim: ClaimName,
    rows: list[EffectRow | None],
    minimum: Effect,
    positive_seeds: SupportCount,
) -> ClaimResult:
    passed = [_passes(row, minimum, positive_seeds) for row in rows]
    refuted = [_refuted(row, minimum) for row in rows]
    return _result(claim, _decide(passed, refuted), sum(passed), len(passed))


def _population_metrics() -> tuple[Metric, ...]:
    return (Metric.FEDERATION_UNSEEN_RECALL, Metric.OWN_DOMAIN_UNSEEN_RECALL)


def local_deficit(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha
    rows = [
        _effect(
            evidence.effects,
            ExperimentName.CONTROLLED_EXPOSURE,
            Learner.CENTRAL,
            Estimand.LOCAL_DEFICIT,
            metric,
            alpha,
        )
        for metric in _population_metrics()
    ]
    return _scoped(
        ClaimName.LOCAL_DEFICIT, rows, gates.local_deficit_min_gap, gates.local_deficit_min_seeds
    )


def collaboration_benefit(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha
    rows = [
        _effect(
            evidence.effects,
            ExperimentName.CONTROLLED_EXPOSURE,
            Learner.FEDAVG,
            Estimand.TOTAL_GAIN,
            metric,
            alpha,
        )
        for metric in _population_metrics()
    ]
    return _scoped(ClaimName.COLLABORATION_BENEFIT, rows, gates.collaboration_min_gain, 0)


def _ctk(
    evidence: GateEvidence, experiment: ExperimentName, metric: Metric, alpha: Alpha
) -> EffectRow | None:
    return _effect(evidence.effects, experiment, Learner.FEDAVG, Estimand.CTK_GAIN, metric, alpha)


def permutation_outcome(row: EffectRow | None, band: Effect) -> PermutationOutcome:
    if row is None or row.ci_low is None or row.ci_high is None:
        return PermutationOutcome.UNRESOLVED
    if row.ci_low >= -band and row.ci_high <= band:
        return PermutationOutcome.EQUIVALENT
    if row.ci_low > band or row.ci_high < -band:
        return PermutationOutcome.EXCEEDS_BAND
    return PermutationOutcome.UNRESOLVED


def complementary_knowledge(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha
    scopes = [
        _ctk(evidence, ExperimentName.CONTROLLED_EXPOSURE, Metric.FEDERATION_UNSEEN_RECALL, alpha),
        _ctk(evidence, ExperimentName.CONTROLLED_EXPOSURE, Metric.OWN_DOMAIN_UNSEEN_RECALL, alpha),
        _ctk(
            evidence, ExperimentName.REPLICATION_FAMILY_SET, Metric.FEDERATION_UNSEEN_RECALL, alpha
        ),
    ]
    permutation = _ctk(
        evidence, ExperimentName.FAMILY_PERMUTATION_CONTROL, Metric.FEDERATION_UNSEEN_RECALL, alpha
    )
    outcome = permutation_outcome(permutation, gates.ctk_min_gain)
    if outcome is PermutationOutcome.EXCEEDS_BAND:
        return _result(ClaimName.COMPLEMENTARY_KNOWLEDGE, ClaimStatus.REJECTED, 0, len(scopes))
    if outcome is PermutationOutcome.UNRESOLVED or evidence.failed_validation_runs:
        return _result(
            ClaimName.COMPLEMENTARY_KNOWLEDGE, ClaimStatus.INSUFFICIENT_EVIDENCE, 0, len(scopes)
        )
    return _scoped(
        ClaimName.COMPLEMENTARY_KNOWLEDGE, scopes, gates.ctk_min_gain, gates.ctk_min_positive_seeds
    )


def generic_pooling_majority(evidence: GateEvidence, config: Config) -> ClaimResult:
    alpha = config.experiments.operating.primary_alpha
    threshold = config.statistics.gates.pooling_majority_share
    rows = [
        _effect(
            evidence.effects,
            ExperimentName.CONTROLLED_EXPOSURE,
            Learner.FEDAVG,
            Estimand.POOLING_SHARE,
            metric,
            alpha,
        )
        for metric in _population_metrics()
    ]
    passed = [row is not None and row.ci_low is not None and row.ci_low > threshold for row in rows]
    refuted = [
        row is not None and row.ci_high is not None and row.ci_high < threshold for row in rows
    ]
    return _result(
        ClaimName.GENERIC_POOLING_MAJORITY, _decide(passed, refuted), sum(passed), len(passed)
    )


def dose_response(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates = config.statistics.gates
    fedavg = evidence.dose.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
    curve = dose_levels(fedavg, gates.dose_min_peers)
    if curve.height < 2:
        return _result(
            ClaimName.DOSE_RESPONSE,
            ClaimStatus.INSUFFICIENT_EVIDENCE,
            0,
            StatisticsLimit.DOSE_CRITERIA,
        )
    recall = curve[Column.RECALL].to_numpy()
    monotone = (np.diff(recall) >= -gates.dose_monotone_tolerance).all().item()
    enough = curve.filter(pl.col(Column.MEETS_DOSE_CRITERION))
    gain = enough[Column.CTK_GAIN].to_numpy().max().item() if enough.height else None
    improves = gain is not None and gain >= gates.dose_min_gain
    family_gains = (
        with_level_exposure(fedavg)
        .filter(pl.col(Column.LEVEL_EFFECTIVE_DOSE) >= gates.dose_min_peers)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.CTK_GAIN).mean())
    )
    not_one_family = family_gains.height > 1 and all(
        _without(family_gains, family) >= gates.dose_min_gain
        for family in family_gains[Column.FAMILY]
    )
    passed = [monotone, improves, not_one_family]
    status = ClaimStatus.NARROWED
    if all(passed):
        status = ClaimStatus.PROMOTED
    elif not any(passed):
        status = ClaimStatus.REJECTED
    return _result(ClaimName.DOSE_RESPONSE, status, sum(passed), len(passed))


def _without(gains: FamilyGainsTable, family: FamilyName) -> Fraction:
    return _mean(gains.filter(pl.col(Column.FAMILY) != family)[Column.CTK_GAIN]) or 0.0


def own_domain_benefit(evidence: GateEvidence, config: Config) -> ClaimResult:
    alpha = config.experiments.operating.primary_alpha
    row = _ctk(evidence, ExperimentName.CONTROLLED_EXPOSURE, Metric.OWN_DOMAIN_UNSEEN_RECALL, alpha)
    return _scoped(ClaimName.OWN_DOMAIN_BENEFIT, [row], 0.0, 0)


def worst_client_benefit(evidence: GateEvidence, config: Config) -> ClaimResult:
    alpha = config.experiments.operating.primary_alpha
    row = _ctk(
        evidence, ExperimentName.CONTROLLED_EXPOSURE, Metric.WORST_CLIENT_UNSEEN_RECALL, alpha
    )
    return _scoped(ClaimName.WORST_CLIENT_BENEFIT, [row], 0.0, 0)


def _seed_means(
    summary: SummaryTable, learner: Learner, metric: Metric, alpha: Alpha
) -> SeedMeansTable:
    return summary.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ALPHA) == alpha)
    ).select(Column.SEED, Column.VALUE)


def known_family_safety(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha
    recalls = {
        learner: _mean(
            _seed_means(evidence.summary, learner, Metric.FEDERATION_UNSEEN_RECALL, alpha)[
                Column.VALUE
            ]
        )
        for learner in federated_arms()
    }
    measured = {learner: value for learner, value in recalls.items() if value is not None}
    if not measured:
        return _result(ClaimName.KNOWN_FAMILY_SAFETY, ClaimStatus.INSUFFICIENT_EVIDENCE, 0, 2)
    strongest = max(measured, key=lambda learner: measured[learner])

    def shift(metric: Metric) -> Effect | None:
        arm = _seed_means(evidence.summary, strongest, metric, alpha)
        local = _seed_means(evidence.summary, Learner.LOCAL, metric, alpha)
        joined = arm.join(local.rename({Column.VALUE: Column.LOCAL_RECALL}), on=Column.SEED)
        return _mean(joined[Column.VALUE] - joined[Column.LOCAL_RECALL])

    recall_shift, fpr_shift = shift(Metric.KNOWN_FAMILY_RECALL), shift(Metric.REALISED_FPR)
    if recall_shift is None or fpr_shift is None:
        return _result(ClaimName.KNOWN_FAMILY_SAFETY, ClaimStatus.INSUFFICIENT_EVIDENCE, 0, 2)
    passed = [abs(recall_shift) <= gates.known_family_tolerance, fpr_shift <= gates.fpr_tolerance]
    status = ClaimStatus.PROMOTED if all(passed) else ClaimStatus.REJECTED
    return _result(
        ClaimName.KNOWN_FAMILY_SAFETY,
        status,
        sum(passed),
        len(passed),
        AllowedWording.STRONGEST_ARM_ONLY if status is ClaimStatus.PROMOTED else None,
    )


def frozen_family_set_experiments() -> tuple[ExperimentName, ...]:
    return (ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET)


def family_dependence(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates = config.statistics.gates
    per_family = (
        evidence.family_seed.filter(
            (pl.col(Column.LEARNER) == Learner.FEDAVG)
            & is_one_of(Column.EXPERIMENT, list(frozen_family_set_experiments()))
        )
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.CTK_GAIN).mean())
    )
    if per_family.height < 2:
        return _result(ClaimName.FAMILY_DEPENDENCE, ClaimStatus.INSUFFICIENT_EVIDENCE, 0, 1)
    gains = per_family[Column.CTK_GAIN].to_numpy()
    spread = gains.max() - gains.min()
    heterogeneous = spread >= gates.heterogeneity_min
    status = ClaimStatus.PROMOTED if heterogeneous else ClaimStatus.REJECTED
    return _result(ClaimName.FAMILY_DEPENDENCE, status, 1 if heterogeneous else 0, 1)


def representation_limited_family(evidence: GateEvidence, config: Config) -> ClaimResult:
    poor = config.statistics.gates.poor_full_recall

    def poor_families(experiment: ExperimentName, learner: Learner) -> set[FamilyName]:
        table = evidence.family_effects.filter(
            (pl.col(Column.EXPERIMENT) == experiment)
            & (pl.col(Column.LEARNER) == learner)
            & (pl.col(Column.FULL_RECALL) < poor)
        )
        return set(table[Column.FAMILY].to_list())

    primary = poor_families(ExperimentName.CONTROLLED_EXPOSURE, Learner.CENTRAL)
    independent = poor_families(
        ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR, Learner.CENTRAL
    ) | poor_families(ExperimentName.MODEL_FAMILY_REPLICATION_TREES, Learner.CENTRAL)
    qualifying = primary & independent
    status = ClaimStatus.PROMOTED if qualifying else ClaimStatus.REJECTED
    partial = status is ClaimStatus.PROMOTED and len(qualifying) < len(primary)
    return _result(
        ClaimName.REPRESENTATION_LIMITED_FAMILY,
        status,
        len(qualifying),
        len(primary),
        AllowedWording.NARROWED if partial else None,
    )


def feature_novelty_explanation(evidence: GateEvidence, config: Config) -> ClaimResult:
    minimum = config.statistics.gates.novelty_min_abs_spearman
    outcomes: list[Passed] = []
    directions: set[Positive] = set()
    for experiment in (ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET):
        association = evidence.associations.get(experiment)
        if association is None or association.interval is None:
            outcomes.append(False)
            continue
        excludes_zero = association.interval.low > 0 or association.interval.high < 0
        outcomes.append(abs(association.rho) >= minimum and excludes_zero)
        directions.add(association.rho > 0)
    consistent = len(directions) <= 1
    passed = [outcome and consistent for outcome in outcomes]
    resolved = all(
        evidence.associations.get(experiment) is not None for experiment in evidence.associations
    )
    status = _decide(passed, [not outcome and resolved for outcome in outcomes])
    return _result(ClaimName.FEATURE_NOVELTY_EXPLANATION, status, sum(passed), len(passed))


def new_mechanism_trigger(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates, alpha = config.statistics.gates, config.experiments.operating.primary_alpha

    def best_gap(metric: Metric) -> Effect | None:
        full = _mean(
            evidence.summary.filter(
                (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
                & (pl.col(Column.LEARNER) == Learner.CENTRAL)
                & (pl.col(Column.CONDITION) == ExposureCondition.FULL_EXPOSURE)
                & (pl.col(Column.METRIC) == metric)
                & (pl.col(Column.ALPHA) == alpha)
            )[Column.VALUE]
        )
        baselines = [
            _mean(_seed_means(evidence.summary, learner, metric, alpha)[Column.VALUE])
            for learner in simple_baselines()
        ]
        measured = [value for value in baselines if value is not None]
        return None if full is None or not measured else full - max(measured)

    mean_gap, worst_gap = (
        best_gap(Metric.FEDERATION_UNSEEN_RECALL),
        best_gap(Metric.WORST_CLIENT_UNSEEN_RECALL),
    )
    if mean_gap is None or worst_gap is None:
        return _result(ClaimName.NEW_MECHANISM_TRIGGER, ClaimStatus.INSUFFICIENT_EVIDENCE, 0, 2)
    headroom = mean_gap > gates.mechanism_mean_gap or worst_gap > gates.mechanism_worst_gap
    status = ClaimStatus.INSUFFICIENT_EVIDENCE if headroom else ClaimStatus.REJECTED
    return _result(ClaimName.NEW_MECHANISM_TRIGGER, status, 1 if headroom else 0, 2)


def evaluate_claims(evidence: GateEvidence, config: Config) -> ClaimsTable:
    return records_to_frame(
        [
            local_deficit(evidence, config),
            collaboration_benefit(evidence, config),
            complementary_knowledge(evidence, config),
            generic_pooling_majority(evidence, config),
            dose_response(evidence, config),
            own_domain_benefit(evidence, config),
            worst_client_benefit(evidence, config),
            known_family_safety(evidence, config),
            family_dependence(evidence, config),
            representation_limited_family(evidence, config),
            feature_novelty_explanation(evidence, config),
            new_mechanism_trigger(evidence, config),
        ]
    )


def top_support_families(families: FamilyCountsTable, count: SupportCount) -> list[FamilyName]:
    ranked = (
        families.filter(pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.TRIALS).mean())
        .sort([Column.TRIALS, Column.FAMILY], descending=[True, False])
    )
    return ranked[Column.FAMILY].head(count).to_list()


def micro_ctk_by_seed(
    families: FamilyCountsTable,
    alpha: Alpha,
    excluded: list[FamilyName],
    hits: Column = Column.HITS,
    trials: Column = Column.TRIALS,
) -> MicroGainTable:
    def pooled(condition: ExposureCondition, name: Column) -> PooledRecallTable:
        return (
            families.filter(
                (pl.col(Column.LEARNER) == Learner.FEDAVG)
                & (pl.col(Column.CONDITION) == condition)
                & pl.col(Column.DOSE).is_null()
                & (pl.col(Column.ALPHA) == alpha)
                & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
                & ~is_one_of(Column.FAMILY, excluded)
            )
            .group_by(Column.EXPERIMENT, Column.SEED, Column.SALT)
            .agg((pl.col(hits).sum() / pl.col(trials).sum()).alias(name))
        )

    return (
        pooled(ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            pooled(ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL),
            on=[Column.EXPERIMENT, Column.SEED, Column.SALT],
        )
        .with_columns(
            (pl.col(Column.PEER_RECALL) - pl.col(Column.ABSENT_RECALL)).alias(
                Column.MICRO_POOLED_CTK_GAIN
            )
        )
    )


def robustness_table(families: FamilyCountsTable, config: Config) -> RobustnessTable:
    alpha = config.experiments.operating.primary_alpha
    removed = top_support_families(families, config.experiments.top_family_removal_count)
    rows: list[RobustnessRow] = []
    for sensitivity, excluded, hits, trials in (
        (Sensitivity.ALL_FAMILIES, [], Column.HITS, Column.TRIALS),
        (Sensitivity.TOP_FAMILY_REMOVAL, removed, Column.HITS, Column.TRIALS),
        (Sensitivity.DEDUPLICATED_TEST, [], Column.UNIQUE_HITS, Column.UNIQUE_TRIALS),
    ):
        gains = micro_ctk_by_seed(families, alpha, excluded, hits, trials)
        for group in gains.sort(Column.SEED).partition_by(Column.EXPERIMENT, Column.SALT):
            head = group.row(0, named=True)
            effect = paired_effect(
                group[Column.MICRO_POOLED_CTK_GAIN].to_numpy(), config.statistics
            )
            rows.append(
                RobustnessRow(
                    experiment=head[Column.EXPERIMENT],
                    salt=head[Column.SALT],
                    alpha=alpha,
                    sensitivity=sensitivity,
                    aggregation=CtkAggregation.MICRO_POOLED,
                    micro_pooled_ctk_gain=effect.mean,
                    median_difference=effect.median,
                    ci_low=effect.interval.low if effect.interval else None,
                    ci_high=effect.interval.high if effect.interval else None,
                    positive_seeds=effect.positive_seeds,
                    seed_count=effect.seeds,
                )
            )
    return records_to_frame(rows).sort(Column.EXPERIMENT, Column.SALT, Column.SENSITIVITY)


def select_hyperparameters(summary: SummaryTable, alpha: Alpha) -> SelectionTable:
    grid = summary.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.BASELINE_FAIRNESS)
        & (pl.col(Column.METRIC) == Metric.CALIBRATION_AUROC)
        & (pl.col(Column.ALPHA) == alpha)
        & pl.col(Column.PARAMETER).is_not_null()
    )
    per_value = (
        grid.group_by(Column.PARAMETER, Column.TUNING_VALUE)
        .agg(
            pl.col(Column.VALUE).mean().alias(Column.CALIBRATION_AUROC),
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
        )
        .sort(
            [Column.PARAMETER, Column.CALIBRATION_AUROC, Column.TUNING_VALUE],
            descending=[False, True, False],
        )
    )
    return per_value.with_columns(
        (pl.int_range(pl.len()).over(Column.PARAMETER) == 0).alias(Column.SELECTED)
    )


def selected_value(selection: SelectionTable, parameter: TunedParameter) -> TuningValue:
    chosen = selection.filter((pl.col(Column.PARAMETER) == parameter) & pl.col(Column.SELECTED))
    return chosen[Column.TUNING_VALUE].item()


def frozen_hyperparameters(selection: SelectionTable) -> FrozenHyperparameters:
    return FrozenHyperparameters(
        local_epochs=selected_value(selection, TunedParameter.LOCAL_EPOCHS),
        finetune_epochs=selected_value(selection, TunedParameter.FINETUNE_EPOCHS),
        fedprox_mu=selected_value(selection, TunedParameter.FEDPROX_STRENGTH),
    )


def frozen_drift(selection: SelectionTable, training: TrainingConfig) -> list[TunedParameter]:
    chosen = frozen_hyperparameters(selection)
    configured = {
        TunedParameter.LOCAL_EPOCHS: (chosen.local_epochs, training.local_epochs),
        TunedParameter.FINETUNE_EPOCHS: (chosen.finetune_epochs, training.finetune_epochs),
        TunedParameter.FEDPROX_STRENGTH: (chosen.fedprox_mu, training.fedprox_mu),
    }
    return [parameter for parameter, (found, frozen) in configured.items() if found != frozen]


def _variance_rows(
    experiment: ExperimentName, learner: Learner, matrix: SeedMatrix
) -> list[VarianceRow]:
    families, seeds = matrix.shape
    grand = matrix.mean()
    total = ((matrix - grand) ** 2).sum()
    by_family = seeds * ((matrix.mean(axis=1) - grand) ** 2).sum()
    by_seed = families * ((matrix.mean(axis=0) - grand) ** 2).sum()
    parts = (
        (VarianceSource.FAMILY, by_family, families - 1),
        (VarianceSource.SEED, by_seed, seeds - 1),
        (VarianceSource.RESIDUAL, total - by_family - by_seed, (families - 1) * (seeds - 1)),
    )
    return [
        VarianceRow(
            evidence_class=EvidenceClass.POST_CONFIRMATORY,
            experiment=experiment,
            learner=learner,
            source=source,
            sum_squares=np.maximum(squares, 0.0).item(),
            degrees_of_freedom=degrees,
            share=np.maximum(squares, 0.0).item() / total.item() if total > 0 else 0.0,
        )
        for source, squares, degrees in parts
    ]


def _mean_or_zero(values: SeedEffects) -> Effect:
    return values.mean().item() if values.size else 0.0


def ctk_variance_components(family_seed: FamilySeedTable) -> VarianceTable:
    rows: list[VarianceRow] = []
    for experiment in frozen_family_set_experiments():
        per_pair = (
            family_seed.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.LEARNER) == Learner.FEDAVG)
            )
            .group_by(Column.FAMILY, Column.SEED)
            .agg(pl.col(Column.CTK_GAIN).mean())
        )
        if per_pair.height == 0:
            continue
        wide = per_pair.pivot(on=Column.SEED, index=Column.FAMILY, values=Column.CTK_GAIN)
        complete = wide.drop_nulls()
        if complete.height < 2 or complete.width <= 2:
            continue
        matrix = complete.drop(Column.FAMILY).to_numpy().astype(np.float64)
        rows.extend(_variance_rows(experiment, Learner.FEDAVG, matrix))
    return records_to_frame(rows)


def family_associations(family_effects: FamilyEffectsTable) -> AssociationTable:
    rows: list[FamilyAssociationRow] = []
    for experiment in frozen_family_set_experiments():
        fedavg = family_effects.filter(
            (pl.col(Column.EXPERIMENT) == experiment) & (pl.col(Column.LEARNER) == Learner.FEDAVG)
        )
        if fedavg.height < StatisticsLimit.ASSOCIATION_FAMILIES:
            continue
        local = fedavg[Column.LOCAL_RECALL].to_numpy()
        pooling = (fedavg[Column.ABSENT_RECALL] - fedavg[Column.LOCAL_RECALL]).to_numpy()
        total = (fedavg[Column.PEER_RECALL] - fedavg[Column.LOCAL_RECALL]).to_numpy()
        ctk = fedavg[Column.CTK_GAIN].to_numpy()
        for predictor, x in (
            (FamilyPredictor.LOCAL_RECALL, local),
            (FamilyPredictor.POOLING_GAIN, pooling),
        ):
            for outcome, y in (
                (FamilyOutcomeMeasure.CTK_GAIN, ctk),
                (FamilyOutcomeMeasure.TOTAL_GAIN, total),
            ):
                result = stats.spearmanr(x, y)
                if not np.isfinite(result.statistic):
                    continue
                rows.append(
                    FamilyAssociationRow(
                        evidence_class=EvidenceClass.POST_CONFIRMATORY,
                        experiment=experiment,
                        predictor=predictor,
                        outcome_measure=outcome,
                        rho=result.statistic.item(),
                        p_value=result.pvalue.item(),
                        families=fedavg.height,
                    )
                )
    return records_to_frame(rows)


def family_client_ctk(families: FamilyCountsTable, config: Config) -> FamilyClientTable:
    alpha = config.experiments.operating.primary_alpha
    own = families.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.ALPHA) == alpha)
        & (pl.col(Column.POPULATION) == EvaluationPopulation.OWN_DOMAIN)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.TRIALS) > 0)
        & is_one_of(Column.LEARNER, [Learner.LOCAL, Learner.FEDAVG])
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    if own.height == 0:
        return pl.DataFrame()

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> FamilyClientTable:
        return own.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(
            Column.SEED,
            Column.CLIENT,
            Column.FAMILY,
            pl.col(Column.RECALL).alias(name),
            pl.col(Column.TRIALS),
        )

    keys = [Column.SEED, Column.CLIENT, Column.FAMILY]
    wide = (
        arm(Learner.FEDAVG, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            arm(
                Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL
            ).drop(Column.TRIALS),
            on=keys,
        )
        .join(
            arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL).drop(
                Column.TRIALS
            ),
            on=keys,
            how=LibraryOption.JOIN_LEFT,
        )
        .sort(Column.SEED)
    )
    rows: list[FamilyClientRow] = []
    for group in wide.partition_by(Column.CLIENT, Column.FAMILY):
        head = group.row(0, named=True)
        peer = group[Column.PEER_RECALL].to_numpy()
        absent = group[Column.ABSENT_RECALL].to_numpy()
        summary = summarize_seeds(peer - absent, config.statistics)
        if summary is None:
            continue
        rows.append(
            FamilyClientRow(
                evidence_class=EvidenceClass.POST_CONFIRMATORY,
                experiment=ExperimentName.CONTROLLED_EXPOSURE,
                client=head[Column.CLIENT],
                family=head[Column.FAMILY],
                local_recall=_mean_or_zero(group[Column.LOCAL_RECALL].drop_nulls().to_numpy()),
                absent_recall=absent.mean().item(),
                peer_recall=peer.mean().item(),
                hidden_trials_per_seed=_mean_or_zero(group[Column.TRIALS].to_numpy()),
                **summary.model_dump(),
            )
        )
    return records_to_frame(rows).sort(Column.CLIENT, Column.FAMILY) if rows else pl.DataFrame()


def hidden_populations() -> tuple[EvaluationPopulation, ...]:
    return (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE)


def variance_components() -> tuple[VarianceComponent, ...]:
    return (
        VarianceComponent.FAMILY,
        VarianceComponent.CLIENT,
        VarianceComponent.FAMILY_BY_CLIENT,
        VarianceComponent.SEED,
        VarianceComponent.RESIDUAL,
    )


def transfer_scopes() -> tuple[TransferScopeSpec, ...]:
    return (
        TransferScopeSpec(scope=TransferScope.CELL, keys=(Column.CLIENT, Column.FAMILY)),
        TransferScopeSpec(scope=TransferScope.FAMILY, keys=(Column.FAMILY,)),
        TransferScopeSpec(scope=TransferScope.CLIENT, keys=(Column.CLIENT,)),
        TransferScopeSpec(scope=TransferScope.OVERALL, keys=()),
    )


def masking_arms() -> tuple[Learner, ...]:
    return (*federated_arms(), Learner.BLEND)


def masking_aggregates() -> tuple[Metric, ...]:
    return (Metric.AUROC, Metric.AUPRC)


def masking_recalls() -> tuple[Metric, ...]:
    return (Metric.OWN_DOMAIN_UNSEEN_RECALL, Metric.FEDERATION_UNSEEN_RECALL)


def hidden_cells(families: FamilyCountsTable, alpha: Alpha) -> CellTable:
    keys = [
        Column.EXPERIMENT,
        Column.SEED,
        Column.SALT,
        Column.POPULATION,
        Column.CLIENT,
        Column.FAMILY,
    ]
    recalls = families.filter(
        is_one_of(Column.EXPERIMENT, list(frozen_family_set_experiments()))
        & is_one_of(Column.POPULATION, list(hidden_populations()))
        & is_one_of(Column.LEARNER, [Learner.LOCAL, Learner.FEDAVG])
        & (pl.col(Column.ALPHA) == alpha)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.TRIALS) > 0)
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> CellTable:
        return recalls.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(*keys, pl.col(Column.RECALL).alias(name), Column.TRIALS)

    peer = pl.col(Column.PEER_RECALL)
    absent = pl.col(Column.ABSENT_RECALL)
    local = pl.col(Column.LOCAL_RECALL)
    wide = (
        arm(Learner.FEDAVG, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            arm(
                Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL
            ).drop(Column.TRIALS),
            on=keys,
        )
        .join(
            arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL).drop(
                Column.TRIALS
            ),
            on=keys,
        )
        .with_columns(
            (absent - local).alias(Column.POOLING_GAIN),
            (peer - local).alias(Column.TOTAL_GAIN),
            (peer - absent).alias(Column.CTK_GAIN),
        )
    )
    gain = pl.max_horizontal(pl.col(Column.CTK_GAIN), pl.lit(0))
    repair = pl.min_horizontal(gain, pl.max_horizontal(-pl.col(Column.POOLING_GAIN), pl.lit(0)))
    return (
        wide.with_columns(repair.alias(Column.REPAIR))
        .with_columns(
            (gain - pl.col(Column.REPAIR)).alias(Column.NEW_CAPABILITY),
            pl.min_horizontal(pl.col(Column.CTK_GAIN), pl.lit(0)).alias(Column.CTK_HARM),
        )
        .sort(*keys)
    )


def _codes(labels: ValueSeries) -> GroupCodes:
    return np.unique(labels.to_numpy(), return_inverse=True)[1].reshape(-1).astype(np.int64)


def _pair_codes(first: GroupCodes, second: GroupCodes) -> GroupCodes:
    stacked = np.stack([first, second], axis=1)
    return np.unique(stacked, axis=0, return_inverse=True)[1].reshape(-1).astype(np.int64)


def _design(cells: CellTable) -> RandomEffectsDesign:
    family = _codes(cells[Column.FAMILY])
    client = _codes(cells[Column.CLIENT])
    return RandomEffectsDesign(
        response=cells[Column.CTK_GAIN].to_numpy().astype(np.float64),
        factors=(family, client, _pair_codes(family, client), _codes(cells[Column.SEED])),
    )


def _reml_deviance(
    variances: VarianceVector, response: SeedEffects, grams: list[SeedEffects]
) -> DevianceAndGradient:
    covariance = sum(
        (weight * gram for weight, gram in zip(variances, grams, strict=True)),
        np.eye(response.size) * Tolerance.VARIANCE_FLOOR,
    )
    factor = linalg.cho_factor(covariance, lower=True)
    inverse = linalg.cho_solve(factor, np.eye(response.size))
    inverse_ones = inverse.sum(axis=1)
    total = inverse_ones.sum()
    projection = inverse - np.outer(inverse_ones, inverse_ones) / total
    projected = projection @ response
    deviance = 2 * np.log(np.diag(factor[0])).sum() + np.log(total) + response @ projected
    gradient = np.array(
        [(projection * gram).sum() - projected @ gram @ projected for gram in grams]
    )
    return deviance.item(), gradient


def _reml(design: RandomEffectsDesign, warm: VarianceVector | None) -> VarianceEstimate:
    centred = design.response - design.response.mean()
    scale = centred.var().item()
    count = len(design.factors) + 1
    if scale <= 0:
        return VarianceEstimate(variances=np.zeros(count), converged=True)
    response = centred / np.sqrt(scale)
    grams = [(codes[:, None] == codes[None, :]).astype(np.float64) for codes in design.factors]
    grams.append(np.eye(response.size))
    starts = (
        (np.full(count, 1 / count), np.append(np.full(count - 1, 0.5 / count), 0.5))
        if warm is None
        else (np.maximum(warm, Tolerance.WARM_START_FLOOR),)
    )
    fits = [
        optimize.minimize(
            _reml_deviance,
            start,
            args=(response, grams),
            jac=True,
            method=LibraryOption.LBFGSB,
            bounds=optimize.Bounds(0, np.inf),
        )
        for start in starts
    ]
    best = min(fits, key=lambda fit: fit.fun)
    return VarianceEstimate(variances=best.x * scale, converged=best.success)


def _shares(estimate: VarianceEstimate) -> VarianceVector:
    total = estimate.variances.sum()
    return estimate.variances / total if total > 0 else np.zeros(estimate.variances.size)


def _resampled(design: RandomEffectsDesign, rng: np.random.Generator) -> RandomEffectsDesign:
    seed_codes = design.factors[-1]
    draws = rng.choice(np.unique(seed_codes), size=np.unique(seed_codes).size)
    rows: list[GroupCodes] = [np.flatnonzero(seed_codes == draw) for draw in draws]
    relabelled = np.concatenate([np.full(part.size, index) for index, part in enumerate(rows)])
    chosen = np.concatenate(rows)
    return RandomEffectsDesign(
        response=design.response[chosen],
        factors=(*(codes[chosen] for codes in design.factors[:-1]), relabelled.astype(np.int64)),
    )


def _share_interval(
    design: RandomEffectsDesign,
    warm: VarianceVector,
    resamples: ResampleCount,
    seed: RowCount,
    level: Confidence,
) -> list[Interval]:
    rng = np.random.default_rng(seed)
    with threadpool_limits(limits=1):
        draws = np.stack([_shares(_reml(_resampled(design, rng), warm)) for _ in range(resamples)])
    low, high = np.quantile(draws, [(1 - level) / 2, (1 + level) / 2], axis=0)
    return [
        Interval(low=lower.item(), high=upper.item())
        for lower, upper in zip(low, high, strict=True)
    ]


def _sampling_noise(cells: CellTable) -> Effect:
    peer = cells[Column.PEER_RECALL].to_numpy()
    absent = cells[Column.ABSENT_RECALL].to_numpy()
    trials = cells[Column.TRIALS].to_numpy()
    return ((peer * (1 - peer) + absent * (1 - absent)) / trials).mean().item()


def ctk_heterogeneity_components(cells: CellTable, config: Config) -> HeterogeneityTable:
    rows: list[HeterogeneityRow] = []
    for experiment in frozen_family_set_experiments():
        for population in hidden_populations():
            scoped = cells.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.POPULATION) == population)
            )
            if scoped.height == 0 or scoped[Column.SEED].n_unique() < StatisticsLimit.BCA_SEEDS:
                continue
            design = _design(scoped)
            with threadpool_limits(limits=1):
                estimate = _reml(design, None)
            shares = _shares(estimate)
            intervals = _share_interval(
                design,
                shares,
                config.statistics.cluster_bootstrap_resamples,
                config.statistics.statistics_seed,
                config.statistics.confidence_level,
            )
            pair_sizes = np.bincount(design.factors[2])
            for index, component in enumerate(variance_components()):
                interval = intervals[index]
                rows.append(
                    HeterogeneityRow(
                        evidence_class=EvidenceClass.POST_CONFIRMATORY,
                        experiment=experiment,
                        population=population,
                        component=component,
                        variance=estimate.variances[index].item(),
                        share=shares[index].item(),
                        share_ci_low=interval.low,
                        share_ci_high=interval.high,
                        observations=scoped.height,
                        cells=pair_sizes.size,
                        replicated_cells=(pair_sizes > 1).sum().item(),
                        seeds=scoped[Column.SEED].n_unique(),
                        families=scoped[Column.FAMILY].n_unique(),
                        clients=scoped[Column.CLIENT].n_unique(),
                        sampling_noise_reference=_sampling_noise(scoped),
                        converged=estimate.converged,
                        bootstrap_resamples=config.statistics.cluster_bootstrap_resamples,
                    )
                )
    return records_to_frame(rows)


def _verdict(interval: Interval | None, reference: Effect) -> IntervalVerdict:
    if interval is None:
        return IntervalVerdict.INCONCLUSIVE
    if interval.low > reference:
        return IntervalVerdict.POSITIVE
    if interval.high < reference:
        return IntervalVerdict.NEGATIVE
    return IntervalVerdict.INCONCLUSIVE


def _metric_by_seed(
    summary: SummaryTable,
    experiment: ExperimentName,
    arm: ArmSpec,
    metric: Metric,
    alpha: Alpha,
    name: Column,
) -> Table:
    return summary.filter(
        (pl.col(Column.EXPERIMENT) == experiment)
        & (pl.col(Column.LEARNER) == arm.learner)
        & (pl.col(Column.CONDITION) == arm.condition)
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ALPHA) == alpha)
        & (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.VALID)
        & pl.col(Column.DOSE).is_null()
        & pl.col(Column.VALUE).is_finite()
    ).select(Column.SEED, pl.col(Column.VALUE).alias(name))


def _seed_difference(
    summary: SummaryTable,
    experiment: ExperimentName,
    arms: ArmPair,
    metric: Metric,
    alpha: Alpha,
) -> Table:
    minuend = _metric_by_seed(summary, experiment, arms.minuend, metric, alpha, Column.MINUEND)
    subtrahend = _metric_by_seed(
        summary, experiment, arms.subtrahend, metric, alpha, Column.SUBTRAHEND
    )
    return minuend.join(subtrahend, on=Column.SEED).select(
        Column.SEED, (pl.col(Column.MINUEND) - pl.col(Column.SUBTRAHEND)).alias(Column.DIFFERENCE)
    )


def _opposed(first: IntervalVerdict, second: IntervalVerdict) -> Passed:
    return {first, second} == {IntervalVerdict.POSITIVE, IntervalVerdict.NEGATIVE}


def _seed_correlation(aggregate: SeedEffects, recall: SeedEffects) -> Correlation | None:
    if aggregate.size < StatisticsLimit.BCA_SEEDS or np.ptp(aggregate) == 0 or np.ptp(recall) == 0:
        return None
    return np.corrcoef(aggregate, recall)[0, 1].item()


def _masking_row(
    experiment: ExperimentName,
    learner: Learner,
    contrast: MaskingContrast,
    metrics: MetricPair,
    aggregate_differences: Table,
    recall_differences: Table,
    config: Config,
) -> MaskingRow | None:
    paired = aggregate_differences.join(
        recall_differences, on=Column.SEED, suffix=Column.SUBTRAHEND
    )
    if paired.height == 0:
        return None
    aggregate = paired[Column.DIFFERENCE].to_numpy()
    recall = paired[f"{Column.DIFFERENCE}{Column.SUBTRAHEND}"].to_numpy()
    aggregate_effect = paired_effect(aggregate, config.statistics)
    recall_effect = paired_effect(recall, config.statistics)
    threshold = config.statistics.gates.ctk_min_gain
    aggregate_verdict = _verdict(aggregate_effect.interval, 0)
    recall_verdict = _verdict(recall_effect.interval, 0)
    missed = ((recall >= threshold) & (aggregate <= 0)).sum().item()
    reassured = ((recall <= -threshold) & (aggregate >= 0)).sum().item()
    low = recall_effect.interval.low if recall_effect.interval else None
    high = recall_effect.interval.high if recall_effect.interval else None
    return MaskingRow(
        evidence_class=EvidenceClass.POST_CONFIRMATORY,
        experiment=experiment,
        learner=learner,
        contrast=contrast,
        aggregate_metric=metrics.aggregate,
        recall_metric=metrics.recall,
        seed_count=paired.height,
        aggregate_mean=aggregate_effect.mean,
        aggregate_ci_low=aggregate_effect.interval.low if aggregate_effect.interval else None,
        aggregate_ci_high=aggregate_effect.interval.high if aggregate_effect.interval else None,
        aggregate_verdict=aggregate_verdict,
        recall_mean=recall_effect.mean,
        recall_ci_low=low,
        recall_ci_high=high,
        recall_verdict=recall_verdict,
        material_gain_threshold=threshold,
        verdicts_opposed=_opposed(aggregate_verdict, recall_verdict),
        masked_gain=low is not None
        and low > threshold
        and aggregate_verdict is not IntervalVerdict.POSITIVE,
        masked_loss=high is not None
        and high < -threshold
        and aggregate_verdict is not IntervalVerdict.NEGATIVE,
        sign_disagreement_seeds=(np.sign(aggregate) * np.sign(recall) < 0).sum().item(),
        gain_missed_seeds=missed,
        false_reassurance_seeds=reassured,
        opposite_conclusion_seeds=missed + reassured,
        seed_correlation=_seed_correlation(aggregate, recall),
    )


def aggregate_metric_masking(summary: SummaryTable, config: Config) -> MaskingTable:
    alpha = config.experiments.operating.primary_alpha
    rows: list[MaskingRow] = []
    for experiment in frozen_family_set_experiments():
        for learner in masking_arms():
            rows.extend(_masking_rows_for_learner(summary, experiment, learner, alpha, config))
    return records_to_frame(rows)


def _masking_rows_for_learner(
    summary: SummaryTable,
    experiment: ExperimentName,
    learner: Learner,
    alpha: Alpha,
    config: Config,
) -> list[MaskingRow]:
    peer = ExposureCondition.PEER_PRESENT
    present = ArmSpec(learner=learner, condition=peer)
    contrasts = (
        ContrastSpec(
            contrast=MaskingContrast.PEER_VERSUS_LOCAL,
            arms=ArmPair(
                minuend=present, subtrahend=ArmSpec(learner=Learner.LOCAL, condition=peer)
            ),
        ),
        ContrastSpec(
            contrast=MaskingContrast.PEER_VERSUS_FAMILY_ABSENT,
            arms=ArmPair(
                minuend=present,
                subtrahend=ArmSpec(
                    learner=learner, condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE
                ),
            ),
        ),
    )
    return [
        row
        for spec in contrasts
        for aggregate in masking_aggregates()
        for recall in masking_recalls()
        if (
            row := _masking_row(
                experiment,
                learner,
                spec.contrast,
                MetricPair(aggregate=aggregate, recall=recall),
                _seed_difference(summary, experiment, spec.arms, aggregate, alpha),
                _seed_difference(summary, experiment, spec.arms, recall, alpha),
                config,
            )
        )
        is not None
    ]


def _transfer_row(
    experiment: ExperimentName,
    population: EvaluationPopulation,
    spec: TransferScopeSpec,
    group: CellTable,
    config: Config,
) -> TransferRow | None:
    per_seed = group.group_by(Column.SEED, maintain_order=True).agg(
        pl.col(Column.POOLING_GAIN).mean(),
        pl.col(Column.CTK_GAIN).mean(),
        pl.col(Column.REPAIR).mean(),
        pl.col(Column.NEW_CAPABILITY).mean(),
        pl.col(Column.CTK_HARM).mean(),
    )

    def summary(column: Column) -> SeedSummary | None:
        return summarize_seeds(per_seed[column].to_numpy(), config.statistics)

    pooling = summary(Column.POOLING_GAIN)
    ctk = summary(Column.CTK_GAIN)
    repair = summary(Column.REPAIR)
    new = summary(Column.NEW_CAPABILITY)
    harm = summary(Column.CTK_HARM)
    if pooling is None or ctk is None or repair is None or new is None or harm is None:
        return None
    head = group.row(0, named=True)
    gross = repair.mean_difference + new.mean_difference
    return TransferRow(
        evidence_class=EvidenceClass.POST_CONFIRMATORY,
        experiment=experiment,
        population=population,
        scope=spec.scope,
        client=head[Column.CLIENT] if Column.CLIENT in spec.keys else None,
        family=head[Column.FAMILY] if Column.FAMILY in spec.keys else None,
        seed_count=per_seed.height,
        observations=group.height,
        cells=group.select(Column.CLIENT, Column.FAMILY).n_unique(),
        pooling_mean=pooling.mean_difference,
        pooling_ci_low=pooling.ci_low,
        pooling_ci_high=pooling.ci_high,
        hurt_seeds=(per_seed[Column.POOLING_GAIN].to_numpy() < 0).sum().item(),
        hurts=pooling.mean_difference < 0,
        hurts_interval_below_zero=pooling.ci_high is not None and pooling.ci_high < 0,
        ctk_mean=ctk.mean_difference,
        ctk_ci_low=ctk.ci_low,
        ctk_ci_high=ctk.ci_high,
        repair_mean=repair.mean_difference,
        repair_ci_low=repair.ci_low,
        repair_ci_high=repair.ci_high,
        new_capability_mean=new.mean_difference,
        new_capability_ci_low=new.ci_low,
        new_capability_ci_high=new.ci_high,
        harm_mean=harm.mean_difference,
        harm_ci_low=harm.ci_low,
        harm_ci_high=harm.ci_high,
        repair_share=repair.mean_difference / gross if gross > 0 else None,
    )


def negative_transfer_decomposition(cells: CellTable, config: Config) -> TransferTable:
    rows: list[TransferRow | None] = []
    for experiment in frozen_family_set_experiments():
        for population in hidden_populations():
            scoped = cells.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.POPULATION) == population)
            )
            if scoped.height == 0:
                continue
            for spec in transfer_scopes():
                groups = (
                    scoped.partition_by(*spec.keys, maintain_order=True) if spec.keys else [scoped]
                )
                rows.extend(
                    _transfer_row(experiment, population, spec, group, config) for group in groups
                )
    return records_to_frame([row for row in rows if row is not None])
