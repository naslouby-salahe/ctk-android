from enum import Enum, IntEnum, StrEnum
from typing import Final


class DatasetName(StrEnum):
    LAMDA = "lamda"
    ANDROZOO = "androzoo"


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


class ExperimentName(StrEnum):
    END_TO_END = "end-to-end"
    BASELINE_FAIRNESS = "baseline-fairness"
    CONTROLLED_EXPOSURE = "controlled-exposure"
    PEER_DOSE_RESPONSE = "peer-dose-response"
    NATURAL_SCARCITY = "natural-scarcity"
    FAMILY_PERMUTATION_CONTROL = "family-permutation-control"
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


class ExposureMode(StrEnum):
    HIDE_FROM_TARGET = "hide-from-target"
    NATURAL = "natural"


class FamilySetName(StrEnum):
    PRIMARY = "primary"
    REPLICATION = "replication"


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


class AndroZooColumn(StrEnum):
    SHA256 = "sha256"
    PACKAGE = "pkg_name"
    MARKETS = "markets"
    VT_DETECTION = "vt_detection"


class Artifact(StrEnum):
    CLIENT_CTK = "client-ctk-analysis.parquet"
    FAMILY_CLIENT_CTK = "family-client-ctk.parquet"
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


class Device(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"


class Column(StrEnum):
    SHA256 = "sha256"
    ROW = "row"
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


class Display(IntEnum):
    FINGERPRINT_PREFIX = 12


class PythonRequirement(IntEnum):
    MAJOR = 3
    MINOR = 12


class Tolerance(float, Enum):
    PARTITION_FRACTIONS = 1e-9
    THROUGHPUT_FLOOR = 1e-9


class Separator(StrEnum):
    NEWLINE = "\n"
    COLON = ":"
    COLON_SPACE = ": "
    COMMA = ","
    PIPE = "|"
    EMPTY = ""


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


class Pattern(StrEnum):
    SHA256 = r"^[0-9a-f]{64}$"
    YEAR_MONTH = r"^\d{4}-\d{2}$"
    FEATURE_COLUMN = r"^feat_\d+$"


class FeatureNaming(StrEnum):
    PREFIX = "feat_"


class MarketCount(IntEnum):
    SINGLE = 1


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


class VarianceSource(StrEnum):
    FAMILY = "family"
    SEED = "seed"
    RESIDUAL = "family-by-seed-residual"


class FamilyPredictor(StrEnum):
    LOCAL_RECALL = "local-recall"
    POOLING_GAIN = "pooling-gain"


class FamilyOutcomeMeasure(StrEnum):
    CTK_GAIN = "ctk-gain"
    TOTAL_GAIN = "total-gain"


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


class ResultsFile(StrEnum):
    MANIFEST = "manifest.json"
    SOURCE_DATA = "source-data.json"
    CODE = "code.json"
    ENVIRONMENT = "environment.json"
    PROTOCOL = "protocol.json"
    SEED_STATUS = "seed-status.csv"
    CLAIMS = "claims.csv"
    EXTENSION_AUDIT = "permutation-control-audit.csv"


class PromotionBlock(StrEnum):
    NOT_CONFIRMATORY = "not-confirmatory"
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


class PermutationOutcome(StrEnum):
    EQUIVALENT = "equivalent"
    EXCEEDS_BAND = "exceeds-band"
    UNRESOLVED = "unresolved"


class TunedParameter(StrEnum):
    LOCAL_EPOCHS = "local-epochs"
    FINETUNE_EPOCHS = "finetune-epochs"
    FEDPROX_STRENGTH = "fedprox-strength"
