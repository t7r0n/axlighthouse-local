from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class Pillar(StrEnum):
    ACCESS = "access"
    CONTEXT = "context"
    TOOLS = "tools"
    ORCHESTRATION = "orchestration"


class TargetSurface(BaseModel):
    id: str
    name: str
    url: str
    agent_signup: bool = False
    sandbox_key_flow: bool = False
    deploy_without_handoff: bool = False
    machine_docs: bool = False
    llms_txt: bool = False
    well_known_manifest: bool = False
    mcp_discovery: bool = False
    api_noun_coverage: float = Field(ge=0.0, le=1.0)
    tool_listed_actions: int = Field(ge=0)
    skill_docs: bool = False
    webhook_trigger: bool = False
    chained_runs: bool = False
    serverless_agent_runtime: bool = False
    notes: str = ""


class ProbeResult(BaseModel):
    probe_id: str
    pillar: Pillar
    score: float = Field(ge=0.0)
    max_score: float = Field(gt=0.0)
    passed: bool
    evidence: str
    fix: str


class AuditReport(BaseModel):
    run_id: str
    target_id: str
    target_name: str
    agent_runtime: str
    pillar_scores: dict[Pillar, float]
    total_score: float
    grade: str
    transcript_hash: str
    pass_audit: bool
    probe_results: list[ProbeResult]


class TranscriptEvent(BaseModel):
    event_index: int
    run_id: str
    target_id: str
    agent_runtime: str
    probe_id: str
    pillar: Pillar
    outcome: dict[str, str | float | bool]


class SuiteSummary(BaseModel):
    run_id: str
    target_count: int
    pass_rate: float
    avg_score: float
    top_score: float
    deterministic_replay: bool
    all_pillars_present: bool
    pass_gates: bool


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]

