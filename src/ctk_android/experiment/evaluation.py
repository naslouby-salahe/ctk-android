from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.metrics import average_precision_score, roc_auc_score

from ctk_android.config import OperatingConfig
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    FamilyPopulation,
    Learner,
    SplitRole,
)
from ctk_android.experiment.models import scorer_logits
from ctk_android.experiment.thresholds import calibrate
from ctk_android.types import (
    ArmKey,
    ArmScores,
    BlendWeight,
    BoolArray,
    FamilyName,
    FloatArray,
    IntArray,
    OperatingPoint,
    Scorer,
    StudyData,
    TargetPair,
)


@dataclass(frozen=True)
class RowAttributes:
    labels: IntArray
    clients: np.ndarray
    roles: np.ndarray
    masks: dict[FamilyName, BoolArray]


@dataclass(frozen=True)
class ArmEvaluation:
    operating: pl.DataFrame
    clients: pl.DataFrame
    families: pl.DataFrame
    discrimination: pl.DataFrame


def row_attributes(study: StudyData, masks: dict[FamilyName, BoolArray]) -> RowAttributes:
    table = study.table
    return RowAttributes(
        labels=table[Column.LABEL].to_numpy().astype(np.int64),
        clients=table[Column.CLIENT].to_numpy(),
        roles=table[Column.ROLE].to_numpy(),
        masks=masks,
    )


def target_families(targets: tuple[TargetPair, ...], client: ClientId) -> tuple[FamilyName, ...]:
    return tuple(pair.family for pair in targets if pair.client is client)


def _unseen_mask(attributes: RowAttributes, families: tuple[FamilyName, ...]) -> BoolArray:
    mask = np.zeros(attributes.labels.size, dtype=bool)
    for family in families:
        mask |= attributes.masks[family]
    return mask


def build_pools(
    attributes: RowAttributes, targets: tuple[TargetPair, ...]
) -> dict[ClientId, IntArray]:
    pools: dict[ClientId, IntArray] = {}
    test = attributes.roles == SplitRole.TEST
    for client in ClientId:
        own = attributes.clients == client
        calibration = (
            own & (attributes.roles == SplitRole.CALIBRATION) & (attributes.labels == 0)
        )
        unseen = _unseen_mask(attributes, target_families(targets, client)) & test
        pools[client] = np.flatnonzero(calibration | (own & test) | unseen)
    return pools


def score_shared(scorer: Scorer, study: StudyData, pools: dict[ClientId, IntArray]) -> ArmScores:
    union = np.unique(np.concatenate(list(pools.values())))
    logits = scorer_logits(scorer, study.features, union)
    return {client: logits[np.searchsorted(union, rows)] for client, rows in pools.items()}


def score_per_client(
    scorers: dict[ClientId, Scorer], study: StudyData, pools: dict[ClientId, IntArray]
) -> ArmScores:
    return {
        client: scorer_logits(scorers[client], study.features, rows) for client, rows in pools.items()
    }


def blend_scores(local: ArmScores, shared: ArmScores, weight: BlendWeight) -> ArmScores:
    def sigmoid(values: FloatArray) -> FloatArray:
        return 1.0 / (1.0 + np.exp(-values))

    return {
        client: weight * sigmoid(local[client]) + (1.0 - weight) * sigmoid(shared[client])
        for client in local
    }


def _arm_columns(arm: ArmKey) -> dict[Column, object]:
    return {
        Column.LEARNER: arm.learner,
        Column.CONDITION: arm.condition,
        Column.DOSE: -1 if arm.dose is None else arm.dose,
    }


def evaluate_arm(
    arm: ArmKey,
    scores: ArmScores,
    pools: dict[ClientId, IntArray],
    attributes: RowAttributes,
    targets: tuple[TargetPair, ...],
    operating: OperatingConfig,
) -> ArmEvaluation:
    prefix = _arm_columns(arm)
    operating_rows: list[dict[Column, object]] = []
    client_rows: list[dict[Column, object]] = []
    family_rows: list[dict[Column, object]] = []
    discrimination_rows: list[dict[Column, object]] = []
    for client in ClientId:
        rows = pools[client]
        score = scores[client]
        labels = attributes.labels[rows]
        roles = attributes.roles[rows]
        own = attributes.clients[rows] == client
        families = target_families(targets, client)
        unseen = _unseen_mask(attributes, families)[rows]
        benign_cal = own & (roles == SplitRole.CALIBRATION) & (labels == 0)
        own_test = own & (roles == SplitRole.TEST)
        test = roles == SplitRole.TEST
        populations: dict[EvaluationPopulation, BoolArray] = {
            EvaluationPopulation.BENIGN: own_test & (labels == 0),
            EvaluationPopulation.KNOWN_FAMILY: own_test & (labels == 1) & ~unseen,
            EvaluationPopulation.OWN_DOMAIN: own_test & (labels == 1) & unseen,
            EvaluationPopulation.FEDERATION_WIDE: test & (labels == 1) & unseen,
        }
        if own_test.any() and len(np.unique(labels[own_test])) == 2:
            discrimination_rows.append(
                {
                    **prefix,
                    Column.CLIENT: client,
                    Column.POPULATION: EvaluationPopulation.DISCRIMINATION,
                    Column.RECALL: roc_auc_score(labels[own_test], score[own_test]),
                    Column.VALUE: average_precision_score(labels[own_test], score[own_test]),
                }
            )
        for alpha in operating.alphas:
            point: OperatingPoint = calibrate(score[benign_cal], alpha, operating.min_expected_exceedances)
            operating_rows.append(
                {
                    **prefix,
                    Column.CLIENT: client,
                    Column.ALPHA: alpha,
                    Column.THRESHOLD: point.threshold,
                    Column.CALIBRATION_BENIGN: point.calibration_benign,
                    Column.OPERATING_STATUS: point.status,
                }
            )
            flagged = score > point.threshold
            for population, mask in populations.items():
                client_rows.append(
                    {
                        **prefix,
                        Column.CLIENT: client,
                        Column.ALPHA: alpha,
                        Column.POPULATION: population,
                        Column.HITS: int((flagged & mask).sum()),
                        Column.TRIALS: int(mask.sum()),
                    }
                )
            for family in families:
                member = attributes.masks[family][rows]
                for population, base in (
                    (FamilyPopulation.OWN_DOMAIN, own_test),
                    (FamilyPopulation.FEDERATION_WIDE, test),
                ):
                    mask = base & member
                    family_rows.append(
                        {
                            **prefix,
                            Column.CLIENT: client,
                            Column.FAMILY: family,
                            Column.ALPHA: alpha,
                            Column.POPULATION: population,
                            Column.HITS: int((flagged & mask).sum()),
                            Column.TRIALS: int(mask.sum()),
                        }
                    )
    return ArmEvaluation(
        operating=pl.DataFrame(operating_rows),
        clients=pl.DataFrame(client_rows),
        families=pl.DataFrame(family_rows) if family_rows else pl.DataFrame(),
        discrimination=pl.DataFrame(discrimination_rows) if discrimination_rows else pl.DataFrame(),
    )


def learner_needs_local(learner: Learner) -> bool:
    return learner in (Learner.LOCAL, Learner.BLEND)
