import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import (
    Artifact,
    ClaimName,
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
from ctk_android.reporting.records import collect_evidence
from ctk_android.types import CtkError
from ctk_android.workflows.report import run_analysis, run_report
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)
MODE = ExecutionMode.DEVELOPMENT


def _require_development_runs() -> None:
    if not PATHS.plan_file(MODE, Artifact.RUN_MATRIX).is_file():
        pytest.skip("development runs are not available; run the development plan first")


def test_report_regenerates_every_table_and_figure_from_saved_evidence() -> None:
    _require_development_runs()
    config = load_config(PATHS)
    decision = run_report(PATHS, config, MODE, promote_evidence=False)
    assert decision is None
    for table in ReportTable:
        assert PATHS.report_table_file(MODE, table).stat().st_size > 0
    for figure in ReportFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            assert PATHS.report_figure_file(MODE, figure, suffix).stat().st_size > 0
    decomposition = pl.read_csv(
        PATHS.report_table_file(MODE, ReportTable.COLLABORATION_DECOMPOSITION)
    )
    assert {Column.ALPHA, Column.P_HOLM, Column.CI_LOW, Column.CI_HIGH} <= set(
        decomposition.columns
    )


def test_every_planned_claim_receives_an_outcome_and_the_report_is_deterministic() -> None:
    _require_development_runs()
    config = load_config(PATHS)
    first = run_analysis(PATHS, config, MODE)
    second = run_analysis(PATHS, config, MODE)
    assert set(first[Column.CLAIM].to_list()) == set(ClaimName)
    assert first.equals(second)


def test_promotion_is_blocked_outside_confirmatory_mode_and_writes_no_results() -> None:
    _require_development_runs()
    config = load_config(PATHS)
    decision = run_report(PATHS, config, MODE, promote_evidence=True)
    assert decision is not None
    assert decision.state is PromotionState.BLOCKED
    assert decision.blocks == (PromotionBlock.NOT_CONFIRMATORY,)
    assert not (REPO_ROOT / "results").exists()


def test_runs_made_under_a_different_configuration_are_stale_and_never_analysed() -> None:
    _require_development_runs()
    config = load_config(PATHS)
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
    evidence = collect_evidence(PATHS, changed, MODE, fairness=False)
    completed = evidence.index.filter(pl.col(Column.STATUS) == RunStatus.COMPLETED).height
    assert completed == 0
    assert evidence.index.filter(pl.col(Column.STATUS) == RunStatus.STALE).height > 0
    with pytest.raises(CtkError) as failure:
        run_analysis(PATHS, changed, MODE)
    assert failure.value.reason is FailureReason.NO_COMPLETED_RUNS
