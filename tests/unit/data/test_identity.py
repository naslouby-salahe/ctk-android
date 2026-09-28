import numpy as np
import polars as pl

from ctk_android.data.preparation import build_identities
from ctk_android.enums import Column


def _assignments(packages: list[str]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            Column.SHA256: [f"{index:064x}" for index in range(len(packages))],
            Column.PACKAGE: packages,
        }
    )


def test_rows_sharing_a_package_or_a_feature_vector_share_a_component() -> None:
    features = np.array([[1, 0], [0, 1], [0, 1], [1, 1]], dtype=np.uint8)
    identities = build_identities(_assignments(["p", "p", "q", "r"]), features)
    components = identities[Column.COMPONENT].to_list()
    assert components[0] == components[1] == components[2]
    assert components[3] != components[0]


def test_components_are_transitive_across_both_relations() -> None:
    features = np.array([[1, 0], [1, 0], [0, 1], [0, 1]], dtype=np.uint8)
    identities = build_identities(_assignments(["a", "b", "b", "c"]), features)
    assert len(set(identities[Column.COMPONENT].to_list())) == 1


def test_identity_construction_is_deterministic() -> None:
    features = np.random.default_rng(1).integers(0, 2, size=(50, 6)).astype(np.uint8)
    packages = [f"pkg{index % 7}" for index in range(50)]
    first = build_identities(_assignments(packages), features)
    second = build_identities(_assignments(packages), features)
    assert first.equals(second)
