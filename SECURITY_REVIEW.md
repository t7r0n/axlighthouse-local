# Security Review

## Scope

Local CLI, deterministic synthetic AX target fixtures, probe evaluator, transcript replay, DuckDB run store, JSONL tool loop, static dashboard, and demo-pack export.

## Assessment

The application is offline and synthetic-only. It does not contact websites, model APIs, hosted agent runtimes, identity systems, deployment systems, or shell commands at runtime.

## Controls

- Fixtures and tool-loop inputs are parsed through Pydantic models.
- Probe IDs, pillar names, and scoring rules are closed local enumerations.
- Scores are computed from deterministic probe outcomes, not generated narration.
- Transcript replay ignores runtime labels for scoring and verifies transcript hashes.
- DuckDB writes use parameterized inserts.
- Dashboard rendering uses Jinja autoescaping.
- Generated runtime state, outputs, caches, and virtual environments are ignored by git.

## Focused Scan Status

Completed for the public release.

## Results

- Static public-release hygiene scan: clean for non-public context, personal account strings, cloud credential markers, and common secret prefixes.
- Runtime surface scan: no network clients, dynamic code execution, unsafe deserialization, or shell execution in application code.
- Test-only process launch is limited to CLI regression coverage.
- Validation suite: `ruff`, `pytest`, `axlighthouse-local verify`, `axlighthouse-local benchmark --iterations 100`, and dashboard HTML/browser checks passed.
- DuckDB access is guarded by a local file lock to avoid parallel-run store contention.

## Residual Risk

This is a deterministic offline benchmark over synthetic target surfaces. It is not a hosted crawler, authentication tester, or production agent runtime. Real deployments should add explicit permission controls, bounded network fetch rules, and target-owner authorization.
