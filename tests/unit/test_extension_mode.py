from ctk_android.config import load_config
from ctk_android.enums import ExecutionMode, ExperimentName
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
SEEDS = CONFIG.project.seeds


def test_extension_seeds_are_fresh_and_disjoint_from_every_earlier_role() -> None:
    earlier = {*SEEDS.smoke, *SEEDS.development, *SEEDS.confirmatory}
    assert SEEDS.extension
    assert not earlier & set(SEEDS.extension)
    assert SEEDS.for_mode(ExecutionMode.EXTENSION) == SEEDS.extension


def test_only_declared_experiments_run_in_extension_mode() -> None:
    experiments = CONFIG.experiments
    assert experiments.runs_in(ExperimentName.FAMILY_PERMUTATION_CONTROL, ExecutionMode.EXTENSION)
    assert not experiments.runs_in(ExperimentName.CONTROLLED_EXPOSURE, ExecutionMode.EXTENSION)


def test_the_extension_does_not_change_an_original_experiment_run_fingerprint() -> None:
    spec = CONFIG.experiments.experiments[ExperimentName.FAMILY_PERMUTATION_CONTROL]
    assert CONFIG.run_fingerprint(spec, ExecutionMode.EXTENSION) == CONFIG.run_fingerprint(
        spec, ExecutionMode.CONFIRMATORY
    )
    assert ExecutionMode.EXTENSION not in spec.modes
