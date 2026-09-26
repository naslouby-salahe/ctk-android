import numpy as np
import polars as pl
import pytest

from ctk_android.data.preparation import feature_identities
from ctk_android.enums import ClientId, Column, EligibilityReason, SplitRole
from ctk_android.experiment import design
from ctk_android.types import CtkError, RandomSeed, StudyData, TargetPair

FAMILIES = ("alpha", "beta", "gamma", "delta", "epsilon")
PER_CELL = 100
BUDGET = 60
SEED = RandomSeed(7)


def _study() -> StudyData:
    rows: list[dict[Column, object]] = []
    for client in ClientId:
        for role in SplitRole:
            for label in (0, 1):
                for index in range(PER_CELL):
                    rows.append(
                        {
                            Column.CLIENT: client,
                            Column.ROLE: role,
                            Column.LABEL: label,
                            Column.FAMILY: "benign" if label == 0 else FAMILIES[index % 5],
                            Column.REASON: EligibilityReason.ELIGIBLE
                            if label
                            else EligibilityReason.NOT_IN_FAMILY_SET,
                        }
                    )
    table = pl.DataFrame(rows).with_row_index(Column.ROW)
    features = (np.random.default_rng(0).random((table.height, 6)) < 0.5).astype(np.uint8)
    table = table.with_columns(pl.Series(Column.FEATURE_ID, feature_identities(features)))
    return StudyData(table=table, features=features)


STUDY = _study()
TARGETS = (
    TargetPair(client=ClientId.ANZHI, family="alpha"),
    TargetPair(client=ClientId.APPCHINA, family="beta"),
)
MASKS = design.family_masks(STUDY, ("alpha", "beta"))
ORDERS = design.training_orders(STUDY, SEED, 0)
FIT = design.family_fit_rows(STUDY)


def _absent() -> dict[ClientId, np.ndarray]:
    return {
        client: rows[~(MASKS["alpha"][rows] | MASKS["beta"][rows])][:BUDGET]
        for client, rows in ORDERS.items()
    }


def _peer() -> dict[ClientId, np.ndarray]:
    return {
        client: rows[
            ~(MASKS["alpha"][rows] if client is ClientId.ANZHI else np.zeros(rows.size, bool))
            & ~(MASKS["beta"][rows] if client is ClientId.APPCHINA else np.zeros(rows.size, bool))
        ][:BUDGET]
        for client, rows in ORDERS.items()
    }


def _rng() -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([SEED, 1]))


def _peer_count(rows: dict[ClientId, np.ndarray], pair: TargetPair) -> int:
    return sum(
        MASKS[pair.family][chosen].sum().item()
        for client, chosen in rows.items()
        if client is not pair.client
    )


def test_family_fit_rows_only_hold_named_malware_fit_rows_and_totals_cover_all_roles() -> None:
    roles = STUDY.table[Column.ROLE].to_numpy()
    assert all((roles[rows] == SplitRole.FIT).all() for by in FIT.values() for rows in by.values())
    assert design.family_totals(STUDY)["alpha"] == 4 * 3 * PER_CELL // 5


@pytest.mark.parametrize("dose", [0, 10, 25, 60])
def test_exact_dose_is_realised_at_peers_zero_at_target_and_volume_is_preserved(dose: int) -> None:
    absent = _absent()
    draw = design.draw_dose(FIT, absent, TARGETS, _rng())
    rows = design.substitute(
        absent, design.dose_extras(draw, TARGETS, dose), draw.replacement_order
    )
    for pair in TARGETS:
        assert _peer_count(rows, pair) == dose
        assert not MASKS[pair.family][rows[pair.client]].any()
    assert {client: chosen.size for client, chosen in rows.items()} == {
        client: chosen.size for client, chosen in absent.items()
    }
    assert all(np.unique(chosen).size == chosen.size for chosen in rows.values())
    roles = STUDY.table[Column.ROLE].to_numpy()
    assert all((roles[chosen] == SplitRole.FIT).all() for chosen in rows.values())


def test_dose_zero_reproduces_the_absent_rows_and_levels_are_nested() -> None:
    absent = _absent()
    draw = design.draw_dose(FIT, absent, TARGETS, _rng())
    zero = design.substitute(absent, design.dose_extras(draw, TARGETS, 0), draw.replacement_order)
    assert all(np.array_equal(zero[client], absent[client]) for client in ClientId)
    small = design.dose_extras(draw, TARGETS, 10)
    large = design.dose_extras(draw, TARGETS, 25)
    assert all(np.isin(small[client], large[client]).all() for client in ClientId)


def test_placebo_is_unhidden_unique_and_matches_the_hidden_family_counts() -> None:
    absent, peer = _absent(), _peer()
    choices = design.choose_placebos(
        FIT, design.family_totals(STUDY), MASKS, peer, absent, TARGETS, 10
    )
    placebos = [choice.placebo for choice in choices]
    assert len(set(placebos)) == len(placebos)
    assert not {"alpha", "beta"} & set(placebos)
    assert {(choice.client, choice.family) for choice in choices} == {
        (pair.client, pair.family) for pair in TARGETS
    }
    for choice in choices:
        pair = next(item for item in TARGETS if item.family == choice.family)
        assert choice.counts == {
            client: MASKS[pair.family][peer[client]].sum().item()
            for client in ClientId
            if client is not pair.client
        }
        assert choice.allocated == choice.counts
        assert choice.reallocated == 0
    rows = design.substitute(
        absent,
        design.placebo_extras(FIT, absent, choices, _rng()),
        {client: np.arange(chosen.size) for client, chosen in absent.items()},
    )
    for client in ClientId:
        added = np.setdiff1d(rows[client], absent[client])
        assert added.size == sum(choice.allocated.get(client, 0) for choice in choices)
        pools = [FIT[choice.placebo].get(client, np.empty(0, np.int64)) for choice in choices]
        assert np.isin(added, np.concatenate(pools)).all()
    assert {client: chosen.size for client, chosen in rows.items()} == {
        client: chosen.size for client, chosen in absent.items()
    }


def test_placebo_prefers_the_family_with_the_closest_peer_fit_count() -> None:
    absent, peer = _absent(), _peer()
    choices = design.choose_placebos(
        FIT, design.family_totals(STUDY), MASKS, peer, absent, TARGETS, 10
    )
    assert choices[0].hidden_peer_fit == choices[0].placebo_peer_fit


def test_placebo_rows_move_to_other_peers_when_a_peer_lacks_the_family() -> None:
    absent = _absent()
    scarce = {
        family: {
            client: rows[:1] if client is ClientId.PLAY_EARLY else rows
            for client, rows in by_client.items()
        }
        for family, by_client in FIT.items()
    }
    peer = {client: rows.copy() for client, rows in absent.items()}
    pair = TARGETS[0]
    hidden_rows = FIT[pair.family][ClientId.PLAY_EARLY][:5]
    peer[ClientId.PLAY_EARLY] = np.concatenate([peer[ClientId.PLAY_EARLY][:-5], hidden_rows])
    choices = design.choose_placebos(
        scarce, design.family_totals(STUDY), MASKS, peer, absent, (pair,), 10
    )
    choice = choices[0]
    assert choice.counts[ClientId.PLAY_EARLY] == 5
    assert choice.allocated[ClientId.PLAY_EARLY] <= 1
    assert sum(choice.allocated.values()) == sum(choice.counts.values())
    assert choice.reallocated == 5 - choice.allocated[ClientId.PLAY_EARLY]


def test_placebo_pairs_are_processed_from_the_largest_hidden_family() -> None:
    absent, peer = _absent(), _peer()
    choices = design.choose_placebos(
        FIT, design.family_totals(STUDY), MASKS, peer, absent, TARGETS, 10
    )
    fits = [choice.hidden_peer_fit for choice in choices]
    assert fits == sorted(fits, reverse=True)


def test_placebo_choice_fails_when_no_family_reaches_the_row_minimum() -> None:
    totals = design.family_totals(STUDY)
    peer, absent = _peer(), _absent()
    with pytest.raises(CtkError):
        design.choose_placebos(FIT, totals, MASKS, peer, absent, TARGETS, 10**6)
