from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

from ctk_android import logs
from ctk_android.config import Config, load_config
from ctk_android.enums import (
    CliCommand,
    CliMessage,
    ExecutionMode,
    ExperimentName,
    LogEvent,
    LogField,
    Verdict,
)
from ctk_android.logs import Stopwatch, bind, configure_logging
from ctk_android.paths import Paths
from ctk_android.types import CtkError, Overwrite, Promote, Seed, seed_adapter
from ctk_android.workflows import doctor as doctor_workflow
from ctk_android.workflows import plan as plan_workflow
from ctk_android.workflows import preprocess as preprocess_workflow
from ctk_android.workflows import report as report_workflow
from ctk_android.workflows import run as run_workflow
from ctk_android.workflows import smoke as smoke_workflow
from ctk_android.workflows import status as status_workflow

app = typer.Typer(no_args_is_help=True, add_completion=False)


@dataclass(frozen=True)
class CliContext:
    paths: Paths
    config: Config
    watch: Stopwatch


def _context(command: CliCommand) -> CliContext:
    paths = Paths.discover(Path.cwd())
    config = load_config(paths)
    configure_logging(paths, command, config.project.logging_level)
    bind({LogField.COMMAND: command})
    logs.info(
        LogEvent.COMMAND_STARTED,
        {
            LogField.CONFIG_FINGERPRINT: config.fingerprint(),
            LogField.DEVICE: config.project.device,
        },
    )
    return CliContext(paths=paths, config=config, watch=Stopwatch())


def _finished(context: CliContext, verdict: Verdict) -> None:
    logs.info(
        LogEvent.COMMAND_FINISHED,
        {LogField.STATUS: verdict, LogField.SECONDS: context.watch.seconds()},
    )


def _failed(context: CliContext, error: CtkError) -> None:
    logs.error(
        LogEvent.COMMAND_FAILED,
        {
            LogField.REASON: error.reason,
            LogField.ERROR: f"{error}",
            LogField.SECONDS: context.watch.seconds(),
        },
    )


@app.command(name=CliCommand.DOCTOR)
def doctor() -> None:
    context = _context(CliCommand.DOCTOR)
    results = doctor_workflow.run_doctor(context.paths, context.config)
    for result in results:
        verdict = Verdict.PASS if result.passed else Verdict.FAIL
        typer.echo(
            CliMessage.DOCTOR_LINE.format(verdict=verdict, check=result.check, detail=result.detail)
        )
    healthy = all(result.passed for result in results)
    _finished(context, Verdict.PASS if healthy else Verdict.FAIL)
    if not healthy:
        raise typer.Exit(code=1)


@app.command(name=CliCommand.PREPROCESS)
def preprocess(overwrite: Annotated[Overwrite, typer.Option()] = False) -> None:
    context = _context(CliCommand.PREPROCESS)
    try:
        reports = preprocess_workflow.run_preprocess(context.paths, context.config, overwrite)
    except CtkError as error:
        _failed(context, error)
        raise typer.Exit(code=1) from error
    for report in reports:
        typer.echo(
            CliMessage.STAGE_LINE.format(
                stage=report.stage, reused=report.reused, directory=report.directory
            )
        )
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.PLAN)
def plan(mode: ExecutionMode) -> None:
    context = _context(CliCommand.PLAN)
    try:
        planned = plan_workflow.run_plan(context.paths, context.config, mode)
    except CtkError as error:
        _failed(context, error)
        raise typer.Exit(code=1) from error
    typer.echo(CliMessage.PLANNED.format(count=len(planned), mode=mode))
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.SMOKE)
def smoke(overwrite: Annotated[Overwrite, typer.Option()] = False) -> None:
    context = _context(CliCommand.SMOKE)
    try:
        report = smoke_workflow.run_smoke(context.paths, context.config, overwrite)
    except CtkError as error:
        _failed(context, error)
        raise typer.Exit(code=1) from error
    typer.echo(CliMessage.SMOKE_LINE.format(status=report.status, directory=report.directory))
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.RUN)
def run(
    experiment: ExperimentName,
    mode: ExecutionMode = ExecutionMode.DEVELOPMENT,
    seed: Annotated[Seed | None, typer.Option(parser=seed_adapter.validate_python)] = None,
    overwrite: Annotated[Overwrite, typer.Option()] = False,
) -> None:
    context = _context(CliCommand.RUN)
    seeds = context.config.project.seeds.for_mode(mode) if seed is None else (seed,)
    try:
        reports = run_workflow.run_experiment(
            context.paths, context.config, experiment, mode, seeds, overwrite
        )
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    for report in reports:
        typer.echo(
            CliMessage.RUN_LINE.format(
                experiment=report.key.experiment, seed=report.key.seed, status=report.status
            )
        )
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.STATUS)
def status(mode: ExecutionMode = ExecutionMode.CONFIRMATORY) -> None:
    context = _context(CliCommand.STATUS)
    typer.echo(status_workflow.run_status(context.paths, mode))
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.REPORT)
def report(
    mode: ExecutionMode = ExecutionMode.CONFIRMATORY,
    promote: Annotated[Promote, typer.Option()] = False,
) -> None:
    context = _context(CliCommand.REPORT)
    try:
        decision = report_workflow.run_report(context.paths, context.config, mode, promote)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    if decision is not None:
        typer.echo(CliMessage.PROMOTION_LINE.format(state=decision.state, blocks=decision.blocks))
    _finished(context, Verdict.PASS)
