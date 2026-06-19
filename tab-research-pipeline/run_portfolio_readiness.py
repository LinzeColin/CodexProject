import json
from pathlib import Path

from tab_research.boards import audit_portfolio, render_portfolio_markdown
from tab_research.io import atomic_write_json, atomic_write_text, single_instance_lock
from tab_research.paths import resolve_output_dir, resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
VERSION = "v0_12"
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        portfolio = audit_portfolio(OUT)
        gate_path = OUT / f"portfolio_automation_gate_{VERSION}.json"
        report_path = OUT / f"tab_fifa_portfolio_readiness_{VERSION}.md"
        atomic_write_json(gate_path, portfolio)
        atomic_write_text(report_path, render_portfolio_markdown(portfolio))
    print(json.dumps({
        "version": VERSION,
        "portfolio_automation_ready": portfolio["portfolio_automation_ready"],
        "ready_required_boards": f"{portfolio['ready_required_board_count']}/{portfolio['required_board_count']}",
        "gate": str(gate_path),
        "report": str(report_path),
    }, indent=2))
