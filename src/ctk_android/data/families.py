import numpy as np
import polars as pl

from ctk_android.config import DataConfig, EligibilityRule
from ctk_android.enums import (
    ClientId,
    Column,
    EligibilityProfile,
    EligibilityReason,
    FamilySetName,
    SplitRole,
)
from ctk_android.types import FamilyName, Seed

NAMED_FAMILY_COLUMN = Column.FAMILY


def classify_labels(assignments: pl.DataFrame, config: DataConfig) -> pl.DataFrame:
    family = pl.col(Column.FAMILY)
    reason = (
        pl.when(pl.col(Column.LABEL) == 0)
        .then(pl.lit(EligibilityReason.NOT_IN_FAMILY_SET))
        .when(family.str.strip_chars() == "")
        .then(pl.lit(EligibilityReason.EMPTY_LABEL))
        .when(family.is_in(list(config.unknown_labels)))
        .then(pl.lit(EligibilityReason.UNKNOWN_LABEL))
        .when(family.str.starts_with(config.singleton_prefix))
        .then(pl.lit(EligibilityReason.SINGLETON_LABEL))
        .otherwise(pl.lit(EligibilityReason.ELIGIBLE))
        .alias(Column.REASON)
    )
    return assignments.with_columns(reason)


def corpus_support(labelled: pl.DataFrame) -> pl.DataFrame:
    return (
        labelled.filter(pl.col(Column.REASON) == EligibilityReason.ELIGIBLE)
        .group_by(Column.CLIENT, Column.FAMILY)
        .agg(pl.len().alias(Column.ROWS))
        .sort(Column.CLIENT, Column.FAMILY)
    )


def label_eligibility(labelled: pl.DataFrame) -> pl.DataFrame:
    return (
        labelled.filter(pl.col(Column.LABEL) == 1)
        .group_by(Column.REASON)
        .agg(pl.len().alias(Column.ROWS), pl.col(Column.FAMILY).n_unique().alias(Column.PACKAGES))
        .sort(Column.REASON)
    )


def select_family_sets(
    support: pl.DataFrame, config: DataConfig, set_size: int
) -> dict[FamilySetName, tuple[FamilyName, ...]]:
    totals = (
        support.group_by(Column.FAMILY)
        .agg(pl.col(Column.ROWS).sum().alias(Column.ROWS), pl.col(Column.CLIENT).n_unique().alias(Column.MARKETS))
        .filter(
            (pl.col(Column.ROWS) >= config.family_selection.candidate_min_total_support)
            & (pl.col(Column.MARKETS) >= 2)
        )
        .sort([Column.ROWS, Column.FAMILY], descending=[True, False])
    )
    ranked = totals[Column.FAMILY].to_list()
    return {
        FamilySetName.PRIMARY: tuple(ranked[0::2][:set_size]),
        FamilySetName.REPLICATION: tuple(ranked[1::2][:set_size]),
    }


def role_counts(labelled: pl.DataFrame, roles: pl.Series, families: tuple[FamilyName, ...]) -> pl.DataFrame:
    return (
        labelled.with_columns(roles.alias(Column.ROLE))
        .filter(
            (pl.col(Column.REASON) == EligibilityReason.ELIGIBLE)
            & pl.col(Column.FAMILY).is_in(list(families))
        )
        .group_by(Column.CLIENT, Column.FAMILY, Column.ROLE)
        .agg(pl.len().alias(Column.ROWS))
    )


def _count(table: pl.DataFrame, role: SplitRole) -> pl.DataFrame:
    return table.filter(pl.col(Column.ROLE) == role).select(
        Column.CLIENT, Column.FAMILY, pl.col(Column.ROWS)
    )


def controlled_pairs(
    counts: pl.DataFrame,
    client_fit_rows: pl.DataFrame,
    rule: EligibilityRule,
) -> pl.DataFrame:
    fit = _count(counts, SplitRole.FIT).rename({Column.ROWS: Column.TARGET_FIT_ROWS})
    fed_fit = fit.group_by(Column.FAMILY).agg(pl.col(Column.TARGET_FIT_ROWS).sum().alias(Column.TOTAL_FIT_ROWS))
    fed_test = (
        _count(counts, SplitRole.TEST)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.ROWS).sum().alias(Column.FEDERATION_TEST_ROWS))
    )
    own_test = _count(counts, SplitRole.TEST).rename({Column.ROWS: Column.TARGET_TEST_ROWS})
    return (
        fit.join(fed_fit, on=Column.FAMILY)
        .join(fed_test, on=Column.FAMILY, how="left")
        .join(own_test, on=[Column.CLIENT, Column.FAMILY], how="left")
        .join(client_fit_rows, on=Column.CLIENT)
        .with_columns(
            pl.col(Column.FEDERATION_TEST_ROWS).fill_null(0),
            pl.col(Column.TARGET_TEST_ROWS).fill_null(0),
            (pl.col(Column.TOTAL_FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS)).alias(Column.PEER_FIT_ROWS),
        )
        .with_columns(
            (
                (pl.col(Column.TARGET_FIT_ROWS) >= rule.target_min_fit)
                & (pl.col(Column.PEER_FIT_ROWS) >= rule.peer_min_fit)
                & (pl.col(Column.FEDERATION_TEST_ROWS) >= rule.federation_min_test)
                & (pl.col(Column.FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS) >= rule.target_min_remaining_fit)
            ).alias(Column.ELIGIBLE)
        )
        .sort(Column.FAMILY, Column.CLIENT)
    )


def natural_pairs(
    counts: pl.DataFrame,
    client_fit_rows: pl.DataFrame,
    max_target_share: float,
    peer_min_fit: int,
    own_domain_min_test: int,
) -> pl.DataFrame:
    fit = _count(counts, SplitRole.FIT).rename({Column.ROWS: Column.TARGET_FIT_ROWS})
    total = fit.group_by(Column.FAMILY).agg(pl.col(Column.TARGET_FIT_ROWS).sum().alias(Column.TOTAL_FIT_ROWS))
    own_test = _count(counts, SplitRole.TEST).rename({Column.ROWS: Column.TARGET_TEST_ROWS})
    clients = client_fit_rows.select(Column.CLIENT)
    families = total.select(Column.FAMILY)
    grid = clients.join(families, how="cross")
    return (
        grid.join(fit, on=[Column.CLIENT, Column.FAMILY], how="left")
        .join(total, on=Column.FAMILY)
        .join(own_test, on=[Column.CLIENT, Column.FAMILY], how="left")
        .with_columns(
            pl.col(Column.TARGET_FIT_ROWS).fill_null(0),
            pl.col(Column.TARGET_TEST_ROWS).fill_null(0),
        )
        .with_columns(
            (pl.col(Column.TARGET_FIT_ROWS) / pl.col(Column.TOTAL_FIT_ROWS)).alias(Column.TARGET_SHARE),
            (pl.col(Column.TOTAL_FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS)).alias(Column.PEER_FIT_ROWS),
        )
        .with_columns(
            (
                (pl.col(Column.TARGET_SHARE) <= max_target_share)
                & (pl.col(Column.PEER_FIT_ROWS) >= peer_min_fit)
                & (pl.col(Column.TARGET_TEST_ROWS) >= own_domain_min_test)
            ).alias(Column.ELIGIBLE)
        )
        .sort(Column.FAMILY, Column.CLIENT)
    )


def assign_targets(
    pairs: pl.DataFrame, seed: Seed, families: tuple[FamilyName, ...], rule: EligibilityRule
) -> list[tuple[ClientId, FamilyName]]:
    remaining = {
        row[Column.CLIENT]: row[Column.FIT_ROWS]
        for row in pairs.select(Column.CLIENT, Column.FIT_ROWS).unique().iter_rows(named=True)
    }
    rng = np.random.default_rng(np.random.SeedSequence([seed, len(families)]))
    chosen: list[tuple[ClientId, FamilyName]] = []
    for family in families:
        options = pairs.filter(
            (pl.col(Column.FAMILY) == family) & pl.col(Column.ELIGIBLE)
        ).sort(Column.CLIENT)
        candidates = list(options.iter_rows(named=True))
        order = rng.permutation(len(candidates))
        for index in order:
            row = candidates[int(index)]
            client = ClientId(row[Column.CLIENT])
            after = remaining[client] - row[Column.TARGET_FIT_ROWS]
            if after >= rule.target_min_remaining_fit:
                remaining[client] = after
                chosen.append((client, family))
                break
    return chosen


def profile_rule(config: DataConfig, profile: EligibilityProfile) -> EligibilityRule:
    return config.eligibility[profile]


def permute_family_labels(labelled: pl.DataFrame, seed: Seed, offset: Seed) -> pl.DataFrame:
    eligible = (labelled[Column.REASON] == EligibilityReason.ELIGIBLE).to_numpy()
    positions = np.flatnonzero(eligible)
    rng = np.random.default_rng(np.random.SeedSequence([seed, offset]))
    permuted = labelled[Column.FAMILY].to_numpy().copy()
    permuted[positions] = permuted[positions][rng.permutation(positions.size)]
    return labelled.with_columns(pl.Series(Column.FAMILY, permuted))
