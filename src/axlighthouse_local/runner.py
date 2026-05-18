from __future__ import annotations

import fcntl
import json
import shutil
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from statistics import mean

import duckdb

from axlighthouse_local.audit import audit_target, latest_transcript_for, outputs_dir, replay_transcript
from axlighthouse_local.fixtures import load_targets, write_demo_fixtures
from axlighthouse_local.models import AuditReport, Pillar, SuiteSummary, project_root


def runs_dir() -> Path:
    path = project_root() / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return runs_dir() / "axlighthouse.duckdb"


@contextmanager
def store_lock() -> Iterator[None]:
    lock_path = project_root() / ".axlighthouse.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(db_path()))
    con.execute(
        """
        create table if not exists audits (
          run_id varchar,
          target_id varchar,
          target_name varchar,
          total_score double,
          grade varchar,
          access_score double,
          context_score double,
          tools_score double,
          orchestration_score double,
          transcript_hash varchar,
          pass_audit boolean
        )
        """
    )
    return con


def run_suite(agent_runtime: str = "codex") -> SuiteSummary:
    write_demo_fixtures()
    suite_id = f"suite-{time.time_ns():x}"[-20:]
    reports = [audit_target(target.id, agent_runtime=agent_runtime) for target in load_targets()]
    with store_lock():
        con = _connect()
        try:
            for report in reports:
                con.execute(
                    "insert into audits values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        report.run_id,
                        report.target_id,
                        report.target_name,
                        report.total_score,
                        report.grade,
                        report.pillar_scores[Pillar.ACCESS],
                        report.pillar_scores[Pillar.CONTEXT],
                        report.pillar_scores[Pillar.TOOLS],
                        report.pillar_scores[Pillar.ORCHESTRATION],
                        report.transcript_hash,
                        report.pass_audit,
                    ],
                )
        finally:
            con.close()
    deterministic = all(
        replay_transcript(
            latest_transcript_for(report.target_id),
            agent_runtime="alternate",
        ).total_score
        == report.total_score
        for report in reports
    )
    summary = SuiteSummary(
        run_id=suite_id,
        target_count=len(reports),
        pass_rate=round(sum(report.pass_audit for report in reports) / len(reports), 4),
        avg_score=round(float(mean(report.total_score for report in reports)), 2),
        top_score=max(report.total_score for report in reports),
        deterministic_replay=deterministic,
        all_pillars_present=all(set(report.pillar_scores) == set(Pillar) for report in reports),
        pass_gates=deterministic and all(set(report.pillar_scores) == set(Pillar) for report in reports),
    )
    write_outputs(reports, summary)
    return summary


def write_outputs(reports: list[AuditReport], summary: SuiteSummary) -> None:
    out = outputs_dir()
    leaderboard = sorted(reports, key=lambda report: report.total_score, reverse=True)
    (out / "leaderboard.json").write_text(
        json.dumps([report.model_dump(mode="json") for report in leaderboard], indent=2),
        encoding="utf-8",
    )
    (out / "summary.json").write_text(summary.model_dump_json(indent=2), encoding="utf-8")
    (out / "leaderboard.md").write_text(render_leaderboard(leaderboard, summary), encoding="utf-8")


def render_leaderboard(reports: list[AuditReport], summary: SuiteSummary) -> str:
    lines = [
        "# AXLighthouse Leaderboard",
        "",
        f"- Run: `{summary.run_id}`",
        f"- Average score: {summary.avg_score}",
        f"- Deterministic replay: {summary.deterministic_replay}",
        "",
        "| Rank | Target | Score | Access | Context | Tools | Orchestration | Grade |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, report in enumerate(reports, start=1):
        lines.append(
            f"| {rank} | {report.target_name} | {report.total_score} | "
            f"{report.pillar_scores[Pillar.ACCESS]} | {report.pillar_scores[Pillar.CONTEXT]} | "
            f"{report.pillar_scores[Pillar.TOOLS]} | {report.pillar_scores[Pillar.ORCHESTRATION]} | "
            f"{report.grade} |"
        )
    return "\n".join(lines) + "\n"


def verify_outputs() -> tuple[bool, dict[str, bool]]:
    summary_path = outputs_dir() / "summary.json"
    leaderboard_path = outputs_dir() / "leaderboard.json"
    dashboard_path = outputs_dir() / "dashboard.html"
    checks: dict[str, bool] = {
        "summary_exists": summary_path.exists(),
        "leaderboard_exists": leaderboard_path.exists(),
        "dashboard_exists": dashboard_path.exists(),
        "store_exists": db_path().exists(),
    }
    if not summary_path.exists() or not leaderboard_path.exists():
        return False, checks
    summary = SuiteSummary.model_validate_json(summary_path.read_text(encoding="utf-8"))
    reports = [AuditReport.model_validate(row) for row in json.loads(leaderboard_path.read_text(encoding="utf-8"))]
    checks.update(
        {
            "target_count": summary.target_count == len(load_targets()) == len(reports),
            "top_score_gate": summary.top_score >= 90.0,
            "legacy_control_low": any(
                report.target_id == "legacy-control" and report.total_score <= 25.0 for report in reports
            ),
            "deterministic_replay": summary.deterministic_replay,
            "all_pillars_present": summary.all_pillars_present,
            "markdown_exists": (outputs_dir() / "leaderboard.md").exists(),
        }
    )
    with store_lock():
        con = _connect()
        try:
            row_count = con.execute("select count(*) from audits").fetchone()[0]
        finally:
            con.close()
    checks["store_rows_present"] = row_count >= len(reports)
    return all(checks.values()), checks


def benchmark(iterations: int = 100) -> SuiteSummary:
    last = run_suite()
    for _ in range(iterations - 1):
        last = run_suite()
    return last


def export_demo_pack() -> Path:
    if not (outputs_dir() / "summary.json").exists():
        run_suite()
    pack = outputs_dir() / "demo_pack"
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir(parents=True)
    for name in ["summary.json", "leaderboard.json", "leaderboard.md"]:
        shutil.copy2(outputs_dir() / name, pack / name)
    reports_dir = pack / "reports"
    reports_dir.mkdir()
    for report in sorted(outputs_dir().glob("*/report.md")):
        target_dir = reports_dir / report.parent.name
        target_dir.mkdir()
        shutil.copy2(report, target_dir / "report.md")
        shutil.copy2(report.with_suffix(".json"), target_dir / "report.json")
    (pack / "manifest.json").write_text(
        json.dumps(
            {
                "name": "axlighthouse-local-demo-pack",
                "files": sorted(str(path.relative_to(pack)) for path in pack.rglob("*") if path.is_file()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return pack
