import numpy as np
import polars as pl
from matplotlib.figure import Figure

from ctk_android.config import Config
from ctk_android.data.cache import is_one_of
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    CtkAggregation,
    Estimand,
    EvaluationPopulation,
    ExecutionMode,
    ExperimentName,
    ExposureCondition,
    FileSuffix,
    Learner,
    LibraryOption,
    Metric,
    PlotGeometry,
    PlotText,
    ReportFigure,
    RobustnessScope,
    SubplotGrid,
    TradeoffComparison,
    TradeoffMeasure,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    ClientCtkTable,
    ComparisonTable,
    Directory,
    Effect,
    EffectsTable,
    FamilyRescueTable,
    ForestRow,
    ForestText,
    PlotAxes,
    PlotBand,
    PlotFigure,
    PlotSize,
    PlotVector,
    SummaryTable,
    SynthesisTable,
)


def _blank(
    width: PlotSize = PlotGeometry.WIDTH, height: PlotSize = PlotGeometry.HEIGHT
) -> PlotFigure:
    return Figure(figsize=(width, height))


def _axes(figure: PlotFigure) -> PlotAxes:
    return figure.add_subplot()


def _save(figure: PlotFigure, paths: Paths, mode: ExecutionMode, name: ReportFigure) -> None:
    for suffix in (FileSuffix.PDF, FileSuffix.PNG):
        target = paths.report_figure_file(mode, name, suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(target, dpi=PlotGeometry.DPI, bbox_inches=LibraryOption.BBOX_TIGHT)


def _summary(paths: Paths, config: Config, mode: ExecutionMode) -> SummaryTable:
    return pl.read_parquet(paths.analysis_file(mode, Artifact.ARM_METRICS)).filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & pl.col(Column.DOSE).is_null()
    )


def _mean(
    summary: SummaryTable, learner: Learner, condition: ExposureCondition, metric: Metric
) -> Effect | None:
    values = (
        summary.filter(
            (pl.col(Column.LEARNER) == learner)
            & (pl.col(Column.CONDITION) == condition)
            & (pl.col(Column.METRIC) == metric)
        )[Column.VALUE]
        .drop_nulls()
        .to_numpy()
    )
    return values.mean().item() if values.size else None


def _effects(paths: Paths, config: Config, mode: ExecutionMode) -> EffectsTable:
    return pl.read_parquet(paths.statistics_file(mode, Artifact.PAIRED_EFFECTS)).filter(
        pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha
    )


def _effect(
    effects: EffectsTable, learner: Learner, estimand: Estimand, metric: Metric
) -> PlotBand:
    row = effects.filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.ESTIMAND) == estimand)
        & (pl.col(Column.METRIC) == metric)
    )
    if row.height == 0:
        return PlotBand(mean=None, lower=None, upper=None)
    mean = row[Column.MEAN_DIFFERENCE].item()
    low, high = row[Column.CI_LOW].item(), row[Column.CI_HIGH].item()
    return PlotBand(
        mean=mean,
        lower=None if low is None else mean - low,
        upper=None if high is None else high - mean,
    )


def _values(items: list[Effect | None]) -> PlotVector:
    return np.array(items, dtype=np.float64)


def _or_nan(value: Effect | None) -> Effect:
    return np.nan if value is None else value


def collaboration_decomposition(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    summary, effects = _summary(paths, config, mode), _effects(paths, config, mode)
    figure = _blank()
    axes = _axes(figure)
    learners = [Learner.CENTRAL, Learner.FEDAVG]
    positions = np.arange(len(learners))
    local = _or_nan(
        _mean(
            summary,
            Learner.LOCAL,
            ExposureCondition.PEER_PRESENT,
            Metric.FEDERATION_UNSEEN_RECALL,
        )
    )
    pooling = _values(
        [
            _effect(effects, learner, Estimand.POOLING_GAIN, Metric.FEDERATION_UNSEEN_RECALL).mean
            for learner in learners
        ]
    )
    ctk = _values(
        [
            _effect(effects, learner, Estimand.CTK_GAIN, Metric.FEDERATION_UNSEEN_RECALL).mean
            for learner in learners
        ]
    )
    axes.bar(positions, np.full(len(learners), local), PlotGeometry.BAR_WIDTH, label=PlotText.LOCAL)
    axes.bar(positions, pooling, PlotGeometry.BAR_WIDTH, bottom=local, label=PlotText.POOLING)
    axes.bar(positions, ctk, PlotGeometry.BAR_WIDTH, bottom=local + pooling, label=PlotText.CTK)
    ceiling = _or_nan(
        _mean(
            summary,
            Learner.CENTRAL,
            ExposureCondition.FULL_EXPOSURE,
            Metric.FEDERATION_UNSEEN_RECALL,
        )
    )
    axes.axhline(ceiling, linestyle=LibraryOption.LINE_DASHED, label=PlotText.FULL_CEILING)
    axes.set_xticks(positions, learners)
    axes.set_ylabel(PlotText.RECALL)
    axes.set_title(PlotText.DECOMPOSITION_TITLE)
    axes.legend()
    _save(figure, paths, mode, ReportFigure.COLLABORATION_DECOMPOSITION)


def mean_versus_worst_client(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    summary = _summary(paths, config, mode)
    figure = _blank()
    recall_axes = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 1)
    fnr_axes = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 2)
    learners = list(Learner)
    positions = np.arange(len(learners))
    for axes, title, mean_metric, worst_metric in (
        (
            recall_axes,
            PlotText.RECALL,
            Metric.FEDERATION_UNSEEN_RECALL,
            Metric.WORST_CLIENT_UNSEEN_RECALL,
        ),
        (fnr_axes, PlotText.FNR, Metric.FEDERATION_UNSEEN_RECALL, Metric.WORST_CLIENT_FNR),
    ):
        mean = _values(
            [
                _mean(summary, learner, ExposureCondition.PEER_PRESENT, mean_metric)
                for learner in learners
            ]
        )
        worst = _values(
            [
                _mean(summary, learner, ExposureCondition.PEER_PRESENT, worst_metric)
                for learner in learners
            ]
        )
        axes.bar(
            positions - PlotGeometry.BAR_WIDTH / 2,
            1.0 - mean if worst_metric is Metric.WORST_CLIENT_FNR else mean,
            PlotGeometry.BAR_WIDTH,
            label=PlotText.MEAN_CLIENT,
        )
        axes.bar(
            positions + PlotGeometry.BAR_WIDTH / 2,
            worst,
            PlotGeometry.BAR_WIDTH,
            label=PlotText.WORST_CLIENT,
        )
        axes.set_xticks(positions, learners, rotation=PlotGeometry.TICK_ROTATION)
        axes.set_title(title)
    recall_axes.legend()
    figure.suptitle(PlotText.MEAN_VERSUS_WORST_TITLE)
    _save(figure, paths, mode, ReportFigure.MEAN_VERSUS_WORST_CLIENT)


def own_domain_versus_federation_wide(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    effects = _effects(paths, config, mode)
    figure = _blank()
    axes = _axes(figure)
    learners = [Learner.CENTRAL, Learner.FEDAVG]
    positions = np.arange(len(learners))
    for offset, metric, label in (
        (-PlotGeometry.BAR_WIDTH / 2, Metric.OWN_DOMAIN_UNSEEN_RECALL, PlotText.OWN_DOMAIN),
        (PlotGeometry.BAR_WIDTH / 2, Metric.FEDERATION_UNSEEN_RECALL, PlotText.FEDERATION_WIDE),
    ):
        bands = [_effect(effects, learner, Estimand.CTK_GAIN, metric) for learner in learners]
        axes.bar(
            positions + offset,
            _values([band.mean for band in bands]),
            PlotGeometry.BAR_WIDTH,
            yerr=np.vstack(
                [_values([band.lower for band in bands]), _values([band.upper for band in bands])]
            ),
            label=label,
        )
    axes.set_xticks(positions, learners)
    axes.set_ylabel(PlotText.GAIN)
    axes.set_title(PlotText.DOMAIN_TITLE)
    axes.legend()
    _save(figure, paths, mode, ReportFigure.OWN_DOMAIN_VERSUS_FEDERATION_WIDE)


def peer_dose_response(paths: Paths, mode: ExecutionMode) -> None:
    curve = pl.read_parquet(paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE))
    figure = _blank()
    axes = _axes(figure)
    for learner in sorted(curve[Column.LEARNER].unique().to_list()):
        rows = (
            curve.filter(pl.col(Column.LEARNER) == learner)
            .group_by(Column.DOSE)
            .agg(pl.col(Column.EFFECTIVE_DOSE).mean(), pl.col(Column.RECALL).mean())
            .sort(Column.EFFECTIVE_DOSE)
        )
        axes.plot(
            rows[Column.EFFECTIVE_DOSE].to_numpy(),
            rows[Column.RECALL].to_numpy(),
            marker=LibraryOption.MARKER_CIRCLE,
            label=learner,
        )
    axes.set_xscale(LibraryOption.SCALE_SYMLOG)
    axes.set_xlabel(PlotText.EFFECTIVE_DOSE)
    axes.set_ylabel(PlotText.RECALL)
    axes.set_title(PlotText.DOSE_TITLE)
    axes.legend()
    _save(figure, paths, mode, ReportFigure.PEER_DOSE_RESPONSE)


def _family_rescue(paths: Paths, mode: ExecutionMode) -> FamilyRescueTable:
    return pl.read_parquet(paths.analysis_file(mode, Artifact.FAMILY_RESCUE)).filter(
        (pl.col(Column.EXPERIMENT) == ExperimentName.CONTROLLED_EXPOSURE)
        & (pl.col(Column.LEARNER) == Learner.FEDAVG)
    )


def family_rescue_map(paths: Paths, mode: ExecutionMode) -> None:
    table = _family_rescue(paths, mode).sort(Column.FAMILY)
    figure = _blank()
    axes = _axes(figure)
    columns = [Column.LOCAL_RECALL, Column.ABSENT_RECALL, Column.PEER_RECALL, Column.FULL_RECALL]
    matrix = table.select(columns).to_numpy() if table.height else np.zeros((1, len(columns)))
    image = axes.imshow(matrix, vmin=0.0, vmax=1.0, aspect=LibraryOption.ASPECT_AUTO)
    axes.set_xticks(
        range(len(columns)), [PlotText.LOCAL, PlotText.ABSENT, PlotText.PEER, PlotText.FULL]
    )
    axes.set_yticks(range(table.height), table[Column.FAMILY].to_list())
    axes.set_title(PlotText.RESCUE_TITLE)
    figure.colorbar(image, ax=axes)
    _save(figure, paths, mode, ReportFigure.FAMILY_RESCUE_MAP)


def feature_novelty_versus_ctk_gain(paths: Paths, mode: ExecutionMode) -> None:
    table = _family_rescue(paths, mode).drop_nulls(Column.NOVELTY)
    figure = _blank()
    axes = _axes(figure)
    axes.scatter(
        table[Column.NOVELTY].to_numpy(),
        table[Column.CTK_GAIN].to_numpy(),
        s=PlotGeometry.MARKER_SIZE,
    )
    for row in table.iter_rows(named=True):
        axes.annotate(row[Column.FAMILY], (row[Column.NOVELTY], row[Column.CTK_GAIN]))
    axes.set_xlabel(PlotText.NOVELTY)
    axes.set_ylabel(PlotText.GAIN)
    axes.set_title(PlotText.NOVELTY_TITLE)
    _save(figure, paths, mode, ReportFigure.FEATURE_NOVELTY_VERSUS_CTK_GAIN)


def known_versus_unseen_tradeoff(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    summary = _summary(paths, config, mode)
    figure = _blank()
    axes = _axes(figure)
    for learner in Learner:
        unseen = _mean(
            summary, learner, ExposureCondition.PEER_PRESENT, Metric.FEDERATION_UNSEEN_RECALL
        )
        known = _mean(summary, learner, ExposureCondition.PEER_PRESENT, Metric.KNOWN_FAMILY_RECALL)
        axes.scatter(_values([unseen]), _values([known]), s=PlotGeometry.MARKER_SIZE, label=learner)
    axes.set_xlabel(PlotText.UNSEEN_RECALL)
    axes.set_ylabel(PlotText.KNOWN_RECALL)
    axes.set_title(PlotText.TRADEOFF_TITLE)
    axes.legend()
    _save(figure, paths, mode, ReportFigure.KNOWN_VERSUS_UNSEEN_TRADEOFF)


def _forest_selection(synthesis: SynthesisTable, config: Config) -> SynthesisTable:
    primary = config.experiments.operating.primary_alpha
    scope = pl.col(Column.SCOPE)
    preferred = (pl.col(Column.LEARNER) == Learner.FEDAVG) | (
        (scope == RobustnessScope.TREE_MODEL) & (pl.col(Column.LEARNER) == Learner.CENTRAL)
    )
    federation = pl.col(Column.METRIC) == Metric.FEDERATION_UNSEEN_RECALL
    at_primary = pl.col(Column.ALPHA) == primary
    populations = is_one_of(Column.SCOPE, [RobustnessScope.PRIMARY_FAMILY_SET]) | is_one_of(
        Column.SCOPE, [RobustnessScope.NATURAL_SCARCITY]
    )
    paired = synthesis.filter(
        (pl.col(Column.AGGREGATION) == CtkAggregation.PAIRED_SEED_MACRO)
        & preferred
        & (
            (federation & at_primary)
            | (populations & at_primary)
            | ((scope == RobustnessScope.PRIMARY_FAMILY_SET) & federation)
        )
    )
    micro = synthesis.filter(
        (pl.col(Column.AGGREGATION) == CtkAggregation.MICRO_POOLED)
        & at_primary
        & is_one_of(
            Column.SCOPE,
            [
                RobustnessScope.PRIMARY_FAMILY_SET,
                RobustnessScope.REPLICATION_FAMILY_SET,
                RobustnessScope.NATURAL_SCARCITY,
            ],
        )
    )
    order = {name: index for index, name in enumerate(RobustnessScope)}
    return (
        pl.concat([paired, micro])
        .with_columns(pl.col(Column.SCOPE).replace_strict(order).alias(Column.SCOPE_ORDER))
        .sort(
            Column.AGGREGATION,
            Column.SCOPE_ORDER,
            Column.SALT,
            Column.METRIC,
            Column.SENSITIVITY,
            Column.ALPHA,
            descending=[True, False, False, False, False, False],
        )
    )


def _forest_label(row: ForestRow) -> ForestText:
    detail = row.metric or row.sensitivity
    if row.scope is RobustnessScope.PARTITION_SALT:
        detail = PlotText.FOREST_SALT.format(detail=detail, salt=row.salt)
    return PlotText.FOREST_ROW.format(
        scope=row.scope,
        detail=detail,
        learner=row.learner,
        alpha=row.alpha,
    )


def ctk_robustness_forest(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    synthesis = pl.read_parquet(paths.analysis_file(mode, Artifact.ROBUSTNESS_SYNTHESIS))
    table = _forest_selection(synthesis, config) if synthesis.height else synthesis
    if table.height == 0:
        _save(_blank(), paths, mode, ReportFigure.CTK_ROBUSTNESS_FOREST)
        return
    figure = _blank(
        PlotGeometry.FOREST_WIDTH,
        table.height * PlotGeometry.FOREST_ROW_HEIGHT + PlotGeometry.FOREST_MARGIN,
    )
    axes = _axes(figure)
    positions = np.arange(table.height)
    means = table[Column.MEAN_DIFFERENCE].to_numpy()
    low = table[Column.CI_LOW].fill_null(table[Column.MEAN_DIFFERENCE]).to_numpy()
    high = table[Column.CI_HIGH].fill_null(table[Column.MEAN_DIFFERENCE]).to_numpy()
    micro = (table[Column.AGGREGATION] == CtkAggregation.MICRO_POOLED).to_numpy()
    for selected, marker, label in (
        (~micro, LibraryOption.MARKER_CIRCLE, PlotText.PAIRED_SEED_LEGEND),
        (micro, LibraryOption.MARKER_SQUARE, PlotText.MICRO_POOLED_LEGEND),
    ):
        axes.errorbar(
            means[selected],
            positions[selected],
            xerr=[means[selected] - low[selected], high[selected] - means[selected]],
            fmt=marker,
            label=label,
        )
    axes.axvline(0.0, color=LibraryOption.NEUTRAL_COLOR)
    axes.axvline(
        config.statistics.gates.ctk_min_gain,
        linestyle=LibraryOption.LINE_DASHED,
        color=LibraryOption.THRESHOLD_COLOR,
        label=PlotText.PRACTICAL_THRESHOLD,
    )
    labels = [
        _forest_label(
            ForestRow(
                metric=row[Column.METRIC],
                sensitivity=row[Column.SENSITIVITY],
                scope=row[Column.SCOPE],
                salt=row[Column.SALT],
                learner=row[Column.LEARNER],
                alpha=row[Column.ALPHA],
            )
        )
        for row in table.iter_rows(named=True)
    ]
    axes.set_yticks(positions, labels)
    axes.tick_params(axis=LibraryOption.AXIS_Y, labelsize=PlotGeometry.SMALL_FONT)
    axes.set_ylim(table.height - 0.5, -0.5)
    axes.grid(axis=LibraryOption.AXIS_X, alpha=PlotGeometry.GRID_ALPHA)
    axes.set_xlabel(PlotText.FOREST_AXIS)
    axes.set_title(PlotText.FOREST_TITLE)
    axes.legend(
        loc=LibraryOption.UPPER_CENTER,
        bbox_to_anchor=(PlotGeometry.LEGEND_ANCHOR_X, PlotGeometry.LEGEND_ANCHOR_Y),
    )
    figure.subplots_adjust(left=PlotGeometry.FOREST_LEFT)
    _save(figure, paths, mode, ReportFigure.CTK_ROBUSTNESS_FOREST)


def federated_arm_tradeoff_figure(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    table = pl.read_parquet(paths.analysis_file(mode, Artifact.ARM_TRADEOFF))
    if table.height:
        table = table.filter(pl.col(Column.COMPARISON) == TradeoffComparison.VERSUS_LOCAL)
    if table.height == 0:
        _save(_blank(), paths, mode, ReportFigure.FEDERATED_ARM_TRADEOFF)
        return
    measures = [
        TradeoffMeasure.FEDERATION_UNSEEN_RECALL_CHANGE,
        TradeoffMeasure.OWN_DOMAIN_UNSEEN_RECALL_CHANGE,
        TradeoffMeasure.WORST_CLIENT_UNSEEN_RECALL_CHANGE,
        TradeoffMeasure.CTK_GAIN,
        TradeoffMeasure.KNOWN_FAMILY_RECALL_CHANGE,
        TradeoffMeasure.REALISED_FPR_CHANGE,
    ]
    arms = [
        Learner.FEDAVG,
        Learner.FEDPROX,
        Learner.FEDAVG_FINETUNE,
        Learner.BLEND,
        Learner.CENTRAL,
    ]
    figure = _blank(PlotGeometry.PANEL_WIDTH, PlotGeometry.PANEL_HEIGHT)
    for index, measure in enumerate(measures, start=1):
        axes = figure.add_subplot(SubplotGrid.PANEL_ROWS, SubplotGrid.PANEL_COLUMNS, index)
        rows = table.filter(pl.col(Column.MEASURE) == measure)
        present = [arm for arm in arms if rows.filter(pl.col(Column.LEARNER) == arm).height]
        means = _values(
            [
                rows.filter(pl.col(Column.LEARNER) == arm)[Column.MEAN_DIFFERENCE].item()
                for arm in present
            ]
        )
        low = _values(
            [rows.filter(pl.col(Column.LEARNER) == arm)[Column.CI_LOW].item() for arm in present]
        )
        high = _values(
            [rows.filter(pl.col(Column.LEARNER) == arm)[Column.CI_HIGH].item() for arm in present]
        )
        positions = np.arange(len(present))
        axes.errorbar(
            means,
            positions,
            xerr=[
                means - np.where(np.isnan(low), means, low),
                np.where(np.isnan(high), means, high) - means,
            ],
            fmt=LibraryOption.MARKER_CIRCLE,
        )
        axes.axvline(0.0, color=LibraryOption.NEUTRAL_COLOR)
        axes.set_yticks(positions, present)
        axes.set_ylim(len(present) - 0.5, -0.5)
        axes.set_title(measure, fontsize=PlotGeometry.SMALL_FONT)
        axes.tick_params(labelsize=PlotGeometry.SMALL_FONT)
        if measure is TradeoffMeasure.KNOWN_FAMILY_RECALL_CHANGE:
            tolerance = config.statistics.gates.known_family_tolerance
            for bound in (-tolerance, tolerance):
                axes.axvline(bound, linestyle=LibraryOption.LINE_DASHED)
    figure.subplots_adjust(wspace=PlotGeometry.PANEL_SPACE, hspace=PlotGeometry.PANEL_SPACE)
    figure.suptitle(PlotText.TRADEOFF_SUPTITLE)
    _save(figure, paths, mode, ReportFigure.FEDERATED_ARM_TRADEOFF)


def natural_versus_controlled(paths: Paths, mode: ExecutionMode) -> None:
    table = pl.read_parquet(paths.analysis_file(mode, Artifact.NATURAL_COMPARISON))
    if table.height:
        table = table.filter(pl.col(Column.LEARNER) == Learner.FEDAVG)
    if table.height == 0:
        _save(_blank(), paths, mode, ReportFigure.NATURAL_VERSUS_CONTROLLED)
        return
    metrics = [
        Metric.FEDERATION_UNSEEN_RECALL,
        Metric.OWN_DOMAIN_UNSEEN_RECALL,
        Metric.WORST_CLIENT_UNSEEN_RECALL,
    ]
    estimands = [
        (Estimand.TOTAL_GAIN, PlotText.ESTIMAND_TOTAL),
        (Estimand.POOLING_GAIN, PlotText.ESTIMAND_POOLING),
        (Estimand.CTK_GAIN, PlotText.ESTIMAND_CTK),
    ]
    figure = _blank(PlotGeometry.PANEL_WIDTH, PlotGeometry.HEIGHT)
    for index, metric in enumerate(metrics, start=1):
        axes = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.THREE_COLUMNS, index)
        positions = np.arange(len(estimands))
        for offset, experiment, label in (
            (
                -PlotGeometry.BAR_WIDTH / 2,
                ExperimentName.CONTROLLED_EXPOSURE,
                PlotText.CONTROLLED_LABEL,
            ),
            (PlotGeometry.BAR_WIDTH / 2, ExperimentName.NATURAL_SCARCITY, PlotText.NATURAL_LABEL),
        ):
            bands = [_band(table, experiment, metric, estimand) for estimand, _ in estimands]
            axes.bar(
                positions + offset,
                _values([band.mean for band in bands]),
                PlotGeometry.BAR_WIDTH,
                yerr=np.vstack(
                    [
                        _values([band.lower for band in bands]),
                        _values([band.upper for band in bands]),
                    ]
                ),
                label=label,
            )
        axes.set_xticks(positions, [text for _, text in estimands])
        axes.set_title(metric, fontsize=PlotGeometry.SMALL_FONT)
        axes.axhline(0.0, color=LibraryOption.NEUTRAL_COLOR)
        if index == 1:
            axes.legend()
    figure.subplots_adjust(wspace=PlotGeometry.PANEL_SPACE)
    figure.suptitle(PlotText.NATURAL_TITLE)
    _save(figure, paths, mode, ReportFigure.NATURAL_VERSUS_CONTROLLED)


def client_ctk_figure(paths: Paths, config: Config, mode: ExecutionMode) -> None:
    table = pl.read_parquet(paths.analysis_file(mode, Artifact.CLIENT_CTK))
    if table.height == 0:
        _save(_blank(), paths, mode, ReportFigure.CLIENT_CTK_ANALYSIS)
        return
    figure = _blank(PlotGeometry.PANEL_WIDTH, PlotGeometry.HEIGHT)
    clients = list(ClientId)
    positions = np.arange(len(clients))
    gains = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 1)
    federation = table.filter(
        (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
        & (pl.col(Column.LEARNER) == Learner.FEDAVG)
    )
    for offset, gain, low, high, label in (
        (
            -PlotGeometry.BAR_WIDTH / 2,
            Column.POOLING_GAIN,
            Column.POOLING_CI_LOW,
            Column.POOLING_CI_HIGH,
            PlotText.POOLING,
        ),
        (
            PlotGeometry.BAR_WIDTH / 2,
            Column.CTK_GAIN,
            Column.CTK_CI_LOW,
            Column.CTK_CI_HIGH,
            PlotText.CTK,
        ),
    ):
        means = _values([_client_value(federation, client, gain) for client in clients])
        lower = _values([_client_value(federation, client, low) for client in clients])
        upper = _values([_client_value(federation, client, high) for client in clients])
        gains.bar(
            positions + offset,
            means,
            PlotGeometry.BAR_WIDTH,
            yerr=np.vstack(
                [
                    np.where(np.isnan(lower), 0.0, means - lower),
                    np.where(np.isnan(upper), 0.0, upper - means),
                ]
            ),
            label=label,
        )
    gains.axhline(0.0, color=LibraryOption.NEUTRAL_COLOR)
    gains.set_xticks(positions, clients)
    gains.set_ylabel(PlotText.GAIN)
    gains.legend()
    known = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 2)
    arms = [Learner.FEDAVG, Learner.FEDPROX, Learner.CENTRAL]
    width = PlotGeometry.BAR_WIDTH / 2
    for index, arm in enumerate(arms):
        rows = table.filter(
            (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
            & (pl.col(Column.LEARNER) == arm)
        )
        means = _values(
            [_client_value(rows, client, Column.KNOWN_FAMILY_CHANGE) for client in clients]
        )
        lower = _values(
            [_client_value(rows, client, Column.KNOWN_FAMILY_CHANGE_CI_LOW) for client in clients]
        )
        upper = _values(
            [_client_value(rows, client, Column.KNOWN_FAMILY_CHANGE_CI_HIGH) for client in clients]
        )
        known.bar(
            positions + (index - 1) * width,
            means,
            width,
            yerr=np.vstack([means - lower, upper - means]),
            label=arm,
        )
    tolerance = config.statistics.gates.known_family_tolerance
    for bound in (-tolerance, tolerance):
        known.axhline(bound, linestyle=LibraryOption.LINE_DASHED)
    known.set_xticks(positions, clients)
    known.set_title(PlotText.CLIENT_KNOWN_TITLE, fontsize=PlotGeometry.SMALL_FONT)
    known.legend()
    figure.suptitle(PlotText.CLIENT_TITLE, fontsize=PlotGeometry.SMALL_FONT)
    _save(figure, paths, mode, ReportFigure.CLIENT_CTK_ANALYSIS)


def _client_value(table: ClientCtkTable, client: ClientId, column: Column) -> Effect | None:
    row = table.filter(pl.col(Column.CLIENT) == client)
    return None if row.height == 0 else row[column].item()


def _band(
    table: ComparisonTable, experiment: ExperimentName, metric: Metric, estimand: Estimand
) -> PlotBand:
    row = table.filter(
        (pl.col(Column.EXPERIMENT) == experiment)
        & (pl.col(Column.METRIC) == metric)
        & (pl.col(Column.ESTIMAND) == estimand)
    )
    if row.height == 0:
        return PlotBand(mean=None, lower=None, upper=None)
    mean = row[Column.MEAN_DIFFERENCE].item()
    low, high = row[Column.CI_LOW].item(), row[Column.CI_HIGH].item()
    return PlotBand(
        mean=mean,
        lower=None if low is None else mean - low,
        upper=None if high is None else high - mean,
    )


def build_figures(paths: Paths, config: Config, mode: ExecutionMode) -> Directory:
    collaboration_decomposition(paths, config, mode)
    mean_versus_worst_client(paths, config, mode)
    own_domain_versus_federation_wide(paths, config, mode)
    peer_dose_response(paths, mode)
    family_rescue_map(paths, mode)
    feature_novelty_versus_ctk_gain(paths, mode)
    known_versus_unseen_tradeoff(paths, config, mode)
    ctk_robustness_forest(paths, config, mode)
    federated_arm_tradeoff_figure(paths, config, mode)
    natural_versus_controlled(paths, mode)
    client_ctk_figure(paths, config, mode)
    return paths.report_figure_file(mode, ReportFigure.CTK_ROBUSTNESS_FOREST, FileSuffix.PNG).parent
