from pathlib import Path

# Pyright cannot infer callback signatures for monkeypatch lambda stubs.
# pyright: reportUnknownLambdaType=false, reportUnknownArgumentType=false
import polars as pl
import pytest

import ctk_android.reporting.artifacts as artifacts
from ctk_android.config import load_config
from ctk_android.data.cache import write_record, write_table
from ctk_android.enums import (
    Artifact,
    Column,
    EvidenceClass,
    ExecutionMode,
    ExtensionStudy,
    PromotionBlock,
    PromotionState,
    ResultsDirectory,
    ResultsFile,
    RunStatus,
    Stage,
)
from ctk_android.paths import Paths
from ctk_android.types import CodeProvenance, DesignPromotion, PromotedOutput, ResultsManifest
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))


def _index(*statuses: RunStatus) -> pl.DataFrame:
    return pl.DataFrame({Column.STATUS: list(statuses)}, schema={Column.STATUS: pl.String})


def test_extension_blocks_collect_all_run_and_provenance_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    mode = ExecutionMode.EXTENSION_B
    write_table(
        _index(RunStatus.FAILED_VALIDATION, RunStatus.INCOMPLETE),
        paths.analysis_file(mode, Artifact.RUN_INDEX),
    )
    monkeypatch.setattr(artifacts, "_stale_runs", lambda *_args: True)

    blocks = artifacts._extension_blocks(paths, CONFIG, mode)  # pyright: ignore[reportPrivateUsage]

    assert set(blocks) == {
        PromotionBlock.VALIDATION_FAILED,
        PromotionBlock.RUNS_INCOMPLETE,
        PromotionBlock.PROVENANCE_STALE,
    }


def test_artifact_copy_and_csv_write_return_digest_entries(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    source = tmp_path / "source.parquet"
    pl.DataFrame({Column.VALUE: [1.0]}).write_parquet(source)
    copied = paths.results_file(ResultsDirectory.EVIDENCE, Artifact.PAIRED_EFFECTS)
    csv_target = paths.results_file(ResultsDirectory.TABLES, ResultsFile.CLAIMS)

    copy_entry = artifacts._copy(source, copied, EvidenceClass.CONFIRMATORY_SEEDS)  # pyright: ignore[reportPrivateUsage]
    csv_entry = artifacts._write_csv(  # pyright: ignore[reportPrivateUsage]
        pl.DataFrame({Column.CLAIM: ["claim"]}), csv_target, EvidenceClass.POST_CONFIRMATORY
    )

    assert copied.is_file()
    assert csv_target.is_file()
    assert copy_entry.digest
    assert copy_entry.evidence_class is EvidenceClass.CONFIRMATORY_SEEDS
    assert csv_entry.evidence_class is EvidenceClass.POST_CONFIRMATORY
    assert copy_entry.name != csv_entry.name


def test_hidden_family_promotion_blocks_when_manifest_is_absent_or_runs_are_incomplete(
    tmp_path: Path,
) -> None:
    paths = Paths(tmp_path)
    blocked = artifacts.promote_hidden_family(paths, ExecutionMode.CONFIRMATORY, _index())
    assert blocked.state is PromotionState.BLOCKED
    assert blocked.blocks == (PromotionBlock.NOT_CONFIRMATORY,)

    write_record(
        paths.results_root_file(ResultsFile.MANIFEST),
        ResultsManifest(mode=ExecutionMode.CONFIRMATORY, files=()),
    )
    incomplete = artifacts.promote_hidden_family(
        paths, ExecutionMode.CONFIRMATORY, _index(RunStatus.INCOMPLETE)
    )
    assert incomplete.state is PromotionState.BLOCKED
    assert incomplete.blocks == (PromotionBlock.RUNS_INCOMPLETE,)


def test_hidden_family_promotion_copies_each_table_and_merges_manifest(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    mode = ExecutionMode.CONFIRMATORY
    write_record(
        paths.results_root_file(ResultsFile.MANIFEST),
        ResultsManifest(mode=mode, files=()),
    )
    for artifact in artifacts.hidden_family_files():
        write_table(pl.DataFrame({Column.VALUE: [1.0]}), paths.analysis_file(mode, artifact))

    decision = artifacts.promote_hidden_family(paths, mode, _index(RunStatus.COMPLETED))

    manifest = artifacts.ResultsManifest.model_validate_json(
        paths.results_root_file(ResultsFile.MANIFEST).read_text(encoding="utf-8")
    )
    assert decision.state is PromotionState.PROMOTED
    assert len(manifest.files) == 2 * len(artifacts.hidden_family_files())
    assert all(entry.evidence_class is EvidenceClass.POST_CONFIRMATORY for entry in manifest.files)


def test_promotion_rejects_non_confirmatory_modes_before_reading_results(tmp_path: Path) -> None:
    decision = artifacts.promote(Paths(tmp_path), CONFIG, ExecutionMode.DEVELOPMENT)
    assert decision.state is PromotionState.BLOCKED
    assert decision.blocks == (PromotionBlock.NOT_CONFIRMATORY,)


def test_large_family_promotion_copies_typed_and_csv_artifacts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = Paths(tmp_path)
    mode = ExecutionMode.EXTENSION_B
    index = _index(RunStatus.COMPLETED)
    write_table(index, paths.analysis_file(mode, Artifact.RUN_INDEX))
    artifacts_to_copy = (
        Artifact.LARGE_FAMILY_CTK,
        Artifact.LARGE_FAMILY_SEED_CTK,
        Artifact.LARGE_FAMILY_SUMMARY,
        Artifact.LARGE_FAMILY_STABILITY,
        Artifact.LARGE_FAMILY_STABILITY_SEEDS,
        Artifact.LARGE_FAMILY_STABILITY_SUMMARY,
    )
    for artifact in artifacts_to_copy:
        write_table(pl.DataFrame({Column.VALUE: [1.0]}), paths.analysis_file(mode, artifact))
    write_table(
        pl.DataFrame({Column.FAMILY: ["family"]}),
        paths.stage_file(Stage.FAMILIES, Artifact.LARGE_SELECTION),
    )
    monkeypatch.setattr(artifacts, "_extension_blocks", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(artifacts, "record_study", lambda *_args: None)
    monkeypatch.setattr(
        artifacts,
        "_code",
        lambda *_args: CodeProvenance(
            execution_revision="rev1", analysis_revision="rev2", analysis_sources_clean=True
        ),
    )

    decision = artifacts.promote_large_family(paths, CONFIG, mode)

    manifest = ResultsManifest.model_validate_json(
        paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.MANIFEST).read_text(
            encoding="utf-8"
        )
    )
    assert decision.state is PromotionState.PROMOTED
    assert len(manifest.files) == 16
    assert all(
        entry.evidence_class is EvidenceClass.PROSPECTIVE_EXTENSION for entry in manifest.files
    )


@pytest.mark.parametrize("promoter", ["design", "diagnostics"])
def test_extension_design_promoters_record_requested_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, promoter: str
) -> None:
    paths = Paths(tmp_path)
    mode = ExecutionMode.EXTENSION_B
    index_artifact = Artifact.DOSE_RUN_INDEX
    output_artifact = Artifact.DOSE_EFFECTS
    write_table(_index(RunStatus.COMPLETED), paths.analysis_file(mode, index_artifact))
    write_table(pl.DataFrame({Column.VALUE: [1.0]}), paths.analysis_file(mode, output_artifact))
    monkeypatch.setattr(artifacts, "_extension_blocks", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(artifacts, "record_study", lambda *_args: None)
    monkeypatch.setattr(
        artifacts,
        "_code",
        lambda *_args: CodeProvenance(
            execution_revision="rev1", analysis_revision="rev2", analysis_sources_clean=False
        ),
    )
    request = DesignPromotion(
        study=ExtensionStudy.DOSE,
        experiments=(),
        index_artifact=index_artifact,
        code_file=ResultsFile.DOSE_CODE,
        artifacts=(output_artifact,),
        outputs=(
            PromotedOutput(
                artifact=output_artifact, evidence_class=EvidenceClass.POST_CONFIRMATORY
            ),
        ),
    )
    promote = (
        artifacts.promote_extension_design
        if promoter == "design"
        else artifacts.promote_diagnostics
    )

    decision = promote(paths, CONFIG, mode, request)

    manifest = ResultsManifest.model_validate_json(
        paths.results_file(ResultsDirectory.EXTENSION_B, ResultsFile.MANIFEST).read_text(
            encoding="utf-8"
        )
    )
    assert decision.state is PromotionState.PROMOTED
    assert len(manifest.files) == (4 if promoter == "design" else 2)
    expected_evidence = (
        EvidenceClass.PROSPECTIVE_EXTENSION
        if promoter == "design"
        else EvidenceClass.POST_CONFIRMATORY
    )
    assert {entry.evidence_class for entry in manifest.files} == {expected_evidence}
