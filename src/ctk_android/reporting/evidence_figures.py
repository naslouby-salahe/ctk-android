import numpy as np
import polars as pl
from matplotlib.figure import Figure

from ctk_android.config import Config
from ctk_android.enums import (
    Artifact,
    ClientId,
    Column,
    EvaluationPopulation,
    EvidenceFigure,
    ExecutionMode,
    ExtensionContrast,
    ExtensionScope,
    FileSuffix,
    Learner,
    LibraryOption,
    PlotGeometry,
    PlotText,
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
    SubplotGrid,
)
from ctk_android.paths import Paths
from ctk_android.types import (
    BarGroup,
    Effect,
    EffectsTable,
    PlotAxes,
    PlotFigure,
    PlotSize,
    PlotVector,
    Table,
)


def _blank(
    width: PlotSize = PlotGeometry.WIDTH, height: PlotSize = PlotGeometry.HEIGHT
) -> PlotFigure:
    return Figure(figsize=(width, height))


def _save(figure: PlotFigure, paths: Paths, name: EvidenceFigure) -> None:
    for suffix in (FileSuffix.PDF, FileSuffix.PNG):
        target = paths.evidence_figure_file(name, suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(target, dpi=PlotGeometry.DPI, bbox_inches=LibraryOption.BBOX_TIGHT)


def _extension(paths: Paths, artifact: Artifact) -> Table:
    return pl.read_parquet(paths.analysis_file(ExecutionMode.EXTENSION_B, artifact))


def _effects(paths: Paths, config: Config, artifact: Artifact) -> EffectsTable:
    return _extension(paths, artifact).filter(
        (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(Column.SCOPE) == ExtensionScope.POOLED)
    )


def _whiskers(rows: Table) -> PlotVector:
    mean = rows[Column.MEAN].to_numpy()
    return np.vstack(
        [mean - rows[Column.CI_LOW].to_numpy(), rows[Column.CI_HIGH].to_numpy() - mean]
    )


def _headroom(rows: Table) -> Effect:
    return rows[Column.CI_HIGH].to_numpy().max().item() * PlotGeometry.HEADROOM


def _populations(rows: Table) -> list[EvaluationPopulation]:
    return [
        population
        for population in (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE)
        if population in rows[Column.POPULATION].to_list()
    ]


def _grouped_bars(axes: PlotAxes, rows: Table, groups: list[BarGroup]) -> None:
    populations = _populations(rows)
    positions = np.arange(len(populations))
    width = PlotGeometry.BAR_WIDTH * 2 / len(groups)
    for index, group in enumerate(groups):
        chosen = rows.filter(pl.col(Column.CONTRAST) == group.contrast)
        ordered = pl.concat(
            [chosen.filter(pl.col(Column.POPULATION) == population) for population in populations]
        )
        axes.bar(
            positions + (index - (len(groups) - 1) / 2) * width,
            ordered[Column.MEAN].to_numpy(),
            width,
            yerr=_whiskers(ordered),
            label=group.label,
        )
    axes.set_xticks(positions, populations)
    axes.axhline(0.0, color=LibraryOption.THRESHOLD_COLOR, linewidth=PlotGeometry.THIN_LINE)
    axes.axhline(
        rows[Column.MARGIN].max(),
        color=LibraryOption.NEUTRAL_COLOR,
        linestyle=LibraryOption.LINE_DASHED,
        label=PlotText.PRACTICAL_THRESHOLD,
    )
    axes.set_ylabel(PlotText.FAMILY_MACRO_GAIN)
    axes.set_ylim(top=_headroom(rows))
    axes.legend(loc=LibraryOption.UPPER_CENTER, ncol=SubplotGrid.COLUMNS)


def exact_dose_response(paths: Paths, config: Config) -> None:
    effects = _effects(paths, config, Artifact.DOSE_EFFECTS).filter(
        pl.col(Column.CONTRAST) == ExtensionContrast.DOSE_CTK
    )
    figure = _blank(PlotGeometry.FOREST_WIDTH)
    populations = _populations(effects)
    for position, population in enumerate(populations, start=1):
        axes = figure.add_subplot(SubplotGrid.ROWS, len(populations), position)
        for learner in (Learner.CENTRAL, Learner.FEDAVG):
            rows = effects.filter(
                (pl.col(Column.POPULATION) == population) & (pl.col(Column.LEARNER) == learner)
            ).sort(Column.LEVEL)
            axes.errorbar(
                np.arange(rows.height),
                rows[Column.MEAN].to_numpy(),
                yerr=_whiskers(rows),
                marker=LibraryOption.MARKER_CIRCLE,
                capsize=PlotGeometry.CAP_SIZE,
                label=learner,
            )
            axes.set_xticks(np.arange(rows.height), rows[Column.LEVEL].to_list())
        axes.axhline(0.0, color=LibraryOption.THRESHOLD_COLOR, linewidth=PlotGeometry.THIN_LINE)
        axes.set_xlabel(PlotText.DOSE_LEVEL)
        axes.set_ylabel(PlotText.CTK_AT_DOSE)
        axes.set_title(population)
        axes.legend()
    figure.suptitle(PlotText.DOSE_EXACT_TITLE)
    figure.subplots_adjust(top=PlotGeometry.TITLE_TOP)
    _save(figure, paths, EvidenceFigure.EXACT_DOSE_RESPONSE)


def placebo_controls(paths: Paths, config: Config) -> None:
    rows = _effects(paths, config, Artifact.CONTROLS_EFFECTS)
    figure = _blank()
    axes = figure.add_subplot()
    _grouped_bars(
        axes,
        rows.filter(pl.col(Column.LEARNER) == Learner.FEDAVG),
        [
            BarGroup(contrast=ExtensionContrast.PLACEBO_EFFECT, label=PlotText.PLACEBO_EFFECT),
            BarGroup(
                contrast=ExtensionContrast.CTK_MINUS_PLACEBO, label=PlotText.CTK_MINUS_PLACEBO
            ),
        ],
    )
    axes.set_title(PlotText.PLACEBO_TITLE)
    _save(figure, paths, EvidenceFigure.PLACEBO_CONTROLS)


def robust_aggregation(paths: Paths, config: Config) -> None:
    rows = _effects(paths, config, Artifact.CONTROLS_EFFECTS)
    figure = _blank()
    axes = figure.add_subplot()
    _grouped_bars(
        axes,
        rows.filter(pl.col(Column.LEARNER) == Learner.FEDAVG),
        [
            BarGroup(contrast=ExtensionContrast.CTK_MEAN, label=PlotText.AGG_MEAN),
            BarGroup(contrast=ExtensionContrast.CTK_TRIMMED, label=PlotText.AGG_TRIMMED),
            BarGroup(contrast=ExtensionContrast.CTK_MEDIAN, label=PlotText.AGG_MEDIAN),
        ],
    )
    axes.set_title(PlotText.AGGREGATION_TITLE)
    _save(figure, paths, EvidenceFigure.ROBUST_AGGREGATION)


def large_family_ctk(paths: Paths, config: Config) -> None:
    del config
    table = _extension(paths, Artifact.LARGE_FAMILY_CTK).sort(Column.CTK_GAIN, descending=True)
    figure = _blank(PlotGeometry.FOREST_WIDTH)
    ranked = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 1)
    scatter = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, 2)
    positions = np.arange(table.height)
    for meets, label in ((False, PlotText.LARGE_BELOW), (True, PlotText.LARGE_ABOVE)):
        chosen = table.with_row_index(Column.ROW).filter(pl.col(Column.MEETS_THRESHOLD) == meets)
        ranked.bar(
            positions[chosen[Column.ROW].to_numpy()],
            chosen[Column.CTK_GAIN].to_numpy(),
            yerr=chosen[Column.CTK_SD].fill_null(0.0).to_numpy(),
            label=label,
        )
        scatter.scatter(
            chosen[Column.NOVELTY].to_numpy(), chosen[Column.CTK_GAIN].to_numpy(), label=label
        )
    ranked.set_xticks(
        positions,
        table[Column.FAMILY].to_list(),
        rotation=PlotGeometry.VERTICAL_ROTATION,
        fontsize=PlotGeometry.SMALL_FONT,
    )
    ranked.axhline(0.0, color=LibraryOption.THRESHOLD_COLOR, linewidth=PlotGeometry.THIN_LINE)
    ranked.set_ylabel(PlotText.LARGE_RANKED)
    ranked.legend()
    scatter.set_xlabel(PlotText.NOVELTY)
    scatter.set_ylabel(PlotText.FAMILY_CTK_GAIN)
    figure.suptitle(PlotText.LARGE_TITLE)
    figure.subplots_adjust(top=PlotGeometry.TITLE_TOP)
    _save(figure, paths, EvidenceFigure.LARGE_FAMILY_CTK)


def representation_comparison(paths: Paths, config: Config) -> None:
    levels = _extension(paths, Artifact.REPRESENTATION_LEVELS).filter(
        (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    )
    figure = _blank(PlotGeometry.FOREST_WIDTH)
    present = [
        representation
        for representation in Representation
        if representation in levels[Column.REPRESENTATION].to_list()
    ]
    positions = np.arange(len(present))
    for panel, (measure, title) in enumerate(
        (
            (RepresentationMeasure.CTK, PlotText.REPRESENTATION_CTK),
            (RepresentationMeasure.FULL_EXPOSURE_RECALL, PlotText.REPRESENTATION_FULL),
        ),
        start=1,
    ):
        axes = figure.add_subplot(SubplotGrid.ROWS, SubplotGrid.COLUMNS, panel)
        for index, (group, label) in enumerate(
            (
                (RepresentationGroup.PRIORITY_MACRO, PlotText.PRIORITY),
                (RepresentationGroup.CONTRAST_MACRO, PlotText.CONTRAST),
            )
        ):
            rows = pl.concat(
                [
                    levels.filter(
                        (pl.col(Column.MEASURE) == measure)
                        & (pl.col(Column.GROUP) == group)
                        & (pl.col(Column.REPRESENTATION) == representation)
                    )
                    for representation in present
                ]
            )
            axes.bar(
                positions + (index - 0.5) * PlotGeometry.BAR_WIDTH,
                rows[Column.MEAN].to_numpy(),
                PlotGeometry.BAR_WIDTH,
                yerr=_whiskers(rows),
                label=label,
            )
        axes.set_xticks(
            positions, present, rotation=PlotGeometry.TICK_ROTATION, ha=LibraryOption.ALIGN_RIGHT
        )
        axes.axhline(0.0, color=LibraryOption.THRESHOLD_COLOR, linewidth=PlotGeometry.THIN_LINE)
        axes.set_title(title)
        axes.set_ylim(top=_headroom(levels.filter(pl.col(Column.MEASURE) == measure)))
        axes.legend(loc=LibraryOption.UPPER_CENTER, ncol=SubplotGrid.COLUMNS)
    figure.suptitle(PlotText.REPRESENTATION_TITLE)
    figure.subplots_adjust(top=PlotGeometry.TITLE_TOP)
    _save(figure, paths, EvidenceFigure.REPRESENTATION_COMPARISON)


def fpr_client_diagnostics(paths: Paths, config: Config) -> None:
    operating = config.experiments.operating
    figure = _blank()
    axes = figure.add_subplot()
    clients = list(ClientId)
    positions = np.arange(len(clients))
    sources = (
        (
            pl.read_parquet(
                paths.analysis_file(ExecutionMode.CONFIRMATORY, Artifact.OPERATING_CLIENT_SUMMARY)
            ),
            PlotText.CONFIRMATORY_SCOPE,
        ),
        (_extension(paths, Artifact.DIAGNOSTIC_FPR_CLIENTS), PlotText.EXTENSION_B_SCOPE),
    )
    for index, (table, label) in enumerate(sources):
        rows = table.filter(pl.col(Column.REQUESTED_ALPHA) == operating.primary_alpha)
        per_client = rows.group_by(Column.CLIENT, maintain_order=True).agg(
            pl.col(Column.CLIENT_REALISED_FPR).mean(), pl.col(Column.MAX_FPR_DEVIATION).max()
        )
        ordered = pl.concat(
            [per_client.filter(pl.col(Column.CLIENT) == client) for client in clients]
        )
        axes.bar(
            positions + (index - 0.5) * PlotGeometry.BAR_WIDTH,
            ordered[Column.CLIENT_REALISED_FPR].to_numpy(),
            PlotGeometry.BAR_WIDTH,
            label=PlotText.FPR_BAR_LABEL.format(measure=PlotText.FPR_CLIENT, scope=label),
        )
        axes.scatter(
            positions + (index - 0.5) * PlotGeometry.BAR_WIDTH,
            operating.primary_alpha + ordered[Column.MAX_FPR_DEVIATION].to_numpy(),
            marker=LibraryOption.MARKER_SQUARE,
            label=PlotText.FPR_BAR_LABEL.format(measure=PlotText.FPR_WORST, scope=label),
        )
    axes.axhline(
        operating.primary_alpha,
        color=LibraryOption.THRESHOLD_COLOR,
        linestyle=LibraryOption.LINE_DASHED,
        label=PlotText.FPR_REQUESTED,
    )
    for bound, label in (
        (operating.primary_alpha - operating.realised_fpr_tolerance, PlotText.FPR_TOLERANCE),
        (operating.primary_alpha + operating.realised_fpr_tolerance, None),
    ):
        axes.axhline(
            bound,
            color=LibraryOption.NEUTRAL_COLOR,
            linestyle=LibraryOption.LINE_DOTTED,
            label=label,
        )
    axes.set_xticks(positions, clients)
    axes.set_ylabel(PlotText.FPR_CLIENT)
    axes.set_title(PlotText.FPR_TITLE)
    axes.legend(fontsize=PlotGeometry.SMALL_FONT)
    _save(figure, paths, EvidenceFigure.FPR_CLIENT_DIAGNOSTICS)


def build_evidence_figures(paths: Paths, config: Config) -> None:
    exact_dose_response(paths, config)
    placebo_controls(paths, config)
    robust_aggregation(paths, config)
    large_family_ctk(paths, config)
    representation_comparison(paths, config)
    fpr_client_diagnostics(paths, config)
