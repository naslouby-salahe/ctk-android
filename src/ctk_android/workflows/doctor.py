import subprocess
import sys

import torch

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.enums import (
    DetailMessage,
    Device,
    Display,
    DoctorCheck,
    GitArgument,
    LogEvent,
    LogField,
    PythonRequirement,
    SourceFile,
    WorkspaceDirectory,
)
from ctk_android.paths import Paths
from ctk_android.types import Clean, DoctorResult, GitArguments, GitOutput, Message, Moment


def git_revision(paths: Paths) -> DoctorResult:
    completed = subprocess.run(
        [
            GitArgument.GIT,
            GitArgument.DIRECTORY,
            f"{paths.root}",
            GitArgument.REV_PARSE,
            GitArgument.HEAD,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return DoctorResult(
        check=DoctorCheck.GIT_REVISION,
        passed=completed.returncode == 0,
        detail=completed.stdout.strip() or DetailMessage.NOT_A_CHECKOUT,
    )


def _git(paths: Paths, arguments: GitArguments) -> GitOutput:
    completed = subprocess.run(
        [GitArgument.GIT, GitArgument.DIRECTORY, f"{paths.root}", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip()


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


def _raw_lamda(paths: Paths, config: Config) -> DoctorResult:
    files = paths.lamda_release_files(config.data.lamda_release)
    missing = [path for path in files if not path.is_file()]
    return DoctorResult(
        check=DoctorCheck.RAW_LAMDA,
        passed=not missing,
        detail=DetailMessage.FILE_COUNT.format(count=len(files), missing=len(missing)),
    )


def run_doctor(paths: Paths, config: Config) -> list[DoctorResult]:
    results = _checks(paths, config)
    for result in results:
        report = logs.info if result.passed else logs.warning
        report(
            LogEvent.DOCTOR_CHECKED,
            {
                LogField.CHECK: result.check,
                LogField.PASSED: result.passed,
                LogField.DETAIL: result.detail,
            },
        )
    return results


def _checks(paths: Paths, config: Config) -> list[DoctorResult]:
    archive = paths.androzoo_archive()
    device = Device.CUDA if torch.cuda.is_available() else Device.CPU
    return [
        DoctorResult(
            check=DoctorCheck.PYTHON_VERSION,
            passed=sys.version_info[:2] >= (PythonRequirement.MAJOR, PythonRequirement.MINOR),
            detail=sys.version.split()[0],
        ),
        DoctorResult(
            check=DoctorCheck.CONFIG_VALID,
            passed=True,
            detail=DetailMessage.CONFIG_FINGERPRINT.format(
                prefix=config.fingerprint()[: Display.FINGERPRINT_PREFIX]
            ),
        ),
        _raw_lamda(paths, config),
        DoctorResult(
            check=DoctorCheck.RAW_ANDROZOO,
            passed=archive.is_file(),
            detail=f"{archive}",
        ),
        DoctorResult(
            check=DoctorCheck.COMPUTE_DEVICE,
            passed=device is config.project.device or device is Device.CPU,
            detail=DetailMessage.DEVICE.format(available=device, configured=config.project.device),
        ),
        git_revision(paths),
    ]
