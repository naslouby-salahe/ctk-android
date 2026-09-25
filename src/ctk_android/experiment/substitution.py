import numpy as np
import polars as pl
from numpy.random import Generator

from ctk_android.enums import (
    ClientId,
    Column,
    EligibilityReason,
    ErrorMessage,
    FailureReason,
    SplitRole,
)
from ctk_android.types import (
    ClientPieces,
    ClientRowCounts,
    CtkError,
    DoseDraw,
    FamilyFitRows,
    FamilyMasks,
    FamilyName,
    FamilyRows,
    FamilyRowTotals,
    MalwareRowsTable,
    PlaceboChoice,
    PlaceboOption,
    RowCount,
    RowIndices,
    StudyData,
    SupportCount,
    TargetPair,
    TrainingRows,
)


def _named_malware(study: StudyData) -> MalwareRowsTable:
    return (
        study.table.with_row_index(Column.ROW_POSITION)
        .filter((pl.col(Column.LABEL) == 1) & (pl.col(Column.REASON) == EligibilityReason.ELIGIBLE))
        .select(Column.ROW_POSITION, Column.CLIENT, Column.FAMILY, Column.ROLE)
    )


def family_fit_rows(study: StudyData) -> FamilyFitRows:
    grouped = (
        _named_malware(study)
        .filter(pl.col(Column.ROLE) == SplitRole.FIT)
        .group_by(Column.FAMILY, Column.CLIENT)
        .agg(pl.col(Column.ROW_POSITION))
    )
    rows: FamilyFitRows = {}
    for record in grouped.iter_rows(named=True):
        rows.setdefault(record[Column.FAMILY], {})[ClientId(record[Column.CLIENT])] = np.sort(
            np.asarray(record[Column.ROW_POSITION], dtype=np.int64)
        )
    return rows


def family_totals(study: StudyData) -> FamilyRowTotals:
    counted = _named_malware(study).group_by(Column.FAMILY).agg(pl.len().alias(Column.ROWS))
    return dict(zip(counted[Column.FAMILY].to_list(), counted[Column.ROWS].to_list(), strict=True))


def _peer_rows(fit: FamilyFitRows, family: FamilyName, target: ClientId) -> TrainingRows:
    empty: RowIndices = np.empty(0, dtype=np.int64)
    return {
        client: fit.get(family, {}).get(client, empty)
        for client in ClientId
        if client is not target
    }


def draw_dose(
    fit: FamilyFitRows, base: TrainingRows, targets: tuple[TargetPair, ...], rng: Generator
) -> DoseDraw:
    pooled: FamilyRows = {}
    owners: FamilyRows = {}
    clients = list(ClientId)
    for pair in targets:
        peers = _peer_rows(fit, pair.family, pair.client)
        rows = np.concatenate(list(peers.values()))
        holder = np.concatenate(
            [np.full(part.size, clients.index(client)) for client, part in peers.items()]
        )
        order = rng.permutation(rows.size)
        pooled[pair.family] = rows[order]
        owners[pair.family] = holder[order]
    return DoseDraw(
        pooled=pooled,
        owners=owners,
        replacement_order={client: rng.permutation(rows.size) for client, rows in base.items()},
    )


def dose_extras(
    draw: DoseDraw, targets: tuple[TargetPair, ...], dose: SupportCount
) -> TrainingRows:
    clients = list(ClientId)
    parts: ClientPieces = {client: [] for client in clients}
    for pair in targets:
        rows, holder = draw.pooled[pair.family][:dose], draw.owners[pair.family][:dose]
        for index, client in enumerate(clients):
            parts[client].append(rows[holder == index])
    return {
        client: np.concatenate(pieces) if pieces else np.empty(0, dtype=np.int64)
        for client, pieces in parts.items()
    }


def substitute(base: TrainingRows, extras: TrainingRows, order: TrainingRows) -> TrainingRows:
    result: TrainingRows = {}
    for client, rows in base.items():
        added = extras[client]
        replaced = rows.copy()
        replaced[order[client][: added.size]] = added
        result[client] = replaced
    return result


def _counts(masks: FamilyMasks, peer: TrainingRows, pair: TargetPair) -> ClientRowCounts:
    return {
        client: masks[pair.family][rows].sum().item()
        for client, rows in peer.items()
        if client is not pair.client
    }


def _available(
    fit: FamilyFitRows, base: TrainingRows, family: FamilyName, target: ClientId
) -> TrainingRows:
    return {
        client: np.setdiff1d(rows, base[client])
        for client, rows in _peer_rows(fit, family, target).items()
    }


def _allocate(counts: ClientRowCounts, free: TrainingRows) -> ClientRowCounts:
    allocated = {client: min(count, free[client].size) for client, count in counts.items()}
    remaining = sum(counts.values()) - sum(allocated.values())
    for client in allocated:
        moved = min(free[client].size - allocated[client], remaining)
        allocated[client] += moved
        remaining -= moved
    return allocated


def _hidden_fit(fit: FamilyFitRows, pair: TargetPair) -> RowCount:
    return sum(rows.size for rows in _peer_rows(fit, pair.family, pair.client).values())


def choose_placebos(
    fit: FamilyFitRows,
    totals: FamilyRowTotals,
    masks: FamilyMasks,
    peer: TrainingRows,
    base: TrainingRows,
    targets: tuple[TargetPair, ...],
    minimum: SupportCount,
) -> tuple[PlaceboChoice, ...]:
    taken = {pair.family for pair in targets}
    choices: list[PlaceboChoice] = []
    for pair in sorted(targets, key=lambda item: (-_hidden_fit(fit, item), item.family)):
        counts = _counts(masks, peer, pair)
        need: RowCount = sum(counts.values())
        hidden_fit = _hidden_fit(fit, pair)
        options: list[PlaceboOption] = []
        for family in sorted(totals):
            if family in taken or totals[family] < minimum:
                continue
            free = _available(fit, base, family, pair.client)
            if sum(rows.size for rows in free.values()) >= need:
                peer_fit = sum(rows.size for rows in _peer_rows(fit, family, pair.client).values())
                options.append(
                    PlaceboOption(
                        distance=abs(peer_fit - hidden_fit), family=family, peer_fit=peer_fit
                    )
                )
        if not options:
            raise CtkError(
                FailureReason.NO_ELIGIBLE_TARGETS,
                ErrorMessage.NO_PLACEBO.format(family=pair.family, need=need),
            )
        best = min(options, key=lambda option: (option.distance, option.family))
        taken.add(best.family)
        allocated = _allocate(counts, _available(fit, base, best.family, pair.client))
        choices.append(
            PlaceboChoice(
                client=pair.client,
                family=pair.family,
                placebo=best.family,
                counts=counts,
                allocated=allocated,
                reallocated=sum(
                    max(allocated[client] - count, 0) for client, count in counts.items()
                ),
                hidden_peer_fit=hidden_fit,
                placebo_peer_fit=best.peer_fit,
            )
        )
    return tuple(choices)


def placebo_extras(
    fit: FamilyFitRows,
    base: TrainingRows,
    choices: tuple[PlaceboChoice, ...],
    rng: Generator,
) -> TrainingRows:
    parts: ClientPieces = {client: [] for client in ClientId}
    for choice in choices:
        free = _available(fit, base, choice.placebo, choice.client)
        for client, count in choice.allocated.items():
            parts[client].append(rng.permutation(free[client])[:count])
    return {
        client: np.concatenate(pieces) if pieces else np.empty(0, dtype=np.int64)
        for client, pieces in parts.items()
    }
