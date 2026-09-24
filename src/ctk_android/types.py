from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any, Protocol

import numpy as np
import polars as pl
import torch
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter
from sklearn.ensemble import HistGradientBoostingClassifier

from ctk_android.enums import (
    AllowedWording,
    Artifact,
    BudgetLevel,
    ClaimName,
    ClaimStatus,
    ClientId,
    Column,
    ContrastFamily,
    DatasetName,
    Device,
    DoctorCheck,
    EligibilityProfile,
    Estimand,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExposureMode,
    FailureReason,
    FamilyLabelSource,
    FamilySetName,
    Grouping,
    LamdaRelease,
    Learner,
    LibraryOption,
    Metric,
    ModelFamily,
    NameFragment,
    NoveltyDescriptor,
    OperatingPointStatus,
    Pattern,
    PromotionBlock,
    PromotionState,
    ReportTable,
    RunStatus,
    Sensitivity,
    SplitRole,
    Stage,
    TunedParameter,
    ValidationCheck,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
OpenUnitInterval = Annotated[float, Field(gt=0.0, lt=1.0, allow_inf_nan=False)]

Seed = NonNegativeInt
Salt = NonNegativeInt
RowCount = NonNegativeInt
FeatureCount = PositiveInt
Epochs = PositiveInt
Rounds = PositiveInt
BatchSize = PositiveInt
UnitCount = PositiveInt
ResampleCount = PositiveInt
TreeIterations = PositiveInt
TreeDepth = PositiveInt
VtCount = NonNegativeInt
Rank = NonNegativeInt
DoseSweep = bool
FairnessGrid = bool
TuningValue = NonNegativeFloat
Axis = NonNegativeInt
ExceedanceCount = PositiveInt

seed_adapter: TypeAdapter[Seed] = TypeAdapter(Seed)

Fraction = UnitInterval
Seconds = NonNegativeFloat
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

FamilyName = Annotated[str, StringConstraints(strip_whitespace=True)]
YearMonth = Annotated[str, StringConstraints(pattern=Pattern.YEAR_MONTH)]
Fingerprint = Annotated[str, StringConstraints(pattern=Pattern.SHA256)]
Message = Annotated[str, StringConstraints(min_length=1)]
FeatureColumn = Annotated[str, StringConstraints(pattern=Pattern.FEATURE_COLUMN)]

FloatArray = NDArray[np.float64]
Float32Array = NDArray[np.float32]
IntArray = NDArray[np.int64]
BoolArray = NDArray[np.bool_]
ByteMatrix = NDArray[np.uint8]
ObjectArray = NDArray[np.object_]

Table = pl.DataFrame
SummaryTable = pl.DataFrame
DecompositionTable = pl.DataFrame
FamilyCountsTable = pl.DataFrame
FamilySeedTable = pl.DataFrame
FamilyEffectsTable = pl.DataFrame
FamilyArmTable = pl.DataFrame
DoseRecallTable = pl.DataFrame
ExposureTable = pl.DataFrame
TargetsTable = pl.DataFrame
EffectiveDoseTable = pl.DataFrame
DoseCurveTable = pl.DataFrame
EffectsTable = pl.DataFrame
FamilyGainsTable = pl.DataFrame
SeedMeansTable = pl.DataFrame
ClaimsTable = pl.DataFrame
DescriptorTable = pl.DataFrame
NoveltyTable = pl.DataFrame
DescriptorScoreTable = pl.DataFrame
MicroGainTable = pl.DataFrame
RobustnessTable = pl.DataFrame
PooledRecallTable = pl.DataFrame
GroupTable = pl.DataFrame
JoinedTable = pl.DataFrame
UnmatchedTable = pl.DataFrame
AssignmentsTable = pl.DataFrame
ClientSupportTable = pl.DataFrame
LabelledTable = pl.DataFrame
FamilySupportTable = pl.DataFrame
EligibilityTable = pl.DataFrame
RoleCountsTable = pl.DataFrame
RoleSliceTable = pl.DataFrame
ClientFitRowsTable = pl.DataFrame
PairsTable = pl.DataFrame
IdentitiesTable = pl.DataFrame
ComponentSummaryTable = pl.DataFrame
LamdaMetadataTable = pl.DataFrame
AndroZooTable = pl.DataFrame
ClientCountsTable = pl.DataFrame
DiscriminationTable = pl.DataFrame
OperatingTable = pl.DataFrame
RatesTable = pl.DataFrame
MetricTable = pl.DataFrame
FamilyRescueTable = pl.DataFrame
RunIndexTable = pl.DataFrame
ClientAuditTable = pl.DataFrame
ArmComparisonTable = pl.DataFrame
DecompositionReportTable = pl.DataFrame
DoseReportTable = pl.DataFrame
FamilyLevelTable = pl.DataFrame
ClusterTable = pl.DataFrame
StatusCountsTable = pl.DataFrame
StudyTable = pl.DataFrame
ValueSeries = pl.Series
RoleSeries = pl.Series
PackageSeries = pl.Series
ShaSeries = pl.Series
RowIndices = IntArray
Prevalence = FloatArray
ActiveMask = BoolArray
NoveltyVector = FloatArray
GainVector = FloatArray
SeedEffects = FloatArray
PValueVector = FloatArray
HitVector = IntArray
TrialVector = IntArray
GroupIds = IntArray
IdentityIds = IntArray
FeatureMatrix = ByteMatrix
LabelVector = IntArray
AttributeColumn = ObjectArray
RowMask = BoolArray
LogitVector = FloatArray
ScoreVector = FloatArray
Priorities = FloatArray
WeightVector = FloatArray
LogitChunk = Float32Array
PlotVector = FloatArray
SelectionTable = pl.DataFrame

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


class CtkError(Exception):
    def __init__(self, reason: FailureReason, message: Message) -> None:
        super().__init__(message)
        self.reason = reason


class LamdaTable(FrozenRecord):
    metadata: LamdaMetadataTable
    features: FeatureMatrix
    non_binary_cells: RowCount
    negative_cells: RowCount


class JoinResult(FrozenRecord):
    joined: JoinedTable
    unmatched: UnmatchedTable
    validations: tuple[ValidationRecord, ...]


class TargetPair(FrozenRecord):
    client: ClientId
    family: FamilyName


class PartitionResult(FrozenRecord):
    roles: RoleSeries
    attempt: NonNegativeInt
    controlled: PairsTable
    natural: PairsTable
    validations: tuple[ValidationRecord, ...]


class StageReport(FrozenRecord):
    stage: Stage
    directory: Directory
    reused: bool
    fingerprint: Fingerprint


DoseRequest = NonNegativeInt | None
TrainingRows = dict[ClientId, IntArray]


class ArmRow(FrozenRecord):
    learner: Learner
    condition: ExposureCondition
    dose: DoseRequest
    parameter: TunedParameter | None = None
    tuning_value: TuningValue | None = None


class TuningPoint(FrozenRecord):
    parameter: TunedParameter
    level: TuningValue


class ArmKey(FrozenRecord):
    learner: Learner
    condition: ExposureCondition
    dose: DoseRequest
    tuning: TuningPoint | None = None

    def label(self) -> str:
        dose = NameFragment.ALL_DOSE if self.dose is None else f"{self.dose}"
        parts = [self.learner, self.condition, f"{NameFragment.DOSE}{dose}"]
        if self.tuning is not None:
            parts.append(f"{self.tuning.parameter}{NameFragment.SEPARATOR}{self.tuning.level}")
        return NameFragment.ARM_SEPARATOR.join(parts)

    def columns(self) -> ArmRow:
        return ArmRow(
            learner=self.learner,
            condition=self.condition,
            dose=self.dose,
            parameter=None if self.tuning is None else self.tuning.parameter,
            tuning_value=None if self.tuning is None else self.tuning.level,
        )


class StudyData(FrozenRecord):
    table: StudyTable
    features: FeatureMatrix


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
    unique_hits: SupportCount
    unique_trials: SupportCount


class DiscriminationRow(ArmRow):
    client: ClientId
    split: SplitRole
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


class Interval(FrozenRecord):
    low: FiniteFloat
    high: FiniteFloat


class PairedEffect(FrozenRecord):
    mean: Effect
    median: Effect
    positive_seeds: RowCount
    seeds: RowCount
    effect_size: Effect | None
    interval: Interval | None
    p_value: PValue


class RunEvidence(FrozenRecord):
    index: RunIndexTable
    summary: SummaryTable
    clients: ClientCountsTable
    families: FamilyCountsTable
    exposure: ExposureTable
    novelty: NoveltyTable


class EffectRow(FrozenRecord):
    experiment: ExperimentName
    salt: Salt
    alpha: Alpha
    metric: Metric
    learner: Learner
    estimand: Estimand
    contrast_family: ContrastFamily
    mean_difference: Effect
    median_difference: Effect | None
    positive_seeds: RowCount | None
    seed_count: RowCount
    effect_size: Effect | None
    ci_low: Effect | None
    ci_high: Effect | None
    p_value: PValue | None
    p_holm: PValue | None


class NoveltyAssociation(FrozenRecord):
    rho: Correlation
    p_value: PValue
    interval: Interval | None
    families: RowCount


class ClaimResult(FrozenRecord):
    claim: ClaimName
    claim_status: ClaimStatus
    scopes_passed: RowCount
    scopes_total: RowCount
    wording: AllowedWording


class GateEvidence(FrozenRecord):
    effects: EffectsTable
    summary: SummaryTable
    family_seed: FamilySeedTable
    family_effects: FamilyEffectsTable
    dose: DoseCurveTable
    associations: dict[ExperimentName, NoveltyAssociation | None]
    failed_validation_runs: RowCount


class RobustnessRow(FrozenRecord):
    experiment: ExperimentName
    sensitivity: Sensitivity
    mean_difference: Effect
    ci_low: Effect | None
    ci_high: Effect | None
    seed_count: RowCount


class AssociationRow(FrozenRecord):
    experiment: ExperimentName
    rho: Correlation
    p_value: PValue
    ci_low: Effect | None
    ci_high: Effect | None
    families: RowCount


class ClusterRow(FrozenRecord):
    experiment: ExperimentName
    seed: Seed
    salt: Salt
    ci_low: Effect
    ci_high: Effect


class PlotAxes(Protocol):
    """Typed facade over matplotlib axes; matplotlib's own stubs leave **kwargs unknown."""

    def bar(self, *args: Any, **kwargs: Any) -> Any: ...

    def plot(self, *args: Any, **kwargs: Any) -> Any: ...

    def scatter(self, *args: Any, **kwargs: Any) -> Any: ...

    def errorbar(self, *args: Any, **kwargs: Any) -> Any: ...

    def imshow(self, *args: Any, **kwargs: Any) -> Any: ...

    def annotate(self, *args: Any, **kwargs: Any) -> Any: ...

    def axhline(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_xticks(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_yticks(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_xlabel(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_ylabel(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_title(self, *args: Any, **kwargs: Any) -> Any: ...

    def set_xscale(self, *args: Any, **kwargs: Any) -> Any: ...

    def legend(self, *args: Any, **kwargs: Any) -> Any: ...


class PlotFigure(Protocol):
    def add_subplot(self, *args: Any, **kwargs: Any) -> Any: ...

    def suptitle(self, *args: Any, **kwargs: Any) -> Any: ...

    def colorbar(self, *args: Any, **kwargs: Any) -> Any: ...

    def savefig(self, *args: Any, **kwargs: Any) -> Any: ...


class PlotBand(FrozenRecord):
    mean: Effect | None
    lower: Effect | None
    upper: Effect | None


class ManifestEntry(FrozenRecord):
    name: FileName
    digest: Fingerprint


class ResultsManifest(FrozenRecord):
    mode: ExecutionMode
    files: tuple[ManifestEntry, ...]


class SourceProvenance(FrozenRecord):
    lamda: Fingerprint
    androzoo: Fingerprint


class CodeProvenance(FrozenRecord):
    revision: Message


class ProtocolProvenance(FrozenRecord):
    config: Fingerprint
    roadmap: Fingerprint


class PromotionDecision(FrozenRecord):
    state: PromotionState
    blocks: tuple[PromotionBlock, ...]


class EligibilityRule(FrozenRecord):
    peer_min_fit: SupportCount
    federation_min_test: SupportCount
    own_domain_min_test: SupportCount
    target_min_remaining_fit: SupportCount
    target_min_fit: SupportCount


class ExperimentSpec(FrozenRecord):
    modes: tuple[ExecutionMode, ...]
    model_family: ModelFamily
    family_set: FamilySetName
    exposure_mode: ExposureMode
    family_labels: FamilyLabelSource
    grouping: Grouping
    budget: BudgetLevel
    eligibility: EligibilityProfile
    salts: tuple[Salt, ...]
    learners: tuple[Learner, ...]
    conditions: tuple[ExposureCondition, ...]
    dose_sweep: DoseSweep
    fairness_grid: FairnessGrid


class ArmResult(FrozenRecord):
    scores: dict[ClientId, FloatArray]
    scorers: dict[ClientId, Scorer]


class PairTables(FrozenRecord):
    controlled: PairsTable
    natural: PairsTable


class SourceScan(FrozenRecord):
    fingerprint: SourceFingerprint
    inventory: SourceInventory


class PlannedTargets(FrozenRecord):
    status: RunStatus
    targets: tuple[TargetPair, ...]


class ExposureSetting(FrozenRecord):
    condition: ExposureCondition
    dose: DoseRequest


Overwrite = bool
Reused = bool
Promote = bool
Reusable = bool
Stale = bool
Passed = bool
Refuted = bool
Positive = bool
IncludeAllDose = bool
Records = Sequence[FrozenRecord]
LabelValues = Sequence[str]
Predicate = pl.Expr
FamilyMasks = dict[FamilyName, BoolArray]
ClientPools = dict[ClientId, IntArray]
ClientScorers = dict[ClientId, Scorer]
PopulationMasks = dict[EvaluationPopulation, BoolArray]
DescriptorValues = dict[NoveltyDescriptor, Score]
FamilySets = dict[FamilySetName, tuple[FamilyName, ...]]
DoseCaps = dict[FamilyName, SupportCount]
DoseTargets = dict[FamilyName, ClientId]
ExcludedFamilies = dict[ClientId, tuple[FamilyName, ...]]
TrainingSizes = dict[ClientId, set[RowCount]]
TrainingByArm = dict[ArmKey, TrainingRows]
ResultsByArm = dict[ArmKey, ArmResult]
AssociationMap = dict[ExperimentName, NoveltyAssociation | None]
ReportTables = dict[ReportTable, pl.DataFrame]
FrameLists = dict[Artifact, list[pl.DataFrame]]
HitVectors = dict[ExposureCondition, list[IntArray]]
EligibilityRules = dict[EligibilityProfile, EligibilityRule]
BudgetRows = dict[BudgetLevel, RowCount]
ExperimentSpecs = dict[ExperimentName, ExperimentSpec]


LogValue = str | int | float | bool | None
LogFields = dict[str, LogValue]


class FrozenHyperparameters(FrozenRecord):
    local_epochs: TuningValue
    finetune_epochs: TuningValue
    fedprox_mu: TuningValue
