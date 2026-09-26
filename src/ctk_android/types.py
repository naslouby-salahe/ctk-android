from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, NewType, Protocol

import numpy as np
import polars as pl
import scipy.sparse as sp
import torch
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter
from sklearn.ensemble import HistGradientBoostingClassifier

from ctk_android.enums import (
    Aggregation,
    AllowedWording,
    Artifact,
    BudgetLevel,
    ClaimName,
    ClaimStatus,
    ClientId,
    Column,
    ConsistencyMeasure,
    ContrastFamily,
    CtkAggregation,
    DatasetName,
    Device,
    DiagnosticColumn,
    DoctorCheck,
    EligibilityProfile,
    Estimand,
    EvaluationPopulation,
    EvidenceClass,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    ExposureCondition,
    ExposureMode,
    ExtensionContrast,
    ExtensionHypothesis,
    ExtensionScope,
    ExtensionStudy,
    FailureReason,
    FamilyLabelSource,
    FamilyOutcomeMeasure,
    FamilyPredictor,
    FamilySetName,
    Grouping,
    HiddadStatus,
    IntervalStatus,
    IntervalVerdict,
    LamdaRelease,
    LargeFamilyMeasure,
    Learner,
    LibraryOption,
    LogField,
    MaskingContrast,
    Metric,
    ModelFamily,
    NameFragment,
    NoveltyDescriptor,
    OperatingPointStatus,
    Pattern,
    PermutationOutcome,
    PromotionBlock,
    PromotionState,
    ReallocationStratum,
    ReportTable,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    RepresentationOutcome,
    ResultsFile,
    RobustnessScope,
    RunStatus,
    Sensitivity,
    SignTail,
    SplitRole,
    Stage,
    TradeoffComparison,
    TradeoffMeasure,
    TransferScope,
    TunedParameter,
    ValidationCheck,
    VarianceComponent,
    VarianceSource,
)

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]
OpenUnitInterval = Annotated[float, Field(gt=0.0, lt=1.0, allow_inf_nan=False)]

RandomSeed = NewType("RandomSeed", int)
SeedComponent = NewType("SeedComponent", int)
NonNegativeRandomSeed = Annotated[RandomSeed, Field(ge=0)]
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
EffectiveDoseCount = NonNegativeInt

seed_adapter: TypeAdapter[RandomSeed] = TypeAdapter(NonNegativeRandomSeed)

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
SerializedConfig = str
Message = Annotated[str, StringConstraints(min_length=1)]
FeatureColumn = Annotated[str, StringConstraints(pattern=Pattern.FEATURE_COLUMN)]
ArmLabel = NewType("ArmLabel", str)
DoseLabel = NewType("DoseLabel", str)

FloatArray = NDArray[np.float64]
Float32Array = NDArray[np.float32]
IntArray = NDArray[np.int64]
BoolArray = NDArray[np.bool_]
ByteMatrix = NDArray[np.uint8]
CsrMatrix = sp.csr_matrix
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
DoseLevelTable = pl.DataFrame
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
RoleFrame = pl.DataFrame
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
BinaryMatrix = ByteMatrix
FeatureMatrix = BinaryMatrix | Float32Array | CsrMatrix
ModelInputs = Float32Array
ColumnIds = IntArray
PositionArray = IntArray
HalfPrecision = bool
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
AnchoredTable = pl.DataFrame
TradeoffTable = pl.DataFrame
SynthesisTable = pl.DataFrame
AuditTable = pl.DataFrame
HeadroomTable = pl.DataFrame
PatternTable = pl.DataFrame
FidelityTable = pl.DataFrame
ComparisonTable = pl.DataFrame
ClientCtkTable = pl.DataFrame
VarianceTable = pl.DataFrame
SeedMatrix = FloatArray
AssociationTable = pl.DataFrame
FamilyClientTable = pl.DataFrame
LargeSelectionTable = pl.DataFrame
LargeFamilyTable = pl.DataFrame
LargeSummaryTable = pl.DataFrame
CellTable = pl.DataFrame
HeterogeneityTable = pl.DataFrame
MaskingTable = pl.DataFrame
TransferTable = pl.DataFrame
GroupCodes = IntArray
VarianceVector = FloatArray
DevianceAndGradient = tuple[float, FloatArray]
RunsInMode = bool
ArmSeries = pl.DataFrame
MeanTrialCount = NonNegativeFloat
ScopeMap = dict[ExperimentName, RobustnessScope]
ForestText = str
PlotSize = float

Directory = Path
Moment = datetime
GitOutput = str
GitArguments = list[str]
Clean = bool
LamdaReleaseFiles = list[Path]
EntryName = Annotated[str, StringConstraints(min_length=1)]
File = Path
# Exact PyTorch Module.state_dict/load_state_dict boundary payload.
StateDict = dict[str, torch.Tensor]


class FrozenRecord(BaseModel):
    model_config = ConfigDict(
        frozen=True, extra=LibraryOption.FORBID_EXTRA, arbitrary_types_allowed=True
    )


class ForestRow(FrozenRecord):
    metric: Metric | None
    sensitivity: Sensitivity | None
    scope: RobustnessScope
    salt: Salt
    learner: Learner
    alpha: Alpha


LabelPrefix = Annotated[str, StringConstraints(min_length=1)]
SupportCount = NonNegativeInt
StatKey = Annotated[str, StringConstraints(min_length=1)]
FileName = Annotated[str, StringConstraints(min_length=1)]


class PartitionKey(FrozenRecord):
    seed: NonNegativeRandomSeed
    salt: Salt
    grouping: Grouping
    profile: EligibilityProfile


class RunKey(FrozenRecord):
    mode: ExecutionMode
    experiment: ExperimentName
    seed: NonNegativeRandomSeed
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


class McNdroidShard(FrozenRecord):
    matrix: File
    meta: File


class ShaBlock(FrozenRecord):
    shas: ShaSeries
    matrix: CsrMatrix


class CsrFiles(FrozenRecord):
    data: File
    indices: File
    indptr: File


# Learned input preprocessing of a representation (EXT-REP R2/R3): fitted by each trained model
# from its own training rows only (Roadmap 31.4, Amendment A3). `min_prevalence` None means
# standardise every column; otherwise keep columns whose share of positive values reaches it.
class TransformRule(FrozenRecord):
    min_prevalence: Fraction | None


class InputTransform(FrozenRecord):
    columns: ColumnIds | None
    mean: ModelInputs
    spread: ModelInputs


class OverlapManifest(FrozenRecord):
    lamda_rows: RowCount
    rows: RowCount
    malware_rows: RowCount
    benign_rows: RowCount
    lamda_features: FeatureCount
    static_features: FeatureCount
    graph_features: FeatureCount
    json_columns_total: FeatureCount


class Provenance(FrozenRecord):
    stage: Stage
    inputs: Fingerprint


class CtkError(Exception):
    def __init__(self, reason: FailureReason, message: Message) -> None:
        super().__init__(message)
        self.reason = reason


class LamdaTable(FrozenRecord):
    metadata: LamdaMetadataTable
    features: BinaryMatrix
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

    def label(self) -> ArmLabel:
        dose = NameFragment.ALL_DOSE if self.dose is None else f"{self.dose}"
        parts = [self.learner, self.condition, f"{NameFragment.DOSE}{dose}"]
        if self.tuning is not None:
            parts.append(f"{self.tuning.parameter}{NameFragment.SEPARATOR}{self.tuning.level}")
        return ArmLabel(NameFragment.ARM_SEPARATOR.join(parts))

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
    transform: InputTransform | None


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
    seeds: tuple[NonNegativeRandomSeed, ...]


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
    salt: Salt
    alpha: Alpha
    sensitivity: Sensitivity
    aggregation: CtkAggregation
    micro_pooled_ctk_gain: Effect
    median_difference: Effect
    ci_low: Effect | None
    ci_high: Effect | None
    positive_seeds: RowCount
    seed_count: RowCount


class SeedSummary(FrozenRecord):
    mean_difference: Effect
    median_difference: Effect
    ci_low: Effect | None
    ci_high: Effect | None
    positive_seeds: RowCount
    seed_count: RowCount


class EvidenceRow(SeedSummary):
    evidence_class: EvidenceClass


class AnchoredEffectRow(EvidenceRow):
    learner: Learner
    estimand: Estimand


class AnchoredSelectionRow(FrozenRecord):
    evidence_class: EvidenceClass
    client: ClientId
    seeds_selected: RowCount
    mean_local_recall: Fraction


class VarianceRow(FrozenRecord):
    evidence_class: EvidenceClass
    experiment: ExperimentName
    learner: Learner
    source: VarianceSource
    sum_squares: NonNegativeFloat
    degrees_of_freedom: RowCount
    share: Fraction


class RandomEffectsDesign(FrozenRecord):
    response: FloatArray
    factors: tuple[GroupCodes, ...]


class VarianceEstimate(FrozenRecord):
    variances: VarianceVector
    converged: bool


class HeterogeneityRow(FrozenRecord):
    evidence_class: EvidenceClass
    experiment: ExperimentName
    population: EvaluationPopulation
    component: VarianceComponent
    variance: NonNegativeFloat
    share: Fraction
    share_ci_low: Fraction | None
    share_ci_high: Fraction | None
    observations: RowCount
    cells: RowCount
    replicated_cells: RowCount
    seeds: RowCount
    families: RowCount
    clients: RowCount
    sampling_noise_reference: NonNegativeFloat
    converged: bool
    bootstrap_resamples: RowCount


class MaskingRow(FrozenRecord):
    evidence_class: EvidenceClass
    experiment: ExperimentName
    learner: Learner
    contrast: MaskingContrast
    aggregate_metric: Metric
    recall_metric: Metric
    seed_count: RowCount
    aggregate_mean: Effect
    aggregate_ci_low: Effect | None
    aggregate_ci_high: Effect | None
    aggregate_verdict: IntervalVerdict
    recall_mean: Effect
    recall_ci_low: Effect | None
    recall_ci_high: Effect | None
    recall_verdict: IntervalVerdict
    material_gain_threshold: Effect
    verdicts_opposed: bool
    masked_gain: bool
    masked_loss: bool
    sign_disagreement_seeds: RowCount
    gain_missed_seeds: RowCount
    false_reassurance_seeds: RowCount
    opposite_conclusion_seeds: RowCount
    seed_correlation: Correlation | None


class TransferRow(FrozenRecord):
    evidence_class: EvidenceClass
    experiment: ExperimentName
    population: EvaluationPopulation
    scope: TransferScope
    client: ClientId | None
    family: FamilyName | None
    seed_count: RowCount
    observations: RowCount
    cells: RowCount
    pooling_mean: Effect
    pooling_ci_low: Effect | None
    pooling_ci_high: Effect | None
    hurt_seeds: RowCount
    hurts: bool
    hurts_interval_below_zero: bool
    ctk_mean: Effect
    ctk_ci_low: Effect | None
    ctk_ci_high: Effect | None
    repair_mean: Effect
    repair_ci_low: Effect | None
    repair_ci_high: Effect | None
    new_capability_mean: Effect
    new_capability_ci_low: Effect | None
    new_capability_ci_high: Effect | None
    harm_mean: Effect
    harm_ci_low: Effect | None
    harm_ci_high: Effect | None
    repair_share: Effect | None


class FamilyAssociationRow(FrozenRecord):
    evidence_class: EvidenceClass
    experiment: ExperimentName
    predictor: FamilyPredictor
    outcome_measure: FamilyOutcomeMeasure
    rho: Correlation
    p_value: PValue
    families: RowCount


class FamilyClientRow(EvidenceRow):
    experiment: ExperimentName
    client: ClientId
    family: FamilyName
    local_recall: Fraction
    absent_recall: Fraction
    peer_recall: Fraction
    hidden_trials_per_seed: NonNegativeFloat


class LargeFamilyRow(FrozenRecord):
    experiment: ExperimentName
    family: FamilyName
    seed_count: SupportCount
    ctk_gain: Effect
    ctk_sd: NonNegativeFloat | None
    local_recall: Fraction
    absent_recall: Fraction
    peer_recall: Fraction
    trials: NonNegativeFloat
    min_trials: RowCount
    novelty: Score | None
    meets_threshold: bool


class LargeSummaryRow(FrozenRecord):
    measure: LargeFamilyMeasure
    assumed_rho: Correlation | None
    value: Score


class ArmSpec(FrozenRecord):
    learner: Learner
    condition: ExposureCondition


class ArmPair(FrozenRecord):
    minuend: ArmSpec
    subtrahend: ArmSpec


class ContrastSpec(FrozenRecord):
    contrast: MaskingContrast
    arms: ArmPair


class MetricPair(FrozenRecord):
    aggregate: Metric
    recall: Metric


class TransferScopeSpec(FrozenRecord):
    scope: TransferScope
    keys: tuple[Column, ...]


class ClientCtkRow(FrozenRecord):
    evidence_class: EvidenceClass
    client: ClientId
    learner: Learner
    alpha: Alpha
    population: EvaluationPopulation
    local_recall: Fraction
    absent_recall: Fraction
    peer_recall: Fraction
    full_recall: Fraction | None
    total_gain: Effect
    total_ci_low: Effect | None
    total_ci_high: Effect | None
    pooling_gain: Effect
    pooling_ci_low: Effect | None
    pooling_ci_high: Effect | None
    ctk_gain: Effect
    ctk_ci_low: Effect | None
    ctk_ci_high: Effect | None
    ctk_positive_seeds: RowCount
    known_family_recall_local: Fraction | None
    known_family_recall_collaborative: Fraction | None
    known_family_change: Effect | None
    known_family_change_ci_low: Effect | None
    known_family_change_ci_high: Effect | None
    realised_fpr: Fraction | None
    hidden_family_trials_per_seed: MeanTrialCount
    contributing_seeds: RowCount
    eligible_pairs: RowCount
    interval_status: IntervalStatus


class TradeoffRow(EvidenceRow):
    learner: Learner
    comparison: TradeoffComparison
    measure: TradeoffMeasure
    within_tolerance: bool | None


class SynthesisRow(EvidenceRow):
    scope: RobustnessScope
    experiment: ExperimentName
    salt: Salt
    alpha: Alpha
    metric: Metric | None
    learner: Learner
    aggregation: CtkAggregation
    sensitivity: Sensitivity | None
    exceeds_practical_threshold: bool
    ci_excludes_zero: bool | None


class PermutationAuditRow(EvidenceRow):
    experiment: ExperimentName
    alpha: Alpha
    metric: Metric
    learner: Learner
    outcome: PermutationOutcome


class HeadroomRow(EvidenceRow):
    learner: Learner
    metric: Metric
    gate_threshold: Effect
    exceeds_gate_threshold: bool


class AssociationRow(FrozenRecord):
    experiment: ExperimentName
    rho: Correlation
    p_value: PValue
    ci_low: Effect | None
    ci_high: Effect | None
    families: RowCount


class ClusterRow(FrozenRecord):
    experiment: ExperimentName
    seed: NonNegativeRandomSeed
    salt: Salt
    ci_low: Effect
    ci_high: Effect


class PlotAxes(Protocol):
    """Matplotlib boundary; artist keyword sets vary by backend."""

    def bar(self, *args: Any, **kwargs: Any) -> object: ...

    def plot(self, *args: Any, **kwargs: Any) -> object: ...

    def scatter(self, *args: Any, **kwargs: Any) -> object: ...

    def errorbar(self, *args: Any, **kwargs: Any) -> object: ...

    def imshow(self, *args: Any, **kwargs: Any) -> object: ...

    def annotate(self, *args: Any, **kwargs: Any) -> object: ...

    def axhline(self, *args: Any, **kwargs: Any) -> object: ...

    def axvline(self, *args: Any, **kwargs: Any) -> object: ...

    def set_ylim(self, *args: Any, **kwargs: Any) -> object: ...

    def tick_params(self, *args: Any, **kwargs: Any) -> object: ...

    def grid(self, *args: Any, **kwargs: Any) -> object: ...

    def set_xticks(self, *args: Any, **kwargs: Any) -> object: ...

    def set_yticks(self, *args: Any, **kwargs: Any) -> object: ...

    def set_xlabel(self, *args: Any, **kwargs: Any) -> object: ...

    def set_ylabel(self, *args: Any, **kwargs: Any) -> object: ...

    def set_title(self, *args: Any, **kwargs: Any) -> object: ...

    def set_xscale(self, *args: Any, **kwargs: Any) -> object: ...

    def legend(self, *args: Any, **kwargs: Any) -> object: ...


class PlotFigure(Protocol):
    def add_subplot(self, *args: Any, **kwargs: Any) -> PlotAxes: ...

    def suptitle(self, *args: Any, **kwargs: Any) -> object: ...

    def subplots_adjust(self, *args: Any, **kwargs: Any) -> object: ...

    def colorbar(self, *args: Any, **kwargs: Any) -> object: ...

    def savefig(self, *args: Any, **kwargs: Any) -> object: ...


class PlotBand(FrozenRecord):
    mean: Effect | None
    lower: Effect | None
    upper: Effect | None


class ManifestEntry(FrozenRecord):
    name: FileName
    digest: Fingerprint
    evidence_class: EvidenceClass


class ResultsManifest(FrozenRecord):
    mode: ExecutionMode
    files: tuple[ManifestEntry, ...]


class SourceProvenance(FrozenRecord):
    lamda: Fingerprint
    androzoo: Fingerprint


class CodeProvenance(FrozenRecord):
    execution_revision: Message
    analysis_revision: Message
    analysis_sources_clean: bool


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
    design: ExperimentDesign = ExperimentDesign.STANDARD
    representation: Representation | None = None


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
SpreadVector = FloatArray
SeedCountVector = FloatArray
ExperimentScope = tuple[ExperimentName, ...] | None
ModeSelection = tuple[ExecutionMode, ...]
IncludeDesigns = bool
Reusable = bool
Stale = bool
Passed = bool
Refuted = bool
Positive = bool
IncludeAllDose = bool
Records = Sequence[FrozenRecord]
LabelValues = Sequence[StrEnum | FamilyName]
Predicate = pl.Expr
FamilyMasks = dict[FamilyName, BoolArray]
ClientPools = dict[ClientId, IntArray]
ClientScorers = dict[ClientId, Scorer]
PopulationMasks = dict[EvaluationPopulation, BoolArray]
DescriptorValues = dict[NoveltyDescriptor, Score]
FamilySets = dict[FamilySetName, tuple[FamilyName, ...]]


class LargeFamilySelection(FrozenRecord):
    table: LargeSelectionTable
    sets: FamilySets


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
LogFields = dict[LogField, LogValue]


class FrozenHyperparameters(FrozenRecord):
    local_epochs: TuningValue
    finetune_epochs: TuningValue
    fedprox_mu: TuningValue


ExtensionTable = pl.DataFrame
SeedRecallTable = pl.DataFrame
PlaceboTable = pl.DataFrame
ClientRowCounts = dict[ClientId, RowCount]
FamilyFitRows = dict[FamilyName, dict[ClientId, IntArray]]
FamilyRows = dict[FamilyName, IntArray]
LevelRows = dict[SupportCount, TrainingRows]
ClientPieces = dict[ClientId, list[IntArray]]
MalwareRowsTable = pl.DataFrame
FamilyRowTotals = dict[FamilyName, RowCount]
FamilyCentroids = dict[FamilyName, Prevalence]


class AggregationRule(FrozenRecord):
    rule: Aggregation
    trim_per_side: SupportCount


class DoseDraw(FrozenRecord):
    pooled: FamilyRows
    owners: FamilyRows
    replacement_order: TrainingRows


class PlaceboChoice(FrozenRecord):
    client: ClientId
    family: FamilyName
    placebo: FamilyName
    counts: ClientRowCounts
    allocated: ClientRowCounts
    reallocated: RowCount
    hidden_peer_fit: RowCount
    placebo_peer_fit: RowCount


class PlaceboOption(FrozenRecord):
    distance: SupportCount
    family: FamilyName
    peer_fit: RowCount


class PlaceboPairRow(FrozenRecord):
    client: ClientId
    family: FamilyName
    placebo_family: FamilyName
    need: RowCount
    reallocated: RowCount
    hidden_peer_fit: RowCount
    placebo_peer_fit: RowCount
    centroid_distance: Score
    nearest_known_distance: Score | None
    placebo_rank: Rank | None
    known_families: RowCount


class Relatedness(FrozenRecord):
    centroid_distance: Score
    nearest_known_distance: Score | None
    placebo_rank: Rank | None
    known_families: RowCount


class DesignSetting(FrozenRecord):
    condition: ExposureCondition
    dose: DoseRequest
    aggregation: Aggregation | None
    rows: TrainingRows


class ArmSelector(FrozenRecord):
    condition: ExposureCondition
    dose: DoseRequest
    aggregation: Aggregation | None


class SelectorPair(FrozenRecord):
    minuend: ArmSelector
    subtrahend: ArmSelector


class EffectCell(FrozenRecord):
    scope: ExtensionScope
    population: EvaluationPopulation
    alpha: Alpha


class ExtensionEffectRow(FrozenRecord):
    hypothesis: ExtensionHypothesis
    scope: ExtensionScope
    learner: Learner
    population: EvaluationPopulation
    alpha: Alpha
    contrast: ExtensionContrast
    level: DoseRequest
    seed_count: RowCount
    mean: Effect
    median: Effect
    positive_seeds: RowCount
    ci_low: Effect | None
    ci_high: Effect | None
    alternative: SignTail
    null_reference: Effect
    p_value: PValue
    p_holm: PValue | None
    margin: Effect
    above_margin: bool
    within_band: bool
    above_noninferiority: bool


HolmKey = tuple[
    ExtensionHypothesis, ExtensionScope, Learner, EvaluationPopulation, Alpha, ExtensionContrast
]
HolmIndex = dict[HolmKey, list[RowCount]]
ScopeExperiments = dict[ExtensionScope, tuple[ExperimentName, ...]]


class ContrastHeader(FrozenRecord):
    hypothesis: ExtensionHypothesis
    learner: Learner
    contrast: ExtensionContrast
    level: DoseRequest
    tail: SignTail
    reference: Effect


class ContrastEffects(FrozenRecord):
    seeds: ExtensionTable
    rows: tuple[ExtensionEffectRow, ...]


class ConsistencyRow(FrozenRecord):
    experiment: ExperimentName
    measure: ConsistencyMeasure
    level: DoseRequest
    checked: RowCount
    mismatched: RowCount
    rows: RowCount


class ExtensionVerdictRow(FrozenRecord):
    hypothesis: ExtensionHypothesis
    scope: ExtensionScope
    learner: Learner
    population: EvaluationPopulation
    alpha: Alpha
    met: bool | None
    onset_level: DoseRequest


MetVerdict = bool | None


class RecallArm(FrozenRecord):
    learner: Learner
    condition: ExposureCondition


RepresentationOf = dict[ExperimentName, Representation]
RepresentationTable = pl.DataFrame
PlannedTargetsBySeed = dict[RandomSeed, tuple[TargetPair, ...]]


class RepresentationEffectRow(FrozenRecord):
    measure: RepresentationMeasure
    representation: Representation
    group: RepresentationGroup
    family: FamilyName | None
    population: EvaluationPopulation
    alpha: Alpha
    seed_count: RowCount
    mean_level: Effect
    mean_baseline: Effect
    mean: Effect
    median: Effect
    positive_seeds: RowCount
    ci_low: Effect | None
    ci_high: Effect | None
    p_value: PValue
    p_margin: PValue
    p_holm: PValue | None
    margin: Effect
    above_margin: bool
    below_margin: bool
    within_band: bool


class RepresentationLevelRow(FrozenRecord):
    measure: RepresentationMeasure
    representation: Representation
    group: RepresentationGroup
    family: FamilyName | None
    population: EvaluationPopulation
    alpha: Alpha
    seed_count: RowCount
    mean: Effect
    ci_low: Effect | None
    ci_high: Effect | None


class RepresentationVerdictRow(FrozenRecord):
    hypothesis: ExtensionHypothesis
    representation: Representation | None
    met: bool | None
    outcome: RepresentationOutcome | HiddadStatus | None


class RepresentationTables(FrozenRecord):
    seeds: RepresentationTable
    effects: tuple[RepresentationEffectRow, ...]
    levels: tuple[RepresentationLevelRow, ...]


StabilitySeedTable = pl.DataFrame
EligibilityStabilityTable = pl.DataFrame
SeedPairsTables = dict[RandomSeed, PairsTable]


class LargeStabilityRow(FrozenRecord):
    family: FamilyName
    family_set: FamilySetName
    rank: Rank
    seed_count: SupportCount
    eligible_seeds: SupportCount
    eligible_seed_fraction: Fraction
    eligible_in_every_seed: bool
    measured_seeds: SupportCount
    min_eligible_pairs: SupportCount
    mean_eligible_pairs: NonNegativeFloat
    max_eligible_pairs: SupportCount
    min_eligible_target_test_rows: RowCount
    mean_eligible_target_test_rows: NonNegativeFloat


# Measures of one Spearman association: rho, p value, interval low, high and width.
AssociationMeasures = tuple[
    LargeFamilyMeasure,
    LargeFamilyMeasure,
    LargeFamilyMeasure,
    LargeFamilyMeasure,
    LargeFamilyMeasure,
]


DiagnosticTable = pl.DataFrame
DiagnosticCell = (
    str | bytes | int | float | Decimal | bool | date | datetime | time | timedelta | None
)
DiagnosticColumnName = NewType("DiagnosticColumnName", str)
DiagnosticKey = Column | DiagnosticColumn | DiagnosticColumnName
DiagnosticRow = dict[DiagnosticKey, DiagnosticCell]
DiagnosticRows = list[DiagnosticRow]


class DiagnosticInterval(FrozenRecord):
    low: Effect | None
    high: Effect | None


class DiagnosticSummary(FrozenRecord):
    count: RowCount
    mean: Effect | None
    median: Effect | None
    positive_count: RowCount
    low: Effect | None
    high: Effect | None


DiagnosticVector = FloatArray
DiagnosticMatrix = FloatArray
ScoreFiles = dict[ArmLabel, pl.DataFrame]
FitParameters = tuple[float, ...]
StudyCache = dict[PartitionKey, StudyTable]
StratumTables = dict[ReallocationStratum, pl.DataFrame]


class ScopedExperiments(FrozenRecord):
    scope: ExtensionScope
    experiments: tuple[ExperimentName, ...]


class ControlStratum(FrozenRecord):
    scoped: ScopedExperiments
    population: EvaluationPopulation
    alpha: Alpha


class DoseFit(FrozenRecord):
    parameters: FitParameters
    predicted: DiagnosticVector


# Stored per-row scores and operating tables of one representation run, read-only.
class ScoredRun(FrozenRecord):
    representation: Representation
    seed: NonNegativeRandomSeed
    targets: tuple[TargetPair, ...]
    study: StudyTable
    thresholds: OperatingTable
    families: FamilyCountsTable
    operating: OperatingTable
    scores: ScoreFiles


class RepresentationDiagnostics(FrozenRecord):
    targets: DiagnosticTable
    health: DiagnosticTable
    effects: DiagnosticTable


class InfluenceTables(FrozenRecord):
    families: DiagnosticTable
    summary: DiagnosticTable


class DoseDiagnostics(FrozenRecord):
    curve: DiagnosticTable
    increments: DiagnosticTable
    family_curves: DiagnosticTable
    family_summary: DiagnosticTable
    associations: DiagnosticTable
    client_curves: DiagnosticTable
    model_fits: DiagnosticTable
    heterogeneity: DiagnosticTable


class ControlDiagnostics(FrozenRecord):
    strata: DiagnosticTable
    clients: DiagnosticTable
    reallocation: DiagnosticTable
    slopes: DiagnosticTable
    associations: DiagnosticTable
    placebo_pairs: DiagnosticTable
    families: DiagnosticTable
    support_levels: DiagnosticTable
    support: DiagnosticTable


class SynthesisDiagnostics(FrozenRecord):
    cells: DiagnosticTable
    taxonomy: DiagnosticTable
    family_ctk: DiagnosticTable
    large_family_ctk: DiagnosticTable
    large_taxonomy: DiagnosticTable
    rank_concordance: DiagnosticTable
    large_associations: DiagnosticTable


class FileDigest(FrozenRecord):
    name: FileName
    sha256: Fingerprint


class RunConfigFingerprint(FrozenRecord):
    experiment: ExperimentName
    fingerprint: Fingerprint


class DataFingerprints(FrozenRecord):
    lamda: Fingerprint
    androzoo: Fingerprint
    mcndroid_inventory: Fingerprint | None


class StudyProvenance(FrozenRecord):
    name: ExtensionStudy
    mode: ExecutionMode
    seeds: tuple[NonNegativeRandomSeed, ...]
    evidence_class: EvidenceClass
    protocol: FileDigest | None
    config_fingerprint: Fingerprint
    run_fingerprints: tuple[RunConfigFingerprint, ...]
    data: DataFingerprints
    code: CodeProvenance
    artifacts: tuple[ManifestEntry, ...]
    superseded: tuple[FileDigest, ...]


class ExtensionProvenance(FrozenRecord):
    studies: tuple[StudyProvenance, ...]


class StudyRequest(FrozenRecord):
    study: ExtensionStudy
    mode: ExecutionMode
    experiments: tuple[ExperimentName, ...]
    evidence_class: EvidenceClass
    code: CodeProvenance
    artifacts: tuple[ManifestEntry, ...]


class PromotedOutput(FrozenRecord):
    artifact: Artifact
    evidence_class: EvidenceClass


class DesignPromotion(FrozenRecord):
    study: ExtensionStudy
    experiments: tuple[ExperimentName, ...]
    index_artifact: Artifact
    artifacts: tuple[Artifact, ...] = ()
    outputs: tuple[PromotedOutput, ...] = ()
    code_file: ResultsFile
