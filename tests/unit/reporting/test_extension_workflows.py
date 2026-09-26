from pathlib import Path

# Pyright cannot infer callback signatures for monkeypatch lambda stubs.
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false
from types import SimpleNamespace

import polars as pl
import pytest

import ctk_android.workflows.report as workflow
from ctk_android.config import load_config
from ctk_android.data.cache import write_table
from ctk_android.enums import Artifact, ExecutionMode, ExperimentName, ExtensionStudy, Stage
from ctk_android.paths import Paths
from ctk_android.types import DesignPromotion, RunEvidence
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
EMPTY = pl.DataFrame()
EVIDENCE = RunEvidence(
    index=EMPTY,
    summary=pl.DataFrame({"present": [True]}),
    clients=EMPTY,
    families=EMPTY,
    exposure=EMPTY,
    novelty=EMPTY,
)


def _shared(monkeypatch: pytest.MonkeyPatch) -> list[tuple[Path, pl.DataFrame]]:
    writes: list[tuple[Path, pl.DataFrame]] = []
    monkeypatch.setattr(workflow, "collect_evidence", lambda *_args, **_kwargs: EVIDENCE)
    monkeypatch.setattr(workflow, "write_table", lambda table, path: writes.append((path, table)))
    monkeypatch.setattr(workflow, "records_to_frame", lambda _rows: EMPTY)
    return writes


def test_dose_extension_writes_all_outputs_and_builds_promotion_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    writes = _shared(monkeypatch)
    names = (ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY,)
    monkeypatch.setattr(workflow, "dose_experiments", lambda *_args: names)
    monkeypatch.setattr(
        workflow, "dose_effects", lambda *_args: SimpleNamespace(seeds=EMPTY, rows=[])
    )
    monkeypatch.setattr(workflow, "dose_family_curves", lambda *_args: EMPTY)
    monkeypatch.setattr(workflow, "dose_consistency", lambda *_args: EMPTY)
    monkeypatch.setattr(workflow, "dose_verdicts", lambda *_args: EMPTY)
    requests: list[DesignPromotion] = []
    monkeypatch.setattr(
        workflow,
        "promote_extension_design",
        lambda _paths, _config, _mode, request: requests.append(request) or "promoted",
    )

    assert workflow.run_dose_extension(Paths(tmp_path), CONFIG, MODE, False) is None
    assert len(writes) == 6
    assert workflow.run_dose_extension(Paths(tmp_path), CONFIG, MODE, True) == "promoted"
    assert requests[0].study is ExtensionStudy.DOSE
    assert requests[0].index_artifact is Artifact.DOSE_RUN_INDEX
    assert len(requests[0].artifacts) == 5


def test_controls_extension_collects_placebos_and_writes_five_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    writes = _shared(monkeypatch)
    names = (ExperimentName.PLACEBO_ROBUST_PRIMARY,)
    monkeypatch.setattr(workflow, "controls_experiments", lambda *_args: names)
    monkeypatch.setattr(
        workflow,
        "controls_effects",
        lambda *_args: SimpleNamespace(seeds=EMPTY, rows=[]),
    )
    monkeypatch.setattr(workflow, "collect_placebo_pairs", lambda *_args: EMPTY)
    monkeypatch.setattr(workflow, "placebo_table", lambda _table: EMPTY)
    monkeypatch.setattr(workflow, "controls_verdicts", lambda *_args: EMPTY)
    promotion: list[DesignPromotion] = []
    monkeypatch.setattr(
        workflow,
        "promote_extension_design",
        lambda _paths, _config, _mode, request: promotion.append(request) or "done",
    )

    assert workflow.run_controls_extension(Paths(tmp_path), CONFIG, MODE, False) is None
    assert len(writes) == 5
    assert workflow.run_controls_extension(Paths(tmp_path), CONFIG, MODE, True) == "done"
    assert promotion[0].index_artifact is Artifact.CONTROLS_RUN_INDEX


def test_representation_extension_builds_seed_targets_and_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    writes = _shared(monkeypatch)
    names = workflow.representation_experiments(CONFIG, MODE)
    assert names
    monkeypatch.setattr(workflow, "representation_experiments", lambda *_args: names)
    monkeypatch.setattr(workflow, "planned_targets", lambda *_args: SimpleNamespace(targets=()))
    monkeypatch.setattr(workflow, "read_family_set", lambda *_args: ("family",))
    monkeypatch.setattr(
        workflow,
        "representation_tables",
        lambda *_args: SimpleNamespace(seeds=EMPTY, effects=[], levels=[]),
    )
    monkeypatch.setattr(workflow, "representation_verdicts", lambda *_args: EMPTY)

    result = workflow.run_representation_extension(Paths(tmp_path), CONFIG, MODE, False)

    assert result is None
    assert len(writes) == 6
    assert all(path.parent.name == MODE for path, _ in writes)


def test_large_family_analysis_writes_metrics_and_stability_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    writes = _shared(monkeypatch)
    frame = pl.DataFrame({"value": [1.0]})
    monkeypatch.setattr(workflow, "_planned_families", lambda *_args: 4)
    monkeypatch.setattr(workflow, "_fresh_seed_pairs", lambda *_args: {})
    monkeypatch.setattr(workflow, "large_seed_effects", lambda *_args: frame)
    monkeypatch.setattr(workflow, "large_family_table", lambda *_args: frame)
    monkeypatch.setattr(workflow, "large_family_summary", lambda *_args: frame)
    monkeypatch.setattr(workflow, "stability_seed_table", lambda *_args: frame)
    monkeypatch.setattr(workflow, "eligibility_stability_table", lambda *_args: frame)
    monkeypatch.setattr(workflow, "eligibility_stability_summary", lambda *_args: frame)
    write_table(EMPTY, Paths(tmp_path).stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION))

    result = workflow.run_large_family(Paths(tmp_path), CONFIG, MODE, False)

    assert result is None
    assert len(writes) == 7
    assert {path.name for path, _ in writes} >= {
        Artifact.LARGE_FAMILY_CTK,
        Artifact.LARGE_FAMILY_STABILITY,
        Artifact.LARGE_FAMILY_SUMMARY,
    }


def test_empty_evidence_stops_extension_workflows_before_analysis(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = EVIDENCE.model_copy(update={"summary": EMPTY})
    monkeypatch.setattr(workflow, "collect_evidence", lambda *_args, **_kwargs: empty)
    for name, function in (
        ("dose_experiments", workflow.run_dose_extension),
        ("controls_experiments", workflow.run_controls_extension),
        ("representation_experiments", workflow.run_representation_extension),
    ):
        monkeypatch.setattr(
            workflow, name, lambda *_args: (ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY,)
        )
        with pytest.raises(workflow.CtkError):
            function(Paths(tmp_path), CONFIG, MODE, False)
