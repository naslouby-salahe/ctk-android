from pathlib import Path

from ctk_android.enums import WorkspaceDirectory

EVIDENCE_DIRECTORIES = (WorkspaceDirectory.OUTPUTS, WorkspaceDirectory.RESULTS)


def snapshot_evidence(root: Path) -> dict[str, tuple[int, ...]]:
    snapshot: dict[str, tuple[int, ...]] = {}
    for name in EVIDENCE_DIRECTORIES:
        directory = root / name
        snapshot[f"{name}"] = (int(directory.exists()),)
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            stat = path.lstat()
            snapshot[f"{path.relative_to(root)}"] = (
                int(path.is_dir()),
                stat.st_size,
                stat.st_mtime_ns,
            )
    return snapshot
