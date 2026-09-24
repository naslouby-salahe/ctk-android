import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.architecture.source_index import REPO_ROOT

RULES = REPO_ROOT / "quality" / "semgrep.yml"
BIN = Path(sys.executable).parent
VIOLATIONS = {
    "no-primitive-function-boundary": "def f(value: int) -> str:\n    return 'x'\n",
    "no-raw-dict-domain-io": "def f(value: dict[str, object]) -> None:\n    return None\n",
    "no-broad-cast": "value = cast(int, 1)\n",
    "no-type-suppression": "value = 1  # type: ignore\n",
    "no-generic-constrained-alias-outside-types": "size: NonNegativeInt = 1\n",
    "no-yaml-parsing-outside-config": "document = yaml.safe_load(text)\n",
    "no-enum-value-escape": "name = member.value\n",
    "no-type-hiding-scalar-call": "value = float(other)\n",
}


@pytest.mark.parametrize(("rule", "snippet"), sorted(VIOLATIONS.items()))
def test_each_semgrep_rule_flags_its_violation(rule: str, snippet: str, tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text(snippet, encoding="utf-8")
    completed = subprocess.run(
        [str(BIN / "semgrep"), "--config", str(RULES), "--json", "--quiet", str(sample)],
        capture_output=True,
        text=True,
        check=False,
    )
    flagged = {
        result["check_id"].split(".")[-1] for result in json.loads(completed.stdout)["results"]
    }
    assert rule in flagged, flagged


def test_every_semgrep_rule_has_a_regression_case() -> None:
    declared = {
        line.split(":", maxsplit=1)[1].strip()
        for line in RULES.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- id:")
    }
    assert declared == set(VIOLATIONS)
