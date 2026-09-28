import numpy as np
import polars as pl

from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    ExposureCondition,
    Learner,
    OperatingPointStatus,
    SplitRole,
)
from ctk_android.experiment import design, evaluation
from ctk_android.paths import Paths
from ctk_android.types import ArmKey
from tests.architecture.source_index import REPO_ROOT
from tests.unit.synthetic import synthetic_study, synthetic_targets

OPERATING = load_config(Paths(REPO_ROOT)).experiments.operating
STUDY = synthetic_study()
TARGETS = synthetic_targets()
MASKS = design.family_masks(STUDY, ("alpha", "beta"))
ATTRIBUTES = evaluation.row_attributes(STUDY, MASKS)
POOLS = evaluation.build_pools(ATTRIBUTES, TARGETS)
ARM = ArmKey(learner=Learner.CENTRAL, condition=ExposureCondition.PEER_PRESENT, dose=None)


def _scores(seed: int) -> dict[ClientId, np.ndarray]:
    rng = np.random.default_rng(seed)
    return {client: rng.normal(size=rows.size) for client, rows in POOLS.items()}


def test_pools_contain_hidden_family_calibration_rows_but_evaluation_never_uses_them() -> None:
    roles = ATTRIBUTES.roles
    pooled_hidden_calibration = [
        rows[MASKS["alpha"][rows] & (roles[rows] == SplitRole.CALIBRATION)].size
        for rows in POOLS.values()
    ]
    assert max(pooled_hidden_calibration) > 0
    result = evaluation.evaluate_arm(ARM, _scores(0), POOLS, ATTRIBUTES, TARGETS, OPERATING)
    assert (roles[result.hidden_rows] == SplitRole.TEST).all()
    assert result.hidden_rows.size > 0


def test_thresholds_depend_only_on_benign_calibration_scores() -> None:
    base = _scores(1)
    altered = {client: scores.copy() for client, scores in base.items()}
    for client, rows in POOLS.items():
        malware_calibration = (
            (ATTRIBUTES.roles[rows] == SplitRole.CALIBRATION)
            & (ATTRIBUTES.labels[rows] == 1)
            & (ATTRIBUTES.clients[rows] == client)
        )
        altered[client][malware_calibration] += 100.0
    first = evaluation.evaluate_arm(ARM, base, POOLS, ATTRIBUTES, TARGETS, OPERATING)
    second = evaluation.evaluate_arm(ARM, altered, POOLS, ATTRIBUTES, TARGETS, OPERATING)
    assert (
        first.operating[Column.THRESHOLD].to_list() == second.operating[Column.THRESHOLD].to_list()
    )


def test_calibration_and_test_discrimination_are_reported_separately() -> None:
    result = evaluation.evaluate_arm(ARM, _scores(2), POOLS, ATTRIBUTES, TARGETS, OPERATING)
    splits = set(result.discrimination[Column.SPLIT].to_list())
    assert splits == {SplitRole.TEST, SplitRole.CALIBRATION}


def test_a_tail_target_without_calibration_support_is_labelled_insufficient() -> None:
    result = evaluation.evaluate_arm(ARM, _scores(3), POOLS, ATTRIBUTES, TARGETS, OPERATING)
    statuses = result.operating.filter(pl.col(Column.ALPHA) == min(OPERATING.alphas))[
        Column.OPERATING_STATUS
    ]
    assert set(statuses.to_list()) == {OperatingPointStatus.INSUFFICIENT_EVIDENCE}


def testfirst_occurrence_counts_each_feature_identity_once() -> None:
    ids = np.array([5, 5, 7, 5, 7, 9])
    mask = np.array([True, True, True, False, True, True])
    first = evaluation.first_occurrence(mask, ids)
    assert first.tolist() == [True, False, True, False, False, True]


def test_unique_counts_never_exceed_raw_counts() -> None:
    result = evaluation.evaluate_arm(ARM, _scores(0), POOLS, ATTRIBUTES, TARGETS, OPERATING)
    families = result.families
    assert (families[Column.UNIQUE_TRIALS] <= families[Column.TRIALS]).all()
    assert (families[Column.UNIQUE_HITS] <= families[Column.UNIQUE_TRIALS]).all()
