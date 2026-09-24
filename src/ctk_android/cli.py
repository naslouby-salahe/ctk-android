import logging
from pathlib import Path
from typing import Annotated

import structlog
import typer

from ctk_android.config import Config, load_config
from ctk_android.enums import CliCommand, CliMessage, ExecutionMode, ExperimentName, Verdict
from ctk_android.paths import Paths
from ctk_android.types import CtkError, Seed, seed_adapter
from ctk_android.workflows import doctor as doctor_workflow
from ctk_android.workflows import plan as plan_workflow
from ctk_android.workflows import preprocess as preprocess_workflow
from ctk_android.workflows import run as run_workflow
from ctk_android.workflows import smoke as smoke_workflow
from ctk_android.workflows import status as status_workflow

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _context() -> tuple[Paths, Config]:
    paths = Paths.discover(Path.cwd())
    config = load_config(paths)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelNamesMapping()[config.project.logging_level]
        )
    )
    return paths, config


@app.command(name=CliCommand.DOCTOR)
def doctor() -> None:
    paths, config = _context()
    results = doctor_workflow.run_doctor(paths, config)
    for result in results:
        verdict = Verdict.PASS if result.passed else Verdict.FAIL
        typer.echo(
            CliMessage.DOCTOR_LINE.format(verdict=verdict, check=result.check, detail=result.detail)
        )
    if not all(result.passed for result in results):
        raise typer.Exit(code=1)


@app.command(name=CliCommand.PREPROCESS)
def preprocess(overwrite: Annotated[bool, typer.Option()] = False) -> None:
    paths, config = _context()
    for report in preprocess_workflow.run_preprocess(paths, config, overwrite):
        typer.echo(
            CliMessage.STAGE_LINE.format(
                stage=report.stage, reused=report.reused, directory=report.directory
            )
        )


@app.command(name=CliCommand.PLAN)
def plan(mode: ExecutionMode) -> None:
    paths, config = _context()
    planned = plan_workflow.run_plan(paths, config, mode)
    typer.echo(CliMessage.PLANNED.format(count=len(planned), mode=mode))


@app.command(name=CliCommand.SMOKE)
def smoke(overwrite: Annotated[bool, typer.Option()] = False) -> None:
    paths, config = _context()
    report = smoke_workflow.run_smoke(paths, config, overwrite)
    typer.echo(CliMessage.SMOKE_LINE.format(status=report.status, directory=report.directory))


@app.command(name=CliCommand.RUN)
def run(
    experiment: ExperimentName,
    mode: ExecutionMode = ExecutionMode.DEVELOPMENT,
    seed: Annotated[Seed | None, typer.Option(parser=seed_adapter.validate_python)] = None,
    overwrite: Annotated[bool, typer.Option()] = False,
) -> None:
    paths, config = _context()
    seeds = config.project.seeds.for_mode(mode) if seed is None else (seed,)
    try:
        reports = run_workflow.run_experiment(paths, config, experiment, mode, seeds, overwrite)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        raise typer.Exit(code=1) from error
    for report in reports:
        typer.echo(
            CliMessage.RUN_LINE.format(
                experiment=report.key.experiment, seed=report.key.seed, status=report.status
            )
        )


@app.command(name=CliCommand.STATUS)
def status(mode: ExecutionMode = ExecutionMode.CONFIRMATORY) -> None:
    paths, _ = _context()
    typer.echo(status_workflow.run_status(paths, mode))
