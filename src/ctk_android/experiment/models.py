import numpy as np
import torch
from sklearn.ensemble import HistGradientBoostingClassifier
from torch import nn

from ctk_android.config import TrainingConfig
from ctk_android.enums import Device, ModelFamily
from ctk_android.types import (
    ByteMatrix,
    Epochs,
    FeatureCount,
    Float32Array,
    FloatArray,
    IntArray,
    ProximalAnchor,
    Scorer,
    Seed,
    StateDict,
    Stepper,
)

SCORING_CHUNK_ROWS = 1 << 13


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


def _tensor(features: ByteMatrix, rows: IntArray, device: Device) -> torch.Tensor:
    return torch.as_tensor(np.asarray(features[rows], dtype=np.float32)).to(device)


def _optimizer(network: nn.Module, config: TrainingConfig) -> Stepper:
    return torch.optim.Adam(
        network.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )


def fit_epochs(
    network: nn.Module,
    features: ByteMatrix,
    labels: IntArray,
    rows: IntArray,
    epochs: Epochs,
    config: TrainingConfig,
    seed: Seed,
    device: Device,
    proximal: ProximalAnchor | None,
) -> None:
    generator = torch.Generator().manual_seed(seed)
    inputs = _tensor(features, rows, device)
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
                    ((param - proximal.state[name]) ** 2).sum()
                    for name, param in network.named_parameters()
                )
                loss = loss + 0.5 * proximal.strength * penalty
            loss.backward()
            optimizer.step()
    network.eval()


def average_states(states: list[StateDict], weights: FloatArray) -> StateDict:
    normalised = torch.as_tensor((weights / weights.sum()).astype(np.float32))
    return {
        name: torch.stack(
            [state[name].to(Device.CPU) * normalised[index] for index, state in enumerate(states)]
        ).sum(dim=0)
        for name in states[0]
    }


def fit_trees(
    features: ByteMatrix, labels: IntArray, rows: IntArray, config: TrainingConfig, seed: Seed
) -> HistGradientBoostingClassifier:
    model = HistGradientBoostingClassifier(
        max_iter=config.trees.max_iter,
        max_depth=config.trees.max_depth,
        learning_rate=config.trees.learning_rate,
        random_state=seed,
    )
    return model.fit(np.asarray(features[rows]), labels[rows])


def scorer_logits(scorer: Scorer, features: ByteMatrix, rows: IntArray) -> FloatArray:
    if scorer.trees is not None:
        return scorer.trees.decision_function(np.asarray(features[rows])).astype(np.float64)
    if scorer.network is None:
        raise ValueError("scorer has neither network nor trees")
    scorer.network.to(scorer.device).eval()
    outputs: list[Float32Array] = []
    with torch.no_grad():
        for start in range(0, rows.size, SCORING_CHUNK_ROWS):
            chunk = _tensor(features, rows[start : start + SCORING_CHUNK_ROWS], scorer.device)
            outputs.append(scorer.network(chunk).squeeze(-1).cpu().numpy())
    return np.concatenate(outputs).astype(np.float64) if outputs else np.empty(0)
