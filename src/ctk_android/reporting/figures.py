import numpy as np
import polars as pl
from matplotlib.figure import Figure

from ctk_android.config import Config
from ctk_android.enums import (
    Artifact,
    Column,
    Estimand,
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
    SubplotGrid,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    Directory,
    Effect,
    EffectsTable,
    FamilyRescueTable,
    PlotAxes,
    PlotBand,
    PlotFigure,
    PlotVector,
    SummaryTable,
)


def _blank() -> PlotFigure:
    return Figure(figsize=(PlotGeometry.WIDTH, PlotGeometry.HEIGHT))


def _axes(figure: PlotFigure) -> PlotAxes:
    return figure.add_subplot()


def _save(figure: PlotFigure, paths: Paths, name: ReportFigure) -> None:
    for suffix in (FileSuffix.PDF, FileSuffix.PNG):
        target = paths.report_figure_file(name, suffix)
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
    _save(figure, paths, ReportFigure.COLLABORATION_DECOMPOSITION)


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
        mean = np.array(
            [
                _mean(summary, learner, ExposureCondition.PEER_PRESENT, mean_metric)
                for learner in learners
            ]
        )
        worst = np.array(
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
    _save(figure, paths, ReportFigure.MEAN_VERSUS_WORST_CLIENT)


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
    _save(figure, paths, ReportFigure.OWN_DOMAIN_VERSUS_FEDERATION_WIDE)


def peer_dose_response(paths: Paths, mode: ExecutionMode) -> None:
    curve = pl.read_parquet(paths.analysis_file(mode, Artifact.PEER_DOSE_RESPONSE))
    figure = _blank()
    axes = _axes(figure)
    for learner in curve[Column.LEARNER].unique():
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
    _save(figure, paths, ReportFigure.PEER_DOSE_RESPONSE)


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
    _save(figure, paths, ReportFigure.FAMILY_RESCUE_MAP)


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
    _save(figure, paths, ReportFigure.FEATURE_NOVELTY_VERSUS_CTK_GAIN)


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
    _save(figure, paths, ReportFigure.KNOWN_VERSUS_UNSEEN_TRADEOFF)


def robustness_summary(paths: Paths, mode: ExecutionMode) -> None:
    table = pl.read_parquet(paths.statistics_file(mode, Artifact.PAIRED_EFFECTS)).filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & (pl.col(Column.ESTIMAND) == Estimand.CTK_GAIN)
        & (pl.col(Column.METRIC) == Metric.FEDERATION_UNSEEN_RECALL)
    )
    figure = _blank()
    axes = _axes(figure)
    labels = [
        PlotText.ROBUSTNESS_ROW.format(experiment=row[Column.EXPERIMENT], alpha=row[Column.ALPHA])
        for row in table.iter_rows(named=True)
    ]
    means = table[Column.MEAN_DIFFERENCE].to_numpy()
    low = table[Column.CI_LOW].fill_null(table[Column.MEAN_DIFFERENCE]).to_numpy()
    high = table[Column.CI_HIGH].fill_null(table[Column.MEAN_DIFFERENCE]).to_numpy()
    axes.errorbar(
        means, range(len(labels)), xerr=[means - low, high - means], fmt=LibraryOption.MARKER_CIRCLE
    )
    axes.set_yticks(range(len(labels)), labels)
    axes.set_xlabel(PlotText.GAIN)
    axes.set_title(PlotText.ROBUSTNESS_TITLE)
    _save(figure, paths, ReportFigure.ROBUSTNESS_SUMMARY)


def build_figures(paths: Paths, config: Config, mode: ExecutionMode) -> Directory:
    collaboration_decomposition(paths, config, mode)
    mean_versus_worst_client(paths, config, mode)
    own_domain_versus_federation_wide(paths, config, mode)
    peer_dose_response(paths, mode)
    family_rescue_map(paths, mode)
    feature_novelty_versus_ctk_gain(paths, mode)
    known_versus_unseen_tradeoff(paths, config, mode)
    robustness_summary(paths, mode)
    return paths.report_figure_file(ReportFigure.ROBUSTNESS_SUMMARY, FileSuffix.PNG).parent
