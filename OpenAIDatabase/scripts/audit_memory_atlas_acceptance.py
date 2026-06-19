#!/usr/bin/env python3
"""Audit Memory Atlas acceptance criteria across source, build, and local app state."""

from __future__ import annotations

import argparse
import json
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_memory_atlas_release import AuditError as ReleaseAuditError  # noqa: E402
from audit_memory_atlas_release import audit_memory_atlas_json, audit_release, audit_tracked_files  # noqa: E402
from audit_memory_atlas_visual_acceptance import (  # noqa: E402
    VisualAcceptanceError,
    audit_visual_acceptance,
)
from preflight_cloudflare_pages_access import PreflightError, preflight as cloudflare_preflight  # noqa: E402


class AcceptanceError(RuntimeError):
    pass


def pass_check(checks: list[dict[str, str]], name: str, evidence: str) -> None:
    checks.append({"name": name, "status": "PASS", "evidence": evidence})


def fail_check(checks: list[dict[str, str]], name: str, evidence: str) -> None:
    checks.append({"name": name, "status": "FAIL", "evidence": evidence})


def require(checks: list[dict[str, str]], condition: bool, name: str, evidence: str, failure: str) -> None:
    if condition:
        pass_check(checks, name, evidence)
    else:
        fail_check(checks, name, failure)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def recommendation_item_ready(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    required_text_fields = ["id", "title", "statement", "source", "confidence", "importance", "reason"]
    return (
        all(isinstance(item.get(field), str) and item.get(field).strip() for field in required_text_fields)
        and isinstance(item.get("evidence_count"), int)
        and item.get("evidence_count", 0) > 0
        and item.get("confidence") in {"high", "medium", "low"}
        and item.get("importance") in {"高", "中", "低"}
    )


def recommendation_bucket_ready(bucket: Any) -> bool:
    if not isinstance(bucket, dict):
        return False
    if not all(isinstance(bucket.get(key), list) for key in ["current", "added", "modified", "deleted"]):
        return False
    if len(bucket.get("current", [])) < 1:
        return False
    if not all(recommendation_item_ready(item) for item in bucket.get("current", [])):
        return False
    modified = bucket.get("modified", [])
    return all(
        isinstance(item, dict)
        and recommendation_item_ready(item.get("before"))
        and recommendation_item_ready(item.get("after"))
        for item in modified
    )


def data_source_registry_ready(registry: Any, atlas: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(registry, dict):
        return False, "registry is not a JSON object"
    sources = registry.get("sources")
    if registry.get("schema_version") != "memory_atlas_data_source_registry.v1" or not isinstance(sources, list):
        return False, "registry schema_version or sources list is invalid"
    source_map = {source.get("id"): source for source in sources if isinstance(source, dict)}
    required_status = {
        "memory_atlas": "active",
        "codex": "active",
        "wechat": "planned",
        "xiaohongshu": "planned",
        "douyin": "planned",
    }
    missing = [source_id for source_id in required_status if source_id not in source_map]
    if missing:
        return False, f"missing registered sources: {missing}"
    wrong_status = [
        source_id
        for source_id, status in required_status.items()
        if source_map.get(source_id, {}).get("status") != status
    ]
    if wrong_status:
        return False, f"registered source statuses are wrong: {wrong_status}"
    canonical = registry.get("canonical_event_contract", {})
    required_fields = canonical.get("required_fields") if isinstance(canonical, dict) else []
    for field in ["source_id", "record_id", "occurred_at", "record_type", "summary", "sensitivity", "dedupe_key"]:
        if field not in required_fields:
            return False, f"canonical required field missing: {field}"
    for source_id in ["wechat", "xiaohongshu", "douyin"]:
        source = source_map[source_id]
        if source.get("ingestion_status") != "planned_no_real_data":
            return False, f"{source_id} should be planned_no_real_data until real ingestion exists"
        raw_policy = str(source.get("raw_payload_policy") or "")
        if "plaintext" not in raw_policy or "no_" not in raw_policy:
            return False, f"{source_id} raw_payload_policy does not fail closed"

    atlas_sources = atlas.get("data_sources", [])
    atlas_source_map = {source.get("id"): source for source in atlas_sources if isinstance(source, dict)}
    visible_source_ids = [source.get("id") for source in atlas_sources if isinstance(source, dict)]
    if visible_source_ids != ["all", "memory_atlas", "codex"]:
        return False, f"homepage data_sources must be exactly all/memory_atlas/codex, got: {visible_source_ids}"
    expected_labels = {"all": "总数据源", "memory_atlas": "ChatGPT", "codex": "Codex"}
    wrong_labels = [
        source_id
        for source_id, label in expected_labels.items()
        if atlas_source_map.get(source_id, {}).get("label") != label
    ]
    if wrong_labels:
        return False, f"homepage data source labels are wrong: {wrong_labels}"
    for source_id in ["all", "memory_atlas", "codex"]:
        if source_id not in atlas_source_map:
            return False, f"Atlas data_sources missing {source_id}"
    for source_id in ["wechat", "xiaohongshu", "douyin"]:
        if source_id in atlas_source_map:
            return False, f"{source_id} must remain registry-only until the homepage selector is explicitly expanded"

    registry_contract = atlas.get("source_contract", {}).get("data_source_registry", {})
    planned_ids = set(registry_contract.get("planned_source_ids", [])) if isinstance(registry_contract, dict) else set()
    if not {"wechat", "xiaohongshu", "douyin"}.issubset(planned_ids):
        return False, "Atlas source_contract does not expose planned future source IDs"
    if "fake" not in str(registry_contract.get("mock_policy") or ""):
        return False, "Atlas source_contract does not carry the no-fake-source policy"
    return True, "homepage selector exposes only total/ChatGPT/Codex while registry keeps planned future sources without mock data"


def current_git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def audit_acceptance(repo_root: Path, publish_dir: Path | None = None, require_local_apps: bool = False) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checks: list[dict[str, str]] = []

    required_paths = [
        "AGENTS.md",
        "README.md",
        "docs/MEMORY_ATLAS_DEPLOYMENT.md",
        "docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md",
        "docs/MEMORY_ATLAS_COMPETITOR_ARCHITECTURE_MATRIX.md",
        "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
        "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
        "docs/USER_REQUIREMENTS.md",
        "config/data_sources/source_registry.json",
        "config/cloudflare/pages_direct_upload.template.json",
        "config/cloudflare/access_self_hosted_application.template.json",
        "wrangler.jsonc",
        ".github/workflows/ci.yml",
        "scripts/build_memory_atlas_data.py",
        "scripts/build_agent_context_pack.py",
        "scripts/sync_codex_memory_data.py",
        "scripts/install_codex_weekly_sync.py",
        "scripts/audit_memory_atlas_release.py",
        "scripts/audit_memory_atlas_visual_acceptance.py",
        "scripts/audit_memory_atlas_goal_completion.py",
        "scripts/deploy_memory_atlas_cloudflare.py",
        "scripts/install_memory_atlas_app.py",
        "scripts/preflight_cloudflare_pages_access.py",
        "apps/memory-atlas/index.html",
        "apps/memory-atlas/package.json",
        "apps/memory-atlas/vite.config.ts",
        "apps/memory-atlas/src/App.tsx",
        "apps/memory-atlas/src/components/GalaxyScene.tsx",
        "apps/memory-atlas/src/data/atlas.ts",
        "data/derived/agent_context/agent_context_pack.json",
        "data/derived/agent_context/AGENT_CONTEXT.md",
        "data/derived/visualization/memory_atlas.json",
    ]
    missing = [relative for relative in required_paths if not (repo_root / relative).exists()]
    require(checks, not missing, "required_files_present", f"{len(required_paths)} files present", f"missing files: {missing}")

    tracked_problems = audit_tracked_files(repo_root)
    require(checks, not tracked_problems, "tracked_file_safety", "no tracked raw exports, app bundles, env/key files, cookies, sessions, or auth files", "\n".join(tracked_problems))

    atlas_path = repo_root / "data/derived/visualization/memory_atlas.json"
    atlas = load_json(atlas_path)
    codex_snapshot_path = repo_root / "data/processed/codex/codex_activity_snapshot.json"
    agent_context_path = repo_root / "data/derived/agent_context/agent_context_pack.json"
    data_source_registry_path = repo_root / "config/data_sources/source_registry.json"
    codex_snapshot = load_json(codex_snapshot_path) if codex_snapshot_path.exists() else {}
    agent_context = load_json(agent_context_path) if agent_context_path.exists() else {}
    data_source_registry = load_json(data_source_registry_path) if data_source_registry_path.exists() else {}
    recommendations = atlas.get("agent_recommendations", {})
    atlas_problems: list[str] = []
    audit_memory_atlas_json(atlas_path, atlas_problems)
    require(checks, not atlas_problems, "redacted_atlas_contract", "memory_atlas.json passes release JSON contract", "\n".join(atlas_problems))
    source_contract = atlas.get("source_contract", {})
    writeback_policy = source_contract.get("writeback_policy", {})
    registry_ok, registry_evidence = data_source_registry_ready(data_source_registry, atlas)
    require(
        checks,
        registry_ok,
        "multi_source_registry_ready",
        registry_evidence,
        registry_evidence,
    )
    require(
        checks,
        codex_snapshot.get("schema_version") == "codex_activity_snapshot.v1"
        and codex_snapshot.get("source") == "real_codex_local_data"
        and int(codex_snapshot.get("session_count") or 0) > 0
        and int(codex_snapshot.get("message_count") or 0) > 0
        and int(codex_snapshot.get("tool_call_count") or 0) > 0
        and atlas.get("overview", {}).get("codex_session_count") == codex_snapshot.get("session_count")
        and recommendations.get("session_count") == codex_snapshot.get("session_count")
        and recommendations.get("source") == "real_codex_local_sessions_redacted_summary",
        "real_codex_snapshot_not_mock",
        "Atlas and recommendations are backed by non-empty real local Codex activity snapshot",
        "Codex snapshot is missing, empty, mock-like, or not aligned with Atlas/recommendations",
    )
    require(
        checks,
        recommendations.get("schema_version") == "codex_agent_recommendations.v1"
        and isinstance(recommendations.get("generated_at"), str)
        and isinstance(recommendations.get("top_topics"), list)
        and len(recommendations.get("top_topics", [])) >= 3
        and all(
            isinstance(topic, dict)
            and isinstance(topic.get("label"), str)
            and topic.get("label", "").strip()
            and isinstance(topic.get("count"), int)
            and topic.get("count", 0) > 0
            for topic in recommendations.get("top_topics", [])[:3]
        )
        and recommendation_bucket_ready(recommendations.get("memory"))
        and recommendation_bucket_ready(recommendations.get("meta_data")),
        "agent_ready_personalization_contract",
        "Memory and Meta Data recommendation buckets contain current/changed agent-ready personalization records",
        "Agent recommendations are missing required Memory/Meta Data current records, changes, source, confidence, evidence, or topics",
    )
    require(
        checks,
        agent_context.get("schema_version") == "agent_context_pack.v1"
        and agent_context.get("generated_at") == recommendations.get("generated_at")
        and agent_context.get("behavior", {}).get("source") == "real_codex_local_data"
        and agent_context.get("behavior", {}).get("session_count") == codex_snapshot.get("session_count")
        and agent_context.get("behavior", {}).get("message_count") == codex_snapshot.get("message_count")
        and agent_context.get("behavior", {}).get("tool_call_count") == codex_snapshot.get("tool_call_count")
        and isinstance(agent_context.get("read_order"), list)
        and "data/derived/agent_context/AGENT_CONTEXT.md" in agent_context.get("read_order", [])
        and len(agent_context.get("profile", {}).get("core_profile_items", [])) >= 1
        and recommendation_bucket_ready({"current": agent_context.get("memory", {}).get("current", []), "added": [], "modified": [], "deleted": []})
        and recommendation_bucket_ready({"current": agent_context.get("meta_data", {}).get("current", []), "added": [], "modified": [], "deleted": []})
        and agent_context.get("safety", {}).get("raw_transcripts_included") is False
        and agent_context.get("safety", {}).get("plaintext_high_risk_secrets_included") is False
        and agent_context.get("safety", {}).get("local_absolute_paths_included") is False,
        "fixed_agent_context_pack_ready",
        "Fixed-path Agent Context Pack exposes profile, memory, preferences, metadata, behavior, and safety fields",
        "Fixed-path Agent Context Pack is missing, stale, unsafe, or not aligned with real Codex snapshot/recommendations",
    )
    require(
        checks,
        atlas.get("visual_layers", {}).get("primary") == "galaxy"
        and set(atlas.get("visual_layers", {}).get("secondary", []))
        >= {"notion_map", "roi_dashboard", "obsidian_graph", "timeline", "contribution_grid", "summary_iteration"},
        "visual_layers_declared",
        "galaxy primary plus Notion/ROI/Obsidian/timeline/contribution/summary secondary layers",
        "visual_layers missing required modes",
    )
    require(
        checks,
        writeback_policy.get("frontend_can_request_writeback") is True
        and writeback_policy.get("writeback_must_use_proposals") is True
        and writeback_policy.get("direct_frontend_mutation_of_active_memory") is False
        and "conflict_detection" in writeback_policy,
        "writeback_proposal_only",
        "frontend can create proposals; direct active-memory mutation is disabled; conflict detection is delegated",
        "writeback policy does not enforce proposal-only flow",
    )

    vite_config = read_text(repo_root / "apps/memory-atlas/vite.config.ts")
    atlas_loader = read_text(repo_root / "apps/memory-atlas/src/data/atlas.ts")
    app_source = read_text(repo_root / "apps/memory-atlas/src/App.tsx")
    galaxy_source = read_text(repo_root / "apps/memory-atlas/src/components/GalaxyScene.tsx")
    index_html = read_text(repo_root / "apps/memory-atlas/index.html")
    installer_source = read_text(repo_root / "scripts/install_memory_atlas_app.py")
    codex_sync_source = read_text(repo_root / "scripts/sync_codex_memory_data.py")
    codex_weekly_source = read_text(repo_root / "scripts/install_codex_weekly_sync.py")
    deployment_doc = read_text(repo_root / "docs/MEMORY_ATLAS_DEPLOYMENT.md")
    model_parameters_doc = read_text(repo_root / "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")
    delivery_record_doc = read_text(repo_root / "docs/MEMORY_ATLAS_DELIVERY_RECORD.md")
    ci_workflow = read_text(repo_root / ".github/workflows/ci.yml")

    require(
        checks,
        'new URL("/memory_atlas.json", window.location.origin)' in atlas_loader
        and 'url.searchParams.set("snapshot", String(Date.now()))' in atlas_loader
        and 'cache: "no-store"' in atlas_loader
        and '"Cache-Control": "no-cache"' in atlas_loader
        and "memory_atlas.json" not in app_source
        and "publicDir: atlasDataDir" in vite_config,
        "runtime_atlas_fetch",
        "frontend loads a cache-busted /memory_atlas.json at runtime through Vite publicDir",
        "frontend may not be using runtime redacted snapshot fetch",
    )
    require(
        checks,
        "sourcemap: process.env.VITE_SOURCEMAP === \"1\"" in vite_config,
        "production_sourcemap_disabled_by_default",
        "sourcemaps require explicit VITE_SOURCEMAP=1",
        "production sourcemap default is not locked down",
    )
    require(
        checks,
        'lang="zh-CN"' in index_html
        and "<title>记忆星图</title>" in index_html
        and 'lang="zh-CN"' in installer_source
        and "记忆星图启动中" in installer_source
        and "个节点 /" in app_source
        and "个事件 ·" in app_source
        and "change proposal" not in app_source
        and "versioned proposal" not in app_source
        and "active memory" not in app_source,
        "chinese_user_facing_ui",
        "app shell, startup page, stats, and writeback explanation are Chinese-first",
        "found English user-facing text in core UI surfaces",
    )
    require(
        checks,
        "模型假设" in model_parameters_doc
        and "输入" in model_parameters_doc
        and "输出" in model_parameters_doc
        and "参数与阈值" in model_parameters_doc
        and "activity_score.v2" in model_parameters_doc
        and "leverage_score" in model_parameters_doc
        and "情绪分" in model_parameters_doc
        and "当前未实现" in model_parameters_doc
        and "交付运行方式" in delivery_record_doc
        and "验收标准" in delivery_record_doc
        and "历史过程记录" in delivery_record_doc
        and "待开发清单" in delivery_record_doc,
        "model_parameters_and_delivery_record_ready",
        "Model parameters and delivery record distinguish formulas/thresholds from feature logs and keep run/acceptance/history readable",
        "Model parameter or delivery record docs are missing assumptions, inputs, outputs, formulas, thresholds, delivery mode, acceptance, or history",
    )
    require(
        checks,
        'import {\n  AdditiveBlending' in galaxy_source
        and 'from "three"' in galaxy_source
        and '{renderError ? <canvas className="nebula-canvas"' in galaxy_source
        and 'aria-label="可点击记忆星体层"' in galaxy_source
        and '"未选择"' in galaxy_source,
        "galaxy_threejs_and_clean_fallback",
        "Galaxy uses Three.js, keeps fallback canvas error-gated, and keeps point labels simple",
        "Galaxy source does not match the expected WebGL/fallback/label contract",
    )
    require(
        checks,
        "const daysInYear = isLeapYear(year) ? 366 : 365" in app_source
        and "const weekColumns = Math.ceil((daysInYear + startWeekday) / 7)" in app_source
        and "Array.from({ length: daysInYear }" in app_source
        and "Array.from({ length: 24 }" in app_source
        and 'className="year-trend-grid vertical-year-trend"' in app_source
        and "startColumn" not in app_source
        and '(["day", "week", "month", "year"] as ContributionScale[])' in app_source,
        "contribution_grid_time_scales",
        "day/week use 365/366 daily cells; month uses 24 two-year columns; year uses vertically stacked comparison cards",
        "contribution grid time-scale requirements are not represented in source",
    )
    require(
        checks,
        "分析对象" in app_source
        and "AgentRecommendationsPanel" in app_source
        and "Memory（给 ChatGPT / Codex Personalization）" in app_source
        and "Meta Data（给 ChatGPT / Codex Agents.md）" in app_source
        and "calendarWeekKey(year, weekColumn)" in app_source
        and "contributionYears(atlas, nodes)" in app_source,
        "codex_source_recommendations_and_grid_controls",
        "UI includes source selection, Memory/Meta Data recommendations, natural week keys, and year picker",
        "Source selection, recommendation panels, natural week keys, or year picker are missing",
    )
    require(
        checks,
        "real local Codex session logs" in codex_sync_source
        and "redacted_summary_only_no_raw_transcript_no_plaintext_secret" in codex_sync_source
        and "OpenAIDatabase" in codex_sync_source
        and "--build-atlas" in codex_weekly_source
        and "--commit" in codex_weekly_source
        and "--push" in codex_weekly_source
        and "StartCalendarInterval" in codex_weekly_source,
        "real_codex_weekly_sync_ready",
        "Real Codex redacted sync and weekly GitHub backup LaunchAgent are present",
        "Codex sync or weekly backup launcher does not meet the real-data redacted backup contract",
    )
    try:
        visual_result = audit_visual_acceptance(repo_root)
    except VisualAcceptanceError as exc:
        fail_check(checks, "memory_atlas_visual_acceptance", str(exc))
    else:
        pass_check(checks, "memory_atlas_visual_acceptance", f"{len(visual_result['checks'])} visual acceptance checks passed")
    require(
        checks,
        "Cloudflare Pages + Access" in deployment_doc
        and "Zero Trust Access" in deployment_doc
        and "MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md" in deployment_doc
        and "Build output directory: apps/memory-atlas/dist" in deployment_doc
        and load_json(repo_root / "wrangler.jsonc").get("pages_build_output_dir") == "apps/memory-atlas/dist",
        "cloudflare_pages_access_ready",
        "wrangler config and deployment docs cover Pages + Access",
        "Cloudflare Pages + Access readiness docs/config missing",
    )
    try:
        preflight_result = cloudflare_preflight(repo_root, publish_dir)
    except PreflightError as exc:
        fail_check(checks, "cloudflare_pages_access_preflight", str(exc))
    else:
        pass_check(checks, "cloudflare_pages_access_preflight", f"{len(preflight_result['checks'])} Cloudflare preflight checks passed")
    require(
        checks,
        "scripts/audit_memory_atlas_acceptance.py" in ci_workflow
        and "scripts/audit_memory_atlas_visual_acceptance.py" in ci_workflow
        and "scripts/audit_memory_atlas_goal_completion.py" in ci_workflow
        and "scripts/deploy_memory_atlas_cloudflare.py" in ci_workflow
        and "scripts/preflight_cloudflare_pages_access.py" in ci_workflow
        and "scripts/audit_memory_atlas_release.py" in ci_workflow
        and "scripts/sync_codex_memory_data.py" in ci_workflow
        and "scripts/build_agent_context_pack.py" in ci_workflow
        and "scripts/install_codex_weekly_sync.py" in ci_workflow
        and "npm run build --prefix apps/memory-atlas" in ci_workflow,
        "ci_acceptance_gate",
        "CI builds data/frontend and runs release, acceptance, and Cloudflare preflight audits",
        "CI does not include the Memory Atlas acceptance gate",
    )
    require(
        checks,
        "default_targets" in installer_source
        and "Downloads" in installer_source
        and "/Applications" in installer_source
        and "create_app_icon" in installer_source
        and "CFBundleIconFile" in installer_source
        and "Memory Atlas macOS app icon was not created" in installer_source
        and "memory_atlas_build.json" in installer_source
        and "runtime_is_stale" in installer_source
        and "local static runtime build manifest matches current git HEAD" in read_text(repo_root / "scripts/audit_memory_atlas_acceptance.py")
        and "def remove_tree" in installer_source
        and "clean_frontend_dependencies" in installer_source
        and "clean_frontend_build_cache" in installer_source
        and "构建缓存清理失败" in installer_source
        and "Application Support/OpenAIDatabase/MemoryAtlas" in installer_source
        and "scripts/audit_memory_atlas_release.py" in installer_source
        and "request_shutdown" in installer_source
        and "release_requested" in installer_source
        and "active_thread_count" in installer_source
        and "allow_reuse_address = True" in installer_source
        and '"-m http.server"' in installer_source
        and "last_seen_at = time.time() - max" not in installer_source,
        "local_app_launcher_contract",
        "installer creates Downloads/Applications launchers, custom icon, runtime cache manifest/stale checks, cleanup guard, release audit gate, and immediate tab-close shutdown",
        "local app launcher contract missing required pieces",
    )

    if publish_dir is not None:
        try:
            release_result = audit_release(repo_root, publish_dir)
        except ReleaseAuditError as exc:
            fail_check(checks, "publish_dir_release_safe", str(exc))
        else:
            pass_check(checks, "publish_dir_release_safe", f"{release_result['file_count']} publish files audited")

    if require_local_apps:
        audit_local_apps(repo_root, checks)

    failed = [check for check in checks if check["status"] != "PASS"]
    if failed:
        raise AcceptanceError(json.dumps({"status": "FAIL", "checks": checks}, ensure_ascii=False, indent=2))
    return {"status": "PASS", "checks": checks}


def audit_local_apps(repo_root: Path, checks: list[dict[str, str]]) -> None:
    targets = [Path.home() / "Downloads/Memory Atlas.app", Path("/Applications/Memory Atlas.app")]
    missing = [str(path) for path in targets if not path.exists()]
    require(checks, not missing, "local_app_bundles_present", "Downloads and /Applications app bundles exist", f"missing app bundles: {missing}")

    for target in targets:
        executable = target / "Contents/MacOS/memory-atlas-launcher"
        info_plist = target / "Contents/Info.plist"
        launcher_ok = executable.exists() and executable.stat().st_mode & 0o111
        if launcher_ok:
            launcher_text = read_text(executable)
            launcher_ok = "记忆星图启动中" in launcher_text and "scripts/audit_memory_atlas_release.py" in launcher_text
        plist_ok = False
        if info_plist.exists():
            with info_plist.open("rb") as handle:
                plist = plistlib.load(handle)
            plist_ok = (
                plist.get("CFBundleName") == "Memory Atlas"
                and plist.get("CFBundleExecutable") == "memory-atlas-launcher"
                and plist.get("CFBundleIconFile") == "MemoryAtlas"
                and str(plist.get("CFBundleVersion", "")).isdigit()
                and "脱敏可视化快照" in plist.get("NSDocumentsFolderUsageDescription", "")
            )
        icon_path = target / "Contents/Resources/MemoryAtlas.icns"
        icon_ok = icon_path.exists() and icon_path.stat().st_size > 1024
        require(
            checks,
            launcher_ok and plist_ok and icon_ok,
            f"local_app_bundle_valid:{target}",
            "launcher executable, icon plist/file, Chinese startup page, and release audit gate are present",
            f"invalid app bundle: {target}",
        )

    runtime_dir = Path.home() / "Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime"
    try:
        release_result = audit_release(repo_root, runtime_dir)
    except ReleaseAuditError as exc:
        fail_check(checks, "local_runtime_release_safe", str(exc))
    else:
        pass_check(checks, "local_runtime_release_safe", f"{release_result['file_count']} runtime files audited")
    build_info_path = runtime_dir / "memory_atlas_build.json"
    build_info_ok = False
    if build_info_path.exists():
        try:
            build_info = load_json(build_info_path)
        except json.JSONDecodeError:
            build_info = {}
        current_commit = current_git_commit(repo_root)
        build_info_ok = (
            build_info.get("schema_version") == "memory_atlas_build.v1"
            and bool(build_info.get("git_commit"))
            and (current_commit is None or build_info.get("git_commit") == current_commit)
        )
    require(
        checks,
        build_info_ok,
        "local_runtime_matches_current_git",
        "local static runtime build manifest matches current git HEAD",
        "local static runtime is missing build info or does not match current git HEAD",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas acceptance criteria.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--publish-dir", type=Path)
    parser.add_argument("--require-local-apps", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = audit_acceptance(args.repo_root, args.publish_dir, args.require_local_apps)
    except AcceptanceError as exc:
        print(exc)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
