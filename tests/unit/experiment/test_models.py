import numpy as np
import scipy.sparse as sp
import torch

from ctk_android.config import load_config
from ctk_android.enums import Aggregation, Device, ModelFamily
from ctk_android.experiment.models import (
    build_network,
    fit_epochs,
    fit_transform,
    fit_trees,
    model_inputs,
    resolve_device,
    robust_states,
    scorer_logits,
)
from ctk_android.paths import Paths
from ctk_android.types import AggregationRule, ProximalAnchor, Scorer, TransformRule
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT)).experiments.smoke_training
DEVICE = resolve_device(Device.CUDA)
FEATURES = 12
ROWS = 200
STRENGTH = 50.0
EPOCHS = 3
SEED = 4


def _data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    features = (rng.random((ROWS, FEATURES)) < 0.5).astype(np.uint8)
    labels = (features[:, 0] | features[:, 1]).astype(np.int64)
    return features, labels, np.arange(ROWS)


def _distance(anchor_state: dict[str, torch.Tensor], strength: float) -> float:
    features, labels, rows = _data()
    torch.default_generator.manual_seed(SEED)
    network = build_network(ModelFamily.MLP, FEATURES, CONFIG)
    network.load_state_dict(anchor_state)
    anchor = ProximalAnchor(state=anchor_state, strength=strength) if strength else None
    fit_epochs(network, features, labels, rows, EPOCHS, CONFIG, SEED, DEVICE, anchor, None)
    return sum(
        ((param.detach().cpu() - anchor_state[name].cpu()) ** 2).sum().item()
        for name, param in network.named_parameters()
    )


def test_fedprox_trains_on_the_configured_device_and_stays_closer_to_its_anchor() -> None:
    torch.default_generator.manual_seed(SEED)
    template = build_network(ModelFamily.MLP, FEATURES, CONFIG)
    anchor_state = {name: value.detach().clone() for name, value in template.state_dict().items()}
    free = _distance(anchor_state, 0.0)
    proximal = _distance(anchor_state, STRENGTH)
    assert proximal < free


def test_every_model_family_learns_a_separable_rule() -> None:
    features, labels, rows = _data()
    torch.default_generator.manual_seed(SEED)
    linear = build_network(ModelFamily.LINEAR, FEATURES, CONFIG)
    fit_epochs(linear, features, labels, rows, 30, CONFIG, SEED, DEVICE, None, None)
    mlp = build_network(ModelFamily.MLP, FEATURES, CONFIG)
    fit_epochs(mlp, features, labels, rows, 30, CONFIG, SEED, DEVICE, None, None)
    scorers = [
        Scorer(
            family=ModelFamily.LINEAR, network=linear, trees=None, device=DEVICE, transform=None
        ),
        Scorer(family=ModelFamily.MLP, network=mlp, trees=None, device=DEVICE, transform=None),
        Scorer(
            family=ModelFamily.GRADIENT_BOOSTED_TREES,
            network=None,
            trees=fit_trees(features, labels, rows, CONFIG, SEED, None),
            device=DEVICE,
            transform=None,
        ),
    ]
    for scorer in scorers:
        logits = scorer_logits(scorer, features, rows)
        assert logits[labels == 1].mean() > logits[labels == 0].mean()


def _states(values: list[float]) -> list[dict[str, torch.Tensor]]:
    return [{"w": torch.tensor([value, -value])} for value in values]


def test_trimmed_mean_drops_the_extreme_client_on_each_side_per_coordinate() -> None:
    rule = AggregationRule(rule=Aggregation.TRIMMED_MEAN, trim_per_side=1)
    merged = robust_states(_states([1.0, 2.0, 4.0, 100.0]), rule)
    assert torch.allclose(merged["w"], torch.tensor([3.0, -3.0]))


def test_coordinate_median_is_robust_to_a_single_outlier_and_takes_the_lower_middle() -> None:
    rule = AggregationRule(rule=Aggregation.COORDINATE_MEDIAN, trim_per_side=1)
    merged = robust_states(_states([1.0, 2.0, 4.0, 100.0]), rule)
    assert torch.allclose(merged["w"], torch.tensor([2.0, -4.0]))


def test_robust_aggregation_keeps_the_state_dtype_and_names() -> None:
    rule = AggregationRule(rule=Aggregation.TRIMMED_MEAN, trim_per_side=1)
    states = [{"n": torch.tensor([value], dtype=torch.int64)} for value in (1, 2, 3, 4)]
    merged = robust_states(states, rule)
    assert merged["n"].dtype == torch.int64
    assert set(merged) == {"n"}


def test_fitted_transforms_use_only_the_given_training_rows() -> None:
    dense = np.random.default_rng(3).random((40, 5)).astype(np.float32)
    dense[:, 3] = 0.0
    dense[30:, 3] = 1.0
    matrix = sp.csr_matrix(dense)
    rows = np.arange(30)
    rule = TransformRule(min_prevalence=None)
    transform = fit_transform(matrix, rows, rule)
    np.testing.assert_allclose(transform.mean, dense[rows].mean(axis=0), rtol=1e-5, atol=1e-7)
    shifted = dense.copy()
    shifted[30:] = 99.0
    again = fit_transform(sp.csr_matrix(shifted), rows, rule)
    np.testing.assert_allclose(again.mean, transform.mean)
    np.testing.assert_allclose(again.spread, transform.spread)
    standard = model_inputs(matrix, rows, transform)
    np.testing.assert_allclose(standard[:, [0, 1, 2, 4]].mean(axis=0), 0.0, atol=1e-5)


def test_prevalence_selection_is_fitted_on_the_training_rows() -> None:
    dense = np.zeros((10, 3), dtype=np.float32)
    dense[:5, 0] = 1.0
    dense[:1, 1] = 1.0
    dense[5:, 2] = 1.0
    matrix = sp.csr_matrix(dense)
    selected = fit_transform(matrix, np.arange(5), TransformRule(min_prevalence=0.5))
    assert selected.columns is not None and selected.columns.tolist() == [0]
    assert model_inputs(matrix, np.arange(10), selected).shape == (10, 1)
    everyone = fit_transform(matrix, np.arange(10), TransformRule(min_prevalence=0.5))
    assert everyone.columns is not None and everyone.columns.tolist() == [0, 2]
