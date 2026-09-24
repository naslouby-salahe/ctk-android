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


class FailureReason(StrEnum):
    SCHEMA_MISMATCH = "schema-mismatch"
    NO_ELIGIBLE_TARGETS = "no-eligible-targets"
    INSUFFICIENT_CALIBRATION = "insufficient-calibration"
    NOT_APPLICABLE_MODEL_FAMILY = "not-applicable-model-family"


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


class ContrastFamily(StrEnum):
    PRIMARY = "primary"


class ClaimName(StrEnum):
    DOSE_RESPONSE = "dose-response"


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


class LogEvent(StrEnum):
    STAGE_REUSED = "stage-reused"
    STAGE_BUILT = "stage-built"
    STAGE_FAILED = "stage-failed"
    RUN_STARTED = "run-started"
    RUN_REUSED = "run-reused"
    RUN_FINISHED = "run-finished"
    ARM_TRAINED = "arm-trained"


class CliCommand(StrEnum):
    DOCTOR = "doctor"
    PREPROCESS = "preprocess"
    PLAN = "plan"
    SMOKE = "smoke"
    RUN = "run"
    STATUS = "status"


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
    SOURCE = "src"
    PACKAGE = "ctk_android"
    CONFIGS = "configs"
    OUTPUTS = "outputs"
    PREPROCESSING = "preprocessing"
    LINKAGE = "linkage"
    CACHE = "cache"
    PLANS = "plans"
    METRICS = "metrics"
    SCORES = "scores"
    MODELS = "models"


class SourceFile(StrEnum):
    PROJECT_MARKER = "pyproject.toml"
    LAMDA_FEATURE_MAPPING = "feature_mapping.csv"
    LAMDA_PARQUET_GLOB = "*/*.parquet"
    ANDROZOO_ARCHIVE = "latest.csv.gz"
    PYTHON_GLOB = "*.py"


class CoreModule(StrEnum):
    TYPES = "types.py"
    ENUMS = "enums.py"
    CONFIG = "config.py"
    PATHS = "paths.py"


class FileSuffix(StrEnum):
    PARQUET = ".parquet"
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


class Separator(StrEnum):
    NEWLINE = "\n"
    COLON = ":"
    COLON_SPACE = ": "
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
    CALIBRATION_ROWS = "calibration rows are own-client benign calibration rows"
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


class Pattern(StrEnum):
    SHA256 = r"^[0-9a-f]{64}$"
    YEAR_MONTH = r"^\d{4}-\d{2}$"
    FEATURE_COLUMN = r"^feat_\d+$"


class FeatureNaming(StrEnum):
    PREFIX = "feat_"


class MarketCount(IntEnum):
    SINGLE = 1
