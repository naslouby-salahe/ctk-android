from pathlib import Path

import pytest

from ctk_android.config import load_config
from ctk_android.data.cache import write_record, write_table
from ctk_android.enums import (
    Artifact,
    CompletionState,
    ExecutionMode,
    ExperimentName,
    RunStatus,
)
from ctk_android.experiment import planning
from ctk_android.paths import Paths
from ctk_android.types import RunKey, RunStatusDocument
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
FROZEN_RUNS_PER_MODE = {
    ExecutionMode.SMOKE: 11,
    ExecutionMode.DEVELOPMENT: 65,
    ExecutionMode.CONFIRMATORY: 140,
    ExecutionMode.EXTENSION: 10,
    ExecutionMode.EXTENSION_B: 120,
}


@pytest.mark.parametrize(("mode", "runs"), list(FROZEN_RUNS_PER_MODE.items()))
def test_each_scope_keeps_its_frozen_run_count(mode: ExecutionMode, runs: int) -> None:
    keys = CONFIG.mode_keys(mode)
    assert len(keys) == runs
    assert len(set(keys)) == runs
    assert all(key.mode is mode for key in keys)


def test_the_campaign_is_every_scope_except_smoke() -> None:
    campaign = [
        key for name in CONFIG.experiments.experiments for key in CONFIG.campaign_keys(name)
    ]
    assert len(campaign) == sum(
        runs for mode, runs in FROZEN_RUNS_PER_MODE.items() if mode is not ExecutionMode.SMOKE
    )
    assert not [key for key in campaign if key.mode is ExecutionMode.SMOKE]


def test_the_campaign_and_the_per_mode_plans_enumerate_the_same_runs() -> None:
    by_experiment = {
        key.model_dump_json()
        for name in CONFIG.experiments.experiments
        for key in CONFIG.experiment_keys(name)
    }
    by_mode = {key.model_dump_json() for mode in ExecutionMode for key in CONFIG.mode_keys(mode)}
    assert by_experiment == by_mode


def test_seeds_and_salts_come_from_the_configuration_only() -> None:
    keys = CONFIG.campaign_keys(ExperimentName.PARTITION_SALT_SENSITIVITY)
    assert {key.salt for key in keys} == {1, 2, 3}
    assert {key.seed for key in keys} == set(CONFIG.project.seeds.confirmatory)
    dose = CONFIG.campaign_keys(ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY)
    assert {key.seed for key in dose} == set(CONFIG.project.seeds.extension_dose)
    controls = CONFIG.campaign_keys(ExperimentName.PLACEBO_ROBUST_PRIMARY)
    assert {key.seed for key in controls} == set(CONFIG.project.seeds.extension_controls)
    representation = CONFIG.campaign_keys(ExperimentName.REPRESENTATION_R2)
    assert {key.seed for key in representation if key.mode is ExecutionMode.EXTENSION_B} == set(
        CONFIG.project.seeds.extension_representation
    )


def test_status_reports_every_campaign_experiment_as_missing_before_any_run(
    tmp_path: Path,
) -> None:
    status = planning.campaign_status(Paths(tmp_path), CONFIG)
    assert {item.experiment for item in status.experiments} == {
        name for name in CONFIG.experiments.experiments if CONFIG.experiments.campaign_modes(name)
    }
    assert ExperimentName.END_TO_END not in {item.experiment for item in status.experiments}
    assert status.total.expected == sum(item.counts.expected for item in status.experiments)
    assert status.total.missing == status.total.expected
    assert status.total.completed == 0
    assert status.total.state is CompletionState.INCOMPLETE
    assert not (tmp_path / "outputs").exists()


def _write_run(paths: Paths, key: RunKey, status: RunStatus, complete: bool) -> None:
    write_record(
        paths.run_file(key, Artifact.STATUS), RunStatusDocument(status=status, reason=None)
    )
    if complete:
        for file in (
            paths.run_file(key, Artifact.MANIFEST),
            paths.run_file(key, Artifact.VALIDATION),
            paths.provenance_file(paths.run_dir(key)),
        ):
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text("{}", encoding="utf-8")
        import polars as pl

        write_table(pl.DataFrame(), paths.run_metric_file(key, Artifact.SUMMARY))


def test_status_distinguishes_completed_failed_invalid_and_missing_runs(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    experiment = ExperimentName.NATURAL_SCARCITY
    keys = CONFIG.campaign_keys(experiment)
    _write_run(paths, keys[0], RunStatus.COMPLETED, complete=True)
    _write_run(paths, keys[1], RunStatus.FAILED_VALIDATION, complete=True)
    _write_run(paths, keys[2], RunStatus.COMPLETED, complete=False)
    paths.run_file(keys[3], Artifact.STATUS).parent.mkdir(parents=True)
    paths.run_file(keys[3], Artifact.STATUS).write_text("not json", encoding="utf-8")
    _write_run(paths, keys[4], RunStatus.INFEASIBLE, complete=False)

    status = planning.campaign_status(paths, CONFIG)
    counts = next(item.counts for item in status.experiments if item.experiment is experiment)
    assert counts.expected == len(keys)
    assert (counts.completed, counts.failed, counts.invalid, counts.infeasible) == (1, 1, 2, 1)
    assert counts.missing == len(keys) - 5
    assert counts.state is CompletionState.ATTENTION
    assert status.total.state is CompletionState.ATTENTION
