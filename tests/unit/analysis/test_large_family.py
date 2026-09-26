import polars as pl
import pytest

from ctk_android.analysis.extensions import (
    eligibility_stability_summary,
    eligibility_stability_table,
    expected_ci_width,
    large_family_summary,
    large_family_table,
    large_seed_effects,
    stability_seed_table,
)
from ctk_android.config import load_config
from ctk_android.data.preparation import large_family_sets
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExposureCondition,
    LargeFamilyMeasure,
    Learner,
    NoveltyDescriptor,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
LARGE = CONFIG.experiments.extension_b_experiments[0]
SEEDS = (1, 2, 3)
FAMILIES = 6
TRIALS = 100
Z = 1.96


def _counts() -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for index in range(FAMILIES):
        for seed in SEEDS:
            for learner, condition, hits in (
                (Learner.FEDAVG, ExposureCondition.PEER_PRESENT, 50 + 8 * index),
                (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, 50),
                (Learner.LOCAL, ExposureCondition.PEER_PRESENT, 40),
            ):
                rows.append(
                    {
                        Column.EXPERIMENT: LARGE,
                        Column.SEED: seed,
                        Column.SALT: 0,
                        Column.CLIENT: ClientId.ANZHI,
                        Column.FAMILY: f"f{index}",
                        Column.LEARNER: learner,
                        Column.CONDITION: condition,
                        Column.ALPHA: ALPHA,
                        Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
                        Column.DOSE: None,
                        Column.HITS: hits,
                        Column.TRIALS: TRIALS,
                    }
                )
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


def _novelty() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: LARGE,
                Column.SEED: seed,
                Column.CLIENT: ClientId.ANZHI,
                Column.FAMILY: f"f{index}",
                Column.DESCRIPTOR: NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE,
                Column.VALUE: float(index),
            }
            for index in range(FAMILIES)
            for seed in SEEDS
        ]
    )


def test_family_ctk_is_peer_minus_family_absent_recall_averaged_over_seeds() -> None:
    effects = large_seed_effects(_counts(), CONFIG)
    table = large_family_table(effects, _novelty(), CONFIG)
    gains = dict(zip(table[Column.FAMILY], table[Column.CTK_GAIN], strict=True))
    assert gains["f0"] == pytest.approx(0.0)
    assert gains["f5"] == pytest.approx(0.40)
    assert set(table[Column.SEED_COUNT]) == {len(SEEDS)}
    flags = dict(zip(table[Column.FAMILY], table[Column.MEETS_THRESHOLD], strict=True))
    assert not flags["f0"]
    assert flags["f5"]


def test_summary_reports_rank_association_support_and_spread() -> None:
    effects = large_seed_effects(_counts(), CONFIG)
    table = large_family_table(effects, _novelty(), CONFIG)
    summary = large_family_summary(table, FAMILIES, CONFIG, effects)
    values = {
        row[Column.MEASURE]: row[Column.VALUE]
        for row in summary.filter(pl.col("assumed_rho").is_null()).iter_rows(named=True)
    }
    assert values[LargeFamilyMeasure.FAMILIES_DEFINED] == FAMILIES
    assert values[LargeFamilyMeasure.RHO] == pytest.approx(1.0)
    assert values[LargeFamilyMeasure.MIN_SUPPORT] == TRIALS
    assert values[LargeFamilyMeasure.FAMILIES_ABOVE_THRESHOLD] == FAMILIES - 1
    assert values[LargeFamilyMeasure.CTK_NOISE_SD] == pytest.approx(0.0)
    assert values[LargeFamilyMeasure.CTK_RELIABILITY] == pytest.approx(1.0)
    draws = CONFIG.statistics.bootstrap_resamples
    assert 1 / (1 + draws) <= values[LargeFamilyMeasure.RHO_PERMUTATION_P] < 0.05
    assert values[LargeFamilyMeasure.SEEDS_WITH_RHO] == len(SEEDS)
    assert values[LargeFamilyMeasure.SEED_RHO_MEDIAN] == pytest.approx(1.0)
    assert values[LargeFamilyMeasure.SEED_RHO_POSITIVE] == len(SEEDS)


def test_expected_interval_narrows_with_more_families_and_is_narrower_for_strong_rho() -> None:
    assert expected_ci_width(0.3, 40, Z) < expected_ci_width(0.3, 20, Z)
    assert expected_ci_width(0.7, 30, Z) < expected_ci_width(0.0, 30, Z)


def test_no_families_gives_an_empty_summary() -> None:
    assert large_family_summary(pl.DataFrame(), 0, CONFIG, pl.DataFrame()).height == 0


UNSTABLE = "f5"


def _selection() -> pl.DataFrame:
    batches = large_family_sets()
    return pl.DataFrame(
        {
            Column.RANK: list(range(FAMILIES)),
            Column.FAMILY: [f"f{index}" for index in range(FAMILIES)],
            Column.FAMILY_SET: [batches[index % len(batches)] for index in range(FAMILIES)],
        }
    )


def _pairs() -> dict[int, pl.DataFrame]:
    # Every family has one eligible and one ineligible pair, except UNSTABLE after the first seed.
    tables: dict[int, pl.DataFrame] = {}
    for seed in SEEDS:
        rows: list[dict[Column, object]] = []
        for index in range(FAMILIES):
            family = f"f{index}"
            for client, eligible in ((ClientId.ANZHI, True), (ClientId.APPCHINA, False)):
                rows.append(
                    {
                        Column.CLIENT: client,
                        Column.FAMILY: family,
                        Column.TARGET_TEST_ROWS: TRIALS,
                        Column.ELIGIBLE: eligible and (family != UNSTABLE or seed == SEEDS[0]),
                    }
                )
        tables[seed] = pl.DataFrame(rows)
    return tables


def test_stability_counts_seeds_in_which_each_frozen_family_is_eligible() -> None:
    per_seed = stability_seed_table(_pairs(), _selection())
    assert per_seed.height == FAMILIES * len(SEEDS)
    effects = large_seed_effects(_counts(), CONFIG)
    stability = eligibility_stability_table(per_seed, _selection(), effects)
    fraction = dict(zip(stability[Column.FAMILY], stability[Column.ELIGIBLE_FRACTION], strict=True))
    assert fraction[UNSTABLE] == pytest.approx(1 / len(SEEDS))
    assert fraction["f0"] == pytest.approx(1.0)
    assert stability.filter(pl.col(Column.STABLE)).height == FAMILIES - 1
    lowest = dict(zip(stability[Column.FAMILY], stability[Column.MIN_ELIGIBLE_PAIRS], strict=True))
    assert lowest[UNSTABLE] == 0
    assert set(stability[Column.MEASURED_SEEDS]) == {len(SEEDS)}


def test_stable_family_rho_is_a_labelled_sensitivity_that_leaves_the_frozen_result() -> None:
    effects = large_seed_effects(_counts(), CONFIG)
    table = large_family_table(effects, _novelty(), CONFIG)
    frozen = large_family_summary(table, FAMILIES, CONFIG, effects)
    stability = eligibility_stability_table(
        stability_seed_table(_pairs(), _selection()), _selection(), effects
    )
    summary = eligibility_stability_summary(stability, table, CONFIG)
    values = dict(zip(summary[Column.MEASURE], summary[Column.VALUE], strict=True))
    assert values[LargeFamilyMeasure.STABLE_FAMILIES] == FAMILIES - 1
    assert values[LargeFamilyMeasure.STABLE_RHO] == pytest.approx(1.0)
    assert LargeFamilyMeasure.RHO not in values
    assert large_family_summary(table, FAMILIES, CONFIG, effects).equals(frozen)


def test_no_fresh_seed_partitions_give_an_empty_stability_table() -> None:
    assert stability_seed_table({}, _selection()).height == 0
