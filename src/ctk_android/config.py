import hashlib
import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from ctk_android.enums import (
    BudgetLevel,
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
    NoveltyDescriptor,
)
from ctk_android.types import (
    Alpha,
    BatchSize,
    BlendWeight,
    Confidence,
    DropoutRate,
    Epochs,
    ExceedanceCount,
    Fingerprint,
    FamilyName,
    Fraction,
    LabelPrefix,
    LearningRate,
    ProximalStrength,
    ReleaseName,
    ResampleCount,
    RowCount,
    Rounds,
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


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SeedConfig(Frozen):
    smoke: tuple[Seed, ...]
    development: tuple[Seed, ...]
    confirmatory: tuple[Seed, ...]

    @model_validator(mode="after")
    def _disjoint_roles(self) -> "SeedConfig":
        roles = (set(self.smoke), set(self.development), set(self.confirmatory))
        if sum(len(role) for role in roles) != len(set().union(*roles)):
            raise ValueError("seed roles must be disjoint")
        return self

    def for_mode(self, mode: ExecutionMode) -> tuple[Seed, ...]:
        if mode is ExecutionMode.SMOKE:
            return self.smoke
        if mode is ExecutionMode.DEVELOPMENT:
            return self.development
        return self.confirmatory


class SaltConfig(Frozen):
    primary: Salt
    sensitivity: tuple[Salt, ...]


class ProjectConfig(Frozen):
    seeds: SeedConfig
    salts: SaltConfig
    device: Device
    logging_level: LabelPrefix


class PartitionConfig(Frozen):
    fit: Fraction
    calibration: Fraction
    test: Fraction
    attempts: SupportCount

    @model_validator(mode="after")
    def _sums_to_one(self) -> "PartitionConfig":
        if abs(self.fit + self.calibration + self.test - 1.0) > 1e-9:
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
    linear_epochs: Epochs
    trees: TreeConfig
    min_rows_per_class: SupportCount


class OperatingConfig(Frozen):
    primary_alpha: Alpha
    alphas: tuple[Alpha, ...]
    min_expected_exceedances: ExceedanceCount


class NoveltyConfig(Frozen):
    min_active_prevalence: Fraction
    min_known_family_rows: SupportCount
    primary_descriptor: NoveltyDescriptor


class FairnessGrids(Frozen):
    local_epochs: tuple[Epochs, ...]
    finetune_epochs: tuple[Epochs, ...]
    fedprox_mu: tuple[ProximalStrength, ...]


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
    top_family_removal_count: SupportCount
    permutation_seed_offset: Seed
    fairness_grids: FairnessGrids
    experiments: dict[ExperimentName, ExperimentSpec]


class GateConfig(Frozen):
    local_deficit_min_seeds: SupportCount
    local_deficit_min_gap: Fraction
    collaboration_min_gain: Fraction
    ctk_min_gain: Fraction
    ctk_min_positive_seeds: SupportCount
    pooling_majority_share: Fraction
    dose_min_peers: SupportCount
    dose_min_gain: Fraction
    dose_max_family_share: Fraction
    known_family_tolerance: Fraction
    fpr_tolerance: Fraction
    poor_full_recall: Fraction
    novelty_min_abs_spearman: Fraction
    mechanism_mean_gap: Fraction
    mechanism_worst_gap: Fraction
    permutation_null_max: Fraction
    operating_point_tolerance: Fraction
    dose_monotone_tolerance: Fraction
    heterogeneity_min: Fraction


class StatisticsConfig(Frozen):
    bootstrap_resamples: ResampleCount
    cluster_bootstrap_resamples: ResampleCount
    confidence_level: Confidence
    statistics_seed: Seed
    share_min_total_gain: Fraction
    gates: GateConfig


class Config(Frozen):
    project: ProjectConfig
    data: DataConfig
    experiments: ExperimentsConfig
    statistics: StatisticsConfig

    def fingerprint(self) -> Fingerprint:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


def load_config(config_dir: Path) -> Config:
    def read(name: str) -> YamlDocument:
        return yaml.safe_load((config_dir / name).read_text(encoding="utf-8"))

    return Config.model_validate(
        {
            "project": read("project.yaml"),
            "data": read("data.yaml"),
            "experiments": read("experiments.yaml"),
            "statistics": read("statistics.yaml"),
        }
    )
