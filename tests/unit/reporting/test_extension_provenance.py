from pathlib import Path

from ctk_android.config import load_config
from ctk_android.data.cache import read_record, write_record
from ctk_android.enums import (
    Artifact,
    DatasetName,
    EvidenceClass,
    ExecutionMode,
    ExtensionStudy,
    ResultsFile,
)
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import record_study
from ctk_android.types import (
    CodeProvenance,
    ExtensionProvenance,
    ManifestEntry,
    SourceFingerprint,
    StudyRequest,
)
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
DIGEST = "a" * 64
CODE = CodeProvenance(execution_revision="x", analysis_revision="y", analysis_sources_clean=True)


def _workspace(root: Path) -> Paths:
    paths = Paths(root)
    for dataset in (DatasetName.LAMDA, DatasetName.ANDROZOO):
        write_record(
            paths.source_file(dataset, Artifact.FINGERPRINT),
            SourceFingerprint(dataset=dataset, fingerprint=DIGEST, file_count=1, total_bytes=1),
        )
    write_record(
        paths.representation_file(Artifact.FINGERPRINT),
        SourceFingerprint(
            dataset=DatasetName.MCNDROID, fingerprint="b" * 64, file_count=1, total_bytes=1
        ),
    )
    return paths


def _request(study: ExtensionStudy, name: str) -> StudyRequest:
    return StudyRequest(
        study=study,
        mode=MODE,
        experiments=CONFIG.experiments.extension_b_experiments,
        evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION,
        code=CODE,
        artifacts=(
            ManifestEntry(
                name=name, digest=DIGEST, evidence_class=EvidenceClass.PROSPECTIVE_EXTENSION
            ),
        ),
    )


def test_each_study_keeps_one_entry_replaced_on_repromotion(tmp_path: Path) -> None:
    paths = _workspace(tmp_path)
    record_study(paths, CONFIG, _request(ExtensionStudy.REPRESENTATION, "first"))
    record_study(paths, CONFIG, _request(ExtensionStudy.DOSE, "dose"))
    record_study(paths, CONFIG, _request(ExtensionStudy.REPRESENTATION, "second"))
    record = read_record(
        paths.results_root_file(ResultsFile.EXTENSION_PROVENANCE), ExtensionProvenance
    )
    assert [study.name for study in record.studies] == [
        ExtensionStudy.DOSE,
        ExtensionStudy.REPRESENTATION,
    ]
    dose, representation = record.studies
    assert representation.artifacts[0].name == "second"
    assert representation.data.mcndroid_inventory == "b" * 64
    assert dose.data.mcndroid_inventory is None
    assert dose.seeds == tuple(
        sorted(
            {
                seed
                for experiment in CONFIG.experiments.extension_b_experiments
                for seed in CONFIG.seeds_for(experiment, MODE)
            }
        )
    )


def test_diagnostic_study_is_recorded(tmp_path: Path) -> None:
    paths = _workspace(tmp_path)
    record_study(paths, CONFIG, _request(ExtensionStudy.DIAGNOSTICS, "diagnostic"))
    record = read_record(
        paths.results_root_file(ResultsFile.EXTENSION_PROVENANCE), ExtensionProvenance
    )
    assert len(record.studies[0].run_fingerprints) == len(
        CONFIG.experiments.extension_b_experiments
    )
