from pathlib import Path

import polars as pl
import pytest

from ctk_android.config import load_config
from ctk_android.enums import (
    Column,
    DiagnosticColumn,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    Metric,
    OperatingPointStatus,
    RunStatus,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    DiagnosticTable,
    RunIndexTable,
    ValidationDocument,
    ValidationRecord,
)
from ctk_android.workflows import report
from ctk_android.workflows.report import extension_b_diagnostic_experiments
from tests.architecture.source_index import REPO_ROOT


def test_extension_b_fpr_diagnostic_covers_all_extension_designs() -> None:
    config = load_config(Paths(REPO_ROOT))

    experiments = extension_b_diagnostic_experiments(config)

    assert len(experiments) == 12
    assert {
        ExperimentName.LARGE_FAMILY_SET_1,
        ExperimentName.LARGE_FAMILY_SET_2,
        ExperimentName.LARGE_FAMILY_SET_3,
        ExperimentName.LARGE_FAMILY_SET_4,
        ExperimentName.EXACT_EFFECTIVE_DOSE_PRIMARY,
        ExperimentName.EXACT_EFFECTIVE_DOSE_REPLICATION,
        ExperimentName.PLACEBO_ROBUST_PRIMARY,
        ExperimentName.PLACEBO_ROBUST_REPLICATION,
        ExperimentName.REPRESENTATION_R0,
        ExperimentName.REPRESENTATION_R1,
        ExperimentName.REPRESENTATION_R2,
        ExperimentName.REPRESENTATION_R3,
    } == set(experiments)


def test_fpr_exception_diagnostic_uses_validator_summary_and_retains_clients(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = load_config(Paths(REPO_ROOT))
    validation = ValidationDocument(
        validations=(
            ValidationRecord(
                check=ValidationCheck.OPERATING_POINT_REALISED,
                passed=False,
                detail="max |realised FPR - alpha| = 0.025",
            ),
        )
    )
    summary = pl.DataFrame(
        {
            Column.ALPHA: [0.05, 0.05, 0.05, 0.05],
            Column.METRIC: [Metric.REALISED_FPR] * 4,
            Column.OPERATING_STATUS: [
                OperatingPointStatus.VALID,
                OperatingPointStatus.VALID,
                OperatingPointStatus.VALID,
                OperatingPointStatus.INSUFFICIENT_EVIDENCE,
            ],
            Column.VALUE: [0.075, 0.07, 0.05, 0.9],
            Column.LEARNER: ["central", "fedavg", "local", "central"],
            Column.CONDITION: ["full-exposure", "peer-present", "peer-present", "bad"],
        }
    )
    clients = pl.DataFrame(
        {
            Column.ALPHA: [0.05] * 4,
            Column.POPULATION: [EvaluationPopulation.BENIGN] * 4,
            Column.TRIALS: [100] * 4,
            Column.HITS: [5, 6, 13, 7],
            Column.CLIENT: ["play-early", "play-late", "anzhi", "appchina"],
            Column.LEARNER: ["central"] * 4,
            Column.CONDITION: ["full-exposure"] * 4,
        }
    )
    monkeypatch.setattr(
        report,
        "read_record",
        lambda *_args: validation,
    )

    def read_metric(path: Path) -> pl.DataFrame:
        return summary if path.name == "summary.parquet" else clients

    monkeypatch.setattr(report.pl, "read_parquet", read_metric)
    index: RunIndexTable = pl.DataFrame(
        {
            Column.EXPERIMENT: [ExperimentName.REPRESENTATION_R0],
            Column.STATUS: [RunStatus.COMPLETED],
            Column.SEED: [333],
            Column.SALT: [0],
        }
    )

    result: DiagnosticTable = report.fpr_exceptions(Paths(tmp_path), config, index)

    assert result.height == 4
    assert result.get_column(DiagnosticColumn.MACRO_DEVIATION).unique().to_list() == pytest.approx(
        [0.025]
    )
    assert set(result.get_column(Column.CLIENT).to_list()) == {
        "play-early",
        "play-late",
        "anzhi",
        "appchina",
    }
    anzhi = result.filter(pl.col(Column.CLIENT) == "anzhi").row(0, named=True)
    assert anzhi[DiagnosticColumn.CLIENT_FPR] == pytest.approx(0.13)
    assert result.get_column(Column.EVIDENCE_CLASS).unique().to_list() == [
        EvidenceClass.POST_HOC_DIAGNOSTIC
    ]
