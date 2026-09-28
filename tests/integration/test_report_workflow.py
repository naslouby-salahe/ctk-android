import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import (
    Artifact,
    Column,
    ExecutionMode,
    FailureReason,
    FileSuffix,
    PromotionBlock,
    PromotionState,
    ReportFigure,
    ReportTable,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import collect_evidence, promote
from ctk_android.types import CtkError
from ctk_android.workflows.report import run_analysis, run_mode_report

MODE = ExecutionMode.DEVELOPMENT


def _require_development_runs(paths: Paths) -> None:
    if not paths.plan_file(MODE, Artifact.RUN_MATRIX).is_file():
        pytest.skip("development runs are not available; run the development plan first")


def test_report_regenerates_every_table_and_figure_from_saved_evidence(
    evidence_workspace: Paths,
) -> None:
    paths = evidence_workspace
    _require_development_runs(paths)
    config = load_config(paths)
    run_mode_report(paths, config, MODE)
    for table in ReportTable:
        assert paths.report_table_file(MODE, table).stat().st_size > 0
    for figure in ReportFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            assert paths.report_figure_file(MODE, figure, suffix).stat().st_size > 0
    decomposition = pl.read_csv(
        paths.report_table_file(MODE, ReportTable.COLLABORATION_DECOMPOSITION)
    )
    assert {Column.ALPHA, Column.P_HOLM, Column.CI_LOW, Column.CI_HIGH} <= set(
        decomposition.columns
    )


def test_promotion_is_blocked_outside_confirmatory_mode_and_writes_no_results(
    evidence_workspace: Paths,
) -> None:
    paths = evidence_workspace
    _require_development_runs(paths)
    config = load_config(paths)

    def snapshot() -> dict[str, int]:
        return {
            f"{path}": path.stat().st_mtime_ns
            for path in (paths.root / "results").rglob("*")
            if path.is_file()
        }

    before = snapshot()
    decision = promote(paths, config, MODE)
    assert decision.state is PromotionState.BLOCKED
    assert decision.blocks == (PromotionBlock.NOT_CONFIRMATORY,)
    assert snapshot() == before


def test_runs_made_under_a_different_configuration_are_stale_and_never_analysed(
    evidence_workspace: Paths,
) -> None:
    paths = evidence_workspace
    _require_development_runs(paths)
    config = load_config(paths)
    changed = config.model_copy(
        update={
            "experiments": config.experiments.model_copy(
                update={
                    "training": config.experiments.training.model_copy(
                        update={"local_epochs": config.experiments.training.local_epochs + 1}
                    )
                }
            )
        }
    )
    evidence = collect_evidence(paths, changed, MODE, fairness=False)
    completed = evidence.index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED).height
    assert completed == 0
    assert evidence.index.filter(pl.col(Column.STATUS) == RunStatus.STALE).height > 0
    with pytest.raises(CtkError) as failure:
        run_analysis(paths, changed, MODE)
    assert failure.value.reason is FailureReason.NO_COMPLETED_RUNS
