from __future__ import annotations

import json
from pathlib import Path

from quantlab.system.macos_public_acceptance import (
    build_macos_public_acceptance_summary,
    macos_public_acceptance_markdown,
    write_macos_public_acceptance_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_public_acceptance_summary_has_no_local_details() -> None:
    for relative in (
        "docs/evidence/MacOSAcceptancePublicSummary_latest.json",
        "docs/evidence/MacOSAcceptancePublicSummary_latest.md",
    ):
        text = (PROJECT_ROOT / relative).read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "/Applications/" not in text
        assert "Google Chrome.app" not in text
        assert "Contents/MacOS" not in text
        assert ".png" not in text
        assert ".log" not in text
        assert "Process id" not in text
        assert "opened=/" not in text


def test_public_acceptance_summary_redacts_local_runtime_and_ui_evidence(tmp_path: Path) -> None:
    runtime = tmp_path / "MacOSRuntimeAcceptance_latest.json"
    ui = tmp_path / "UIVisualAcceptance_latest.json"
    runtime.write_text(
        json.dumps(
            {
                "schema": "EVAOSMacOSRuntimeAcceptanceV1",
                "status": "Pass",
                "generated_at": "2026-06-16T18:59:28",
                "project_root": "/Users/linzezhang/private/EVA_OS",
                "summary": {"pass": 10, "fail": 0, "info": 0, "total": 10},
                "started_by_acceptance": True,
                "launch_method": "app",
                "checks": [
                    {"check": "AppOpenLaunched", "status": "Pass", "evidence": "opened=/Users/linzezhang/Downloads/EVA_OS.app"},
                    {"check": "HealthAfterStart", "status": "Pass", "evidence": "healthy_ports=[8501]"},
                    {"check": "CleanCacheRefusesWhileRunning", "status": "Pass", "evidence": "pid 12345"},
                    {"check": "HealthAfterStop", "status": "Pass", "evidence": "healthy_ports=[]"},
                    {"check": "CleanCacheDryRunAfterStop", "status": "Pass", "evidence": "candidates=0"},
                ],
                "outputs": {"latest_json": "/Users/linzezhang/private/EVA_OS/data/systemAudit/MacOSRuntimeAcceptance_latest.json"},
            }
        ),
        encoding="utf-8",
    )
    ui.write_text(
        json.dumps(
            {
                "schema": "EVAOSUIVisualAcceptanceV1",
                "status": "Pass",
                "generated_at": "2026-06-17T08:12:44Z",
                "summary": {"pass": 16, "fail": 0, "info": 0, "total": 16},
                "started_by_acceptance": True,
                "checks": [
                    {"name": "VisibleText:EVA_OS", "status": "Pass", "evidence": "EVA_OS"},
                    {"name": "VisibleText:macOS 生命周期", "status": "Pass", "evidence": "macOS 生命周期"},
                    {"name": "VisibleText:运行时验收证据", "status": "Pass", "evidence": "运行时验收证据"},
                    {"name": "LifecycleButton:开发检查", "status": "Pass", "evidence": "开发检查"},
                    {"name": "LifecycleButton:轻量验收", "status": "Pass", "evidence": "轻量验收"},
                    {"name": "LifecycleButton:生命周期验收", "status": "Pass", "evidence": "生命周期验收"},
                    {"name": "NoVisibleError:Traceback", "status": "Pass", "evidence": "Traceback"},
                    {"name": "NoVisibleError:ModuleNotFoundError", "status": "Pass", "evidence": "ModuleNotFoundError"},
                    {"name": "NoVisibleError:ImportError:", "status": "Pass", "evidence": "ImportError:"},
                    {"name": "NoVisibleError:Connection lost", "status": "Pass", "evidence": "Connection lost"},
                    {"name": "ScreenshotCaptured", "status": "Pass", "evidence": "bytes=278744"},
                ],
                "outputs": {"screenshot": "/Users/linzezhang/private/EVA_OS/data/systemAudit/UIVisualAcceptance.png"},
                "browser": {"executable": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"},
                "visual_metrics": {"screenshot_bytes": 278744, "viewport": "1440x1000"},
            }
        ),
        encoding="utf-8",
    )

    payload = build_macos_public_acceptance_summary(
        project_root=tmp_path,
        runtime_evidence=runtime,
        ui_evidence=ui,
    )
    rendered = json.dumps(payload, ensure_ascii=False)
    markdown = macos_public_acceptance_markdown(payload)

    assert payload["schema"] == "EVAOSMacOSPublicAcceptanceSummaryV1"
    assert payload["status"] == "Pass"
    assert payload["summary"]["sources_pass"] == 2
    assert all(row["status"] == "Pass" for row in payload["coverage"])
    assert "/Users/" not in rendered
    assert "/Applications/" not in rendered
    assert "Google Chrome.app" not in rendered
    assert ".png" not in rendered
    assert "pid 12345" not in rendered
    assert "/Users/" not in markdown
    assert "Google Chrome.app" not in markdown


def test_write_public_acceptance_summary_creates_json_and_markdown(tmp_path: Path) -> None:
    system_audit = tmp_path / "data" / "systemAudit"
    system_audit.mkdir(parents=True)
    (system_audit / "MacOSRuntimeAcceptance_latest.json").write_text(
        json.dumps(
            {
                "schema": "EVAOSMacOSRuntimeAcceptanceV1",
                "status": "Pass",
                "summary": {"pass": 5, "fail": 0, "info": 0, "total": 5},
                "checks": [
                    {"check": "AppOpenLaunched", "status": "Pass"},
                    {"check": "HealthAfterStart", "status": "Pass"},
                    {"check": "CleanCacheRefusesWhileRunning", "status": "Pass"},
                    {"check": "HealthAfterStop", "status": "Pass"},
                    {"check": "CleanCacheDryRunAfterStop", "status": "Pass"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (system_audit / "UIVisualAcceptance_latest.json").write_text(
        json.dumps(
            {
                "schema": "EVAOSUIVisualAcceptanceV1",
                "status": "Pass",
                "summary": {"pass": 6, "fail": 0, "info": 0, "total": 6},
                "checks": [
                    {"name": "VisibleText:EVA_OS", "status": "Pass"},
                    {"name": "VisibleText:macOS 生命周期", "status": "Pass"},
                    {"name": "VisibleText:运行时验收证据", "status": "Pass"},
                    {"name": "LifecycleButton:开发检查", "status": "Pass"},
                    {"name": "LifecycleButton:轻量验收", "status": "Pass"},
                    {"name": "LifecycleButton:生命周期验收", "status": "Pass"},
                    {"name": "NoVisibleError:Traceback", "status": "Pass"},
                    {"name": "NoVisibleError:ModuleNotFoundError", "status": "Pass"},
                    {"name": "NoVisibleError:ImportError:", "status": "Pass"},
                    {"name": "NoVisibleError:Connection lost", "status": "Pass"},
                    {"name": "ScreenshotCaptured", "status": "Pass"},
                ],
                "visual_metrics": {"screenshot_bytes": 10001},
            }
        ),
        encoding="utf-8",
    )

    payload = write_macos_public_acceptance_summary(project_root=tmp_path, output_dir=tmp_path / "docs" / "evidence")

    assert Path(tmp_path / payload["outputs"]["latest_json"]).exists()
    assert Path(tmp_path / payload["outputs"]["latest_markdown"]).exists()
    assert "docs/evidence/" in payload["outputs"]["latest_json"]
