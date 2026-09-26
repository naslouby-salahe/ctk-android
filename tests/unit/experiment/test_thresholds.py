import numpy as np

from ctk_android.enums import OperatingPointStatus
from ctk_android.experiment.evaluation import calibrate

MIN_EXCEEDANCES = 10
ALPHA = 0.05
SAMPLES = 2000


def test_threshold_is_the_benign_calibration_quantile() -> None:
    scores = np.random.default_rng(0).normal(size=SAMPLES)
    point = calibrate(scores, ALPHA, MIN_EXCEEDANCES)
    assert (scores > point.threshold).mean() <= ALPHA
    assert point.status is OperatingPointStatus.VALID
    assert point.calibration_benign == SAMPLES


def test_tail_target_without_resolution_is_insufficient_evidence() -> None:
    scores = np.random.default_rng(0).normal(size=200)
    assert (
        calibrate(scores, 0.01, MIN_EXCEEDANCES).status
        is OperatingPointStatus.INSUFFICIENT_EVIDENCE
    )


def test_empty_calibration_is_insufficient_evidence() -> None:
    assert (
        calibrate(np.empty(0), ALPHA, MIN_EXCEEDANCES).status
        is OperatingPointStatus.INSUFFICIENT_EVIDENCE
    )
