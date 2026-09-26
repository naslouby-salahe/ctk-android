from pathlib import Path

import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import (
    Artifact,
    Column,
    ExecutionMode,
    ExperimentName,
    ExtensionStudy,
    PromotionBlock,
    PromotionState,
    ResultsFile,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import collect_placebo_pairs, promote_extension_design
from ctk_android.types import CtkError, DesignPromotion, RandomSeed, RunKey
from ctk_android.workflows.report import run_controls_extension, run_dose_extension
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
NAME = ExperimentName.PLACEBO_ROBUST_PRIMARY


def _write_pairs(paths: Paths, seed: RandomSeed) -> None:
    file = paths.run_file(
        RunKey(mode=MODE, experiment=NAME, seed=seed, salt=0), Artifact.PLACEBO_PAIRS
    )
    file.parent.mkdir(parents=True)
    pl.DataFrame({Column.FAMILY: [f"hidden-{seed}"], Column.RANK: [seed]}).write_parquet(file)


def test_placebo_pairs_are_collected_only_for_completed_runs(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    for seed in (RandomSeed(320), RandomSeed(321)):
        _write_pairs(paths, seed)
    index = pl.DataFrame(
        {
            Column.EXPERIMENT: [NAME, NAME],
            Column.SEED: [320, 321],
            Column.SALT: [0, 0],
            Column.STATUS: [RunStatus.COMPLETED, RunStatus.FAILED_VALIDATION],
        }
    )
    collected = collect_placebo_pairs(paths, index, MODE)
    assert collected[Column.SEED].to_list() == [320]
    assert collected[Column.EXPERIMENT].to_list() == [NAME]
    assert collect_placebo_pairs(paths, index.clear(), MODE).height == 0


def test_the_analysis_commands_refuse_to_run_without_completed_runs(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    with pytest.raises(CtkError):
        run_dose_extension(paths, CONFIG, MODE, False)
    with pytest.raises(CtkError):
        run_controls_extension(paths, CONFIG, MODE, False)


def test_promotion_is_limited_to_the_extension_b_mode(tmp_path: Path) -> None:
    decision = promote_extension_design(
        Paths(tmp_path),
        CONFIG,
        ExecutionMode.CONFIRMATORY,
        DesignPromotion(
            study=ExtensionStudy.CONTROLS,
            experiments=(NAME,),
            index_artifact=Artifact.CONTROLS_RUN_INDEX,
            artifacts=(Artifact.CONTROLS_EFFECTS,),
            code_file=ResultsFile.CONTROLS_CODE,
        ),
    )
    assert decision.state is PromotionState.BLOCKED
    assert decision.blocks == (PromotionBlock.NOT_EXTENSION_B,)
