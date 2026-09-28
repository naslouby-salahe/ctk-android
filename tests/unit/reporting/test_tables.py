import polars as pl

from ctk_android.enums import Column, ExperimentName, FamilyOutcome
from ctk_android.reporting.tables import classify_families

POOR = 0.60


def _classes(full_recalls: dict[str, float | None]) -> dict[str, FamilyOutcome]:
    rescue = pl.DataFrame(
        {
            Column.EXPERIMENT: [ExperimentName.NATURAL_SCARCITY] * len(full_recalls),
            Column.LEARNER: ["fedavg"] * len(full_recalls),
            Column.FAMILY: list(full_recalls),
            Column.FULL_RECALL: pl.Series(list(full_recalls.values()), dtype=pl.Float64),
        }
    )
    table = classify_families(rescue, POOR)
    return dict(zip(table[Column.FAMILY], table[Column.CLASSIFICATION], strict=True))


def test_a_family_without_a_full_exposure_arm_is_not_called_rescued() -> None:
    classes = _classes({"alpha": None, "beta": 0.9, "gamma": 0.3})
    assert classes["alpha"] == FamilyOutcome.NOT_CLASSIFIABLE
    assert classes["beta"] == FamilyOutcome.RESCUED
    assert classes["gamma"] == FamilyOutcome.POORLY_RESCUED
