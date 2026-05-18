from __future__ import annotations

import hashlib
import time
from pathlib import Path

from axlighthouse_local.fixtures import load_target
from axlighthouse_local.models import AuditReport, Pillar, TranscriptEvent, project_root
from axlighthouse_local.probes import grade, run_probes


def outputs_dir() -> Path:
    path = project_root() / "outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def transcript_dir() -> Path:
    path = project_root() / "runs" / "transcripts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _hash_lines(lines: list[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _pillar_scores(results: list) -> dict[Pillar, float]:
    scores = {pillar: 0.0 for pillar in Pillar}
    for result in results:
        scores[result.pillar] += result.score
    return {pillar: round(score, 2) for pillar, score in scores.items()}


def audit_target(target_id: str, agent_runtime: str = "codex") -> AuditReport:
    target = load_target(target_id)
    run_id = f"run-{time.time_ns():x}"[-18:]
    results = run_probes(target)
    pillar_scores = _pillar_scores(results)
    total_score = round(sum(pillar_scores.values()), 2)
    lines: list[str] = []
    for index, result in enumerate(results):
        event = TranscriptEvent(
            event_index=index,
            run_id=run_id,
            target_id=target.id,
            agent_runtime=agent_runtime,
            probe_id=result.probe_id,
            pillar=result.pillar,
            outcome={
                "score": result.score,
                "max_score": result.max_score,
                "passed": result.passed,
                "evidence": result.evidence,
                "fix": result.fix,
            },
        )
        lines.append(event.model_dump_json())
    transcript_hash = _hash_lines(lines)
    transcript_path = transcript_dir() / f"{run_id}-{target.id}.jsonl"
    transcript_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = AuditReport(
        run_id=run_id,
        target_id=target.id,
        target_name=target.name,
        agent_runtime=agent_runtime,
        pillar_scores=pillar_scores,
        total_score=total_score,
        grade=grade(total_score),
        transcript_hash=transcript_hash,
        pass_audit=total_score >= 70.0 and all(score >= 10.0 for score in pillar_scores.values()),
        probe_results=results,
    )
    write_report(report)
    return report


def write_report(report: AuditReport) -> None:
    target_out = outputs_dir() / report.target_id
    target_out.mkdir(parents=True, exist_ok=True)
    (target_out / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    lines = [
        f"# AX Audit: {report.target_name}",
        "",
        f"- Score: {report.total_score}/100 ({report.grade})",
        f"- Runtime label: `{report.agent_runtime}`",
        f"- Transcript hash: `{report.transcript_hash}`",
        "",
        "| Pillar | Score |",
        "| --- | ---: |",
    ]
    for pillar, score in report.pillar_scores.items():
        lines.append(f"| {pillar.value} | {score}/25 |")
    lines.extend(["", "## Probe Findings", ""])
    for result in report.probe_results:
        status = "PASS" if result.passed else "MISS"
        lines.append(
            f"- `{result.probe_id}` [{status}] {result.score}/{result.max_score}: "
            f"{result.evidence}. Fix: {result.fix}"
        )
    (target_out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def replay_transcript(path: Path, agent_runtime: str = "codex") -> AuditReport:
    events = [
        TranscriptEvent.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    if not events:
        raise ValueError("empty transcript")
    target_id = events[0].target_id
    target = load_target(target_id)
    fresh = run_probes(target)
    fresh_by_id = {result.probe_id: result for result in fresh}
    for event in events:
        expected = fresh_by_id[event.probe_id]
        if float(event.outcome["score"]) != expected.score or bool(event.outcome["passed"]) != expected.passed:
            raise ValueError(f"transcript outcome drift for {event.probe_id}")
    pillar_scores = _pillar_scores(fresh)
    total_score = round(sum(pillar_scores.values()), 2)
    canonical_lines = [
        TranscriptEvent(
            event_index=event.event_index,
            run_id=event.run_id,
            target_id=event.target_id,
            agent_runtime=event.agent_runtime,
            probe_id=event.probe_id,
            pillar=event.pillar,
            outcome=event.outcome,
        ).model_dump_json()
        for event in events
    ]
    return AuditReport(
        run_id=events[0].run_id,
        target_id=target.id,
        target_name=target.name,
        agent_runtime=agent_runtime,
        pillar_scores=pillar_scores,
        total_score=total_score,
        grade=grade(total_score),
        transcript_hash=_hash_lines(canonical_lines),
        pass_audit=total_score >= 70.0 and all(score >= 10.0 for score in pillar_scores.values()),
        probe_results=fresh,
    )


def latest_transcript_for(target_id: str) -> Path:
    candidates = sorted(transcript_dir().glob(f"*-{target_id}.jsonl"))
    if not candidates:
        audit_target(target_id)
        candidates = sorted(transcript_dir().glob(f"*-{target_id}.jsonl"))
    return candidates[-1]
