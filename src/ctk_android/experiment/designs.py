from dataclasses import dataclass

import numpy as np

from ctk_android import logs
from ctk_android.analysis.novelty import family_relatedness, known_family_centroids
from ctk_android.config import Config
from ctk_android.data.cache import records_to_frame
from ctk_android.enums import (
    Aggregation,
    ClientId,
    DetailMessage,
    DrawStream,
    ExperimentDesign,
    ExposureCondition,
    Learner,
    LogEvent,
    LogField,
    TunedParameter,
    ValidationCheck,
)
from ctk_android.experiment import evaluation, exposure, substitution, training
from ctk_android.experiment.training import learner_stream
from ctk_android.logs import Stopwatch
from ctk_android.types import (
    AggregationRule,
    ArmKey,
    ArmResult,
    ClientPools,
    DesignSetting,
    DoseRequest,
    ExperimentSpec,
    FamilyFitRows,
    FamilyMasks,
    LevelRows,
    LogFields,
    Passed,
    PlaceboChoice,
    PlaceboPairRow,
    ResultsByArm,
    RowCount,
    RunKey,
    StudyData,
    SupportCount,
    Table,
    TargetPair,
    TrainingByArm,
    TrainingRows,
    TuningPoint,
    ValidationRecord,
)


@dataclass(frozen=True)
class DesignArms:
    arms: ResultsByArm
    trainings: TrainingByArm
    checks: tuple[ValidationRecord, ...]
    placebo: Table | None


@dataclass(frozen=True)
class DesignInputs:
    spec: ExperimentSpec
    config: Config
    key: RunKey
    context: training.TrainingContext
    study: StudyData
    masks: FamilyMasks
    pools: ClientPools
    orders: TrainingRows
    targets: tuple[TargetPair, ...]
    budget: SupportCount


def run_fields(key: RunKey) -> LogFields:
    return {
        LogField.EXPERIMENT: key.experiment,
        LogField.MODE: key.mode,
        LogField.SEED: key.seed,
        LogField.SALT: key.salt,
    }


def aggregation_rule(kind: Aggregation, trim_per_side: SupportCount) -> AggregationRule:
    return AggregationRule(rule=kind, trim_per_side=trim_per_side)


def _arm(
    learner: Learner,
    condition: ExposureCondition,
    dose: DoseRequest,
    aggregation: Aggregation | None,
) -> ArmKey:
    tuning = (
        None
        if aggregation is None
        else TuningPoint(parameter=TunedParameter.AGGREGATION, level=aggregation)
    )
    return ArmKey(learner=learner, condition=condition, dose=dose, tuning=tuning)


def _train(
    inputs: DesignInputs, arm: ArmKey, rows: TrainingRows, aggregation: Aggregation | None
) -> ArmResult:
    context = inputs.context
    watch = Stopwatch()
    stream = learner_stream(arm.learner)
    if arm.learner is Learner.CENTRAL:
        scorer = training.train_scorer(
            context, training.pooled_rows(rows), context.config.central_epochs, stream
        )
    else:
        rule = (
            None
            if aggregation is None
            else aggregation_rule(aggregation, inputs.config.experiments.robust_trim_per_side)
        )
        scorer = training.train_federated(context, rows, arm.learner, 0.0, stream, rule)
    logs.info(
        LogEvent.ARM_TRAINED,
        {
            **run_fields(inputs.key),
            LogField.ARM: arm.label(),
            LogField.TRAIN_ROWS: sum(chosen.size for chosen in rows.values()),
            LogField.SECONDS: watch.seconds(),
        },
    )
    return ArmResult(
        scores=evaluation.score_shared(scorer, inputs.study, inputs.pools),
        scorers=dict.fromkeys(ClientId, scorer),
    )


def _standard_rows(inputs: DesignInputs, condition: ExposureCondition) -> TrainingRows:
    base = ArmKey(learner=Learner.CENTRAL, condition=condition, dose=None)
    spec = exposure.exposure_spec(base, inputs.spec.exposure_mode, inputs.targets)
    return exposure.select_training(inputs.orders, inputs.masks, spec, {}, inputs.budget)


def _peer_rows_of(rows: TrainingRows, masks: FamilyMasks, pair: TargetPair) -> RowCount:
    return sum(
        masks[pair.family][chosen].sum().item()
        for client, chosen in rows.items()
        if client is not pair.client
    )


def _dose_checks(
    inputs: DesignInputs, levels: LevelRows, absent: TrainingRows
) -> tuple[ValidationRecord, ...]:
    masks, targets = inputs.masks, inputs.targets
    checks: list[ValidationRecord] = []
    for dose, rows in levels.items():
        realised: Passed = all(_peer_rows_of(rows, masks, pair) == dose for pair in targets)
        target_zero: Passed = all(
            not masks[pair.family][rows[pair.client]].any().item() for pair in targets
        )
        checks.append(
            ValidationRecord(
                check=ValidationCheck.EXACT_DOSE_REALISED,
                passed=realised,
                detail=DetailMessage.DOSE_REALISED.format(dose=dose),
            )
        )
        checks.append(
            ValidationRecord(
                check=ValidationCheck.EXACT_DOSE_TARGET_ZERO,
                passed=target_zero,
                detail=DetailMessage.DOSE_TARGET_ZERO.format(dose=dose),
            )
        )
    identical: Passed = (
        all(np.array_equal(levels[0][client], absent[client]) for client in ClientId)
        if 0 in levels
        else True
    )
    checks.append(
        ValidationRecord(
            check=ValidationCheck.DOSE_ZERO_IS_ABSENT,
            passed=identical,
            detail=DetailMessage.DOSE_ZERO_IS_ABSENT,
        )
    )
    return tuple(checks)


def _train_dose(inputs: DesignInputs) -> DesignArms:
    config, spec = inputs.config, inputs.spec
    peer = _standard_rows(inputs, ExposureCondition.PEER_PRESENT)
    absent = _standard_rows(inputs, ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    fit = substitution.family_fit_rows(inputs.study)
    seeds = [inputs.key.seed, inputs.key.salt, DrawStream.DOSE]
    draw = substitution.draw_dose(
        fit, absent, inputs.targets, np.random.default_rng(np.random.SeedSequence(seeds))
    )
    levels: LevelRows = {
        dose: substitution.substitute(
            absent,
            substitution.dose_extras(draw, inputs.targets, dose),
            draw.replacement_order,
        )
        for dose in config.experiments.exact_dose_levels
    }
    settings = [
        DesignSetting(
            condition=ExposureCondition.PEER_PRESENT, dose=None, aggregation=None, rows=peer
        ),
        DesignSetting(
            condition=ExposureCondition.FAMILY_ABSENT_EVERYWHERE,
            dose=None,
            aggregation=None,
            rows=absent,
        ),
        *(
            DesignSetting(
                condition=ExposureCondition.EXACT_DOSE, dose=dose, aggregation=None, rows=rows
            )
            for dose, rows in levels.items()
        ),
    ]
    arms: ResultsByArm = {}
    trainings: TrainingByArm = {}
    for setting in settings:
        for learner in spec.learners:
            arm = _arm(learner, setting.condition, setting.dose, None)
            arms[arm] = _train(inputs, arm, setting.rows, None)
            trainings[arm] = setting.rows
    return DesignArms(
        arms=arms,
        trainings=trainings,
        checks=_dose_checks(inputs, levels, absent),
        placebo=None,
    )


def _placebo_checks(
    inputs: DesignInputs,
    fit: FamilyFitRows,
    choices: tuple[PlaceboChoice, ...],
    rows: TrainingRows,
    absent: TrainingRows,
) -> tuple[ValidationRecord, ...]:
    hidden = {pair.family for pair in inputs.targets}
    placebos = [choice.placebo for choice in choices]
    valid: Passed = len(set(placebos)) == len(placebos) and not hidden & set(placebos)
    matched: Passed = True
    for client in ClientId:
        added = np.setdiff1d(rows[client], absent[client])
        pools = [fit[choice.placebo].get(client, np.empty(0, dtype=np.int64)) for choice in choices]
        expected = sum(choice.allocated.get(client, 0) for choice in choices)
        matched &= added.size == expected and np.isin(added, np.concatenate(pools)).all().item()
    hidden_zero: Passed = all(
        not inputs.masks[pair.family][chosen].any().item()
        for pair in inputs.targets
        for chosen in rows.values()
    )
    return (
        ValidationRecord(
            check=ValidationCheck.PLACEBO_COUNTS_MATCHED,
            passed=matched,
            detail=DetailMessage.PLACEBO_COUNTS,
        ),
        ValidationRecord(
            check=ValidationCheck.PLACEBO_FAMILY_VALID,
            passed=valid,
            detail=DetailMessage.PLACEBO_VALID,
        ),
        ValidationRecord(
            check=ValidationCheck.PLACEBO_HIDDEN_ABSENT,
            passed=hidden_zero,
            detail=DetailMessage.PLACEBO_HIDDEN_ZERO,
        ),
    )


def _placebo_table(
    inputs: DesignInputs, fit: FamilyFitRows, choices: tuple[PlaceboChoice, ...]
) -> Table:
    hidden = frozenset(pair.family for pair in inputs.targets)
    centroids = known_family_centroids(inputs.study, fit, hidden, inputs.config.experiments.novelty)
    rows: list[PlaceboPairRow] = []
    for choice in choices:
        related = family_relatedness(inputs.study, fit, centroids, choice)
        rows.append(
            PlaceboPairRow(
                client=choice.client,
                family=choice.family,
                placebo_family=choice.placebo,
                need=sum(choice.counts.values()),
                reallocated=choice.reallocated,
                hidden_peer_fit=choice.hidden_peer_fit,
                placebo_peer_fit=choice.placebo_peer_fit,
                centroid_distance=related.centroid_distance,
                nearest_known_distance=related.nearest_known_distance,
                placebo_rank=related.placebo_rank,
                known_families=related.known_families,
            )
        )
    return records_to_frame(rows)


def _placebo_settings(
    peer: TrainingRows, absent: TrainingRows, placebo: TrainingRows
) -> list[DesignSetting]:
    plain = [
        DesignSetting(condition=condition, dose=None, aggregation=None, rows=rows)
        for condition, rows in (
            (ExposureCondition.PEER_PRESENT, peer),
            (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, absent),
            (ExposureCondition.PLACEBO, placebo),
        )
    ]
    robust = [
        DesignSetting(condition=condition, dose=None, aggregation=rule, rows=rows)
        for rule in Aggregation
        for condition, rows in (
            (ExposureCondition.PEER_PRESENT, peer),
            (ExposureCondition.FAMILY_ABSENT_EVERYWHERE, absent),
        )
    ]
    return [*plain, *robust]


def _train_placebo(inputs: DesignInputs) -> DesignArms:
    config = inputs.config
    peer = _standard_rows(inputs, ExposureCondition.PEER_PRESENT)
    absent = _standard_rows(inputs, ExposureCondition.FAMILY_ABSENT_EVERYWHERE)
    fit = substitution.family_fit_rows(inputs.study)
    choices = substitution.choose_placebos(
        fit,
        substitution.family_totals(inputs.study),
        inputs.masks,
        peer,
        absent,
        inputs.targets,
        config.experiments.placebo_min_malware_rows,
    )
    seeds = [inputs.key.seed, inputs.key.salt, DrawStream.PLACEBO]
    rng = np.random.default_rng(np.random.SeedSequence(seeds))
    order = {client: rng.permutation(rows.size) for client, rows in absent.items()}
    placebo = substitution.substitute(
        absent, substitution.placebo_extras(fit, absent, choices, rng), order
    )
    arms: ResultsByArm = {}
    trainings: TrainingByArm = {}
    for setting in _placebo_settings(peer, absent, placebo):
        arm = _arm(Learner.FEDAVG, setting.condition, None, setting.aggregation)
        arms[arm] = _train(inputs, arm, setting.rows, setting.aggregation)
        trainings[arm] = setting.rows
    return DesignArms(
        arms=arms,
        trainings=trainings,
        checks=_placebo_checks(inputs, fit, choices, placebo, absent),
        placebo=_placebo_table(inputs, fit, choices),
    )


def train_design_arms(inputs: DesignInputs) -> DesignArms:
    if inputs.spec.design is ExperimentDesign.EXACT_DOSE:
        return _train_dose(inputs)
    return _train_placebo(inputs)
