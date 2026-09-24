import numpy as np
import polars as pl

from ctk_android.analysis.decomposition import decomposed_learners
from ctk_android.analysis.gates import (
    federated_arms,
    frozen_family_set_experiments,
    permutation_outcome,
    simple_baselines,
)
from ctk_android.analysis.statistics import paired_effect
from ctk_android.config import Config, StatisticsConfig
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    CtkAggregation,
    Estimand,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    Learner,
    LibraryOption,
    Metric,
    OperatingPointStatus,
    RobustnessScope,
    TradeoffComparison,
    TradeoffMeasure,
)
from ctk_android.types import (
    Alpha,
    AnchoredEffectRow,
    AnchoredSelectionRow,
    AnchoredTable,
    AuditTable,
    ClientCountsTable,
    ComparisonTable,
    Effect,
    EffectRow,
    EffectsTable,
    FamilyEffectsTable,
    FamilySeedTable,
    FidelityTable,
    HeadroomRow,
    HeadroomTable,
    Passed,
    PatternTable,
    PermutationAuditRow,
    RatesTable,
    RobustnessTable,
    ScopeMap,
    SeedEffects,
    SeedSummary,
    SelectionTable,
    SummaryTable,
    SynthesisRow,
    SynthesisTable,
    Table,
    TradeoffRow,
    TradeoffTable,
)


def _ordered(frame: Table, *columns: Column) -> Table:
    return frame.sort(*columns) if frame.height else frame


def _summary(values: SeedEffects, config: StatisticsConfig) -> SeedSummary | None:
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
            summary = _summary(values, config.statistics)
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


def federated_arm_tradeoff(summary: SummaryTable, config: Config) -> TradeoffTable:
    alpha = config.experiments.operating.primary_alpha
    arms = [*federated_arms(), Learner.BLEND, Learner.CENTRAL]
    rows: list[TradeoffRow] = []
    for measure in TradeoffMeasure:
        reference = _measure(summary, Learner.FEDAVG, measure, alpha)
        for learner in arms:
            values = _measure(summary, learner, measure, alpha)
            if values is None:
                continue
            versus_local = _summary(values, config.statistics)
            if versus_local is None:
                continue
            rows.append(
                TradeoffRow(
                    evidence_class=EvidenceClass.POST_CONFIRMATORY,
                    learner=learner,
                    comparison=TradeoffComparison.VERSUS_LOCAL,
                    measure=measure,
                    within_tolerance=_within_tolerance(
                        measure, versus_local.mean_difference, config
                    ),
                    **versus_local.model_dump(),
                )
            )
            if learner is Learner.FEDAVG or reference is None:
                continue
            difference = _summary(values - reference, config.statistics)
            if difference is None:
                continue
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
            gap = _summary(full - peer, config.statistics)
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
