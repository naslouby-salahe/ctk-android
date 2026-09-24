import polars as pl
import pytest

from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    ExposureCondition,
    Learner,
    Metric,
    OperatingPointStatus,
)
from ctk_android.experiment.metrics import summarize
from ctk_android.types import ClientCountRow, DiscriminationRow, FamilyCountRow, OperatingRow

ALPHA = 0.05


def _count(
    client: ClientId, population: EvaluationPopulation, hits: int, trials: int
) -> ClientCountRow:
    return ClientCountRow(
        learner=Learner.CENTRAL,
        condition=ExposureCondition.PEER_PRESENT,
        dose=None,
        client=client,
        alpha=ALPHA,
        population=population,
        hits=hits,
        trials=trials,
    )


def _summary() -> pl.DataFrame:
    clients = records_to_frame(
        [
            _count(ClientId.ANZHI, EvaluationPopulation.FEDERATION_WIDE, 8, 10),
            _count(ClientId.APPCHINA, EvaluationPopulation.FEDERATION_WIDE, 4, 10),
            _count(ClientId.ANZHI, EvaluationPopulation.BENIGN, 5, 100),
            _count(ClientId.APPCHINA, EvaluationPopulation.BENIGN, 7, 100),
            _count(ClientId.ANZHI, EvaluationPopulation.KNOWN_FAMILY, 9, 10),
            _count(ClientId.ANZHI, EvaluationPopulation.OWN_DOMAIN, 3, 4),
        ]
    )
    families = records_to_frame(
        [
            FamilyCountRow(
                learner=Learner.CENTRAL,
                condition=ExposureCondition.PEER_PRESENT,
                dose=None,
                client=ClientId.ANZHI,
                alpha=ALPHA,
                population=EvaluationPopulation.FEDERATION_WIDE,
                family="alpha",
                hits=8,
                trials=10,
            )
        ]
    )
    operating = records_to_frame(
        [
            OperatingRow(
                learner=Learner.CENTRAL,
                condition=ExposureCondition.PEER_PRESENT,
                dose=None,
                client=client,
                alpha=ALPHA,
                threshold=0.0,
                calibration_benign=1000,
                operating_status=OperatingPointStatus.VALID,
            )
            for client in (ClientId.ANZHI, ClientId.APPCHINA)
        ]
    )
    discrimination = records_to_frame(
        [
            DiscriminationRow(
                learner=Learner.CENTRAL,
                condition=ExposureCondition.PEER_PRESENT,
                dose=None,
                client=ClientId.ANZHI,
                auroc=0.9,
                auprc=0.8,
            )
        ]
    )
    return summarize(clients, families, discrimination, operating, 1)


def _value(summary: pl.DataFrame, metric: Metric) -> float:
    return summary.filter(pl.col(Column.METRIC) == metric)[Column.VALUE].item()


def test_client_macro_worst_client_and_fpr_definitions() -> None:
    summary = _summary()
    assert _value(summary, Metric.FEDERATION_UNSEEN_RECALL) == pytest.approx(0.6)
    assert _value(summary, Metric.WORST_CLIENT_UNSEEN_RECALL) == pytest.approx(0.4)
    assert abs(_value(summary, Metric.WORST_CLIENT_FNR) - 0.6) < 1e-12
    assert abs(_value(summary, Metric.REALISED_FPR) - 0.06) < 1e-12
    assert _value(summary, Metric.WORST_CLIENT_FPR) == pytest.approx(0.07)


def test_own_domain_known_family_and_family_macro_definitions() -> None:
    summary = _summary()
    assert _value(summary, Metric.OWN_DOMAIN_UNSEEN_RECALL) == pytest.approx(0.75)
    assert _value(summary, Metric.KNOWN_FAMILY_RECALL) == pytest.approx(0.9)
    assert _value(summary, Metric.FAMILY_MACRO_UNSEEN_RECALL) == pytest.approx(0.8)
    assert _value(summary, Metric.AUROC) == pytest.approx(0.9)
