from pathlib import Path
from typing import Annotated, Any, Protocol

import numpy as np
import polars as pl
import torch
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter
from sklearn.ensemble import HistGradientBoostingClassifier

from ctk_android.enums import (
    ClientId,
    Column,
    DatasetName,
    Device,
    DoctorCheck,
    EligibilityProfile,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    FailureReason,
    Grouping,
    LamdaRelease,
    Learner,
    LibraryOption,
    ModelFamily,
    NameFragment,
    NoveltyDescriptor,
    OperatingPointStatus,
    Pattern,
    RunStatus,
    Stage,
    ValidationCheck,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
SignedInt = int
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
OpenUnitInterval = Annotated[float, Field(gt=0.0, lt=1.0, allow_inf_nan=False)]

Seed = NonNegativeInt
Salt = NonNegativeInt
RowCount = NonNegativeInt
RowIndex = NonNegativeInt
ComponentId = NonNegativeInt
FeatureCount = PositiveInt
FeatureIndex = NonNegativeInt
Epochs = PositiveInt
Rounds = PositiveInt
BatchSize = PositiveInt
UnitCount = PositiveInt
Dose = SignedInt
ResampleCount = PositiveInt
TreeIterations = PositiveInt
TreeDepth = PositiveInt
VtCount = NonNegativeInt
Rank = NonNegativeInt
ExceedanceCount = PositiveInt

seed_adapter: TypeAdapter[Seed] = TypeAdapter(Seed)

Fraction = UnitInterval
Rate = UnitInterval
Alpha = OpenUnitInterval
Confidence = OpenUnitInterval
LearningRate = PositiveFloat
WeightDecay = NonNegativeFloat
DropoutRate = UnitInterval
ProximalStrength = NonNegativeFloat
BlendWeight = UnitInterval
Score = FiniteFloat
Threshold = FiniteFloat
Effect = FiniteFloat
Correlation = FiniteFloat
PValue = UnitInterval
Seconds = NonNegativeFloat

Sha256 = Annotated[str, StringConstraints(pattern=Pattern.SHA256)]
PackageName = Annotated[str, StringConstraints(min_length=1)]
FamilyName = Annotated[str, StringConstraints(strip_whitespace=True)]
YearMonth = Annotated[str, StringConstraints(pattern=Pattern.YEAR_MONTH)]
Fingerprint = Annotated[str, StringConstraints(pattern=Pattern.SHA256)]
Message = Annotated[str, StringConstraints(min_length=1)]
FeatureColumn = Annotated[str, StringConstraints(pattern=Pattern.FEATURE_COLUMN)]
Label = Annotated[int, Field(ge=0, le=1)]

FloatArray = NDArray[np.float64]
Float32Array = NDArray[np.float32]
IntArray = NDArray[np.int64]
BoolArray = NDArray[np.bool_]
ByteMatrix = NDArray[np.uint8]

Directory = Path
LamdaReleaseFiles = list[Path]
EntryName = Annotated[str, StringConstraints(min_length=1)]
File = Path
StateDict = dict[str, torch.Tensor]


class FrozenRecord(BaseModel):
    model_config = ConfigDict(
        frozen=True, extra=LibraryOption.FORBID_EXTRA, arbitrary_types_allowed=True
    )


LabelPrefix = Annotated[str, StringConstraints(min_length=1)]
SupportCount = NonNegativeInt
StatKey = Annotated[str, StringConstraints(min_length=1)]
FileName = Annotated[str, StringConstraints(min_length=1)]

YamlDocument = dict[str, Any]


class PartitionKey(FrozenRecord):
    seed: Seed
    salt: Salt
    grouping: Grouping
    profile: EligibilityProfile


class RunKey(FrozenRecord):
    mode: ExecutionMode
    experiment: ExperimentName
    seed: Seed
    salt: Salt


class SourceFingerprint(FrozenRecord):
    dataset: DatasetName
    fingerprint: Fingerprint
    file_count: RowCount
    total_bytes: RowCount


class ValidationRecord(FrozenRecord):
    check: ValidationCheck
    passed: bool
    detail: Message


class Provenance(FrozenRecord):
    stage: Stage
    inputs: Fingerprint
    code: Fingerprint


class CtkError(Exception):
    def __init__(self, reason: FailureReason, message: Message) -> None:
        super().__init__(message)
        self.reason = reason


class LamdaTable(FrozenRecord):
    metadata: pl.DataFrame
    features: ByteMatrix
    non_binary_cells: RowCount
    negative_cells: RowCount


class JoinResult(FrozenRecord):
    joined: pl.DataFrame
    unmatched: pl.DataFrame
    validations: tuple[ValidationRecord, ...]


class TargetPair(FrozenRecord):
    client: ClientId
    family: FamilyName


class PartitionResult(FrozenRecord):
    roles: pl.Series
    attempt: NonNegativeInt
    controlled: pl.DataFrame
    natural: pl.DataFrame
    validations: tuple[ValidationRecord, ...]


class StageReport(FrozenRecord):
    stage: Stage
    directory: Directory
    reused: bool
    fingerprint: Fingerprint


DoseRequest = NonNegativeInt | None
TrainingRows = dict[ClientId, IntArray]


class ArmKey(FrozenRecord):
    learner: Learner
    condition: ExposureCondition
    dose: DoseRequest

    def label(self) -> str:
        dose = NameFragment.ALL_DOSE if self.dose is None else f"{self.dose}"
        parts = (self.learner, self.condition, f"{NameFragment.DOSE}{dose}")
        return NameFragment.ARM_SEPARATOR.join(parts)


class StudyData(FrozenRecord):
    table: pl.DataFrame
    features: ByteMatrix


class ExposureSpec(FrozenRecord):
    excluded: dict[ClientId, tuple[FamilyName, ...]]
    dose_caps: dict[FamilyName, SupportCount]
    dose_targets: dict[FamilyName, ClientId]


class Scorer(FrozenRecord):
    family: ModelFamily
    network: torch.nn.Module | None
    trees: HistGradientBoostingClassifier | None
    device: Device


ArmScores = dict[ClientId, FloatArray]


class OperatingPoint(FrozenRecord):
    threshold: Threshold
    calibration_benign: RowCount
    status: OperatingPointStatus


class PlannedRun(FrozenRecord):
    key: RunKey
    partition: PartitionKey
    targets: tuple[TargetPair, ...]
    status: RunStatus
    reason: FailureReason | None


class RunReport(FrozenRecord):
    key: RunKey
    status: RunStatus
    reused: bool
    directory: Directory


class Stepper(Protocol):
    def zero_grad(self) -> None: ...

    def step(self) -> None: ...


class DoctorResult(FrozenRecord):
    check: DoctorCheck
    passed: bool
    detail: Message


class ArmRow(FrozenRecord):
    learner: Learner
    condition: ExposureCondition
    dose: DoseRequest


class OperatingRow(ArmRow):
    client: ClientId
    alpha: Alpha
    threshold: Threshold
    calibration_benign: RowCount
    operating_status: OperatingPointStatus


class ClientCountRow(ArmRow):
    client: ClientId
    alpha: Alpha
    population: EvaluationPopulation
    hits: RowCount
    trials: RowCount


class FamilyCountRow(ClientCountRow):
    family: FamilyName


class DiscriminationRow(ArmRow):
    client: ClientId
    auroc: Rate
    auprc: Rate


class ExposureRow(ArmRow):
    client: ClientId
    family: FamilyName
    rows: RowCount
    train_rows: RowCount


class DescriptorRow(FrozenRecord):
    client: ClientId
    family: FamilyName
    descriptor: NoveltyDescriptor
    value: Score


class StatusRow(FrozenRecord):
    experiment: ExperimentName
    status: RunStatus


class InventoryEntry(FrozenRecord):
    name: FileName
    stat: StatKey
    digest: Fingerprint


class SourceInventory(FrozenRecord):
    entries: tuple[InventoryEntry, ...]


class ValidationDocument(FrozenRecord):
    validations: tuple[ValidationRecord, ...]


class LamdaSchema(FrozenRecord):
    release: LamdaRelease
    feature_count: FeatureCount
    metadata_columns: tuple[Column, ...]
    non_binary_cells_binarized: RowCount
    negative_cells: RowCount


class LamdaCounts(FrozenRecord):
    rows: RowCount
    malware: RowCount
    benign: RowCount


class LinkageSchema(FrozenRecord):
    columns: tuple[Column, ...]


class LinkageCounts(FrozenRecord):
    linked_rows: RowCount


class FamilySetDocument(FrozenRecord):
    families: tuple[FamilyName, ...]


class PartitionManifest(FrozenRecord):
    key: PartitionKey
    attempt: Rank
    eligible_controlled_pairs: RowCount
    eligible_natural_pairs: RowCount


class PlanSummary(FrozenRecord):
    mode: ExecutionMode
    config_fingerprint: Fingerprint
    runs: RowCount
    infeasible: RowCount
    seeds: tuple[Seed, ...]


class RunStatusDocument(FrozenRecord):
    status: RunStatus
    reason: FailureReason | None


class EnvironmentRecord(FrozenRecord):
    python: Message
    platform: Message
    torch: Message
    numpy: Message
    polars: Message
    scikit_learn: Message
    device: Device


class RunInputs(FrozenRecord):
    key: RunKey
    partition: Provenance
    config: Fingerprint
    targets: tuple[TargetPair, ...]


class RunManifest(FrozenRecord):
    key: RunKey
    partition: PartitionKey
    targets: tuple[TargetPair, ...]
    arms: tuple[ArmKey, ...]
    budget: RowCount
    training: Fingerprint
    config: Fingerprint
    provenance: Provenance
    environment: EnvironmentRecord
    status: RunStatus


class ProximalAnchor(FrozenRecord):
    state: StateDict
    strength: ProximalStrength
