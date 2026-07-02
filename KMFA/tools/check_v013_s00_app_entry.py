#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path


APP_PATH = Path("/Users/linzezhang/Downloads/KMFA.app")
PROJECT_ROOT = Path("/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa")
TARGET_HTML_REL = Path("KMFA/stage_artifacts/S11_P1_home_navigation/exports/html/kmfa_home_navigation.html")
MANIFEST_PATH = PROJECT_ROOT / "KMFA/stage_artifacts/V013_S00_APP_ENTRY/machine/app_entry_manifest.json"


class ValidationError(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise ValidationError(f"manifest missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_app_entry(app_path: Path = APP_PATH, project_root: Path = PROJECT_ROOT, manifest_path: Path = MANIFEST_PATH) -> dict:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(app_path.exists() and app_path.is_dir(), f"app bundle missing: {app_path}")
    contents = app_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    info_plist = contents / "Info.plist"
    executable = macos / "KMFA"
    icon = resources / "KMFAAppIcon.icns"
    root_binding = resources / "KMFA_PROJECT_ROOT"
    target_binding = resources / "KMFA_TARGET_HTML"
    target_html = project_root / TARGET_HTML_REL

    require(info_plist.exists(), "Info.plist missing")
    require(executable.exists(), "launcher executable missing")
    require(os.access(executable, os.X_OK), "launcher executable is not executable")
    require(icon.exists(), "app icon missing")
    require(root_binding.exists(), "project root binding missing")
    require(target_binding.exists(), "target html binding missing")
    require(target_html.exists(), f"target HTML missing: {target_html}")

    plist = {}
    if info_plist.exists():
        try:
            plist = plistlib.loads(info_plist.read_bytes())
        except Exception as exc:  # pragma: no cover - surfaced through CLI output
            errors.append(f"Info.plist parse failed: {exc}")
    require(plist.get("CFBundleDisplayName") == "KMFA", "CFBundleDisplayName must be KMFA")
    require(plist.get("CFBundleExecutable") == "KMFA", "CFBundleExecutable must be KMFA")
    require(plist.get("CFBundleIconFile") == "KMFAAppIcon", "CFBundleIconFile must be KMFAAppIcon")
    require(plist.get("CFBundleIdentifier") == "com.linze.kmfa.launcher", "unexpected CFBundleIdentifier")

    if root_binding.exists():
        require(root_binding.read_text(encoding="utf-8").strip() == str(project_root), "project root binding is not canonical")
    if target_binding.exists():
        require(target_binding.read_text(encoding="utf-8").strip() == str(TARGET_HTML_REL), "target html binding mismatch")
    if icon.exists():
        require(icon.stat().st_size > 10_000, "icon file is too small to be a real icns")
        require(icon.read_bytes()[:4] == b"icns", "icon file does not have icns header")

    dry_run_stdout = ""
    if executable.exists() and os.access(executable, os.X_OK):
        result = subprocess.run(
            [str(executable)],
            cwd=str(project_root),
            env={**os.environ, "KMFA_APP_LAUNCH_DRY_RUN": "1"},
            text=True,
            capture_output=True,
            timeout=10,
        )
        dry_run_stdout = result.stdout.strip()
        require(result.returncode == 0, f"launcher dry-run failed: rc={result.returncode} stderr={result.stderr.strip()}")
        require("KMFA_APP_LAUNCH:" in dry_run_stdout, "launcher dry-run did not print launch marker")
        require(str(target_html) in dry_run_stdout, "launcher dry-run did not bind target HTML")

    manifest = {}
    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        errors.append(str(exc))
    if manifest:
        require(manifest.get("stage_phase") == "S00-P1", "manifest stage_phase must be S00-P1")
        require(manifest.get("app_path") == str(app_path), "manifest app path mismatch")
        require(manifest.get("project_root") == str(project_root), "manifest project root mismatch")
        require(manifest.get("target_html") == str(target_html), "manifest target html mismatch")
        require(manifest.get("delivery_allowed") is False, "manifest must keep delivery_allowed=false")
        require(manifest.get("formal_report_allowed") is False, "manifest must keep formal_report_allowed=false")
        require(manifest.get("github_upload_this_phase") is False, "manifest must not upload during this phase")
        if icon.exists():
            require(manifest.get("icon_sha256") == sha256_file(icon), "manifest icon sha mismatch")

    if errors:
        raise ValidationError("\n".join(errors))

    return {
        "app_path": str(app_path),
        "target_html": str(target_html),
        "icon_sha256": sha256_file(icon),
        "dry_run_stdout": dry_run_stdout,
        "manifest": str(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KMFA v0.1.3 Stage 0 Downloads app entry.")
    parser.add_argument("--app-path", type=Path, default=APP_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    try:
        result = validate_app_entry(args.app_path, args.project_root, args.manifest)
    except ValidationError as exc:
        print("FAIL: KMFA v0.1.3 S00 app entry validation failed")
        print(exc)
        return 1
    print(
        "PASS: KMFA v0.1.3 S00 app entry is installed "
        f"(app={result['app_path']}, target={result['target_html']}, icon={result['icon_sha256']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
