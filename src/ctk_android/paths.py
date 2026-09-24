from ctk_android.enums import (
    Artifact,
    ConfigFile,
    DatasetName,
    EligibilityProfile,
    ExecutionMode,
    FamilySetName,
    Grouping,
    Stage,
)
from ctk_android.types import ArmKey, Directory, File, PartitionKey, ReleaseName, RunKey

PROJECT_MARKER = "pyproject.toml"
LAMDA_ARCHIVE_GLOB = "*/*.parquet"
LAMDA_FEATURE_MAPPING = "feature_mapping.csv"
ANDROZOO_ARCHIVE = "latest.csv.gz"
CORE_MODULE_NAMES = ("types.py", "enums.py", "config.py", "paths.py")


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
    def source_root(self) -> Directory:
        return self.root / "src" / "ctk_android"

    @property
    def data_package(self) -> Directory:
        return self.source_root / "data"

    @property
    def core_modules(self) -> list[File]:
        return [self.source_root / name for name in CORE_MODULE_NAMES]

    def config_file(self, name: ConfigFile) -> File:
        return self.root / "configs" / name

    def raw_data(self, dataset: DatasetName) -> Directory:
        return self.root / "data" / dataset / "raw"

    def lamda_release_files(self, release: ReleaseName) -> list[File]:
        release_dir = self.raw_data(DatasetName.LAMDA) / release
        return [*sorted(release_dir.glob(LAMDA_ARCHIVE_GLOB)), release_dir / LAMDA_FEATURE_MAPPING]

    def androzoo_archive(self) -> File:
        return self.raw_data(DatasetName.ANDROZOO) / ANDROZOO_ARCHIVE

    @property
    def outputs(self) -> Directory:
        return self.root / "outputs"

    @property
    def preprocessing(self) -> Directory:
        return self.outputs / "preprocessing"

    def provenance_file(self, directory: Directory) -> File:
        return directory / Artifact.PROVENANCE

    def audit_file(self, directory: Directory) -> File:
        return directory / Artifact.AUDIT

    def source_dir(self, dataset: DatasetName) -> Directory:
        return self.preprocessing / Stage.SOURCE_AUDIT / dataset

    def source_file(self, dataset: DatasetName, artifact: Artifact) -> File:
        return self.source_dir(dataset) / artifact

    @property
    def linkage_dir(self) -> Directory:
        return self.preprocessing / Stage.SOURCE_AUDIT / "linkage"

    def linkage_file(self, artifact: Artifact) -> File:
        return self.linkage_dir / artifact

    def stage_dir(self, stage: Stage) -> Directory:
        return self.preprocessing / stage

    def stage_file(self, stage: Stage, artifact: Artifact) -> File:
        return self.stage_dir(stage) / artifact

    def cache_file(self, artifact: Artifact) -> File:
        return self.preprocessing / "cache" / artifact

    def family_set_file(self, family_set: FamilySetName) -> File:
        return self.stage_dir(Stage.FAMILIES) / f"{family_set}-family-set.json"

    def partition_dir(self, key: PartitionKey) -> Directory:
        name = f"seed-{key.seed:03d}"
        if key.salt:
            name += f"-salt-{key.salt}"
        if key.grouping is not Grouping.COMPONENT:
            name += f"-{key.grouping}"
        if key.profile is not EligibilityProfile.PRIMARY:
            name += f"-{key.profile}"
        return self.stage_dir(Stage.PARTITIONS) / name

    def partition_file(self, key: PartitionKey, artifact: Artifact) -> File:
        return self.partition_dir(key) / artifact

    def plan_dir(self, mode: ExecutionMode) -> Directory:
        return self.outputs / "plans" / mode

    def plan_file(self, mode: ExecutionMode, artifact: Artifact) -> File:
        return self.plan_dir(mode) / artifact

    def run_dir(self, key: RunKey) -> Directory:
        name = f"seed-{key.seed:03d}" + (f"-salt-{key.salt}" if key.salt else "")
        return self.outputs / Stage.RUNS / key.mode / key.experiment / name

    def run_file(self, key: RunKey, artifact: Artifact) -> File:
        return self.run_dir(key) / artifact

    def run_metric_file(self, key: RunKey, artifact: Artifact) -> File:
        return self.run_dir(key) / "metrics" / artifact

    def run_scores_file(self, key: RunKey, arm: ArmKey) -> File:
        return self.run_dir(key) / "scores" / f"{arm.label()}.parquet"

    def run_models_file(self, key: RunKey, arm: ArmKey) -> File:
        return self.run_dir(key) / "models" / f"{arm.label()}.pt"
