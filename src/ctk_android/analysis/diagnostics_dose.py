import warnings
from itertools import pairwise

import numpy as np
import polars as pl
from scipy import optimize, stats
from sklearn.isotonic import IsotonicRegression

from ctk_android.analysis.diagnostics_statistics import (
    interval_high,
    interval_low,
    labelled,
    ordered_scopes,
    own_domain_minimum,
    percentile_limits,
    scope_members,
    seeded_bca,
    set_labels,
    spearman,
    spearman_p,
)
from ctk_android.config import Config
from ctk_android.enums import (
    Column,
    DiagnosticColumn,
    DiagnosticLimit,
    DiagnosticResamples,
    DiagnosticSeed,
    DoseCode,
    DoseFitLevel,
    DoseLevel,
    DoseModel,
    DoseResponseClass,
    DoseRole,
    EmaxBound,
    EmaxStart,
    EvaluationPopulation,
    EvidenceClass,
    ExperimentName,
    ExposureCondition,
    Learner,
    LibraryOption,
    NoveltyDescriptor,
    Separator,
    StatisticsLimit,
)
from ctk_android.types import (
    Alpha,
    DiagnosticMatrix,
    DiagnosticRow,
    DiagnosticRows,
    DiagnosticTable,
    DiagnosticVector,
    DoseDiagnostics,
    DoseFit,
    DoseName,
    Effect,
    FamilyCountsTable,
    FamilyLevelTable,
    NoveltyTable,
    ScopedExperiments,
    SupportCount,
)


def pair_ctk(
    families: FamilyCountsTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticTable:
    # CTK(d) = recall(d) - recall(dose 0) per target (client, family) pair; the natural
    # peer-present arm is carried as dose code -1.
    usable = families.filter(
        pl.col(Column.TRIALS)
        >= pl.when(pl.col(Column.POPULATION) == EvaluationPopulation.OWN_DOMAIN)
        .then(own_domain_minimum(config, experiments))
        .otherwise(1)
    ).with_columns((pl.col(Column.HITS) / pl.col(Column.TRIALS)).alias(Column.RECALL))
    keys = [
        Column.EXPERIMENT,
        Column.SEED,
        Column.LEARNER,
        Column.POPULATION,
        Column.ALPHA,
        Column.CLIENT,
        Column.FAMILY,
    ]
    base = usable.filter(
        (pl.col(Column.CONDITION) == ExposureCondition.EXACT_DOSE) & (pl.col(Column.DOSE) == 0)
    ).select(*keys, pl.col(Column.RECALL).alias(Column.BASELINE))
    arms = usable.filter(
        pl.col(Column.CONDITION).is_in(
            [ExposureCondition.EXACT_DOSE, ExposureCondition.PEER_PRESENT]
        )
    ).with_columns(
        pl.when(pl.col(Column.CONDITION) == ExposureCondition.PEER_PRESENT)
        .then(pl.lit(DoseCode.NATURAL, dtype=pl.Int64))
        .otherwise(pl.col(Column.DOSE))
        .alias(DiagnosticColumn.DOSE_CODE)
    )
    return (
        arms.join(base, on=keys)
        .with_columns((pl.col(Column.RECALL) - pl.col(Column.BASELINE)).alias(DiagnosticColumn.CTK))
        .join(set_labels(config, experiments), on=Column.EXPERIMENT)
    )


def seed_level(pairs: DiagnosticTable, scoped: ScopedExperiments) -> DiagnosticTable:
    # Pooled rows follow the official seed-paired convention: the family macro is taken over
    # the target pairs of both family sets within a seed.
    return (
        pairs.filter(pl.col(Column.EXPERIMENT).is_in(list(scoped.experiments)))
        .group_by(
            Column.SEED,
            Column.LEARNER,
            Column.POPULATION,
            Column.ALPHA,
            DiagnosticColumn.DOSE_CODE,
            maintain_order=True,
        )
        .agg(pl.col(DiagnosticColumn.CTK).mean())
    )


def family_seed_level(pairs: DiagnosticTable) -> DiagnosticTable:
    return pairs.group_by(
        DiagnosticColumn.SET,
        Column.SEED,
        Column.LEARNER,
        Column.POPULATION,
        Column.ALPHA,
        Column.FAMILY,
        DiagnosticColumn.DOSE_CODE,
        maintain_order=True,
    ).agg(pl.col(DiagnosticColumn.CTK).mean())


def dose_name(dose: SupportCount) -> DoseName:
    return DoseLevel.NATURAL if dose == DoseCode.NATURAL else f"{dose}"


def wide_by_dose(table: DiagnosticTable) -> DiagnosticTable:
    return table.pivot(
        on=DiagnosticColumn.DOSE_CODE, index=Column.SEED, values=DiagnosticColumn.CTK
    ).sort(Column.SEED)


def _column(wide: DiagnosticTable, dose: SupportCount) -> DiagnosticVector:
    return wide[f"{dose}"].to_numpy().astype(np.float64)


def _bca(values: DiagnosticVector, config: Config) -> DiagnosticRow:
    interval = seeded_bca(values, config, DiagnosticSeed.DOSE, StatisticsLimit.BCA_SEEDS)
    return {Column.CI_LOW: interval_low(interval), Column.CI_HIGH: interval_high(interval)}


def _role(
    learner: Learner, population: EvaluationPopulation, alpha: Alpha, config: Config
) -> DoseRole:
    primary = (
        learner is Learner.FEDAVG
        and population is EvaluationPopulation.FEDERATION_WIDE
        and alpha == config.experiments.operating.primary_alpha
    )
    return DoseRole.PRIMARY if primary else DoseRole.SECONDARY


def _selected(
    table: DiagnosticTable, learner: Learner, population: EvaluationPopulation, alpha: Alpha
) -> DiagnosticTable:
    return table.filter(
        (pl.col(Column.LEARNER) == learner)
        & (pl.col(Column.POPULATION) == population)
        & (pl.col(Column.ALPHA) == alpha)
    )


def _populations() -> tuple[EvaluationPopulation, ...]:
    return (EvaluationPopulation.FEDERATION_WIDE, EvaluationPopulation.OWN_DOMAIN)


def ctk_by_dose(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = seed_level(pairs, scoped)
        for learner in (Learner.FEDAVG, Learner.CENTRAL):
            for population in _populations():
                for alpha in config.experiments.operating.alphas:
                    wide = wide_by_dose(_selected(level, learner, population, alpha))
                    for dose in (*doses, DoseCode.NATURAL):
                        values = _column(wide, dose)
                        rows.append(
                            {
                                DiagnosticColumn.SET: scoped.scope,
                                Column.LEARNER: learner,
                                Column.POPULATION: population,
                                Column.ALPHA: alpha,
                                Column.ROLE: _role(learner, population, alpha, config),
                                Column.DOSE: dose_name(dose),
                                DiagnosticColumn.N: values.size,
                                Column.MEAN_CTK: values.mean().item(),
                                **_bca(values, config),
                                Column.POSITIVE_SEEDS: (values > 0).sum().item(),
                            }
                        )
    return rows


def dose_increments(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = seed_level(pairs, scoped)
        for learner in (Learner.FEDAVG, Learner.CENTRAL):
            for population in _populations():
                for alpha in config.experiments.operating.alphas:
                    wide = wide_by_dose(_selected(level, learner, population, alpha))
                    for low, high in pairwise(doses):
                        values = _column(wide, high) - _column(wide, low)
                        interval = _bca(values, config)
                        scale = DiagnosticLimit.DOSE_UNIT / (high - low)
                        lower, upper = interval[Column.CI_LOW], interval[Column.CI_HIGH]
                        rows.append(
                            {
                                DiagnosticColumn.SET: scoped.scope,
                                Column.LEARNER: learner,
                                Column.POPULATION: population,
                                Column.ALPHA: alpha,
                                Column.ROLE: _role(learner, population, alpha, config),
                                DiagnosticColumn.SEGMENT: f"{low}{Separator.ARROW}{high}",
                                DiagnosticColumn.N: values.size,
                                DiagnosticColumn.INCREMENT: values.mean().item(),
                                **interval,
                                DiagnosticColumn.PER_UNIT: values.mean().item() * scale,
                                DiagnosticColumn.PER_UNIT_LOW: None
                                if lower is None
                                else lower * scale,
                                DiagnosticColumn.PER_UNIT_HIGH: None
                                if upper is None
                                else upper * scale,
                            }
                        )
    return rows


def family_curves(families: DiagnosticTable, config: Config) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    rows: DiagnosticRows = []
    for population in _populations():
        selected = _selected(
            families, Learner.FEDAVG, population, config.experiments.operating.primary_alpha
        ).sort(DiagnosticColumn.SET, Column.FAMILY, maintain_order=True)
        for group in selected.partition_by(
            DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
        ):
            head = group.row(0, named=True)
            wide = wide_by_dose(group)
            for dose in (*doses, DoseCode.NATURAL):
                if f"{dose}" not in wide.columns:
                    continue
                values = wide[f"{dose}"].drop_nulls().to_numpy().astype(np.float64)
                rows.append(
                    {
                        DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                        Column.POPULATION: population,
                        Column.FAMILY: head[Column.FAMILY],
                        DiagnosticColumn.DOSE_CODE: dose,
                        Column.DOSE: dose_name(dose),
                        DiagnosticColumn.SEEDS: values.size,
                        Column.MEAN_CTK: values.mean().item(),
                        **_bca(values, config),
                    }
                )
    return rows


def _onset(group: DiagnosticTable, criterion: pl.Expr) -> SupportCount | None:
    hits = group.filter((pl.col(DiagnosticColumn.DOSE_CODE) > 0) & criterion)
    return None if hits.height == 0 else hits[DiagnosticColumn.DOSE_CODE].item(0)


def family_summary(curves: DiagnosticTable, config: Config) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    onset = config.statistics.gates.ctk_min_gain
    rows: DiagnosticRows = []
    for group in curves.partition_by(
        Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
    ):
        head = group.row(0, named=True)
        means = {row[DiagnosticColumn.DOSE_CODE]: row for row in group.iter_rows(named=True)}
        end = means[doses[-1]]
        lower = end[Column.CI_LOW]
        first_mean = _onset(group, pl.col(Column.MEAN_CTK) >= onset)
        first_interval = _onset(
            group, pl.col(Column.CI_LOW).is_not_null() & (pl.col(Column.CI_LOW) > 0)
        )
        responsive = not (end[Column.MEAN_CTK] < onset or lower is None or lower <= 0)
        early = first_mean is not None and first_mean <= DiagnosticLimit.EARLY_ONSET
        response = (
            DoseResponseClass.NONRESPONSIVE
            if not responsive
            else DoseResponseClass.EARLY
            if early
            else DoseResponseClass.LATE
        )
        rows.append(
            {
                DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                Column.POPULATION: head[Column.POPULATION],
                Column.FAMILY: head[Column.FAMILY],
                DiagnosticColumn.SEEDS: end[DiagnosticColumn.SEEDS],
                **{
                    f"{DiagnosticColumn.CTK}{dose}": means[dose][Column.MEAN_CTK]
                    for dose in doses[1:]
                },
                DiagnosticColumn.CTK_TOP_LOW: lower,
                DiagnosticColumn.CTK_TOP_HIGH: end[Column.CI_HIGH],
                DiagnosticColumn.NATURAL_CTK: means[DoseCode.NATURAL][Column.MEAN_CTK],
                DiagnosticColumn.ONSET_MEAN: first_mean,
                DiagnosticColumn.ONSET_INTERVAL: first_interval,
                DiagnosticColumn.RESPONSE_CLASS: response,
            }
        )
    return rows


def with_family_context(
    summary: DiagnosticTable, family_level: FamilyLevelTable, novelty: NoveltyTable
) -> DiagnosticTable:
    confirmatory = family_level.filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & pl.col(Column.EXPERIMENT).is_in(
            [ExperimentName.CONTROLLED_EXPOSURE, ExperimentName.REPLICATION_FAMILY_SET]
        )
    ).select(
        Column.FAMILY,
        Column.LOCAL_RECALL,
        Column.FULL_RECALL,
        pl.col(Column.CTK_GAIN).alias(DiagnosticColumn.CONFIRMATORY_CTK),
        pl.col(Column.NOVELTY).alias(DiagnosticColumn.CONFIRMATORY_NOVELTY),
    )
    dose_novelty = (
        novelty.filter(pl.col(Column.DESCRIPTOR) == NoveltyDescriptor.NEAREST_KNOWN_FAMILY_DISTANCE)
        .group_by(Column.FAMILY, maintain_order=True)
        .agg(pl.col(Column.VALUE).mean().alias(DiagnosticColumn.DOSE_NOVELTY))
    )
    return (
        summary.join(confirmatory, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .join(dose_novelty, on=Column.FAMILY, how=LibraryOption.JOIN_LEFT)
        .sort(Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY)
    )


def family_associations(summary: DiagnosticTable, config: Config) -> DiagnosticRows:
    top = f"{DiagnosticColumn.CTK}{config.experiments.exact_dose_levels[-1]}"
    wide = summary.filter(pl.col(Column.POPULATION) == EvaluationPopulation.FEDERATION_WIDE)
    rows: DiagnosticRows = []
    for outcome in (top, DiagnosticColumn.ONSET_MEAN):
        for predictor in (
            Column.LOCAL_RECALL,
            Column.FULL_RECALL,
            DiagnosticColumn.CONFIRMATORY_CTK,
            DiagnosticColumn.NATURAL_CTK,
            DiagnosticColumn.CONFIRMATORY_NOVELTY,
            DiagnosticColumn.DOSE_NOVELTY,
        ):
            pair = wide.select(predictor, outcome).drop_nulls().to_numpy().astype(np.float64)
            if len(pair) < StatisticsLimit.ASSOCIATION_FAMILIES:
                continue
            rows.append(
                {
                    DiagnosticColumn.OUTCOME: outcome,
                    DiagnosticColumn.PREDICTOR: predictor,
                    Column.FAMILIES: len(pair),
                    DiagnosticColumn.RHO: spearman(pair[:, 0], pair[:, 1]),
                    Column.P_VALUE: spearman_p(pair[:, 0], pair[:, 1]),
                }
            )
    return rows


def client_curves(
    pairs: DiagnosticTable, config: Config, experiments: tuple[ExperimentName, ...]
) -> DiagnosticRows:
    doses = config.experiments.exact_dose_levels
    selected = pairs.filter(
        (pl.col(Column.LEARNER) == Learner.FEDAVG)
        & (pl.col(Column.ALPHA) == config.experiments.operating.primary_alpha)
        & (pl.col(DiagnosticColumn.DOSE_CODE) >= 0)
    )
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        level = (
            selected.filter(pl.col(Column.EXPERIMENT).is_in(list(scoped.experiments)))
            .group_by(
                Column.SEED,
                Column.POPULATION,
                Column.CLIENT,
                DiagnosticColumn.DOSE_CODE,
                maintain_order=True,
            )
            .agg(pl.col(DiagnosticColumn.CTK).mean())
            .sort(Column.POPULATION, Column.CLIENT, maintain_order=True)
        )
        for group in level.partition_by(Column.POPULATION, Column.CLIENT, maintain_order=True):
            head = group.row(0, named=True)
            wide = wide_by_dose(group)
            if wide.height < DiagnosticLimit.CLIENT_SEEDS:
                continue
            for dose in doses[1:]:
                values = wide[f"{dose}"].drop_nulls().to_numpy().astype(np.float64)
                rows.append(
                    {
                        DiagnosticColumn.SET: scoped.scope,
                        Column.POPULATION: head[Column.POPULATION],
                        Column.CLIENT: head[Column.CLIENT],
                        DiagnosticColumn.SEEDS: wide.height,
                        Column.DOSE: dose_name(dose),
                        Column.MEAN_CTK: values.mean().item(),
                        **_bca(values, config),
                    }
                )
    return rows


def log_linear(doses: DiagnosticVector, slope: Effect) -> DiagnosticVector:
    return slope * np.log1p(doses)


def emax_curve(doses: DiagnosticVector, top: Effect, half: Effect) -> DiagnosticVector:
    return top * doses / (half + doses)


def fit_curve(curves: DiagnosticMatrix, doses: DiagnosticVector, model: DoseModel) -> DoseFit:
    # Descriptive dose-response fits on the units x doses matrix (NaN cells dropped).
    level = np.tile(doses, curves.shape[0])
    outcome = curves.ravel()
    present = ~np.isnan(outcome)
    level, outcome = level[present], outcome[present]
    if model is DoseModel.LOG_LINEAR:
        transformed = np.log1p(level)
        slope = ((transformed @ outcome) / (transformed @ transformed)).item()
        return DoseFit(parameters=(slope,), predicted=log_linear(doses, slope))
    if model is DoseModel.EMAX:
        best: DoseFit | None = None
        best_error = np.inf
        for start in EmaxStart:
            with warnings.catch_warnings():
                warnings.simplefilter(LibraryOption.WARNINGS_IGNORE)
                try:
                    parameters, _ = optimize.curve_fit(
                        emax_curve,
                        level,
                        outcome,
                        p0=(max(outcome.max().item(), EmaxBound.START_FLOOR), start),
                        bounds=(
                            [EmaxBound.TOP_LOW, EmaxBound.HALF_LOW],
                            [EmaxBound.TOP_HIGH, EmaxBound.HALF_HIGH],
                        ),
                        maxfev=DiagnosticLimit.EMAX_EVALUATIONS,
                    )
                except (RuntimeError, ValueError):
                    continue
            top, half = parameters[0].item(), parameters[1].item()
            error = ((outcome - emax_curve(level, top, half)) ** 2).sum().item()
            if best is None or error < best_error:
                best_error = error
                best = DoseFit(parameters=(top, half), predicted=emax_curve(doses, top, half))
        if best is None:
            return DoseFit(parameters=(np.nan, np.nan), predicted=np.full(doses.size, np.nan))
        return best
    weights = (~np.isnan(curves)).sum(0)
    isotonic = IsotonicRegression(increasing=True).fit(
        doses, np.nanmean(curves, axis=0), sample_weight=weights
    )
    return DoseFit(parameters=(), predicted=isotonic.predict(doses))


def akaike(
    curves: DiagnosticMatrix, predicted: DiagnosticVector, parameters: SupportCount
) -> Effect:
    residuals = (curves - predicted[None, :]).ravel()
    residuals = residuals[~np.isnan(residuals)]
    size = residuals.size
    return (size * np.log((residuals**2).sum() / size) + 2 * (parameters + 1)).item()


def cross_validated(curves: DiagnosticMatrix, doses: DiagnosticVector, model: DoseModel) -> Effect:
    errors: list[Effect] = []
    for unit in range(curves.shape[0]):
        predicted = fit_curve(np.delete(curves, unit, 0), doses, model).predicted
        residual: DiagnosticVector = curves[unit] - predicted
        errors.append(np.nanmean(residual**2).item())
    return np.mean(errors).item()


def equivalent_dose(curve: DiagnosticVector, natural: Effect, doses: DiagnosticVector) -> Effect:
    # First dose at which the piecewise-linear mean curve reaches the natural-arm CTK.
    if natural <= curve[0]:
        return 0.0
    for index in range(1, doses.size):
        if curve[index] >= natural:
            low, high = curve[index - 1], curve[index]
            step = doses[index] - doses[index - 1]
            return (doses[index - 1] + (natural - low) / (high - low) * step).item()
    return np.inf


def _model_parameters(model: DoseModel, fit: DoseFit) -> SupportCount:
    if model is DoseModel.LOG_LINEAR:
        return 1
    if model is DoseModel.EMAX:
        return 2
    return np.unique(np.round(fit.predicted, DiagnosticLimit.ISOTONIC_DECIMALS)).size


def model_block(
    wide: DiagnosticTable,
    label: DoseName,
    config: Config,
    rng: np.random.Generator,
) -> DiagnosticRow:
    doses = config.experiments.exact_dose_levels
    grid = np.array(doses, dtype=np.float64)
    top = doses[-1]
    curves = wide.select([f"{dose}" for dose in doses]).to_numpy().astype(np.float64)
    natural_name = f"{DoseCode.NATURAL}"
    natural = (
        wide[natural_name].to_numpy().astype(np.float64) if natural_name in wide.columns else None
    )
    units = curves.shape[0]
    row: DiagnosticRow = {DiagnosticColumn.CURVE: label, DiagnosticColumn.UNITS: units}
    for model in DoseModel:
        fit = fit_curve(curves, grid, model)
        row[f"{DiagnosticColumn.AIC}{model}"] = akaike(
            curves, fit.predicted, _model_parameters(model, fit)
        )
        row[f"{DiagnosticColumn.CV_MSE}{model}"] = (
            cross_validated(curves, grid, model) if units >= StatisticsLimit.BCA_SEEDS else np.nan
        )
        if model is DoseModel.EMAX:
            row[DiagnosticColumn.EMAX] = fit.parameters[0]
            row[DiagnosticColumn.ED50] = fit.parameters[1]
        if model is DoseModel.LOG_LINEAR:
            row[DiagnosticColumn.LOG_SLOPE] = fit.parameters[0]
    tops: list[Effect] = []
    halves: list[Effect] = []
    equivalents: list[Effect] = []
    for _ in range(DiagnosticResamples.DOSE_FIT):
        draw = rng.integers(0, units, units)
        fit = fit_curve(curves[draw], grid, DoseModel.EMAX)
        tops.append(fit.parameters[0])
        halves.append(fit.parameters[1])
        if natural is not None:
            equivalents.append(
                equivalent_dose(np.nanmean(curves[draw], 0), np.nanmean(natural[draw]).item(), grid)
            )
    tail = (1.0 - config.statistics.confidence_level) / 2.0
    top_limits = np.quantile(tops, [tail, 1.0 - tail])
    half_values = np.array(halves)
    half_limits = np.quantile(half_values, [tail, 1.0 - tail])
    at_bound = (half_values > EmaxBound.HALF_AT_BOUND).mean().item()
    row |= {
        DiagnosticColumn.EMAX_LOW: top_limits[0].item(),
        DiagnosticColumn.EMAX_HIGH: top_limits[1].item(),
        DiagnosticColumn.ED50_LOW: half_limits[0].item(),
        DiagnosticColumn.ED50_HIGH: half_limits[1].item(),
        DiagnosticColumn.ED50_BEYOND_TOP: (half_values > top).mean().item(),
        DiagnosticColumn.ED50_AT_BOUND: at_bound,
        DiagnosticColumn.ED50_IDENTIFIED: half_limits[1].item() <= top and at_bound < tail,
    }
    if natural is not None:
        mean_curve = np.nanmean(curves, 0)
        equivalent = np.array(equivalents)
        # Resamples that never reach the natural CTK are +inf; their limits stay inf/NaN.
        with np.errstate(invalid=LibraryOption.WARNINGS_IGNORE):
            limits = np.quantile(equivalent, [tail, 1.0 - tail])
        row |= {
            DiagnosticColumn.NATURAL_CTK: np.nanmean(natural).item(),
            f"{DiagnosticColumn.CTK}{top}": mean_curve[-1].item(),
            DiagnosticColumn.EQUIVALENT_DOSE: equivalent_dose(
                mean_curve, np.nanmean(natural).item(), grid
            ),
            DiagnosticColumn.EQUIVALENT_LOW: limits[0].item(),
            DiagnosticColumn.EQUIVALENT_HIGH: limits[1].item(),
            DiagnosticColumn.EQUIVALENT_BEYOND_TOP: np.isinf(equivalent).mean().item(),
        }
    return row


def model_fits(
    pairs: DiagnosticTable,
    families: DiagnosticTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    rng: np.random.Generator,
) -> DiagnosticRows:
    alpha = config.experiments.operating.primary_alpha
    population = EvaluationPopulation.FEDERATION_WIDE
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        wide = wide_by_dose(_selected(seed_level(pairs, scoped), Learner.FEDAVG, population, alpha))
        rows.append(
            {
                DiagnosticColumn.FIT_LEVEL: DoseFitLevel.FAMILY_MACRO,
                DiagnosticColumn.SET: scoped.scope,
                **model_block(wide, scoped.scope, config, rng),
            }
        )
    selected = _selected(families, Learner.FEDAVG, population, alpha).sort(
        DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
    )
    for group in selected.partition_by(DiagnosticColumn.SET, Column.FAMILY, maintain_order=True):
        head = group.row(0, named=True)
        wide = wide_by_dose(group)
        if wide.height >= DiagnosticLimit.FIT_SEEDS:
            rows.append(
                {
                    DiagnosticColumn.FIT_LEVEL: DoseFitLevel.FAMILY,
                    DiagnosticColumn.SET: head[DiagnosticColumn.SET],
                    **model_block(wide, head[Column.FAMILY], config, rng),
                }
            )
    return rows


def _between_within(groups: list[DiagnosticVector]) -> DiagnosticVector:
    count = len(groups)
    total = sum(group.size for group in groups)
    grand = np.concatenate(groups).mean()
    between = sum(group.size * (group.mean() - grand) ** 2 for group in groups)
    within = sum(((group - group.mean()) ** 2).sum() for group in groups)
    size = (total - sum(group.size**2 for group in groups) / total) / (count - 1)
    return np.array([between, within, between / (count - 1), within / (total - count), size])


def _icc(groups: list[DiagnosticVector]) -> Effect:
    _, _, between, within, size = _between_within(groups)
    component = max((between - within) / size, 0.0)
    return (component / (component + within)).item() if component + within > 0 else np.nan


def heterogeneity(
    families: DiagnosticTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
    rng: np.random.Generator,
) -> DiagnosticRows:
    top = config.experiments.exact_dose_levels[-1]
    alpha = config.experiments.operating.primary_alpha
    rows: DiagnosticRows = []
    for scoped in ordered_scopes(config, experiments):
        members = scope_members(scoped.scope)
        for population in _populations():
            selected = (
                _selected(families, Learner.FEDAVG, population, alpha)
                .filter(
                    (pl.col(DiagnosticColumn.DOSE_CODE) == top)
                    & pl.col(DiagnosticColumn.SET).is_in(members)
                )
                .sort(DiagnosticColumn.SET, Column.FAMILY, Column.SEED, maintain_order=True)
            )
            groups = [
                group[DiagnosticColumn.CTK].to_numpy().astype(np.float64)
                for group in selected.partition_by(
                    DiagnosticColumn.SET, Column.FAMILY, maintain_order=True
                )
            ]
            count = len(groups)
            between_sum, within_sum, between, within, size = _between_within(groups)
            component = max((between - within) / size, 0.0)
            resampled = np.array(
                [
                    _icc([groups[index] for index in rng.integers(0, count, count)])
                    for _ in range(DiagnosticResamples.DOSE_FIT)
                ]
            )
            interval = percentile_limits(resampled, config)
            rows.append(
                {
                    DiagnosticColumn.SET: scoped.scope,
                    Column.POPULATION: population,
                    Column.FAMILIES: count,
                    DiagnosticColumn.UNITS: sum(group.size for group in groups),
                    DiagnosticColumn.VARIANCE_BETWEEN: component,
                    DiagnosticColumn.VARIANCE_WITHIN: within.item(),
                    DiagnosticColumn.ICC: (component / (component + within)).item(),
                    DiagnosticColumn.ICC_LOW: interval_low(interval),
                    DiagnosticColumn.ICC_HIGH: interval_high(interval),
                    DiagnosticColumn.ETA_SQUARED: (between_sum / (between_sum + within_sum)).item(),
                    Column.P_VALUE: stats.f_oneway(*groups).pvalue.item(),
                }
            )
    return rows


def dose_diagnostics(
    families: FamilyCountsTable,
    novelty: NoveltyTable,
    family_level: FamilyLevelTable,
    config: Config,
    experiments: tuple[ExperimentName, ...],
) -> DoseDiagnostics:
    evidence = EvidenceClass.POST_HOC_DIAGNOSTIC
    pairs = pair_ctk(families, config, experiments)
    by_family = family_seed_level(pairs)
    curves = labelled(family_curves(by_family, config), evidence)
    summary = with_family_context(
        labelled(family_summary(curves, config), evidence), family_level, novelty
    )
    rng = np.random.default_rng(DiagnosticSeed.DOSE)
    return DoseDiagnostics(
        curve=labelled(ctk_by_dose(pairs, config, experiments), evidence),
        increments=labelled(dose_increments(pairs, config, experiments), evidence),
        family_curves=curves.drop(DiagnosticColumn.DOSE_CODE).sort(
            Column.POPULATION, DiagnosticColumn.SET, Column.FAMILY, Column.DOSE
        ),
        family_summary=summary,
        associations=labelled(family_associations(summary, config), evidence),
        client_curves=labelled(client_curves(pairs, config, experiments), evidence),
        model_fits=labelled(model_fits(pairs, by_family, config, experiments, rng), evidence).sort(
            DiagnosticColumn.FIT_LEVEL, DiagnosticColumn.SET, DiagnosticColumn.CURVE
        ),
        heterogeneity=labelled(heterogeneity(by_family, config, experiments, rng), evidence),
    )
