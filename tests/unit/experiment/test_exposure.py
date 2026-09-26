import numpy as np

from ctk_android.enums import ClientId, Column, ExposureCondition, ExposureMode, Learner, SplitRole
from ctk_android.experiment import design
from ctk_android.types import ArmKey
from tests.unit.synthetic import synthetic_study, synthetic_targets

BUDGET = 30
STUDY = synthetic_study()
TARGETS = synthetic_targets()
MASKS = design.family_masks(STUDY, ("alpha", "beta"))
ORDERS = design.training_orders(STUDY, 5, 0)


def _select(condition: ExposureCondition, dose: int | None = None) -> dict[ClientId, np.ndarray]:
    arm = ArmKey(learner=Learner.CENTRAL, condition=condition, dose=dose)
    spec = design.exposure_spec(arm, ExposureMode.HIDE_FROM_TARGET, TARGETS)
    priorities = design.row_priorities(STUDY, 5, 0)
    allowed = design.allowed_dose_rows(STUDY, MASKS, spec, priorities)
    return design.select_training(ORDERS, MASKS, spec, allowed, BUDGET)


def _count(rows: dict[ClientId, np.ndarray], client: ClientId, family: str) -> int:
    return MASKS[family][rows[client]].sum().item()


def test_hidden_family_is_absent_from_its_target_and_present_at_peers() -> None:
    rows = _select(ExposureCondition.PEER_PRESENT)
    assert _count(rows, ClientId.ANZHI, "alpha") == 0
    assert _count(rows, ClientId.APPCHINA, "beta") == 0
    assert _count(rows, ClientId.PLAY_EARLY, "alpha") > 0
    assert _count(rows, ClientId.ANZHI, "beta") > 0


def test_family_absent_everywhere_removes_target_families_from_every_client() -> None:
    rows = _select(ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    assert all(
        _count(rows, client, family) == 0 for client in ClientId for family in ("alpha", "beta")
    )


def test_full_exposure_restores_hidden_family_examples() -> None:
    rows = _select(ExposureCondition.FULL_EXPOSURE)
    assert _count(rows, ClientId.ANZHI, "alpha") > 0


def test_training_sizes_match_across_conditions_and_use_only_fit_rows() -> None:
    sizes = {
        condition: {client: rows.size for client, rows in _select(condition).items()}
        for condition in ExposureCondition
    }
    assert len({tuple(sorted(per.items())) for per in sizes.values()}) == 1
    roles = STUDY.table[Column.ROLE].to_numpy()
    for rows in _select(ExposureCondition.PEER_PRESENT).values():
        assert (roles[rows] == SplitRole.FIT).all()


def test_zero_dose_matches_the_family_absent_condition_for_target_families() -> None:
    rows = _select(ExposureCondition.PEER_PRESENT, dose=0)
    assert all(_count(rows, client, "alpha") == 0 for client in ClientId)


def test_dose_caps_the_peer_exposure_to_the_requested_count() -> None:
    dose = 3
    rows = _select(ExposureCondition.PEER_PRESENT, dose=dose)
    peers = sum(
        _count(rows, client, "alpha") for client in ClientId if client is not ClientId.ANZHI
    )
    assert peers <= dose
