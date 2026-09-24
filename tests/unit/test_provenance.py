from datetime import UTC, datetime

from ctk_android.enums import ResultsDirectory, ResultsFile
from ctk_android.paths import Paths
from ctk_android.types import CodeProvenance, ProtocolProvenance
from ctk_android.workflows.doctor import git_revision, revision_at_or_before, sources_are_clean
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)
DISTANT_FUTURE = datetime(2050, 1, 1, tzinfo=UTC)


def test_the_execution_revision_is_the_latest_commit_at_or_before_the_moment() -> None:
    assert revision_at_or_before(PATHS, DISTANT_FUTURE) == git_revision(PATHS).detail


def test_a_moment_before_the_history_names_no_revision() -> None:
    assert (
        revision_at_or_before(PATHS, datetime(1971, 1, 1, tzinfo=UTC)) != git_revision(PATHS).detail
    )


def test_source_cleanliness_is_reported_as_a_flag() -> None:
    assert isinstance(sources_are_clean(PATHS), bool)


def test_promoted_provenance_separates_execution_from_analysis_revision() -> None:
    record = PATHS.results_file(ResultsDirectory.PROVENANCE, ResultsFile.CODE)
    provenance = CodeProvenance.model_validate_json(record.read_text(encoding="utf-8"))
    assert provenance.execution_revision
    assert provenance.analysis_revision
    protocol = PATHS.results_file(ResultsDirectory.PROVENANCE, ResultsFile.PROTOCOL)
    assert ProtocolProvenance.model_validate_json(protocol.read_text(encoding="utf-8")).config
