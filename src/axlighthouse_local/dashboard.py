# ruff: noqa: E501
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, select_autoescape

from axlighthouse_local.models import AuditReport, Pillar, SuiteSummary, project_root
from axlighthouse_local.runner import outputs_dir, run_suite

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AXLighthouse Local</title>
  <style>
    :root { color-scheme: light; --bg:#f8faf8; --panel:#fff; --text:#17201b; --muted:#64726b; --line:#dce8e1; --blue:#3b6fd8; --green:#209668; --amber:#be7c22; --red:#ce4f4f; --track:#edf3ef; }
    html[data-theme="dark"] { color-scheme: dark; --bg:#101512; --panel:#18201c; --text:#edf7f1; --muted:#a8b6af; --line:#2c3933; --track:#26302c; }
    * { box-sizing:border-box; }
    body { margin:0; overflow-x:hidden; background:var(--bg); color:var(--text); font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    main { max-width:1200px; margin:0 auto; padding:32px 20px 48px; }
    header { display:flex; justify-content:space-between; gap:18px; align-items:end; margin-bottom:24px; }
    h1 { margin:0 0 8px; font-size:32px; line-height:1.08; letter-spacing:0; }
    h2 { margin:0 0 14px; font-size:21px; letter-spacing:0; }
    p { margin:0; color:var(--muted); }
    .actions { display:flex; gap:10px; align-items:center; }
    .pill,.toggle { border:1px solid var(--line); border-radius:999px; padding:8px 12px; background:var(--panel); color:var(--text); font:inherit; font-size:13px; white-space:nowrap; }
    .toggle { cursor:pointer; }
    .grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; }
    .metric span { color:var(--muted); font-size:13px; }
    .metric strong { display:block; margin-top:8px; font-size:28px; }
    .wide { grid-column:span 2; }
    .full { grid-column:1/-1; }
    .bar { display:grid; grid-template-columns:150px 1fr 70px; gap:12px; align-items:center; margin:12px 0; }
    .track { height:13px; border-radius:999px; background:var(--track); overflow:hidden; }
    .fill { height:100%; border-radius:999px; background:var(--blue); }
    .fill.good { background:var(--green); }
    .fill.warn { background:var(--amber); }
    .fill.bad { background:var(--red); }
    .ok { color:var(--green); font-weight:700; }
    .bad-text { color:var(--red); font-weight:700; }
    .table-wrap { width:100%; overflow-x:auto; }
    table { width:100%; border-collapse:collapse; margin-top:8px; font-size:14px; }
    th,td { text-align:left; border-bottom:1px solid var(--line); padding:11px 8px; vertical-align:top; }
    th { color:var(--muted); font-weight:600; }
    td, th, p, h1, h2, .bar span { overflow-wrap:anywhere; }
    @media (max-width:860px) { header { display:block; } .actions { margin-top:16px; } .grid { grid-template-columns:1fr; } .wide { grid-column:auto; } }
  </style>
  <script>
    const savedTheme = localStorage.getItem("axlighthouse-theme") || "light";
    document.documentElement.dataset.theme = savedTheme;
    function toggleTheme() {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      localStorage.setItem("axlighthouse-theme", next);
      document.querySelector("#themeToggle").textContent = next === "dark" ? "Light" : "Dark";
    }
    window.addEventListener("DOMContentLoaded", () => {
      document.querySelector("#themeToggle").textContent =
        document.documentElement.dataset.theme === "dark" ? "Light" : "Dark";
    });
  </script>
</head>
<body>
<main>
  <header>
    <div>
      <h1>AXLighthouse Local</h1>
      <p>Deterministic agent-experience audits across Access, Context, Tools, and Orchestration.</p>
    </div>
    <div class="actions"><button class="toggle" id="themeToggle" onclick="toggleTheme()" type="button">Dark</button><div class="pill">Run {{ summary.run_id }}</div></div>
  </header>
  <section class="grid">
    <div class="panel metric"><span>Targets</span><strong>{{ summary.target_count }}</strong></div>
    <div class="panel metric"><span>Top score</span><strong>{{ summary.top_score }}</strong></div>
    <div class="panel metric"><span>Average</span><strong>{{ summary.avg_score }}</strong></div>
    <div class="panel metric"><span>Replay</span><strong>{{ "OK" if summary.deterministic_replay else "FAIL" }}</strong></div>
    <div class="panel wide score-bars">
      <h2>Leaderboard</h2>
      {% for report in reports %}
      <div class="bar"><span>{{ report.target_name }}</span><div class="track"><div class="fill {{ 'good' if report.total_score >= 80 else 'warn' if report.total_score >= 55 else 'bad' }}" style="width: {{ report.total_score }}%"></div></div><strong>{{ report.total_score }}</strong></div>
      {% endfor %}
    </div>
    <div class="panel wide">
      <h2>Suite Gates</h2>
      <table><tbody>
        <tr><td>Deterministic replay</td><td class="{{ 'ok' if summary.deterministic_replay else 'bad-text' }}">{{ "PASS" if summary.deterministic_replay else "FAIL" }}</td></tr>
        <tr><td>All pillars present</td><td class="{{ 'ok' if summary.all_pillars_present else 'bad-text' }}">{{ "PASS" if summary.all_pillars_present else "FAIL" }}</td></tr>
        <tr><td>Top score >= 90</td><td class="ok">{{ "PASS" if summary.top_score >= 90 else "FAIL" }}</td></tr>
        <tr><td>Legacy control stays low</td><td class="ok">{{ "PASS" if legacy_low else "FAIL" }}</td></tr>
      </tbody></table>
    </div>
    <div class="panel full">
      <h2>Audit Results</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Target</th><th>Total</th><th>Access</th><th>Context</th><th>Tools</th><th>Orchestration</th><th>Grade</th></tr></thead>
          <tbody>
          {% for report in reports %}
            <tr><td>{{ report.target_name }}</td><td>{{ report.total_score }}</td><td>{{ report.pillar_scores[access] }}</td><td>{{ report.pillar_scores[context] }}</td><td>{{ report.pillar_scores[tools] }}</td><td>{{ report.pillar_scores[orchestration] }}</td><td>{{ report.grade }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </section>
</main>
</body>
</html>
"""


def build_dashboard() -> Path:
    if not (outputs_dir() / "summary.json").exists():
        run_suite()
    summary = SuiteSummary.model_validate_json((outputs_dir() / "summary.json").read_text(encoding="utf-8"))
    reports = [AuditReport.model_validate(row) for row in json.loads((outputs_dir() / "leaderboard.json").read_text(encoding="utf-8"))]
    env = Environment(autoescape=select_autoescape(enabled_extensions=("html", "xml")), trim_blocks=True, lstrip_blocks=True)
    path = project_root() / "outputs" / "dashboard.html"
    legacy_low = any(report.target_id == "legacy-control" and report.total_score <= 25.0 for report in reports)
    path.write_text(
        env.from_string(TEMPLATE).render(
            summary=summary,
            reports=reports,
            legacy_low=legacy_low,
            access=Pillar.ACCESS,
            context=Pillar.CONTEXT,
            tools=Pillar.TOOLS,
            orchestration=Pillar.ORCHESTRATION,
        ),
        encoding="utf-8",
    )
    return path
