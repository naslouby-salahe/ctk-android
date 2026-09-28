import subprocess
from datetime import UTC, datetime

from ctk_android.enums import DetailMessage, GitArgument, SourceFile, WorkspaceDirectory
from ctk_android.paths import Paths
from ctk_android.types import (
    Clean,
    GitArguments,
    GitOutput,
    Message,
    Moment,
    TimestampedRevision,
)


def _git(paths: Paths, arguments: GitArguments) -> GitOutput:
    completed = subprocess.run(
        [GitArgument.GIT, GitArgument.DIRECTORY, f"{paths.root}", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()


def git_revision(paths: Paths) -> Message:
    return _git(paths, [GitArgument.REV_PARSE, GitArgument.HEAD]) or DetailMessage.NOT_A_CHECKOUT


def revision_at_or_before(paths: Paths, moment: Moment) -> Message:
    objects = _git(
        paths,
        [GitArgument.CAT_FILE, GitArgument.BATCH_ALL_OBJECTS, GitArgument.BATCH_CHECK],
    )
    commits = [
        line.split()[1]
        for line in objects.splitlines()
        if line.startswith(GitArgument.COMMIT_OBJECT_PREFIX)
    ]
    if not commits:
        return DetailMessage.NOT_A_CHECKOUT
    history = _git(paths, [GitArgument.LOG, GitArgument.COMMIT_FORMAT, *commits])
    candidates: list[TimestampedRevision] = []
    for line in history.splitlines():
        revision, committed_at = line.split(GitArgument.FIELD_SEPARATOR, maxsplit=1)
        committed = datetime.fromisoformat(committed_at).astimezone(UTC)
        if committed <= moment:
            candidates.append((committed, revision))
    if not candidates:
        return DetailMessage.NO_REVISION_AT_TIME
    return max(candidates, key=lambda candidate: candidate[0])[1]


def sources_are_clean(paths: Paths) -> Clean:
    tracked = [WorkspaceDirectory.SOURCE, WorkspaceDirectory.CONFIGS, SourceFile.PROJECT_MARKER]
    return not _git(
        paths, [GitArgument.STATUS, GitArgument.PORCELAIN, GitArgument.PATHSPEC, *tracked]
    )
