import polars as pl

from ctk_android.config import TrainingConfig
from ctk_android.enums import Column, ExperimentName, Metric, TunedParameter
from ctk_android.types import (
    Alpha,
    FrozenHyperparameters,
    SelectionTable,
    SummaryTable,
    TuningValue,
)


def select_hyperparameters(summary: SummaryTable, alpha: Alpha) -> SelectionTable:
    grid = summary.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.BASELINE_FAIRNESS)
        & (pl.col(Column.METRIC) == Metric.CALIBRATION_AUROC)
        & (pl.col(Column.ALPHA) == alpha)
        & pl.col(Column.PARAMETER).is_not_null()
    )
    per_value = (
        grid.group_by(Column.PARAMETER, Column.TUNING_VALUE)
        .agg(
            pl.col(Column.VALUE).mean().alias(Column.CALIBRATION_AUROC),
            pl.col(Column.SEED).n_unique().alias(Column.SEED_COUNT),
        )
        .sort(
            [Column.PARAMETER, Column.CALIBRATION_AUROC, Column.TUNING_VALUE],
            descending=[False, True, False],
        )
    )
    return per_value.with_columns(
        (pl.int_range(pl.len()).over(Column.PARAMETER) == 0).alias(Column.SELECTED)
    )


def selected_value(selection: SelectionTable, parameter: TunedParameter) -> TuningValue:
    chosen = selection.filter((pl.col(Column.PARAMETER) == parameter) & pl.col(Column.SELECTED))
    return chosen[Column.TUNING_VALUE].item()


def frozen_hyperparameters(selection: SelectionTable) -> FrozenHyperparameters:
    return FrozenHyperparameters(
        local_epochs=selected_value(selection, TunedParameter.LOCAL_EPOCHS),
        finetune_epochs=selected_value(selection, TunedParameter.FINETUNE_EPOCHS),
        fedprox_mu=selected_value(selection, TunedParameter.FEDPROX_STRENGTH),
    )


def frozen_drift(selection: SelectionTable, training: TrainingConfig) -> list[TunedParameter]:
    chosen = frozen_hyperparameters(selection)
    configured = {
        TunedParameter.LOCAL_EPOCHS: (chosen.local_epochs, training.local_epochs),
        TunedParameter.FINETUNE_EPOCHS: (chosen.finetune_epochs, training.finetune_epochs),
        TunedParameter.FEDPROX_STRENGTH: (chosen.fedprox_mu, training.fedprox_mu),
    }
    return [parameter for parameter, (found, frozen) in configured.items() if found != frozen]
