import polars as pl

from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    LibraryOption,
    Metric,
    OperatingPointStatus,
    SplitRole,
)
from ctk_android.types import (
    ClientCountsTable,
    DiscriminationTable,
    FamilyCountsTable,
    MetricTable,
    OperatingTable,
    RatesTable,
    SummaryTable,
    SupportCount,
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
