import numpy as np
import polars as pl
from scipy import stats

from ctk_android.analysis.gates import frozen_family_set_experiments
from ctk_android.analysis.post_confirmatory import summarize_seeds
from ctk_android.config import Config
from ctk_android.data.cache import is_one_of, records_to_frame
from ctk_android.enums import (
    Column,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    FamilyOutcomeMeasure,
    FamilyPredictor,
    Learner,
    LibraryOption,
    StatisticsLimit,
    VarianceSource,
)
from ctk_android.types import (
    AssociationTable,
    Effect,
    FamilyAssociationRow,
    FamilyClientRow,
    FamilyClientTable,
    FamilyCountsTable,
    FamilyEffectsTable,
    FamilySeedTable,
    SeedEffects,
    SeedMatrix,
    VarianceRow,
    VarianceTable,
)


def _variance_rows(
    experiment: ExperimentName, learner: Learner, matrix: SeedMatrix
) -> list[VarianceRow]:
    families, seeds = matrix.shape
    grand = matrix.mean()
    total = ((matrix - grand) ** 2).sum()
    by_family = seeds * ((matrix.mean(axis=1) - grand) ** 2).sum()
    by_seed = families * ((matrix.mean(axis=0) - grand) ** 2).sum()
    parts = (
        (VarianceSource.FAMILY, by_family, families - 1),
        (VarianceSource.SEED, by_seed, seeds - 1),
        (VarianceSource.RESIDUAL, total - by_family - by_seed, (families - 1) * (seeds - 1)),
    )
    return [
        VarianceRow(
            evidence_class=EvidenceClass.POST_CONFIRMATORY,
            experiment=experiment,
            learner=learner,
            source=source,
            sum_squares=np.maximum(squares, 0.0).item(),
            degrees_of_freedom=degrees,
            share=np.maximum(squares, 0.0).item() / total.item() if total > 0 else 0.0,
        )
        for source, squares, degrees in parts
    ]


def _mean_or_zero(values: SeedEffects) -> Effect:
    return values.mean().item() if values.size else 0.0


def ctk_variance_components(family_seed: FamilySeedTable) -> VarianceTable:
    rows: list[VarianceRow] = []
    for experiment in frozen_family_set_experiments():
        per_pair = (
            family_seed.filter(
                (pl.col(Column.EXPERIMENT) == experiment)
                & (pl.col(Column.LEARNER) == Learner.FEDAVG)
            )
            .group_by(Column.FAMILY, Column.SEED)
            .agg(pl.col(Column.CTK_GAIN).mean())
        )
        if per_pair.height == 0:
            continue
        wide = per_pair.pivot(on=Column.SEED, index=Column.FAMILY, values=Column.CTK_GAIN)
        complete = wide.drop_nulls()
        if complete.height < 2 or complete.width <= 2:
            continue
        matrix = complete.drop(Column.FAMILY).to_numpy().astype(np.float64)
        rows.extend(_variance_rows(experiment, Learner.FEDAVG, matrix))
    return records_to_frame(rows)


def family_associations(family_effects: FamilyEffectsTable) -> AssociationTable:
    rows: list[FamilyAssociationRow] = []
    for experiment in frozen_family_set_experiments():
        fedavg = family_effects.filter(
            (pl.col(Column.EXPERIMENT) == experiment) & (pl.col(Column.LEARNER) == Learner.FEDAVG)
        )
        if fedavg.height < StatisticsLimit.ASSOCIATION_FAMILIES:
            continue
        local = fedavg[Column.LOCAL_RECALL].to_numpy()
        pooling = (fedavg[Column.ABSENT_RECALL] - fedavg[Column.LOCAL_RECALL]).to_numpy()
        total = (fedavg[Column.PEER_RECALL] - fedavg[Column.LOCAL_RECALL]).to_numpy()
        ctk = fedavg[Column.CTK_GAIN].to_numpy()
        for predictor, x in (
            (FamilyPredictor.LOCAL_RECALL, local),
            (FamilyPredictor.POOLING_GAIN, pooling),
        ):
            for outcome, y in (
                (FamilyOutcomeMeasure.CTK_GAIN, ctk),
                (FamilyOutcomeMeasure.TOTAL_GAIN, total),
            ):
                result = stats.spearmanr(x, y)
                if not np.isfinite(result.statistic):
                    continue
                rows.append(
                    FamilyAssociationRow(
                        evidence_class=EvidenceClass.POST_CONFIRMATORY,
                        experiment=experiment,
                        predictor=predictor,
                        outcome_measure=outcome,
                        rho=result.statistic.item(),
                        p_value=result.pvalue.item(),
                        families=fedavg.height,
                    )
                )
    return records_to_frame(rows)


def family_client_ctk(families: FamilyCountsTable, config: Config) -> FamilyClientTable:
    alpha = config.experiments.operating.primary_alpha
    own = families.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.ALPHA) == alpha)
        & (pl.col(Column.POPULATION) == EvaluationPopulation.OWN_DOMAIN)
        & pl.col(Column.DOSE).is_null()
        & (pl.col(Column.TRIALS) > 0)
        & is_one_of(Column.LEARNER, [Learner.LOCAL, Learner.FEDAVG])
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    if own.height == 0:
        return pl.DataFrame()

    def arm(learner: Learner, condition: ExposureCondition, name: Column) -> FamilyClientTable:
        return own.filter(
            (pl.col(Column.LEARNER) == learner) & (pl.col(Column.CONDITION) == condition)
        ).select(
            Column.SEED,
            Column.CLIENT,
            Column.FAMILY,
            pl.col(Column.RECALL).alias(name),
            pl.col(Column.TRIALS),
        )

    keys = [Column.SEED, Column.CLIENT, Column.FAMILY]
    wide = (
        arm(Learner.FEDAVG, ExposureCondition.PEER_PRESENT, Column.PEER_RECALL)
        .join(
            arm(
                Learner.FEDAVG, ExposureCondition.FAMILY_ABSENT_EVERYWHERE, Column.ABSENT_RECALL
            ).drop(Column.TRIALS),
            on=keys,
        )
        .join(
            arm(Learner.LOCAL, ExposureCondition.PEER_PRESENT, Column.LOCAL_RECALL).drop(
                Column.TRIALS
            ),
            on=keys,
            how=LibraryOption.JOIN_LEFT,
        )
        .sort(Column.SEED)
    )
    rows: list[FamilyClientRow] = []
    for group in wide.partition_by(Column.CLIENT, Column.FAMILY):
        head = group.row(0, named=True)
        peer = group[Column.PEER_RECALL].to_numpy()
        absent = group[Column.ABSENT_RECALL].to_numpy()
        summary = summarize_seeds(peer - absent, config.statistics)
        if summary is None:
            continue
        rows.append(
            FamilyClientRow(
                evidence_class=EvidenceClass.POST_CONFIRMATORY,
                experiment=ExperimentName.CONTROLLED_EXPOSURE,
                client=head[Column.CLIENT],
                family=head[Column.FAMILY],
                local_recall=_mean_or_zero(group[Column.LOCAL_RECALL].drop_nulls().to_numpy()),
                absent_recall=absent.mean().item(),
                peer_recall=peer.mean().item(),
                hidden_trials_per_seed=_mean_or_zero(group[Column.TRIALS].to_numpy()),
                **summary.model_dump(),
            )
        )
    return records_to_frame(rows).sort(Column.CLIENT, Column.FAMILY) if rows else pl.DataFrame()
