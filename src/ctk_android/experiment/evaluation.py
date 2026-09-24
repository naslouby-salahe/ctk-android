from dataclasses import dataclass

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from ctk_android.config import OperatingConfig
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    SplitRole,
)
from ctk_android.experiment.models import scorer_logits
from ctk_android.experiment.thresholds import calibrate
from ctk_android.types import (
    ArmKey,
    ArmScores,
    AttributeColumn,
    BlendWeight,
    ClientCountRow,
    ClientCountsTable,
    ClientPools,
    ClientScorers,
    DiscriminationRow,
    DiscriminationTable,
    FamilyCountRow,
    FamilyCountsTable,
    FamilyMasks,
    FamilyName,
    LabelVector,
    LogitVector,
    OperatingRow,
    OperatingTable,
    PopulationMasks,
    RowMask,
    Scorer,
    ScoreVector,
    StudyData,
    TargetPair,
)


@dataclass(frozen=True)
class RowAttributes:
    labels: LabelVector
    clients: AttributeColumn
    roles: AttributeColumn
    masks: FamilyMasks


@dataclass(frozen=True)
class ArmEvaluation:
    operating: OperatingTable
    clients: ClientCountsTable
    families: FamilyCountsTable
    discrimination: DiscriminationTable


def row_attributes(study: StudyData, masks: FamilyMasks) -> RowAttributes:
    table = study.table
    return RowAttributes(
        labels=table[Column.LABEL].to_numpy().astype(np.int64),
        clients=table[Column.CLIENT].to_numpy(),
        roles=table[Column.ROLE].to_numpy(),
        masks=masks,
    )


def target_families(targets: tuple[TargetPair, ...], client: ClientId) -> tuple[FamilyName, ...]:
    return tuple(pair.family for pair in targets if pair.client is client)


def _unseen_mask(attributes: RowAttributes, families: tuple[FamilyName, ...]) -> RowMask:
    mask = np.zeros(attributes.labels.size, dtype=bool)
    for family in families:
        mask |= attributes.masks[family]
    return mask


def build_pools(attributes: RowAttributes, targets: tuple[TargetPair, ...]) -> ClientPools:
    pools: ClientPools = {}
    test = attributes.roles == SplitRole.TEST
    for client in ClientId:
        own = attributes.clients == client
        calibration = own & (attributes.roles == SplitRole.CALIBRATION) & (attributes.labels == 0)
        unseen = _unseen_mask(attributes, target_families(targets, client)) & test
        pools[client] = np.flatnonzero(calibration | (own & test) | unseen)
    return pools


def score_shared(scorer: Scorer, study: StudyData, pools: ClientPools) -> ArmScores:
    union = np.unique(np.concatenate(list(pools.values())))
    logits = scorer_logits(scorer, study.features, union)
    return {client: logits[np.searchsorted(union, rows)] for client, rows in pools.items()}


def score_per_client(scorers: ClientScorers, study: StudyData, pools: ClientPools) -> ArmScores:
    return {
        client: scorer_logits(scorers[client], study.features, rows)
        for client, rows in pools.items()
    }


def blend_scores(local: ArmScores, shared: ArmScores, weight: BlendWeight) -> ArmScores:
    def sigmoid(values: LogitVector) -> ScoreVector:
        return 1.0 / (1.0 + np.exp(-values))

    return {
        client: weight * sigmoid(local[client]) + (1.0 - weight) * sigmoid(shared[client])
        for client in local
    }


def evaluate_arm(
    arm: ArmKey,
    scores: ArmScores,
    pools: ClientPools,
    attributes: RowAttributes,
    targets: tuple[TargetPair, ...],
    operating: OperatingConfig,
) -> ArmEvaluation:
    operating_rows: list[OperatingRow] = []
    client_rows: list[ClientCountRow] = []
    family_rows: list[FamilyCountRow] = []
    discrimination_rows: list[DiscriminationRow] = []
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
        populations: PopulationMasks = {
            EvaluationPopulation.BENIGN: own_test & (labels == 0),
            EvaluationPopulation.KNOWN_FAMILY: own_test & (labels == 1) & ~unseen,
            EvaluationPopulation.OWN_DOMAIN: own_test & (labels == 1) & unseen,
            EvaluationPopulation.FEDERATION_WIDE: test & (labels == 1) & unseen,
        }
        if own_test.any() and len(np.unique(labels[own_test])) == 2:
            discrimination_rows.append(
                DiscriminationRow(
                    learner=arm.learner,
                    condition=arm.condition,
                    dose=arm.dose,
                    client=client,
                    auroc=np.asarray(roc_auc_score(labels[own_test], score[own_test])).item(),
                    auprc=np.asarray(
                        average_precision_score(labels[own_test], score[own_test])
                    ).item(),
                )
            )
        for alpha in operating.alphas:
            point = calibrate(score[benign_cal], alpha, operating.min_expected_exceedances)
            operating_rows.append(
                OperatingRow(
                    learner=arm.learner,
                    condition=arm.condition,
                    dose=arm.dose,
                    client=client,
                    alpha=alpha,
                    threshold=point.threshold,
                    calibration_benign=point.calibration_benign,
                    operating_status=point.status,
                )
            )
            flagged = score > point.threshold
            client_rows.extend(
                ClientCountRow(
                    learner=arm.learner,
                    condition=arm.condition,
                    dose=arm.dose,
                    client=client,
                    alpha=alpha,
                    population=population,
                    hits=(flagged & mask).sum().item(),
                    trials=mask.sum().item(),
                )
                for population, mask in populations.items()
            )
            for family in families:
                member = attributes.masks[family][rows]
                for population, base in (
                    (EvaluationPopulation.OWN_DOMAIN, own_test),
                    (EvaluationPopulation.FEDERATION_WIDE, test),
                ):
                    mask = base & member
                    family_rows.append(
                        FamilyCountRow(
                            learner=arm.learner,
                            condition=arm.condition,
                            dose=arm.dose,
                            client=client,
                            alpha=alpha,
                            population=population,
                            family=family,
                            hits=(flagged & mask).sum().item(),
                            trials=mask.sum().item(),
                        )
                    )
    return ArmEvaluation(
        operating=records_to_frame(operating_rows),
        clients=records_to_frame(client_rows),
        families=records_to_frame(family_rows),
        discrimination=records_to_frame(discrimination_rows),
    )
