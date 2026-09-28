import numpy as np
import polars as pl
import pytest

from ctk_android.analysis.extensions import descriptor_by_family, novelty_association
from ctk_android.config import load_config
from ctk_android.enums import Column, NoveltyDescriptor
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT)).statistics


def test_a_monotone_relation_has_unit_rank_correlation() -> None:
    scores = np.arange(8, dtype=np.float64)
    result = novelty_association(scores * 0.01, scores, CONFIG)
    assert result is not None
    assert result.rho == pytest.approx(1.0)
    assert result.families == 8


def test_an_unrelated_score_has_an_interval_spanning_zero() -> None:
    rng = np.random.default_rng(5)
    result = novelty_association(rng.normal(size=12), rng.normal(size=12), CONFIG)
    assert result is not None
    assert result.interval is not None
    assert result.interval.low < 0 < result.interval.high


def test_too_few_families_cannot_be_associated() -> None:
    assert novelty_association(np.array([0.1, 0.2]), np.array([1.0, 2.0]), CONFIG) is None


def test_family_scores_are_ordered_by_family_so_association_intervals_are_reproducible() -> None:
    frame = pl.DataFrame(
        {
            Column.CLIENT: ["b", "a", "a", "b"],
            Column.FAMILY: ["zeta", "zeta", "alpha", "alpha"],
            Column.DESCRIPTOR: [NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE] * 4,
            Column.VALUE: [1.0, 2.0, 3.0, 4.0],
        }
    )
    scores = descriptor_by_family(frame, NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE)
    assert scores[Column.FAMILY].to_list() == ["alpha", "zeta"]
