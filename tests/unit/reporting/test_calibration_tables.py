from pathlib import Path

import polars as pl

from ctk_android.config import load_config
from ctk_android.data.cache import write_table
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    ExecutionMode,
    ExperimentName,
    Metric,
    OperatingPointStatus,
    OptimizationStatus,
    RunStatus,
)
from ctk_android.paths import Paths
from ctk_android.reporting.tables import (
    client_fpr_summary,
    operating_calibration,
    training_convergence,
)
from ctk_android.types import RandomSeed, RunKey
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
MODE = ExecutionMode.EXTENSION_B
NAME = ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY
SEED = RandomSeed(310)
ALPHA = CONFIG.experiments.operating.primary_alpha
TOLERANCE = CONFIG.experiments.operating.realised_fpr_tolerance


def _index() -> pl.DataFrame:
    return pl.DataFrame(
        {
            Column.EXPERIMENT: [NAME, NAME],
            Column.SEED: [SEED, SEED + 1],
            Column.SALT: [0, 0],
            Column.STATUS: [RunStatus.COMPLETED, RunStatus.FAILED_VALIDATION],
        }
    )


def _write_run(paths: Paths, hits: dict[ClientId, int]) -> None:
    key = RunKey(mode=MODE, experiment=NAME, seed=SEED, salt=0)
    rows = [
        {
            Column.LEARNER: "fedavg",
            Column.CONDITION: "peer-present",
            Column.DOSE: None,
            Column.PARAMETER: None,
            Column.TUNING_VALUE: None,
            Column.CLIENT: client,
            Column.ALPHA: ALPHA,
            Column.THRESHOLD: 0.5,
            Column.CALIBRATION_BENIGN: 3000,
            Column.OPERATING_STATUS: OperatingPointStatus.VALID,
            Column.HITS: hit,
            Column.TRIALS: 1000,
            Column.VALUE: hit / 1000,
        }
        for client, hit in hits.items()
    ]
    schema = pl.Schema(
        {
            f"{Column.DOSE}": pl.Int64,
            f"{Column.PARAMETER}": pl.String,
            f"{Column.TUNING_VALUE}": pl.Float64,
        }
    )
    write_table(
        pl.DataFrame(rows, schema_overrides=schema),
        paths.run_metric_file(key, Artifact.OPERATING_POINTS),
    )


def test_operating_calibration_reports_every_client_with_counts_threshold_and_deviation(
    tmp_path: Path,
) -> None:
    paths = Paths(tmp_path)
    breach_hits = round((ALPHA + TOLERANCE + 0.05) * 1000)
    _write_run(paths, {ClientId.ANZHI: breach_hits, ClientId.PLAY_EARLY: round(ALPHA * 1000)})

    table = operating_calibration(paths, CONFIG, MODE, _index())

    assert table.height == 2
    assert {
        Column.CLIENT,
        Column.REQUESTED_ALPHA,
        Column.THRESHOLD,
        Column.CALIBRATION_BENIGN,
        Column.BENIGN_TEST,
        Column.CLIENT_REALISED_FPR,
        Column.CLIENT_FPR_DEVIATION,
        Column.FPR_BREACH,
    } <= set(table.columns)
    anzhi = table.filter(pl.col(Column.CLIENT) == ClientId.ANZHI).row(0, named=True)
    assert anzhi[Column.BENIGN_TEST] == 1000
    assert anzhi[Column.CALIBRATION_BENIGN] == 3000
    assert anzhi[Column.REQUESTED_ALPHA] == ALPHA
    assert anzhi[Column.CLIENT_FPR_DEVIATION] == breach_hits / 1000 - ALPHA
    assert anzhi[Column.FPR_BREACH]
    early = table.filter(pl.col(Column.CLIENT) == ClientId.PLAY_EARLY).row(0, named=True)
    assert not early[Column.FPR_BREACH]
    assert early[Column.SEED] == SEED


def test_only_completed_runs_contribute_calibration_evidence(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    assert operating_calibration(paths, CONFIG, MODE, _index().clear()).is_empty()


def test_client_fpr_summary_keeps_breaches_visible(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    _write_run(paths, {ClientId.ANZHI: 200, ClientId.PLAY_EARLY: round(ALPHA * 1000)})
    summary = client_fpr_summary(operating_calibration(paths, CONFIG, MODE, _index()))
    anzhi = summary.filter(pl.col(Column.CLIENT) == ClientId.ANZHI).row(0, named=True)
    assert anzhi[Column.BREACHES] == 1
    assert anzhi[Column.MAX_FPR_DEVIATION] > TOLERANCE
    early = summary.filter(pl.col(Column.CLIENT) == ClientId.PLAY_EARLY).row(0, named=True)
    assert early[Column.BREACHES] == 0
    assert client_fpr_summary(pl.DataFrame()).is_empty()


def _training(paths: Paths, losses: list[float | None], finite: bool) -> None:
    key = RunKey(mode=MODE, experiment=NAME, seed=SEED, salt=0)
    rows = [
        {
            Column.LEARNER: "fedavg",
            Column.CONDITION: "peer-present",
            Column.DOSE: None,
            Column.PARAMETER: None,
            Column.TUNING_VALUE: None,
            Column.PHASE: "federated-global",
            Column.CLIENT: None,
            "round": round_index,
            "epoch": None,
            Column.LOSS: loss,
            Column.NONFINITE_BATCHES: 0 if finite else 2,
            Column.PARAMETERS_FINITE: finite,
            Column.STATUS: OptimizationStatus.COMPLETED
            if finite
            else OptimizationStatus.NON_FINITE_LOSS,
        }
        for round_index, loss in enumerate(losses)
    ]
    schema = pl.Schema(
        {
            f"{Column.DOSE}": pl.Int64,
            f"{Column.PARAMETER}": pl.String,
            f"{Column.TUNING_VALUE}": pl.Float64,
            f"{Column.CLIENT}": pl.String,
            "epoch": pl.Int64,
            f"{Column.LOSS}": pl.Float64,
        }
    )
    write_table(pl.DataFrame(rows, schema_overrides=schema), paths.run_file(key, Artifact.TRAINING))
    summary = pl.DataFrame(
        {
            Column.LEARNER: ["fedavg"],
            Column.CONDITION: ["peer-present"],
            Column.DOSE: [None],
            Column.PARAMETER: [None],
            Column.TUNING_VALUE: [None],
            Column.ALPHA: [ALPHA],
            Column.METRIC: [Metric.CALIBRATION_AUROC],
            Column.VALUE: [0.9],
        },
        schema_overrides=schema,
    )
    write_table(summary, paths.run_metric_file(key, Artifact.SUMMARY))


def test_training_convergence_summarises_loss_trajectory_and_flags_non_finite_runs(
    tmp_path: Path,
) -> None:
    paths = Paths(tmp_path)
    _training(paths, [0.9, 0.6, 0.4], finite=True)
    table = training_convergence(paths, MODE, _index())
    row = table.row(0, named=True)
    assert row[Column.RECORDS] == 3
    assert row[Column.FIRST_LOSS] == 0.9
    assert row[Column.FINAL_LOSS] == 0.4
    assert row[Column.CALIBRATION_AUROC] == 0.9
    assert row[Column.PARAMETERS_FINITE]
    assert not row[Column.FLAGGED]

    _training(paths, [0.9, None], finite=False)
    broken = training_convergence(paths, MODE, _index()).row(0, named=True)
    assert broken[Column.FLAGGED]
    assert not broken[Column.PARAMETERS_FINITE]
    assert broken[Column.NONFINITE_BATCHES] == 4


def test_runs_without_a_training_record_are_left_out_not_invented(tmp_path: Path) -> None:
    assert training_convergence(Paths(tmp_path), MODE, _index()).is_empty()
