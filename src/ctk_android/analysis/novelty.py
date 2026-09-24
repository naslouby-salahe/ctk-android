import numpy as np
import polars as pl
from scipy import stats

from ctk_android.config import NoveltyConfig, StatisticsConfig
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    Column,
    EligibilityReason,
    NoveltyDescriptor,
    SplitRole,
    StatisticsLimit,
)
from ctk_android.types import (
    BoolArray,
    Correlation,
    DescriptorRow,
    FamilyName,
    FloatArray,
    Fraction,
    IntArray,
    Interval,
    NoveltyAssociation,
    Rate,
    Score,
    StudyData,
    TargetPair,
)


def _prevalence(study: StudyData, rows: IntArray) -> FloatArray:
    return np.asarray(study.features[rows], dtype=np.float64).mean(axis=0)


def _active(prevalence: FloatArray, threshold: Fraction) -> BoolArray:
    return prevalence >= threshold


def _jaccard(left: BoolArray, right: BoolArray) -> Rate:
    union = np.logical_or(left, right).sum().item()
    return 1.0 if union == 0 else np.logical_and(left, right).sum().item() / union


def _distance(left: FloatArray, right: FloatArray) -> Score:
    return np.linalg.norm(left - right).item()


def family_descriptors(
    study: StudyData,
    targets: tuple[TargetPair, ...],
    masks: dict[FamilyName, BoolArray],
    config: NoveltyConfig,
) -> pl.DataFrame:
    table = study.table
    fit = (table[Column.ROLE] == SplitRole.FIT).to_numpy()
    malware = (table[Column.LABEL] == 1).to_numpy()
    named = (table[Column.REASON] == EligibilityReason.ELIGIBLE).to_numpy()
    client = table[Column.CLIENT].to_numpy()
    family = table[Column.FAMILY].to_numpy()
    rows: list[DescriptorRow] = []
    for pair in targets:
        own = client == pair.client
        hidden = np.zeros(table.height, dtype=bool)
        for other in (p.family for p in targets if p.client is pair.client):
            hidden |= masks[other]
        peer_rows = np.flatnonzero(masks[pair.family] & fit & ~own)
        known_mask = own & fit & malware & ~hidden & ~masks[pair.family]
        known_rows = np.flatnonzero(known_mask)
        benign_rows = np.flatnonzero(own & fit & ~malware)
        if peer_rows.size == 0 or known_rows.size == 0 or benign_rows.size == 0:
            continue
        target = _prevalence(study, peer_rows)
        known_centroid = _prevalence(study, known_rows)
        target_active = _active(target, config.min_active_prevalence)
        distances: list[Score] = []
        jaccards: list[Rate] = []
        for name in np.unique(family[known_mask & named]):
            group = np.flatnonzero(known_mask & named & (family == name))
            if group.size < config.min_known_family_rows:
                continue
            centroid = _prevalence(study, group)
            distances.append(_distance(target, centroid))
            jaccards.append(
                _jaccard(target_active, _active(centroid, config.min_active_prevalence))
            )
        represented = np.logical_and(
            target_active, _active(known_centroid, config.min_active_prevalence)
        ).sum()
        values: dict[NoveltyDescriptor, Score] = {
            NoveltyDescriptor.CENTROID_DISTANCE_TO_KNOWN_MALWARE: _distance(target, known_centroid),
            NoveltyDescriptor.DISTANCE_TO_BENIGN_CENTROID: _distance(
                target, _prevalence(study, benign_rows)
            ),
            NoveltyDescriptor.FRACTION_ACTIVE_FEATURES_KNOWN: represented.item()
            / max(target_active.sum().item(), 1),
        }
        if distances:
            values[NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE] = min(distances)
            values[NoveltyDescriptor.MAX_JACCARD_TO_KNOWN_FAMILY] = max(jaccards)
        rows.extend(
            DescriptorRow(
                client=pair.client, family=pair.family, descriptor=descriptor, value=value
            )
            for descriptor, value in values.items()
        )
    return records_to_frame(rows)


def descriptor_by_family(novelty: pl.DataFrame, descriptor: NoveltyDescriptor) -> pl.DataFrame:
    return (
        novelty.filter(pl.col(Column.DESCRIPTOR) == descriptor)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.VALUE).mean().alias(Column.NOVELTY))
    )


def _rank_correlation(first: FloatArray, second: FloatArray) -> Correlation:
    return np.corrcoef(stats.rankdata(first), stats.rankdata(second))[0, 1].item()


def novelty_association(
    gains: FloatArray, scores: FloatArray, config: StatisticsConfig
) -> NoveltyAssociation | None:
    if gains.size < StatisticsLimit.ASSOCIATION_FAMILIES:
        return None
    result = stats.spearmanr(scores, gains)
    rng = np.random.default_rng(config.statistics_seed)
    picks = rng.integers(0, gains.size, size=(config.bootstrap_resamples, gains.size))
    resampled = np.array(
        [_rank_correlation(scores[pick], gains[pick]) for pick in picks], dtype=np.float64
    )
    resampled = resampled[np.isfinite(resampled)]
    tail = (1.0 - config.confidence_level) / 2.0
    interval = (
        Interval(
            low=np.quantile(resampled, tail).item(), high=np.quantile(resampled, 1.0 - tail).item()
        )
        if resampled.size
        else None
    )
    return NoveltyAssociation(
        rho=result.statistic.item(),
        p_value=result.pvalue.item(),
        interval=interval,
        families=gains.size,
    )
