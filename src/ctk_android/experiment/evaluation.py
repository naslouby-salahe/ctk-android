from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.metrics import average_precision_score, roc_auc_score

from ctk_android.config import OperatingConfig
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    ClientId,
    Column,
    EvaluationPopulation,
    LibraryOption,
    Metric,
    OperatingPointStatus,
    SplitRole,
)
from ctk_android.experiment.models import scorer_logits
from ctk_android.types import (
    Alpha,
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
    ExceedanceCount,
    FamilyCountRow,
    FamilyCountsTable,
    FamilyMasks,
    FamilyName,
    LabelVector,
    LogitVector,
    MetricTable,
    OperatingPoint,
    OperatingRow,
    OperatingTable,
    PopulationMasks,
    RatesTable,
    RowIndices,
    RowMask,
    Scorer,
    ScoreVector,
    StudyData,
    SummaryTable,
    SupportCount,
    TargetPair,
)


@dataclass(frozen=True)
class RowAttributes:
    labels: LabelVector
    clients: AttributeColumn
    roles: AttributeColumn
    feature_ids: AttributeColumn
    masks: FamilyMasks


@dataclass(frozen=True)
class ArmEvaluation:
    operating: OperatingTable
    clients: ClientCountsTable
    families: FamilyCountsTable
    discrimination: DiscriminationTable
    hidden_rows: RowIndices


def row_attributes(study: StudyData, masks: FamilyMasks) -> RowAttributes:
    table = study.table
    return RowAttributes(
        labels=table[Column.LABEL].to_numpy().astype(np.int64),
        clients=table[Column.CLIENT].to_numpy(),
        roles=table[Column.ROLE].to_numpy(),
        feature_ids=table[Column.FEATURE_ID].to_numpy(),
        masks=masks,
    )


def target_families(targets: tuple[TargetPair, ...], client: ClientId) -> tuple[FamilyName, ...]:
    return tuple(pair.family for pair in targets if pair.client is client)


def _unseen_mask(attributes: RowAttributes, families: tuple[FamilyName, ...]) -> RowMask:
    mask = np.zeros(attributes.labels.size, dtype=bool)
    for family in families:
        mask |= attributes.masks[family]
    return mask


def first_occurrence(mask: RowMask, feature_ids: AttributeColumn) -> RowMask:
    first = np.zeros(mask.size, dtype=bool)
    rows = np.flatnonzero(mask)
    _, position = np.unique(feature_ids[rows], return_index=True)
    first[rows[position]] = True
    return first


def build_pools(attributes: RowAttributes, targets: tuple[TargetPair, ...]) -> ClientPools:
    pools: ClientPools = {}
    test = attributes.roles == SplitRole.TEST
    for client in ClientId:
        own = attributes.clients == client
        calibration = own & (attributes.roles == SplitRole.CALIBRATION)
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


def _discrimination(
    arm: ArmKey, client: ClientId, split: SplitRole, labels: LabelVector, score: ScoreVector
) -> list[DiscriminationRow]:
    if len(np.unique(labels)) < 2:
        return []
    return [
        DiscriminationRow(
            **arm.columns().model_dump(),
            client=client,
            split=split,
            auroc=np.asarray(roc_auc_score(labels, score)).item(),
            auprc=np.asarray(average_precision_score(labels, score)).item(),
        )
    ]


def evaluate_arm(
    arm: ArmKey,
    scores: ArmScores,
    pools: ClientPools,
    attributes: RowAttributes,
    targets: tuple[TargetPair, ...],
    operating: OperatingConfig,
) -> ArmEvaluation:
    base = arm.columns().model_dump()
    operating_rows: list[OperatingRow] = []
    client_rows: list[ClientCountRow] = []
    family_rows: list[FamilyCountRow] = []
    discrimination_rows: list[DiscriminationRow] = []
    hidden_used: list[RowIndices] = []
    for client in ClientId:
        rows = pools[client]
        score = scores[client]
        labels = attributes.labels[rows]
        roles = attributes.roles[rows]
        own = attributes.clients[rows] == client
        families = target_families(targets, client)
        unseen = _unseen_mask(attributes, families)[rows]
        benign_cal = own & (roles == SplitRole.CALIBRATION) & (labels == 0)
        own_calibration = own & (roles == SplitRole.CALIBRATION)
        own_test = own & (roles == SplitRole.TEST)
        test = roles == SplitRole.TEST
        populations: PopulationMasks = {
            EvaluationPopulation.BENIGN: own_test & (labels == 0),
            EvaluationPopulation.KNOWN_FAMILY: own_test & (labels == 1) & ~unseen,
            EvaluationPopulation.OWN_DOMAIN: own_test & (labels == 1) & unseen,
            EvaluationPopulation.FEDERATION_WIDE: test & (labels == 1) & unseen,
        }
        hidden_used.append(
            rows[
                populations[EvaluationPopulation.OWN_DOMAIN]
                | populations[EvaluationPopulation.FEDERATION_WIDE]
            ]
        )
        discrimination_rows += _discrimination(
            arm, client, SplitRole.TEST, labels[own_test], score[own_test]
        )
        discrimination_rows += _discrimination(
            arm, client, SplitRole.CALIBRATION, labels[own_calibration], score[own_calibration]
        )
        for alpha in operating.alphas:
            point = calibrate(score[benign_cal], alpha, operating.min_expected_exceedances)
            operating_rows.append(
                OperatingRow(
                    **base,
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
                    **base,
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
                for population, scope in (
                    (EvaluationPopulation.OWN_DOMAIN, own_test),
                    (EvaluationPopulation.FEDERATION_WIDE, test),
                ):
                    mask = scope & member
                    unique = first_occurrence(mask, attributes.feature_ids[rows])
                    family_rows.append(
                        FamilyCountRow(
                            **base,
                            client=client,
                            alpha=alpha,
                            population=population,
                            family=family,
                            hits=(flagged & mask).sum().item(),
                            trials=mask.sum().item(),
                            unique_hits=(flagged & unique).sum().item(),
                            unique_trials=unique.sum().item(),
                        )
                    )
    return ArmEvaluation(
        operating=records_to_frame(operating_rows),
        clients=records_to_frame(client_rows),
        families=records_to_frame(family_rows),
        discrimination=records_to_frame(discrimination_rows),
        hidden_rows=np.concatenate(hidden_used),
    )


def calibrate(
    benign_scores: ScoreVector, alpha: Alpha, min_exceedances: ExceedanceCount
) -> OperatingPoint:
    count = benign_scores.size
    if count == 0:
        return OperatingPoint(
            threshold=0.0,
            calibration_benign=0,
            status=OperatingPointStatus.INSUFFICIENT_EVIDENCE,
        )
    threshold = np.quantile(benign_scores, 1.0 - alpha, method=LibraryOption.QUANTILE_HIGHER).item()
    resolved = count * alpha >= min_exceedances
    return OperatingPoint(
        threshold=threshold,
        calibration_benign=count,
        status=OperatingPointStatus.VALID
        if resolved
        else OperatingPointStatus.INSUFFICIENT_EVIDENCE,
    )


def arm_columns() -> list[Column]:
    return [Column.LEARNER, Column.CONDITION, Column.DOSE, Column.PARAMETER, Column.TUNING_VALUE]


def group_columns() -> list[Column]:
    return [*arm_columns(), Column.ALPHA]


def _rates(
    table: ClientCountsTable, population: EvaluationPopulation, minimum: SupportCount
) -> RatesTable:
    return (
        table.filter(
            (pl.col(Column.POPULATION) == population) & (pl.col(Column.TRIALS) >= max(minimum, 1))
        )
        .with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        .select(*group_columns(), Column.CLIENT, Column.RECALL)
    )


def _long(frame: RatesTable, metric: Metric, expression: pl.Expr) -> MetricTable:
    return (
        frame.group_by(group_columns())
        .agg(expression.alias(Column.VALUE))
        .with_columns(pl.lit(metric).alias(Column.METRIC))
    )


def _spread(expression: pl.Expr) -> pl.Expr:
    return expression.std(ddof=0).fill_null(0.0)


def summarize(
    clients: ClientCountsTable,
    families: FamilyCountsTable,
    discrimination: DiscriminationTable,
    operating: OperatingTable,
    own_domain_min: SupportCount,
) -> SummaryTable:
    recall = pl.col(Column.RECALL)
    parts: list[MetricTable] = []
    own = _rates(clients, EvaluationPopulation.OWN_DOMAIN, own_domain_min)
    parts.append(_long(own, Metric.OWN_DOMAIN_UNSEEN_RECALL, recall.mean()))
    federation = _rates(clients, EvaluationPopulation.FEDERATION_WIDE, 1)
    parts.append(_long(federation, Metric.FEDERATION_UNSEEN_RECALL, recall.mean()))
    parts.append(_long(federation, Metric.WORST_CLIENT_UNSEEN_RECALL, recall.min()))
    parts.append(_long(federation, Metric.WORST_CLIENT_FNR, (1.0 - recall).max()))
    parts.append(_long(federation, Metric.CLIENT_RECALL_DISPERSION, _spread(recall)))
    known = _rates(clients, EvaluationPopulation.KNOWN_FAMILY, 1)
    parts.append(_long(known, Metric.KNOWN_FAMILY_RECALL, recall.mean()))
    fpr = _rates(
        clients.filter(pl.col(Column.POPULATION) == EvaluationPopulation.BENIGN).with_columns(
            pl.lit(EvaluationPopulation.OWN_DOMAIN).alias(Column.POPULATION)
        ),
        EvaluationPopulation.OWN_DOMAIN,
        1,
    )
    parts.append(_long(fpr, Metric.REALISED_FPR, recall.mean()))
    parts.append(_long(fpr, Metric.WORST_CLIENT_FPR, recall.max()))
    parts.append(_long(fpr, Metric.FPR_DISPERSION, _spread(recall)))
    if families.height:
        fed_families = families.filter(
            (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
            & (pl.col(Column.TRIALS) > 0)
        ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
        parts.append(_long(fed_families, Metric.FAMILY_MACRO_UNSEEN_RECALL, recall.mean()))
        parts.append(_long(fed_families, Metric.FAMILY_RECALL_DISPERSION, _spread(recall)))
        parts.append(
            _long(
                fed_families,
                Metric.MICRO_UNSEEN_RECALL,
                pl.col(Column.HITS).sum() / pl.col(Column.TRIALS).sum(),
            )
        )
    if discrimination.height:
        alphas = clients.select(Column.ALPHA).unique()
        for split, column, metric in (
            (SplitRole.TEST, Column.AUROC, Metric.AUROC),
            (SplitRole.TEST, Column.AUPRC, Metric.AUPRC),
            (SplitRole.CALIBRATION, Column.AUROC, Metric.CALIBRATION_AUROC),
        ):
            macro = (
                discrimination.filter(pl.col(Column.SPLIT) == split)
                .group_by(arm_columns())
                .agg(pl.col(column).mean().alias(Column.VALUE))
            )
            parts.append(
                macro.join(alphas, how=LibraryOption.JOIN_CROSS).with_columns(
                    pl.lit(metric).alias(Column.METRIC)
                )
            )
    status = operating.group_by(group_columns()).agg(
        pl.when(
            (pl.col(Column.OPERATING_STATUS) == OperatingPointStatus.INSUFFICIENT_EVIDENCE).any()
        )
        .then(pl.lit(OperatingPointStatus.INSUFFICIENT_EVIDENCE))
        .otherwise(pl.lit(OperatingPointStatus.VALID))
        .alias(Column.OPERATING_STATUS)
    )
    wanted = [*group_columns(), Column.METRIC, Column.VALUE]
    return (
        pl.concat([part.select(wanted) for part in parts])
        .join(status, on=group_columns(), how=LibraryOption.JOIN_LEFT, nulls_equal=True)
        .sort([*group_columns(), Column.METRIC])
    )
