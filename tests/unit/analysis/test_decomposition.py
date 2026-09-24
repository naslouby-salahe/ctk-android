import polars as pl
import pytest

from ctk_android.analysis.decomposition import decompose
from ctk_android.enums import (
    Column,
    Estimand,
    ExperimentName,
    ExposureCondition,
    Learner,
    Metric,
)

ALPHA = 0.05
RECALLS = {
    (Learner.LOCAL, ExposureCondition.PEER_PRESENT): 0.10,
    (Learner.CENTRAL, ExposureCondition.PEER_PRESENT): 0.60,
    (Learner.CENTRAL, ExposureCondition.FAMILY_ABSENT_EVERYWHERE): 0.35,
    (Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE): 0.70,
    (Learner.FEDAVG, ExposureCondition.PEER_PRESENT): 0.50,
    (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE): 0.30,
}


def _summary() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
                Column.SEED: 100,
                Column.SALT: 0,
                Column.LEARNER: learner,
                Column.CONDITION: condition,
                Column.DOSE: None,
                Column.ALPHA: ALPHA,
                Column.METRIC: Metric.FEDERATION_UNSEEN_RECALL,
                Column.VALUE: value,
            }
            for (learner, condition), value in RECALLS.items()
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def _value(frame: pl.DataFrame, learner: Learner, estimand: Estimand) -> float:
    return frame.filter(
        (pl.col(Column.LEARNER) == learner) & (pl.col(Column.ESTIMAND) == estimand)
    )[Column.VALUE].item()


def test_decomposition_identity_total_equals_pooling_plus_complementary() -> None:
    result = decompose(_summary())
    for learner in (Learner.CENTRAL, Learner.FEDAVG):
        total = _value(result, learner, Estimand.TOTAL_GAIN)
        pooling = _value(result, learner, Estimand.POOLING_GAIN)
        complementary = _value(result, learner, Estimand.CTK_GAIN)
        assert total == pytest.approx(pooling + complementary)


def test_component_values_follow_the_roadmap_definitions() -> None:
    result = decompose(_summary())
    assert _value(result, Learner.CENTRAL, Estimand.TOTAL_GAIN) == pytest.approx(0.50)
    assert _value(result, Learner.CENTRAL, Estimand.POOLING_GAIN) == pytest.approx(0.25)
    assert _value(result, Learner.CENTRAL, Estimand.CTK_GAIN) == pytest.approx(0.25)
    assert _value(result, Learner.FEDAVG, Estimand.CTK_GAIN) == pytest.approx(0.20)


def test_oracle_gap_recovery_is_gain_over_full_exposure_headroom() -> None:
    result = decompose(_summary())
    assert _value(result, Learner.FEDAVG, Estimand.ORACLE_GAP_RECOVERY) == pytest.approx(
        (0.50 - 0.10) / (0.70 - 0.10)
    )


def test_local_deficit_is_the_gap_to_the_full_exposure_central_reference() -> None:
    result = decompose(_summary())
    assert _value(result, Learner.CENTRAL, Estimand.LOCAL_DEFICIT) == pytest.approx(0.60)
