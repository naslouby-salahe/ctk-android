import numpy as np
import polars as pl

from ctk_android.config import NoveltyConfig
from ctk_android.enums import Column, EligibilityReason, NoveltyDescriptor, SplitRole
from ctk_android.types import BoolArray, FamilyName, FloatArray, StudyData, TargetPair


def _prevalence(study: StudyData, rows: np.ndarray) -> FloatArray:
    return np.asarray(study.features[rows], dtype=np.float64).mean(axis=0)


def _active(prevalence: FloatArray, threshold: float) -> BoolArray:
    return prevalence >= threshold


def _jaccard(left: BoolArray, right: BoolArray) -> float:
    union = np.logical_or(left, right).sum()
    return 1.0 if union == 0 else np.logical_and(left, right).sum() / union


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
    rows: list[dict[Column, object]] = []
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
        benign_centroid = _prevalence(study, benign_rows)
        target_active = _active(target, config.min_active_prevalence)
        distances: list[float] = []
        jaccards: list[float] = []
        for name in np.unique(family[known_mask & named]):
            group = np.flatnonzero(known_mask & named & (family == name))
            if group.size < config.min_known_family_rows:
                continue
            centroid = _prevalence(study, group)
            distances.append(np.linalg.norm(target - centroid))
            jaccards.append(_jaccard(target_active, _active(centroid, config.min_active_prevalence)))
        values: dict[NoveltyDescriptor, float] = {
            NoveltyDescriptor.CENTROID_DISTANCE_TO_KNOWN_MALWARE: np.linalg.norm(target - known_centroid),
            NoveltyDescriptor.DISTANCE_TO_BENIGN_CENTROID: np.linalg.norm(target - benign_centroid),
            NoveltyDescriptor.FRACTION_ACTIVE_FEATURES_KNOWN: (
                np.logical_and(target_active, _active(known_centroid, config.min_active_prevalence)).sum()
                / max(target_active.sum(), 1)
            ),
        }
        if distances:
            values[NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE] = min(distances)
            values[NoveltyDescriptor.MAX_JACCARD_TO_KNOWN_FAMILY] = max(jaccards)
        rows.extend(
            {
                Column.CLIENT: pair.client,
                Column.FAMILY: pair.family,
                Column.DESCRIPTOR: descriptor,
                Column.VALUE: value,
            }
            for descriptor, value in values.items()
        )
    return pl.DataFrame(
        rows,
        schema={
            Column.CLIENT: pl.String,
            Column.FAMILY: pl.String,
            Column.DESCRIPTOR: pl.String,
            Column.VALUE: pl.Float64,
        },
    )
