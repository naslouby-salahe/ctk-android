from enum import Enum, IntEnum, StrEnum
from typing import Final


class DatasetName(StrEnum):
    LAMDA = "lamda"
    ANDROZOO = "androzoo"
    MCNDROID = "mcndroid"


class ClientId(StrEnum):
    PLAY_EARLY = "play-early"
    PLAY_LATE = "play-late"
    ANZHI = "anzhi"
    APPCHINA = "appchina"


class Market(StrEnum):
    GOOGLE_PLAY = "play.google.com"
    ANZHI = "anzhi"
    APPCHINA = "appchina"


class SplitRole(StrEnum):
    FIT = "fit"
    CALIBRATION = "calibration"
    TEST = "test"


class ExecutionMode(StrEnum):
    SMOKE = "smoke"
    DEVELOPMENT = "development"
    CONFIRMATORY = "confirmatory"
    EXTENSION = "extension"
    EXTENSION_B = "extension-b"


class ExperimentName(StrEnum):
    END_TO_END = "end-to-end"
    BASELINE_FAIRNESS = "baseline-fairness"
    CONTROLLED_EXPOSURE = "controlled-exposure"
    PEER_DOSE_RESPONSE = "peer-dose-response"
    NATURAL_SCARCITY = "natural-scarcity"
    FAMILY_PERMUTATION_CONTROL = "family-permutation-control"
    LARGE_FAMILY_SET_1 = "large-family-set-1"
    LARGE_FAMILY_SET_2 = "large-family-set-2"
    LARGE_FAMILY_SET_3 = "large-family-set-3"
    LARGE_FAMILY_SET_4 = "large-family-set-4"
    EXACT_EFFECTIVE_DOSE_PRIMARY = "exact-effective-dose-primary"
    EXACT_EFFECTIVE_DOSE_REPLICATION = "exact-effective-dose-replication"
    PLACEBO_ROBUST_PRIMARY = "placebo-robust-primary"
    PLACEBO_ROBUST_REPLICATION = "placebo-robust-replication"
    REPRESENTATION_R0 = "representation-r0"
    REPRESENTATION_R1 = "representation-r1"
    REPRESENTATION_R2 = "representation-r2"
    REPRESENTATION_R3 = "representation-r3"
    REPLICATION_FAMILY_SET = "replication-family-set"
    MODEL_FAMILY_REPLICATION_LINEAR = "model-family-replication-linear"
    MODEL_FAMILY_REPLICATION_TREES = "model-family-replication-trees"
    TRAINING_SUPPORT_SENSITIVITY = "training-support-sensitivity"
    PARTITION_SALT_SENSITIVITY = "partition-salt-sensitivity"
    FAMILY_SUPPORT_SENSITIVITY_LOW = "family-support-sensitivity-low"
    FAMILY_SUPPORT_SENSITIVITY_HIGH = "family-support-sensitivity-high"
    PACKAGE_ONLY_GROUPING = "package-only-grouping"


class EligibilityProfile(StrEnum):
    PRIMARY = "primary"
    LOW = "low"
    HIGH = "high"
    SMOKE = "smoke"
    DOSE = "dose"


class BudgetLevel(StrEnum):
    PRIMARY = "primary"
    LOW = "low"
    SMOKE = "smoke"


class ModelFamily(StrEnum):
    MLP = "mlp"
    LINEAR = "linear"
    GRADIENT_BOOSTED_TREES = "gradient-boosted-trees"


class Learner(StrEnum):
    LOCAL = "local"
    CENTRAL = "central"
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDAVG_FINETUNE = "fedavg-finetune"
    BLEND = "blend"


class ExposureCondition(StrEnum):
    PEER_PRESENT = "peer-present"
    FAMILY_ABSENT_EVERYWHERE = "family-absent-everywhere"
    FULL_EXPOSURE = "full-exposure"
    PLACEBO = "placebo"
    EXACT_DOSE = "exact-dose"


class ExperimentDesign(StrEnum):
    STANDARD = "standard"
    EXACT_DOSE = "exact-dose"
    PLACEBO_ROBUST = "placebo-robust"
    REPRESENTATION = "representation"


class Representation(StrEnum):
    LAMDA_STATIC = "lamda-static"
    MCNDROID_STATIC = "mcndroid-static"
    CALL_GRAPH = "call-graph"
    REPORT_JSON = "report-json"


class RepresentationGroup(StrEnum):
    PRIORITY_MACRO = "priority-macro"
    CONTRAST_MACRO = "contrast-macro"
    FAMILY = "family"


class RepresentationMeasure(StrEnum):
    FULL_EXPOSURE_RECALL = "central-full-exposure-recall"
    CTK = "fedavg-ctk"


class RepresentationOutcome(StrEnum):
    FAMILY_SPECIFIC_LIMITS = "rep1-met-rep2-met"
    HIDDAD_RESCUED = "rep1-met-hiddad-rescued"
    HIDDAD_UNRESOLVED = "rep1-met-hiddad-unresolved"
    LIMITS_STAND = "rep1-not-met"
    UNDETERMINED = "undetermined"


class HiddadStatus(StrEnum):
    RESCUED = "rescue-shown"
    NOT_RESCUED = "no-meaningful-rescue"
    UNRESOLVED = "unresolved"


class DrawStream(IntEnum):
    DOSE = 991
    PLACEBO = 992
    LARGE_FAMILY_PERMUTATION = 993


class Aggregation(IntEnum):
    TRIMMED_MEAN = 1
    COORDINATE_MEDIAN = 2


class ExposureMode(StrEnum):
    HIDE_FROM_TARGET = "hide-from-target"
    NATURAL = "natural"


class FamilySetName(StrEnum):
    PRIMARY = "primary"
    REPLICATION = "replication"
    LARGE_1 = "large-1"
    LARGE_2 = "large-2"
    LARGE_3 = "large-3"
    LARGE_4 = "large-4"


class FamilyLabelSource(StrEnum):
    OBSERVED = "observed"
    PERMUTED = "permuted"


class Grouping(StrEnum):
    COMPONENT = "component"
    PACKAGE_ONLY = "package-only"


class EvaluationPopulation(StrEnum):
    OWN_DOMAIN = "own-domain"
    FEDERATION_WIDE = "federation-wide"
    KNOWN_FAMILY = "known-family"
    BENIGN = "benign"


class EligibilityReason(StrEnum):
    ELIGIBLE = "eligible"
    EMPTY_LABEL = "empty-label"
    UNKNOWN_LABEL = "unknown-label"
    SINGLETON_LABEL = "singleton-label"
    NOT_IN_FAMILY_SET = "not-in-family-set"


class RunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED_VALIDATION = "failed-validation"
    INFEASIBLE = "infeasible"
    INCOMPLETE = "incomplete"
    STALE = "stale"


class FailureReason(StrEnum):
    SCHEMA_MISMATCH = "schema-mismatch"
    NO_ELIGIBLE_TARGETS = "no-eligible-targets"
    INSUFFICIENT_CALIBRATION = "insufficient-calibration"
    NOT_APPLICABLE_MODEL_FAMILY = "not-applicable-model-family"
    NO_COMPLETED_RUNS = "no-completed-runs"


class ValidationCheck(StrEnum):
    FEATURE_CONTRACT = "feature-contract"
    SHA_UNIQUENESS = "sha-uniqueness"
    LABEL_RULE = "label-rule"
    LINKAGE_COMPLETE = "linkage-complete"
    CLIENTS_COMPLETE = "clients-complete"
    FAMILY_SETS_DISJOINT = "family-sets-disjoint"
    PARTITION_SHA_DISJOINT = "partition-sha-disjoint"
    PARTITION_COMPONENT_DISJOINT = "partition-component-disjoint"
    PARTITION_FEATURE_DISJOINT = "partition-feature-disjoint"
    HIDDEN_FAMILY_ABSENT_FROM_TARGET = "hidden-family-absent-from-target"
    PEER_FAMILY_PRESENT = "peer-family-present"
    FAMILY_ABSENT_EVERYWHERE = "family-absent-everywhere"
    HIDDEN_ROWS_IN_TEST_ONLY = "hidden-rows-in-test-only"
    SAMPLE_SIZE_MATCHED = "sample-size-matched"
    TRAINING_EXCLUDES_TEST = "training-excludes-test"
    THRESHOLD_FROM_BENIGN_CALIBRATION = "threshold-from-benign-calibration"
    OPERATING_POINT_REALISED = "operating-point-realised"
    EXACT_DOSE_REALISED = "exact-dose-realised-at-peers"
    EXACT_DOSE_TARGET_ZERO = "exact-dose-zero-at-target"
    DOSE_ZERO_IS_ABSENT = "dose-zero-rows-equal-absent-rows"
    PLACEBO_COUNTS_MATCHED = "placebo-counts-match-hidden-family"
    PLACEBO_FAMILY_VALID = "placebo-family-unhidden-and-unique"
    PLACEBO_HIDDEN_ABSENT = "placebo-arm-hidden-family-absent"
    REPRESENTATION_ROWS_ALIGNED = "representation-rows-aligned-by-sha256"


class OperatingPointStatus(StrEnum):
    VALID = "valid"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"


class Metric(StrEnum):
    OWN_DOMAIN_UNSEEN_RECALL = "own-domain-unseen-recall"
    FEDERATION_UNSEEN_RECALL = "federation-unseen-recall"
    FAMILY_MACRO_UNSEEN_RECALL = "family-macro-unseen-recall"
    KNOWN_FAMILY_RECALL = "known-family-recall"
    REALISED_FPR = "realised-fpr"
    AUROC = "auroc"
    AUPRC = "auprc"
    WORST_CLIENT_UNSEEN_RECALL = "worst-client-unseen-recall"
    WORST_CLIENT_FNR = "worst-client-fnr"
    WORST_CLIENT_FPR = "worst-client-fpr"
    CLIENT_RECALL_DISPERSION = "client-recall-dispersion"
    FAMILY_RECALL_DISPERSION = "family-recall-dispersion"
    FPR_DISPERSION = "fpr-dispersion"
    MICRO_UNSEEN_RECALL = "micro-unseen-recall"
    CALIBRATION_AUROC = "calibration-auroc"


class ContrastFamily(StrEnum):
    PRIMARY = "primary"
    REFERENCE = "reference"
    EXPLORATORY = "exploratory"


class NoveltyDescriptor(StrEnum):
    CENTROID_DISTANCE_TO_KNOWN_MALWARE = "centroid-distance-to-known-malware"
    NEAREST_KNOWN_FAMILY_DISTANCE = "nearest-known-family-distance"
    MAX_JACCARD_TO_KNOWN_FAMILY = "max-jaccard-to-known-family"
    FRACTION_ACTIVE_FEATURES_KNOWN = "fraction-active-features-known"
    DISTANCE_TO_BENIGN_CENTROID = "distance-to-benign-centroid"


class Stage(StrEnum):
    SOURCE_AUDIT = "source-audit"
    JOINED = "joined"
    IDENTITY = "identity"
    CLIENTS = "clients"
    FAMILIES = "families"
    PARTITIONS = "partitions"
    RUNS = "runs"
    REPRESENTATION = "representation"


class ConfigFile(StrEnum):
    PROJECT = "project.yaml"
    DATA = "data.yaml"
    EXPERIMENTS = "experiments.yaml"
    STATISTICS = "statistics.yaml"


class LamdaColumn(StrEnum):
    HASH = "hash"
    LABEL = "label"
    FAMILY = "family"
    VT_COUNT = "vt_count"
    YEAR_MONTH = "year_month"


class McNdroidDirectory(StrEnum):
    STATIC = "data_feature"
    REPORT_JSON = "json_feature"
    CALL_GRAPH = "gml_feature"
    PROCESSED = "processed_data"
    BASELINE_YEAR = "init_2013"


class McNdroidSplit(StrEnum):
    TRAIN = "train"
    TEST = "test"


class McNdroidFile(StrEnum):
    SPARSE_MATRIX = "{split}_X.npz"
    SPARSE_META = "{split}_meta.npz"
    GRAPH_MATRIX = "{split}_X_y.npz"


class McNdroidKey(StrEnum):
    HASH = "hash"
    HASHES = "hashes"
    DATA = "data"
    INDICES = "indices"
    INDPTR = "indptr"
    SHAPE = "shape"
    GRAPH_X = "X"


class AndroZooColumn(StrEnum):
    SHA256 = "sha256"
    PACKAGE = "pkg_name"
    MARKETS = "markets"
    VT_DETECTION = "vt_detection"


class Artifact(StrEnum):
    CLIENT_CTK = "client-ctk-analysis.parquet"
    OVERLAP = "overlap.parquet"
    OVERLAP_MANIFEST = "overlap-manifest.json"
    LAMDA_R0_FEATURES = "features-r0.npy"
    MCNDROID_R1_FEATURES = "features-r1.npy"
    GRAPH_DATA = "graph-data.npy"
    GRAPH_INDICES = "graph-indices.npy"
    GRAPH_INDPTR = "graph-indptr.npy"
    JSON_DATA = "json-data.npy"
    JSON_INDICES = "json-indices.npy"
    JSON_INDPTR = "json-indptr.npy"
    REPRESENTATION_RUN_INDEX = "representation-run-index.parquet"
    REPRESENTATION_SEED_EFFECTS = "representation-seed-effects.parquet"
    REPRESENTATION_EFFECTS = "representation-effects.parquet"
    REPRESENTATION_LEVELS = "representation-levels.parquet"
    REPRESENTATION_VERDICTS = "representation-verdicts.parquet"
    REPRESENTATION_ELIGIBILITY = "representation-eligibility.parquet"
    LARGE_CONTROLLED_PAIRS = "large-family-controlled-pairs.parquet"
    LARGE_NATURAL_PAIRS = "large-family-natural-pairs.parquet"
    LARGE_SELECTION = "large-family-selection.parquet"
    LARGE_PROVENANCE = "large-family-provenance.json"
    LARGE_FAMILY_CTK = "large-family-ctk.parquet"
    LARGE_FAMILY_SEED_CTK = "large-family-seed-ctk.parquet"
    LARGE_FAMILY_SUMMARY = "large-family-summary.parquet"
    PLACEBO_PAIRS = "placebo-pairs.parquet"
    DOSE_RUN_INDEX = "exact-dose-run-index.parquet"
    CONTROLS_RUN_INDEX = "controls-run-index.parquet"
    DOSE_SEED_EFFECTS = "exact-dose-seed-effects.parquet"
    DOSE_EFFECTS = "exact-dose-effects.parquet"
    DOSE_FAMILY_CURVES = "exact-dose-family-curves.parquet"
    DOSE_CONSISTENCY = "exact-dose-consistency.parquet"
    DOSE_VERDICTS = "exact-dose-verdicts.parquet"
    CONTROLS_SEED_EFFECTS = "controls-seed-effects.parquet"
    CONTROLS_EFFECTS = "controls-effects.parquet"
    CONTROLS_PLACEBO_PAIRS = "controls-placebo-pairs.parquet"
    CONTROLS_VERDICTS = "controls-verdicts.parquet"
    FAMILY_CLIENT_CTK = "family-client-ctk.parquet"
    HETEROGENEITY_COMPONENTS = "ctk-heterogeneity-components.parquet"
    AGGREGATE_MASKING = "aggregate-metric-masking.parquet"
    NEGATIVE_TRANSFER = "negative-transfer-decomposition.parquet"
    CTK_VARIANCE = "ctk-variance-components.parquet"
    FAMILY_ASSOCIATIONS = "family-associations.parquet"
    ANCHORED_WORST_CLIENT = "anchored-worst-client.parquet"
    ANCHORED_CLIENT_SELECTION = "anchored-client-selection.parquet"
    ARM_TRADEOFF = "federated-arm-tradeoff.parquet"
    ROBUSTNESS_SYNTHESIS = "ctk-robustness-synthesis.parquet"
    FAMILY_PATTERNS = "family-mechanism-patterns.parquet"
    NATURAL_COMPARISON = "natural-scarcity-comparison.parquet"
    PERMUTATION_AUDIT = "permutation-control-audit.parquet"
    MECHANISM_HEADROOM = "mechanism-headroom.parquet"
    OPERATING_FIDELITY = "operating-point-fidelity.parquet"
    PROVENANCE = "provenance.json"
    AUDIT = "audit.json"
    MANIFEST = "manifest.json"
    FINGERPRINT = "fingerprint.json"
    INVENTORY = "inventory.json"
    SCHEMA = "schema.json"
    COUNTS = "counts.json"
    METADATA = "metadata.parquet"
    HASH_LINKAGE = "hash-linkage.parquet"
    UNMATCHED = "unmatched.parquet"
    DATASET = "dataset.parquet"
    ASSIGNMENTS = "assignments.parquet"
    SUPPORT = "support.parquet"
    COMPONENTS = "components.parquet"
    FEATURE_IDENTITIES = "feature-identities.parquet"
    PACKAGE_IDENTITIES = "package-identities.parquet"
    COMPONENT_SUMMARY = "component-summary.parquet"
    ELIGIBILITY = "eligibility.parquet"
    FEATURES = "features.npy"
    CONTROLLED_PAIRS = "controlled-pairs.parquet"
    NATURAL_PAIRS = "natural-pairs.parquet"
    RUN_MATRIX = "run-matrix.parquet"
    FAMILY_ASSIGNMENTS = "family-assignments.parquet"
    PLAN = "plan.json"
    STATUS = "status.json"
    VALIDATION = "validation.json"
    EXPOSURE = "exposure.parquet"
    THRESHOLDS = "thresholds.parquet"
    NOVELTY = "novelty.parquet"
    SUMMARY = "summary.parquet"
    CLIENT_METRICS = "clients.parquet"
    FAMILY_METRICS = "families.parquet"
    OPERATING_POINTS = "operating-points.parquet"
    DISCRIMINATION = "discrimination.parquet"
    RUN_INDEX = "run-index.parquet"
    ARM_METRICS = "arm-metrics.parquet"
    COLLABORATION_DECOMPOSITION = "collaboration-decomposition.parquet"
    FAMILY_RESCUE = "family-rescue.parquet"
    PEER_DOSE_RESPONSE = "peer-dose-response.parquet"
    FEATURE_NOVELTY = "feature-novelty.parquet"
    ROBUSTNESS = "robustness.parquet"
    PAIRED_EFFECTS = "paired-effects.parquet"
    CLUSTER_BOOTSTRAP = "cluster-bootstrap.parquet"
    CLAIM_GATES = "claim-gates.parquet"
    FAIRNESS_SELECTION = "fairness-selection.parquet"
    LARGE_FAMILY_STABILITY = "large-family-eligibility-stability.parquet"
    LARGE_FAMILY_STABILITY_SEEDS = "large-family-eligibility-stability-seeds.parquet"
    LARGE_FAMILY_STABILITY_SUMMARY = "large-family-eligibility-stability-summary.parquet"
    DIAGNOSTICS_RUN_INDEX = "diagnostics-run-index.parquet"
    DIAGNOSTIC_REP_TARGETS = "diagnostic-representation-operating-targets.parquet"
    DIAGNOSTIC_REP_HEALTH = "diagnostic-representation-score-health.parquet"
    DIAGNOSTIC_REP_EFFECTS = "diagnostic-representation-equal-fpr-effects.parquet"
    DIAGNOSTIC_LFAM_INFLUENCE = "diagnostic-large-family-influence.parquet"
    DIAGNOSTIC_LFAM_STABILITY = "diagnostic-large-family-stability.parquet"
    DIAGNOSTIC_DOSE_CURVE = "diagnostic-dose-ctk-by-dose.parquet"
    DIAGNOSTIC_DOSE_INCREMENTS = "diagnostic-dose-increments.parquet"
    DIAGNOSTIC_DOSE_FAMILY_CURVES = "diagnostic-dose-family-curves.parquet"
    DIAGNOSTIC_DOSE_FAMILY_SUMMARY = "diagnostic-dose-family-summary.parquet"
    DIAGNOSTIC_DOSE_ASSOCIATIONS = "diagnostic-dose-family-associations.parquet"
    DIAGNOSTIC_DOSE_CLIENT_CURVES = "diagnostic-dose-client-curves.parquet"
    DIAGNOSTIC_DOSE_MODEL_FITS = "diagnostic-dose-model-fits.parquet"
    DIAGNOSTIC_DOSE_HETEROGENEITY = "diagnostic-dose-heterogeneity.parquet"
    DIAGNOSTIC_CTRL_STRATA = "diagnostic-controls-strata.parquet"
    DIAGNOSTIC_CTRL_CLIENTS = "diagnostic-controls-clients.parquet"
    DIAGNOSTIC_CTRL_REALLOCATION = "diagnostic-controls-reallocation.parquet"
    DIAGNOSTIC_CTRL_SLOPES = "diagnostic-controls-reallocation-slope.parquet"
    DIAGNOSTIC_CTRL_ASSOCIATIONS = "diagnostic-controls-associations.parquet"
    DIAGNOSTIC_CTRL_PLACEBO_PAIRS = "diagnostic-controls-placebo-pairs.parquet"
    DIAGNOSTIC_CTRL_FAMILIES = "diagnostic-controls-families.parquet"
    DIAGNOSTIC_CTRL_SUPPORT_LEVELS = "diagnostic-controls-support-levels.parquet"
    DIAGNOSTIC_CTRL_SUPPORT = "diagnostic-controls-support.parquet"
    DIAGNOSTIC_SYNTH_CELLS = "diagnostic-synthesis-cells.parquet"
    DIAGNOSTIC_SYNTH_TAXONOMY = "diagnostic-synthesis-family-taxonomy.parquet"
    DIAGNOSTIC_SYNTH_FAMILY_CTK = "diagnostic-synthesis-family-ctk.parquet"
    DIAGNOSTIC_SYNTH_LARGE_CTK = "diagnostic-synthesis-large-family-ctk.parquet"
    DIAGNOSTIC_SYNTH_LARGE_TAXONOMY = "diagnostic-synthesis-large-family-taxonomy.parquet"
    DIAGNOSTIC_SYNTH_RANK = "diagnostic-synthesis-rank-concordance.parquet"
    DIAGNOSTIC_SYNTH_LARGE_ASSOCIATIONS = "diagnostic-synthesis-large-family-associations.parquet"


class Device(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"


class Column(StrEnum):
    SHA256 = "sha256"
    ROW = "row"
    ROW_POSITION = "row_position"
    SOURCE_ROW = "source_row"
    REPRESENTATION = "representation"
    GROUP = "group"
    BASELINE = "baseline"
    PACKAGE = "package"
    PACKAGE_ID = "package_id"
    MARKETS = "markets"
    MARKET_COUNT = "market_count"
    LABEL = "label"
    FAMILY = "family"
    VT_COUNT = "vt_count"
    YEAR_MONTH = "year_month"
    CLIENT = "client"
    FEATURE_ID = "feature_id"
    COMPONENT = "component"
    ROLE = "role"
    ROWS = "rows"
    MALWARE_ROWS = "malware_rows"
    BENIGN_ROWS = "benign_rows"
    PACKAGES = "packages"
    SEED = "seed"
    SALT = "salt"
    GROUPING = "grouping"
    FAMILY_SET = "family_set"
    REASON = "reason"
    ELIGIBLE = "eligible"
    FIT_ROWS = "fit_rows"
    TARGET_FIT_ROWS = "target_fit_rows"
    PEER_FIT_ROWS = "peer_fit_rows"
    TARGET_TEST_ROWS = "target_test_rows"
    FEDERATION_TEST_ROWS = "federation_test_rows"
    TARGET_SHARE = "target_share"
    TOTAL_FIT_ROWS = "total_fit_rows"
    EXPERIMENT = "experiment"
    MODE = "mode"
    MODEL_FAMILY = "model_family"
    LEARNER = "learner"
    CONDITION = "condition"
    DOSE = "dose"
    ALPHA = "alpha"
    METRIC = "metric"
    VALUE = "value"
    STATUS = "status"
    POPULATION = "population"
    HITS = "hits"
    TRIALS = "trials"
    UNIQUE_HITS = "unique_hits"
    UNIQUE_TRIALS = "unique_trials"
    SENSITIVITY = "sensitivity"
    OPERATING_STATUS = "operating_status"
    SCORE = "score"
    TARGET_CLIENT = "target_client"
    NOVELTY = "novelty"
    RECALL = "recall"
    AUROC = "auroc"
    AUPRC = "auprc"
    LOW = "low"
    HIGH = "high"
    LINKED_VT = "linked_vt_detection"
    PARAMETER = "parameter"
    TUNING_VALUE = "tuning_value"
    SPLIT = "split"
    SELECTED = "selected"
    CALIBRATION_AUROC = "calibration_auroc"
    SCOPES_PASSED = "scopes_passed"
    SCOPES_TOTAL = "scopes_total"
    MEDIAN_DIFFERENCE = "median_difference"
    CI_HIGH = "ci_high"
    RECALL_STD = "recall_std"
    CLAIM = "claim"
    CLAIM_STATUS = "claim_status"
    CLASSIFICATION = "classification"
    EFFECT_SIZE = "effect_size"
    THRESHOLD = "threshold"
    DESCRIPTOR = "descriptor"
    EFFECTIVE_DOSE = "effective_dose"
    CTK_GAIN = "ctk_gain"
    SEED_COUNT = "seed_count"
    ELIGIBLE_PAIRS = "eligible_pairs"
    OWN_DOMAIN_PAIRS = "own_domain_pairs"
    RANK = "rank"
    CTK_SD = "ctk_sd"
    MIN_TRIALS = "min_trials"
    MEETS_THRESHOLD = "meets_threshold"
    CI_LOW = "ci_low"
    CONTRAST_FAMILY = "contrast_family"
    MEAN_DIFFERENCE = "mean_difference"
    POSITIVE_SEEDS = "positive_seeds"
    P_HOLM = "p_holm"
    P_VALUE = "p_value"
    ABSENT_RECALL = "absent_recall"
    ESTIMAND = "estimand"
    FULL_RECALL = "full_recall"
    LOCAL_RECALL = "local_recall"
    PEER_RECALL = "peer_recall"
    DOSE_LEVEL = "dose_level"
    LEVEL_EFFECTIVE_DOSE = "level_effective_dose"
    MEETS_DOSE_CRITERION = "meets_dose_criterion"
    MICRO_POOLED_CTK_GAIN = "micro_pooled_ctk_gain"
    EVIDENCE_CLASS = "evidence_class"
    KNOWN_LOCAL_RECALL = "known_local_recall"
    KNOWN_PEER_RECALL = "known_peer_recall"
    BENIGN_FPR = "benign_fpr"
    POOLING_CI_LOW = "pooling_ci_low"
    POOLING_CI_HIGH = "pooling_ci_high"
    CTK_CI_LOW = "ctk_ci_low"
    CTK_CI_HIGH = "ctk_ci_high"
    KNOWN_FAMILY_CHANGE = "known_family_change"
    KNOWN_FAMILY_CHANGE_CI_LOW = "known_family_change_ci_low"
    KNOWN_FAMILY_CHANGE_CI_HIGH = "known_family_change_ci_high"
    SCOPE_ORDER = "scope_order"
    COMPARISON = "comparison"
    MEASURE = "measure"
    SCOPE = "scope"
    SEEDS_SELECTED = "seeds_selected"
    MEAN_LOCAL_RECALL = "mean_local_recall"
    POOLING_GAIN = "pooling_gain"
    TOTAL_GAIN = "total_gain"
    FAMILIES = "families"
    CLIENTS = "clients"
    MEAN_FPR = "mean_realised_fpr"
    WORST_FPR = "mean_worst_client_fpr"
    FPR_DEVIATION = "mean_fpr_deviation_from_target"
    VALID_RUNS = "valid_operating_runs"
    RUNS = "runs"
    LINEAR_FULL_RECALL = "linear_full_recall"
    TREES_FULL_RECALL = "trees_full_recall"
    AGGREGATION = "aggregation"
    SHARE = "share"
    OBSERVATIONS = "observations"
    OBSERVATIONS_MET = "observations_meeting_criterion"
    MINUEND = "minuend"
    SUBTRAHEND = "subtrahend"
    DIFFERENCE = "difference"
    REPAIR = "repair"
    NEW_CAPABILITY = "new_capability"
    CTK_HARM = "ctk_harm"
    CONTRAST = "contrast"
    LEVEL = "level"
    MEAN_CTK = "mean_ctk"
    TARGET_ROWS = "target_rows"
    PEER_ROWS = "peer_rows"
    TRAIN_ROWS = "train_rows"
    VOLUME_IDENTICAL = "volume_identical"
    ELIGIBLE_SEEDS = "eligible_seeds"
    ELIGIBLE_FRACTION = "eligible_seed_fraction"
    STABLE = "eligible_in_every_seed"
    MEASURED_SEEDS = "measured_seeds"
    ELIGIBLE_TEST_ROWS = "eligible_target_test_rows"
    MIN_ELIGIBLE_PAIRS = "min_eligible_pairs"
    MEAN_ELIGIBLE_PAIRS = "mean_eligible_pairs"
    MAX_ELIGIBLE_PAIRS = "max_eligible_pairs"
    MIN_ELIGIBLE_TEST_ROWS = "min_eligible_target_test_rows"
    MEAN_ELIGIBLE_TEST_ROWS = "mean_eligible_target_test_rows"


class LogEvent(StrEnum):
    COMMAND_STARTED = "command-started"
    COMMAND_FINISHED = "command-finished"
    COMMAND_FAILED = "command-failed"
    DOCTOR_CHECKED = "doctor-checked"
    SOURCE_FINGERPRINTED = "source-fingerprinted"
    LAMDA_LOADED = "lamda-loaded"
    ANDROZOO_SCANNED = "androzoo-scanned"
    LINKAGE_AUDITED = "linkage-audited"
    CLIENTS_ASSIGNED = "clients-assigned"
    IDENTITIES_BUILT = "identities-built"
    FAMILIES_SELECTED = "families-selected"
    PARTITION_BUILT = "partition-built"
    REPRESENTATION_BUILT = "representation-built"
    STAGE_REUSED = "stage-reused"
    STAGE_BUILT = "stage-built"
    STAGE_FAILED = "stage-failed"
    PLAN_WRITTEN = "plan-written"
    RUN_PLANNED = "run-planned"
    RUN_PLANNED_INFEASIBLE = "run-planned-infeasible"
    RUN_STARTED = "run-started"
    RUN_REUSED = "run-reused"
    RUN_INFEASIBLE = "run-infeasible"
    EXPOSURE_SELECTED = "exposure-selected"
    ARM_TRAINED = "arm-trained"
    FEDERATED_ROUND = "federated-round"
    EVALUATION_FINISHED = "evaluation-finished"
    VALIDATION_PASSED = "validation-passed"
    VALIDATION_FAILED = "validation-failed"
    OPERATING_POINT_UNRESOLVED = "operating-point-unresolved"
    RUN_FINISHED = "run-finished"
    STATUS_SUMMARIZED = "status-summarized"
    EVIDENCE_COLLECTED = "evidence-collected"
    RUN_STALE = "run-stale"
    ANALYSIS_STAGE_FINISHED = "analysis-stage-finished"
    CLAIM_EVALUATED = "claim-evaluated"
    HYPERPARAMETER_SELECTED = "hyperparameter-selected"
    FREEZE_DRIFT = "freeze-drift"
    FAIRNESS_UNAVAILABLE = "fairness-unavailable"
    TABLES_WRITTEN = "tables-written"
    FIGURES_WRITTEN = "figures-written"
    REPORT_WRITTEN = "report-written"
    PROMOTION_DECIDED = "promotion-decided"


class LogField(StrEnum):
    COMMAND = "command"
    STAGE = "stage"
    DATASET = "dataset"
    CLIENT = "client"
    FAMILY = "family"
    SEED = "seed"
    SALT = "salt"
    EXPERIMENT = "experiment"
    MODE = "mode"
    ARM = "arm"
    LEARNER = "learner"
    CONDITION = "condition"
    DOSE = "dose"
    CONFIG_FINGERPRINT = "config_fingerprint"
    DEVICE = "device"
    FAMILY_SET = "family_set"
    ROWS = "rows"
    FILES = "files"
    BYTES = "bytes"
    COUNT = "count"
    REUSED = "reused"
    SECONDS = "seconds"
    PATH = "path"
    STATUS = "status"
    REASON = "reason"
    CHECK = "check"
    DETAIL = "detail"
    PASSED = "passed"
    ATTEMPT = "attempt"
    TRAIN_ROWS = "train_rows"
    ROUND = "round"
    TARGETS = "targets"
    ELIGIBLE = "eligible"
    FEATURES = "features"
    COMPONENTS = "components"
    LARGEST = "largest"
    RUNS = "runs"
    INFEASIBLE = "infeasible"
    COMPLETED = "completed"
    CLAIM = "claim"
    BLOCKS = "blocks"
    UNMATCHED = "unmatched"
    ALPHA = "alpha"
    FAILED = "failed"
    SCOPES_PASSED = "scopes_passed"
    SCOPES_TOTAL = "scopes_total"
    BUDGET = "budget"
    ARMS = "arms"
    ERROR = "error"
    THROUGHPUT = "throughput"
    PARAMETER = "parameter"
    VALUE = "value"
    CALIBRATION_AUROC = "calibration_auroc"


class CliCommand(StrEnum):
    DOCTOR = "doctor"
    PREPROCESS = "preprocess"
    PLAN = "plan"
    SMOKE = "smoke"
    RUN = "run"
    STATUS = "status"
    REPORT = "report"
    POSTHOC = "posthoc"
    LARGE_FAMILY = "large-family"
    DOSE_EXTENSION = "dose-extension"
    CONTROLS_EXTENSION = "controls-extension"
    REPRESENTATION_PREPROCESS = "representation-preprocess"
    REPRESENTATION_EXTENSION = "representation-extension"
    DIAGNOSTICS = "diagnostics"


class DoctorCheck(StrEnum):
    PYTHON_VERSION = "python-version"
    CONFIG_VALID = "config-valid"
    RAW_LAMDA = "raw-lamda"
    RAW_ANDROZOO = "raw-androzoo"
    COMPUTE_DEVICE = "compute-device"
    GIT_REVISION = "git-revision"


class WorkspaceDirectory(StrEnum):
    DATA = "data"
    RAW = "raw"
    CONFIGS = "configs"
    DOCS = "docs"
    OUTPUTS = "outputs"
    LOGS = "logs"
    PREPROCESSING = "preprocessing"
    LINKAGE = "linkage"
    CACHE = "cache"
    PLANS = "plans"
    ANALYSIS = "analysis"
    STATISTICS = "statistics"
    REPORT = "report"
    RESULTS = "results"
    SOURCE = "src"
    TABLES = "tables"
    FIGURES = "figures"
    METRICS = "metrics"
    SCORES = "scores"
    MODELS = "models"


class SourceFile(StrEnum):
    PROJECT_MARKER = "pyproject.toml"
    LAMDA_FEATURE_MAPPING = "feature_mapping.csv"
    LAMDA_PARQUET_GLOB = "*/*.parquet"
    ANDROZOO_ARCHIVE = "latest.csv.gz"
    ROADMAP = "Roadmap.md"


class FileSuffix(StrEnum):
    PARQUET = ".parquet"
    CSV = ".csv"
    JSONL = ".jsonl"
    PDF = ".pdf"
    PNG = ".png"
    TORCH = ".pt"
    FAMILY_SET = "-family-set.json"


class NameFragment(StrEnum):
    SEED = "seed-"
    SALT = "-salt-"
    SEPARATOR = "-"
    ARM_SEPARATOR = "__"
    DOSE = "dose-"
    ALL_DOSE = "all"


class LamdaRelease(StrEnum):
    BASELINE = "Baseline"
    VARIANCE_0_0001 = "var_thresh_0.0001"
    VARIANCE_0_01 = "var_thresh_0.01"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SourceFamilyLabel(StrEnum):
    EMPTY = ""
    UNKNOWN = "unknown"
    BENIGN = "benign"


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class TrackedPackage(StrEnum):
    NUMPY = "numpy"
    POLARS = "polars"
    SCIKIT_LEARN = "scikit-learn"


class ByteBlock(IntEnum):
    ANDROZOO_SCAN = 1 << 26
    HASH_CHUNK = 1 << 22


class RowBlock(IntEnum):
    SCORING = 1 << 13
    STANDARDISATION = 1 << 14


class Display(IntEnum):
    FINGERPRINT_PREFIX = 12


class PythonRequirement(IntEnum):
    MAJOR = 3
    MINOR = 12


class Tolerance(float, Enum):
    PARTITION_FRACTIONS = 1e-9
    THROUGHPUT_FLOOR = 1e-9
    VARIANCE_FLOOR = 1e-10
    WARM_START_FLOOR = 0.01
    STANDARD_DEVIATION_FLOOR = 1e-6
    TARGET_POWER = 0.8


class Separator(StrEnum):
    NEWLINE = "\n"
    COLON = ":"
    COLON_SPACE = ": "
    COMMA = ","
    PIPE = "|"
    EMPTY = ""
    ARROW = "->"
    SPACE = " "


class FormatSpec(StrEnum):
    THREE_DIGITS = "03d"


class TextEncoding(StrEnum):
    UTF8 = "utf-8"


class GitArgument(StrEnum):
    GIT = "git"
    DIRECTORY = "-C"
    REV_PARSE = "rev-parse"
    HEAD = "HEAD"
    REV_LIST = "rev-list"
    LATEST = "-1"
    BEFORE = "--before={moment}"
    STATUS = "status"
    PORCELAIN = "--porcelain"
    PATHSPEC = "--"


class ErrorMessage(StrEnum):
    NO_PROJECT_ROOT = "no {marker} above {start}"
    NO_LAMDA_FILES = "no LAMDA parquet files found"
    NO_MCNDROID_FILES = "no McNdroid {kind} files found under {path}"
    REPRESENTATION_MISSING = (
        "representation namespace missing at {path}; run representation-preprocess first"
    )
    ALIGNMENT_MISSING = "{count} overlap rows are missing from the {kind} shards"
    OVERLAP_EMPTY = "no LAMDA row is present in all three McNdroid representations"
    UNKNOWN_REPRESENTATION = "{representation} has no feature loader"
    FEATURE_COLUMNS_DIFFER = "{name}: feature columns differ"
    STAGE_VALIDATION = "{stage}: {check} {detail}"
    PLAN_MISSING = "no plan for mode {mode}; run plan first"
    RUN_NOT_PLANNED = "run {experiment} seed {seed} is not in the {mode} plan"
    EXPERIMENT_MODE = "{experiment} is not defined for {mode}"
    NEEDS_FEDERATED = "{learner} needs a federated model"
    NEEDS_LOCAL = "blend needs local models"
    STALE_PREPROCESSING = "unreadable provenance at {path}; run preprocess again"
    NO_EVIDENCE = "no completed {mode} runs to analyse; run the planned experiments first"
    PARAMETRIC_ONLY = "federated averaging needs parametric models"
    FINETUNE_NETWORK = "fine-tuning needs a network"
    CLASS_COUNTS = "training rows have class counts {counts}"
    EMPTY_SCORER = "scorer has neither network nor trees"
    PARTITION_ATTEMPTS = "partition attempts must be positive"
    FRACTIONS_SUM = "partition fractions must sum to one"
    SEED_ROLES = "seed roles must be disjoint"
    SMOKE_INCOMPLETE = "smoke workflow incomplete: {detail}"
    SEED_OUTSIDE_PLAN = "seed {seed} is not a {mode} seed in the configuration"
    NO_PLACEBO = "no placebo family fits {family}: need {need} peer rows"
    EXTENSION_MODE = "the extension analysis needs mode {mode}"


class DetailMessage(StrEnum):
    FEATURE_CONTRACT = "rows={rows} features={features} non_binary_cells_binarized={binarized}"
    SHA_UNIQUE = "unique={unique} of {total}"
    LABEL_RULE = "malware>={malware_min}={malware_ok} benign=={benign_vt}={benign_ok}"
    LINKAGE = "matched={matched} unmatched={unmatched} unique_links={unique} vt_agrees={agrees}"
    CROSSING = "crossing={crossing}"
    GROUP_CROSSING = "grouping={grouping} crossing={crossing}"
    FEATURE_CROSSING = "crossing={crossing} enforced={enforced}"
    CLIENTS_PRESENT = "clients={clients}"
    FAMILY_SETS = "disjoint family sets, overlap={overlap}"
    HIDDEN_ZERO = "target training exposure to hidden families is zero"
    PEER_SUPPORT = "peer support >= {minimum} in fit pool and present in training"
    ABSENT_EVERYWHERE = "target families absent from every client in the absent-everywhere arms"
    SIZES = "per-client training sizes {sizes}"
    FIT_ONLY = "all training rows belong to the fit role"
    CALIBRATION_ROWS = (
        "calibration rows are own-client rows; thresholds use only their benign subset"
    )
    HIDDEN_TEST_ONLY = "evaluated hidden-family rows belong to the test partition"
    OPERATING_DEVIATION = "max |realised FPR - alpha| = {deviation}"
    FILE_COUNT = "{count} files, {missing} missing"
    NOT_A_CHECKOUT = "not a git checkout"
    CONFIG_FINGERPRINT = "configuration fingerprint {prefix}"
    DEVICE = "available {available}, configured {configured}"
    DOSE_REALISED = "peer rows of every hidden family equal the requested dose {dose}"
    DOSE_TARGET_ZERO = "target holds no rows of its hidden family at dose {dose}"
    DOSE_ZERO_IS_ABSENT = "dose 0 rows are identical to the family-absent-everywhere rows"
    PLACEBO_COUNTS = "placebo rows per peer equal the hidden family rows under peer-present"
    PLACEBO_VALID = "placebo families are not hidden in this run and each is used once"
    PLACEBO_HIDDEN_ZERO = "no client trains on a hidden family in the placebo arm"
    REPRESENTATION_ALIGNED = (
        "{representations} matrices have {rows} rows in overlap order; sha256 unique={unique}"
    )


class CliMessage(StrEnum):
    DOCTOR_LINE = "{verdict} {check}: {detail}"
    STAGE_LINE = "{stage} reused={reused} {directory}"
    PLANNED = "{count} runs planned for {mode}"
    SMOKE_LINE = "smoke {status} {directory}"
    RUN_LINE = "{experiment} seed={seed} {status}"
    FAILURE_LINE = "{reason}: {error}"
    PROMOTION_LINE = "promotion {state} {blocks}"


class LibraryOption:
    """Literal-typed option values that third-party APIs accept only as string literals."""

    JOIN_LEFT: Final = "left"
    JOIN_INNER: Final = "inner"
    SPARSE_CSR: Final = "csr"
    LBFGSB: Final = "L-BFGS-B"
    JOIN_CROSS: Final = "cross"
    SORT_STABLE: Final = "stable"
    RANK_DENSE: Final = "dense"
    QUANTILE_HIGHER: Final = "higher"
    READ_BINARY: Final = "rb"
    DUMP_JSON: Final = "json"
    FORBID_EXTRA: Final = "forbid"
    VALIDATE_AFTER: Final = "after"
    MMAP_READ: Final = "r"
    BCA: Final = "BCa"
    BBOX_TIGHT: Final = "tight"
    LINE_DASHED: Final = "--"
    MARKER_CIRCLE: Final = "o"
    MARKER_SQUARE: Final = "s"
    NEUTRAL_COLOR: Final = "grey"
    AXIS_X: Final = "x"
    AXIS_Y: Final = "y"
    UPPER_CENTER: Final = "upper center"
    THRESHOLD_COLOR: Final = "black"
    SCALE_SYMLOG: Final = "symlog"
    ASPECT_AUTO: Final = "auto"
    TIMESTAMP_ISO: Final = "iso"
    WILCOXON_EXACT: Final = "exact"
    WILCOXON_GREATER: Final = "greater"
    WILCOXON_TWO_SIDED: Final = "two-sided"
    AGGREGATE_MEAN: Final = "mean"
    CONCAT_DIAGONAL_RELAXED: Final = "diagonal_relaxed"
    WARNINGS_IGNORE: Final = "ignore"
    ORDER_LEFT: Final = "left"


class Pattern(StrEnum):
    SHA256 = r"^[0-9a-f]{64}$"
    YEAR_MONTH = r"^\d{4}-\d{2}$"
    FEATURE_COLUMN = r"^feat_\d+$"


class FeatureNaming(StrEnum):
    PREFIX = "feat_"


class MarketCount(IntEnum):
    SINGLE = 1


class ConfigField(StrEnum):
    ELIGIBILITY = "eligibility"


class SignTail(StrEnum):
    GREATER = "greater"
    TWO_SIDED = "two-sided"


class DoseAnchor(IntEnum):
    ZERO = 0
    LOW = 50
    MID = 100
    HIGH = 200


class ConsistencyMeasure(StrEnum):
    REALISED_DOSE = "realised-effective-dose-equals-level"
    TARGET_ZERO = "target-holds-no-hidden-family-rows"
    VOLUME = "training-volume-identical-across-levels"


class ExtensionScope(StrEnum):
    POOLED = "pooled-family-sets"
    PRIMARY_SET = "primary-set"
    REPLICATION_SET = "replication-set"


class ExtensionHypothesis(StrEnum):
    DOSE_ONSET = "H-DOSE-1"
    DOSE_SATURATION = "H-DOSE-2"
    PLACEBO = "H-CTRL-1"
    ROBUST_AGGREGATION = "H-CTRL-2"
    REPRESENTATION_RESCUE = "H-REP-1"
    REPRESENTATION_HIDDAD = "H-REP-2"
    REPRESENTATION_OUTCOME = "interpretation"
    DESCRIPTIVE = "descriptive"


class ExtensionContrast(StrEnum):
    DOSE_CTK = "ctk-at-dose"
    NATURAL_CTK = "ctk-natural-peer-present"
    INCREMENT_50_100 = "increment-50-to-100"
    INCREMENT_100_200 = "increment-100-to-200"
    ZERO_VERSUS_ABSENT = "dose-zero-minus-absent"
    PLACEBO_EFFECT = "placebo-effect"
    CTK_MEAN = "ctk-mean-aggregation"
    CTK_TRIMMED = "ctk-trimmed-mean-aggregation"
    CTK_MEDIAN = "ctk-median-aggregation"
    CTK_MINUS_PLACEBO = "ctk-minus-placebo-effect"
    TRIMMED_MINUS_MEAN = "ctk-trimmed-minus-ctk-mean"
    MEDIAN_MINUS_MEAN = "ctk-median-minus-ctk-mean"


class Estimand(StrEnum):
    TOTAL_GAIN = "total-gain"
    POOLING_GAIN = "pooling-gain"
    CTK_GAIN = "ctk-gain"
    CTK_SHARE = "ctk-share"
    ORACLE_GAP_RECOVERY = "oracle-gap-recovery"
    LOCAL_DEFICIT = "local-deficit"
    POOLING_SHARE = "pooling-share"


class StatisticsLimit(IntEnum):
    BCA_SEEDS = 3
    ASSOCIATION_FAMILIES = 4
    CLUSTER_CHUNK = 100
    DOSE_CRITERIA = 3
    FISHER_OFFSET = 3


class ClaimName(StrEnum):
    LOCAL_DEFICIT = "local-deficit"
    COLLABORATION_BENEFIT = "collaboration-benefit"
    COMPLEMENTARY_KNOWLEDGE = "complementary-knowledge"
    GENERIC_POOLING_MAJORITY = "generic-pooling-majority"
    DOSE_RESPONSE = "dose-response"
    OWN_DOMAIN_BENEFIT = "own-domain-benefit"
    WORST_CLIENT_BENEFIT = "worst-client-benefit"
    KNOWN_FAMILY_SAFETY = "known-family-safety"
    FAMILY_DEPENDENCE = "family-dependence"
    REPRESENTATION_LIMITED_FAMILY = "representation-limited-family"
    FEATURE_NOVELTY_EXPLANATION = "feature-novelty-explanation"
    NEW_MECHANISM_TRIGGER = "new-mechanism-trigger"


class ClaimStatus(StrEnum):
    PROMOTED = "promoted"
    NARROWED = "narrowed"
    INSUFFICIENT_EVIDENCE = "insufficient-evidence"
    REJECTED = "rejected"


class AllowedWording(StrEnum):
    PROMOTED = "supported in every evaluated scope"
    STRONGEST_ARM_ONLY = (
        "supported for the strongest federated arm only; report every arm's known-family change"
    )
    NARROWED = "supported only in the scopes that passed; state the restriction"
    INSUFFICIENT_EVIDENCE = "not resolved by the confirmatory evidence; report descriptively"
    REJECTED = "not supported; report the measured components without the claim"


class EvidenceClass(StrEnum):
    ORIGINAL_CONFIRMATORY = "A-original-confirmatory"
    CONFIRMATORY_SENSITIVITY = "B-confirmatory-sensitivity"
    POST_CONFIRMATORY = "C-post-confirmatory-evidence-preserving"
    CONFIRMATORY_SEEDS = "A-B-C-confirmatory-seeds-row-labelled"
    PROSPECTIVE_EXTENSION = "D-prospective-extension"
    # Post-hoc diagnostics that read class-D extension runs: descriptive, no gate, no claim.
    POST_HOC_DIAGNOSTIC = "D-post-hoc-diagnostic"


class VarianceSource(StrEnum):
    FAMILY = "family"
    SEED = "seed"
    RESIDUAL = "family-by-seed-residual"


class VarianceComponent(StrEnum):
    FAMILY = "family"
    CLIENT = "client"
    FAMILY_BY_CLIENT = "family-by-client"
    SEED = "seed"
    RESIDUAL = "residual-family-client-seed"


class TransferScope(StrEnum):
    CELL = "client-family-cell"
    FAMILY = "family"
    CLIENT = "client"
    OVERALL = "overall"


class MaskingContrast(StrEnum):
    PEER_VERSUS_LOCAL = "peer-versus-local"
    PEER_VERSUS_FAMILY_ABSENT = "peer-versus-family-absent"


class IntervalVerdict(StrEnum):
    POSITIVE = "interval-above-reference"
    INCONCLUSIVE = "interval-includes-reference"
    NEGATIVE = "interval-below-reference"


class FamilyPredictor(StrEnum):
    LOCAL_RECALL = "local-recall"
    POOLING_GAIN = "pooling-gain"


class FamilyOutcomeMeasure(StrEnum):
    CTK_GAIN = "ctk-gain"
    TOTAL_GAIN = "total-gain"


class LargeFamilyMeasure(StrEnum):
    FAMILIES_PLANNED = "families-planned"
    FAMILIES_DEFINED = "families-with-defined-ctk"
    FAMILIES_WITH_DESCRIPTOR = "families-with-descriptor"
    MEAN_SUPPORT = "mean-federation-test-support"
    MIN_SUPPORT = "min-federation-test-support"
    RHO = "spearman-rho"
    RHO_CI_LOW = "spearman-rho-ci-low"
    RHO_CI_HIGH = "spearman-rho-ci-high"
    RHO_CI_WIDTH = "spearman-rho-ci-width"
    RHO_P_VALUE = "spearman-p-value"
    RHO_PERMUTATION_P = "spearman-permutation-p-value"
    SEEDS_WITH_RHO = "seed-level-rho-seeds"
    SEED_RHO_MIN = "seed-level-rho-min"
    SEED_RHO_MEDIAN = "seed-level-rho-median"
    SEED_RHO_MAX = "seed-level-rho-max"
    SEED_RHO_POSITIVE = "seed-level-rho-positive-seeds"
    CTK_MEAN = "family-ctk-mean"
    CTK_SD = "family-ctk-sd"
    CTK_NOISE_SD = "family-ctk-within-family-seed-sd"
    CTK_SIGNAL_SD = "family-ctk-noise-corrected-signal-sd"
    CTK_RELIABILITY = "family-ctk-reliability"
    FAMILIES_ABOVE_THRESHOLD = "families-with-abs-ctk-at-least-threshold"
    DESCRIPTOR_SD = "descriptor-sd"
    DESCRIPTOR_IQR = "descriptor-iqr"
    DESCRIPTOR_DISTINCT = "descriptor-distinct-values"
    EXPECTED_CI_WIDTH = "expected-rho-ci-width"
    MIN_DETECTABLE_RHO = "min-detectable-abs-rho"
    STABILITY_FAMILIES = "sensitivity-frozen-families-checked"
    STABILITY_SEEDS = "sensitivity-fresh-seeds-checked"
    STABLE_FAMILIES = "sensitivity-families-eligible-in-every-seed"
    MEAN_ELIGIBLE_FRACTION = "sensitivity-mean-eligible-seed-fraction"
    MIN_ELIGIBLE_FRACTION = "sensitivity-min-eligible-seed-fraction"
    STABLE_RHO = "sensitivity-stable-families-spearman-rho"
    STABLE_RHO_CI_LOW = "sensitivity-stable-families-spearman-rho-ci-low"
    STABLE_RHO_CI_HIGH = "sensitivity-stable-families-spearman-rho-ci-high"
    STABLE_RHO_CI_WIDTH = "sensitivity-stable-families-spearman-rho-ci-width"
    STABLE_RHO_P_VALUE = "sensitivity-stable-families-spearman-p-value"


class PrecisionRho(float, Enum):
    NULL = 0.0
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7


class IntervalStatus(StrEnum):
    EXPLORATORY_BCA = "exploratory-bca-interval"
    OMITTED_NOT_COMPUTABLE = "interval-omitted-not-computable"


class TradeoffComparison(StrEnum):
    VERSUS_LOCAL = "versus-local"
    VERSUS_FEDAVG = "versus-fedavg"


class TradeoffMeasure(StrEnum):
    FEDERATION_UNSEEN_RECALL_CHANGE = "federation-unseen-recall-change"
    OWN_DOMAIN_UNSEEN_RECALL_CHANGE = "own-domain-unseen-recall-change"
    WORST_CLIENT_UNSEEN_RECALL_CHANGE = "worst-client-unseen-recall-change"
    CTK_GAIN = "paired-seed-ctk-gain"
    POOLING_GAIN = "paired-seed-pooling-gain"
    KNOWN_FAMILY_RECALL_CHANGE = "known-family-recall-change"
    REALISED_FPR_CHANGE = "realised-fpr-change"
    FULL_EXPOSURE_GAP = "full-exposure-gap"
    ORACLE_GAP_RECOVERY = "oracle-gap-recovery"


class RobustnessScope(StrEnum):
    PRIMARY_FAMILY_SET = "primary-family-set"
    REPLICATION_FAMILY_SET = "replication-family-set"
    LINEAR_MODEL = "linear-model"
    TREE_MODEL = "gradient-boosted-tree-model"
    LOWER_TRAINING_SUPPORT = "lower-training-support"
    LOW_FAMILY_SUPPORT = "low-family-support"
    HIGH_FAMILY_SUPPORT = "high-family-support"
    PARTITION_SALT = "partition-salt"
    PACKAGE_ONLY_GROUPING = "package-only-grouping"
    NATURAL_SCARCITY = "natural-scarcity"
    PERMUTATION_CONTROL = "family-label-permutation-control"


class CtkAggregation(StrEnum):
    PAIRED_SEED_MACRO = "paired-seed-macro"
    MICRO_POOLED = "micro-pooled"


class Sensitivity(StrEnum):
    ALL_FAMILIES = "all-families"
    TOP_FAMILY_REMOVAL = "top-family-removal"
    DEDUPLICATED_TEST = "deduplicated-test"


class ReportTable(StrEnum):
    FAMILY_CLIENT_CTK = "family-client-ctk"
    CTK_VARIANCE = "ctk-variance-components"
    FAMILY_ASSOCIATIONS = "family-associations"
    CLIENT_CTK = "client-ctk-analysis"
    ANCHORED_WORST_CLIENT = "anchored-worst-client"
    ANCHORED_CLIENT_SELECTION = "anchored-client-selection"
    ARM_TRADEOFF = "federated-arm-tradeoff"
    ROBUSTNESS_SYNTHESIS = "ctk-robustness-synthesis"
    FAMILY_PATTERNS = "family-mechanism-patterns"
    NATURAL_COMPARISON = "natural-scarcity-comparison"
    PERMUTATION_AUDIT = "permutation-control-audit"
    MECHANISM_HEADROOM = "mechanism-headroom"
    OPERATING_FIDELITY = "operating-point-fidelity"
    DATASET_CLIENT_AUDIT = "dataset-client-audit"
    PRIMARY_ARM_COMPARISON = "primary-arm-comparison"
    COLLABORATION_DECOMPOSITION = "collaboration-decomposition"
    PEER_DOSE_RESPONSE = "peer-dose-response"
    FAMILY_LEVEL = "family-level"
    CLAIM_GATES = "claim-gates"
    ROBUSTNESS = "robustness"


class ReportFigure(StrEnum):
    COLLABORATION_DECOMPOSITION = "collaboration-decomposition"
    MEAN_VERSUS_WORST_CLIENT = "mean-versus-worst-client"
    OWN_DOMAIN_VERSUS_FEDERATION_WIDE = "own-domain-versus-federation-wide"
    PEER_DOSE_RESPONSE = "peer-dose-response"
    FAMILY_RESCUE_MAP = "family-rescue-map"
    FEATURE_NOVELTY_VERSUS_CTK_GAIN = "feature-novelty-versus-ctk-gain"
    KNOWN_VERSUS_UNSEEN_TRADEOFF = "known-versus-unseen-tradeoff"
    CLIENT_CTK_ANALYSIS = "client-ctk-analysis"
    CTK_ROBUSTNESS_FOREST = "ctk-robustness-forest"
    FEDERATED_ARM_TRADEOFF = "federated-arm-tradeoff"
    NATURAL_VERSUS_CONTROLLED = "natural-versus-controlled"


class FamilyOutcome(StrEnum):
    RESCUED = "rescued"
    POORLY_RESCUED = "poorly-rescued-under-full-exposure"
    NOT_CLASSIFIABLE = "not-classifiable-without-full-exposure"


class DoseLevel(StrEnum):
    ALL_AVAILABLE = "all-available"
    NATURAL = "natural"


class PlotGeometry(float, Enum):
    WIDTH = 8.0
    HEIGHT = 4.5
    BAR_WIDTH = 0.35
    DPI = 200.0
    MARKER_SIZE = 60.0
    TICK_ROTATION = 45.0
    FOREST_WIDTH = 12.0
    FOREST_ROW_HEIGHT = 0.3
    FOREST_MARGIN = 2.0
    FOREST_LEFT = 0.45
    PANEL_WIDTH = 13.0
    PANEL_HEIGHT = 7.0
    SMALL_FONT = 7.0
    GRID_ALPHA = 0.3
    PANEL_SPACE = 0.55
    LEGEND_ANCHOR_X = 0.5
    LEGEND_ANCHOR_Y = -0.05


class SubplotGrid(IntEnum):
    ROWS = 1
    COLUMNS = 2
    THREE_COLUMNS = 3
    PANEL_ROWS = 2
    PANEL_COLUMNS = 3


class PlotText(StrEnum):
    DECOMPOSITION_TITLE = "Collaboration decomposition (federation-wide unseen-family recall)"
    RECALL = "Recall"
    FNR = "False-negative rate"
    LOCAL = "Local baseline"
    POOLING = "Generic pooling gain"
    CTK = "Complementary threat-knowledge gain"
    FULL_CEILING = "Full-exposure ceiling"
    MEAN_VERSUS_WORST_TITLE = "Mean versus worst client"
    MEAN_CLIENT = "Mean client"
    WORST_CLIENT = "Worst client"
    DOMAIN_TITLE = "Seed-paired complementary gain: own-domain versus federation-wide"
    OWN_DOMAIN = "Own-domain"
    FEDERATION_WIDE = "Federation-wide"
    GAIN = "Gain in recall"
    DOSE_TITLE = "Peer-exposure dose response"
    EFFECTIVE_DOSE = "Effective peer samples of the family"
    RESCUE_TITLE = "Family rescue map (FedAvg)"
    ABSENT = "No-family"
    PEER = "Peer-family"
    FULL = "Full exposure"
    NOVELTY_TITLE = "Training-only feature novelty versus complementary gain"
    NOVELTY = "Novelty score"
    TRADEOFF_TITLE = "Known-family recall versus unseen-family recall"
    KNOWN_RECALL = "Known-family recall"
    UNSEEN_RECALL = "Unseen-family recall"
    FOREST_TITLE = "Complementary-knowledge gain across every robustness scope"
    FOREST_AXIS = "Complementary-knowledge recall gain (peer-family minus no-family)"
    FOREST_ROW = "{scope} | {detail} | {learner} | alpha {alpha}"
    FOREST_SALT = "{detail}, salt {salt}"
    PRACTICAL_THRESHOLD = "Practical threshold (+0.03)"
    PAIRED_SEED_LEGEND = "Seed-paired macro estimand (BCa 95% interval)"
    MICRO_POOLED_LEGEND = "Micro-pooled hits/trials estimand (BCa 95% interval)"
    NATURAL_TITLE = "Controlled exposure versus natural scarcity (FedAvg, separate estimands)"
    CONTROLLED_LABEL = "Controlled exposure"
    NATURAL_LABEL = "Natural scarcity"
    CLIENT_TITLE = (
        "Post-confirmatory client-level analysis, FedAvg federation-wide (class C; "
        "exploratory small-n BCa intervals, seeds per client differ)"
    )
    CLIENT_KNOWN_TITLE = "Known-family recall change versus local, by client and arm"
    ESTIMAND_TOTAL = "Total gain"
    ESTIMAND_POOLING = "Pooling gain"
    ESTIMAND_CTK = "CTK gain"
    TRADEOFF_SUPTITLE = (
        "Federated arms versus local (seed-paired, BCa 95% interval). "
        "Descriptive trade-off; no score or ranking is defined"
    )


class ResultsDirectory(StrEnum):
    EVIDENCE = "evidence"
    STATISTICS = "statistics"
    GATES = "gates"
    TABLES = "tables"
    FIGURES = "figures"
    PROVENANCE = "provenance"
    EXTENSION = "extension"
    EXTENSION_B = "extension-b"


class ResultsFile(StrEnum):
    MANIFEST = "manifest.json"
    SOURCE_DATA = "source-data.json"
    CODE = "code.json"
    DOSE_CODE = "dose-code.json"
    CONTROLS_CODE = "controls-code.json"
    REPRESENTATION_CODE = "representation-code.json"
    DIAGNOSTICS_CODE = "diagnostics-code.json"
    EXTENSION_PROVENANCE = "extension-provenance.json"
    ENVIRONMENT = "environment.json"
    PROTOCOL = "protocol.json"
    SEED_STATUS = "seed-status.csv"
    CLAIMS = "claims.csv"
    EXTENSION_AUDIT = "permutation-control-audit.csv"


class PromotionBlock(StrEnum):
    NOT_CONFIRMATORY = "not-confirmatory"
    NOT_EXTENSION_B = "not-extension-b"
    RUNS_INCOMPLETE = "runs-incomplete"
    VALIDATION_FAILED = "validation-failed"
    CLAIMS_INCOMPLETE = "claims-incomplete"
    PROVENANCE_STALE = "provenance-stale"
    ROW_LEVEL_DATA = "row-level-data"


class PromotionState(StrEnum):
    PROMOTED = "promoted"
    BLOCKED = "blocked"


class AnalysisStage(StrEnum):
    DECOMPOSITION = "decomposition"
    STATISTICS = "statistics"
    POST_CONFIRMATORY = "post-confirmatory"
    FAMILY_EFFECTS = "family-effects"
    DOSE_RESPONSE = "dose-response"
    NOVELTY = "novelty"
    ROBUSTNESS = "robustness"
    CLUSTER_BOOTSTRAP = "cluster-bootstrap"
    CLAIM_GATES = "claim-gates"
    HIDDEN_FAMILY = "hidden-family"
    LARGE_FAMILY = "large-family"
    DOSE_EXTENSION = "dose-extension"
    CONTROLS_EXTENSION = "controls-extension"
    REPRESENTATION_EXTENSION = "representation-extension"
    DIAGNOSTICS = "diagnostics"


class PermutationOutcome(StrEnum):
    EQUIVALENT = "equivalent"
    EXCEEDS_BAND = "exceeds-band"
    UNRESOLVED = "unresolved"


class TunedParameter(StrEnum):
    LOCAL_EPOCHS = "local-epochs"
    FINETUNE_EPOCHS = "finetune-epochs"
    FEDPROX_STRENGTH = "fedprox-strength"
    AGGREGATION = "aggregation"


class DiagnosticColumn(StrEnum):
    ARM = "arm"
    SET = "set"
    N = "n"
    SEEDS = "seeds"
    MEAN = "mean"
    MEDIAN = "median"
    POSITIVE = "pos"
    READING = "reading"
    REFERENCE = "r0"
    DIFF = "diff"
    BENIGN_TEST = "n_benign"
    POSITIVE_TEST = "n_pos"
    CALIBRATED_RECALL = "cal_recall"
    CALIBRATED_FPR = "cal_fpr"
    EQUAL_FPR_RECALL = "eq_recall"
    STORED_RECALL = "stored_recall"
    STORED_FPR = "stored_fpr"
    STORED_TRIALS = "stored_trials"
    SCORES = "n_scores"
    NONFINITE = "nonfinite"
    MINIMUM = "min"
    MAXIMUM = "max"
    ABOVE_LARGE = "abs_gt_1e3"
    ABOVE_EXTREME = "abs_gt_1e4"
    STATISTIC = "statistic"
    UNSTABLE = "unstable"
    CTK = "ctk"
    RANK_NOVELTY = "rank_novelty"
    RANK_CTK = "rank_ctk"
    RANK_PRODUCT = "rank_product"
    LOO_RHO = "loo_rho"
    INFLUENCE = "influence"
    INFLUENCE_RANK = "influence_rank"
    LEVERAGE = "leverage"
    COOK_LIKE = "cook_like"
    PAIRS = "pairs"
    TOTAL_TRIALS = "total_trials"
    MEAN_TRIALS = "mean_trials"
    DOSE_CODE = "dose_code"
    SEGMENT = "segment"
    INCREMENT = "increment"
    PER_UNIT = "per10"
    PER_UNIT_LOW = "per10_low"
    PER_UNIT_HIGH = "per10_high"
    CTK_TOP_LOW = "ctk_top_ci_low"
    CTK_TOP_HIGH = "ctk_top_ci_high"
    NATURAL_CTK = "natural_ctk"
    ONSET_MEAN = "onset_mean"
    ONSET_INTERVAL = "onset_ci"
    RESPONSE_CLASS = "response_class"
    CONFIRMATORY_CTK = "confirmatory_ctk"
    CONFIRMATORY_NOVELTY = "novelty_fl"
    DOSE_NOVELTY = "novelty_dose_runs"
    OUTCOME = "outcome"
    PREDICTOR = "predictor"
    RHO = "spearman_rho"
    FIT_LEVEL = "fit_level"
    CURVE = "curve"
    UNITS = "units"
    AIC = "aic_"
    CV_MSE = "cvmse_"
    EMAX = "emax"
    ED50 = "ed50"
    LOG_SLOPE = "log_slope"
    EMAX_LOW = "emax_lo"
    EMAX_HIGH = "emax_hi"
    ED50_LOW = "ed50_lo"
    ED50_HIGH = "ed50_hi"
    ED50_BEYOND_TOP = "p_ed50_beyond_top_dose"
    ED50_AT_BOUND = "p_ed50_at_bound"
    ED50_IDENTIFIED = "ed50_identified"
    EQUIVALENT_DOSE = "effective_dose_equiv"
    EQUIVALENT_LOW = "ede_lo"
    EQUIVALENT_HIGH = "ede_hi"
    EQUIVALENT_BEYOND_TOP = "p_ede_beyond_top_dose"
    VARIANCE_BETWEEN = "var_between_family"
    VARIANCE_WITHIN = "var_within_seed"
    ICC = "icc_family"
    ICC_LOW = "icc_lo"
    ICC_HIGH = "icc_hi"
    ETA_SQUARED = "eta2_family"
    PLACEBO_EFFECT = "placebo_eff"
    CTK_MINUS_PLACEBO = "ctk_minus_pl"
    CTK_MEAN = "ctk_mean"
    CTK_TRIMMED = "ctk_trim"
    CTK_MEDIAN = "ctk_med"
    TRIMMED_MINUS_MEAN = "trim_minus_mean"
    MEDIAN_MINUS_MEAN = "med_minus_mean"
    REALLOCATED = "reallocated"
    NEED = "need"
    REALLOCATED_SHARE = "realloc_share"
    IS_REALLOCATED = "realloc"
    PEERS = "n_peers"
    SUBSTANTIAL_PEERS = "n_peers30"
    TOP_SHARE = "top_share"
    PLACEBO_FAMILY = "placebo_family"
    CENTROID_DISTANCE = "centroid_distance"
    NEAREST_KNOWN_DISTANCE = "nearest_known_distance"
    PLACEBO_RANK = "placebo_rank"
    HIDDEN_PEER_FIT = "hidden_peer_fit"
    PLACEBO_PEER_FIT = "placebo_peer_fit"
    FIT_RATIO = "fit_ratio"
    GATE = "gate"
    STRATUM = "stratum"
    CELLS = "cells"
    EQUIVALENT = "equiv"
    BEYOND_MEAN = "ctkpl_mean"
    BEYOND_LOW = "ctkpl_lo"
    BEYOND = "beyond"
    SLOPE = "slope"
    SLOPE_LOW = "slope_lo"
    SLOPE_HIGH = "slope_hi"
    INTERCEPT = "intercept"
    OTHER_SUFFIX = "_n"
    MEAN_SUFFIX = "_mean"
    LOW_SUFFIX = "_lo"
    HIGH_SUFFIX = "_hi"
    SEEDS_SUFFIX = "_seeds"
    POSITIVE_SUFFIX = "_pos"
    PEER_SUPPORT = "peer_support"
    TARGET_SUPPORT_PRESENT = "target_support_peer_present"
    TARGET_SUPPORT_FULL = "target_support_full"
    CENTRAL_FULL_RECALL = "central_full_recall"
    POOLING = "pooling"
    TOTAL = "total"
    HEADROOM = "headroom"
    RESIDUAL_GAP = "residual_gap"
    FULL_CENTRAL = "full_central"
    FULL_LINEAR = "full_linear"
    FULL_TREES = "full_trees"
    POOR_CLASSES = "n_classes_poor"
    CLASSES = "n_classes"
    LABEL_COUNT = "n_labels"
    LABELS = "labels"
    LOG_ROWS = "log_rows"
    LARGE_FAMILY_CTK = "lfam_ctk"


class InfluenceStatistic(StrEnum):
    RHO_ALL = "rho-all-families"
    RHO_STABLE = "rho-stable-families"
    JACKKNIFE_SE = "jackknife-se"
    JACKKNIFE_BIAS_CORRECTED = "jackknife-bias-corrected-rho"
    LOO_MIN = "leave-one-out-rho-min"
    LOO_MEDIAN = "leave-one-out-rho-median"
    LOO_MAX = "leave-one-out-rho-max"
    WEIGHTED_SEED_COUNT = "weighted-rho-seed-count"
    WEIGHTED_SQRT_TRIALS = "weighted-rho-sqrt-total-trials"
    WEIGHTED_INVERSE_VARIANCE = "weighted-rho-inverse-variance"
    SEED_RHO = "per-seed-rho"
    SEED_PAIR_MIN = "seed-pair-rank-rho-min"
    SEED_PAIR_MEDIAN = "seed-pair-rank-rho-median"
    SEED_PAIR_MEAN = "seed-pair-rank-rho-mean"
    SEED_PAIR_MAX = "seed-pair-rank-rho-max"
    SEED_PAIR_NEGATIVE = "seed-pair-negative-count"
    KENDALL_W = "kendall-w"
    KENDALL_IMPLIED_RHO = "kendall-implied-mean-rho"
    KENDALL_CHI2 = "kendall-chi2"
    KENDALL_P = "kendall-p"
    VARIANCE_BETWEEN = "variance-between-families"
    VARIANCE_WITHIN = "mean-within-family-variance"
    ERROR_VARIANCE = "mean-error-variance-of-mean"
    VARIANCE_RELIABILITY = "variance-reliability"
    SPLIT_HALF_RELIABILITY = "split-half-rank-reliability"
    DISATTENUATED_VARIANCE = "disattenuated-rho-variance-reliability"
    DISATTENUATED_RANK = "disattenuated-rho-rank-reliability"


# Frozen seeds of the scratch diagnostics each analysis reproduces (several coincide).
class DiagnosticSeed(IntEnum):
    INFLUENCE = 20260925
    DOSE = 20260925
    ASSOCIATION = 20260925
    CONTROLS = 20240501
    SLOPE = 1
    TAXONOMY = 7
    RANK_CONCORDANCE = 3


class DiagnosticResamples(IntEnum):
    INFLUENCE = 10000
    SPLIT_HALF = 2000
    DOSE_FIT = 2000
    SLOPE = 2000
    RANK_CONCORDANCE = 2000
    TAXONOMY = 4000


class DiagnosticLimit(IntEnum):
    CLIENT_SEEDS = 5
    FIT_SEEDS = 4
    DOSE_UNIT = 10
    ISOTONIC_DECIMALS = 10
    EARLY_ONSET = 25
    PEER_MIN_ROWS = 30
    POOR_CLASSES = 2
    EMAX_EVALUATIONS = 20000


class KendallConstant(IntEnum):
    NUMERATOR = 12
    CUBE = 3


class DoseCode(IntEnum):
    NATURAL = -1


class DoseFitLevel(StrEnum):
    FAMILY_MACRO = "family-macro"
    FAMILY = "family"


class DoseModel(StrEnum):
    LOG_LINEAR = "log"
    EMAX = "emax"
    ISOTONIC = "iso"


class DoseResponseClass(StrEnum):
    NONRESPONSIVE = "nonresponsive"
    EARLY = "early(<=25)"
    LATE = "late(50-200)"


class DoseRole(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "secondary"


class EmaxBound(float, Enum):
    START_FLOOR = 0.01
    TOP_LOW = -1.0
    TOP_HIGH = 5.0
    HALF_LOW = 1e-3
    HALF_HIGH = 1e5
    HALF_AT_BOUND = 9e4


class EmaxStart(IntEnum):
    HALF_5 = 5
    HALF_25 = 25
    HALF_100 = 100
    HALF_400 = 400
    HALF_2000 = 2000


class ControlArm(StrEnum):
    PLACEBO = "PL"
    PRESENT_MEAN = "P_mean"
    PRESENT_TRIMMED = "P_trim"
    PRESENT_MEDIAN = "P_med"
    ABSENT_MEAN = "A_mean"
    ABSENT_TRIMMED = "A_trim"
    ABSENT_MEDIAN = "A_med"


class PeerShare(float, Enum):
    SINGLE = 0.9
    DOMINANT = 0.6


class ReallocationStratum(StrEnum):
    REALLOCATED = "realloc"
    NOT_REALLOCATED = "norealloc"
    DIFFERENCE = "diff(re-no)"


class SupportStratum(StrEnum):
    SINGLE = "single-peer(>=90%)"
    DOMINANT = "dominant(60-90%)"
    SPREAD = "spread(<60%)"
    SINGLE_PEER = "single>=0.9"
    MULTI_PEER = "multi<0.9"


class TaxonomyLabel(StrEnum):
    EXPOSURE_LIMITED = "exposure_limited"
    REPRESENTATION_LIMITED = "representation_limited"
    POOR_FULL_SINGLE_CLASS = "poor_full_single_class"
    LOW_HEADROOM = "low_headroom"
    POOLING_RESPONSIVE = "pooling_responsive"
    NEGATIVE_TRANSFER_SENSITIVE = "negative_transfer_sensitive"
    EXPOSURE_LIMITED_INTERVAL = "exposure_limited_ci"
    NEGATIVE_TRANSFER_INTERVAL = "negative_transfer_sensitive_ci"
    POOLING_RESPONSIVE_INTERVAL = "pooling_responsive_ci"


class OperatingReading(StrEnum):
    CALIBRATED = "calibrated"
    EQUAL_TEST_FPR = "equal-test-fpr"


class ScoreMagnitude(float, Enum):
    LARGE = 1e3
    EXTREME = 1e4


class ExtensionStudy(StrEnum):
    EXT_1 = "EXT-1"
    LARGE_FAMILY = "EXT-LFAM"
    DOSE = "EXT-DOSE"
    CONTROLS = "EXT-CTRL"
    REPRESENTATION = "EXT-REP"
    DIAGNOSTICS = "EXT-DIAG"


# Frozen extension protocols, relative to the repository root.
class ProtocolDocument(StrEnum):
    EXT_1 = "docs/temp/extension-protocol/EXT-1-permutation-replication.md"
    LARGE_FAMILY = "docs/temp/extension-protocol/EXT-LARGEFAM-larger-family-explanation.md"
    DOSE = "docs/temp/extension-protocol/EXT-DOSE-effective-dose.md"
    CONTROLS = "docs/temp/extension-protocol/EXT-CONTROLS-placebo-and-robust-aggregation.md"
    REPRESENTATION = "docs/temp/extension-protocol/EXT-REP-representation-replication.md"


class SupersededFile(StrEnum):
    EXT_REP_TRANSDUCTIVE = "superseded/ext-rep-transductive-transform/SHA256SUMS"
