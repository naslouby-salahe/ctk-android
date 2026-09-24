import polars as pl

from ctk_android.config import DataConfig
from ctk_android.enums import ClientId, Column, Market

SINGLE_MARKET = 1


def assign_clients(joined: pl.DataFrame, config: DataConfig) -> pl.DataFrame:
    single = joined.filter(pl.col(Column.MARKET_COUNT) == SINGLE_MARKET)
    early_play = pl.col(Column.YEAR_MONTH) < config.play_era_boundary
    client = (
        pl.when(pl.col(Column.MARKETS) == Market.GOOGLE_PLAY)
        .then(pl.when(early_play).then(pl.lit(ClientId.PLAY_EARLY)).otherwise(pl.lit(ClientId.PLAY_LATE)))
        .when(pl.col(Column.MARKETS) == Market.ANZHI)
        .then(pl.lit(ClientId.ANZHI))
        .when(pl.col(Column.MARKETS) == Market.APPCHINA)
        .then(pl.lit(ClientId.APPCHINA))
        .otherwise(None)
        .alias(Column.CLIENT)
    )
    return (
        single.with_columns(client)
        .filter(pl.col(Column.CLIENT).is_not_null())
        .select(
            Column.SHA256,
            Column.PACKAGE,
            Column.LABEL,
            Column.FAMILY,
            Column.VT_COUNT,
            Column.YEAR_MONTH,
            Column.CLIENT,
        )
    )


def client_support(assignments: pl.DataFrame) -> pl.DataFrame:
    return (
        assignments.group_by(Column.CLIENT)
        .agg(
            pl.len().alias(Column.ROWS),
            (pl.col(Column.LABEL) == 1).sum().alias(Column.MALWARE_ROWS),
            (pl.col(Column.LABEL) == 0).sum().alias(Column.BENIGN_ROWS),
            pl.col(Column.PACKAGE).n_unique().alias(Column.PACKAGES),
        )
        .sort(Column.CLIENT)
    )
