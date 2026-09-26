import numpy as np
import scipy.sparse as sp
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from torch import nn

from ctk_android.config import TrainingConfig
from ctk_android.enums import (
    Aggregation,
    Device,
    ErrorMessage,
    ModelFamily,
    RowBlock,
    Tolerance,
)
from ctk_android.types import (
    AggregationRule,
    Epochs,
    FeatureCount,
    FeatureMatrix,
    InputTransform,
    LabelVector,
    LogitChunk,
    LogitVector,
    ModelInputs,
    ProximalAnchor,
    RandomSeed,
    RowIndices,
    Scorer,
    StateDict,
    Stepper,
    TransformRule,
    WeightVector,
)


def resolve_device(requested: Device) -> Device:
    if requested is Device.CUDA and not torch.cuda.is_available():
        return Device.CPU
    return requested


def build_network(family: ModelFamily, features: FeatureCount, config: TrainingConfig) -> nn.Module:
    if family is ModelFamily.LINEAR:
        return nn.Linear(features, 1)
    layers: list[nn.Module] = []
    width = features
    for units in config.hidden_units:
        layers += [nn.Linear(width, units), nn.ReLU(), nn.Dropout(config.dropout)]
        width = units
    layers.append(nn.Linear(width, 1))
    return nn.Sequential(*layers)


def fit_transform(features: FeatureMatrix, rows: RowIndices, rule: TransformRule) -> InputTransform:
    block = sp.csr_matrix(features[rows], dtype=np.float64)
    columns = None
    if rule.min_prevalence is not None:
        prevalence = np.asarray((block > 0).sum(axis=0)).ravel() / rows.size
        columns = np.flatnonzero(prevalence >= rule.min_prevalence)
        block = sp.csr_matrix(block[:, columns])
    mean = np.asarray(block.mean(axis=0)).ravel()
    second = np.asarray(block.multiply(block).mean(axis=0)).ravel()
    spread = np.sqrt(np.maximum(second - mean**2, 0.0)) + Tolerance.STANDARD_DEVIATION_FLOOR
    return InputTransform(
        columns=columns, mean=mean.astype(np.float32), spread=spread.astype(np.float32)
    )


def input_width(features: FeatureMatrix, transform: InputTransform | None) -> FeatureCount:
    return features.shape[1] if transform is None else transform.mean.size


def model_inputs(
    features: FeatureMatrix, rows: RowIndices, transform: InputTransform | None
) -> ModelInputs:
    block = features[rows]
    if transform is not None and transform.columns is not None:
        block = block[:, transform.columns]
    dense = block.toarray() if sp.issparse(block) else np.asarray(block)
    values = dense.astype(np.float32)
    return values if transform is None else (values - transform.mean) / transform.spread


def _tensor(
    features: FeatureMatrix, rows: RowIndices, device: Device, transform: InputTransform | None
) -> torch.Tensor:
    return torch.as_tensor(model_inputs(features, rows, transform)).to(device)


def _optimizer(network: nn.Module, config: TrainingConfig) -> Stepper:
    return torch.optim.Adam(
        network.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )


def fit_epochs(
    network: nn.Module,
    features: FeatureMatrix,
    labels: LabelVector,
    rows: RowIndices,
    epochs: Epochs,
    config: TrainingConfig,
    seed: RandomSeed,
    device: Device,
    proximal: ProximalAnchor | None,
    transform: InputTransform | None,
) -> None:
    generator = torch.Generator().manual_seed(seed)
    inputs = _tensor(features, rows, device, transform)
    targets = torch.as_tensor(labels[rows].astype(np.float32)).to(device)
    network.to(device).train()
    optimizer = _optimizer(network, config)
    loss_fn = nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        order = torch.randperm(rows.size, generator=generator).to(device)
        for start in range(0, rows.size, config.batch_size):
            batch = order[start : start + config.batch_size]
            optimizer.zero_grad()
            loss = loss_fn(network(inputs[batch]).squeeze(-1), targets[batch])
            if proximal is not None:
                penalty = sum(
                    ((param - proximal.state[name].to(device)) ** 2).sum()
                    for name, param in network.named_parameters()
                )
                loss = loss + 0.5 * proximal.strength * penalty
            loss.backward()
            optimizer.step()
    network.eval()


def average_states(states: list[StateDict], weights: WeightVector) -> StateDict:
    normalised = torch.as_tensor((weights / weights.sum()).astype(np.float32))
    return {
        name: torch.stack(
            [state[name].to(Device.CPU) * normalised[index] for index, state in enumerate(states)]
        ).sum(dim=0)
        for name in states[0]
    }


def _robust(stack: torch.Tensor, rule: AggregationRule) -> torch.Tensor:
    if rule.rule is Aggregation.COORDINATE_MEDIAN:
        return stack.median(dim=0).values
    ordered = stack.sort(dim=0).values
    return ordered[rule.trim_per_side : stack.shape[0] - rule.trim_per_side].mean(dim=0)


def _robust_state(values: list[torch.Tensor], rule: AggregationRule) -> torch.Tensor:
    stack = torch.stack([value.to(Device.CPU) for value in values])
    if stack.dtype is torch.float32:
        return _robust(stack, rule)
    return _robust(stack.float(), rule).to(stack.dtype)


def robust_states(states: list[StateDict], rule: AggregationRule) -> StateDict:
    return {name: _robust_state([state[name] for state in states], rule) for name in states[0]}


def fit_trees(
    features: FeatureMatrix,
    labels: LabelVector,
    rows: RowIndices,
    config: TrainingConfig,
    seed: RandomSeed,
    transform: InputTransform | None,
) -> HistGradientBoostingClassifier:
    model = HistGradientBoostingClassifier(
        max_iter=config.trees.max_iter,
        max_depth=config.trees.max_depth,
        learning_rate=config.trees.learning_rate,
        random_state=seed,
    )
    model.fit(model_inputs(features, rows, transform), labels[rows])
    return model


def scorer_logits(scorer: Scorer, features: FeatureMatrix, rows: RowIndices) -> LogitVector:
    if scorer.trees is not None:
        return scorer.trees.decision_function(
            model_inputs(features, rows, scorer.transform)
        ).astype(np.float64)
    if scorer.network is None:
        raise ValueError(ErrorMessage.EMPTY_SCORER)
    scorer.network.to(scorer.device).eval()
    outputs: list[LogitChunk] = []
    with torch.no_grad():
        for start in range(0, rows.size, RowBlock.SCORING):
            chunk = _tensor(
                features, rows[start : start + RowBlock.SCORING], scorer.device, scorer.transform
            )
            outputs.append(scorer.network(chunk).squeeze(-1).cpu().numpy())
    return np.concatenate(outputs).astype(np.float64) if outputs else np.empty(0)
