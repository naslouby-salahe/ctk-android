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
    ProximalStrength,
    Scorer,
    Seed,
)

StateDict = dict[str, torch.Tensor]


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
    return torch.from_numpy(np.asarray(features[rows], dtype=np.float32)).to(device.value)


def fit_epochs(
    network: nn.Module,
    features: ByteMatrix,
    labels: IntArray,
    rows: IntArray,
    epochs: Epochs,
    config: TrainingConfig,
    seed: Seed,
    device: Device,
    anchor: StateDict | None = None,
    proximal: ProximalStrength = 0.0,
) -> None:
    generator = torch.Generator().manual_seed(seed)
    inputs = _tensor(features, rows, device)
    targets = torch.from_numpy(labels[rows].astype(np.float32)).to(device.value)
    network.to(device.value).train()
    optimizer = torch.optim.Adam(
        network.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    reference = (
        {name: value.detach().clone() for name, value in anchor.items()} if anchor else None
    )
    loss_fn = nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        order = torch.randperm(rows.size, generator=generator).to(device.value)
        for start in range(0, rows.size, config.batch_size):
            batch = order[start : start + config.batch_size]
            optimizer.zero_grad()
            loss = loss_fn(network(inputs[batch]).squeeze(-1), targets[batch])
            if reference is not None and proximal > 0.0:
                penalty = sum(
                    ((param - reference[name]) ** 2).sum()
                    for name, param in network.named_parameters()
                )
                loss = loss + 0.5 * proximal * penalty
            loss.backward()
            optimizer.step()
    network.eval()


def average_states(states: list[StateDict], weights: FloatArray) -> StateDict:
    normalised = torch.from_numpy((weights / weights.sum()).astype(np.float32))
    return {
        name: sum(
            state[name].to("cpu") * normalised[index] for index, state in enumerate(states)
        )
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
    scorer.network.to(scorer.device.value).eval()
    outputs: list[Float32Array] = []
    with torch.no_grad():
        for start in range(0, rows.size, 8192):
            chunk = _tensor(features, rows[start : start + 8192], scorer.device)
            outputs.append(scorer.network(chunk).squeeze(-1).cpu().numpy())
    return np.concatenate(outputs).astype(np.float64) if outputs else np.empty(0)
