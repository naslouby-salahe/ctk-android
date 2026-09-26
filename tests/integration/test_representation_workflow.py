from pathlib import Path

import polars as pl
import pytest

from ctk_android.config import Config, load_config
from ctk_android.data.cache import read_record
from ctk_android.enums import (
    Artifact,
    BudgetLevel,
    Column,
    EligibilityProfile,
    ExecutionMode,
    ExperimentName,
    PromotionBlock,
    PromotionState,
    RunStatus,
    Stage,
)
from ctk_android.experiment.planning import plan_run, planned_targets
from ctk_android.paths import Paths
from ctk_android.reporting.artifacts import collect_evidence
from ctk_android.types import EligibilityRule, PartitionKey, Provenance, RandomSeed, RunKey
from ctk_android.workflows.maintenance import run_plan
from ctk_android.workflows.preprocess import (
    representation_keys,
    run_representation_preprocess,
)
from ctk_android.workflows.report import run_representation_extension
from ctk_android.workflows.run import run_experiment
from tests.architecture.source_index import REPO_ROOT
from tests.unit.data.mcndroid_fixture import PRIMARY, write_lamda, write_mcndroid

BASE = load_config(Paths(REPO_ROOT))
LAMDA_ROWS = 2400
OVERLAP = list(range(200, 2200))
MODE = ExecutionMode.DEVELOPMENT
SEEDS = (RandomSeed(1), RandomSeed(2), RandomSeed(3))
SMALL_BUDGET = 100
NAMES = (
    ExperimentName.REPRESENTATION_R0,
    ExperimentName.REPRESENTATION_R1,
    ExperimentName.REPRESENTATION_R2,
    ExperimentName.REPRESENTATION_R3,
)


def _config() -> Config:
    permissive = EligibilityRule(
        peer_min_fit=20,
        federation_min_test=5,
        own_domain_min_test=2,
        target_min_remaining_fit=50,
        target_min_fit=3,
    )
    experiments = BASE.experiments.model_copy(
        update={
            "experiments": {name: BASE.experiments.experiments[name] for name in NAMES},
            "training": BASE.experiments.smoke_training,
            "budgets": {**BASE.experiments.budgets, BudgetLevel.PRIMARY: SMALL_BUDGET},
            "representation_priority_families": (PRIMARY[0],),
            "representation_contrast_families": (PRIMARY[1],),
            "representation_separate_families": (),
            "representation_focus_family": PRIMARY[0],
        }
    )
    data = BASE.data.model_copy(
        update={"eligibility": {**BASE.data.eligibility, EligibilityProfile.PRIMARY: permissive}}
    )
    seeds = BASE.project.seeds.model_copy(update={"development": SEEDS})
    return BASE.model_copy(
        update={
            "experiments": experiments,
            "data": data,
            "project": BASE.project.model_copy(update={"seeds": seeds}),
        }
    )


CONFIG = _config()


@pytest.fixture(scope="module")
def workspace(tmp_path_factory: pytest.TempPathFactory) -> Paths:
    root = tmp_path_factory.mktemp("representation")
    write_lamda(root, LAMDA_ROWS, 24)
    write_mcndroid(root, {"train": OVERLAP[:1500], "test": OVERLAP[1500:]})
    return Paths(root)


def test_only_the_configured_modes_and_seeds_get_representation_partitions() -> None:
    keys = representation_keys(BASE, (ExecutionMode.DEVELOPMENT, ExecutionMode.EXTENSION_B))
    assert [key.seed for key in keys] == [*BASE.project.seeds.development, *range(330, 340)]
    assert representation_keys(BASE, (ExecutionMode.CONFIRMATORY,)) == []
    assert representation_keys(CONFIG, (MODE,)) == [
        PartitionKey(seed=seed, salt=0, grouping=key.grouping, profile=key.profile)
        for seed in SEEDS
        for key in keys[:1]
    ]


def test_preprocess_builds_once_then_reuses_and_rebuilds_on_overwrite(workspace: Paths) -> None:
    first = run_representation_preprocess(workspace, CONFIG, False, (MODE,))
    assert [report.reused for report in first] == [False] * (1 + len(SEEDS))
    assert first[0].stage is Stage.REPRESENTATION
    again = run_representation_preprocess(workspace, CONFIG, False, (MODE,))
    assert all(report.reused for report in again)
    rebuilt = run_representation_preprocess(workspace, CONFIG, True, (MODE,))
    assert not any(report.reused for report in rebuilt)
    stored = read_record(workspace.provenance_file(workspace.representation_dir), Provenance)
    assert stored.inputs == first[0].fingerprint


def test_preprocess_needs_the_lamda_stages(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="preprocess"):
        run_representation_preprocess(Paths(tmp_path), CONFIG, False, (MODE,))


def test_every_representation_shares_the_partition_and_the_planned_targets(
    workspace: Paths,
) -> None:
    run_representation_preprocess(workspace, CONFIG, False, (MODE,))
    run_plan(workspace, CONFIG, MODE)
    for seed in SEEDS:
        planned = [
            planned_targets(workspace, RunKey(mode=MODE, experiment=name, seed=seed, salt=0))
            for name in NAMES
        ]
        assert all(item.status is RunStatus.COMPLETED for item in planned)
        assert all(item.targets == planned[0].targets for item in planned)
        assert {pair.family for pair in planned[0].targets} <= set(PRIMARY)
    one = plan_run(workspace, CONFIG, NAMES[0], MODE, SEEDS[0], 0)
    pairs = pl.read_parquet(
        workspace.representation_partition_file(one.partition, Artifact.CONTROLLED_PAIRS)
    )
    assert set(pairs[Column.FAMILY].to_list()) >= {pair.family for pair in one.targets}


def test_runs_analysis_and_promotion_gate_work_end_to_end_on_the_overlap_partition(
    workspace: Paths,
) -> None:
    run_representation_preprocess(workspace, CONFIG, False, (MODE,))
    run_plan(workspace, CONFIG, MODE)
    for name in NAMES:
        reports = run_experiment(workspace, CONFIG, name, MODE, SEEDS, overwrite=False)
        assert [report.status for report in reports] == [RunStatus.COMPLETED] * len(SEEDS)
    reused = run_experiment(workspace, CONFIG, NAMES[2], MODE, SEEDS[:1], overwrite=False)
    assert reused[0].reused
    decision = run_representation_extension(workspace, CONFIG, MODE, promote_evidence=True)
    assert decision is not None
    assert decision.state is PromotionState.BLOCKED
    assert decision.blocks == (PromotionBlock.NOT_EXTENSION_B,)
    for artifact in (
        Artifact.REPRESENTATION_RUN_INDEX,
        Artifact.REPRESENTATION_SEED_EFFECTS,
        Artifact.REPRESENTATION_EFFECTS,
        Artifact.REPRESENTATION_LEVELS,
        Artifact.REPRESENTATION_VERDICTS,
        Artifact.REPRESENTATION_ELIGIBILITY,
    ):
        assert workspace.analysis_file(MODE, artifact).is_file(), artifact
    effects = pl.read_parquet(workspace.analysis_file(MODE, Artifact.REPRESENTATION_EFFECTS))
    assert effects["representation"].n_unique() == len(NAMES) - 1
    index = pl.read_parquet(workspace.analysis_file(MODE, Artifact.REPRESENTATION_RUN_INDEX))
    assert set(index[Column.STATUS].to_list()) == {RunStatus.COMPLETED}
    eligibility = pl.read_parquet(
        workspace.analysis_file(MODE, Artifact.REPRESENTATION_ELIGIBILITY)
    )
    assert eligibility.height == len(SEEDS) * len(PRIMARY)


def test_changing_the_prevalence_rule_rebuilds_partitions_and_marks_runs_stale(
    workspace: Paths,
) -> None:
    run_representation_preprocess(workspace, CONFIG, False, (MODE,))
    run_plan(workspace, CONFIG, MODE)
    run_experiment(workspace, CONFIG, NAMES[3], MODE, SEEDS[:1], overwrite=False)
    fresh = collect_evidence(workspace, CONFIG, MODE, fairness=False, only=(NAMES[3],))
    statuses = dict(
        zip(
            fresh.index[Column.SEED].to_list(),
            fresh.index[Column.STATUS].to_list(),
            strict=True,
        )
    )
    assert statuses[SEEDS[0]] == RunStatus.COMPLETED
    stricter = CONFIG.model_copy(
        update={
            "experiments": CONFIG.experiments.model_copy(
                update={"representation_min_prevalence": 0.2}
            )
        }
    )
    reports = run_representation_preprocess(workspace, stricter, False, (MODE,))
    assert reports[0].reused
    assert not any(report.reused for report in reports[1:])
    stale = collect_evidence(workspace, stricter, MODE, fairness=False, only=(NAMES[3],))
    assert RunStatus.STALE in stale.index[Column.STATUS].to_list()
