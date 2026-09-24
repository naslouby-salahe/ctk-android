import numpy as np
import pytest

from ctk_android.analysis.novelty import novelty_association
from ctk_android.config import load_config
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
