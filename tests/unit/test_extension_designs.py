import hashlib

from ctk_android.config import load_config
from ctk_android.enums import (
    EligibilityProfile,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    Separator,
)
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
SEEDS = CONFIG.project.seeds
EXPERIMENTS = CONFIG.experiments
DOSE = (
    ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY,
    ExperimentName.EXACT_EFFECTIVE_DOSE_REPLICATION,
)
CONTROLS = (
    ExperimentName.PLACEBO_ROBUST_PRIMARY,
    ExperimentName.PLACEBO_ROBUST_REPLICATION,
)
REPRESENTATION = (
    ExperimentName.REPRESENTATION_R0,
    ExperimentName.REPRESENTATION_R1,
    ExperimentName.REPRESENTATION_R2,
    ExperimentName.REPRESENTATION_R3,
)
MODE = ExecutionMode.EXTENSION_B


def _legacy_fingerprint(name: ExperimentName, mode: ExecutionMode) -> str:
    spec = EXPERIMENTS.experiments[name]
    parts = (
        CONFIG.data.model_dump_json(exclude={"eligibility": {EligibilityProfile.DOSE}}),
        CONFIG.training_for(mode).model_dump_json(),
        spec.model_dump_json(exclude={"design", "representation"}),
        EXPERIMENTS.operating.model_dump_json(),
        EXPERIMENTS.novelty.model_dump_json(),
        EXPERIMENTS.fairness_grids.model_dump_json(),
        f"{EXPERIMENTS.budgets[spec.budget]}",
        f"{EXPERIMENTS.dose_levels}{EXPERIMENTS.dose_include_all_available}",
        f"{EXPERIMENTS.permutation_seed_offset}",
    )
    return hashlib.sha256(Separator.NEWLINE.join(parts).encode()).hexdigest()


def test_extension_seed_ranges_are_fresh_disjoint_and_ordered() -> None:
    assert SEEDS.extension_b == tuple(range(300, 310))
    assert SEEDS.extension_dose == tuple(range(310, 320))
    assert SEEDS.extension_controls == tuple(range(320, 330))
    assert SEEDS.extension_representation == tuple(range(330, 340))
    assert SEEDS.for_mode(MODE) == SEEDS.extension_b


def test_each_experiment_runs_only_on_its_own_extension_seed_range() -> None:
    for name in EXPERIMENTS.extension_b_experiments:
        assert CONFIG.seeds_for(name, MODE) == SEEDS.extension_b
    for name in DOSE:
        assert CONFIG.seeds_for(name, MODE) == SEEDS.extension_dose
    for name in CONTROLS:
        assert CONFIG.seeds_for(name, MODE) == SEEDS.extension_controls
    assert CONFIG.seeds_for(ExperimentName.CONTROLLED_EXPOSURE, ExecutionMode.CONFIRMATORY) == (
        SEEDS.confirmatory
    )


def test_designed_experiments_run_only_in_extension_b() -> None:
    for name in (*DOSE, *CONTROLS):
        assert EXPERIMENTS.runs_in(name, MODE)
        assert not EXPERIMENTS.runs_in(name, ExecutionMode.CONFIRMATORY)
        assert not EXPERIMENTS.runs_in(name, ExecutionMode.EXTENSION)
    assert not any(
        EXPERIMENTS.runs_in(name, MODE)
        for name in EXPERIMENTS.experiments
        if name not in (*DOSE, *CONTROLS, *REPRESENTATION, *EXPERIMENTS.extension_b_experiments)
    )


def test_legacy_run_fingerprints_ignore_the_design_fields_and_the_dose_profile() -> None:
    legacy = [
        name
        for name, spec in EXPERIMENTS.experiments.items()
        if spec.design is ExperimentDesign.STANDARD
    ]
    assert ExperimentName.CONTROLLED_EXPOSURE in legacy
    for name in legacy:
        for mode in ExecutionMode:
            assert CONFIG.run_fingerprint(EXPERIMENTS.experiments[name], mode) == (
                _legacy_fingerprint(name, mode)
            )


def test_dose_profile_is_the_primary_rule_with_the_larger_peer_minimum() -> None:
    primary = CONFIG.data.eligibility[EligibilityProfile.PRIMARY]
    dose = CONFIG.data.eligibility[EligibilityProfile.DOSE]
    assert dose.peer_min_fit == max(EXPERIMENTS.exact_dose_levels)
    assert dose.model_copy(update={"peer_min_fit": primary.peer_min_fit}) == primary


def test_stable_data_fingerprint_ignores_only_the_dose_profile() -> None:
    plain = CONFIG.data.model_dump_json(exclude={"eligibility": {EligibilityProfile.DOSE}})
    assert CONFIG.data.stable_json() == plain
    assert CONFIG.data.stable_fingerprint() == hashlib.sha256(plain.encode()).hexdigest()
    changed = CONFIG.data.eligibility[EligibilityProfile.PRIMARY].model_copy(
        update={"peer_min_fit": 1}
    )
    other = CONFIG.data.model_copy(
        update={"eligibility": {**CONFIG.data.eligibility, EligibilityProfile.PRIMARY: changed}}
    )
    assert other.stable_fingerprint() != CONFIG.data.stable_fingerprint()


def test_design_experiments_share_the_controlled_design_and_declare_their_arms() -> None:
    controlled = EXPERIMENTS.experiments[ExperimentName.CONTROLLED_EXPOSURE]
    for name in (*DOSE, *CONTROLS):
        spec = EXPERIMENTS.experiments[name]
        assert (spec.grouping, spec.budget, spec.salts, spec.exposure_mode) == (
            controlled.grouping,
            controlled.budget,
            controlled.salts,
            controlled.exposure_mode,
        )
    for name in DOSE:
        spec = EXPERIMENTS.experiments[name]
        assert spec.design is ExperimentDesign.EXACT_DOSE
        assert spec.eligibility is EligibilityProfile.DOSE
        assert ExposureCondition.EXACT_DOSE in spec.conditions
    for name in CONTROLS:
        spec = EXPERIMENTS.experiments[name]
        assert spec.design is ExperimentDesign.PLACEBO_ROBUST
        assert spec.eligibility is EligibilityProfile.PRIMARY
        assert ExposureCondition.PLACEBO in spec.conditions


def test_design_parameters_and_eligibility_rule_enter_the_run_fingerprint() -> None:
    spec = EXPERIMENTS.experiments[DOSE[0]]
    base = CONFIG.run_fingerprint(spec, MODE)
    levels = EXPERIMENTS.model_copy(update={"exact_dose_levels": (0, 5)})
    assert CONFIG.model_copy(update={"experiments": levels}).run_fingerprint(spec, MODE) != base
    rule = CONFIG.data.eligibility[EligibilityProfile.DOSE].model_copy(update={"peer_min_fit": 5})
    data = CONFIG.data.model_copy(
        update={"eligibility": {**CONFIG.data.eligibility, EligibilityProfile.DOSE: rule}}
    )
    assert CONFIG.model_copy(update={"data": data}).run_fingerprint(spec, MODE) != base
    control = EXPERIMENTS.experiments[CONTROLS[0]]
    trim = EXPERIMENTS.model_copy(update={"robust_trim_per_side": 2})
    assert CONFIG.model_copy(update={"experiments": trim}).run_fingerprint(
        control, MODE
    ) != CONFIG.run_fingerprint(control, MODE)
