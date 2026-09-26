from typing import Self

from ctk_android.enums import (
    Artifact,
    CliCommand,
    ConfigFile,
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
    ProtocolDocument,
    ReportFigure,
    ReportTable,
    Representation,
    ResultsDirectory,
    ResultsFile,
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
    RandomSeed,
    RunKey,
    Salt,
)


def _run_name(seed: RandomSeed, salt: Salt) -> EntryName:
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
    def roadmap_file(self) -> File:
        return self.root / WorkspaceDirectory.DOCS / SourceFile.ROADMAP

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

    @property
    def representation_dir(self) -> Directory:
        return self.stage_dir(Stage.REPRESENTATION)

    def representation_file(self, artifact: Artifact) -> File:
        return self.representation_dir / artifact

    def representation_partition_dir(self, key: PartitionKey) -> Directory:
        return self.representation_dir / Stage.PARTITIONS / _run_name(key.seed, key.salt)

    def representation_partition_file(self, key: PartitionKey, artifact: Artifact) -> File:
        return self.representation_partition_dir(key) / artifact

    def partition_dir_for(
        self, key: PartitionKey, representation: Representation | None
    ) -> Directory:
        if representation is None:
            return self.partition_dir(key)
        return self.representation_partition_dir(key)

    def plan_dir(self, mode: ExecutionMode) -> Directory:
        return self.outputs / WorkspaceDirectory.PLANS / mode

    def plan_file(self, mode: ExecutionMode, artifact: Artifact) -> File:
        return self.plan_dir(mode) / artifact

    def results_file(self, directory: ResultsDirectory, name: EntryName) -> File:
        return self.root / WorkspaceDirectory.RESULTS / directory / name

    def results_root_file(self, name: ResultsFile) -> File:
        return self.root / WorkspaceDirectory.RESULTS / name

    def protocol_file(self, document: ProtocolDocument) -> File:
        return self.root / document

    def log_file(self, command: CliCommand) -> File:
        return self.outputs / WorkspaceDirectory.LOGS / f"{command}{FileSuffix.JSONL}"

    def analysis_file(self, mode: ExecutionMode, artifact: Artifact) -> File:
        return self.outputs / WorkspaceDirectory.ANALYSIS / mode / artifact

    def statistics_file(self, mode: ExecutionMode, artifact: Artifact) -> File:
        return self.outputs / WorkspaceDirectory.STATISTICS / mode / artifact

    def report_table_file(self, mode: ExecutionMode, name: ReportTable) -> File:
        directory = self.outputs / WorkspaceDirectory.REPORT / mode / WorkspaceDirectory.TABLES
        return directory / f"{name}{FileSuffix.CSV}"

    def report_figure_file(
        self, mode: ExecutionMode, name: ReportFigure, suffix: FileSuffix
    ) -> File:
        directory = self.outputs / WorkspaceDirectory.REPORT / mode / WorkspaceDirectory.FIGURES
        return directory / f"{name}{suffix}"

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
