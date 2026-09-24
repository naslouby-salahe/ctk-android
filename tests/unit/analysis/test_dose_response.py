import polars as pl
import pytest

from ctk_android.analysis.dose_response import dose_curve, dose_recall, effective_peer_dose
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    Learner,
)

ALPHA = 0.05
DOSES = (0, 10, 100, None)
HITS = {0: 10, 10: 30, 100: 60, None: 70}
TARGET = ClientId.ANZHI
PEER_ROWS = {0: 0, 10: 10, 100: 100, None: 240}


def _tag() -> dict[Column, object]:
    return {Column.EXPERIMENT: ExperimentName.PEER_DOSE_RESPONSE, Column.SEED: 100, Column.SALT: 0}


def _families() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                **_tag(),
                Column.LEARNER: Learner.FEDAVG,
                Column.CONDITION: ExposureCondition.PEER_PRESENT,
                Column.DOSE: dose,
                Column.CLIENT: TARGET,
                Column.ALPHA: ALPHA,
                Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
                Column.FAMILY: "alpha",
                Column.HITS: HITS[dose],
                Column.TRIALS: 100,
            }
            for dose in DOSES
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )


def _exposure() -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for dose in DOSES:
        for client in ClientId:
            rows.append(
                {
                    **_tag(),
                    Column.LEARNER: Learner.FEDAVG,
                    Column.CONDITION: ExposureCondition.PEER_PRESENT,
                    Column.DOSE: dose,
                    Column.CLIENT: client,
                    Column.FAMILY: "alpha",
                    Column.ROWS: 0 if client is TARGET else PEER_ROWS[dose] // 3,
                }
            )
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


def _curve() -> pl.DataFrame:
    families = _families()
    return dose_curve(
        dose_recall(families, ALPHA),
        effective_peer_dose(_exposure(), families.select(*_tag(), Column.CLIENT, Column.FAMILY)),
    )


def test_gain_is_measured_against_the_zero_dose_arm() -> None:
    curve = _curve()
    gains = {row[Column.DOSE]: row[Column.CTK_GAIN] for row in curve.iter_rows(named=True)}
    assert gains[0] == pytest.approx(0.0)
    assert gains[100] == pytest.approx(0.50)
    assert gains[None] == pytest.approx(0.60)


def test_effective_dose_counts_peer_rows_only() -> None:
    curve = _curve()
    effective = {
        row[Column.DOSE]: row[Column.EFFECTIVE_DOSE] for row in curve.iter_rows(named=True)
    }
    assert effective[0] == 0
    assert effective[100] == 99
    assert effective[None] == 240
