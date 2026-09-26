import polars as pl

from ctk_android.config import load_config
from ctk_android.enums import (
    Aggregation,
    ClientId,
    Column,
    Device,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    Learner,
    ModelFamily,
    TunedParameter,
    ValidationCheck,
)
from ctk_android.experiment import design, evaluation, training
from ctk_android.experiment.design import DesignInputs, run_fields, train_design_arms
from ctk_android.paths import Paths
from ctk_android.types import RunKey
from tests.architecture.source_index import REPO_ROOT
from tests.unit.experiment.test_substitution import BUDGET, STUDY, TARGETS

FULL = load_config(Paths(REPO_ROOT))
SMALL = FULL.experiments.model_copy(
    update={"exact_dose_levels": (0, 10, 25), "placebo_min_malware_rows": 10}
)
CONFIG = FULL.model_copy(update={"experiments": SMALL})
MASKS = design.family_masks(STUDY, ("alpha", "beta"))
ATTRIBUTES = evaluation.row_attributes(STUDY, MASKS)
POOLS = evaluation.build_pools(ATTRIBUTES, TARGETS)
SEED = 310


def _inputs(name: ExperimentName) -> DesignInputs:
    key = RunKey(mode=ExecutionMode.EXTENSION_B, experiment=name, seed=SEED, salt=0)
    return DesignInputs(
        spec=CONFIG.experiments.experiments[name],
        config=CONFIG,
        key=key,
        context=training.TrainingContext(
            features=STUDY.features,
            labels=ATTRIBUTES.labels,
            config=CONFIG.experiments.smoke_training,
            family=ModelFamily.MLP,
            device=Device.CPU,
            seed=training.derive_seed(SEED, 0),
            transform_rule=None,
        ),
        study=STUDY,
        masks=MASKS,
        pools=POOLS,
        orders=design.training_orders(STUDY, SEED, 0),
        targets=TARGETS,
        budget=BUDGET,
    )


def _failed(checks: tuple[object, ...]) -> list[object]:
    return [check for check in checks if not getattr(check, "passed")]  # noqa: B009


def test_run_fields_identify_the_run() -> None:
    fields = run_fields(_inputs(ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY).key)
    assert fields[Column.SEED] == SEED


def test_exact_dose_design_trains_every_level_for_both_learners_with_identical_volume() -> None:
    designed = train_design_arms(_inputs(ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY))
    levels = CONFIG.experiments.exact_dose_levels
    assert len(designed.arms) == 2 * (2 + len(levels))
    assert designed.placebo is None
    assert not _failed(designed.checks)
    kinds = {check.check for check in designed.checks}
    assert {
        ValidationCheck.EXACT_DOSE_REALISED,
        ValidationCheck.EXACT_DOSE_TARGET_ZERO,
        ValidationCheck.DOSE_ZERO_IS_ABSENT,
    } <= kinds
    volumes = {
        tuple(sorted((client.value, rows.size) for client, rows in per_client.items()))
        for per_client in designed.trainings.values()
    }
    assert len(volumes) == 1
    doses = {arm.dose for arm in designed.arms if arm.condition is ExposureCondition.EXACT_DOSE}
    assert doses == set(levels)


def test_placebo_design_trains_the_mean_and_both_robust_aggregations() -> None:
    designed = train_design_arms(_inputs(ExperimentName.PLACEBO_ROBUST_PRIMARY))
    assert not _failed(designed.checks)
    assert len(designed.arms) == 3 + 2 * len(Aggregation)
    assert {arm.learner for arm in designed.arms} == {Learner.FEDAVG}
    tuned = {arm.tuning.level for arm in designed.arms if arm.tuning is not None}
    assert tuned == {float(rule) for rule in Aggregation}
    assert all(
        arm.tuning.parameter is TunedParameter.AGGREGATION
        for arm in designed.arms
        if arm.tuning is not None
    )
    placebo = designed.placebo
    assert isinstance(placebo, pl.DataFrame)
    assert placebo.height == len(TARGETS)
    hidden = {pair.family for pair in TARGETS}
    assert not hidden & set(placebo["placebo_family"].to_list())
    assert {ClientId.ANZHI.value, ClientId.APPCHINA.value} == set(placebo[Column.CLIENT])
