import polars as pl

from ctk_android import logs
from ctk_android.config import Config
from ctk_android.data.cache import is_reusable, normalise_arm_columns, read_record, run_provenance
from ctk_android.enums import Artifact, Column, ExecutionMode, LogEvent, LogField, RunStatus
from ctk_android.paths import Paths
from ctk_android.types import (
    FairnessGrid,
    FrameLists,
    LogFields,
    RunEvidence,
    RunIndexTable,
    RunKey,
    RunStatusDocument,
    Stale,
    Table,
)
from ctk_android.workflows.plan import experiments_for, planned_targets


def _tagged(frame: Table, key: RunKey) -> Table:
    return normalise_arm_columns(frame).with_columns(
        pl.lit(key.experiment).alias(Column.EXPERIMENT),
        pl.lit(key.seed).alias(Column.SEED),
        pl.lit(key.salt).alias(Column.SALT),
    )


def _concat(frames: list[Table]) -> Table:
    return pl.concat(frames) if frames else pl.DataFrame()


def _is_stale(paths: Paths, config: Config, key: RunKey) -> Stale:
    current = run_provenance(paths, config, key, planned_targets(paths, key).targets)
    return not is_reusable(paths.provenance_file(paths.run_dir(key)), current)


def _stale_fields(key: RunKey) -> LogFields:
    return {
        LogField.EXPERIMENT: key.experiment,
        LogField.SEED: key.seed,
        LogField.SALT: key.salt,
    }


def collect_evidence(
    paths: Paths, config: Config, mode: ExecutionMode, fairness: FairnessGrid
) -> RunEvidence:
    index: list[RunIndexTable] = []
    tables: FrameLists = {
        Artifact.SUMMARY: [],
        Artifact.CLIENT_METRICS: [],
        Artifact.FAMILY_METRICS: [],
        Artifact.EXPOSURE: [],
        Artifact.NOVELTY: [],
    }
    for experiment in experiments_for(config, mode):
        if config.experiments.experiments[experiment].fairness_grid != fairness:
            continue
        for seed in config.project.seeds.for_mode(mode):
            for salt in config.experiments.experiments[experiment].salts:
                key = RunKey(mode=mode, experiment=experiment, seed=seed, salt=salt)
                status_file = paths.run_file(key, Artifact.STATUS)
                document = (
                    read_record(status_file, RunStatusDocument)
                    if status_file.is_file()
                    else RunStatusDocument(status=RunStatus.INCOMPLETE, reason=None)
                )
                index.append(
                    _tagged(
                        pl.DataFrame(
                            {Column.STATUS: [document.status], Column.REASON: [document.reason]}
                        ),
                        key,
                    )
                )
                if document.status is RunStatus.COMPLETED and _is_stale(paths, config, key):
                    logs.warning(LogEvent.RUN_STALE, _stale_fields(key))
                    index[-1] = _tagged(
                        pl.DataFrame(
                            {Column.STATUS: [RunStatus.STALE], Column.REASON: [document.reason]}
                        ),
                        key,
                    )
                    continue
                if document.status is not RunStatus.COMPLETED:
                    continue
                for artifact, frames in tables.items():
                    file = (
                        paths.run_file(key, artifact)
                        if artifact in (Artifact.EXPOSURE, Artifact.NOVELTY)
                        else paths.run_metric_file(key, artifact)
                    )
                    frames.append(_tagged(pl.read_parquet(file), key))
    return RunEvidence(
        index=_concat(index),
        summary=_concat(tables[Artifact.SUMMARY]),
        clients=_concat(tables[Artifact.CLIENT_METRICS]),
        families=_concat(tables[Artifact.FAMILY_METRICS]),
        exposure=_concat(tables[Artifact.EXPOSURE]),
        novelty=_concat(tables[Artifact.NOVELTY]),
    )
