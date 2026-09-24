import subprocess
import sys
from pathlib import Path

from tests.architecture.source_index import REPO_ROOT

BIN = Path(sys.executable).parent


def _run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def test_ruff_passes() -> None:
    result = _run(str(BIN / "ruff"), "check", "src", "tests")
    assert result.returncode == 0, result.stdout


def test_ruff_format_is_clean() -> None:
    result = _run(str(BIN / "ruff"), "format", "--check", "src", "tests")
    assert result.returncode == 0, result.stdout


def test_pyright_strict_passes() -> None:
    result = _run(str(BIN / "pyright"))
    assert result.returncode == 0, result.stdout[-3000:]


def test_semgrep_rules_pass() -> None:
    result = _run(
        str(BIN / "semgrep"), "--config", "quality/semgrep.yml", "--error", "--quiet", "src"
    )
    assert result.returncode == 0, result.stdout[-3000:]
