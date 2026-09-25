import numpy as np
import polars as pl
import pytest
from scipy import stats

from ctk_android.analysis.diagnostics_dose import (
    equivalent_dose,
    family_summary,
    fit_curve,
)
from ctk_android.analysis.diagnostics_influence import (
    influence_tables,
    kendall_w,
    leave_one_out,
    weighted_spearman,
)
from ctk_android.analysis.diagnostics_representation import (
    equal_fpr_arms,
    recall_at_fpr,
    score_health,
    scored_targets,
)
from ctk_android.analysis.diagnostics_statistics import scope_members, seeded_bca
from ctk_android.analysis.diagnostics_synthesis import large_family_taxonomy
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    DiagnosticColumn,
    DiagnosticSeed,
    DoseCode,
    DoseModel,
    DoseResponseClass,
    EvaluationPopulation,
    ExtensionScope,
    InfluenceStatistic,
    Representation,
    SplitRole,
    TaxonomyLabel,
)
from ctk_android.paths import Paths
from ctk_android.types import ScoredRun, TargetPair
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
DOSES = np.array(CONFIG.experiments.exact_dose_levels, dtype=np.float64)


def test_equal_fpr_recall_is_one_for_separated_scores_and_tracks_fpr_for_identical_ones() -> None:
    negatives = np.linspace(0.0, 1.0, 101)
    assert recall_at_fpr(negatives, negatives + 5.0, ALPHA) == pytest.approx(1.0)
    assert recall_at_fpr(negatives, negatives.copy(), ALPHA) == pytest.approx(ALPHA, abs=0.02)


def test_weighted_spearman_with_equal_weights_is_spearman() -> None:
    rng = np.random.default_rng(0)
    first, second = rng.normal(size=20), rng.normal(size=20)
    expected = stats.spearmanr(first, second).statistic
    assert weighted_spearman(first, second, np.ones(20)) == pytest.approx(expected)


def test_kendall_w_is_one_under_perfect_agreement_and_leave_one_out_drops_each_item() -> None:
    ranks = np.tile(np.arange(1.0, 7.0)[:, None], (1, 4))
    assert kendall_w(ranks) == pytest.approx(1.0)
    first = np.arange(6.0)
    second = np.array([0.0, 2.0, 1.0, 3.0, 5.0, 4.0])
    loo = leave_one_out(first, second)
    assert loo.shape == (6,)
    assert loo[0] == pytest.approx(stats.spearmanr(first[1:], second[1:]).statistic)


def test_seeded_bca_is_deterministic_and_skips_degenerate_samples() -> None:
    values = np.array([0.1, 0.3, 0.2, 0.5, 0.4, np.nan])
    first = seeded_bca(values, CONFIG, DiagnosticSeed.CONTROLS, 5)
    second = seeded_bca(values, CONFIG, DiagnosticSeed.CONTROLS, 5)
    assert first == second and first is not None and first.low < 0.3 < first.high
    assert seeded_bca(np.full(8, 0.2), CONFIG, DiagnosticSeed.DOSE, 3) is None
    assert seeded_bca(values, CONFIG, DiagnosticSeed.DOSE, 6) is None


def test_pooled_scope_covers_both_family_sets() -> None:
    assert scope_members(ExtensionScope.POOLED) == [
        ExtensionScope.PRIMARY_SET,
        ExtensionScope.REPLICATION_SET,
    ]
    assert scope_members(ExtensionScope.PRIMARY_SET) == [ExtensionScope.PRIMARY_SET]


def test_dose_fits_recover_exact_curves() -> None:
    emax = 0.3 * DOSES / (40.0 + DOSES)
    fit = fit_curve(np.tile(emax, (5, 1)), DOSES, DoseModel.EMAX)
    assert fit.parameters == pytest.approx((0.3, 40.0), rel=1e-4)
    log = 0.02 * np.log1p(DOSES)
    assert fit_curve(np.tile(log, (4, 1)), DOSES, DoseModel.LOG_LINEAR).parameters[
        0
    ] == pytest.approx(0.02)
    isotonic = fit_curve(np.tile(np.sort(log), (3, 1)), DOSES, DoseModel.ISOTONIC)
    assert isotonic.predicted == pytest.approx(log)


def test_equivalent_dose_interpolates_and_is_infinite_beyond_the_top_dose() -> None:
    curve = np.array([0.0, 0.01, 0.02, 0.04, 0.08, 0.16])
    assert equivalent_dose(curve, 0.06, DOSES) == pytest.approx(75.0)
    assert equivalent_dose(curve, -0.01, DOSES) == 0.0
    assert np.isinf(equivalent_dose(curve, 0.5, DOSES))


def _curve(family: str, means: list[float], low_top: float | None) -> pl.DataFrame:
    doses = [*CONFIG.experiments.exact_dose_levels, DoseCode.NATURAL]
    return pl.DataFrame(
        {
            DiagnosticColumn.SET: [ExtensionScope.PRIMARY_SET] * len(doses),
            Column.POPULATION: [EvaluationPopulation.FEDERATION_WIDE] * len(doses),
            Column.FAMILY: [family] * len(doses),
            DiagnosticColumn.DOSE_CODE: doses,
            DiagnosticColumn.SEEDS: [10] * len(doses),
            Column.MEAN_CTK: [*means, 0.05],
            Column.CI_LOW: [None] * (len(doses) - 2) + [low_top, None],
            Column.CI_HIGH: [None] * len(doses),
        },
        schema_overrides={Column.CI_LOW: pl.Float64, Column.CI_HIGH: pl.Float64},
    )


def test_family_response_classes_follow_the_onset_rules() -> None:
    curves = pl.concat(
        [
            _curve("early", [0.0, 0.01, 0.04, 0.05, 0.06, 0.08], 0.02),
            _curve("late", [0.0, 0.0, 0.01, 0.02, 0.04, 0.06], 0.01),
            _curve("flat", [0.0, 0.0, 0.0, 0.01, 0.02, 0.02], 0.001),
            _curve("wide", [0.0, 0.05, 0.05, 0.05, 0.05, 0.05], None),
        ]
    )
    rows = {row[Column.FAMILY]: row for row in family_summary(curves, CONFIG)}
    assert rows["early"][DiagnosticColumn.RESPONSE_CLASS] is DoseResponseClass.EARLY
    assert rows["early"][DiagnosticColumn.ONSET_MEAN] == 25
    assert rows["late"][DiagnosticColumn.RESPONSE_CLASS] is DoseResponseClass.LATE
    assert rows["flat"][DiagnosticColumn.RESPONSE_CLASS] is DoseResponseClass.NONRESPONSIVE
    assert rows["wide"][DiagnosticColumn.RESPONSE_CLASS] is DoseResponseClass.NONRESPONSIVE


def test_large_family_taxonomy_applies_the_fixed_rules() -> None:
    table = pl.DataFrame(
        {
            Column.FAMILY: ["exposed", "poor", "negative"],
            DiagnosticColumn.CTK: [0.10, 0.01, 0.08],
            Column.FULL_RECALL: [0.9, 0.4, 0.8],
            DiagnosticColumn.HEADROOM: [0.2, 0.01, 0.1],
            DiagnosticColumn.POOLING: [0.0, 0.0, -0.1],
        }
    )
    labels = dict(
        large_family_taxonomy(table, CONFIG).select(Column.FAMILY, DiagnosticColumn.LABELS).rows()
    )
    assert labels["exposed"] == TaxonomyLabel.EXPOSURE_LIMITED
    assert labels["poor"] == f"{TaxonomyLabel.POOR_FULL_SINGLE_CLASS} {TaxonomyLabel.LOW_HEADROOM}"
    assert labels["negative"] == (
        f"{TaxonomyLabel.EXPOSURE_LIMITED} {TaxonomyLabel.NEGATIVE_TRANSFER_SENSITIVE}"
    )


def test_influence_tables_rank_families_by_leave_one_out_influence() -> None:
    names = [f"f{index}" for index in range(8)]
    novelty = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    ctk = np.array([0.01, 0.03, 0.02, 0.05, 0.04, 0.07, 0.06, 0.2])
    families = pl.DataFrame(
        {
            Column.FAMILY: names,
            Column.NOVELTY: novelty,
            Column.CTK_GAIN: ctk,
            Column.SEED_COUNT: [4] * 8,
            Column.CTK_SD: [0.02] * 8,
        }
    )
    seeds = pl.DataFrame(
        {
            Column.FAMILY: [name for name in names for _ in range(4)],
            Column.SEED: [seed for _ in names for seed in (1, 2, 3, 4)],
            Column.CLIENT: [ClientId.ANZHI] * 32,
            Column.TRIALS: [50] * 32,
            Column.CTK_GAIN: [value + shift for value in ctk for shift in (-0.01, 0.0, 0.0, 0.01)],
        }
    )
    stability = pl.DataFrame(
        {Column.FAMILY: names, Column.STABLE: [True] * 7 + [False], Column.ELIGIBLE_SEEDS: [4] * 8}
    )
    tables = influence_tables(families, seeds, stability, CONFIG)
    summary = dict(tables.summary.select(DiagnosticColumn.STATISTIC, Column.VALUE).rows())
    rho = stats.spearmanr(novelty, ctk).statistic
    assert summary[InfluenceStatistic.RHO_ALL] == pytest.approx(rho)
    assert summary[InfluenceStatistic.KENDALL_W] == pytest.approx(1.0)
    ranked = tables.families
    assert ranked[DiagnosticColumn.INFLUENCE_RANK].to_list() == list(range(1, 9))
    assert ranked[DiagnosticColumn.INFLUENCE].is_sorted(descending=True)
    assert ranked.filter(pl.col(DiagnosticColumn.UNSTABLE))[Column.FAMILY].to_list() == ["f7"]


def _scored_run() -> ScoredRun:
    clients = [ClientId.ANZHI] * 6 + [ClientId.APPCHINA] * 4
    labels = [0, 0, 0, 0, 1, 1, 0, 0, 1, 1]
    families = [None, None, None, None, "fam", "fam", None, None, "fam", "other"]
    study = pl.DataFrame(
        {
            Column.LABEL: labels,
            Column.CLIENT: clients,
            Column.ROLE: [SplitRole.TEST] * 10,
            Column.FAMILY: families,
        }
    )
    scores = np.array([0.1, 0.2, 0.3, 0.9, 0.8, 0.4, 0.95, 0.05, 0.7, 0.99])
    arms = equal_fpr_arms()
    operating = pl.DataFrame(
        {
            Column.LEARNER: [arm.learner for arm in arms],
            Column.CONDITION: [arm.condition for arm in arms],
            Column.DOSE: pl.Series([None] * 3, dtype=pl.Int64),
            Column.CLIENT: [ClientId.ANZHI] * 3,
            Column.ALPHA: [ALPHA] * 3,
            Column.THRESHOLD: [0.5] * 3,
            Column.VALUE: [0.25] * 3,
        }
    )
    metrics = operating.with_columns(
        pl.lit(EvaluationPopulation.FEDERATION_WIDE).alias(Column.POPULATION),
        pl.lit("fam").alias(Column.FAMILY),
        pl.lit(2).alias(Column.HITS),
        pl.lit(3).alias(Column.TRIALS),
    )
    frame = pl.DataFrame(
        {
            Column.TARGET_CLIENT: [ClientId.ANZHI] * 10,
            Column.ROW: list(range(10)),
            Column.SCORE: scores,
        }
    )
    return ScoredRun(
        representation=Representation.LAMDA_STATIC,
        seed=1,
        targets=(TargetPair(client=ClientId.ANZHI, family="fam"),),
        study=study,
        thresholds=operating,
        families=metrics,
        operating=operating,
        scores={arm.label(): frame for arm in arms},
    )


def test_scored_targets_reproduce_the_calibrated_operating_point() -> None:
    rows = scored_targets(_scored_run(), CONFIG)
    assert len(rows) == 3
    row = rows[0]
    assert row[DiagnosticColumn.BENIGN_TEST] == 4
    assert row[DiagnosticColumn.POSITIVE_TEST] == 3
    assert row[DiagnosticColumn.CALIBRATED_RECALL] == pytest.approx(2 / 3)
    assert row[DiagnosticColumn.CALIBRATED_FPR] == pytest.approx(0.25)
    assert row[DiagnosticColumn.STORED_RECALL] == pytest.approx(2 / 3)
    assert 0.0 <= row[DiagnosticColumn.EQUAL_FPR_RECALL] <= 1.0


def test_score_health_counts_non_finite_and_extreme_scores() -> None:
    run = _scored_run()
    frame = pl.DataFrame({Column.SCORE: [0.0, np.inf, 2e3, -3e4, np.nan]})
    rows = score_health(run.model_copy(update={"scores": {"arm": frame}}))
    assert rows[0][DiagnosticColumn.NONFINITE] == 2
    assert rows[0][DiagnosticColumn.ABOVE_LARGE] == 3
    assert rows[0][DiagnosticColumn.ABOVE_EXTREME] == 2
