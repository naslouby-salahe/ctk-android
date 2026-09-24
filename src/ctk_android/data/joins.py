import polars as pl

from ctk_android.enums import Column, ValidationCheck
from ctk_android.types import JoinResult, ValidationRecord

MARKET_SEPARATOR = "|"
LINKED_VT = "linked_vt_detection"


def join_sources(lamda: pl.DataFrame, androzoo: pl.DataFrame) -> JoinResult:
    unique_links = androzoo[Column.SHA256].n_unique() == androzoo.height
    linked = lamda.join(
        androzoo.rename({Column.VT_COUNT: LINKED_VT}),
        on=Column.SHA256,
        how="left",
    )
    unmatched = linked.filter(pl.col(Column.PACKAGE).is_null()).select(Column.SHA256)
    joined = linked.filter(pl.col(Column.PACKAGE).is_not_null())
    vt_agrees = joined.select(
        (pl.col(Column.VT_COUNT) == pl.col(LINKED_VT)).all()
    ).item()
    joined = joined.drop(LINKED_VT).with_columns(
        pl.col(Column.MARKETS)
        .str.split(MARKET_SEPARATOR)
        .list.eval(pl.element().sort())
        .list.join(MARKET_SEPARATOR)
        .alias(Column.MARKETS),
        pl.col(Column.MARKETS)
        .str.split(MARKET_SEPARATOR)
        .list.len()
        .alias(Column.MARKET_COUNT),
    )
    return JoinResult(
        joined=joined,
        unmatched=unmatched,
        validations=(
            ValidationRecord(
                check=ValidationCheck.LINKAGE_COMPLETE,
                passed=unmatched.height == 0 and unique_links and bool(vt_agrees),
                detail=(
                    f"matched={joined.height} unmatched={unmatched.height} "
                    f"unique_links={unique_links} vt_agrees={vt_agrees}"
                ),
            ),
        ),
    )
