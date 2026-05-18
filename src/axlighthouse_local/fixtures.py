from __future__ import annotations

import json
from pathlib import Path

from axlighthouse_local.models import TargetSurface, project_root

DEMO_TARGETS = [
    {
        "id": "platform-prime",
        "name": "Platform Prime",
        "url": "https://platform-prime.example",
        "agent_signup": True,
        "sandbox_key_flow": True,
        "deploy_without_handoff": True,
        "machine_docs": True,
        "llms_txt": True,
        "well_known_manifest": True,
        "mcp_discovery": True,
        "api_noun_coverage": 0.92,
        "tool_listed_actions": 18,
        "skill_docs": True,
        "webhook_trigger": True,
        "chained_runs": True,
        "serverless_agent_runtime": True,
        "notes": "High-readiness platform surface with strong agent affordances.",
    },
    {
        "id": "api-foundry",
        "name": "API Foundry",
        "url": "https://api-foundry.example",
        "agent_signup": True,
        "sandbox_key_flow": True,
        "deploy_without_handoff": False,
        "machine_docs": True,
        "llms_txt": True,
        "well_known_manifest": False,
        "mcp_discovery": False,
        "api_noun_coverage": 0.88,
        "tool_listed_actions": 11,
        "skill_docs": True,
        "webhook_trigger": True,
        "chained_runs": False,
        "serverless_agent_runtime": False,
        "notes": "API-first product with strong tools but weaker orchestration.",
    },
    {
        "id": "workflow-hub",
        "name": "Workflow Hub",
        "url": "https://workflow-hub.example",
        "agent_signup": False,
        "sandbox_key_flow": True,
        "deploy_without_handoff": False,
        "machine_docs": True,
        "llms_txt": False,
        "well_known_manifest": True,
        "mcp_discovery": True,
        "api_noun_coverage": 0.74,
        "tool_listed_actions": 9,
        "skill_docs": True,
        "webhook_trigger": True,
        "chained_runs": True,
        "serverless_agent_runtime": False,
        "notes": "Workflow product with useful orchestration but uneven access.",
    },
    {
        "id": "edge-builder",
        "name": "Edge Builder",
        "url": "https://edge-builder.example",
        "agent_signup": True,
        "sandbox_key_flow": False,
        "deploy_without_handoff": True,
        "machine_docs": True,
        "llms_txt": True,
        "well_known_manifest": False,
        "mcp_discovery": True,
        "api_noun_coverage": 0.81,
        "tool_listed_actions": 14,
        "skill_docs": False,
        "webhook_trigger": True,
        "chained_runs": False,
        "serverless_agent_runtime": True,
        "notes": "Modern hosting surface with good access and partial context.",
    },
    {
        "id": "legacy-control",
        "name": "Legacy Control",
        "url": "https://legacy-control.example",
        "agent_signup": False,
        "sandbox_key_flow": False,
        "deploy_without_handoff": False,
        "machine_docs": False,
        "llms_txt": False,
        "well_known_manifest": False,
        "mcp_discovery": False,
        "api_noun_coverage": 0.16,
        "tool_listed_actions": 1,
        "skill_docs": False,
        "webhook_trigger": False,
        "chained_runs": False,
        "serverless_agent_runtime": False,
        "notes": "Control target with mostly human-only workflows.",
    },
]

PROBE_DOCS = {
    "access": "Can an autonomous agent obtain a sandbox, credentials, and a deployable path without human handoff?",
    "context": "Can an agent discover machine-readable docs, manifests, and runtime-specific context?",
    "tools": "Can an agent operate the product noun graph through complete tools and skill-shaped docs?",
    "orchestration": "Can an agent be triggered, chained, and hosted as part of a durable workflow?",
}


def fixtures_dir() -> Path:
    path = project_root() / "fixtures"
    path.mkdir(parents=True, exist_ok=True)
    return path


def targets_path() -> Path:
    return fixtures_dir() / "targets.json"


def write_demo_fixtures(force: bool = False) -> list[Path]:
    paths: list[Path] = []
    if force or not targets_path().exists():
        targets_path().write_text(json.dumps(DEMO_TARGETS, indent=2), encoding="utf-8")
    paths.append(targets_path())
    probe_dir = fixtures_dir() / "probes"
    probe_dir.mkdir(exist_ok=True)
    for pillar, text in PROBE_DOCS.items():
        path = probe_dir / f"{pillar}.md"
        if force or not path.exists():
            path.write_text(f"# {pillar.title()} Probe Skill\n\n{text}\n", encoding="utf-8")
        paths.append(path)
    return paths


def load_targets() -> list[TargetSurface]:
    if not targets_path().exists():
        write_demo_fixtures()
    return [TargetSurface.model_validate(row) for row in json.loads(targets_path().read_text(encoding="utf-8"))]


def load_target(target_id: str) -> TargetSurface:
    targets = {target.id: target for target in load_targets()}
    if target_id not in targets:
        raise KeyError(f"unknown target: {target_id}")
    return targets[target_id]

