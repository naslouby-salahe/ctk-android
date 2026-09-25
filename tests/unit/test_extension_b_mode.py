from ctk_android.config import load_config
from ctk_android.data.families import large_family_sets
from ctk_android.enums import ExecutionMode, ExperimentName
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
SEEDS = CONFIG.project.seeds
LARGE = CONFIG.experiments.extension_b_experiments


def test_extension_b_seeds_are_fresh_and_disjoint_from_every_earlier_role() -> None:
    earlier = {*SEEDS.smoke, *SEEDS.development, *SEEDS.confirmatory, *SEEDS.extension}
    assert SEEDS.extension_b
    assert not earlier & set(SEEDS.extension_b)
    assert SEEDS.for_mode(ExecutionMode.EXTENSION_B) == SEEDS.extension_b


def test_extension_b_runs_only_the_large_family_experiments() -> None:
    experiments = CONFIG.experiments
    assert len(LARGE) == len(large_family_sets())
    for name in LARGE:
        assert experiments.runs_in(name, ExecutionMode.EXTENSION_B)
        assert experiments.runs_in(name, ExecutionMode.DEVELOPMENT)
        assert not experiments.runs_in(name, ExecutionMode.CONFIRMATORY)
        assert not experiments.runs_in(name, ExecutionMode.EXTENSION)
    assert not experiments.runs_in(ExperimentName.CONTROLLED_EXPOSURE, ExecutionMode.EXTENSION_B)
    assert not experiments.runs_in(
        ExperimentName.FAMILY_PERMUTATION_CONTROL, ExecutionMode.EXTENSION_B
    )


def test_each_large_experiment_owns_one_batch_and_shares_the_controlled_design() -> None:
    controlled = CONFIG.experiments.experiments[ExperimentName.CONTROLLED_EXPOSURE]
    owned = [CONFIG.experiments.experiments[name] for name in LARGE]
    assert {spec.family_set for spec in owned} == set(large_family_sets())
    for spec in owned:
        assert (
            spec.model_copy(
                update={
                    "family_set": controlled.family_set,
                    "modes": controlled.modes,
                    "learners": controlled.learners,
                }
            )
            == controlled
        )
