from __future__ import annotations

import json
import subprocess

from axlighthouse_local.audit import audit_target, latest_transcript_for, replay_transcript
from axlighthouse_local.dashboard import build_dashboard
from axlighthouse_local.fixtures import write_demo_fixtures
from axlighthouse_local.runner import export_demo_pack, run_suite, verify_outputs


def test_high_readiness_target_scores_above_90() -> None:
    write_demo_fixtures(force=True)
    report = audit_target("platform-prime", agent_runtime="codex")
    assert report.total_score >= 90
    assert report.grade == "A"


def test_legacy_control_stays_low() -> None:
    write_demo_fixtures(force=True)
    report = audit_target("legacy-control", agent_runtime="codex")
    assert report.total_score <= 25
    assert not report.pass_audit


def test_replay_is_runtime_deterministic() -> None:
    write_demo_fixtures(force=True)
    original = audit_target("api-foundry", agent_runtime="codex")
    replayed = replay_transcript(latest_transcript_for("api-foundry"), agent_runtime="another-agent")
    assert replayed.total_score == original.total_score
    assert replayed.pillar_scores == original.pillar_scores
    assert replayed.transcript_hash == original.transcript_hash


def test_suite_verifies() -> None:
    summary = run_suite()
    assert summary.deterministic_replay
    build_dashboard()
    ok, checks = verify_outputs()
    assert ok, checks


def test_dashboard_and_demo_pack() -> None:
    run_suite()
    dashboard = build_dashboard()
    html = dashboard.read_text(encoding="utf-8")
    assert "AXLighthouse Local" in html
    assert "Audit Results" in html
    assert "themeToggle" in html
    pack = export_demo_pack()
    assert (pack / "manifest.json").exists()


def test_jsonl_tool_loop() -> None:
    payload = {"tool": "audit", "arguments": {"target_id": "platform-prime", "agent": "codex"}}
    completed = subprocess.run(
        ["uv", "run", "--project", "elite_projects/axlighthouse-local", "axlighthouse-local", "tool-loop"],
        input=json.dumps(payload) + "\n",
        text=True,
        capture_output=True,
        check=True,
    )
    report = json.loads(completed.stdout)
    assert report["target_id"] == "platform-prime"
    assert report["total_score"] >= 90


def test_explain_command_resolves_project_fixtures() -> None:
    completed = subprocess.run(
        ["uv", "run", "--project", "elite_projects/axlighthouse-local", "axlighthouse-local", "explain", "context"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Context Probe Skill" in completed.stdout
