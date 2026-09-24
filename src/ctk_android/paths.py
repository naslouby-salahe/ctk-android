from typing import Self

from ctk_android.enums import (
    Artifact,
    ConfigFile,
    CoreModule,
    DatasetName,
    EligibilityProfile,
    ErrorMessage,
    ExecutionMode,
    FamilySetName,
    FileSuffix,
    FormatSpec,
    Grouping,
    LamdaRelease,
    NameFragment,
    SourceFile,
    Stage,
    WorkspaceDirectory,
)
from ctk_android.types import (
    ArmKey,
    Directory,
    EntryName,
    File,
    LamdaReleaseFiles,
    PartitionKey,
    RunKey,
    Salt,
    Seed,
)


def _run_name(seed: Seed, salt: Salt) -> EntryName:
    name = f"{NameFragment.SEED}{format(seed, FormatSpec.THREE_DIGITS)}"
    return f"{name}{NameFragment.SALT}{salt}" if salt else name


class Paths:
    def __init__(self, root: Directory) -> None:
        self.root = root

    @classmethod
    def discover(cls, start: Directory) -> Self:
        for candidate in (start, *start.parents):
            if (candidate / SourceFile.PROJECT_MARKER).is_file():
                return cls(candidate)
        raise FileNotFoundError(
            ErrorMessage.NO_PROJECT_ROOT.format(marker=SourceFile.PROJECT_MARKER, start=start)
        )

    @property
    def source_root(self) -> Directory:
        return self.root / WorkspaceDirectory.SOURCE / WorkspaceDirectory.PACKAGE

    @property
    def data_package(self) -> Directory:
        return self.source_root / WorkspaceDirectory.DATA

    @property
    def core_modules(self) -> list[File]:
        return [self.source_root / module for module in CoreModule]

    def config_file(self, name: ConfigFile) -> File:
        return self.root / WorkspaceDirectory.CONFIGS / name

    def raw_data(self, dataset: DatasetName) -> Directory:
        return self.root / WorkspaceDirectory.DATA / dataset / WorkspaceDirectory.RAW

    def lamda_release_files(self, release: LamdaRelease) -> LamdaReleaseFiles:
        release_dir = self.raw_data(DatasetName.LAMDA) / release
        return [
            *sorted(release_dir.glob(SourceFile.LAMDA_PARQUET_GLOB)),
            release_dir / SourceFile.LAMDA_FEATURE_MAPPING,
        ]

    def androzoo_archive(self) -> File:
        return self.raw_data(DatasetName.ANDROZOO) / SourceFile.ANDROZOO_ARCHIVE

    @property
    def outputs(self) -> Directory:
        return self.root / WorkspaceDirectory.OUTPUTS

    @property
    def preprocessing(self) -> Directory:
        return self.outputs / WorkspaceDirectory.PREPROCESSING

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
        return self.preprocessing / Stage.SOURCE_AUDIT / WorkspaceDirectory.LINKAGE

    def linkage_file(self, artifact: Artifact) -> File:
        return self.linkage_dir / artifact

    def stage_dir(self, stage: Stage) -> Directory:
        return self.preprocessing / stage

    def stage_file(self, stage: Stage, artifact: Artifact) -> File:
        return self.stage_dir(stage) / artifact

    def cache_file(self, artifact: Artifact) -> File:
        return self.preprocessing / WorkspaceDirectory.CACHE / artifact

    def family_set_file(self, family_set: FamilySetName) -> File:
        return self.stage_dir(Stage.FAMILIES) / f"{family_set}{FileSuffix.FAMILY_SET}"

    def partition_dir(self, key: PartitionKey) -> Directory:
        name = _run_name(key.seed, key.salt)
        if key.grouping is not Grouping.COMPONENT:
            name += f"{NameFragment.SEPARATOR}{key.grouping}"
        if key.profile is not EligibilityProfile.PRIMARY:
            name += f"{NameFragment.SEPARATOR}{key.profile}"
        return self.stage_dir(Stage.PARTITIONS) / name

    def partition_file(self, key: PartitionKey, artifact: Artifact) -> File:
        return self.partition_dir(key) / artifact

    def plan_dir(self, mode: ExecutionMode) -> Directory:
        return self.outputs / WorkspaceDirectory.PLANS / mode

    def plan_file(self, mode: ExecutionMode, artifact: Artifact) -> File:
        return self.plan_dir(mode) / artifact

    def run_dir(self, key: RunKey) -> Directory:
        return self.outputs / Stage.RUNS / key.mode / key.experiment / _run_name(key.seed, key.salt)

    def run_file(self, key: RunKey, artifact: Artifact) -> File:
        return self.run_dir(key) / artifact

    def run_metric_file(self, key: RunKey, artifact: Artifact) -> File:
        return self.run_dir(key) / WorkspaceDirectory.METRICS / artifact

    def run_scores_file(self, key: RunKey, arm: ArmKey) -> File:
        return self.run_dir(key) / WorkspaceDirectory.SCORES / f"{arm.label()}{FileSuffix.PARQUET}"

    def run_models_file(self, key: RunKey, arm: ArmKey) -> File:
        return self.run_dir(key) / WorkspaceDirectory.MODELS / f"{arm.label()}{FileSuffix.TORCH}"
