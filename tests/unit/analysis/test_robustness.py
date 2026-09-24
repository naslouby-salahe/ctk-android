import polars as pl

from ctk_android.analysis.robustness import micro_ctk_by_seed, robustness_table
from ctk_android.config import load_config
from ctk_android.enums import (
    Column,
    CtkAggregation,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    Learner,
    Sensitivity,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

ALPHA = 0.05


def _row(condition: ExposureCondition, hits: int, trials: int, unique_hits: int, unique: int):
    return {
        Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
        Column.SEED: 100,
        Column.SALT: 0,
        Column.LEARNER: Learner.FEDAVG,
        Column.CONDITION: condition,
        Column.DOSE: None,
        Column.ALPHA: ALPHA,
        Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
        Column.FAMILY: "alpha",
        Column.HITS: hits,
        Column.TRIALS: trials,
        Column.UNIQUE_HITS: unique_hits,
        Column.UNIQUE_TRIALS: unique,
    }


def _families() -> pl.DataFrame:
    return pl.DataFrame(
        [
            _row(ExposureCondition.PEER_PRESENT, 90, 100, 5, 10),
            _row(ExposureCondition.FAMILY_ABSENT_EVERYWHERE, 30, 100, 2, 10),
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def test_raw_and_deduplicated_gains_use_their_own_counts() -> None:
    raw = micro_ctk_by_seed(_families(), ALPHA, [])[Column.MICRO_POOLED_CTK_GAIN].item()
    unique = micro_ctk_by_seed(_families(), ALPHA, [], Column.UNIQUE_HITS, Column.UNIQUE_TRIALS)[
        Column.MICRO_POOLED_CTK_GAIN
    ].item()
    assert abs(raw - 0.60) < 1e-9
    assert abs(unique - 0.30) < 1e-9


def test_the_micro_pooled_gain_has_its_own_name_and_never_the_paired_seed_name() -> None:
    config = load_config(Paths(REPO_ROOT))
    seeds = [
        _families().with_columns(pl.lit(seed).cast(pl.Int32).alias(Column.SEED))
        for seed in range(4)
    ]
    frame = pl.concat(seeds).with_columns(
        pl.when(pl.col(Column.SEED) == 0)
        .then(pl.col(Column.HITS))
        .otherwise(pl.col(Column.HITS) - 5)
        .alias(Column.HITS)
    )
    table = robustness_table(frame, config)
    assert Column.MICRO_POOLED_CTK_GAIN in table.columns
    assert Column.MEAN_DIFFERENCE not in table.columns
    assert set(table[Column.AGGREGATION]) == {CtkAggregation.MICRO_POOLED}


def test_partition_salts_are_reported_separately_never_pooled_as_extra_seeds() -> None:
    config = load_config(Paths(REPO_ROOT))
    frame = pl.concat(
        [
            _families().with_columns(
                pl.lit(seed).cast(pl.Int32).alias(Column.SEED),
                pl.lit(salt).cast(pl.Int32).alias(Column.SALT),
                pl.lit(ExperimentName.PARTITION_SALT_SENSITIVITY).alias(Column.EXPERIMENT),
            )
            for seed in range(4)
            for salt in (1, 2, 3)
        ]
    )
    table = robustness_table(frame, config).filter(
        pl.col(Column.SENSITIVITY) == Sensitivity.ALL_FAMILIES
    )
    assert sorted(table[Column.SALT].to_list()) == [1, 2, 3]
    assert set(table[Column.SEED_COUNT]) == {4}
