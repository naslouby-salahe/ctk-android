import copy
from dataclasses import dataclass

import numpy as np
import torch

from ctk_android.config import TrainingConfig
from ctk_android.enums import ClientId, Device, ErrorMessage, FailureReason, Learner, ModelFamily
from ctk_android.experiment.models import (
    StateDict,
    average_states,
    build_network,
    fit_epochs,
    fit_trees,
)
from ctk_android.types import (
    ByteMatrix,
    CtkError,
    Epochs,
    IntArray,
    ProximalAnchor,
    Scorer,
    Seed,
    TrainingRows,
)


@dataclass(frozen=True)
class TrainingContext:
    features: ByteMatrix
    labels: IntArray
    config: TrainingConfig
    family: ModelFamily
    device: Device
    seed: Seed


def derive_seed(base: Seed, *parts: Seed) -> Seed:
    return np.random.SeedSequence([base, *parts]).generate_state(1)[0].item()


def _require_both_classes(context: TrainingContext, rows: IntArray) -> None:
    counts = np.bincount(context.labels[rows], minlength=2)
    if counts.min() < context.config.min_rows_per_class:
        raise CtkError(
            FailureReason.INSUFFICIENT_CALIBRATION,
            ErrorMessage.CLASS_COUNTS.format(counts=counts.tolist()),
        )


def _initial_network(context: TrainingContext, stream: Seed) -> torch.nn.Module:
    torch.default_generator.manual_seed(derive_seed(context.seed, stream))
    return build_network(context.family, context.features.shape[1], context.config)


def train_scorer(context: TrainingContext, rows: IntArray, epochs: Epochs, stream: Seed) -> Scorer:
    _require_both_classes(context, rows)
    if context.family is ModelFamily.GRADIENT_BOOSTED_TREES:
        trees = fit_trees(
            context.features,
            context.labels,
            rows,
            context.config,
            derive_seed(context.seed, stream),
        )
        return Scorer(family=context.family, network=None, trees=trees, device=Device.CPU)
    network = _initial_network(context, stream)
    fit_epochs(
        network,
        context.features,
        context.labels,
        rows,
        epochs,
        context.config,
        derive_seed(context.seed, stream, 1),
        context.device,
        None,
    )
    return Scorer(family=context.family, network=network, trees=None, device=context.device)


def pooled_rows(training: TrainingRows) -> IntArray:
    return np.concatenate([training[client] for client in ClientId])


def train_federated(
    context: TrainingContext, training: TrainingRows, learner: Learner, stream: Seed
) -> Scorer:
    if context.family is ModelFamily.GRADIENT_BOOSTED_TREES:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.PARAMETRIC_ONLY)
    for client in ClientId:
        _require_both_classes(context, training[client])
    global_net = _initial_network(context, stream)
    weights = np.array([training[client].size for client in ClientId], dtype=np.float64)
    for round_index in range(context.config.federated_rounds):
        anchor = ProximalAnchor(
            state={k: v.detach().clone() for k, v in global_net.state_dict().items()},
            strength=context.config.fedprox_mu,
        )
        states: list[StateDict] = []
        for client_index, client in enumerate(ClientId):
            local = copy.deepcopy(global_net)
            fit_epochs(
                local,
                context.features,
                context.labels,
                training[client],
                context.config.federated_local_epochs,
                context.config,
                derive_seed(context.seed, stream, round_index, client_index),
                context.device,
                anchor if learner is Learner.FEDPROX else None,
            )
            states.append({k: v.detach().cpu() for k, v in local.state_dict().items()})
        global_net.load_state_dict(average_states(states, weights))
    return Scorer(family=context.family, network=global_net, trees=None, device=context.device)


def finetune(context: TrainingContext, scorer: Scorer, rows: IntArray, stream: Seed) -> Scorer:
    if scorer.network is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.FINETUNE_NETWORK)
    network = copy.deepcopy(scorer.network)
    fit_epochs(
        network,
        context.features,
        context.labels,
        rows,
        context.config.finetune_epochs,
        context.config,
        derive_seed(context.seed, stream),
        context.device,
        None,
    )
    return Scorer(family=context.family, network=network, trees=None, device=context.device)
