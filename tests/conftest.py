from collections.abc import Iterator
from pathlib import Path

import pytest

from ctk_android.enums import SourceFile, Stage, WorkspaceDirectory
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT
from tests.isolation import snapshot_evidence

GIT_DIRECTORY = ".git"
LINKED_ROOT_ENTRIES = (
    SourceFile.PROJECT_MARKER,
    WorkspaceDirectory.CONFIGS,
    WorkspaceDirectory.DATA,
)
PREPROCESSING_ONLY = (WorkspaceDirectory.PREPROCESSING,)
SAVED_EVIDENCE = (
    WorkspaceDirectory.PREPROCESSING,
    WorkspaceDirectory.PLANS,
    Stage.RUNS,
)


def _link(source: Path, target: Path) -> None:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source, target_is_directory=source.is_dir())


def build_workspace(root: Path, shared_outputs: tuple[str, ...]) -> Paths:
    for entry in (*LINKED_ROOT_ENTRIES, GIT_DIRECTORY):
        _link(REPO_ROOT / entry, root / entry)
    for entry in shared_outputs:
        _link(
            REPO_ROOT / WorkspaceDirectory.OUTPUTS / entry,
            root / WorkspaceDirectory.OUTPUTS / entry,
        )
    return Paths(root)


@pytest.fixture(scope="module")
def preprocessed_workspace(tmp_path_factory: pytest.TempPathFactory) -> Paths:
    return build_workspace(tmp_path_factory.mktemp("workspace"), PREPROCESSING_ONLY)


@pytest.fixture(scope="module")
def evidence_workspace(tmp_path_factory: pytest.TempPathFactory) -> Paths:
    return build_workspace(tmp_path_factory.mktemp("evidence"), SAVED_EVIDENCE)


@pytest.fixture
def in_preprocessed_workspace(
    preprocessed_workspace: Paths, monkeypatch: pytest.MonkeyPatch
) -> Paths:
    monkeypatch.chdir(preprocessed_workspace.root)
    return preprocessed_workspace


@pytest.fixture(scope="session", autouse=True)
def real_evidence_stays_untouched() -> Iterator[None]:
    before = snapshot_evidence(REPO_ROOT)
    yield
    after = snapshot_evidence(REPO_ROOT)
    created = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(name for name in set(before) & set(after) if before[name] != after[name])
    assert not (created or removed or changed), (
        f"tests modified real evidence: created={created[:10]} removed={removed[:10]} "
        f"changed={changed[:10]}"
    )
