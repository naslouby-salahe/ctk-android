import hashlib
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from ctk_android.enums import (
    ConfigField,
    ConfigFile,
    Device,
    EligibilityProfile,
    ErrorMessage,
    ExecutionMode,
    ExperimentDesign,
    ExperimentName,
    LamdaRelease,
    LibraryOption,
    LogLevel,
    NoveltyDescriptor,
    Separator,
    SourceFamilyLabel,
    TextEncoding,
    Tolerance,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    Alpha,
    BatchSize,
    BlendWeight,
    BudgetRows,
    Confidence,
    DropoutRate,
    EligibilityRules,
    Epochs,
    ExceedanceCount,
    ExperimentSpec,
    ExperimentSpecs,
    FamilyName,
    Fingerprint,
    Fraction,
    IncludeAllDose,
    LabelPrefix,
    LearningRate,
    NonNegativeRandomSeed,
    ProximalStrength,
    RandomSeed,
    ResampleCount,
    Rounds,
    RowCount,
    RunsInMode,
    SerializedConfig,
    SupportCount,
    TreeDepth,
    TreeIterations,
    UnitCount,
    VtCount,
    WeightDecay,
    YearMonth,
)


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra=LibraryOption.FORBID_EXTRA)


class SeedConfig(Frozen):
    smoke: tuple[NonNegativeRandomSeed, ...]
    development: tuple[NonNegativeRandomSeed, ...]
    confirmatory: tuple[NonNegativeRandomSeed, ...]
    extension: tuple[NonNegativeRandomSeed, ...]
    extension_b: tuple[NonNegativeRandomSeed, ...]
    extension_dose: tuple[NonNegativeRandomSeed, ...]
    extension_controls: tuple[NonNegativeRandomSeed, ...]
    extension_representation: tuple[NonNegativeRandomSeed, ...]

    @model_validator(mode=LibraryOption.VALIDATE_AFTER)
    def _disjoint_roles(self) -> Self:
        every_seed = (
            *self.smoke,
            *self.development,
            *self.confirmatory,
            *self.extension,
            *self.extension_b,
            *self.extension_dose,
            *self.extension_controls,
            *self.extension_representation,
        )
        if len(every_seed) != len(set(every_seed)):
            raise ValueError(ErrorMessage.SEED_ROLES)
        return self

    def for_mode(self, mode: ExecutionMode) -> tuple[RandomSeed, ...]:
        if mode is ExecutionMode.SMOKE:
            return self.smoke
        if mode is ExecutionMode.DEVELOPMENT:
            return self.development
        if mode is ExecutionMode.EXTENSION:
            return self.extension
        if mode is ExecutionMode.EXTENSION_B:
            return self.extension_b
        return self.confirmatory

    def for_design(self, mode: ExecutionMode, design: ExperimentDesign) -> tuple[RandomSeed, ...]:
        if mode is ExecutionMode.EXTENSION_B and design is ExperimentDesign.EXACT_DOSE:
            return self.extension_dose
        if mode is ExecutionMode.EXTENSION_B and design is ExperimentDesign.PLACEBO_ROBUST:
            return self.extension_controls
        if mode is ExecutionMode.EXTENSION_B and design is ExperimentDesign.REPRESENTATION:
            return self.extension_representation
        return self.for_mode(mode)


class ProjectConfig(Frozen):
    seeds: SeedConfig
    device: Device
    logging_level: LogLevel


class PartitionConfig(Frozen):
    fit: Fraction
    calibration: Fraction
    test: Fraction
    attempts: SupportCount

    @model_validator(mode=LibraryOption.VALIDATE_AFTER)
    def _sums_to_one(self) -> Self:
        if abs(self.fit + self.calibration + self.test - 1.0) > Tolerance.PARTITION_FRACTIONS:
            raise ValueError(ErrorMessage.FRACTIONS_SUM)
        return self


class FamilySelectionConfig(Frozen):
    candidate_min_total_support: SupportCount
    set_size: SupportCount


class NaturalScarcityConfig(Frozen):
    max_target_share: Fraction
    peer_min_fit: SupportCount
    own_domain_min_test: SupportCount


class DataConfig(Frozen):
    lamda_release: LamdaRelease
    expected_rows: RowCount
    expected_features: SupportCount
    malware_min_vt: VtCount
    benign_vt: VtCount
    singleton_prefix: LabelPrefix
    unknown_labels: tuple[SourceFamilyLabel, ...]
    play_era_boundary: YearMonth
    partition: PartitionConfig
    family_selection: FamilySelectionConfig
    eligibility: EligibilityRules
    natural_scarcity: NaturalScarcityConfig
    smoke_family_set_size: SupportCount

    def stable_json(self) -> SerializedConfig:
        return self.model_dump_json(exclude={ConfigField.ELIGIBILITY: {EligibilityProfile.DOSE}})

    def stable_fingerprint(self) -> Fingerprint:
        return hashlib.sha256(self.stable_json().encode()).hexdigest()


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


class FairnessGrids(Frozen):
    local_epochs: tuple[Epochs, ...]
    finetune_epochs: tuple[Epochs, ...]
    fedprox_mu: tuple[ProximalStrength, ...]


class NoveltyConfig(Frozen):
    min_active_prevalence: Fraction
    min_known_family_rows: SupportCount
    primary_descriptor: NoveltyDescriptor


class ExperimentsConfig(Frozen):
    budgets: BudgetRows
    training: TrainingConfig
    smoke_training: TrainingConfig
    operating: OperatingConfig
    novelty: NoveltyConfig
    dose_levels: tuple[SupportCount, ...]
    dose_include_all_available: IncludeAllDose
    top_family_removal_count: SupportCount
    fairness_grids: FairnessGrids
    permutation_seed_offset: NonNegativeRandomSeed
    extension_experiments: tuple[ExperimentName, ...]
    extension_b_experiments: tuple[ExperimentName, ...]
    exact_dose_levels: tuple[SupportCount, ...]
    placebo_min_malware_rows: SupportCount
    robust_trim_per_side: SupportCount
    representation_min_prevalence: Fraction
    representation_priority_families: tuple[FamilyName, ...]
    representation_contrast_families: tuple[FamilyName, ...]
    representation_separate_families: tuple[FamilyName, ...]
    representation_focus_family: FamilyName
    experiments: ExperimentSpecs

    def runs_in(self, experiment: ExperimentName, mode: ExecutionMode) -> RunsInMode:
        if mode is ExecutionMode.EXTENSION:
            return experiment in self.extension_experiments
        if mode is ExecutionMode.EXTENSION_B:
            return (
                experiment in self.extension_b_experiments
                or mode in self.experiments[experiment].modes
            )
        return mode in self.experiments[experiment].modes

    def design_fingerprint_parts(self, design: ExperimentDesign) -> tuple[SerializedConfig, ...]:
        parts = [
            part
            for part in (
                f"{design}{self.exact_dose_levels}"
                if design is ExperimentDesign.EXACT_DOSE
                else None,
                f"{design}{self.placebo_min_malware_rows}{self.robust_trim_per_side}"
                if design is ExperimentDesign.PLACEBO_ROBUST
                else None,
                f"{design}{self.representation_min_prevalence}"
                if design is ExperimentDesign.REPRESENTATION
                else None,
            )
            if part is not None
        ]
        return tuple(parts)


class GateConfig(Frozen):
    local_deficit_min_seeds: SupportCount
    local_deficit_min_gap: Fraction
    collaboration_min_gain: Fraction
    ctk_min_gain: Fraction
    ctk_min_positive_seeds: SupportCount
    pooling_majority_share: Fraction
    dose_min_peers: SupportCount
    dose_min_gain: Fraction
    dose_monotone_tolerance: Fraction
    known_family_tolerance: Fraction
    fpr_tolerance: Fraction
    poor_full_recall: Fraction
    novelty_min_abs_spearman: Fraction
    heterogeneity_min: Fraction
    mechanism_mean_gap: Fraction
    mechanism_worst_gap: Fraction


class StatisticsConfig(Frozen):
    bootstrap_resamples: ResampleCount
    cluster_bootstrap_resamples: ResampleCount
    confidence_level: Confidence
    statistics_seed: NonNegativeRandomSeed
    share_min_total_gain: Fraction
    gates: GateConfig


class Config(Frozen):
    project: ProjectConfig
    data: DataConfig
    experiments: ExperimentsConfig
    statistics: StatisticsConfig

    def training_for(self, mode: ExecutionMode) -> TrainingConfig:
        if mode is ExecutionMode.SMOKE:
            return self.experiments.smoke_training
        return self.experiments.training

    def seeds_for(self, experiment: ExperimentName, mode: ExecutionMode) -> tuple[RandomSeed, ...]:
        design = self.experiments.experiments[experiment].design
        return self.project.seeds.for_design(mode, design)

    def run_fingerprint(self, spec: ExperimentSpec, mode: ExecutionMode) -> Fingerprint:
        experiments = self.experiments
        parts = (
            self.data.stable_json(),
            self.training_for(mode).model_dump_json(),
            spec.model_dump_json(exclude_defaults=True),
            experiments.operating.model_dump_json(),
            experiments.novelty.model_dump_json(),
            experiments.fairness_grids.model_dump_json(),
            f"{experiments.budgets[spec.budget]}",
            f"{experiments.dose_levels}{experiments.dose_include_all_available}",
            f"{experiments.permutation_seed_offset}",
            *self.design_parts(spec),
        )
        return hashlib.sha256(Separator.NEWLINE.join(parts).encode()).hexdigest()

    def design_parts(self, spec: ExperimentSpec) -> tuple[SerializedConfig, ...]:
        if spec.design is ExperimentDesign.STANDARD:
            return ()
        return (
            self.data.eligibility[spec.eligibility].model_dump_json(),
            *self.experiments.design_fingerprint_parts(spec.design),
        )

    def fingerprint(self) -> Fingerprint:
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


def load_config(paths: Paths) -> Config:
    def read[Section: BaseModel](name: ConfigFile, model: type[Section]) -> Section:
        payload = yaml.safe_load(paths.config_file(name).read_text(encoding=TextEncoding.UTF8))
        return model.model_validate(payload)

    return Config(
        project=read(ConfigFile.PROJECT, ProjectConfig),
        data=read(ConfigFile.DATA, DataConfig),
        experiments=read(ConfigFile.EXPERIMENTS, ExperimentsConfig),
        statistics=read(ConfigFile.STATISTICS, StatisticsConfig),
    )
