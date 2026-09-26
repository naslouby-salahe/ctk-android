import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.extensions import (
    controls_effects,
    controls_experiments,
    controls_verdicts,
    placebo_table,
)
from ctk_android.config import load_config
from ctk_android.enums import (
    Aggregation,
    ClientId,
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExtensionContrast,
    ExtensionHypothesis,
    ExtensionScope,
    Learner,
    TunedParameter,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
EXPERIMENTS = controls_experiments(CONFIG, MODE)
ALPHA = CONFIG.experiments.operating.primary_alpha
SEEDS = tuple(range(320, 330))
TRIALS = 200
MARGIN = CONFIG.statistics.gates.ctk_min_gain
ABSENT = 0.3
PEER = 0.5
PLACEBO = 0.305
TRIMMED = (0.29, 0.49)
MEDIAN = (0.29, 0.48)


def _hits(recall: float, seed: int, arm: int) -> int:
    wobble = ((seed * 11 + arm) % 7 - 3) * 0.004
    return round(np.clip(recall + wobble, 0.0, 1.0) * TRIALS)


def _rows(scale: float = 1.0) -> pl.DataFrame:
    arms = [
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, None, ABSENT),
        (ExposureCondition.PEER_PRESENT, None, PEER),
        (ExposureCondition.PLACEBO, None, PLACEBO),
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Aggregation.TRIMMED_MEAN, TRIMMED[0]),
        (ExposureCondition.PEER_PRESENT, Aggregation.TRIMMED_MEAN, TRIMMED[1]),
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Aggregation.COORDINATE_MEDIAN, MEDIAN[0]),
        (ExposureCondition.PEER_PRESENT, Aggregation.COORDINATE_MEDIAN, MEDIAN[1]),
    ]
    rows: list[dict[Column, object]] = []
    for experiment in EXPERIMENTS:
        for seed in SEEDS:
            for family in ("f-one", "f-two"):
                for index, (condition, rule, recall) in enumerate(arms):
                    for population in (
                        EvaluationPopulation.FEDERATION_WIDE,
                        EvaluationPopulation.OWN_DOMAIN,
                    ):
                        rows.append(
                            {
                                Column.EXPERIMENT: experiment,
                                Column.SEED: seed,
                                Column.SALT: 0,
                                Column.CLIENT: ClientId.ANZHI,
                                Column.FAMILY: family,
                                Column.LEARNER: Learner.FEDAVG,
                                Column.CONDITION: condition,
                                Column.DOSE: None,
                                Column.PARAMETER: None
                                if rule is None
                                else TunedParameter.AGGREGATION,
                                Column.TUNING_VALUE: None if rule is None else float(rule),
                                Column.ALPHA: ALPHA,
                                Column.POPULATION: population,
                                Column.HITS: _hits(recall * scale, seed, index),
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


EFFECTS = controls_effects(_rows(), CONFIG, EXPERIMENTS)


def _row(contrast: ExtensionContrast, scope: ExtensionScope = ExtensionScope.POOLED):
    return next(
        row
        for row in EFFECTS.rows
        if row.contrast is contrast
        and row.scope is scope
        and row.population is EvaluationPopulation.FEDERATION_WIDE
    )


def test_experiments_are_the_two_family_set_variants() -> None:
    assert set(EXPERIMENTS) == {
        ExperimentName.PLACEBO_ROBUST_PRIMARY,
        ExperimentName.PLACEBO_ROBUST_REPLICATION,
    }


def test_estimands_are_seed_paired_arm_differences() -> None:
    assert _row(ExtensionContrast.CTK_MEAN).mean == pytest.approx(PEER - ABSENT, abs=0.02)
    assert _row(ExtensionContrast.PLACEBO_EFFECT).mean == pytest.approx(PLACEBO - ABSENT, abs=0.02)
    assert _row(ExtensionContrast.CTK_MINUS_PLACEBO).mean == pytest.approx(PEER - PLACEBO, abs=0.02)
    assert _row(ExtensionContrast.CTK_TRIMMED).mean == pytest.approx(
        TRIMMED[1] - TRIMMED[0], abs=0.02
    )
    assert _row(ExtensionContrast.CTK_MEDIAN).mean == pytest.approx(MEDIAN[1] - MEDIAN[0], abs=0.02)
    assert _row(ExtensionContrast.TRIMMED_MINUS_MEAN).mean == pytest.approx(
        (TRIMMED[1] - TRIMMED[0]) - (PEER - ABSENT), abs=0.02
    )
    assert _row(ExtensionContrast.MEDIAN_MINUS_MEAN).seed_count == len(SEEDS)


def test_placebo_specificity_uses_the_equivalence_band_and_the_margin_test() -> None:
    placebo = _row(ExtensionContrast.PLACEBO_EFFECT)
    assert placebo.hypothesis is ExtensionHypothesis.PLACEBO
    assert placebo.within_band
    beyond = _row(ExtensionContrast.CTK_MINUS_PLACEBO)
    assert beyond.above_margin
    assert beyond.null_reference == MARGIN


def test_robust_aggregation_is_holm_adjusted_across_the_two_aggregators_only() -> None:
    trimmed, median = (_row(ExtensionContrast.CTK_TRIMMED), _row(ExtensionContrast.CTK_MEDIAN))
    assert trimmed.p_holm is not None and median.p_holm is not None
    assert trimmed.p_holm >= trimmed.p_value
    assert _row(ExtensionContrast.CTK_MEAN).p_holm is None
    assert _row(ExtensionContrast.PLACEBO_EFFECT).p_holm is None
    for contrast in (ExtensionContrast.TRIMMED_MINUS_MEAN, ExtensionContrast.MEDIAN_MINUS_MEAN):
        assert _row(contrast).null_reference == -MARGIN
        assert _row(contrast).p_holm is not None


def test_verdicts_meet_both_hypotheses_when_placebo_is_null_and_aggregation_is_robust() -> None:
    verdicts = controls_verdicts(EFFECTS.rows, CONFIG).filter(
        (pl.col("scope") == ExtensionScope.POOLED)
        & (pl.col("population") == EvaluationPopulation.FEDERATION_WIDE)
    )
    assert verdicts["met"].to_list() == [True, True]


def test_a_dominant_placebo_effect_leaves_specificity_unmet() -> None:
    families = _rows().with_columns(
        pl.when(pl.col(Column.CONDITION) == ExposureCondition.PLACEBO)
        .then(pl.col(Column.HITS) + 30)
        .otherwise(pl.col(Column.HITS))
        .alias(Column.HITS)
    )
    effects = controls_effects(families, CONFIG, EXPERIMENTS)
    verdicts = controls_verdicts(effects.rows, CONFIG).filter(
        (pl.col("scope") == ExtensionScope.POOLED)
        & (pl.col("population") == EvaluationPopulation.FEDERATION_WIDE)
        & (pl.col("hypothesis") == ExtensionHypothesis.PLACEBO)
    )
    assert verdicts["met"].to_list() == [False]


def test_placebo_pairs_are_sorted_by_run_and_family() -> None:
    frame = pl.DataFrame(
        {
            Column.EXPERIMENT: ["b", "a", "a"],
            Column.SEED: [1, 2, 1],
            Column.FAMILY: ["x", "x", "z"],
        }
    )
    ordered = placebo_table(frame)
    assert ordered[Column.FAMILY].to_list() == ["z", "x", "x"]
    assert placebo_table(pl.DataFrame()).height == 0
