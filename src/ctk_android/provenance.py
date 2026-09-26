import subprocess

from ctk_android.enums import DetailMessage, GitArgument, SourceFile, WorkspaceDirectory
from ctk_android.paths import Paths
from ctk_android.types import Clean, GitArguments, GitOutput, Message, Moment


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
    return (
        _git(
            paths,
            [
                GitArgument.REV_LIST,
                GitArgument.LATEST,
                GitArgument.BEFORE.format(moment=moment.isoformat()),
                GitArgument.HEAD,
            ],
        )
        or DetailMessage.NOT_A_CHECKOUT
    )


def sources_are_clean(paths: Paths) -> Clean:
    tracked = [WorkspaceDirectory.SOURCE, WorkspaceDirectory.CONFIGS, SourceFile.PROJECT_MARKER]
    return not _git(
        paths, [GitArgument.STATUS, GitArgument.PORCELAIN, GitArgument.PATHSPEC, *tracked]
    )
