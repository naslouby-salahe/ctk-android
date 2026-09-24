from enum import StrEnum


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
    EXPLORATORY = "exploratory"


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
    FAMILY_SUPPORT_SENSITIVITY = "family-support-sensitivity"
    PACKAGE_ONLY_GROUPING = "package-only-grouping"


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
    INSUFFICIENT_PEER_SUPPORT = "insufficient-peer-support"
    INSUFFICIENT_TEST_SUPPORT = "insufficient-test-support"
    INVALID_TARGET_TRAINING = "invalid-target-training"
    TARGET_SHARE_TOO_LARGE = "target-share-too-large"
    INSUFFICIENT_OWN_DOMAIN_SUPPORT = "insufficient-own-domain-support"
    NOT_IN_FAMILY_SET = "not-in-family-set"


class RunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED_VALIDATION = "failed-validation"
    INFEASIBLE = "infeasible"
    STRUCTURALLY_EXCLUDED = "structurally-excluded"
    INCOMPLETE = "incomplete"


class FailureReason(StrEnum):
    SCHEMA_MISMATCH = "schema-mismatch"
    ROW_COUNT_MISMATCH = "row-count-mismatch"
    LABEL_RULE_VIOLATION = "label-rule-violation"
    UNMATCHED_LINKAGE = "unmatched-linkage"
    LEAKAGE_SHA = "leakage-sha"
    LEAKAGE_COMPONENT = "leakage-component"
    LEAKAGE_FEATURE_VECTOR = "leakage-feature-vector"
    TARGET_EXPOSURE_NONZERO = "target-exposure-nonzero"
    PEER_SUPPORT_MISSING = "peer-support-missing"
    ABSENT_FAMILY_PRESENT = "absent-family-present"
    SAMPLE_SIZE_MISMATCH = "sample-size-mismatch"
    TEST_ROW_IN_TRAINING = "test-row-in-training"
    NO_ELIGIBLE_TARGETS = "no-eligible-targets"
    INSUFFICIENT_CALIBRATION = "insufficient-calibration"
    OPERATING_POINT_DEVIATION = "operating-point-deviation"
    NOT_APPLICABLE_MODEL_FAMILY = "not-applicable-model-family"


class ValidationCheck(StrEnum):
    FEATURE_CONTRACT = "feature-contract"
    SHA_UNIQUENESS = "sha-uniqueness"
    LABEL_RULE = "label-rule"
    LINKAGE_COMPLETE = "linkage-complete"
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


class Estimand(StrEnum):
    TOTAL_GAIN = "total-gain"
    POOLING_GAIN = "pooling-gain"
    CTK_GAIN = "ctk-gain"
    CTK_SHARE = "ctk-share"
    ORACLE_GAP_RECOVERY = "oracle-gap-recovery"


class ContrastName(StrEnum):
    FEDAVG_PEER_VS_LOCAL = "fedavg-peer-present-vs-local"
    FEDAVG_ABSENT_VS_LOCAL = "fedavg-absent-everywhere-vs-local"
    FEDAVG_PEER_VS_ABSENT = "fedavg-peer-present-vs-absent-everywhere"
    CENTRAL_PEER_VS_LOCAL = "central-peer-present-vs-local"
    CENTRAL_ABSENT_VS_LOCAL = "central-absent-everywhere-vs-local"
    CENTRAL_PEER_VS_ABSENT = "central-peer-present-vs-absent-everywhere"
    LOCAL_VS_FULL_CENTRAL = "local-vs-full-exposure-central"


class ContrastFamily(StrEnum):
    PRIMARY = "primary"
    REFERENCE = "reference"
    EXPLORATORY = "exploratory"


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


class PromotionState(StrEnum):
    PROMOTED = "promoted"
    BLOCKED = "blocked"


class NoveltyDescriptor(StrEnum):
    CENTROID_DISTANCE_TO_KNOWN_MALWARE = "centroid-distance-to-known-malware"
    NEAREST_KNOWN_FAMILY_DISTANCE = "nearest-known-family-distance"
    MAX_JACCARD_TO_KNOWN_FAMILY = "max-jaccard-to-known-family"
    FRACTION_ACTIVE_FEATURES_KNOWN = "fraction-active-features-known"
    DISTANCE_TO_BENIGN_CENTROID = "distance-to-benign-centroid"


class Sensitivity(StrEnum):
    OPERATING_POINT = "operating-point"
    TOP_FAMILY_REMOVAL = "top-family-removal"
    REPRESENTATION_DEDUPLICATION = "representation-deduplication"


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
    CALIBRATION_ROWS = "calibration_rows"
    TEST_ROWS = "test_rows"
    TARGET_FIT_ROWS = "target_fit_rows"
    PEER_FIT_ROWS = "peer_fit_rows"
    TARGET_TEST_ROWS = "target_test_rows"
    FEDERATION_TEST_ROWS = "federation_test_rows"
    TARGET_SHARE = "target_share"
    TOTAL_FIT_ROWS = "total_fit_rows"
    RANK = "rank"
    EXPERIMENT = "experiment"
    MODE = "mode"
    MODEL_FAMILY = "model_family"
    LEARNER = "learner"
    CONDITION = "condition"
    ARM = "arm"
    DOSE = "dose"
    EFFECTIVE_DOSE = "effective_dose"
    ALPHA = "alpha"
    METRIC = "metric"
    VALUE = "value"
    STATUS = "status"
    POPULATION = "population"
    HITS = "hits"
    TRIALS = "trials"
    THRESHOLD = "threshold"
    CALIBRATION_BENIGN = "calibration_benign"
    OPERATING_STATUS = "operating_status"
    SCORE = "score"
    LOCAL_ROWS = "local_rows"
    TARGET_CLIENT = "target_client"
    HYPERPARAMETER = "hyperparameter"
    CONTRAST = "contrast"
    CONTRAST_FAMILY = "contrast_family"
    MEAN_DIFFERENCE = "mean_difference"
    MEDIAN_DIFFERENCE = "median_difference"
    CI_LOW = "ci_low"
    CI_HIGH = "ci_high"
    P_VALUE = "p_value"
    P_HOLM = "p_holm"
    POSITIVE_SEEDS = "positive_seeds"
    SEED_COUNT = "seed_count"
    EFFECT_SIZE = "effect_size"
    ESTIMAND = "estimand"
    CLAIM = "claim"
    CLAIM_STATUS = "claim_status"
    WORDING = "wording"
    DESCRIPTOR = "descriptor"
    SPEARMAN = "spearman"
    STAT_UNIT = "stat_unit"
    TRAIN_ROWS = "train_rows"
    PATH = "path"
    FINGERPRINT = "fingerprint"
    CHECK = "check"
    PASSED = "passed"
    DETAIL = "detail"
    LOCAL_RECALL = "local_recall"
    ABSENT_RECALL = "absent_recall"
    PEER_RECALL = "peer_recall"
    FULL_RECALL = "full_recall"
    CTK_GAIN = "ctk_gain"
    NOVELTY = "novelty"
    CLASSIFICATION = "classification"
    RECALL = "recall"
    LOW = "low"
    HIGH = "high"
    RESAMPLES = "resamples"
    FEATURE_INDEX = "feature_index"
