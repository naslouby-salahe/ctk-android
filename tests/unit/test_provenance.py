from datetime import UTC, datetime

import pytest

from ctk_android import provenance
from ctk_android.enums import GitArgument
from ctk_android.paths import Paths
from ctk_android.provenance import revision_at_or_before, sources_are_clean
from ctk_android.workflows.maintenance import git_revision
from tests.architecture.source_index import REPO_ROOT

PATHS = Paths(REPO_ROOT)
DISTANT_FUTURE = datetime(2050, 1, 1, tzinfo=UTC)


def test_the_execution_revision_is_the_latest_commit_at_or_before_the_moment() -> None:
    assert revision_at_or_before(PATHS, DISTANT_FUTURE) == git_revision(PATHS).detail


def test_a_moment_before_the_history_names_no_revision() -> None:
    assert (
        revision_at_or_before(PATHS, datetime(1971, 1, 1, tzinfo=UTC)) != git_revision(PATHS).detail
    )


def test_execution_revision_searches_unreferenced_repository_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = iter(
        (
            "commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
            "commit bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\t2026-09-24T19:42:42+00:00\n"
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\t2026-09-24T21:12:18+00:00\n",
        )
    )

    def fake_git(_paths: Paths, arguments: list[str]) -> str:
        if arguments[0] == GitArgument.CAT_FILE:
            return next(outputs)
        assert arguments[0] == GitArgument.LOG
        return next(outputs)

    monkeypatch.setattr(provenance, "_git", fake_git)

    result = provenance.revision_at_or_before(PATHS, datetime(2026, 9, 24, 21, 5, tzinfo=UTC))

    assert result == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_source_cleanliness_is_reported_as_a_flag() -> None:
    assert isinstance(sources_are_clean(PATHS), bool)
