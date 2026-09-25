import numpy as np
import polars as pl

from ctk_android.config import load_config
from ctk_android.data.families import large_family_sets, select_large_family_sets
from ctk_android.data.partitions import client_fit_rows
from ctk_android.enums import (
    ClientId,
    Column,
    EligibilityProfile,
    EligibilityReason,
    SplitRole,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

RULE = load_config(Paths(REPO_ROOT)).data.eligibility[EligibilityProfile.PRIMARY]
CLIENTS = (ClientId.ANZHI, ClientId.APPCHINA)
SUPPORT = {"big": 4000, "mid": 2500, "small": 1500, "tiny": 5}


def _labelled() -> pl.DataFrame:
    rows: list[dict[Column, str | int]] = []
    for family, total in SUPPORT.items():
        for client in CLIENTS:
            rows.extend(
                {
                    Column.CLIENT: client,
                    Column.FAMILY: family,
                    Column.LABEL: 1,
                    Column.REASON: EligibilityReason.ELIGIBLE,
                }
                for _ in range(total // len(CLIENTS))
            )
    rows.extend(
        {
            Column.CLIENT: client,
            Column.FAMILY: "unknown",
            Column.LABEL: 0,
            Column.REASON: EligibilityReason.NOT_IN_FAMILY_SET,
        }
        for client in CLIENTS
        for _ in range(3000)
    )
    return pl.DataFrame(rows)


def _roles(height: int) -> pl.Series:
    order = np.random.default_rng(1).permutation(height)
    fit_edge, calibration_edge = int(0.6 * height), int(0.8 * height)
    roles = np.empty(height, dtype=object)
    roles[order[:fit_edge]] = SplitRole.FIT
    roles[order[fit_edge:calibration_edge]] = SplitRole.CALIBRATION
    roles[order[calibration_edge:]] = SplitRole.TEST
    return pl.Series(Column.ROLE, roles.tolist(), dtype=pl.String)


def test_only_structurally_eligible_families_are_selected_and_ranked_by_support() -> None:
    labelled = _labelled()
    roles = _roles(labelled.height)
    selection = select_large_family_sets(labelled, roles, client_fit_rows(labelled, roles), RULE)
    ranked = selection.table
    assert ranked[Column.FAMILY].to_list() == ["big", "mid", "small"]
    assert ranked[Column.RANK].to_list() == [0, 1, 2]
    assert selection.sets[large_family_sets()[0]] == ("big",)
    assert selection.sets[large_family_sets()[1]] == ("mid",)
    assert selection.sets[large_family_sets()[3]] == ()


def test_batches_are_a_partition_of_the_selected_families() -> None:
    labelled = _labelled()
    roles = _roles(labelled.height)
    selection = select_large_family_sets(labelled, roles, client_fit_rows(labelled, roles), RULE)
    members = [family for batch in selection.sets.values() for family in batch]
    assert sorted(members) == sorted(selection.table[Column.FAMILY].to_list())
