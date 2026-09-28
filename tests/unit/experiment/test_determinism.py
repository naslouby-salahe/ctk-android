import os

import numpy as np
import torch

from ctk_android.config import TrainingConfig, load_config
from ctk_android.enums import DeterminismSetting, Device, ModelFamily, OptimizationStatus
from ctk_android.experiment import training
from ctk_android.experiment.models import (
    build_network,
    configure_determinism,
    fit_epochs,
    parameters_are_finite,
    resolve_device,
)
from ctk_android.paths import Paths
from ctk_android.types import RandomSeed, TrainingTrace
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
DROPOUT = CONFIG.experiments.training.model_copy(update={"dropout": 0.5, "hidden_units": (16,)})
DEVICE = resolve_device(Device.CUDA)
FEATURES = 20
ROWS = 300
SEED = RandomSeed(11)


def _data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    features = (rng.random((ROWS, FEATURES)) < 0.5).astype(np.uint8)
    labels = (features[:, 0] | features[:, 1]).astype(np.int64)
    return features, labels, np.arange(ROWS)


def _train(seed: RandomSeed, config: TrainingConfig = DROPOUT) -> list[torch.Tensor]:
    features, labels, rows = _data()
    torch.default_generator.manual_seed(1)
    network = build_network(ModelFamily.MLP, FEATURES, config)
    fit_epochs(network, features, labels, rows, 3, config, seed, DEVICE, None, None)
    return [value.detach().cpu().clone() for value in network.state_dict().values()]


def test_dropout_training_is_bitwise_repeatable_for_one_seed_on_the_configured_device() -> None:
    configure_determinism()
    first, second = _train(SEED), _train(SEED)
    assert all(torch.equal(a, b) for a, b in zip(first, second, strict=True))


def test_dropout_training_depends_on_its_seed() -> None:
    configure_determinism()
    first, other = _train(SEED), _train(RandomSeed(SEED + 1))
    assert not all(torch.equal(a, b) for a, b in zip(first, other, strict=True))


def test_dropout_training_ignores_unrelated_global_random_state() -> None:
    configure_determinism()
    first = _train(SEED)
    torch.default_generator.manual_seed(999)
    np.random.seed(999)
    second = _train(SEED)
    assert all(torch.equal(a, b) for a, b in zip(first, second, strict=True))


def test_determinism_switches_are_configured_for_torch_cudnn_and_cublas() -> None:
    configure_determinism()
    assert torch.are_deterministic_algorithms_enabled()
    assert torch.backends.cudnn.deterministic
    assert not torch.backends.cudnn.benchmark
    assert os.environ[DeterminismSetting.CUBLAS_ENVIRONMENT] == DeterminismSetting.CUBLAS_WORKSPACE


def test_training_records_every_epoch_with_finite_loss_and_parameters() -> None:
    features, labels, rows = _data()
    network = build_network(ModelFamily.MLP, FEATURES, DROPOUT)
    trace = fit_epochs(network, features, labels, rows, 3, DROPOUT, SEED, DEVICE, None, None)
    assert [stat.epoch for stat in trace] == [0, 1, 2]
    assert all(stat.loss is not None and stat.loss > 0 for stat in trace)
    assert all(stat.nonfinite_batches == 0 and stat.parameters_finite for stat in trace)
    assert trace[-1].loss is not None and trace[0].loss is not None
    assert trace[-1].loss < trace[0].loss
    assert parameters_are_finite(network)


def test_non_finite_features_are_reported_instead_of_hidden() -> None:
    features, labels, rows = _data()
    poisoned = features.astype(np.float32)
    poisoned[:, 0] = np.nan
    network = build_network(ModelFamily.MLP, FEATURES, DROPOUT)
    trace = fit_epochs(network, poisoned, labels, rows, 2, DROPOUT, SEED, DEVICE, None, None)
    assert all(stat.nonfinite_batches > 0 for stat in trace)
    assert all(stat.loss is None for stat in trace)
    assert not trace[-1].parameters_finite
    assert not parameters_are_finite(network)


def test_the_training_trace_labels_pending_records_with_the_trained_arm() -> None:
    from ctk_android.enums import ClientId, ExposureCondition, Learner, TrainingPhase
    from ctk_android.types import ArmKey, TrainingRecord

    trace = TrainingTrace()
    record = TrainingRecord(
        phase=TrainingPhase.SCORER,
        client=ClientId.ANZHI,
        round=None,
        epoch=0,
        loss=0.5,
        nonfinite_batches=0,
        parameters_finite=True,
        status=OptimizationStatus.COMPLETED,
    )
    trace.record([record])
    assert not trace.rows
    arm = ArmKey(learner=Learner.LOCAL, condition=ExposureCondition.PEER_PRESENT, dose=None)
    trace.label(arm)
    assert [row.learner for row in trace.rows] == [Learner.LOCAL]
    trace.label(arm)
    assert len(trace.rows) == 1


def test_every_configured_seed_reaches_the_stochastic_leaf_operations() -> None:
    assert training.derive_seed(SEED, training.SeedComponent(1)) != training.derive_seed(
        SEED, training.SeedComponent(2)
    )
    assert training.derive_seed(SEED, training.SeedComponent(1)) == training.derive_seed(
        SEED, training.SeedComponent(1)
    )
