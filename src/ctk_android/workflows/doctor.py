import subprocess
import sys

import torch

from ctk_android.config import Config
from ctk_android.enums import Device, DoctorCheck
from ctk_android.paths import Paths
from ctk_android.types import DoctorResult

MIN_PYTHON = (3, 12)
FINGERPRINT_PREFIX = 12


def _git_revision(paths: Paths) -> DoctorResult:
    completed = subprocess.run(
        ["git", "-C", f"{paths.root}", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return DoctorResult(
        check=DoctorCheck.GIT_REVISION,
        passed=completed.returncode == 0,
        detail=completed.stdout.strip() or "not a git checkout",
    )


def _raw_lamda(paths: Paths, config: Config) -> DoctorResult:
    files = paths.lamda_release_files(config.data.lamda_release)
    missing = [path for path in files if not path.is_file()]
    return DoctorResult(
        check=DoctorCheck.RAW_LAMDA,
        passed=not missing,
        detail=f"{len(files)} files, {len(missing)} missing",
    )


def run_doctor(paths: Paths, config: Config) -> list[DoctorResult]:
    archive = paths.androzoo_archive()
    device = Device.CUDA if torch.cuda.is_available() else Device.CPU
    return [
        DoctorResult(
            check=DoctorCheck.PYTHON_VERSION,
            passed=sys.version_info[:2] >= MIN_PYTHON,
            detail=sys.version.split()[0],
        ),
        DoctorResult(
            check=DoctorCheck.CONFIG_VALID,
            passed=True,
            detail=f"configuration fingerprint {config.fingerprint()[:FINGERPRINT_PREFIX]}",
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
            detail=f"available {device}, configured {config.project.device}",
        ),
        _git_revision(paths),
    ]
