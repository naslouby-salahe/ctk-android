import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.extensions import (
    eligibility_table,
    representation_experiments,
    representation_map,
    representation_tables,
    representation_verdicts,
)
from ctk_android.config import load_config
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExtensionHypothesis,
    HiddadStatus,
    Learner,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    RepresentationOutcome,
)
from ctk_android.paths import Paths
from ctk_android.types import RandomSeed, RepresentationEffectRow, RepresentationTables, TargetPair
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
EXPERIMENTS = representation_experiments(CONFIG, MODE)
ALPHA = CONFIG.experiments.operating.primary_alpha
MARGIN = CONFIG.statistics.gates.ctk_min_gain
SEEDS = tuple(RandomSeed(seed) for seed in range(330, 340))
TRIALS = 400
PRIORITY = CONFIG.experiments.representation_priority_families
CONTRAST = CONFIG.experiments.representation_contrast_families
SEPARATE = CONFIG.experiments.representation_separate_families
BASE = {"hiddad": 0.35, "gappusin": 0.6, "revmob": 0.5, "leadbolt": 0.8, "airpush": 0.75}
GAINS = {
    Representation.LAMDA_STATIC: {},
    Representation.MCNDROID_STATIC: {"gappusin": 0.15, "revmob": 0.15, "adwo": 0.2},
    Representation.CALL_GRAPH: {"gappusin": 0.08, "revmob": 0.1, "hiddad": -0.06},
    Representation.REPORT_JSON: {"gappusin": -0.1, "revmob": -0.1, "hiddad": -0.1},
}
FAMILIES = (*PRIORITY, *CONTRAST, *SEPARATE)
Gains = dict[Representation, dict[str, float]]
Verdicts = dict[ExtensionHypothesis, dict[str, object]]


def _recall(family: str, representation: Representation, gains: Gains, seed: int) -> float:
    base = BASE.get(family, 0.7 if family == "dowgin" else 0.3)
    order = list(Representation).index(representation)
    wobble = ((seed * 7 + len(family) * (order + 1) + order) % 5 - 2) * 0.004
    return float(np.clip(base + gains[representation].get(family, 0.0) + wobble, 0.0, 1.0))


def _families(gains: Gains = GAINS, skip: tuple[str, ...] = ()) -> pl.DataFrame:
    rows: list[dict[Column, object]] = []
    for name in EXPERIMENTS:
        representation = CONFIG.experiments.experiments[name].representation
        assert representation is not None
        for seed in SEEDS:
            for family in FAMILIES:
                if family in skip:
                    continue
                level = _recall(family, representation, gains, seed)
                arms = [
                    (Learner.CENTRAL, ExposureCondition.FULL_EXPOSURE, level),
                    (Learner.FEDAVG, ExposureCondition.PEER_PRESENT, level),
                    (Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, level / 2),
                ]
                for learner, condition, recall in arms:
                    for population in (
                        EvaluationPopulation.FEDERATION_WIDE,
                        EvaluationPopulation.OWN_DOMAIN,
                    ):
                        rows.append(
                            {
                                Column.EXPERIMENT: name,
                                Column.SEED: seed,
                                Column.SALT: 0,
                                Column.CLIENT: ClientId.ANZHI,
                                Column.FAMILY: family,
                                Column.LEARNER: learner,
                                Column.CONDITION: condition,
                                Column.DOSE: None,
                                Column.PARAMETER: None,
                                Column.TUNING_VALUE: None,
                                Column.ALPHA: ALPHA,
                                Column.POPULATION: population,
                                Column.HITS: round(recall * TRIALS),
                                Column.TRIALS: TRIALS,
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


TABLES = representation_tables(_families(), CONFIG, EXPERIMENTS)


def _effect(
    tables: RepresentationTables,
    representation: Representation,
    group: RepresentationGroup,
    family: str | None = None,
    measure: RepresentationMeasure = RepresentationMeasure.FULL_EXPOSURE_RECALL,
    population: EvaluationPopulation = EvaluationPopulation.FEDERATION_WIDE,
) -> RepresentationEffectRow:
    return next(
        row
        for row in tables.effects
        if row.representation is representation
        and row.group is group
        and row.family == family
        and row.measure is measure
        and row.population is population
    )


def _verdict(tables: RepresentationTables) -> Verdicts:
    frame = representation_verdicts(tables.effects, CONFIG)
    return {ExtensionHypothesis(row["hypothesis"]): row for row in frame.iter_rows(named=True)}


def test_the_four_representations_are_the_extension_b_experiments() -> None:
    assert set(EXPERIMENTS) == {
        ExperimentName.REPRESENTATION_R0,
        ExperimentName.REPRESENTATION_R1,
        ExperimentName.REPRESENTATION_R2,
        ExperimentName.REPRESENTATION_R3,
    }
    assert set(representation_map(CONFIG, EXPERIMENTS).values()) == set(Representation)
    assert all(CONFIG.seeds_for(name, MODE) == SEEDS for name in EXPERIMENTS)


def test_differences_are_seed_paired_against_the_lamda_static_baseline() -> None:
    gappusin = _effect(
        TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.FAMILY, "gappusin"
    )
    assert gappusin.seed_count == len(SEEDS)
    assert gappusin.mean == pytest.approx(0.15, abs=0.01)
    assert gappusin.mean_level - gappusin.mean_baseline == pytest.approx(gappusin.mean)
    macro = _effect(TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.PRIORITY_MACRO)
    assert macro.family is None
    assert macro.mean == pytest.approx((0.15 + 0.15 + 0.0) / 3, abs=0.01)
    contrast = _effect(TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.CONTRAST_MACRO)
    assert abs(contrast.mean) < 0.01 and contrast.within_band
    adwo = _effect(TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.FAMILY, "adwo")
    assert adwo.mean == pytest.approx(0.2, abs=0.01)
    assert not any(row.representation is Representation.LAMDA_STATIC for row in TABLES.effects)


def test_margin_flags_follow_the_bca_interval_and_the_configured_band() -> None:
    macro = _effect(TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.PRIORITY_MACRO)
    assert macro.margin == MARGIN
    assert macro.ci_low is not None and macro.ci_low > MARGIN
    assert macro.above_margin and not macro.below_margin
    assert macro.p_margin < 0.05
    hiddad = _effect(TABLES, Representation.MCNDROID_STATIC, RepresentationGroup.FAMILY, "hiddad")
    assert hiddad.below_margin and hiddad.within_band and not hiddad.above_margin


def test_holm_covers_exactly_the_nine_priority_by_representation_tests() -> None:
    adjusted = [row for row in TABLES.effects if row.p_holm is not None]
    assert len(adjusted) == len(PRIORITY) * (len(Representation) - 1)
    assert all(
        row.group is RepresentationGroup.FAMILY
        and row.family in PRIORITY
        and row.measure is RepresentationMeasure.FULL_EXPOSURE_RECALL
        and row.population is EvaluationPopulation.FEDERATION_WIDE
        and row.p_holm is not None
        and row.p_holm >= row.p_value
        for row in adjusted
    )


def test_ctk_is_reported_per_representation_and_as_a_change_from_the_baseline() -> None:
    change = _effect(
        TABLES,
        Representation.MCNDROID_STATIC,
        RepresentationGroup.FAMILY,
        "gappusin",
        RepresentationMeasure.CTK,
    )
    assert change.mean == pytest.approx(0.075, abs=0.01)
    levels = [row for row in TABLES.levels if row.measure is RepresentationMeasure.CTK]
    assert {row.representation for row in levels} == set(Representation)
    reference = next(
        row
        for row in levels
        if row.representation is Representation.LAMDA_STATIC
        and row.family == "gappusin"
        and row.population is EvaluationPopulation.FEDERATION_WIDE
    )
    assert reference.mean == pytest.approx(0.3, abs=0.01)


def test_own_domain_is_kept_as_a_secondary_population() -> None:
    populations = {row.population for row in TABLES.effects}
    assert populations == {EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN}
    assert set(TABLES.seeds[Column.MEASURE].unique().to_list()) == set(RepresentationMeasure)


def test_both_hypotheses_met_when_only_hiddad_stays_unrescued() -> None:
    verdicts = _verdict(TABLES)
    assert verdicts[ExtensionHypothesis.REPRESENTATION_RESCUE]["met"] is True
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["met"] is True
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["outcome"] == HiddadStatus.NOT_RESCUED
    )
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_OUTCOME]["outcome"]
        == RepresentationOutcome.FAMILY_SPECIFIC_LIMITS
    )


def test_a_rescued_hiddad_fails_the_second_hypothesis() -> None:
    gains: Gains = {**GAINS, Representation.CALL_GRAPH: {"hiddad": 0.2}}
    tables = representation_tables(_families(gains), CONFIG, EXPERIMENTS)
    verdicts = _verdict(tables)
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["met"] is False
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["outcome"] == HiddadStatus.RESCUED
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_OUTCOME]["outcome"]
        == RepresentationOutcome.HIDDAD_RESCUED
    )


def test_an_inconclusive_hiddad_interval_is_unresolved_not_a_rescue() -> None:
    static = {**GAINS[Representation.MCNDROID_STATIC], "hiddad": MARGIN}
    gains: Gains = {**GAINS, Representation.MCNDROID_STATIC: static}
    tables = representation_tables(_families(gains), CONFIG, EXPERIMENTS)
    hiddad = _effect(tables, Representation.MCNDROID_STATIC, RepresentationGroup.FAMILY, "hiddad")
    assert hiddad.ci_low is not None and hiddad.ci_high is not None
    assert hiddad.ci_low <= MARGIN <= hiddad.ci_high
    verdicts = _verdict(tables)
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["met"] is False
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["outcome"] == HiddadStatus.UNRESOLVED
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_OUTCOME]["outcome"]
        == RepresentationOutcome.HIDDAD_UNRESOLVED
    )


def test_no_gain_from_mcndroid_static_leaves_the_original_wording_standing() -> None:
    gains: Gains = {**GAINS, Representation.MCNDROID_STATIC: {}}
    tables = representation_tables(_families(gains), CONFIG, EXPERIMENTS)
    verdicts = _verdict(tables)
    assert verdicts[ExtensionHypothesis.REPRESENTATION_RESCUE]["met"] is False
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_OUTCOME]["outcome"]
        == RepresentationOutcome.LIMITS_STAND
    )


def test_a_dropped_hiddad_leaves_the_verdicts_undetermined_and_is_never_replaced() -> None:
    tables = representation_tables(_families(skip=("hiddad",)), CONFIG, EXPERIMENTS)
    assert not any(row.family == "hiddad" for row in tables.effects)
    verdicts = _verdict(tables)
    assert verdicts[ExtensionHypothesis.REPRESENTATION_HIDDAD]["met"] is None
    assert (
        verdicts[ExtensionHypothesis.REPRESENTATION_OUTCOME]["outcome"]
        == RepresentationOutcome.UNDETERMINED
    )
    macro = _effect(tables, Representation.MCNDROID_STATIC, RepresentationGroup.PRIORITY_MACRO)
    assert macro.mean == pytest.approx(0.15, abs=0.01)


def test_empty_evidence_gives_empty_tables() -> None:
    tables = representation_tables(_families().clear(), CONFIG, EXPERIMENTS)
    assert tables.effects == () and tables.levels == () and tables.seeds.height == 0


def test_eligibility_report_lists_every_primary_family_and_marks_the_dropped_ones() -> None:
    planned = {
        RandomSeed(330): (TargetPair(client=ClientId.ANZHI, family="hiddad"),),
        RandomSeed(331): (),
    }
    table = eligibility_table(planned, ("hiddad", "adwo"))
    assert table.height == 4
    flags = {
        (row[Column.SEED], row[Column.FAMILY]): row[Column.ELIGIBLE]
        for row in table.iter_rows(named=True)
    }
    assert flags == {
        (330, "hiddad"): True,
        (330, "adwo"): False,
        (331, "hiddad"): False,
        (331, "adwo"): False,
    }
    assert table.filter(pl.col(Column.ELIGIBLE))[Column.CLIENT].to_list() == [ClientId.ANZHI]
