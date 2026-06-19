import json
import plistlib
from csv import DictWriter
from datetime import date, timedelta
from pathlib import Path

from app.core.completion_audit import run_completion_audit
from app.core.pipeline import import_alipay_csv, run_slot
from app.core.risk_gate_regression import run_risk_gate_regression
from tests.helpers import copy_sample_data, temp_settings


def _write_launchd_template(path: Path, root: Path, *, start_interval: int = 180, command: str = "automation-tick") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "Label": "com.serenity.daily-analysis",
        "ProgramArguments": [
            "/opt/anaconda3/bin/python",
            "-m",
            "app.cli",
            command,
            "--no-dry-run",
            "--send-mail",
            "--local",
            "--json",
        ],
        "WorkingDirectory": root.as_posix(),
        "StartInterval": start_interval,
        "EnvironmentVariables": {
            "SERENITY_DRY_RUN": "true",
            "SERENITY_MAIL_SEND_ENABLED": "false",
        },
    }
    with path.open("wb") as handle:
        plistlib.dump(data, handle)


def test_completion_audit_writes_outputs_and_blocks_missing_production_evidence(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = run_completion_audit(settings)

    assert result["overall_status"] == "blocked"
    assert result["block_count"] > 0
    assert Path(result["json_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert Path(result["csv_path"]).exists()

    items = {item["item_id"]: item for item in result["items"]}
    assert items["schedule_exact"]["status"] == "pass"
    assert items["risk_thresholds"]["status"] == "pass"
    assert items["business_day_schedule_gate"]["status"] == "pass"
    assert items["production_preflight"]["status"] == "block"
    assert items["intake_validation"]["status"] == "block"
    assert items["no_trade_execution_code"]["status"] == "pass"
    assert items["benchmark_dynamic_window"]["status"] == "pass"


def test_completion_audit_blocks_formal_report_local_path_leak(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    report_dir = settings.root_dir / "outputs" / "preflight"
    report_dir.mkdir(parents=True)
    (report_dir / "PRODUCTION_READINESS_REPORT.md").write_text(
        "Formal report leaked /Users/linzezhang/Documents/Codex/private.csv\n",
        encoding="utf-8",
    )
    (report_dir / "PRODUCTION_READINESS_REPORT.pdf").write_bytes(
        b"%PDF-1.4\n(/Users/linzezhang/Documents/Codex/private.csv) Tj\n%%EOF\n"
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["formal_report_path_redaction"]["status"] == "block"
    assert "/Users/" in items["formal_report_path_redaction"]["proof"]


def test_completion_audit_blocks_holdings_discovery_markdown_local_path_leak(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    preflight_dir = settings.root_dir / "outputs" / "preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    review_matrix = preflight_dir / "alipay_holdings_review_matrix.csv"
    review_matrix.write_text("asset_code\nFUND001\n", encoding="utf-8")
    (preflight_dir / "holdings_discovery_latest.json").write_text(
        json.dumps(
            {
                "review_matrix_csv": str(review_matrix),
                "review_summary": {
                    "rows": 1,
                    "row_production_candidate_count": 0,
                    "stale_or_missing_date_count": 1,
                    "special_fund_rule_check_required_count": 0,
                },
            }
        ),
        encoding="utf-8",
    )
    (preflight_dir / "holdings_discovery_latest.md").write_text(
        "Leaked /Users/linzezhang/Documents/Codex/private-holdings.csv\n",
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["holdings_discovery_markdown_redaction"]["status"] == "block"
    assert "/Users/" in items["holdings_discovery_markdown_redaction"]["proof"]


def test_completion_audit_blocks_auxiliary_markdown_local_path_leak(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    preflight_dir = settings.root_dir / "outputs" / "preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    (preflight_dir / "preflight_latest.md").write_text(
        "Auxiliary report leaked /Users/linzezhang/Documents/Codex/private.csv\n",
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["auxiliary_markdown_path_redaction"]["status"] == "block"
    assert "/Users/" in items["auxiliary_markdown_path_redaction"]["proof"]


def test_completion_audit_blocks_intake_pack_user_facing_local_path_leak(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    intake_dir = settings.root_dir / "outputs" / "intake_pack"
    intake_dir.mkdir(parents=True, exist_ok=True)
    (intake_dir / "06_alipay_positions_review_prefill.csv").write_text(
        "asset_code,source_note\nFUND001,prior_source_file=/Users/linzezhang/Downloads/private.mp4\n",
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["intake_pack_user_facing_path_redaction"]["status"] == "block"
    assert "/Users/" in items["intake_pack_user_facing_path_redaction"]["proof"]


def test_completion_audit_blocks_stale_readiness_report_package_count(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    report_dir = settings.root_dir / "outputs" / "preflight"
    package_dir = settings.root_dir / "outputs" / "package"
    report_dir.mkdir(parents=True)
    package_dir.mkdir(parents=True)
    (report_dir / "PRODUCTION_READINESS_REPORT.md").write_text(
        "Delivery packaging uses package-delivery. The latest final ZIP has 219 members and no private-evidence members.\n",
        encoding="utf-8",
    )
    (package_dir / "package_latest.json").write_text(
        json.dumps({"member_count": 239, "included_private_like_members": []}),
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["readiness_report_package_consistency"]["status"] == "block"
    assert "239 members" in items["readiness_report_package_consistency"]["proof"]


def test_completion_audit_blocks_stale_readiness_report_benchmark_summary(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    report_dir = settings.root_dir / "outputs" / "preflight"
    report_dir.mkdir(parents=True)
    history_path = settings.manual_dir / "benchmark_price_history.csv"
    rows = []
    start = date(2026, 3, 1)
    for code, base in [("000001.SH", 4000), ("SPX", 7000)]:
        for offset in range(0, 100, 2):
            rows.append(
                {
                    "asset_code": code,
                    "date": (start + timedelta(days=offset)).isoformat(),
                    "close": str(base + offset),
                    "source_name": "test",
                    "source_type": "public_aggregation",
                    "source_priority": "5",
                    "url_or_path": "https://example.com",
                    "evidence_level": "Medium",
                    "as_of": "2026-06-12",
                }
            )
    with history_path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (report_dir / "PRODUCTION_READINESS_REPORT.md").write_text(
        "Shanghai Composite canonical code `000001.SH`: 49 rows from 2026-03-01 to 2026-06-05.\n"
        "S&P 500 canonical code `SPX`: 49 rows from 2026-03-01 to 2026-06-05.\n",
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["readiness_report_benchmark_consistency"]["status"] == "block"
    assert "000001.SH" in items["readiness_report_benchmark_consistency"]["proof"]


def test_completion_audit_requires_execution_lock_for_manual_review_run(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    candidates_path = settings.manual_dir / "candidates.csv"
    candidates_text = candidates_path.read_text(encoding="utf-8")
    candidates_path.write_text(candidates_text.replace(",2,false,Strong,", ",0,false,Strong,", 1), encoding="utf-8")
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    run_slot(settings, "R7", dry_run=True, run_date=date(2026, 6, 12))

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["execution_lock_zero_order"]["status"] == "pass"
    assert "data_quality_status=manual_review" in items["execution_lock_zero_order"]["proof"]


def test_completion_audit_accepts_risk_gate_regression_when_latest_run_has_no_hard_gate_hit(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    import_alipay_csv(settings, settings.imports_dir / "alipay_positions.csv")
    run_slot(settings, "R7", dry_run=True, run_date=date(2026, 6, 12))
    run_risk_gate_regression(settings)

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["hard_risk_gate_evidence"]["status"] == "pass"
    assert "hard_gate_review_rows=0" in items["hard_risk_gate_evidence"]["proof"]
    assert "regression_status=pass" in items["hard_risk_gate_evidence"]["proof"]


def test_completion_audit_accepts_safe_launchd_runtime_status(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    status_dir = settings.root_dir / "outputs" / "implementation"
    status_dir.mkdir(parents=True)
    (status_dir / "LAUNCHD_STATUS.json").write_text(
        json.dumps(
            {
                "install_state": "loaded",
                "plist_lint": "OK",
                "stderr_bytes": 0,
                "mail_send_enabled": False,
                "automatic_trading": False,
                "latest_tick": {
                    "action": "non_business_day",
                    "dry_run": True,
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["launchd_runtime_status"]["status"] == "pass"
    assert "install_state=loaded" in items["launchd_runtime_status"]["proof"]
    assert "latest_tick_action=non_business_day" in items["launchd_runtime_status"]["proof"]


def test_completion_audit_accepts_shadow_safe_launchd_schedule_contract(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_launchd_template(
        settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist",
        settings.root_dir,
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["launchd_schedule_contract"]["status"] == "pass"
    assert "StartInterval=180" in items["launchd_schedule_contract"]["proof"]


def test_completion_audit_blocks_slow_or_wrong_launchd_schedule_contract(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    _write_launchd_template(
        settings.root_dir / "outputs" / "implementation" / "com.serenity.daily-analysis.plist",
        settings.root_dir,
        start_interval=600,
        command="scheduler-tick",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["launchd_schedule_contract"]["status"] == "block"
    assert "scheduler-tick" in items["launchd_schedule_contract"]["proof"]
    assert "StartInterval=600" in items["launchd_schedule_contract"]["proof"]


def test_completion_audit_surfaces_mail_send_config_gate(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    report_dir = settings.root_dir / "outputs" / "preflight"
    report_dir.mkdir(parents=True)
    (report_dir / "preflight_latest.json").write_text(
        json.dumps(
            {
                "production_ready": False,
                "shadow_ready": True,
                "blockers": [{"name": "mail_send_config"}],
                "checks": [
                    {"name": "mail_send_config", "status": "block", "evidence": {"mail_send_enabled": False}},
                    {"name": "moomoo_opend", "status": "pass", "message": "socket ok"},
                    {"name": "benchmark_sources", "status": "pass", "evidence": {"ok": True}},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["mail_send_config_gate"]["status"] == "block"
    assert "SERENITY_MAIL_SEND_ENABLED=true" in items["mail_send_config_gate"]["next_action"]


def test_completion_audit_requires_production_unlock_workflow_artifact(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["production_unlock_workflow"]["status"] == "block"
    assert "production-unlock-check" in items["production_unlock_workflow"]["next_action"]


def test_completion_audit_accepts_production_unlock_workflow_artifact(tmp_path: Path):
    settings = temp_settings(tmp_path)
    copy_sample_data(settings, Path.cwd())
    output_dir = settings.root_dir / "outputs" / "preflight"
    output_dir.mkdir(parents=True)
    (output_dir / "production_unlock_check_latest.json").write_text(
        json.dumps(
            {
                "status": "blocked",
                "production_ready": False,
                "stop_reason": "pack source evidence audit failed",
                "stages": [
                    {"name": "source_evidence_audit_pack", "status": "block", "summary": {}},
                    {"name": "promote_intake_pack_dry_run", "status": "block", "summary": {}},
                    {"name": "preflight", "status": "block", "summary": {}},
                    {"name": "completion_audit", "status": "block", "summary": {}},
                ],
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "production_unlock_check_latest.md").write_text(
        "# Production Unlock Check\n\n"
        "## Boundary\n\n"
        "- This command does not send mail.\n"
        "- This command does not place trades.\n"
        "- `--apply` only promotes the intake pack after evidence and dry-run promotion checks pass.\n"
        "- Production remains locked unless preflight and completion audit both pass.\n",
        encoding="utf-8",
    )

    result = run_completion_audit(settings)

    items = {item["item_id"]: item for item in result["items"]}
    assert items["production_unlock_workflow"]["status"] == "pass"
    assert "status=blocked" in items["production_unlock_workflow"]["proof"]
