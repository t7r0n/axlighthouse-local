# ruff: noqa: E501
from __future__ import annotations

from collections.abc import Callable

from axlighthouse_local.models import Pillar, ProbeResult, TargetSurface

ProbeFn = Callable[[TargetSurface], tuple[float, bool, str, str]]


def _bool_probe(field: str, points: float, evidence_ok: str, fix: str) -> ProbeFn:
    def check(target: TargetSurface) -> tuple[float, bool, str, str]:
        passed = bool(getattr(target, field))
        return points if passed else 0.0, passed, evidence_ok if passed else f"{field} missing", fix

    return check


def _coverage_probe(target: TargetSurface) -> tuple[float, bool, str, str]:
    score = round(10.0 * target.api_noun_coverage, 2)
    passed = target.api_noun_coverage >= 0.75
    return score, passed, f"API noun coverage {target.api_noun_coverage:.0%}", "Expose core product nouns through API tools."


def _tool_count_probe(target: TargetSurface) -> tuple[float, bool, str, str]:
    capped = min(target.tool_listed_actions, 12)
    score = round(capped / 12.0 * 7.0, 2)
    passed = target.tool_listed_actions >= 8
    return score, passed, f"{target.tool_listed_actions} listed tool actions", "Publish a complete tool manifest."


PROBES: list[tuple[str, Pillar, float, ProbeFn]] = [
    ("access.agent_signup", Pillar.ACCESS, 8.0, _bool_probe("agent_signup", 8.0, "agent can create sandbox account", "Add agent-safe sandbox signup.")),
    ("access.sandbox_key_flow", Pillar.ACCESS, 8.0, _bool_probe("sandbox_key_flow", 8.0, "sandbox credential flow exists", "Add scoped sandbox credential flow.")),
    ("access.deploy_without_handoff", Pillar.ACCESS, 9.0, _bool_probe("deploy_without_handoff", 9.0, "agent can deploy without handoff", "Remove human-only deployment gate.")),
    ("context.machine_docs", Pillar.CONTEXT, 6.0, _bool_probe("machine_docs", 6.0, "machine-readable docs present", "Publish machine-readable docs.")),
    ("context.llms_txt", Pillar.CONTEXT, 6.0, _bool_probe("llms_txt", 6.0, "llms.txt present", "Add llms.txt with canonical docs.")),
    ("context.well_known_manifest", Pillar.CONTEXT, 6.0, _bool_probe("well_known_manifest", 6.0, "well-known manifest present", "Expose a well-known agent manifest.")),
    ("context.mcp_discovery", Pillar.CONTEXT, 7.0, _bool_probe("mcp_discovery", 7.0, "MCP discovery succeeds", "Add MCP discovery metadata.")),
    ("tools.api_noun_coverage", Pillar.TOOLS, 10.0, _coverage_probe),
    ("tools.tool_listed_actions", Pillar.TOOLS, 7.0, _tool_count_probe),
    ("tools.skill_docs", Pillar.TOOLS, 8.0, _bool_probe("skill_docs", 8.0, "skill-shaped docs present", "Publish skill-shaped task docs.")),
    ("orchestration.webhook_trigger", Pillar.ORCHESTRATION, 8.0, _bool_probe("webhook_trigger", 8.0, "webhook trigger exists", "Add webhook or event trigger.")),
    ("orchestration.chained_runs", Pillar.ORCHESTRATION, 8.0, _bool_probe("chained_runs", 8.0, "agent runs can chain", "Allow chained agent runs.")),
    ("orchestration.serverless_agent_runtime", Pillar.ORCHESTRATION, 9.0, _bool_probe("serverless_agent_runtime", 9.0, "hosted agent runtime exists", "Expose hosted execution for agents.")),
]


def run_probes(target: TargetSurface) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for probe_id, pillar, max_score, check in PROBES:
        score, passed, evidence, fix = check(target)
        results.append(
            ProbeResult(
                probe_id=probe_id,
                pillar=pillar,
                score=round(score, 2),
                max_score=max_score,
                passed=passed,
                evidence=evidence,
                fix=fix,
            )
        )
    return results


def grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 55:
        return "D"
    return "F"
