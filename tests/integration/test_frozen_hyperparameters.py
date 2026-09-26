import pytest

from ctk_android.analysis.post_confirmatory import frozen_drift, select_hyperparameters
from ctk_android.config import load_config
from ctk_android.enums import Artifact, ExecutionMode
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import collect_evidence
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)
MODE = ExecutionMode.DEVELOPMENT


def test_frozen_hyperparameters_equal_the_selection_from_saved_development_evidence() -> None:
    if not PATHS.plan_file(MODE, Artifact.RUN_MATRIX).is_file():
        pytest.skip("development runs are not available; run the development plan first")
    config = load_config(PATHS)
    evidence = collect_evidence(PATHS, config, MODE, fairness=True)
    if evidence.summary.height == 0:
        pytest.skip(
            "no current fairness-grid runs; re-run baseline-fairness on the development seeds"
        )
    selection = select_hyperparameters(evidence.summary, config.experiments.operating.primary_alpha)
    assert frozen_drift(selection, config.experiments.training) == []


def test_every_frozen_value_is_a_member_of_its_predeclared_grid() -> None:
    config = load_config(PATHS)
    grids, training = config.experiments.fairness_grids, config.experiments.training
    assert training.local_epochs in grids.local_epochs
    assert training.finetune_epochs in grids.finetune_epochs
    assert training.fedprox_mu in grids.fedprox_mu
