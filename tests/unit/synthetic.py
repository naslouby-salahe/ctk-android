import numpy as np
import polars as pl

from ctk_android.enums import ClientId, Column, EligibilityReason, SplitRole
from ctk_android.types import StudyData, TargetPair

FEATURES = 8
ROWS_PER_CELL = 40
FAMILIES = ("alpha", "beta")


def synthetic_study() -> StudyData:
    rows: list[dict[Column, object]] = []
    for client in ClientId:
        for role in SplitRole:
            for label in (0, 1):
                for index in range(ROWS_PER_CELL):
                    family = "benign" if label == 0 else FAMILIES[index % len(FAMILIES)]
                    rows.append(
                        {
                            Column.CLIENT: client,
                            Column.ROLE: role,
                            Column.LABEL: label,
                            Column.FAMILY: family,
                            Column.REASON: EligibilityReason.ELIGIBLE
                            if label == 1
                            else EligibilityReason.NOT_IN_FAMILY_SET,
                        }
                    )
    table = pl.DataFrame(rows).with_row_index(Column.ROW)
    rng = np.random.default_rng(0)
    features = (rng.random((table.height, FEATURES)) < 0.5).astype(np.uint8)
    return StudyData(table=table, features=features)


def synthetic_targets() -> tuple[TargetPair, ...]:
    return (
        TargetPair(client=ClientId.ANZHI, family="alpha"),
        TargetPair(client=ClientId.APPCHINA, family="beta"),
    )
