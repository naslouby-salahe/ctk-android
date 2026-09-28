from pathlib import Path

import polars as pl

from ctk_android.config import load_config
from ctk_android.data.cache import write_table
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
    Representation,
    RepresentationGroup,
    RepresentationMeasure,
)
from ctk_android.paths import Paths
from ctk_android.reporting import evidence_figures
from tests.architecture.source_index import REPO_ROOT

CONFIG = load_config(Paths(REPO_ROOT))
ALPHA = CONFIG.experiments.operating.primary_alpha
EXTENSION_B = ExecutionMode.EXTENSION_B
POPULATIONS = (EvaluationPopulation.OWN_DOMAIN, EvaluationPopulation.FEDERATION_WIDE)


def _effects(
    contrasts: tuple[ExtensionContrast, ...], levels: tuple[int | None, ...]
) -> pl.DataFrame:
    rows = [
        {
            Column.SCOPE: ExtensionScope.POOLED,
            Column.LEARNER: learner,
            Column.POPULATION: population,
            Column.ALPHA: ALPHA,
            Column.CONTRAST: contrast,
            Column.LEVEL: level,
            Column.MEAN: 0.05,
            Column.CI_LOW: 0.01,
            Column.CI_HIGH: 0.09,
            Column.MARGIN: 0.03,
        }
        for learner in (Learner.CENTRAL, Learner.FEDAVG)
        for population in POPULATIONS
        for contrast in contrasts
        for level in levels
    ]
    return pl.DataFrame(rows, schema_overrides={Column.LEVEL: pl.Int64})


def _synthetic(paths: Paths) -> None:
    write_table(
        _effects((ExtensionContrast.DOSE_CTK,), (0, 10, 50)),
        paths.analysis_file(EXTENSION_B, Artifact.DOSE_EFFECTS),
    )
    write_table(
        _effects(
            (
                ExtensionContrast.PLACEBO_EFFECT,
                ExtensionContrast.CTK_MINUS_PLACEBO,
                ExtensionContrast.CTK_MEAN,
                ExtensionContrast.CTK_TRIMMED,
                ExtensionContrast.CTK_MEDIAN,
            ),
            (None,),
        ),
        paths.analysis_file(EXTENSION_B, Artifact.CONTROLS_EFFECTS),
    )
    write_table(
        pl.DataFrame(
            {
                Column.FAMILY: ["a", "b", "c"],
                Column.CTK_GAIN: [0.2, 0.01, -0.03],
                Column.CTK_SD: [0.02, 0.03, None],
                Column.NOVELTY: [2.0, 1.0, 0.5],
                Column.MEETS_THRESHOLD: [True, False, False],
            },
            schema_overrides={Column.CTK_SD: pl.Float64},
        ),
        paths.analysis_file(EXTENSION_B, Artifact.LARGE_FAMILY_CTK),
    )
    write_table(
        pl.DataFrame(
            [
                {
                    Column.MEASURE: measure,
                    Column.REPRESENTATION: representation,
                    Column.GROUP: group,
                    Column.ALPHA: ALPHA,
                    Column.POPULATION: EvaluationPopulation.FEDERATION_WIDE,
                    Column.MEAN: 0.1,
                    Column.CI_LOW: 0.0,
                    Column.CI_HIGH: 0.2,
                }
                for measure in RepresentationMeasure
                for representation in Representation
                for group in (
                    RepresentationGroup.PRIORITY_MACRO,
                    RepresentationGroup.CONTRAST_MACRO,
                )
            ]
        ),
        paths.analysis_file(EXTENSION_B, Artifact.REPRESENTATION_LEVELS),
    )
    clients = pl.DataFrame(
        {
            Column.EXPERIMENT: ["x"] * len(ClientId),
            Column.CLIENT: list(ClientId),
            Column.REQUESTED_ALPHA: [ALPHA] * len(ClientId),
            Column.CLIENT_REALISED_FPR: [0.05, 0.05, 0.11, 0.05],
            Column.MAX_FPR_DEVIATION: [0.01, 0.01, 0.07, 0.01],
        }
    )
    write_table(
        clients, paths.analysis_file(ExecutionMode.CONFIRMATORY, Artifact.OPERATING_CLIENT_SUMMARY)
    )
    write_table(clients, paths.analysis_file(EXTENSION_B, Artifact.DIAGNOSTIC_FPR_CLIENTS))


def test_every_evidence_figure_is_built_from_published_tables_only(tmp_path: Path) -> None:
    paths = Paths(tmp_path)
    _synthetic(paths)
    evidence_figures.build_evidence_figures(paths, CONFIG)
    for figure in EvidenceFigure:
        for suffix in (FileSuffix.PDF, FileSuffix.PNG):
            assert paths.evidence_figure_file(figure, suffix).stat().st_size > 0, (figure, suffix)


def test_the_figure_set_covers_every_extension_study_the_report_publishes() -> None:
    assert {figure.value for figure in EvidenceFigure} == {
        "exact-dose-response",
        "placebo-negative-controls",
        "robust-aggregation-controls",
        "large-family-ctk-heterogeneity",
        "representation-comparison",
        "fpr-client-diagnostics",
    }


def test_axis_labels_name_their_estimand_instead_of_a_generic_recall_gain() -> None:
    from ctk_android.enums import PlotText

    for label in (
        PlotText.CTK_AT_DOSE,
        PlotText.FAMILY_MACRO_GAIN,
        PlotText.FAMILY_CTK_GAIN,
        PlotText.REPRESENTATION_CTK,
        PlotText.REPRESENTATION_FULL,
    ):
        assert "amily" in label.value
    assert PlotText.FPR_CLIENT.value.lower().startswith("mean realised benign fpr")
    assert PlotText.GAIN.value == "Gain in recall"
    used = (REPO_ROOT / "src/ctk_android/reporting/evidence_figures.py").read_text(encoding="utf-8")
    assert "PlotText.GAIN" not in used
