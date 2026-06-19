from __future__ import annotations

import os
import plistlib
from pathlib import Path

from quantlab.system.macos_acceptance import AppTarget, build_macos_app_acceptance_lite, write_macos_app_acceptance_lite


def test_macos_app_acceptance_lite_passes_fixture_apps_without_heavy_smoke(tmp_path: Path) -> None:
    app_paths = _fixture_apps(tmp_path)

    payload = build_macos_app_acceptance_lite(
        project_root=tmp_path,
        app_targets=tuple(AppTarget(label, path, requires_binding=label != "Source Template") for label, path in app_paths.items()),
        skip_codesign=True,
        run_dry_run=False,
        run_status_script=False,
    )

    assert payload["schema"] == "EVAOSMacOSAppAcceptanceLiteV1"
    assert payload["status"] == "Pass"
    assert payload["summary"]["fail"] == 0
    assert payload["target_count"] == 4
    assert "finalAcceptanceCheck.sh" in payload["heavy_smoke_policy"]
    assert "ciSmoke.sh" in payload["heavy_smoke_policy"]
    assert "does not start the app" in payload["safety_boundary"]
    assert any(row["check"] == "ProjectBinding" and row["status"] == "Pass" for row in payload["checks"])
    assert all("github.com/LinzeColin/EVA_OS" not in row["evidence"] for row in payload["checks"])


def test_macos_app_acceptance_lite_blocks_missing_project_binding(tmp_path: Path) -> None:
    app_paths = _fixture_apps(tmp_path)
    (app_paths["Desktop"] / "Contents" / "Resources" / "EVA_OS_PROJECT_ROOT").unlink()

    payload = build_macos_app_acceptance_lite(
        project_root=tmp_path,
        app_targets=tuple(AppTarget(label, path, requires_binding=label != "Source Template") for label, path in app_paths.items()),
        skip_codesign=True,
        run_dry_run=False,
        run_status_script=False,
    )

    assert payload["status"] == "Blocked"
    assert any(row["target"] == "Desktop" and row["check"] == "ProjectBinding" and row["status"] == "Fail" for row in payload["checks"])
    assert "installEVAOSEntryApps.sh" in payload["next_action"]


def test_write_macos_app_acceptance_lite_outputs_json_and_latest(tmp_path: Path) -> None:
    app_paths = _fixture_apps(tmp_path)
    output_dir = tmp_path / "acceptance"

    payload = write_macos_app_acceptance_lite(
        project_root=tmp_path,
        output_dir=output_dir,
        app_targets=tuple(AppTarget(label, path, requires_binding=label != "Source Template") for label, path in app_paths.items()),
        skip_codesign=True,
        run_dry_run=False,
        run_status_script=False,
    )

    assert Path(payload["outputs"]["json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).exists()
    assert Path(payload["outputs"]["latest_json"]).name == "MacOSAppAcceptanceLite_latest.json"


def _fixture_apps(root: Path) -> dict[str, Path]:
    (root / "StartQuantLab.command").write_text("#!/usr/bin/env zsh\nexit 0\n", encoding="utf-8")
    os.chmod(root / "StartQuantLab.command", 0o755)
    scripts = root / "scripts"
    scripts.mkdir()
    (scripts / "statusQuantLab.sh").write_text("#!/usr/bin/env zsh\necho 'QuantLab is not running on ports 8501-8510.'\n", encoding="utf-8")
    os.chmod(scripts / "statusQuantLab.sh", 0o755)
    app_paths = {
        "Source Template": root / "macos" / "EVA_OS.app",
        "Desktop": root / "Desktop" / "EVA_OS.app",
        "Downloads": root / "Downloads" / "EVA_OS.app",
        "Applications": root / "Applications" / "EVA_OS.app",
    }
    for label, app in app_paths.items():
        _write_app(app, root, write_binding=label != "Source Template")
    return app_paths


def _write_app(app: Path, root: Path, *, write_binding: bool) -> None:
    macos = app / "Contents" / "MacOS"
    resources = app / "Contents" / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)
    (macos / "EVA_OS").write_text("#!/usr/bin/env zsh\necho 'EVA_OS_APP_LAUNCH: project=/tmp command=./StartQuantLab.command mode=open-command'\n", encoding="utf-8")
    os.chmod(macos / "EVA_OS", 0o755)
    if write_binding:
        (resources / "EVA_OS_PROJECT_ROOT").write_text(str(root), encoding="utf-8")
    with (app / "Contents" / "Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "CFBundleDisplayName": "EVA_OS",
                "CFBundleExecutable": "EVA_OS",
                "CFBundleIdentifier": "com.linze.eva-os",
            },
            handle,
        )
