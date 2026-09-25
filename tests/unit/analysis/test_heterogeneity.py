import polars as pl
import pytest

from ctk_android.analysis.heterogeneity import (
    ctk_variance_components,
    family_associations,
    family_client_ctk,
)
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExperimentName,
    ExposureCondition,
    FamilyPredictor,
    Learner,
    VarianceSource,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
CE = ExperimentName.CONTROLLED_EXPOSURE


def _family_seed(effects: dict[str, float]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                Column.EXPERIMENT: CE,
                Column.LEARNER: Learner.FEDAVG,
                Column.SEED: seed,
                Column.CLIENT: ClientId.ANZHI,
                Column.FAMILY: family,
                Column.CTK_GAIN: gain,
            }
            for family, gain in effects.items()
            for seed in range(100, 104)
        ]
    )


def test_a_pure_family_effect_puts_all_variance_on_the_family_source() -> None:
    table = ctk_variance_components(_family_seed({"a": 0.0, "b": 0.1, "c": 0.3}))
    shares = dict(zip(table["source"], table[Column.SHARE], strict=True))
    assert shares[VarianceSource.FAMILY] == pytest.approx(1.0)
    assert shares[VarianceSource.SEED] == pytest.approx(0.0)
    assert sum(shares.values()) == pytest.approx(1.0)


def _family_effects() -> pl.DataFrame:
    rows = [
        {
            Column.EXPERIMENT: CE,
            Column.LEARNER: Learner.FEDAVG,
            Column.FAMILY: f"f{index}",
            Column.LOCAL_RECALL: 0.1 * index,
            Column.ABSENT_RECALL: 0.1 * index + 0.01 * index * index,
            Column.PEER_RECALL: 0.5,
            Column.CTK_GAIN: 0.5 - 0.1 * index,
        }
        for index in range(5)
    ]
    return pl.DataFrame(rows)


def test_family_level_association_reports_the_rank_direction_with_its_sample_size() -> None:
    table = family_associations(_family_effects()).filter(
        (pl.col("predictor") == FamilyPredictor.LOCAL_RECALL)
        & (pl.col("outcome_measure") == "ctk-gain")
    )
    assert table["rho"].item() == pytest.approx(-1.0)
    assert table["families"].item() == 5


def test_family_client_ctk_pairs_each_hidden_family_with_its_target_client() -> None:
    def row(
        learner: Learner, condition: ExposureCondition, seed: int, hits: int
    ) -> dict[Column, object]:
        return {
            Column.EXPERIMENT: CE,
            Column.SEED: seed,
            Column.LEARNER: learner,
            Column.CONDITION: condition,
            Column.DOSE: None,
            Column.ALPHA: ALPHA,
            Column.POPULATION: EvaluationPopulation.OWN_DOMAIN,
            Column.CLIENT: ClientId.ANZHI,
            Column.FAMILY: "alpha",
            Column.HITS: hits,
            Column.TRIALS: 100,
        }

    frame = pl.DataFrame(
        [
            row(learner, condition, seed, hits + (seed - 100))
            for seed in range(100, 104)
            for learner, condition, hits in (
                (Learner.FEDAVG, ExposureCondition.PEER_PRESENT, 70),
                (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, 40),
                (Learner.LOCAL, ExposureCondition.PEER_PRESENT, 50),
            )
        ],
        schema_overrides={Column.DOSE: pl.Int64},
    )
    table = family_client_ctk(frame, CONFIG)
    assert table.height == 1
    assert abs(table["mean_difference"].item() - 0.30) < 1e-9
    assert table["seed_count"].item() == 4
