import numpy as np
import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    AllowedWording,
    ClaimName,
    ClaimStatus,
    Column,
    Estimand,
    ExperimentName,
    ExposureCondition,
    Learner,
    Metric,
    StatisticsLimit,
)
from ctk_android.types import (
    Alpha,
    ClaimResult,
    Effect,
    EffectRow,
    FamilyName,
    Fraction,
    GateEvidence,
    RowCount,
    SupportCount,
)


def federated_arms() -> tuple[Learner, Learner, Learner]:
    return (Learner.FEDAVG, Learner.FEDPROX, Learner.FEDAVG_FINETUNE)


def simple_baselines() -> list[Learner]:
    return [Learner.CENTRAL, *federated_arms(), Learner.BLEND]


def _mean(values: pl.Series) -> Effect | None:
    present = values.drop_nulls().to_numpy()
    return present.mean().item() if present.size else None


def _effect(
    effects: pl.DataFrame,
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


def _passes(row: EffectRow | None, minimum: Effect, positive_seeds: SupportCount) -> bool:
    return (
        row is not None
        and row.mean_difference >= minimum
        and row.ci_low is not None
        and row.ci_low > 0
        and (row.positive_seeds or 0) >= positive_seeds
    )


def _refuted(row: EffectRow | None, minimum: Effect) -> bool:
    return row is not None and row.ci_high is not None and row.ci_high < minimum


def _decide(passed: list[bool], refuted: list[bool]) -> ClaimStatus:
    if passed and all(passed):
        return ClaimStatus.PROMOTED
    if any(passed):
        return ClaimStatus.NARROWED
    if refuted and all(refuted):
        return ClaimStatus.REJECTED
    return ClaimStatus.INSUFFICIENT_EVIDENCE


def _result(
    claim: ClaimName, status: ClaimStatus, passed: RowCount, total: RowCount
) -> ClaimResult:
    return ClaimResult(
        claim=claim,
        claim_status=status,
        scopes_passed=passed,
        scopes_total=total,
        wording=AllowedWording[status.name],
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


def _population_metrics() -> tuple[Metric, Metric]:
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
    null_compatible = (
        permutation is not None and abs(permutation.mean_difference) <= gates.permutation_null_max
    )
    if permutation is not None and not null_compatible:
        return _result(ClaimName.COMPLEMENTARY_KNOWLEDGE, ClaimStatus.REJECTED, 0, len(scopes))
    if not null_compatible or evidence.failed_validation_runs:
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
    curve = (
        evidence.dose.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
        .group_by(Column.DOSE)
        .agg(
            pl.col(Column.RECALL).mean(),
            pl.col(Column.EFFECTIVE_DOSE).mean(),
            pl.col(Column.CTK_GAIN).mean(),
        )
        .filter(pl.col(Column.DOSE).is_not_null())
        .sort(Column.DOSE)
    )
    if curve.height < 2:
        return _result(
            ClaimName.DOSE_RESPONSE,
            ClaimStatus.INSUFFICIENT_EVIDENCE,
            0,
            StatisticsLimit.DOSE_CRITERIA,
        )
    recall = curve[Column.RECALL].to_numpy()
    monotone = (np.diff(recall) >= -gates.dose_monotone_tolerance).all().item()
    enough = curve.filter(pl.col(Column.EFFECTIVE_DOSE) >= gates.dose_min_peers)
    gain = enough[Column.CTK_GAIN].to_numpy().max().item() if enough.height else None
    improves = gain is not None and gain >= gates.dose_min_gain
    family_gains = (
        evidence.dose.filter(
            (pl.col(Column.LEARNER) == Learner.FEDAVG)
            & pl.col(Column.DOSE).is_not_null()
            & (pl.col(Column.EFFECTIVE_DOSE) >= gates.dose_min_peers)
        )
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.CTK_GAIN).mean())
    )
    not_one_family = family_gains.height > 1 and all(
        _without(family_gains, family) >= gates.dose_min_gain
        for family in family_gains[Column.FAMILY]
    )
    passed = [monotone, improves, not_one_family]
    status = (
        ClaimStatus.PROMOTED
        if all(passed)
        else ClaimStatus.REJECTED
        if not any(passed)
        else ClaimStatus.NARROWED
    )
    return _result(ClaimName.DOSE_RESPONSE, status, sum(passed), len(passed))


def _without(gains: pl.DataFrame, family: FamilyName) -> Fraction:
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
    summary: pl.DataFrame, learner: Learner, metric: Metric, alpha: Alpha
) -> pl.DataFrame:
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
    return _result(ClaimName.KNOWN_FAMILY_SAFETY, status, sum(passed), len(passed))


def family_dependence(evidence: GateEvidence, config: Config) -> ClaimResult:
    gates = config.statistics.gates
    per_family = (
        evidence.family_seed.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
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
    return _result(ClaimName.REPRESENTATION_LIMITED_FAMILY, status, len(qualifying), len(primary))


def feature_novelty_explanation(evidence: GateEvidence, config: Config) -> ClaimResult:
    minimum = config.statistics.gates.novelty_min_abs_spearman
    outcomes: list[bool] = []
    directions: set[bool] = set()
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


def evaluate_claims(evidence: GateEvidence, config: Config) -> pl.DataFrame:
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
