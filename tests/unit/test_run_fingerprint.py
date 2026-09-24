from ctk_android.config import load_config
from ctk_android.enums import ExecutionMode, ExperimentName, LogLevel
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.DEVELOPMENT
SPEC = CONFIG.experiments.experiments[ExperimentName.CONTROLLED_EXPOSURE]
BASE = CONFIG.run_fingerprint(SPEC, MODE)


def _with_experiments(**changes: object) -> str:
    experiments = CONFIG.experiments.model_copy(update=changes)
    return CONFIG.model_copy(update={"experiments": experiments}).run_fingerprint(SPEC, MODE)


def test_statistics_and_logging_settings_do_not_invalidate_runs() -> None:
    gates = CONFIG.statistics.gates.model_copy(update={"ctk_min_gain": 0.5})
    statistics = CONFIG.statistics.model_copy(update={"gates": gates, "bootstrap_resamples": 99})
    project = CONFIG.project.model_copy(update={"logging_level": LogLevel.DEBUG})
    changed = CONFIG.model_copy(update={"statistics": statistics, "project": project})
    assert changed.run_fingerprint(SPEC, MODE) == BASE


def test_another_experiments_settings_do_not_invalidate_this_run() -> None:
    specs = dict(CONFIG.experiments.experiments)
    other = ExperimentName.NATURAL_SCARCITY
    specs[other] = specs[other].model_copy(update={"salts": (0, 7)})
    assert _with_experiments(experiments=specs) == BASE


def test_hyperparameters_of_the_resolved_training_config_invalidate_runs() -> None:
    training = CONFIG.experiments.training.model_copy(update={"fedprox_mu": 0.5})
    assert _with_experiments(training=training) != BASE


def test_smoke_runs_are_not_affected_by_full_training_hyperparameters() -> None:
    smoke_spec = CONFIG.experiments.experiments[ExperimentName.END_TO_END]
    before = CONFIG.run_fingerprint(smoke_spec, ExecutionMode.SMOKE)
    training = CONFIG.experiments.training.model_copy(update={"local_epochs": 99})
    experiments = CONFIG.experiments.model_copy(update={"training": training})
    after = CONFIG.model_copy(update={"experiments": experiments}).run_fingerprint(
        smoke_spec, ExecutionMode.SMOKE
    )
    assert before == after


def test_the_experiments_own_spec_and_budget_invalidate_runs() -> None:
    changed_spec = SPEC.model_copy(update={"salts": (0, 1)})
    assert CONFIG.run_fingerprint(changed_spec, MODE) != BASE
    budgets = dict(CONFIG.experiments.budgets)
    budgets[SPEC.budget] = budgets[SPEC.budget] + 1
    assert _with_experiments(budgets=budgets) != BASE


def test_the_data_configuration_invalidates_runs() -> None:
    data = CONFIG.data.model_copy(update={"play_era_boundary": "2020-01"})
    assert CONFIG.model_copy(update={"data": data}).run_fingerprint(SPEC, MODE) != BASE
