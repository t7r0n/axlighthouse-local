# AXLighthouse Local

AXLighthouse Local is an offline, deterministic audit harness for agent experience. It scores product surfaces across four pillars: Access, Context, Tools, and Orchestration.

The project is intentionally local-first. It does not call external sites, model APIs, hosted agent runtimes, identity providers, or deployment platforms. Demo targets are synthetic fixtures, and replay is deterministic so scores stay stable across agent-runtime labels.

## Capabilities

- Four-pillar AX score from deterministic probes.
- Synthetic target fixtures for platform, API-first, workflow, edge-hosting, and legacy-control surfaces.
- Replayable `transcript.jsonl` files with content hashes.
- Cross-agent replay check: the same transcript must produce identical scores for different runtime labels.
- DuckDB run store, static light/dark leaderboard dashboard, Markdown reports, demo pack export, and JSONL tool loop.

## Quickstart

```bash
uv sync
uv run axlighthouse-local init-demo
uv run axlighthouse-local audit platform-prime --agent codex
uv run axlighthouse-local leaderboard
uv run axlighthouse-local verify
uv run axlighthouse-local dashboard
uv run axlighthouse-local benchmark --iterations 100
```

## Release Gate

```bash
uv run ruff check .
uv run pytest -q
uv run axlighthouse-local verify
uv run axlighthouse-local benchmark --iterations 100
```

Generated data, outputs, local databases, caches, and virtual environments are ignored by git.

