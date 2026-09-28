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
    RunStatus,
    Separator,
    Verdict,
)
from ctk_android.logs import Stopwatch, bind, configure_logging
from ctk_android.paths import Paths
from ctk_android.types import CtkError, Overwrite
from ctk_android.workflows import maintenance as maintenance_workflow
from ctk_android.workflows import preprocess as preprocess_workflow
from ctk_android.workflows import report as report_workflow
from ctk_android.workflows import run as run_workflow

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
    results = maintenance_workflow.run_doctor(context.paths, context.config)
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
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
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
        planned = maintenance_workflow.run_plan(context.paths, context.config, mode)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    typer.echo(CliMessage.PLANNED.format(count=len(planned), mode=mode))
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.SMOKE)
def smoke(overwrite: Annotated[Overwrite, typer.Option()] = False) -> None:
    context = _context(CliCommand.SMOKE)
    try:
        reports = run_workflow.run_smoke(context.paths, context.config, overwrite)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    for report in reports:
        typer.echo(CliMessage.SMOKE_LINE.format(status=report.status, directory=report.directory))
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.RUN)
def run(
    experiment: ExperimentName,
    overwrite: Annotated[Overwrite, typer.Option()] = False,
) -> None:
    context = _context(CliCommand.RUN)
    try:
        reports = run_workflow.run_experiment(context.paths, context.config, experiment, overwrite)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    for report in reports:
        typer.echo(
            CliMessage.RUN_LINE.format(
                experiment=report.key.experiment,
                mode=report.key.mode,
                seed=report.key.seed,
                salt=report.key.salt,
                status=report.status,
            )
        )
    unfinished = [report for report in reports if report.status is not RunStatus.COMPLETED]
    if unfinished:
        _finished(context, Verdict.FAIL)
        raise typer.Exit(code=1)
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.STATUS)
def status() -> None:
    context = _context(CliCommand.STATUS)
    campaign = maintenance_workflow.run_status(context.paths, context.config)
    for summary in campaign.experiments:
        counts = summary.counts
        typer.echo(
            CliMessage.STATUS_LINE.format(
                state=counts.state,
                experiment=summary.experiment,
                modes=Separator.COMMA.join(summary.modes),
                expected=counts.expected,
                completed=counts.completed,
                missing=counts.missing,
                failed=counts.failed,
                infeasible=counts.infeasible,
                invalid=counts.invalid,
            )
        )
    total = campaign.total
    typer.echo(
        CliMessage.STATUS_TOTAL_LINE.format(
            state=total.state,
            experiments=len(campaign.experiments),
            expected=total.expected,
            completed=total.completed,
            missing=total.missing,
            failed=total.failed,
            infeasible=total.infeasible,
            invalid=total.invalid,
        )
    )
    _finished(context, Verdict.PASS)


@app.command(name=CliCommand.REPORT)
def report() -> None:
    context = _context(CliCommand.REPORT)
    try:
        stages = report_workflow.run_report(context.paths, context.config)
    except CtkError as error:
        typer.echo(CliMessage.FAILURE_LINE.format(reason=error.reason, error=error))
        _failed(context, error)
        raise typer.Exit(code=1) from error
    for stage in stages:
        typer.echo(CliMessage.REPORT_STAGE_LINE.format(stage=stage))
    typer.echo(CliMessage.REPORT_DONE_LINE)
    _finished(context, Verdict.PASS)
