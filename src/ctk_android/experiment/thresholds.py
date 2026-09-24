import numpy as np

from ctk_android.enums import LibraryOption, OperatingPointStatus
from ctk_android.types import Alpha, ExceedanceCount, OperatingPoint, ScoreVector


def calibrate(
    benign_scores: ScoreVector, alpha: Alpha, min_exceedances: ExceedanceCount
) -> OperatingPoint:
    count = benign_scores.size
    if count == 0:
        return OperatingPoint(
            threshold=0.0,
            calibration_benign=0,
            status=OperatingPointStatus.INSUFFICIENT_EVIDENCE,
        )
    threshold = np.quantile(benign_scores, 1.0 - alpha, method=LibraryOption.QUANTILE_HIGHER).item()
    resolved = count * alpha >= min_exceedances
    return OperatingPoint(
        threshold=threshold,
        calibration_benign=count,
        status=OperatingPointStatus.VALID
        if resolved
        else OperatingPointStatus.INSUFFICIENT_EVIDENCE,
    )
