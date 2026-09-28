from pathlib import Path

from ctk_android.enums import WorkspaceDirectory
from tests.isolation import snapshot_evidence


def test_the_isolation_guard_sees_created_changed_and_removed_evidence(tmp_path: Path) -> None:
    empty = snapshot_evidence(tmp_path)
    assert empty == {
        f"{WorkspaceDirectory.OUTPUTS}": (0,),
        f"{WorkspaceDirectory.RESULTS}": (0,),
    }
    (tmp_path / WorkspaceDirectory.RESULTS).mkdir()
    assert snapshot_evidence(tmp_path) != empty
    evidence = tmp_path / WorkspaceDirectory.RESULTS / "table.csv"
    evidence.write_text("a\n", encoding="utf-8")
    created = snapshot_evidence(tmp_path)
    evidence.write_text("bb\n", encoding="utf-8")
    assert snapshot_evidence(tmp_path) != created
    evidence.unlink()
    assert snapshot_evidence(tmp_path) != created
