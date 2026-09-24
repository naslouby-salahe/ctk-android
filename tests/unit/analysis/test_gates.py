import polars as pl

from ctk_android.analysis.gates import (
    collaboration_benefit,
    complementary_knowledge,
    dose_response,
    generic_pooling_majority,
    local_deficit,
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
    Learner,
    Metric,
)
from ctk_android.paths import Paths
from ctk_android.types import EffectRow, GateEvidence
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


def _permutation(mean: float) -> EffectRow:
    return _ctk(ExperimentName.FAMILY_PERMUTATION_CONTROL, FED, mean, -0.01, 0.01)


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


def test_a_non_null_permutation_control_rejects_the_claim() -> None:
    rows = [
        _ctk(ExperimentName.CONTROLLED_EXPOSURE, FED, 0.08, 0.05, 0.11),
        _permutation(0.06),
    ]
    assert complementary_knowledge(_evidence(rows), CONFIG).claim_status is ClaimStatus.REJECTED


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
