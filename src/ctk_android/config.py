import hashlib
import json

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from ctk_android.enums import (
    BudgetLevel,
    ConfigFile,
    Device,
    EligibilityProfile,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    ExposureMode,
    FamilyLabelSource,
    FamilySetName,
    Grouping,
    Learner,
    ModelFamily,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    Alpha,
    BatchSize,
    BlendWeight,
    DropoutRate,
    Epochs,
    ExceedanceCount,
    FamilyName,
    Fingerprint,
    Fraction,
    LabelPrefix,
    LearningRate,
    ProximalStrength,
    ReleaseName,
    Rounds,
    RowCount,
    Salt,
    Seed,
    SupportCount,
    TreeDepth,
    TreeIterations,
    UnitCount,
    VtCount,
    WeightDecay,
    YamlDocument,
    YearMonth,
)

PARTITION_SUM_TOLERANCE = 1e-9


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SeedConfig(Frozen):
    smoke: tuple[Seed, ...]
    development: tuple[Seed, ...]
    confirmatory: tuple[Seed, ...]

    @model_validator(mode="after")
    def _disjoint_roles(self) -> "SeedConfig":
        every_seed = (*self.smoke, *self.development, *self.confirmatory)
        if len(every_seed) != len(set(every_seed)):
            raise ValueError("seed roles must be disjoint")
        return self

    def for_mode(self, mode: ExecutionMode) -> tuple[Seed, ...]:
        if mode is ExecutionMode.SMOKE:
            return self.smoke
        if mode is ExecutionMode.DEVELOPMENT:
            return self.development
        return self.confirmatory


class ProjectConfig(Frozen):
    seeds: SeedConfig
    device: Device
    logging_level: LabelPrefix


class PartitionConfig(Frozen):
    fit: Fraction
    calibration: Fraction
    test: Fraction
    attempts: SupportCount

    @model_validator(mode="after")
    def _sums_to_one(self) -> "PartitionConfig":
        if abs(self.fit + self.calibration + self.test - 1.0) > PARTITION_SUM_TOLERANCE:
            raise ValueError("partition fractions must sum to one")
        return self


class FamilySelectionConfig(Frozen):
    candidate_min_total_support: SupportCount
    set_size: SupportCount


class EligibilityRule(Frozen):
    peer_min_fit: SupportCount
    federation_min_test: SupportCount
    own_domain_min_test: SupportCount
    target_min_remaining_fit: SupportCount
    target_min_fit: SupportCount


class NaturalScarcityConfig(Frozen):
    max_target_share: Fraction
    peer_min_fit: SupportCount
    own_domain_min_test: SupportCount


class DataConfig(Frozen):
    lamda_release: ReleaseName
    expected_rows: RowCount
    expected_features: SupportCount
    malware_min_vt: VtCount
    benign_vt: VtCount
    singleton_prefix: LabelPrefix
    unknown_labels: tuple[FamilyName, ...]
    play_era_boundary: YearMonth
    partition: PartitionConfig
    family_selection: FamilySelectionConfig
    eligibility: dict[EligibilityProfile, EligibilityRule]
    natural_scarcity: NaturalScarcityConfig
    smoke_family_set_size: SupportCount


class TreeConfig(Frozen):
    max_iter: TreeIterations
    max_depth: TreeDepth
    learning_rate: LearningRate


class TrainingConfig(Frozen):
    batch_size: BatchSize
    learning_rate: LearningRate
    weight_decay: WeightDecay
    hidden_units: tuple[UnitCount, ...]
    dropout: DropoutRate
    local_epochs: Epochs
    central_epochs: Epochs
    federated_rounds: Rounds
    federated_local_epochs: Epochs
    fedprox_mu: ProximalStrength
    finetune_epochs: Epochs
    blend_weight: BlendWeight
    trees: TreeConfig
    min_rows_per_class: SupportCount


class OperatingConfig(Frozen):
    primary_alpha: Alpha
    alphas: tuple[Alpha, ...]
    min_expected_exceedances: ExceedanceCount
    realised_fpr_tolerance: Fraction


class NoveltyConfig(Frozen):
    min_active_prevalence: Fraction
    min_known_family_rows: SupportCount


class ExperimentSpec(Frozen):
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
    dose_sweep: bool


class ExperimentsConfig(Frozen):
    budgets: dict[BudgetLevel, RowCount]
    training: TrainingConfig
    smoke_training: TrainingConfig
    operating: OperatingConfig
    novelty: NoveltyConfig
    dose_levels: tuple[SupportCount, ...]
    dose_include_all_available: bool
    permutation_seed_offset: Seed
    experiments: dict[ExperimentName, ExperimentSpec]


class Config(Frozen):
    project: ProjectConfig
    data: DataConfig
    experiments: ExperimentsConfig

    def fingerprint(self) -> Fingerprint:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


def load_config(paths: Paths) -> Config:
    def read(name: ConfigFile) -> YamlDocument:
        return yaml.safe_load(paths.config_file(name).read_text(encoding="utf-8"))

    return Config(
        project=ProjectConfig.model_validate(read(ConfigFile.PROJECT)),
        data=DataConfig.model_validate(read(ConfigFile.DATA)),
        experiments=ExperimentsConfig.model_validate(read(ConfigFile.EXPERIMENTS)),
    )
