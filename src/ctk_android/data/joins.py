import polars as pl

from ctk_android import logs
from ctk_android.enums import (
    Column,
    DetailMessage,
    LibraryOption,
    LogEvent,
    LogField,
    Separator,
    ValidationCheck,
)
from ctk_android.types import AndroZooTable, JoinResult, LamdaMetadataTable, ValidationRecord


def join_sources(lamda: LamdaMetadataTable, androzoo: AndroZooTable) -> JoinResult:
    unique_links = androzoo[Column.SHA256].n_unique() == androzoo.height
    linked = lamda.join(
        androzoo.rename({Column.VT_COUNT: Column.LINKED_VT}),
        on=Column.SHA256,
        how=LibraryOption.JOIN_LEFT,
    )
    unmatched = linked.filter(pl.col(Column.PACKAGE).is_null()).select(Column.SHA256)
    joined = linked.filter(pl.col(Column.PACKAGE).is_not_null())
    vt_agrees = joined.select((pl.col(Column.VT_COUNT) == pl.col(Column.LINKED_VT)).all()).item()
    joined = joined.drop(Column.LINKED_VT).with_columns(
        pl.col(Column.MARKETS)
        .str.split(Separator.PIPE)
        .list.eval(pl.element().sort())
        .list.join(Separator.PIPE)
        .alias(Column.MARKETS),
        pl.col(Column.MARKETS).str.split(Separator.PIPE).list.len().alias(Column.MARKET_COUNT),
    )
    logs.info(
        LogEvent.LINKAGE_AUDITED,
        {
            LogField.ROWS: joined.height,
            LogField.UNMATCHED: unmatched.height,
            LogField.PASSED: unique_links and vt_agrees,
        },
    )
    return JoinResult(
        joined=joined,
        unmatched=unmatched,
        validations=(
            ValidationRecord(
                check=ValidationCheck.LINKAGE_COMPLETE,
                passed=unmatched.height == 0 and unique_links and vt_agrees,
                detail=DetailMessage.LINKAGE.format(
                    matched=joined.height,
                    unmatched=unmatched.height,
                    unique=unique_links,
                    agrees=vt_agrees,
                ),
            ),
        ),
    )
