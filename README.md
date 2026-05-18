# AXLighthouse Local

AXLighthouse Local is an offline, deterministic audit harness for agent experience. It scores product surfaces across four pillars: Access, Context, Tools, and Orchestration.

The project is intentionally local-first. It does not call external sites, model APIs, hosted agent runtimes, identity providers, or deployment platforms. Demo targets are synthetic fixtures, and replay is deterministic so scores stay stable across agent-runtime labels.

## Design intent

Offline deterministic agent-experience audit harness with replayable transcripts.

## Implementation notes

- Four-pillar AX score from deterministic probes.
- Synthetic target fixtures for platform, API-first, workflow, edge-hosting, and legacy-control surfaces.
- Replayable `transcript.jsonl` files with content hashes.
- Cross-agent replay check: the same transcript must produce identical scores for different runtime labels.
- DuckDB run store, static light/dark leaderboard dashboard, Markdown reports, demo pack export, and JSONL tool loop.

## Reproduce the run

```bash
uv sync
uv run axlighthouse-local init-demo
uv run axlighthouse-local audit platform-prime --agent codex
uv run axlighthouse-local leaderboard
uv run axlighthouse-local verify
uv run axlighthouse-local dashboard
uv run axlighthouse-local benchmark --iterations 100
```

## Artifacts

- `outputs/summary.json` for headline metrics and gate status
- `outputs/reports.json` for per-case results
- `outputs/dashboard.html` for visual inspection
- `outputs/demo-pack.zip` or `outputs/demo_pack/` for portable review

## Release checks

```bash
uv run ruff check .
uv run pytest -q
uv run axlighthouse-local verify
uv run axlighthouse-local benchmark --iterations 100
```

## Public data stance

The `axlighthouse-local` public surface is source, tests, lockfile, and docs. It does not need credentials, browser state, customer records, or hosted services.
