import numpy as np
import polars as pl
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from ctk_android import logs
from ctk_android.config import DataConfig
from ctk_android.data.cache import is_one_of, read_record
from ctk_android.enums import (
    ClientId,
    Column,
    DetailMessage,
    EligibilityReason,
    FamilySetName,
    Grouping,
    LibraryOption,
    LogEvent,
    LogField,
    Market,
    MarketCount,
    Separator,
    SourceFamilyLabel,
    SplitRole,
    ValidationCheck,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    AndroZooTable,
    AssignmentsTable,
    BinaryMatrix,
    ClientFitRowsTable,
    ClientSupportTable,
    ComponentSummaryTable,
    EligibilityRule,
    EligibilityTable,
    FamilyName,
    FamilySetDocument,
    FamilySets,
    FamilySupportTable,
    Fraction,
    GroupIds,
    IdentitiesTable,
    IdentityIds,
    JoinedTable,
    JoinResult,
    LabelledTable,
    LamdaMetadataTable,
    LargeFamilySelection,
    PackageSeries,
    PairsTable,
    RandomSeed,
    Rank,
    RoleCountsTable,
    RoleSeries,
    RoleSliceTable,
    SupportCount,
    TargetPair,
    ValidationRecord,
)


def read_family_set(paths: Paths, name: FamilySetName) -> tuple[FamilyName, ...]:
    return read_record(paths.family_set_file(name), FamilySetDocument).families


def classify_labels(assignments: AssignmentsTable, config: DataConfig) -> LabelledTable:
    family = pl.col(Column.FAMILY)
    reason = (
        pl.when(pl.col(Column.LABEL) == 0)
        .then(pl.lit(EligibilityReason.NOT_IN_FAMILY_SET))
        .when(family.str.strip_chars() == SourceFamilyLabel.EMPTY)
        .then(pl.lit(EligibilityReason.EMPTY_LABEL))
        .when(family.is_in(pl.Series(config.unknown_labels, dtype=pl.String).implode()))
        .then(pl.lit(EligibilityReason.UNKNOWN_LABEL))
        .when(family.str.starts_with(config.singleton_prefix))
        .then(pl.lit(EligibilityReason.SINGLETON_LABEL))
        .otherwise(pl.lit(EligibilityReason.ELIGIBLE))
        .alias(Column.REASON)
    )
    return assignments.with_columns(reason)


def corpus_support(labelled: LabelledTable) -> FamilySupportTable:
    return (
        labelled.filter(pl.col(Column.REASON) == EligibilityReason.ELIGIBLE)
        .group_by(Column.CLIENT, Column.FAMILY)
        .agg(pl.len().alias(Column.ROWS))
        .sort(Column.CLIENT, Column.FAMILY)
    )


def label_eligibility(labelled: LabelledTable) -> EligibilityTable:
    return (
        labelled.filter(pl.col(Column.LABEL) == 1)
        .group_by(Column.REASON)
        .agg(pl.len().alias(Column.ROWS), pl.col(Column.FAMILY).n_unique().alias(Column.PACKAGES))
        .sort(Column.REASON)
    )


def select_family_sets(
    support: FamilySupportTable, config: DataConfig, set_size: SupportCount
) -> FamilySets:
    totals = (
        support.group_by(Column.FAMILY)
        .agg(
            pl.col(Column.ROWS).sum().alias(Column.ROWS),
            pl.col(Column.CLIENT).n_unique().alias(Column.MARKETS),
        )
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


def large_family_sets() -> tuple[FamilySetName, ...]:
    return (
        FamilySetName.LARGE_1,
        FamilySetName.LARGE_2,
        FamilySetName.LARGE_3,
        FamilySetName.LARGE_4,
    )


def select_large_family_sets(
    labelled: LabelledTable,
    roles: RoleSeries,
    client_fit_rows: ClientFitRowsTable,
    rule: EligibilityRule,
) -> LargeFamilySelection:
    support = corpus_support(labelled)
    totals = support.group_by(Column.FAMILY).agg(pl.col(Column.ROWS).sum())
    universe = tuple(totals[Column.FAMILY].to_list())
    pairs = controlled_pairs(role_counts(labelled, roles, universe), client_fit_rows, rule)
    eligible = (
        pairs.filter(pl.col(Column.ELIGIBLE))
        .group_by(Column.FAMILY)
        .agg(
            pl.len().alias(Column.ELIGIBLE_PAIRS),
            (pl.col(Column.TARGET_TEST_ROWS) >= rule.own_domain_min_test)
            .sum()
            .alias(Column.OWN_DOMAIN_PAIRS),
        )
    )
    batches = large_family_sets()
    ranked = (
        totals.join(eligible, on=Column.FAMILY)
        .sort([Column.ROWS, Column.FAMILY], descending=[True, False])
        .with_row_index(Column.RANK)
    )
    ranked = ranked.with_columns(
        pl.Series(
            Column.FAMILY_SET,
            [batches[rank % len(batches)] for rank in range(ranked.height)],
            dtype=pl.String,
        )
    )
    return LargeFamilySelection(
        table=ranked,
        sets={
            batch: tuple(ranked.filter(pl.col(Column.FAMILY_SET) == batch)[Column.FAMILY].to_list())
            for batch in batches
        },
    )


def role_counts(
    labelled: LabelledTable, roles: RoleSeries, families: tuple[FamilyName, ...]
) -> RoleCountsTable:
    return (
        labelled.with_columns(roles.alias(Column.ROLE))
        .filter(
            (pl.col(Column.REASON) == EligibilityReason.ELIGIBLE)
            & is_one_of(Column.FAMILY, families)
        )
        .group_by(Column.CLIENT, Column.FAMILY, Column.ROLE)
        .agg(pl.len().alias(Column.ROWS))
    )


def _count(table: RoleCountsTable, role: SplitRole) -> RoleSliceTable:
    return table.filter(pl.col(Column.ROLE) == role).select(
        Column.CLIENT, Column.FAMILY, pl.col(Column.ROWS)
    )


def controlled_pairs(
    counts: RoleCountsTable,
    client_fit_rows: ClientFitRowsTable,
    rule: EligibilityRule,
) -> PairsTable:
    fit = _count(counts, SplitRole.FIT).rename({Column.ROWS: Column.TARGET_FIT_ROWS})
    fed_fit = fit.group_by(Column.FAMILY).agg(
        pl.col(Column.TARGET_FIT_ROWS).sum().alias(Column.TOTAL_FIT_ROWS)
    )
    fed_test = (
        _count(counts, SplitRole.TEST)
        .group_by(Column.FAMILY)
        .agg(pl.col(Column.ROWS).sum().alias(Column.FEDERATION_TEST_ROWS))
    )
    own_test = _count(counts, SplitRole.TEST).rename({Column.ROWS: Column.TARGET_TEST_ROWS})
    return (
        fit.join(fed_fit, on=Column.FAMILY)
        .join(fed_test, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .join(own_test, on=[Column.CLIENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT)
        .join(client_fit_rows, on=Column.CLIENT)
        .with_columns(
            pl.col(Column.FEDERATION_TEST_ROWS).fill_null(0),
            pl.col(Column.TARGET_TEST_ROWS).fill_null(0),
            (pl.col(Column.TOTAL_FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS)).alias(
                Column.PEER_FIT_ROWS
            ),
        )
        .with_columns(
            (
                (pl.col(Column.TARGET_FIT_ROWS) >= rule.target_min_fit)
                & (pl.col(Column.PEER_FIT_ROWS) >= rule.peer_min_fit)
                & (pl.col(Column.FEDERATION_TEST_ROWS) >= rule.federation_min_test)
                & (
                    pl.col(Column.FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS)
                    >= rule.target_min_remaining_fit
                )
            ).alias(Column.ELIGIBLE)
        )
        .sort(Column.FAMILY, Column.CLIENT)
    )


def natural_pairs(
    counts: RoleCountsTable,
    client_fit_rows: ClientFitRowsTable,
    max_target_share: Fraction,
    peer_min_fit: SupportCount,
    own_domain_min_test: SupportCount,
) -> PairsTable:
    fit = _count(counts, SplitRole.FIT).rename({Column.ROWS: Column.TARGET_FIT_ROWS})
    total = fit.group_by(Column.FAMILY).agg(
        pl.col(Column.TARGET_FIT_ROWS).sum().alias(Column.TOTAL_FIT_ROWS)
    )
    own_test = _count(counts, SplitRole.TEST).rename({Column.ROWS: Column.TARGET_TEST_ROWS})
    clients = client_fit_rows.select(Column.CLIENT)
    families = total.select(Column.FAMILY)
    grid = clients.join(families, how=LibraryOption.JOIN_CROSS)
    return (
        grid.join(fit, on=[Column.CLIENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT)
        .join(total, on=Column.FAMILY)
        .join(own_test, on=[Column.CLIENT, Column.FAMILY], how=LibraryOption.JOIN_LEFT)
        .with_columns(
            pl.col(Column.TARGET_FIT_ROWS).fill_null(0),
            pl.col(Column.TARGET_TEST_ROWS).fill_null(0),
        )
        .with_columns(
            (pl.col(Column.TARGET_FIT_ROWS) / pl.col(Column.TOTAL_FIT_ROWS)).alias(
                Column.TARGET_SHARE
            ),
            (pl.col(Column.TOTAL_FIT_ROWS) - pl.col(Column.TARGET_FIT_ROWS)).alias(
                Column.PEER_FIT_ROWS
            ),
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
    pairs: PairsTable, seed: RandomSeed, families: tuple[FamilyName, ...], rule: EligibilityRule
) -> list[TargetPair]:
    remaining = {
        row[Column.CLIENT]: row[Column.FIT_ROWS]
        for row in pairs.select(Column.CLIENT, Column.FIT_ROWS).unique().iter_rows(named=True)
    }
    rng = np.random.default_rng(np.random.SeedSequence([seed, len(families)]))
    chosen: list[TargetPair] = []
    for family in families:
        options = pairs.filter((pl.col(Column.FAMILY) == family) & pl.col(Column.ELIGIBLE)).sort(
            Column.CLIENT
        )
        candidates = list(options.iter_rows(named=True))
        order: list[Rank] = rng.permutation(len(candidates)).tolist()
        for index in order:
            row = candidates[index]
            client = ClientId(row[Column.CLIENT])
            after = remaining[client] - row[Column.TARGET_FIT_ROWS]
            if after >= rule.target_min_remaining_fit:
                remaining[client] = after
                chosen.append(TargetPair(client=client, family=family))
                break
    return chosen


def permute_family_labels(
    labelled: LabelledTable, seed: RandomSeed, offset: RandomSeed
) -> LabelledTable:
    eligible = (labelled[Column.REASON] == EligibilityReason.ELIGIBLE).to_numpy()
    positions = np.flatnonzero(eligible)
    rng = np.random.default_rng(np.random.SeedSequence([seed, offset]))
    permuted = labelled[Column.FAMILY].to_numpy().copy()
    permuted[positions] = permuted[positions][rng.permutation(positions.size)]
    return labelled.with_columns(pl.Series(Column.FAMILY, permuted))


def _first_occurrence_ids(labels: IdentityIds) -> IdentityIds:
    _, first_index, inverse = np.unique(labels, return_index=True, return_inverse=True)
    rank = np.empty(first_index.size, dtype=np.int64)
    rank[np.argsort(first_index, kind=LibraryOption.SORT_STABLE)] = np.arange(first_index.size)
    return rank[inverse.reshape(-1)]


def feature_identities(features: BinaryMatrix) -> IdentityIds:
    packed = np.ascontiguousarray(np.packbits(features, axis=1))
    voids = packed.view(np.dtype((np.void, packed.shape[1]))).reshape(-1)
    _, inverse = np.unique(voids, return_inverse=True)
    return _first_occurrence_ids(inverse.reshape(-1).astype(np.int64))


def package_identities(packages: PackageSeries) -> IdentityIds:
    return _first_occurrence_ids(
        packages.rank(LibraryOption.RANK_DENSE).to_numpy().astype(np.int64)
    )


def connected_component_ids(package_ids: IdentityIds, feature_ids: IdentityIds) -> GroupIds:
    rows = package_ids.size
    package_count = package_ids.max(initial=-1).item() + 1
    feature_count = feature_ids.max(initial=-1).item() + 1
    row_index = np.arange(rows)
    sources = np.concatenate([row_index, row_index])
    targets = np.concatenate([rows + package_ids, rows + package_count + feature_ids])
    nodes = rows + package_count + feature_count
    graph = coo_matrix(
        (np.ones(sources.size, dtype=np.int8), (sources, targets)), shape=(nodes, nodes)
    )
    _, labels = connected_components(graph, directed=False)
    return _first_occurrence_ids(labels[:rows].astype(np.int64))


def build_identities(assignments: AssignmentsTable, features: BinaryMatrix) -> IdentitiesTable:
    package_ids = package_identities(assignments[Column.PACKAGE])
    feature_ids = feature_identities(features)
    return pl.DataFrame(
        {
            Column.SHA256: assignments[Column.SHA256],
            Column.PACKAGE_ID: package_ids,
            Column.FEATURE_ID: feature_ids,
            Column.COMPONENT: connected_component_ids(package_ids, feature_ids),
        }
    ).with_row_index(Column.ROW)


def grouping_ids(identities: IdentitiesTable, grouping: Grouping) -> GroupIds:
    column = Column.COMPONENT if grouping is Grouping.COMPONENT else Column.PACKAGE_ID
    return identities[column].to_numpy().astype(np.int64)


def component_summary(
    identities: IdentitiesTable, assignments: AssignmentsTable
) -> ComponentSummaryTable:
    return (
        identities.with_columns(assignments[Column.LABEL])
        .group_by(Column.COMPONENT)
        .agg(
            pl.len().alias(Column.ROWS),
            (pl.col(Column.LABEL) == 1).sum().alias(Column.MALWARE_ROWS),
            pl.col(Column.PACKAGE_ID).n_unique().alias(Column.PACKAGES),
        )
        .sort(Column.COMPONENT)
    )


def assign_clients(joined: JoinedTable, config: DataConfig) -> AssignmentsTable:
    single = joined.filter(pl.col(Column.MARKET_COUNT) == MarketCount.SINGLE)
    early_play = pl.col(Column.YEAR_MONTH) < config.play_era_boundary
    client = (
        pl.when(pl.col(Column.MARKETS) == Market.GOOGLE_PLAY)
        .then(
            pl.when(early_play)
            .then(pl.lit(ClientId.PLAY_EARLY))
            .otherwise(pl.lit(ClientId.PLAY_LATE))
        )
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


def client_support(assignments: AssignmentsTable) -> ClientSupportTable:
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
