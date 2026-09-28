import copy
from dataclasses import dataclass, field

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
    OptimizationStatus,
    TrainingPhase,
)
from ctk_android.experiment.models import (
    StateDict,
    average_states,
    build_network,
    fit_epochs,
    fit_transform,
    fit_trees,
    input_width,
    parameters_are_finite,
    robust_states,
)
from ctk_android.types import (
    AggregationRule,
    CtkError,
    Epochs,
    EpochStat,
    FeatureMatrix,
    FitTrace,
    InputTransform,
    LabelVector,
    LossValue,
    ProximalAnchor,
    ProximalStrength,
    RandomSeed,
    RoundIndex,
    RowCount,
    RowIndices,
    Scorer,
    SeedComponent,
    TrainingRecord,
    TrainingRows,
    TrainingTrace,
    TransformRule,
    WeightVector,
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
    trace: TrainingTrace = field(default_factory=TrainingTrace)


def derive_seed(base: RandomSeed, *parts: SeedComponent) -> RandomSeed:
    return RandomSeed(np.random.SeedSequence([base, *parts]).generate_state(1)[0].item())


def _status(stat: EpochStat) -> OptimizationStatus:
    if stat.nonfinite_batches:
        return OptimizationStatus.NON_FINITE_LOSS
    if not stat.parameters_finite:
        return OptimizationStatus.NON_FINITE_PARAMETERS
    return OptimizationStatus.COMPLETED


def _records(
    trace: FitTrace, phase: TrainingPhase, client: ClientId | None, round_index: RoundIndex | None
) -> list[TrainingRecord]:
    return [
        TrainingRecord(
            phase=phase,
            client=client,
            round=round_index,
            epoch=stat.epoch,
            loss=stat.loss,
            nonfinite_batches=stat.nonfinite_batches,
            parameters_finite=stat.parameters_finite,
            status=_status(stat),
        )
        for stat in trace
    ]


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


def _transform(context: TrainingContext, rows: RowIndices) -> InputTransform | None:
    rule = context.transform_rule
    return None if rule is None else fit_transform(context.features, rows, rule)


def train_scorer(
    context: TrainingContext,
    rows: RowIndices,
    epochs: Epochs,
    stream: RandomSeed,
    client: ClientId | None = None,
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
        context.trace.record(
            [
                TrainingRecord(
                    phase=TrainingPhase.TREES,
                    client=client,
                    round=None,
                    epoch=trees.n_iter_,
                    loss=None,
                    nonfinite_batches=0,
                    parameters_finite=True,
                    status=OptimizationStatus.COMPLETED,
                )
            ]
        )
        return Scorer(
            family=context.family, network=None, trees=trees, device=Device.CPU, transform=transform
        )
    network = _initial_network(context, stream, transform)
    fitted = fit_epochs(
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
    context.trace.record(_records(fitted, TrainingPhase.SCORER, client, None))
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
        round_losses: list[LossValue | None] = []
        round_skipped: RowCount = 0
        for client_index, client in enumerate(ClientId):
            local = copy.deepcopy(global_net)
            fitted = fit_epochs(
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
            context.trace.record(
                _records(fitted, TrainingPhase.FEDERATED_CLIENT, client, round_index)
            )
            round_losses.append(fitted[-1].loss)
            round_skipped += sum(stat.nonfinite_batches for stat in fitted)
        global_net.load_state_dict(
            average_states(states, weights)
            if aggregation is None
            else robust_states(states, aggregation)
        )
        context.trace.record(
            [_round_record(global_net, round_index, round_losses, weights, round_skipped)]
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


def _round_record(
    network: torch.nn.Module,
    round_index: RoundIndex,
    client_losses: list[LossValue | None],
    weights: WeightVector,
    skipped: RowCount,
) -> TrainingRecord:
    losses = np.array([np.nan if loss is None else loss for loss in client_losses])
    valid = ~np.isnan(losses)
    finite = parameters_are_finite(network)
    if skipped:
        status = OptimizationStatus.NON_FINITE_LOSS
    elif not finite:
        status = OptimizationStatus.NON_FINITE_PARAMETERS
    else:
        status = OptimizationStatus.COMPLETED
    return TrainingRecord(
        phase=TrainingPhase.FEDERATED_GLOBAL,
        client=None,
        round=round_index,
        epoch=None,
        loss=np.average(losses[valid], weights=weights[valid]).item() if valid.any() else None,
        nonfinite_batches=skipped,
        parameters_finite=finite,
        status=status,
    )


def finetune(
    context: TrainingContext,
    scorer: Scorer,
    rows: RowIndices,
    epochs: Epochs,
    stream: RandomSeed,
    client: ClientId,
) -> Scorer:
    if scorer.network is None:
        raise CtkError(FailureReason.NOT_APPLICABLE_MODEL_FAMILY, ErrorMessage.FINETUNE_NETWORK)
    network = copy.deepcopy(scorer.network)
    fitted = fit_epochs(
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
    context.trace.record(_records(fitted, TrainingPhase.FINETUNE, client, None))
    return Scorer(
        family=context.family,
        network=network,
        trees=None,
        device=context.device,
        transform=scorer.transform,
    )
