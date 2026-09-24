import numpy as np
import pytest

from ctk_android.analysis.statistics import (
    bca_interval,
    cluster_bootstrap_difference,
    exact_wilcoxon,
    holm_adjust,
    paired_effect,
    ratio_interval,
)
from ctk_android.config import load_config
from ctk_android.paths import Paths
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT)).statistics
RNG = np.random.default_rng(0)
DIFFERENCES = RNG.normal(0.05, 0.02, size=10)
LEVEL = 0.95


def test_paired_effect_reports_mean_median_and_positive_seeds() -> None:
    effect = paired_effect(DIFFERENCES, CONFIG)
    assert effect.mean == pytest.approx(DIFFERENCES.mean())
    assert effect.median == pytest.approx(np.median(DIFFERENCES))
    assert effect.positive_seeds == (DIFFERENCES > 0).sum()
    assert effect.seeds == DIFFERENCES.size
    assert effect.effect_size == pytest.approx(DIFFERENCES.mean() / DIFFERENCES.std(ddof=1))


def test_bca_interval_brackets_the_mean_and_is_deterministic() -> None:
    interval = bca_interval(DIFFERENCES, CONFIG)
    assert interval is not None
    assert interval.low < DIFFERENCES.mean() < interval.high
    assert interval == bca_interval(DIFFERENCES, CONFIG)


def test_bca_interval_is_unavailable_for_too_few_seeds() -> None:
    assert bca_interval(np.array([0.1, 0.2]), CONFIG) is None


def test_exact_wilcoxon_matches_the_closed_form_for_all_positive_differences() -> None:
    assert exact_wilcoxon(np.arange(1.0, 11.0)) == pytest.approx(2 / 2**10)


def test_wilcoxon_of_zero_differences_carries_no_evidence() -> None:
    assert exact_wilcoxon(np.zeros(10)) == 1.0


def test_holm_matches_the_step_down_definition() -> None:
    adjusted = holm_adjust(np.array([0.01, 0.04, 0.03]))
    assert adjusted == pytest.approx([0.03, 0.06, 0.06])


def test_ratio_interval_recovers_a_known_ratio() -> None:
    denominator = RNG.uniform(0.04, 0.06, size=10)
    noisy = 2.0 * denominator + RNG.normal(0.0, 0.002, size=10)
    interval = ratio_interval(noisy, denominator, 0.01, CONFIG)
    assert interval is not None
    assert interval.low <= 2.0 <= interval.high


def test_ratio_is_not_reported_when_the_denominator_is_negligible() -> None:
    assert ratio_interval(DIFFERENCES, np.full(10, 1e-6), 0.01, CONFIG) is None


def test_cluster_bootstrap_detects_a_real_difference_and_a_null() -> None:
    groups = np.repeat(np.arange(200), 5)
    trials = np.ones(1000, dtype=np.int64)
    strong = (RNG.random(1000) < 0.9).astype(np.int64)
    weak = (RNG.random(1000) < 0.4).astype(np.int64)
    separated = cluster_bootstrap_difference(strong, weak, trials, groups, 500, 1, LEVEL)
    null = cluster_bootstrap_difference(strong, strong, trials, groups, 500, 1, LEVEL)
    assert separated is not None
    assert null is not None
    assert separated.low > 0
    assert null.low <= 0 <= null.high
