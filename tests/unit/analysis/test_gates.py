import polars as pl

from ctk_android.analysis.gates import (
    collaboration_benefit,
    complementary_knowledge,
    dose_response,
    family_dependence,
    feature_novelty_explanation,
    generic_pooling_majority,
    known_family_safety,
    local_deficit,
    new_mechanism_trigger,
    permutation_outcome,
    representation_limited_family,
)
from ctk_android.config import load_config
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    ClaimStatus,
    Column,
    ContrastFamily,
    Estimand,
    ExperimentName,
    ExposureCondition,
    Learner,
    Metric,
    PermutationOutcome,
)
from ctk_android.paths import Paths
from ctk_android.types import EffectRow, GateEvidence, Interval, NoveltyAssociation
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
FED = Metric.FEDERATION_UNSEEN_RECALL
OWN = Metric.OWN_DOMAIN_UNSEEN_RECALL


def _row(
    experiment: ExperimentName,
    learner: Learner,
    estimand: Estimand,
    metric: Metric,
    mean: float,
    low: float | None,
    high: float | None,
    positive: int = 10,
) -> EffectRow:
    return EffectRow(
        experiment=experiment,
        salt=0,
        alpha=ALPHA,
        metric=metric,
        learner=learner,
        estimand=estimand,
        contrast_family=ContrastFamily.EXPLORATORY,
        mean_difference=mean,
        median_difference=mean,
        positive_seeds=positive,
        seed_count=10,
        effect_size=None,
        ci_low=low,
        ci_high=high,
        p_value=0.01,
        p_holm=None,
    )


def _evidence(rows: list[EffectRow], failed: int = 0) -> GateEvidence:
    empty = pl.DataFrame()
    return GateEvidence(
        effects=records_to_frame(rows),
        summary=empty,
        family_seed=empty,
        family_effects=empty,
        dose=empty,
        associations={},
        failed_validation_runs=failed,
    )


def _ctk(
    experiment: ExperimentName, metric: Metric, mean: float, low: float, high: float
) -> EffectRow:
    return _row(experiment, Learner.FEDAVG, Estimand.CTK_GAIN, metric, mean, low, high)


BAND = CONFIG.statistics.gates.ctk_min_gain


def _permutation(mean: float, low: float | None = None, high: float | None = None) -> EffectRow:
    row = _ctk(
        ExperimentName.FAMILY_PERMUTATION_CONTROL,
        FED,
        mean,
        mean - 0.005 if low is None else low,
        mean + 0.005 if high is None else high,
    )
    return row


def test_complementary_knowledge_is_promoted_when_every_scope_passes() -> None:
    rows = [
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11),
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, OWN, 0.06, 0.03, 0.09),
        _ctk(ExperimentName.REPLICATION_FAMILY_SET, FED, 0.05, 0.02, 0.08),
        _permutation(0.001),
    ]
    assert complementary_knowledge(_evidence(rows), CONFIG).claim_status is ClaimStatus.PROMOTED


def test_complementary_knowledge_is_narrowed_when_only_one_scope_passes() -> None:
    rows = [
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11),
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, OWN, 0.01, -0.02, 0.04),
        _ctk(ExperimentName.REPLICATION_FAMILY_SET, FED, 0.01, -0.01, 0.03),
        _permutation(0.0),
    ]
    result = complementary_knowledge(_evidence(rows), CONFIG)
    assert result.claim_status is ClaimStatus.NARROWED
    assert result.scopes_passed == 1


def _claim_with(permutation: EffectRow) -> ClaimStatus:
    rows = [
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11),
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, OWN, 0.06, 0.03, 0.09),
        _ctk(ExperimentName.REPLICATION_FAMILY_SET, FED, 0.05, 0.02, 0.08),
        permutation,
    ]
    return complementary_knowledge(_evidence(rows), CONFIG).claim_status


def test_the_permutation_null_is_the_ci_within_the_predeclared_ctk_band() -> None:
    assert BAND == 0.03
    developed = _permutation(-0.010038, -0.015527, -0.004057)
    assert permutation_outcome(developed, BAND) is PermutationOutcome.EQUIVALENT
    assert _claim_with(developed) is ClaimStatus.PROMOTED


def test_the_equivalence_band_is_inclusive() -> None:
    assert (
        permutation_outcome(_permutation(0.0, -BAND, BAND), BAND) is PermutationOutcome.EQUIVALENT
    )


def test_an_interval_entirely_outside_the_band_rejects_the_claim() -> None:
    above = _permutation(0.06, 0.05, 0.07)
    below = _permutation(-0.06, -0.07, -0.05)
    assert permutation_outcome(above, BAND) is PermutationOutcome.EXCEEDS_BAND
    assert _claim_with(above) is ClaimStatus.REJECTED
    assert _claim_with(below) is ClaimStatus.REJECTED


def test_an_interval_straddling_a_band_edge_is_unresolved_not_rejected() -> None:
    straddling = _permutation(0.01, -0.02, 0.05)
    assert permutation_outcome(straddling, BAND) is PermutationOutcome.UNRESOLVED
    assert _claim_with(straddling) is ClaimStatus.INSUFFICIENT_EVIDENCE


def test_a_permutation_effect_with_a_small_mean_but_a_wide_interval_is_not_equivalent() -> None:
    wide = _permutation(0.0, -0.06, 0.06)
    assert permutation_outcome(wide, BAND) is PermutationOutcome.UNRESOLVED


def test_an_unavailable_interval_cannot_establish_equivalence() -> None:
    row = _permutation(0.0)
    assert permutation_outcome(None, BAND) is PermutationOutcome.UNRESOLVED
    assert (
        permutation_outcome(row.model_copy(update={"ci_low": None}), BAND)
        is PermutationOutcome.UNRESOLVED
    )


def test_a_missing_permutation_control_leaves_the_claim_unresolved() -> None:
    rows = [_ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11)]
    result = complementary_knowledge(_evidence(rows), CONFIG)
    assert result.claim_status is ClaimStatus.INSUFFICIENT_EVIDENCE


def test_failed_validation_blocks_promotion() -> None:
    rows = [
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11),
        _permutation(0.0),
    ]
    result = complementary_knowledge(_evidence(rows, failed=1), CONFIG)
    assert result.claim_status is ClaimStatus.INSUFFICIENT_EVIDENCE


def test_local_deficit_requires_gap_interval_and_seed_count() -> None:
    def row(positive: int) -> list[EffectRow]:
        return [
            _row(
                ExperimentName.CONTROLLED_EXPOSURE,
                Learner.CENTRAL,
                Estimand.LOCAL_DEFICIT,
                metric,
                0.3,
                0.2,
                0.4,
                positive,
            )
            for metric in (FED, OWN)
        ]

    assert local_deficit(_evidence(row(9)), CONFIG).claim_status is ClaimStatus.PROMOTED
    assert local_deficit(_evidence(row(5)), CONFIG).claim_status is not ClaimStatus.PROMOTED


def test_collaboration_benefit_needs_a_practical_effect() -> None:
    rows = [
        _row(
            ExperimentName.CONTROLLED_EXPOSURE,
            Learner.FEDAVG,
            Estimand.TOTAL_GAIN,
            metric,
            0.001,
            -0.01,
            0.005,
        )
        for metric in (FED, OWN)
    ]
    assert collaboration_benefit(_evidence(rows), CONFIG).claim_status is ClaimStatus.REJECTED


def test_generic_pooling_majority_needs_the_interval_above_one_half() -> None:
    def share(low: float, high: float) -> list[EffectRow]:
        return [
            _row(
                ExperimentName.CONTROLLED_EXPOSURE,
                Learner.FEDAVG,
                Estimand.POOLING_SHARE,
                metric,
                0.7,
                low,
                high,
            )
            for metric in (FED, OWN)
        ]

    assert (
        generic_pooling_majority(_evidence(share(0.55, 0.9)), CONFIG).claim_status
        is ClaimStatus.PROMOTED
    )
    assert (
        generic_pooling_majority(_evidence(share(0.2, 0.4)), CONFIG).claim_status
        is ClaimStatus.REJECTED
    )
    assert (
        generic_pooling_majority(_evidence(share(0.3, 0.8)), CONFIG).claim_status
        is ClaimStatus.INSUFFICIENT_EVIDENCE
    )


def _dose_frame(gains: dict[int, float]) -> pl.DataFrame:
    rows = [
        {
            Column.LEARNER: Learner.FEDAVG,
            Column.DOSE: dose,
            Column.FAMILY: family,
            Column.RECALL: 0.1 + gain,
            Column.EFFECTIVE_DOSE: float(dose),
            Column.CTK_GAIN: gain,
        }
        for dose, gain in gains.items()
        for family in ("alpha", "beta", "gamma")
    ]
    return pl.DataFrame(rows)


def test_dose_response_is_promoted_for_a_rising_curve_not_driven_by_one_family() -> None:
    evidence = _evidence([]).model_copy(
        update={"dose": _dose_frame({0: 0.0, 10: 0.01, 100: 0.05, 500: 0.08})}
    )
    assert dose_response(evidence, CONFIG).claim_status is ClaimStatus.PROMOTED


def test_dose_response_is_rejected_for_a_flat_curve() -> None:
    evidence = _evidence([]).model_copy(
        update={"dose": _dose_frame({0: 0.0, 10: 0.0, 100: 0.0, 500: 0.0})}
    )
    assert dose_response(evidence, CONFIG).claim_status is not ClaimStatus.PROMOTED


def test_representation_limited_family_needs_a_second_model_to_agree() -> None:
    def frame(experiment: ExperimentName, recalls: dict[str, float]) -> pl.DataFrame:
        return pl.DataFrame(
            [
                {
                    Column.EXPERIMENT: experiment,
                    Column.LEARNER: Learner.CENTRAL,
                    Column.FAMILY: family,
                    Column.FULL_RECALL: value,
                }
                for family, value in recalls.items()
            ]
        )

    effects = pl.concat(
        [
            frame(ExperimentName.CONTROLLED_EXPOSURE, {"alpha": 0.3, "beta": 0.9}),
            frame(ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR, {"alpha": 0.4, "beta": 0.8}),
            frame(ExperimentName.MODEL_FAMILY_REPLICATION_TREES, {"alpha": 0.7, "beta": 0.9}),
        ]
    )
    evidence = _evidence([]).model_copy(update={"family_effects": effects})
    result = representation_limited_family(evidence, CONFIG)
    assert result.claim_status is ClaimStatus.PROMOTED
    assert result.scopes_passed == 1


def _summary_rows(values: dict[tuple[Learner, ExposureCondition, Metric], float]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
                Column.SEED: seed,
                Column.LEARNER: learner,
                Column.CONDITION: condition,
                Column.DOSE: None,
                Column.METRIC: metric,
                Column.ALPHA: ALPHA,
                Column.VALUE: value,
            }
            for (learner, condition, metric), value in values.items()
            for seed in range(5)
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


PEER = ExposureCondition.PEER_PRESENT
KNOWN = Metric.KNOWN_FAMILY_RECALL
FPR = Metric.REALISED_FPR


def test_known_family_safety_is_promoted_when_the_strongest_arm_barely_moves_known_recall() -> None:
    summary = _summary_rows(
        {
            (Learner.LOCAL, PEER, KNOWN): 0.72,
            (Learner.LOCAL, PEER, FPR): 0.050,
            (Learner.FEDAVG, PEER, FED): 0.60,
            (Learner.FEDAVG, PEER, KNOWN): 0.73,
            (Learner.FEDAVG, PEER, FPR): 0.052,
        }
    )
    evidence = _evidence([]).model_copy(update={"summary": summary})
    assert known_family_safety(evidence, CONFIG).claim_status is ClaimStatus.PROMOTED


def test_known_family_safety_is_rejected_for_a_material_known_family_cost() -> None:
    summary = _summary_rows(
        {
            (Learner.LOCAL, PEER, KNOWN): 0.72,
            (Learner.LOCAL, PEER, FPR): 0.050,
            (Learner.FEDAVG, PEER, FED): 0.60,
            (Learner.FEDAVG, PEER, KNOWN): 0.60,
            (Learner.FEDAVG, PEER, FPR): 0.050,
        }
    )
    evidence = _evidence([]).model_copy(update={"summary": summary})
    assert known_family_safety(evidence, CONFIG).claim_status is ClaimStatus.REJECTED


def _family_seed(gains: dict[str, float]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {Column.LEARNER: Learner.FEDAVG, Column.FAMILY: family, Column.CTK_GAIN: gain}
            for family, gain in gains.items()
        ]
    )


def test_family_dependence_needs_a_material_spread_across_families() -> None:
    wide = _evidence([]).model_copy(update={"family_seed": _family_seed({"a": 0.02, "b": 0.25})})
    flat = _evidence([]).model_copy(update={"family_seed": _family_seed({"a": 0.10, "b": 0.11})})
    assert family_dependence(wide, CONFIG).claim_status is ClaimStatus.PROMOTED
    assert family_dependence(flat, CONFIG).claim_status is ClaimStatus.REJECTED


def _association(rho: float, low: float, high: float) -> NoveltyAssociation:
    return NoveltyAssociation(
        rho=rho, p_value=0.01, interval=Interval(low=low, high=high), families=8
    )


def test_feature_novelty_needs_a_strong_consistent_association_in_both_family_sets() -> None:
    both = {
        ExperimentName.CONTROLLED_EXPOSURE: _association(0.6, 0.2, 0.9),
        ExperimentName.REPLICATION_FAMILY_SET: _association(0.5, 0.1, 0.8),
    }
    opposite = {
        ExperimentName.CONTROLLED_EXPOSURE: _association(0.6, 0.2, 0.9),
        ExperimentName.REPLICATION_FAMILY_SET: _association(-0.6, -0.9, -0.2),
    }
    weak = {
        ExperimentName.CONTROLLED_EXPOSURE: _association(0.1, -0.4, 0.5),
        ExperimentName.REPLICATION_FAMILY_SET: _association(0.1, -0.4, 0.5),
    }
    promoted = feature_novelty_explanation(
        _evidence([]).model_copy(update={"associations": both}), CONFIG
    )
    contradicted = feature_novelty_explanation(
        _evidence([]).model_copy(update={"associations": opposite}), CONFIG
    )
    inconclusive = feature_novelty_explanation(
        _evidence([]).model_copy(update={"associations": weak}), CONFIG
    )
    assert promoted.claim_status is ClaimStatus.PROMOTED
    assert contradicted.claim_status is not ClaimStatus.PROMOTED
    assert inconclusive.claim_status is not ClaimStatus.PROMOTED


def test_the_mechanism_trigger_closes_when_baselines_recover_most_of_the_gap() -> None:
    full = ExposureCondition.FULL_EXPOSURE
    closed = _summary_rows(
        {
            (Learner.CENTRAL, full, FED): 0.70,
            (Learner.CENTRAL, full, Metric.WORST_CLIENT_UNSEEN_RECALL): 0.50,
            (Learner.FEDAVG, PEER, FED): 0.66,
            (Learner.FEDAVG, PEER, Metric.WORST_CLIENT_UNSEEN_RECALL): 0.45,
        }
    )
    open_gap = _summary_rows(
        {
            (Learner.CENTRAL, full, FED): 0.90,
            (Learner.CENTRAL, full, Metric.WORST_CLIENT_UNSEEN_RECALL): 0.80,
            (Learner.FEDAVG, PEER, FED): 0.60,
            (Learner.FEDAVG, PEER, Metric.WORST_CLIENT_UNSEEN_RECALL): 0.40,
        }
    )
    assert (
        new_mechanism_trigger(
            _evidence([]).model_copy(update={"summary": closed}), CONFIG
        ).claim_status
        is ClaimStatus.REJECTED
    )
    assert (
        new_mechanism_trigger(
            _evidence([]).model_copy(update={"summary": open_gap}), CONFIG
        ).claim_status
        is ClaimStatus.INSUFFICIENT_EVIDENCE
    )
