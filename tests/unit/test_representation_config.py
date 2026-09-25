from ctk_android.config import load_config
from ctk_android.enums import ExecutionMode, ExperimentDesign, ExperimentName, Representation
from ctk_android.paths import Paths
from ctk_android.types import PartitionKey
from ctk_android.workflows.preprocess import required_partition_keys
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
EXPERIMENTS = CONFIG.experiments
NAMES = {
    ExperimentName.REPRESENTATION_R0: Representation.LAMDA_STATIC,
    ExperimentName.REPRESENTATION_R1: Representation.MCNDROID_STATIC,
    ExperimentName.REPRESENTATION_R2: Representation.CALL_GRAPH,
    ExperimentName.REPRESENTATION_R3: Representation.REPORT_JSON,
}
EXTENSION_SEEDS = tuple(range(330, 340))
OTHER_SEED_RANGES = (100, 200, 300, 310, 320)


def test_the_four_experiments_differ_only_in_representation() -> None:
    specs = {name: EXPERIMENTS.experiments[name] for name in NAMES}
    assert {name: spec.representation for name, spec in specs.items()} == NAMES
    stripped = [spec.model_copy(update={"representation": None}) for spec in specs.values()]
    assert all(item == stripped[0] for item in stripped)
    only = stripped[0]
    assert only.design is ExperimentDesign.REPRESENTATION
    assert only.family_set == EXPERIMENTS.experiments[ExperimentName.CONTROLLED_EXPOSURE].family_set
    assert only.budget == EXPERIMENTS.experiments[ExperimentName.CONTROLLED_EXPOSURE].budget
    assert (
        only.eligibility == EXPERIMENTS.experiments[ExperimentName.CONTROLLED_EXPOSURE].eligibility
    )


def test_experiments_run_in_development_and_extension_b_only_with_fresh_seeds() -> None:
    for name in NAMES:
        assert EXPERIMENTS.runs_in(name, ExecutionMode.EXTENSION_B)
        assert EXPERIMENTS.runs_in(name, ExecutionMode.DEVELOPMENT)
        for mode in (ExecutionMode.CONFIRMATORY, ExecutionMode.EXTENSION, ExecutionMode.SMOKE):
            assert not EXPERIMENTS.runs_in(name, mode)
        assert CONFIG.seeds_for(name, ExecutionMode.EXTENSION_B) == EXTENSION_SEEDS
        assert CONFIG.seeds_for(name, ExecutionMode.DEVELOPMENT) == CONFIG.project.seeds.development
    other = {
        seed
        for mode in ExecutionMode
        for name in EXPERIMENTS.experiments
        if EXPERIMENTS.experiments[name].design is not ExperimentDesign.REPRESENTATION
        for seed in CONFIG.seeds_for(name, mode)
    }
    assert not other & set(EXTENSION_SEEDS)
    assert all(seed // 10 != start // 10 for start in OTHER_SEED_RANGES for seed in EXTENSION_SEEDS)


def test_representation_fingerprints_differ_and_ignore_no_other_experiment() -> None:
    fingerprints = {
        CONFIG.run_fingerprint(EXPERIMENTS.experiments[name], ExecutionMode.EXTENSION_B)
        for name in NAMES
    }
    assert len(fingerprints) == len(NAMES)
    for name, spec in EXPERIMENTS.experiments.items():
        if name not in NAMES:
            assert "representation" not in spec.model_dump_json(exclude_defaults=True)


def test_representation_experiments_never_need_standard_partitions() -> None:
    keys = required_partition_keys(CONFIG)
    assert all(isinstance(key, PartitionKey) for key in keys)
    assert not {key.seed for key in keys} & set(EXTENSION_SEEDS)


def test_the_frozen_family_sets_and_prevalence_rule_are_configured() -> None:
    assert EXPERIMENTS.representation_priority_families == ("hiddad", "gappusin", "revmob")
    assert EXPERIMENTS.representation_contrast_families == ("leadbolt", "airpush", "dowgin")
    assert EXPERIMENTS.representation_separate_families == ("adwo",)
    assert EXPERIMENTS.representation_focus_family == "hiddad"
    assert EXPERIMENTS.representation_min_prevalence == 0.01
