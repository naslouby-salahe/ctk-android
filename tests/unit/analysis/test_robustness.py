import polars as pl

from ctk_android.analysis.robustness import micro_ctk_by_seed
from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    Learner,
)

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
    raw = micro_ctk_by_seed(_families(), ALPHA, [])[Column.CTK_GAIN].item()
    unique = micro_ctk_by_seed(_families(), ALPHA, [], Column.UNIQUE_HITS, Column.UNIQUE_TRIALS)[
        Column.CTK_GAIN
    ].item()
    assert abs(raw - 0.60) < 1e-9
    assert abs(unique - 0.30) < 1e-9
