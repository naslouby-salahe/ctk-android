import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.decomposition import decompose
from ctk_android.analysis.statistics import paired_effect_table
from ctk_android.config import load_config
from ctk_android.enums import (
    Column,
    ContrastFamily,
    Estimand,
    ExperimentName,
    ExposureCondition,
    Learner,
    Metric,
)
from ctk_android.paths import Paths
from ctk_android.types import EffectRow
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
SEEDS = range(100, 110)
RNG = np.random.default_rng(3)


def _summary() -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for seed in SEEDS:
        base = {
            (Learner.LOCAL, ExposureCondition.PEER_PRESENT): 0.10,
            (Learner.CENTRAL, ExposureCondition.PEER_PRESENT): 0.60,
            (Learner.CENTRAL, ExposureCondition.FAMILY_ABSENT_EVERYWHERE): 0.35,
            (Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE): 0.70,
            (Learner.FEDAVG, ExposureCondition.PEER_PRESENT): 0.50,
            (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE): 0.30,
        }
        for (learner, condition), value in base.items():
            rows.append(
                {
                    Column.EXPERIMENT: ExperimentName.CONTROLLED_EXPOSURE,
                    Column.SEED: seed,
                    Column.SALT: 0,
                    Column.LEARNER: learner,
                    Column.CONDITION: condition,
                    Column.DOSE: None,
                    Column.ALPHA: ALPHA,
                    Column.METRIC: Metric.FEDERATION_UNSEEN_RECALL,
                    Column.VALUE: value + RNG.normal(0.0, 0.01),
                }
            )
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


TABLE = paired_effect_table(decompose(_summary()), CONFIG)


def _row(learner: Learner, estimand: Estimand) -> EffectRow:
    rows = TABLE.filter((pl.col(Column.LEARNER) == learner) & (pl.col(Column.ESTIMAND) == estimand))
    return EffectRow.model_validate(rows.row(0, named=True))


def test_primary_family_is_the_fedavg_trio_with_holm_adjustment() -> None:
    primary = TABLE.filter(pl.col(Column.CONTRAST_FAMILY) == ContrastFamily.PRIMARY)
    assert primary.height == 3
    assert primary[Column.P_HOLM].null_count() == 0
    assert (primary[Column.P_HOLM] >= primary[Column.P_VALUE]).all()


def test_central_contrasts_form_the_reference_family() -> None:
    reference = TABLE.filter(pl.col(Column.CONTRAST_FAMILY) == ContrastFamily.REFERENCE)
    assert reference.height == 3


def test_ctk_effect_counts_every_positive_seed_and_has_an_interval() -> None:
    row = _row(Learner.FEDAVG, Estimand.CTK_GAIN)
    assert row.mean_difference == pytest.approx(0.20, abs=0.02)
    assert row.positive_seeds == len(SEEDS)
    assert row.ci_low is not None
    assert row.ci_low > 0


def test_shares_are_ratios_of_seed_means() -> None:
    ctk = _row(Learner.FEDAVG, Estimand.CTK_SHARE)
    pooling = _row(Learner.FEDAVG, Estimand.POOLING_SHARE)
    assert ctk.mean_difference == pytest.approx(0.20 / 0.40, abs=0.05)
    assert ctk.mean_difference + pooling.mean_difference == pytest.approx(1.0)
