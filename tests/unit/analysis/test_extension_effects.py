import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.extension_effects import (
    holm_group,
    scope_experiments,
    seed_recalls,
    shifted_wilcoxon,
    with_holm,
)
from ctk_android.analysis.novelty import family_relatedness, known_family_centroids
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentDesign,
    ExposureCondition,
    ExtensionContrast,
    ExtensionHypothesis,
    ExtensionScope,
    Learner,
    SignTail,
)
from ctk_android.paths import Paths
from ctk_android.types import ExtensionEffectRow, PlaceboChoice, StudyData
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
NAMES = tuple(
    name
    for name, spec in CONFIG.experiments.experiments.items()
    if spec.design is ExperimentDesign.PLACEBO_ROBUST
    and CONFIG.experiments.runs_in(name, ExecutionMode.EXTENSION_B)
)


def test_shifted_wilcoxon_is_one_sided_against_the_reference() -> None:
    values = np.array([0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12])
    assert shifted_wilcoxon(values, 0.0, SignTail.GREATER) == pytest.approx(1 / 2**8)
    assert shifted_wilcoxon(values, 0.0, SignTail.TWO_SIDED) == pytest.approx(2 / 2**8)
    assert shifted_wilcoxon(values, 0.2, SignTail.GREATER) == pytest.approx(1.0, abs=0.01)
    assert shifted_wilcoxon(np.zeros(5), 0.0, SignTail.GREATER) == 1.0


def _row(
    contrast: ExtensionContrast, p_value: float, level: int | None = None
) -> ExtensionEffectRow:
    return ExtensionEffectRow(
        hypothesis=ExtensionHypothesis.DOSE_ONSET,
        scope=ExtensionScope.POOLED,
        learner=Learner.FEDAVG,
        population=EvaluationPopulation.FEDERATION_WIDE,
        alpha=ALPHA,
        contrast=contrast,
        level=level,
        seed_count=10,
        mean=0.1,
        median=0.1,
        positive_seeds=10,
        ci_low=0.05,
        ci_high=0.15,
        alternative=SignTail.GREATER,
        null_reference=0.0,
        p_value=p_value,
        p_holm=None,
        margin=0.03,
        above_margin=True,
        within_band=False,
        above_noninferiority=True,
    )


def test_holm_groups_pair_the_dose_levels_and_natural_and_the_two_aggregators() -> None:
    assert holm_group(ExtensionContrast.NATURAL_CTK) is holm_group(ExtensionContrast.DOSE_CTK)
    assert holm_group(ExtensionContrast.CTK_MEDIAN) is holm_group(ExtensionContrast.CTK_TRIMMED)
    assert holm_group(ExtensionContrast.PLACEBO_EFFECT) is None
    assert holm_group(ExtensionContrast.CTK_MEAN) is None
    assert holm_group(ExtensionContrast.TRIMMED_MINUS_MEAN) is not holm_group(
        ExtensionContrast.CTK_TRIMMED
    )


def test_holm_adjusts_only_within_a_group_and_leaves_other_rows_untouched() -> None:
    rows = [
        _row(ExtensionContrast.DOSE_CTK, 0.01, 10),
        _row(ExtensionContrast.DOSE_CTK, 0.02, 25),
        _row(ExtensionContrast.NATURAL_CTK, 0.03),
        _row(ExtensionContrast.INCREMENT_50_100, 0.001, 100),
    ]
    adjusted = with_holm(rows)
    assert [row.p_holm for row in adjusted[:3]] == [
        pytest.approx(0.03),
        pytest.approx(0.04),
        pytest.approx(0.04),
    ]
    assert adjusted[3].p_holm is None


def _families(trials: int) -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for family, hits in (("a", 10), ("b", 30)):
        for population in (EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN):
            rows.append(
                {
                    Column.EXPERIMENT: NAMES[0],
                    Column.SEED: 1,
                    Column.SALT: 0,
                    Column.CLIENT: ClientId.ANZHI,
                    Column.FAMILY: family,
                    Column.LEARNER: Learner.FEDAVG,
                    Column.CONDITION: ExposureCondition.PEER_PRESENT,
                    Column.DOSE: None,
                    Column.PARAMETER: None,
                    Column.TUNING_VALUE: None,
                    Column.ALPHA: ALPHA,
                    Column.POPULATION: population,
                    Column.HITS: hits,
                    Column.TRIALS: trials if family == "a" else 100,
                }
            )
    return pl.DataFrame(
        rows,
        schema_overrides={
            Column.DOSE: pl.Int64,
            Column.PARAMETER: pl.String,
            Column.TUNING_VALUE: pl.Float64,
        },
    )


def test_seed_recalls_are_family_macro_and_own_domain_needs_the_minimum_test_rows() -> None:
    minimum = CONFIG.data.eligibility[
        CONFIG.experiments.experiments[NAMES[0]].eligibility
    ].own_domain_min_test
    recalls = seed_recalls(_families(minimum), CONFIG, (NAMES[0],)).filter(
        pl.col(Column.SCOPE) == ExtensionScope.POOLED
    )
    fed = recalls.filter(pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    assert fed[Column.RECALL].to_list() == [pytest.approx((10 / minimum + 0.3) / 2)]
    thin = seed_recalls(_families(minimum - 1), CONFIG, (NAMES[0],))
    own = thin.filter(
        (pl.col(Column.POPULATION) == EvaluationPopulation.OWN_DOMAIN)
        & (pl.col(Column.SCOPE) == ExtensionScope.POOLED)
    )
    assert own[Column.FAMILIES].to_list() == [1]
    assert seed_recalls(pl.DataFrame(), CONFIG, (NAMES[0],)).height == 0


def test_scopes_split_the_family_sets_and_pool_them() -> None:
    scopes = scope_experiments(CONFIG, NAMES)
    assert scopes[ExtensionScope.POOLED] == NAMES
    assert len(scopes[ExtensionScope.PRIMARY_SET]) == 1
    assert len(scopes[ExtensionScope.REPLICATION_SET]) == 1


def _study() -> StudyData:
    rng = np.random.default_rng(3)
    centres = {"near": 0.2, "hidden": 0.2, "far": 0.8}
    rows: list[dict[Column, object]] = []
    matrix: list[np.ndarray] = []
    for family, centre in centres.items():
        for _ in range(60):
            matrix.append((rng.random(20) < centre).astype(np.uint8))
            rows.append({Column.FAMILY: family})
    return StudyData(table=pl.DataFrame(rows), features=np.array(matrix))


def test_relatedness_reports_centroid_distance_and_the_rank_among_known_families() -> None:
    study = _study()
    fit = {
        "near": {ClientId.ANZHI: np.arange(60, 120)},
        "hidden": {ClientId.ANZHI: np.arange(0, 60)},
        "far": {ClientId.ANZHI: np.arange(120, 180)},
    }
    novelty = CONFIG.experiments.novelty
    centroids = known_family_centroids(study, fit, frozenset({"hidden"}), novelty)
    assert set(centroids) == {"near", "far"}
    near = PlaceboChoice(
        client=ClientId.ANZHI,
        family="hidden",
        placebo="near",
        counts={},
        allocated={},
        reallocated=0,
        hidden_peer_fit=60,
        placebo_peer_fit=60,
    )
    far = near.model_copy(update={"placebo": "far"})
    close = family_relatedness(study, fit, centroids, near)
    distant = family_relatedness(study, fit, centroids, far)
    assert close.placebo_rank == 1
    assert distant.placebo_rank == 2
    assert close.centroid_distance < distant.centroid_distance
    assert close.nearest_known_distance == pytest.approx(close.centroid_distance)
    assert close.known_families == 2
