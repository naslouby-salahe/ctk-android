import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.post_confirmatory import (
    aggregate_metric_masking,
    ctk_heterogeneity_components,
    hidden_cells,
    negative_transfer_decomposition,
)
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    IntervalVerdict,
    Learner,
    MaskingContrast,
    Metric,
    OperatingPointStatus,
    TransferScope,
    VarianceComponent,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

BASE = load_config(Paths(REPO_ROOT))
CONFIG = BASE.model_copy(
    update={
        "statistics": BASE.statistics.model_copy(update={"cluster_bootstrap_resamples": 20}),
    }
)
ALPHA = CONFIG.experiments.operating.primary_alpha
CE = ExperimentName.CONTROLLED_EXPOSURE
PEER = ExposureCondition.PEER_PRESENT
ABSENT = ExposureCondition.FAMILY_ABSENT_EVERYWHERE
OWN = EvaluationPopulation.OWN_DOMAIN
SEEDS = range(100, 106)


def _counts(cases: dict[tuple[ClientId, str], tuple[int, int, int]]) -> pl.DataFrame:
    rows = [
        {
            Column.EXPERIMENT: CE,
            Column.SEED: seed,
            Column.SALT: 0,
            Column.LEARNER: learner,
            Column.CONDITION: condition,
            Column.DOSE: None,
            Column.ALPHA: ALPHA,
            Column.POPULATION: OWN,
            Column.CLIENT: client,
            Column.FAMILY: family,
            Column.HITS: hits,
            Column.TRIALS: 100,
        }
        for (client, family), (local, absent, peer) in cases.items()
        for seed in SEEDS
        for learner, condition, hits in (
            (Learner.LOCAL, PEER, local + seed % 3),
            (Learner.FEDAVG, ABSENT, absent + seed % 3),
            (Learner.FEDAVG, PEER, peer + seed % 3),
        )
    ]
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


def _cell(frame: pl.DataFrame, client: ClientId, family: str) -> dict[str, float]:
    return frame.filter((pl.col(Column.CLIENT) == client) & (pl.col(Column.FAMILY) == family)).row(
        0, named=True
    )


def test_ctk_splits_into_repair_new_capability_and_harm() -> None:
    cases = {
        (ClientId.ANZHI, "degraded-then-repaired"): (50, 30, 70),
        (ClientId.ANZHI, "pooling-helps-then-peer-helps"): (50, 60, 80),
        (ClientId.ANZHI, "peer-hurts"): (50, 60, 40),
        (ClientId.ANZHI, "partial-repair"): (50, 30, 40),
    }
    cells = hidden_cells(_counts(cases), ALPHA)
    for client, family in cases:
        row = _cell(cells, client, family)
        assert row[Column.REPAIR] + row[Column.NEW_CAPABILITY] + row[Column.CTK_HARM] == (
            pytest.approx(row[Column.CTK_GAIN])
        )
    repaired = _cell(cells, ClientId.ANZHI, "degraded-then-repaired")
    assert repaired[Column.REPAIR] == pytest.approx(0.2)
    assert repaired[Column.NEW_CAPABILITY] == pytest.approx(0.2)
    helped = _cell(cells, ClientId.ANZHI, "pooling-helps-then-peer-helps")
    assert helped[Column.REPAIR] == pytest.approx(0.0)
    assert helped[Column.NEW_CAPABILITY] == pytest.approx(0.2)
    hurt = _cell(cells, ClientId.ANZHI, "peer-hurts")
    assert hurt[Column.CTK_HARM] == pytest.approx(-0.2)
    assert hurt[Column.REPAIR] == pytest.approx(0.0)
    partial = _cell(cells, ClientId.ANZHI, "partial-repair")
    assert partial[Column.REPAIR] == pytest.approx(0.1)
    assert partial[Column.NEW_CAPABILITY] == pytest.approx(0.0)


def test_negative_transfer_flags_the_client_where_pooling_falls_below_local() -> None:
    cases = {
        (ClientId.ANZHI, "a"): (50, 30, 70),
        (ClientId.ANZHI, "b"): (50, 35, 60),
        (ClientId.APPCHINA, "a"): (40, 50, 70),
        (ClientId.APPCHINA, "b"): (40, 55, 60),
    }
    table = negative_transfer_decomposition(hidden_cells(_counts(cases), ALPHA), CONFIG)
    by_client = table.filter(pl.col("scope") == TransferScope.CLIENT).sort(Column.CLIENT)
    assert by_client["hurts"].to_list() == [True, False]
    assert by_client["hurt_seeds"].to_list() == [len(SEEDS), 0]
    assert by_client["client"].to_list() == [ClientId.ANZHI, ClientId.APPCHINA]
    assert by_client["family"].null_count() == 2
    overall = table.filter(pl.col("scope") == TransferScope.OVERALL)
    assert overall["observations"].item() == 4 * len(SEEDS)
    assert 0.0 <= overall["repair_share"].item() <= 1.0


def _cell_frame(rng: np.random.Generator) -> pl.DataFrame:
    client_effect = {ClientId.ANZHI: 0.0, ClientId.APPCHINA: 0.2, ClientId.PLAY_EARLY: 0.4}
    rows = [
        {
            Column.EXPERIMENT: CE,
            Column.POPULATION: OWN,
            Column.SEED: seed,
            Column.CLIENT: client,
            Column.FAMILY: family,
            Column.CTK_GAIN: effect + rng.normal(scale=0.01),
            Column.PEER_RECALL: 0.5,
            Column.ABSENT_RECALL: 0.5,
            Column.TRIALS: 100,
        }
        for client, effect in client_effect.items()
        for family in ("a", "b", "c")
        for seed in SEEDS
    ]
    return pl.DataFrame(rows)


def test_a_pure_client_effect_puts_the_variance_on_the_client_component() -> None:
    table = ctk_heterogeneity_components(_cell_frame(np.random.default_rng(0)), CONFIG)
    shares = dict(zip(table["component"], table["share"], strict=True))
    assert shares[VarianceComponent.CLIENT] > 0.9
    assert sum(shares.values()) == pytest.approx(1.0)
    assert table["observations"].unique().to_list() == [54]
    assert table["replicated_cells"].unique().to_list() == [9]
    assert (table["share_ci_low"] <= table["share_ci_high"]).all()


def _summary(recall_gain: float) -> pl.DataFrame:
    def row(
        learner: Learner, condition: ExposureCondition, metric: Metric, seed: int, value: float
    ) -> dict[Column, object]:
        return {
            Column.EXPERIMENT: CE,
            Column.SEED: seed,
            Column.SALT: 0,
            Column.LEARNER: learner,
            Column.CONDITION: condition,
            Column.DOSE: None,
            Column.ALPHA: ALPHA,
            Column.METRIC: metric,
            Column.VALUE: value,
            Column.OPERATING_STATUS: OperatingPointStatus.VALID,
        }

    rows = [
        row(learner, condition, metric, seed, value)
        for seed in SEEDS
        for learner, condition, lift in (
            (Learner.LOCAL, PEER, 0.0),
            (Learner.FEDAVG, PEER, recall_gain + 0.005 * (seed - SEEDS[0])),
            (Learner.FEDAVG, ABSENT, 0.0),
        )
        for metric, value in (
            (Metric.AUROC, 0.90 + 0.001 * seed),
            (Metric.OWN_DOMAIN_UNSEEN_RECALL, 0.30 + lift),
        )
    ]
    return pl.DataFrame(rows, schema_overrides={Column.DOSE: pl.Int64})


def test_a_flat_aggregate_metric_masks_a_material_hidden_family_gain() -> None:
    table = aggregate_metric_masking(_summary(0.10), CONFIG)
    row = table.filter(
        (pl.col("learner") == Learner.FEDAVG)
        & (pl.col("contrast") == MaskingContrast.PEER_VERSUS_LOCAL)
        & (pl.col("aggregate_metric") == Metric.AUROC)
        & (pl.col("recall_metric") == Metric.OWN_DOMAIN_UNSEEN_RECALL)
    )
    assert row["seed_count"].item() == len(SEEDS)
    assert row["aggregate_verdict"].item() == IntervalVerdict.INCONCLUSIVE
    assert row["recall_verdict"].item() == IntervalVerdict.POSITIVE
    assert row["masked_gain"].item()
    assert not row["masked_loss"].item()
    assert row["gain_missed_seeds"].item() == len(SEEDS)
    assert row["false_reassurance_seeds"].item() == 0


def test_no_masking_is_reported_when_the_hidden_family_gain_is_immaterial() -> None:
    table = aggregate_metric_masking(_summary(0.0), CONFIG)
    assert not table["masked_gain"].any()
    assert table["gain_missed_seeds"].to_numpy().max() < len(SEEDS)
