import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.dose_extension import (
    dose_consistency,
    dose_effects,
    dose_experiments,
    dose_family_curves,
    dose_verdicts,
)
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    ConsistencyMeasure,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExtensionContrast,
    ExtensionHypothesis,
    ExtensionScope,
    Learner,
)
from ctk_android.paths import Paths
from ctk_android.types import ExtensionEffectRow
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
EXPERIMENTS = dose_experiments(CONFIG, MODE)
ALPHA = CONFIG.experiments.operating.primary_alpha
LEVELS = CONFIG.experiments.exact_dose_levels
SEEDS = tuple(range(310, 320))
TRIALS = 200
FLAT_AFTER = 100
GAIN = {0: 0.0, 10: 0.05, 25: 0.12, 50: 0.2, 100: 0.3, 200: 0.3}
BASE = 0.3
TARGET = ClientId.ANZHI


def _hits(recall: float, seed: int, family: str, arm: int) -> int:
    wobble = ((seed * 11 + arm) % 7 - 3) * 0.006 + (len(family) % 2) * 0.003
    return round(np.clip(recall + wobble, 0.0, 1.0) * TRIALS)


def _families() -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for experiment in EXPERIMENTS:
        for seed in SEEDS:
            for family in ("f-one", "f-three"):
                arms = [
                    (Learner.FEDAVG, ExposureCondition.EXACT_DOSE, dose, BASE + gain)
                    for dose, gain in GAIN.items()
                ] + [
                    (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, None, BASE),
                    (Learner.FEDAVG, ExposureCondition.PEER_PRESENT, None, BASE + 0.25),
                ]
                for learner, condition, dose, recall in arms:
                    for population in (
                        EvaluationPopulation.FEDERATION_WIDE,
                        EvaluationPopulation.OWN_DOMAIN,
                    ):
                        rows.append(
                            {
                                Column.EXPERIMENT: experiment,
                                Column.SEED: seed,
                                Column.SALT: 0,
                                Column.CLIENT: TARGET,
                                Column.FAMILY: family,
                                Column.LEARNER: learner,
                                Column.CONDITION: condition,
                                Column.DOSE: dose,
                                Column.PARAMETER: None,
                                Column.TUNING_VALUE: None,
                                Column.ALPHA: ALPHA,
                                Column.POPULATION: population,
                                Column.HITS: _hits(
                                    recall, seed, family, -1 if dose is None else dose
                                ),
                                Column.TRIALS: TRIALS,
                            }
                        )
    return pl.DataFrame(
        rows,
        schema_overrides={
            Column.DOSE: pl.Int64,
            Column.PARAMETER: pl.String,
            Column.TUNING_VALUE: pl.Float64,
        },
    )


FAMILIES = _families()
EFFECTS = dose_effects(FAMILIES, CONFIG, EXPERIMENTS)


def _row(
    contrast: ExtensionContrast, level: int | None, scope: ExtensionScope = ExtensionScope.POOLED
):
    return next(
        row
        for row in EFFECTS.rows
        if row.contrast is contrast
        and row.level == level
        and row.scope is scope
        and row.population is EvaluationPopulation.FEDERATION_WIDE
    )


def test_experiments_are_the_two_family_set_variants_in_extension_b() -> None:
    assert set(EXPERIMENTS) == {
        ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY,
        ExperimentName.EXACT_EFFECTIVE_DOSE_REPLICATION,
    }


def test_ctk_at_dose_is_the_seed_paired_recall_difference_to_dose_zero() -> None:
    for level, gain in GAIN.items():
        if level:
            row = _row(ExtensionContrast.DOSE_CTK, level)
            assert row.seed_count == len(SEEDS)
            assert row.mean == pytest.approx(gain, abs=0.02)
    natural = _row(ExtensionContrast.NATURAL_CTK, None)
    assert natural.mean == pytest.approx(0.25, abs=0.02)


def test_onset_statements_use_one_sided_exact_wilcoxon_with_holm_over_six_levels() -> None:
    onset = [
        row
        for row in EFFECTS.rows
        if row.hypothesis is ExtensionHypothesis.DOSE_ONSET
        and row.scope is ExtensionScope.POOLED
        and row.population is EvaluationPopulation.FEDERATION_WIDE
    ]
    assert len(onset) == len(LEVELS)
    smallest = 1 / 2 ** len(SEEDS)
    assert all(row.p_value >= smallest - 1e-12 for row in onset)
    assert all(row.p_holm is not None and row.p_holm >= row.p_value for row in onset)
    assert max(row.p_holm or 0.0 for row in onset) <= 1.0


def test_saturation_is_equivalence_of_the_hundred_to_two_hundred_increment() -> None:
    row = _row(ExtensionContrast.INCREMENT_100_200, 200)
    assert row.hypothesis is ExtensionHypothesis.DOSE_SATURATION
    assert abs(row.mean) < CONFIG.statistics.gates.ctk_min_gain
    steep = _row(ExtensionContrast.INCREMENT_50_100, 100)
    assert steep.mean == pytest.approx(0.1, abs=0.02)
    assert not steep.within_band


def test_dose_zero_versus_absent_is_recorded_and_agrees() -> None:
    row = _row(ExtensionContrast.ZERO_VERSUS_ABSENT, 0)
    assert abs(row.mean) < CONFIG.statistics.gates.ctk_min_gain


def test_seed_effects_carry_one_row_per_seed_and_contrast() -> None:
    seeds = EFFECTS.seeds.filter(
        (pl.col(Column.CONTRAST) == ExtensionContrast.DOSE_CTK)
        & (pl.col(Column.LEVEL) == 50)
        & (pl.col(Column.SCOPE) == ExtensionScope.POOLED)
        & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    )
    assert sorted(seeds[Column.SEED].to_list()) == list(SEEDS)


def test_verdicts_report_onset_level_and_saturation_at_the_primary_alpha() -> None:
    verdicts = dose_verdicts(EFFECTS.rows, CONFIG).filter(
        (pl.col("scope") == ExtensionScope.POOLED)
        & (pl.col("population") == EvaluationPopulation.FEDERATION_WIDE)
    )
    onset = verdicts.filter(pl.col("hypothesis") == ExtensionHypothesis.DOSE_ONSET).row(
        0, named=True
    )
    assert onset["met"]
    assert onset["onset_level"] in LEVELS
    saturation = verdicts.filter(pl.col("hypothesis") == ExtensionHypothesis.DOSE_SATURATION)
    assert saturation["met"].to_list() == [True]


def test_family_curves_give_the_mean_gain_per_family_and_level() -> None:
    curves = dose_family_curves(FAMILIES, EXPERIMENTS)
    part = curves.filter(
        (pl.col(Column.FAMILY) == "f-one")
        & (pl.col(Column.DOSE) == FLAT_AFTER)
        & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    )
    assert part[Column.MEAN_CTK].to_list() == [pytest.approx(0.3, abs=0.02)] * len(EXPERIMENTS)


def _exposure(peer_rows: dict[int, int], target_rows: int, volume: int) -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for experiment in EXPERIMENTS:
        for seed in SEEDS:
            for level, peers in peer_rows.items():
                for client in ClientId:
                    rows.append(
                        {
                            Column.EXPERIMENT: experiment,
                            Column.SEED: seed,
                            Column.SALT: 0,
                            Column.LEARNER: Learner.FEDAVG,
                            Column.CONDITION: ExposureCondition.EXACT_DOSE,
                            Column.DOSE: level,
                            Column.CLIENT: client,
                            Column.FAMILY: "f-one",
                            Column.ROWS: target_rows if client is TARGET else peers // 3,
                            Column.TRAIN_ROWS: volume,
                        }
                    )
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


def _mismatches(table: pl.DataFrame, measure: ConsistencyMeasure) -> int:
    return table.filter(pl.col("measure") == measure)["mismatched"].to_numpy().sum().item()


def test_consistency_counts_realised_dose_target_rows_and_volume() -> None:
    families = FAMILIES.filter(pl.col(Column.FAMILY) == "f-one")
    clean = dose_consistency(_exposure({0: 0, 30: 30}, 0, 100), families, EXPERIMENTS)
    assert _mismatches(clean, ConsistencyMeasure.REALISED_DOSE) == 0
    assert _mismatches(clean, ConsistencyMeasure.TARGET_ZERO) == 0
    assert _mismatches(clean, ConsistencyMeasure.VOLUME) == 0
    off = dose_consistency(_exposure({0: 0, 30: 27}, 2, 100), families, EXPERIMENTS)
    assert _mismatches(off, ConsistencyMeasure.REALISED_DOSE) > 0
    assert _mismatches(off, ConsistencyMeasure.TARGET_ZERO) > 0


def test_onset_needs_family_macro_ctk_non_decreasing_across_exact_levels() -> None:
    def dip(row: ExtensionEffectRow) -> ExtensionEffectRow:
        if row.contrast is ExtensionContrast.DOSE_CTK and row.level == 50:
            return row.model_copy(update={"mean": 0.0})
        return row

    rows = tuple(dip(row) for row in EFFECTS.rows)
    verdicts = dose_verdicts(rows, CONFIG).filter(
        (pl.col("scope") == ExtensionScope.POOLED)
        & (pl.col("population") == EvaluationPopulation.FEDERATION_WIDE)
        & (pl.col("hypothesis") == ExtensionHypothesis.DOSE_ONSET)
    )
    assert verdicts["met"].to_list() == [False]
