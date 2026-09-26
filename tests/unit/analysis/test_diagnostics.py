# Pyright cannot infer callback signatures for monkeypatch lambda stubs.
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false
import numpy as np
import polars as pl
import pytest
from scipy import stats

from ctk_android.analysis.diagnostic_synthesis import (
    family_taxonomy,
    influence_tables,
    kendall_w,
    large_family_associations,
    large_family_table,
    large_family_taxonomy,
    leave_one_out,
    rank_concordance,
    weighted_spearman,
)
from ctk_android.analysis.diagnostics import (
    client_curves,
    control_cells,
    control_diagnostics,
    ctk_by_dose,
    dose_increments,
    equal_fpr_arms,
    equivalent_dose,
    family_curves,
    family_seed_level,
    family_summary,
    fit_curve,
    pair_ctk,
    recall_at_fpr,
    scope_members,
    score_health,
    scored_targets,
    seeded_bca,
)
from ctk_android.analysis.extensions import dose_experiments
from ctk_android.config import load_config
from ctk_android.enums import (
    Aggregation,
    ClientId,
    Column,
    DiagnosticColumn,
    DiagnosticSeed,
    DoseCode,
    DoseModel,
    DoseResponseClass,
    EvaluationPopulation,
    EvidenceClass,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExtensionScope,
    FamilySetName,
    InfluenceStatistic,
    Learner,
    NoveltyDescriptor,
    Representation,
    SplitRole,
    TaxonomyLabel,
)
from ctk_android.paths import Paths
from ctk_android.types import RandomSeed, ScoredRun, TargetPair
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
    assert first == second
    assert first is not None
    assert first.low < 0.3 < first.high
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
        seed=RandomSeed(1),
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
    equal_fpr_recall = row[DiagnosticColumn.EQUAL_FPR_RECALL]
    assert isinstance(equal_fpr_recall, int | float)
    assert 0.0 <= equal_fpr_recall <= 1.0


def test_score_health_counts_non_finite_and_extreme_scores() -> None:
    run = _scored_run()
    frame = pl.DataFrame({Column.SCORE: [0.0, np.inf, 2e3, -3e4, np.nan]})
    rows = score_health(run.model_copy(update={"scores": {"arm": frame}}))
    assert rows[0][DiagnosticColumn.NONFINITE] == 2
    assert rows[0][DiagnosticColumn.ABOVE_LARGE] == 3
    assert rows[0][DiagnosticColumn.ABOVE_EXTREME] == 2


def test_control_diagnostics_builds_paired_control_cells_and_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    experiments = tuple(
        name
        for name, spec in CONFIG.experiments.experiments.items()
        if spec.design is ExperimentDesign.PLACEBO_ROBUST
        and CONFIG.experiments.runs_in(name, ExecutionMode.EXTENSION_B)
    )
    assert experiments
    alphas = CONFIG.experiments.operating.alphas
    family_rows: list[dict[Column, object]] = []
    novelty_rows: list[dict[Column, object]] = []
    placebo_rows: list[dict[Column | DiagnosticColumn, object]] = []
    exposure_rows: list[dict[Column, object]] = []
    arms = (
        (ExposureCondition.PLACEBO, None, 20),
        (ExposureCondition.PEER_PRESENT, None, 40),
        (ExposureCondition.PEER_PRESENT, Aggregation.TRIMMED_MEAN, 38),
        (ExposureCondition.PEER_PRESENT, Aggregation.COORDINATE_MEDIAN, 36),
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, None, 30),
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Aggregation.TRIMMED_MEAN, 31),
        (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Aggregation.COORDINATE_MEDIAN, 29),
    )
    for experiment in experiments:
        for seed in (1, 2):
            for condition, tuning, hits in arms:
                for population in (
                    EvaluationPopulation.FEDERATION_WIDE,
                    EvaluationPopulation.OWN_DOMAIN,
                ):
                    for alpha in alphas:
                        family_rows.append(
                            {
                                Column.EXPERIMENT: experiment,
                                Column.SEED: seed,
                                Column.LEARNER: Learner.FEDAVG,
                                Column.CONDITION: condition,
                                Column.TUNING_VALUE: tuning,
                                Column.POPULATION: population,
                                Column.ALPHA: alpha,
                                Column.CLIENT: ClientId.ANZHI,
                                Column.FAMILY: "hidden",
                                Column.HITS: hits + seed,
                                Column.TRIALS: 100,
                            }
                        )
            for descriptor, value in (
                (NoveltyDescriptor.CENTROID_DISTANCE_TO_KNOWN_MALWARE, 0.4),
                (NoveltyDescriptor.MAX_JACCARD_TO_KNOWN_FAMILY, 0.2),
            ):
                novelty_rows.append(
                    {
                        Column.EXPERIMENT: experiment,
                        Column.SEED: seed,
                        Column.CLIENT: ClientId.ANZHI,
                        Column.FAMILY: "hidden",
                        Column.DESCRIPTOR: descriptor,
                        Column.VALUE: value + seed,
                    }
                )
            placebo_rows.append(
                {
                    Column.EXPERIMENT: experiment,
                    Column.SEED: seed,
                    Column.CLIENT: ClientId.ANZHI,
                    Column.FAMILY: "hidden",
                    DiagnosticColumn.PLACEBO_FAMILY: "placebo",
                    DiagnosticColumn.NEED: 10,
                    DiagnosticColumn.REALLOCATED: 1 + seed,
                    DiagnosticColumn.CENTROID_DISTANCE: 0.3 + seed,
                    DiagnosticColumn.NEAREST_KNOWN_DISTANCE: 0.2 + seed,
                    DiagnosticColumn.PLACEBO_RANK: 2,
                    DiagnosticColumn.HIDDEN_PEER_FIT: 100,
                    DiagnosticColumn.PLACEBO_PEER_FIT: 80,
                }
            )
            exposure_rows.append(
                {
                    Column.EXPERIMENT: experiment,
                    Column.SEED: seed,
                    Column.CONDITION: ExposureCondition.PEER_PRESENT,
                    Column.TUNING_VALUE: None,
                    Column.CLIENT: ClientId.APPCHINA,
                    Column.FAMILY: "hidden",
                    Column.ROWS: 100,
                }
            )

    cells = control_cells(
        pl.DataFrame(family_rows),
        pl.DataFrame(exposure_rows),
        pl.DataFrame(novelty_rows),
        pl.DataFrame(placebo_rows),
        CONFIG,
        experiments,
    )
    assert cells.height == 4 * len(experiments) * len(alphas)
    assert cells[DiagnosticColumn.CTK_MEAN].to_list() == pytest.approx([0.1] * cells.height)
    assert cells[DiagnosticColumn.PEERS].to_list() == [1] * cells.height
    assert cells[DiagnosticColumn.FIT_RATIO].to_list() == pytest.approx([0.8] * cells.height)

    monkeypatch.setattr("ctk_android.analysis.diagnostics.reallocation_slopes", lambda *_args: [])
    result = control_diagnostics(cells, CONFIG, experiments)
    assert result.strata.height > 0
    assert result.clients.height > 0
    assert result.families.height > 0
    assert result.support_levels.height > 0


def test_dose_diagnostic_tables_keep_seed_family_and_natural_arm_contrasts() -> None:
    experiments = dose_experiments(CONFIG, ExecutionMode.EXTENSION_B)
    assert experiments
    rows: list[dict[Column, object]] = []
    for experiment in experiments:
        for seed in (1, 2):
            for learner in (Learner.FEDAVG, Learner.CENTRAL):
                for population in (
                    EvaluationPopulation.FEDERATION_WIDE,
                    EvaluationPopulation.OWN_DOMAIN,
                ):
                    for alpha in CONFIG.experiments.operating.alphas:
                        for family_index in range(2):
                            family = f"family-{family_index}"
                            baseline = 10 + seed + family_index
                            for dose in CONFIG.experiments.exact_dose_levels:
                                rows.append(
                                    {
                                        Column.EXPERIMENT: experiment,
                                        Column.SEED: seed,
                                        Column.LEARNER: learner,
                                        Column.CONDITION: ExposureCondition.EXACT_DOSE,
                                        Column.DOSE: dose,
                                        Column.POPULATION: population,
                                        Column.ALPHA: alpha,
                                        Column.CLIENT: ClientId.ANZHI,
                                        Column.FAMILY: family,
                                        Column.HITS: baseline + dose,
                                        Column.TRIALS: 100,
                                    }
                                )
                            rows.append(
                                {
                                    Column.EXPERIMENT: experiment,
                                    Column.SEED: seed,
                                    Column.LEARNER: learner,
                                    Column.CONDITION: ExposureCondition.PEER_PRESENT,
                                    Column.DOSE: None,
                                    Column.POPULATION: population,
                                    Column.ALPHA: alpha,
                                    Column.CLIENT: ClientId.ANZHI,
                                    Column.FAMILY: family,
                                    Column.HITS: baseline + 30,
                                    Column.TRIALS: 100,
                                }
                            )

    pairs = pair_ctk(pl.DataFrame(rows), CONFIG, experiments)
    assert pairs.height > 0
    natural = pairs.filter(pl.col(DiagnosticColumn.DOSE_CODE) == DoseCode.NATURAL)
    assert natural.height > 0
    assert (natural[DiagnosticColumn.CTK] > 0).all()

    curves_by_seed = family_seed_level(pairs)
    curves = family_curves(curves_by_seed, CONFIG)
    summary = family_summary(pl.DataFrame(curves), CONFIG)
    assert ctk_by_dose(pairs, CONFIG, experiments)
    assert dose_increments(pairs, CONFIG, experiments)
    assert summary
    assert client_curves(pairs, CONFIG, experiments) == []


def test_confirmatory_family_taxonomy_uses_intervals_and_model_family_context() -> None:
    rows: list[dict[Column | DiagnosticColumn, object]] = []
    experiments = (
        ExperimentName.CONTROLLED_EXPOSURE,
        ExperimentName.REPLICATION_FAMILY_SET,
    )
    for experiment in experiments:
        for population in (
            EvaluationPopulation.OWN_DOMAIN,
            EvaluationPopulation.FEDERATION_WIDE,
        ):
            for family, gain, full in (("responsive", 0.2, 0.9), ("poor", 0.0, 0.1)):
                for seed in range(1, 11):
                    for learner, recall in (
                        (Learner.FEDAVG, full),
                        (Learner.CENTRAL, full + 0.05),
                    ):
                        rows.append(
                            {
                                Column.EXPERIMENT: experiment,
                                Column.POPULATION: population,
                                Column.FAMILY: family,
                                Column.SEED: seed,
                                Column.LEARNER: learner,
                                Column.FULL_RECALL: recall,
                                DiagnosticColumn.CTK: gain,
                                DiagnosticColumn.POOLING: 0.1 if family == "responsive" else -0.1,
                                Column.LOCAL_RECALL: 0.4 if family == "responsive" else 0.05,
                                DiagnosticColumn.HEADROOM: 0.5 if family == "responsive" else 0.05,
                                Column.PEER_RECALL: 0.6,
                                Column.ABSENT_RECALL: 0.3,
                            }
                        )
    for experiment in (
        ExperimentName.MODEL_FAMILY_REPLICATION_LINEAR,
        ExperimentName.MODEL_FAMILY_REPLICATION_TREES,
    ):
        for population in (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE):
            for family in ("responsive", "poor"):
                for seed in range(1, 11):
                    rows.append(
                        {
                            Column.EXPERIMENT: experiment,
                            Column.POPULATION: population,
                            Column.FAMILY: family,
                            Column.SEED: seed,
                            Column.LEARNER: Learner.FEDAVG,
                            Column.FULL_RECALL: 0.8 if family == "responsive" else 0.1,
                            DiagnosticColumn.CTK: 0.1,
                            DiagnosticColumn.POOLING: 0.0,
                            Column.LOCAL_RECALL: 0.3,
                            DiagnosticColumn.HEADROOM: 0.5,
                            Column.PEER_RECALL: 0.5,
                            Column.ABSENT_RECALL: 0.3,
                        }
                    )

    table = family_taxonomy(pl.DataFrame(rows), CONFIG, np.random.default_rng(7))
    flags = dict(table.select(Column.FAMILY, DiagnosticColumn.LABELS).unique().rows())
    assert "responsive" in flags
    assert "poor" in flags
    assert table[Column.EVIDENCE_CLASS].unique().to_list() == [EvidenceClass.POST_CONFIRMATORY]


def test_large_family_diagnostic_table_and_rank_associations_preserve_seed_pairs() -> None:
    names = [f"family-{index}" for index in range(8)]
    seeds: list[dict[Column | DiagnosticColumn, object]] = []
    for index, family in enumerate(names):
        for seed in (1, 2):
            seeds.append(
                {
                    Column.LEARNER: Learner.FEDAVG,
                    Column.FAMILY: family,
                    Column.SEED: seed,
                    Column.CTK_GAIN: index / 10,
                    Column.LOCAL_RECALL: index / 20,
                    Column.FULL_RECALL: 0.4 + index / 20,
                    Column.ABSENT_RECALL: 0.2 + index / 20,
                    Column.PEER_RECALL: 0.5 + index / 20,
                    Column.TRIALS: 50 + index,
                }
            )
    families = pl.DataFrame(
        {
            Column.FAMILY: names,
            Column.NOVELTY: [float(index) for index in range(8)],
            Column.MIN_TRIALS: [50 + index for index in range(8)],
            Column.MEETS_THRESHOLD: [False, *([True] * 7)],
        }
    )
    selection = pl.DataFrame(
        {
            Column.FAMILY: names,
            Column.ROWS: [100 + index for index in range(8)],
            Column.FAMILY_SET: [FamilySetName.LARGE_1] * 8,
        }
    )

    table = large_family_table(pl.DataFrame(seeds), families, selection)
    assert table.height == 8
    assert table[DiagnosticColumn.HEADROOM].to_list() == pytest.approx([0.4] * 8)
    assert table[DiagnosticColumn.LOG_ROWS].is_sorted()
    taxonomy = large_family_taxonomy(table, CONFIG)
    assert len(taxonomy[DiagnosticColumn.LABELS]) == 8

    family_ctk = pl.DataFrame(
        [
            {
                Column.EXPERIMENT: ExperimentName.LARGE_FAMILY_SET_1,
                Column.POPULATION: population,
                Column.LEARNER: Learner.FEDAVG,
                Column.FAMILY: family,
                DiagnosticColumn.CTK: index / 10,
            }
            for population in (
                EvaluationPopulation.OWN_DOMAIN,
                EvaluationPopulation.FEDERATION_WIDE,
            )
            for index, family in enumerate(names)
        ]
    )
    large = pl.DataFrame(
        {Column.FAMILY: names, Column.CTK_GAIN: [index / 10 for index in range(8)]}
    )
    concordance = rank_concordance(family_ctk, large, CONFIG)
    associations = large_family_associations(table, CONFIG)
    assert len(concordance) == 2
    assert all(row[Column.FAMILIES] == 8 for row in concordance)
    assert len(associations) == 7
