import numpy as np
import polars as pl

from ctk_android.config import load_config
from ctk_android.data.partitions import assign_roles
from ctk_android.enums import EligibilityProfile, Grouping, SplitRole
from ctk_android.paths import Paths
from ctk_android.types import PartitionKey
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT)).data
KEY = PartitionKey(seed=3, salt=0, grouping=Grouping.COMPONENT, profile=EligibilityProfile.PRIMARY)
GROUPS = np.random.default_rng(0).integers(0, 400, size=6000).astype(np.int64)
GROUP_TOLERANCE = 0.05


def test_a_group_is_never_split_across_roles() -> None:
    roles = assign_roles(GROUPS, KEY, 0, CONFIG)
    frame = pl.DataFrame({"group": GROUPS, "role": roles})
    per_group = frame.group_by("group").agg(pl.col("role").n_unique().alias("roles"))
    assert per_group["roles"].max() == 1


def test_role_proportions_follow_the_configured_split() -> None:
    roles = assign_roles(GROUPS, KEY, 0, CONFIG)
    share = roles.value_counts().with_columns(pl.col("count") / GROUPS.size)
    expected = {
        SplitRole.FIT: CONFIG.partition.fit,
        SplitRole.CALIBRATION: CONFIG.partition.calibration,
        SplitRole.TEST: CONFIG.partition.test,
    }
    for row in share.iter_rows(named=True):
        assert abs(row["count"] - expected[SplitRole(row["role"])]) < GROUP_TOLERANCE


def test_roles_are_deterministic_and_seed_dependent() -> None:
    first = assign_roles(GROUPS, KEY, 0, CONFIG)
    assert first.equals(assign_roles(GROUPS, KEY, 0, CONFIG))
    other = PartitionKey(
        seed=4, salt=0, grouping=Grouping.COMPONENT, profile=EligibilityProfile.PRIMARY
    )
    assert not first.equals(assign_roles(GROUPS, other, 0, CONFIG))
