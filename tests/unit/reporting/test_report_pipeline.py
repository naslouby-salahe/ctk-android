from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import ctk_android.reporting.artifacts as artifacts
import ctk_android.workflows.report as workflow
from ctk_android.config import load_config
from ctk_android.data.cache import fingerprint_file, write_record
from ctk_android.enums import (
    CompletionState,
    EvidenceClass,
    ExecutionMode,
    ExperimentName,
    ExtensionStudy,
    FailureReason,
    PromotionBlock,
    PromotionState,
    ReportStage,
    ResultsDirectory,
    ResultsFile,
    RunStatus,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    CodeProvenance,
    CtkError,
    DataFingerprints,
    ExecutionRecord,
    ManifestEntry,
    PromotionDecision,
    RandomSeed,
    ResultsManifest,
    RunKey,
    RunState,
)
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
PROMOTED = PromotionDecision(state=PromotionState.PROMOTED, blocks=())
EXPECTED_ORDER = (
    ReportStage.DEVELOPMENT,
    ReportStage.CONFIRMATORY,
    ReportStage.HIDDEN_FAMILY,
    ReportStage.EXTENSION,
    ReportStage.LARGE_FAMILY,
    ReportStage.EXACT_DOSE,
    ReportStage.CONTROLS,
    ReportStage.REPRESENTATION,
    ReportStage.DIAGNOSTICS,
    ReportStage.EVIDENCE_FIGURES,
    ReportStage.VALIDATION,
)


def _typed_callback(callback: Callable[..., Any]) -> Callable[..., Any]:
    return callback


def test_report_stages_run_in_the_documented_dependency_order() -> None:
    assert tuple(ReportStage) == EXPECTED_ORDER


def test_every_stage_only_depends_on_stages_that_run_before_it() -> None:
    order = list(ReportStage)
    for stage in ReportStage:
        for required in workflow.stage_requirements(stage):
            assert order.index(required) < order.index(stage), (stage, required)


def test_the_dependency_graph_matches_what_each_analysis_reads() -> None:
    assert workflow.stage_requirements(ReportStage.HIDDEN_FAMILY) == (ReportStage.CONFIRMATORY,)
    assert set(workflow.stage_requirements(ReportStage.DIAGNOSTICS)) == {
        ReportStage.CONFIRMATORY,
        ReportStage.LARGE_FAMILY,
        ReportStage.EXACT_DOSE,
        ReportStage.CONTROLS,
        ReportStage.REPRESENTATION,
    }
    assert set(workflow.stage_requirements(ReportStage.EVIDENCE_FIGURES)) == {
        ReportStage.CONFIRMATORY,
        ReportStage.LARGE_FAMILY,
        ReportStage.EXACT_DOSE,
        ReportStage.CONTROLS,
        ReportStage.REPRESENTATION,
        ReportStage.DIAGNOSTICS,
    }
    assert set(workflow.stage_requirements(ReportStage.VALIDATION)) == set(ReportStage) - {
        ReportStage.VALIDATION
    }
    assert workflow.stage_requirements(ReportStage.DEVELOPMENT) == ()


def test_report_finishes_every_stage_once_and_in_order(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    ran: list[ReportStage] = []
    monkeypatch.setattr(workflow, "require_final_state", _typed_callback(lambda *_args: None))
    monkeypatch.setattr(
        workflow,
        "run_stage",
        _typed_callback(lambda _paths, _config, stage: ran.append(stage)),
    )
    finished = workflow.run_report(Paths(tmp_path), CONFIG)
    assert finished == EXPECTED_ORDER
    assert ran == list(EXPECTED_ORDER)


def test_report_checks_completeness_and_source_state_before_any_analysis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def refuse(*_args: object) -> None:
        raise CtkError(FailureReason.NO_COMPLETED_RUNS, "incomplete")

    monkeypatch.setattr(workflow, "require_final_state", _typed_callback(refuse))
    monkeypatch.setattr(
        workflow,
        "run_stage",
        _typed_callback(lambda *_args: pytest.fail("analysis ran before the preflight")),
    )
    with pytest.raises(CtkError):
        workflow.run_report(Paths(tmp_path), CONFIG)


def test_the_dispatcher_reaches_every_analysis_with_its_own_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[str, ExecutionMode | None]] = []

    def recorder(name: str) -> Callable[..., PromotionDecision]:
        def call(*args: object) -> PromotionDecision:
            mode = next((arg for arg in args if isinstance(arg, ExecutionMode)), None)
            calls.append((name, mode))
            return PROMOTED

        return call

    monkeypatch.setattr(
        workflow,
        "build_evidence_figures",
        _typed_callback(lambda *_args: calls.append(("build_evidence_figures", None))),
    )
    monkeypatch.setattr(
        workflow,
        "promote_evidence_figures",
        _typed_callback(
            lambda *_args: calls.append(("promote_evidence_figures", None)) or PROMOTED
        ),
    )
    for name in (
        "run_mode_report",
        "promote",
        "run_posthoc",
        "run_large_family",
        "run_dose_extension",
        "run_controls_extension",
        "run_representation_extension",
        "run_diagnostics",
    ):
        monkeypatch.setattr(workflow, name, _typed_callback(recorder(name)))
    monkeypatch.setattr(workflow, "validate_results", _typed_callback(lambda _paths: ()))
    paths = Paths(tmp_path)
    for stage in ReportStage:
        workflow.run_stage(paths, CONFIG, stage)
    assert calls == [
        ("run_mode_report", ExecutionMode.DEVELOPMENT),
        ("run_mode_report", ExecutionMode.CONFIRMATORY),
        ("promote", ExecutionMode.CONFIRMATORY),
        ("run_posthoc", ExecutionMode.CONFIRMATORY),
        ("run_mode_report", ExecutionMode.EXTENSION),
        ("promote", ExecutionMode.EXTENSION),
        ("run_large_family", ExecutionMode.EXTENSION_B),
        ("run_dose_extension", ExecutionMode.EXTENSION_B),
        ("run_controls_extension", ExecutionMode.EXTENSION_B),
        ("run_representation_extension", ExecutionMode.EXTENSION_B),
        ("run_diagnostics", ExecutionMode.EXTENSION_B),
        ("build_evidence_figures", None),
        ("promote_evidence_figures", None),
    ]


def test_a_blocked_publication_fails_the_report_instead_of_being_skipped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    blocked = PromotionDecision(
        state=PromotionState.BLOCKED, blocks=(PromotionBlock.PROVENANCE_STALE,)
    )
    monkeypatch.setattr(workflow, "run_mode_report", _typed_callback(lambda *_args: None))
    monkeypatch.setattr(workflow, "promote", _typed_callback(lambda *_args: blocked))
    with pytest.raises(CtkError) as raised:
        workflow.run_stage(Paths(tmp_path), CONFIG, ReportStage.CONFIRMATORY)
    assert raised.value.reason is FailureReason.EVIDENCE_BLOCKED
    assert PromotionBlock.PROVENANCE_STALE in f"{raised.value}"


def _states(*statuses: RunStatus) -> list[RunState]:
    experiment = ExperimentName.CONTROLLED_EXPOSURE
    return [
        RunState(
            key=RunKey(
                mode=ExecutionMode.CONFIRMATORY,
                experiment=experiment,
                seed=RandomSeed(seed),
                salt=0,
            ),
            status=status,
            intact=True,
        )
        for seed, status in enumerate(statuses, start=100)
    ]


def _execution(revision: str, clean: bool) -> ExecutionRecord:
    return ExecutionRecord(
        revision=revision,
        sources_clean=clean,
        executed_at=datetime.now(UTC),
        protocol="c" * 64,
        resolved_configuration="resolved",
        data=DataFingerprints(lamda="a" * 64, androzoo="b" * 64, mcndroid_inventory=None),
    )


def _bind_state(
    monkeypatch: pytest.MonkeyPatch,
    states: list[RunState],
    executions: list[ExecutionRecord | None],
    clean: bool = True,
) -> None:
    monkeypatch.setattr(
        artifacts.planning, "campaign_states", _typed_callback(lambda *_args: states)
    )
    monkeypatch.setattr(artifacts, "sources_are_clean", _typed_callback(lambda _paths: clean))
    monkeypatch.setattr(artifacts, "_executions", _typed_callback(lambda *_args: executions))


def test_final_state_requires_every_configured_run_to_be_completed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bind_state(monkeypatch, _states(RunStatus.COMPLETED, RunStatus.INCOMPLETE), [])
    with pytest.raises(CtkError) as raised:
        artifacts.require_final_state(Paths(tmp_path), CONFIG)
    assert raised.value.reason is FailureReason.NO_COMPLETED_RUNS
    assert "1 of 2" in f"{raised.value}"


def test_final_state_refuses_a_completed_run_whose_artifacts_are_damaged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    states = _states(RunStatus.COMPLETED)
    damaged = [state.model_copy(update={"intact": False}) for state in states]
    _bind_state(monkeypatch, damaged, [_execution("a" * 40, True)])
    with pytest.raises(CtkError) as raised:
        artifacts.require_final_state(Paths(tmp_path), CONFIG)
    assert raised.value.reason is FailureReason.NO_COMPLETED_RUNS


def test_final_state_refuses_a_dirty_worktree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bind_state(
        monkeypatch, _states(RunStatus.COMPLETED), [_execution("a" * 40, True)], clean=False
    )
    with pytest.raises(CtkError) as raised:
        artifacts.require_final_state(Paths(tmp_path), CONFIG)
    assert raised.value.reason is FailureReason.SOURCE_STATE


def test_final_state_refuses_runs_executed_from_dirty_sources(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bind_state(monkeypatch, _states(RunStatus.COMPLETED), [_execution("a" * 40, False)])
    with pytest.raises(CtkError) as raised:
        artifacts.require_final_state(Paths(tmp_path), CONFIG)
    assert raised.value.reason is FailureReason.SOURCE_STATE


def test_final_state_refuses_runs_from_more_than_one_source_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bind_state(
        monkeypatch,
        _states(RunStatus.COMPLETED, RunStatus.COMPLETED),
        [_execution("a" * 40, True), _execution("b" * 40, True)],
    )
    with pytest.raises(CtkError) as raised:
        artifacts.require_final_state(Paths(tmp_path), CONFIG)
    assert raised.value.reason is FailureReason.SOURCE_STATE


def test_final_state_accepts_one_clean_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _bind_state(
        monkeypatch,
        _states(RunStatus.COMPLETED, RunStatus.COMPLETED),
        [_execution("a" * 40, True), _execution("a" * 40, True)],
    )
    artifacts.require_final_state(Paths(tmp_path), CONFIG)


def _seed_results(paths: Paths) -> ManifestEntry:
    target = paths.results_file(ResultsDirectory.EVIDENCE, "table.csv")
    target.parent.mkdir(parents=True)
    target.write_text("value\n1\n", encoding="utf-8")
    entry = ManifestEntry(
        name="evidence/table.csv",
        digest=fingerprint_file(target),
        evidence_class=EvidenceClass.CONFIRMATORY_SEEDS,
    )
    write_record(
        paths.results_root_file(ResultsFile.MANIFEST),
        ResultsManifest(mode=ExecutionMode.CONFIRMATORY, files=(entry,)),
    )
    return entry


def _checks(paths: Paths) -> dict[ValidationCheck, bool]:
    return {record.check: record.passed for record in artifacts.validate_results(paths)}


def test_results_validation_detects_changed_and_unlisted_files(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    _seed_results(paths)
    checks = _checks(paths)
    assert checks[ValidationCheck.RESULTS_DIGESTS_MATCH]
    assert checks[ValidationCheck.RESULTS_NO_STRAY_FILES]
    assert not checks[ValidationCheck.RESULTS_STUDIES_RECORDED]
    assert not checks[ValidationCheck.RESULTS_CONFIRMATORY_COMPLETE]
    assert not checks[ValidationCheck.RESULTS_SOURCES_CLEAN]

    paths.results_file(ResultsDirectory.EVIDENCE, "table.csv").write_text("tampered\n")
    paths.results_file(ResultsDirectory.TABLES, "stray.csv").parent.mkdir(parents=True)
    paths.results_file(ResultsDirectory.TABLES, "stray.csv").write_text("x\n")
    tampered = _checks(paths)
    assert not tampered[ValidationCheck.RESULTS_DIGESTS_MATCH]
    assert not tampered[ValidationCheck.RESULTS_NO_STRAY_FILES]


def test_results_validation_writes_its_own_document_and_ignores_it_on_the_next_pass(
    tmp_path: Path,
) -> None:
    paths = Paths(tmp_path)
    _seed_results(paths)
    artifacts.validate_results(paths)
    assert paths.results_root_file(ResultsFile.VALIDATION).is_file()
    assert _checks(paths)[ValidationCheck.RESULTS_NO_STRAY_FILES]


def test_results_validation_needs_a_clean_analysis_revision(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    _seed_results(paths)
    code = paths.results_file(ResultsDirectory.PROVENANCE, ResultsFile.CODE)
    for clean in (False, True):
        write_record(
            code,
            CodeProvenance(
                execution_revision="a" * 40,
                analysis_revision="a" * 40,
                analysis_sources_clean=clean,
            ),
        )
        assert _checks(paths)[ValidationCheck.RESULTS_SOURCES_CLEAN] is clean


def test_every_study_must_be_recorded_before_results_are_valid() -> None:
    assert set(ExtensionStudy) == {
        ExtensionStudy.EXT_1,
        ExtensionStudy.LARGE_FAMILY,
        ExtensionStudy.DOSE,
        ExtensionStudy.CONTROLS,
        ExtensionStudy.REPRESENTATION,
        ExtensionStudy.DIAGNOSTICS,
    }


def test_completion_states_cover_the_status_summary() -> None:
    assert {state.value for state in CompletionState} == {"complete", "incomplete", "attention"}
