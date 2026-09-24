from pathlib import Path

from ctk_android.enums import (
    DatasetName,
    EligibilityProfile,
    ExecutionMode,
    ExperimentName,
    FamilySetName,
    Grouping,
)
from ctk_android.types import Directory, File, PartitionKey, RunKey

PROJECT_MARKER = "pyproject.toml"


class Paths:
    def __init__(self, root: Directory) -> None:
        self.root = root

    @staticmethod
    def discover(start: Directory) -> "Paths":
        for candidate in (start, *start.parents):
            if (candidate / PROJECT_MARKER).is_file():
                return Paths(candidate)
        raise FileNotFoundError(f"no {PROJECT_MARKER} above {start}")

    @property
    def config_dir(self) -> Directory:
        return self.root / "configs"

    def raw_data(self, dataset: DatasetName) -> Directory:
        return self.root / "data" / dataset / "raw"

    @property
    def outputs(self) -> Directory:
        return self.root / "outputs"

    @property
    def results(self) -> Directory:
        return self.root / "results"

    @property
    def preprocessing(self) -> Directory:
        return self.outputs / "preprocessing"

    def source_audit(self, dataset: DatasetName) -> Directory:
        return self.preprocessing / "source-audit" / dataset

    @property
    def linkage(self) -> Directory:
        return self.preprocessing / "source-audit" / "linkage"

    @property
    def joined(self) -> Directory:
        return self.preprocessing / "joined"

    @property
    def identity(self) -> Directory:
        return self.preprocessing / "identity"

    @property
    def clients(self) -> Directory:
        return self.preprocessing / "clients"

    @property
    def families(self) -> Directory:
        return self.preprocessing / "families"

    def family_set_file(self, family_set: FamilySetName) -> File:
        return self.families / f"{family_set}-family-set.json"

    @property
    def partitions(self) -> Directory:
        return self.preprocessing / "partitions"

    def partition(self, key: PartitionKey) -> Directory:
        name = f"seed-{key.seed:03d}"
        if key.salt:
            name += f"-salt-{key.salt}"
        if key.grouping is not Grouping.COMPONENT:
            name += f"-{key.grouping}"
        if key.profile is not EligibilityProfile.PRIMARY:
            name += f"-{key.profile}"
        return self.partitions / name

    @property
    def cache(self) -> Directory:
        return self.preprocessing / "cache"

    def plan(self, mode: ExecutionMode) -> Directory:
        return self.outputs / "plans" / mode

    def run(self, key: RunKey) -> Directory:
        name = f"seed-{key.seed:03d}" + (f"-salt-{key.salt}" if key.salt else "")
        return self.outputs / "runs" / key.mode / key.experiment / name

    def experiment_runs(self, mode: ExecutionMode, experiment: ExperimentName) -> Directory:
        return self.outputs / "runs" / mode / experiment

    def analysis(self, mode: ExecutionMode) -> Directory:
        return self.outputs / "analysis" / mode

    def statistics(self, mode: ExecutionMode) -> Directory:
        return self.outputs / "statistics" / mode

    @property
    def report(self) -> Directory:
        return self.outputs / "report"

    @property
    def audit(self) -> Directory:
        return self.outputs / "audit"

    @property
    def logs(self) -> Directory:
        return self.outputs / "logs"


