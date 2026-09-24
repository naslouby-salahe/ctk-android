import numpy as np
import torch

from ctk_android.config import load_config
from ctk_android.enums import Device, ModelFamily
from ctk_android.experiment.models import (
    build_network,
    fit_epochs,
    fit_trees,
    resolve_device,
    scorer_logits,
)
from ctk_android.paths import Paths
from ctk_android.types import ProximalAnchor, Scorer
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
    fit_epochs(network, features, labels, rows, EPOCHS, CONFIG, SEED, DEVICE, anchor)
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
    fit_epochs(linear, features, labels, rows, 30, CONFIG, SEED, DEVICE, None)
    mlp = build_network(ModelFamily.MLP, FEATURES, CONFIG)
    fit_epochs(mlp, features, labels, rows, 30, CONFIG, SEED, DEVICE, None)
    scorers = [
        Scorer(family=ModelFamily.LINEAR, network=linear, trees=None, device=DEVICE),
        Scorer(family=ModelFamily.MLP, network=mlp, trees=None, device=DEVICE),
        Scorer(
            family=ModelFamily.GRADIENT_BOOSTED_TREES,
            network=None,
            trees=fit_trees(features, labels, rows, CONFIG, SEED),
            device=DEVICE,
        ),
    ]
    for scorer in scorers:
        logits = scorer_logits(scorer, features, rows)
        assert logits[labels == 1].mean() > logits[labels == 0].mean()
