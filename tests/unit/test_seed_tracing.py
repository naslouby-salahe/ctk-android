import numpy as np
import polars as pl

from ctk_android.config import load_config
from ctk_android.data.partitions import assign_roles
from ctk_android.data.preparation import assign_targets
from ctk_android.enums import ClientId, Column, EligibilityProfile, Grouping
from ctk_android.experiment import design
from ctk_android.paths import Paths
from ctk_android.types import PartitionKey, RandomSeed
from tests.architecture.source_index import REPO_ROOT
from tests.unit.synthetic import synthetic_study

CONFIG = load_config(Paths(REPO_ROOT))
STUDY = synthetic_study()
GROUPS = np.random.default_rng(3).integers(0, 200, size=4000)


def _key(seed: int, salt: int = 0) -> PartitionKey:
    return PartitionKey(
        seed=RandomSeed(seed),
        salt=salt,
        grouping=Grouping.COMPONENT,
        profile=EligibilityProfile.PRIMARY,
    )


def _roles(seed: int, salt: int = 0, attempt: int = 0) -> list[str]:
    return assign_roles(GROUPS, _key(seed, salt), attempt, CONFIG.data).to_list()


def test_partition_roles_are_a_pure_function_of_seed_salt_and_attempt() -> None:
    assert _roles(1) == _roles(1)
    assert _roles(1) != _roles(2)
    assert _roles(1) != _roles(1, salt=1)
    assert _roles(1) != _roles(1, attempt=1)


def test_training_order_and_priorities_are_reproducible_and_depend_on_seed_and_salt() -> None:
    first = design.training_orders(STUDY, RandomSeed(5), 0)
    again = design.training_orders(STUDY, RandomSeed(5), 0)
    assert all(np.array_equal(first[client], again[client]) for client in ClientId)
    other_seed = design.training_orders(STUDY, RandomSeed(6), 0)
    other_salt = design.training_orders(STUDY, RandomSeed(5), 1)
    assert any(not np.array_equal(first[client], other_seed[client]) for client in ClientId)
    assert any(not np.array_equal(first[client], other_salt[client]) for client in ClientId)
    assert all(
        np.array_equal(np.sort(first[client]), np.sort(other_seed[client])) for client in ClientId
    )
    priorities = design.row_priorities(STUDY, RandomSeed(5), 0)
    assert np.array_equal(priorities, design.row_priorities(STUDY, RandomSeed(5), 0))
    assert not np.array_equal(priorities, design.row_priorities(STUDY, RandomSeed(6), 0))


def _pairs() -> pl.DataFrame:
    rows = [
        {
            Column.CLIENT: client,
            Column.FAMILY: family,
            Column.FIT_ROWS: 1000,
            Column.TARGET_FIT_ROWS: 100,
            Column.ELIGIBLE: True,
        }
        for client in ClientId
        for family in ("f1", "f2", "f3", "f4")
    ]
    return pl.DataFrame(rows)


def test_target_assignment_does_not_depend_on_pair_row_order() -> None:
    rule = CONFIG.data.eligibility[EligibilityProfile.PRIMARY]
    families = ("f1", "f2", "f3", "f4")
    pairs = _pairs()
    reference = assign_targets(pairs, RandomSeed(7), families, rule)
    for shuffle in range(5):
        shuffled = pairs.sample(fraction=1.0, shuffle=True, seed=shuffle)
        assert assign_targets(shuffled, RandomSeed(7), families, rule) == reference
    seeds = {
        tuple(assign_targets(pairs, RandomSeed(seed), families, rule)[0].client for _ in (0,))
        for seed in range(20)
    }
    assert len(seeds) > 1
