from pathlib import Path
from typing import Annotated, Any

import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
import polars as pl
from numpy.typing import NDArray
from ctk_android.enums import (
    ClientId,
    DatasetName,
    Device,
    EligibilityProfile,
    ExecutionMode,
    ExposureCondition,
    ExperimentName,
    FailureReason,
    Grouping,
    Learner,
    ModelFamily,
    OperatingPointStatus,
    RunStatus,
    Stage,
    ValidationCheck,
)
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

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

Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
PackageName = Annotated[str, StringConstraints(min_length=1)]
FamilyName = Annotated[str, StringConstraints(strip_whitespace=True)]
YearMonth = Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}$")]
Fingerprint = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Revision = Annotated[str, StringConstraints(min_length=1)]
Message = Annotated[str, StringConstraints(min_length=1)]
FeatureColumn = Annotated[str, StringConstraints(pattern=r"^feat_\d+$")]
Label = Annotated[int, Field(ge=0, le=1)]

FloatArray = NDArray[np.float64]
Float32Array = NDArray[np.float32]
IntArray = NDArray[np.int64]
BoolArray = NDArray[np.bool_]
ByteMatrix = NDArray[np.uint8]

Directory = Path
File = Path


class FrozenRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

ReleaseName = Annotated[str, StringConstraints(min_length=1)]
LabelPrefix = Annotated[str, StringConstraints(min_length=1)]
SupportCount = NonNegativeInt
StatKey = Annotated[str, StringConstraints(min_length=1)]

YamlDocument = dict[str, Any]
JsonDocument = dict[str, Any]
InventoryDocument = dict[str, tuple[str, str]]


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
        dose = "all" if self.dose is None else str(self.dose)
        return f"{self.learner}__{self.condition}__dose-{dose}"


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
