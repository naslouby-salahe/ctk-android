import polars as pl

from ctk_android.analysis.post_confirmatory import (
    anchored_client_selection,
    anchored_worst_client,
    ctk_robustness_synthesis,
    federated_arm_tradeoff,
)
from ctk_android.analysis.robustness import robustness_table
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    CtkAggregation,
    Estimand,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    Learner,
    Metric,
    TradeoffComparison,
    TradeoffMeasure,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
PEER = ExposureCondition.PEER_PRESENT
ABSENT = ExposureCondition.FAMILY_ABSENT_EVERYWHERE
FULL = ExposureCondition.FULL_EXPOSURE
WORSE, BETTER = ClientId.ANZHI, ClientId.APPCHINA
RECALLS = {
    (Learner.LOCAL, PEER): {WORSE: 0.2, BETTER: 0.5},
    (Learner.FEDAVG, PEER): {WORSE: 0.5, BETTER: 0.3},
    (Learner.FEDAVG, ABSENT): {WORSE: 0.3, BETTER: 0.9},
    (Learner.CENTRAL, PEER): {WORSE: 0.5, BETTER: 0.3},
    (Learner.CENTRAL, ABSENT): {WORSE: 0.3, BETTER: 0.9},
    (Learner.CENTRAL, FULL): {WORSE: 0.6, BETTER: 0.9},
}


def _clients() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
                Column.SEED: seed,
                Column.SALT: 0,
                Column.LEARNER: learner,
                Column.CONDITION: condition,
                Column.DOSE: None,
                Column.ALPHA: ALPHA,
                Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
                Column.CLIENT: client,
                Column.HITS: round(recall * 100),
                Column.TRIALS: 100,
            }
            for seed in range(100, 104)
            for (learner, condition), by_client in RECALLS.items()
            for client, recall in by_client.items()
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def _value(table: pl.DataFrame, learner: Learner, estimand: Estimand) -> float:
    row = table.filter((pl.col(Column.LEARNER) == learner) & (pl.col(Column.ESTIMAND) == estimand))
    return row[Column.MEAN_DIFFERENCE].item()


def test_the_worst_client_is_frozen_under_the_local_baseline_and_followed_across_arms() -> None:
    table = anchored_worst_client(_clients(), CONFIG)
    assert abs(_value(table, Learner.FEDAVG, Estimand.CTK_GAIN) - 0.2) < 1e-9
    assert abs(_value(table, Learner.FEDAVG, Estimand.TOTAL_GAIN) - 0.3) < 1e-9
    assert abs(_value(table, Learner.FEDAVG, Estimand.POOLING_GAIN) - 0.1) < 1e-9
    selection = anchored_client_selection(_clients(), CONFIG)
    assert selection[Column.CLIENT].to_list() == [WORSE]
    assert selection[Column.SEEDS_SELECTED].to_list() == [4]


def _summary_rows() -> pl.DataFrame:
    values = {
        (Learner.LOCAL, PEER, Metric.KNOWN_FAMILY_RECALL): 0.72,
        (Learner.FEDAVG, PEER, Metric.KNOWN_FAMILY_RECALL): 0.68,
        (Learner.FEDPROX, PEER, Metric.KNOWN_FAMILY_RECALL): 0.715,
    }
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
                Column.SEED: seed,
                Column.LEARNER: learner,
                Column.CONDITION: condition,
                Column.DOSE: None,
                Column.ALPHA: ALPHA,
                Column.METRIC: metric,
                Column.VALUE: value + seed * 1e-4,
            }
            for seed in range(100, 104)
            for (learner, condition, metric), value in values.items()
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def test_arm_specific_known_family_tolerance_is_reported_per_arm() -> None:
    table = federated_arm_tradeoff(_summary_rows(), CONFIG).filter(
        (pl.col(Column.MEASURE) == TradeoffMeasure.KNOWN_FAMILY_RECALL_CHANGE)
        & (pl.col(Column.COMPARISON) == TradeoffComparison.VERSUS_LOCAL)
    )
    tolerance = dict(zip(table[Column.LEARNER], table["within_tolerance"], strict=True))
    assert tolerance[Learner.FEDAVG] is False
    assert tolerance[Learner.FEDPROX] is True


def _families() -> pl.DataFrame:
    def row(condition: ExposureCondition, hits: int, seed: int) -> dict[Column, object]:
        return {
            Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
            Column.SEED: seed,
            Column.SALT: 0,
            Column.LEARNER: Learner.FEDAVG,
            Column.CONDITION: condition,
            Column.DOSE: None,
            Column.ALPHA: ALPHA,
            Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
            Column.FAMILY: "alpha",
            Column.HITS: hits,
            Column.TRIALS: 100,
            Column.UNIQUE_HITS: hits,
            Column.UNIQUE_TRIALS: 100,
        }

    return pl.DataFrame(
        [
            row(condition, hits + seed, seed)
            for seed in range(4)
            for condition, hits in ((PEER, 80), (ABSENT, 40))
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def test_the_synthesis_labels_micro_pooled_and_paired_estimands_separately() -> None:
    micro = robustness_table(_families(), CONFIG)
    synthesis = ctk_robustness_synthesis(pl.DataFrame(), micro, CONFIG)
    assert set(synthesis[Column.AGGREGATION]) == {CtkAggregation.MICRO_POOLED}
    assert synthesis[Column.METRIC].null_count() == synthesis.height
