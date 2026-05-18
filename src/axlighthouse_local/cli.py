from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from axlighthouse_local.audit import audit_target, latest_transcript_for, replay_transcript
from axlighthouse_local.dashboard import build_dashboard
from axlighthouse_local.fixtures import load_targets, write_demo_fixtures
from axlighthouse_local.models import Pillar, project_root
from axlighthouse_local.runner import benchmark, export_demo_pack, run_suite, verify_outputs

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def init_demo(force: bool = typer.Option(False, "--force", help="Overwrite existing fixtures.")) -> None:
    paths = write_demo_fixtures(force=force)
    console.print({"fixtures": [str(path) for path in paths]})


@app.command()
def audit(target_id: str, agent: str = typer.Option("codex", "--agent")) -> None:
    report = audit_target(target_id, agent_runtime=agent)
    console.print_json(report.model_dump_json())


@app.command()
def leaderboard(agent: str = typer.Option("codex", "--agent")) -> None:
    summary = run_suite(agent_runtime=agent)
    console.print_json(summary.model_dump_json())


@app.command()
def replay(transcript: Path, agent: str = typer.Option("codex", "--agent")) -> None:
    report = replay_transcript(transcript, agent_runtime=agent)
    console.print_json(report.model_dump_json())


@app.command()
def replay_latest(target_id: str, agent: str = typer.Option("alternate", "--agent")) -> None:
    report = replay_transcript(latest_transcript_for(target_id), agent_runtime=agent)
    console.print_json(report.model_dump_json())


@app.command()
def explain(pillar: Pillar) -> None:
    path = project_root() / "fixtures" / "probes" / f"{pillar.value}.md"
    if not path.exists():
        write_demo_fixtures()
    console.print(path.read_text(encoding="utf-8"))


@app.command()
def targets() -> None:
    table = Table(title="Demo Targets")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("URL")
    for target in load_targets():
        table.add_row(target.id, target.name, target.url)
    console.print(table)


@app.command()
def verify() -> None:
    ok, checks = verify_outputs()
    table = Table(title="Verification")
    table.add_column("Gate")
    table.add_column("Status")
    for key, value in checks.items():
        table.add_row(key, "PASS" if value else "FAIL")
    console.print(table)
    if not ok:
        raise typer.Exit(1)


@app.command()
def dashboard() -> None:
    path = build_dashboard()
    console.print(f"Dashboard written: {path}")


@app.command("benchmark")
def benchmark_cmd(iterations: int = typer.Option(100, "--iterations", min=1)) -> None:
    summary = benchmark(iterations=iterations)
    table = Table(title="Benchmark")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("audits", str(summary.target_count * iterations))
    table.add_row("average score", str(summary.avg_score))
    table.add_row("top score", str(summary.top_score))
    table.add_row("deterministic replay", str(summary.deterministic_replay))
    table.add_row("pass gates", str(summary.pass_gates))
    console.print(table)


@app.command("export-demo-pack")
def export_demo_pack_cmd() -> None:
    path = export_demo_pack()
    console.print(f"Demo pack written: {path}")


@app.command()
def tool_loop() -> None:
    for line in sys.stdin:
        payload = json.loads(line)
        tool = payload.get("tool")
        args = payload.get("arguments", {})
        if tool == "audit":
            report = audit_target(args["target_id"], agent_runtime=args.get("agent", "codex"))
            print(report.model_dump_json())
        elif tool == "replay-latest":
            report = replay_transcript(
                latest_transcript_for(args["target_id"]),
                agent_runtime=args.get("agent", "alternate"),
            )
            print(report.model_dump_json())
        elif tool == "leaderboard":
            summary = run_suite(agent_runtime=args.get("agent", "codex"))
            print(summary.model_dump_json())
        else:
            print(json.dumps({"error": f"unknown tool: {tool}"}))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
