import polars as pl

from ctk_android.config import Config
from ctk_android.data.cache import read_record
from ctk_android.enums import Artifact, Column, ExecutionMode, RunStatus
from ctk_android.paths import Paths
from ctk_android.types import RunEvidence, RunKey, RunStatusDocument
from ctk_android.workflows.plan import experiments_for


def _tagged(frame: pl.DataFrame, key: RunKey) -> pl.DataFrame:
    return frame.with_columns(
        pl.lit(key.experiment).alias(Column.EXPERIMENT),
        pl.lit(key.seed).alias(Column.SEED),
        pl.lit(key.salt).alias(Column.SALT),
    )


def collect_evidence(paths: Paths, config: Config, mode: ExecutionMode) -> RunEvidence:
    index: list[pl.DataFrame] = []
    tables: dict[Artifact, list[pl.DataFrame]] = {
        Artifact.SUMMARY: [],
        Artifact.CLIENT_METRICS: [],
        Artifact.FAMILY_METRICS: [],
        Artifact.EXPOSURE: [],
        Artifact.NOVELTY: [],
    }
    for experiment in experiments_for(config, mode):
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
        index=pl.concat(index),
        summary=pl.concat(tables[Artifact.SUMMARY]),
        clients=pl.concat(tables[Artifact.CLIENT_METRICS]),
        families=pl.concat(tables[Artifact.FAMILY_METRICS]),
        exposure=pl.concat(tables[Artifact.EXPOSURE]),
        novelty=pl.concat(tables[Artifact.NOVELTY]),
    )
