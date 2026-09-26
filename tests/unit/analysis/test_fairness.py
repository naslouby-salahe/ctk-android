import polars as pl

from ctk_android.analysis.post_confirmatory import (
    frozen_drift,
    frozen_hyperparameters,
    select_hyperparameters,
)
from ctk_android.config import load_config
from ctk_android.enums import Column, ExperimentName, Metric, TunedParameter
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
SEEDS = (1, 2, 3)


def _rows(
    parameter: TunedParameter,
    values: dict[float, float],
    metric: Metric = Metric.CALIBRATION_AUROC,
    experiment: ExperimentName = ExperimentName.BASELINE_FAIRNESS,
) -> list[dict[Column, object]]:
    return [
        {
            Column.EXPERIMENT: experiment,
            Column.SEED: seed,
            Column.PARAMETER: parameter,
            Column.TUNING_VALUE: level,
            Column.METRIC: metric,
            Column.ALPHA: ALPHA,
            Column.VALUE: score,
        }
        for level, score in values.items()
        for seed in SEEDS
    ]


def _summary(rows: list[dict[Column, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows)


def _chosen(selection: pl.DataFrame, parameter: TunedParameter) -> float:
    return selection.filter((pl.col(Column.PARAMETER) == parameter) & pl.col(Column.SELECTED))[
        Column.TUNING_VALUE
    ].item()


def test_the_best_mean_calibration_auroc_is_selected_per_parameter() -> None:
    rows = _rows(TunedParameter.LOCAL_EPOCHS, {10: 0.93, 20: 0.92, 40: 0.91})
    rows += _rows(TunedParameter.FEDPROX_STRENGTH, {0.001: 0.90, 0.01: 0.94, 0.1: 0.93})
    selection = select_hyperparameters(_summary(rows), ALPHA)
    assert _chosen(selection, TunedParameter.LOCAL_EPOCHS) == 10
    assert _chosen(selection, TunedParameter.FEDPROX_STRENGTH) == 0.01
    assert selection.filter(pl.col(Column.SELECTED)).height == 2


def test_ties_go_to_the_smaller_value() -> None:
    rows = _rows(TunedParameter.FINETUNE_EPOCHS, {2: 0.9, 5: 0.9, 10: 0.9})
    selection = select_hyperparameters(_summary(rows), ALPHA)
    assert _chosen(selection, TunedParameter.FINETUNE_EPOCHS) == 2


def test_test_split_metrics_and_other_experiments_never_influence_selection() -> None:
    rows = _rows(TunedParameter.LOCAL_EPOCHS, {10: 0.90, 20: 0.91})
    rows += _rows(TunedParameter.LOCAL_EPOCHS, {10: 0.99, 20: 0.10}, metric=Metric.AUROC)
    rows += _rows(
        TunedParameter.LOCAL_EPOCHS,
        {10: 0.0, 20: 1.0},
        experiment=ExperimentName.CONTROLLED_EXPOSURE,
    )
    selection = select_hyperparameters(_summary(rows), ALPHA)
    assert _chosen(selection, TunedParameter.LOCAL_EPOCHS) == 20


def test_the_configured_hyperparameters_are_reported_as_drift_when_they_differ() -> None:
    rows = _rows(TunedParameter.LOCAL_EPOCHS, {10: 0.9, 20: 0.8})
    rows += _rows(TunedParameter.FINETUNE_EPOCHS, {2: 0.9, 5: 0.8})
    rows += _rows(TunedParameter.FEDPROX_STRENGTH, {0.01: 0.9, 0.1: 0.8})
    selection = select_hyperparameters(_summary(rows), ALPHA)
    chosen = frozen_hyperparameters(selection)
    assert (chosen.local_epochs, chosen.finetune_epochs, chosen.fedprox_mu) == (10, 2, 0.01)
    drift = frozen_drift(selection, CONFIG.experiments.training)
    assert TunedParameter.FEDPROX_STRENGTH in drift
    assert TunedParameter.LOCAL_EPOCHS not in drift
