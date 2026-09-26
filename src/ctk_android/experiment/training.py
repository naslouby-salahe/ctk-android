import copy
from dataclasses import dataclass

import numpy as np
import torch

from ctk_android import logs
from ctk_android.config import TrainingConfig
from ctk_android.enums import (
    ClientId,
    Device,
    ErrorMessage,
    FailureReason,
    Learner,
    LogEvent,
    LogField,
    ModelFamily,
)
from ctk_android.experiment.models import (
    StateDict,
    average_states,
    build_network,
    fit_epochs,
    fit_transform,
    fit_trees,
    input_width,
    robust_states,
)
from ctk_android.types import (
    AggregationRule,
    CtkError,
    Epochs,
    FeatureMatrix,
    InputTransform,
    LabelVector,
    ProximalAnchor,
    ProximalStrength,
    RandomSeed,
    RowIndices,
    Scorer,
    SeedComponent,
    TrainingRows,
    TransformRule,
)


@dataclass(frozen=True)
class TrainingContext:
    features: FeatureMatrix
    labels: LabelVector
    config: TrainingConfig
    family: ModelFamily
    device: Device
    seed: RandomSeed
    transform_rule: TransformRule | None


def derive_seed(base: RandomSeed, *parts: SeedComponent) -> RandomSeed:
    return RandomSeed(np.random.SeedSequence([base, *parts]).generate_state(1)[0].item())


def learner_stream(learner: Learner) -> RandomSeed:
    return RandomSeed(list(Learner).index(learner) + 1)


def _require_both_classes(context: TrainingContext, rows: RowIndices) -> None:
    counts = np.bincount(context.labels[rows], minlength=2)
    if counts.min() < context.config.min_rows_per_class:
        raise CtkError(
            FailureReason.INSUFFICIENT_CALIBRATION,
            ErrorMessage.CLASS_COUNTS.format(counts=counts.tolist()),
        )


def _initial_network(
    context: TrainingContext, stream: RandomSeed, transform: InputTransform | None
) -> torch.nn.Module:
    torch.default_generator.manual_seed(derive_seed(context.seed, SeedComponent(stream)))
    return build_network(context.family, input_width(context.features, transform), context.config)


# Learned preprocessing sees exactly the rows the model is trained on (Amendment A3).
def _transform(context: TrainingContext, rows: RowIndices) -> InputTransform | None:
    rule = context.transform_rule
    return None if rule is None else fit_transform(context.features, rows, rule)


def train_scorer(
    context: TrainingContext, rows: RowIndices, epochs: Epochs, stream: RandomSeed
) -> Scorer:
    _require_both_classes(context, rows)
    transform = _transform(context, rows)
    if context.family is ModelFamily.GRADIENT_BOOSTED_TREES:
        trees = fit_trees(
            context.features,
            context.labels,
            rows,
            context.config,
            derive_seed(context.seed, SeedComponent(stream)),
            transform,
        )
        return Scorer(
            family=context.family, network=None, trees=trees, device=Device.CPU, transform=transform
        )
    network = _initial_network(context, stream, transform)
    fit_epochs(
        network,
        context.features,
        context.labels,
        rows,
        epochs,
        context.config,
        derive_seed(context.seed, SeedComponent(stream), SeedComponent(1)),
        context.device,
        None,
        transform,
    )
    return Scorer(
        family=context.family,
        network=network,
        trees=None,
        device=context.device,
        transform=transform,
    )


def pooled_rows(training: TrainingRows) -> RowIndices:
    return np.concatenate([training[client] for client in ClientId])


def train_federated(
    context: TrainingContext,
    training: TrainingRows,
    learner: Learner,
    strength: ProximalStrength,
    stream: RandomSeed,
    aggregation: AggregationRule | None = None,
) -> Scorer:
    if context.family is ModelFamily.GRADIENT_BOOSTED_TREES:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.PARAMETRIC_ONLY)
    for client in ClientId:
        _require_both_classes(context, training[client])
    transform = _transform(context, pooled_rows(training))
    global_net = _initial_network(context, stream, transform)
    weights = np.array([training[client].size for client in ClientId], dtype=np.float64)
    for round_index in range(context.config.federated_rounds):
        anchor = ProximalAnchor(
            state={k: v.detach().clone() for k, v in global_net.state_dict().items()},
            strength=strength,
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
                derive_seed(
                    context.seed,
                    SeedComponent(stream),
                    SeedComponent(round_index),
                    SeedComponent(client_index),
                ),
                context.device,
                anchor if learner is Learner.FEDPROX else None,
                transform,
            )
            states.append({k: v.detach().cpu() for k, v in local.state_dict().items()})
        global_net.load_state_dict(
            average_states(states, weights)
            if aggregation is None
            else robust_states(states, aggregation)
        )
        logs.debug(
            LogEvent.FEDERATED_ROUND,
            {LogField.ROUND: round_index, LogField.LEARNER: learner, LogField.SEED: context.seed},
        )
    return Scorer(
        family=context.family,
        network=global_net,
        trees=None,
        device=context.device,
        transform=transform,
    )


def finetune(
    context: TrainingContext, scorer: Scorer, rows: RowIndices, epochs: Epochs, stream: RandomSeed
) -> Scorer:
    if scorer.network is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.FINETUNE_NETWORK)
    network = copy.deepcopy(scorer.network)
    fit_epochs(
        network,
        context.features,
        context.labels,
        rows,
        epochs,
        context.config,
        derive_seed(context.seed, SeedComponent(stream)),
        context.device,
        None,
        scorer.transform,
    )
    return Scorer(
        family=context.family,
        network=network,
        trees=None,
        device=context.device,
        transform=scorer.transform,
    )
