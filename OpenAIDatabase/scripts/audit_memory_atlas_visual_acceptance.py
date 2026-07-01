#!/usr/bin/env python3
"""Audit Memory Atlas visual acceptance contracts.

This is intentionally source-level and deterministic. Browser screenshot
capture can be unavailable or flaky in headless/local agent environments, so
these checks lock the implementation contracts that prevent the specific
visual regressions the user called out.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class VisualAcceptanceError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def pass_check(checks: list[dict[str, str]], name: str, evidence: str) -> None:
    checks.append({"name": name, "status": "PASS", "evidence": evidence})


def fail_check(checks: list[dict[str, str]], name: str, evidence: str) -> None:
    checks.append({"name": name, "status": "FAIL", "evidence": evidence})


def require(checks: list[dict[str, str]], condition: bool, name: str, evidence: str, failure: str) -> None:
    if condition:
        pass_check(checks, name, evidence)
    else:
        fail_check(checks, name, failure)


def function_block(source: str, function_name: str, next_function_name: str) -> str:
    pattern = rf"function {re.escape(function_name)}\("
    start_match = re.search(pattern, source)
    if not start_match:
        raise VisualAcceptanceError(f"missing function {function_name}")
    next_match = re.search(rf"\nfunction {re.escape(next_function_name)}\(", source[start_match.start() :])
    if not next_match:
        raise VisualAcceptanceError(f"missing function {next_function_name} after {function_name}")
    return source[start_match.start() : start_match.start() + next_match.start()]


def audit_visual_acceptance(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checks: list[dict[str, str]] = []

    app_source = read_text(repo_root / "apps/memory-atlas/src/App.tsx")
    galaxy_source = read_text(repo_root / "apps/memory-atlas/src/components/GalaxyScene.tsx")
    starfield_params_source = read_text(repo_root / "apps/memory-atlas/src/config/memoryStarfieldParameters.ts")
    obsidian_source = read_text(repo_root / "apps/memory-atlas/src/components/ObsidianGraphScene.tsx")
    visual_flags_source = read_text(repo_root / "apps/memory-atlas/src/config/visualFlags.ts")
    css_source = read_text(repo_root / "apps/memory-atlas/src/styles.css")
    model_params_source = read_text(repo_root / "config/visualization/model_parameters.memory_starfield.yaml")
    memory_river_params_source = read_text(repo_root / "config/visualization/model_parameters.memory_river.yaml")
    data_builder_source = read_text(repo_root / "scripts/build_memory_atlas_data.py")
    installer_source = read_text(repo_root / "scripts/install_memory_atlas_app.py")
    stage7_visual_source = read_text(repo_root / "apps/memory-atlas/scripts/validate_stage7_visual_acceptance.cjs")
    stage7_performance_source = read_text(repo_root / "apps/memory-atlas/scripts/validate_stage7_performance_acceptance.cjs")
    stage7_privacy_accessibility_source = read_text(repo_root / "apps/memory-atlas/scripts/validate_stage7_privacy_accessibility.cjs")
    readme = read_text(repo_root / "README.md")
    atlas_path = repo_root / "data/derived/visualization/memory_atlas.json"
    atlas_source = atlas_path.read_text(encoding="utf-8") if atlas_path.exists() else ""

    data_guide_node = function_block(app_source, "DataGuideSvgNode", "buildFilteredSlice")
    timeline_view = function_block(app_source, "TimelineView", "ContributionGrid")
    contribution_grid = function_block(app_source, "ContributionGrid", "SearchReview")

    require(
        checks,
        '{ key: "home", label: "记忆总览", icon: Home }' in app_source
        and ('const [activeView, setActiveView] = useState<ViewKey>("home")' in app_source or "const activeView = sharedState.mode.activeView" in app_source)
        and 'if (activeView === "home")' in app_source
        and "function HomeOverviewView" in app_source
        and "function buildHomeOverviewModel" in app_source
        and "Memory Weather" in app_source
        and "Next Best Actions" in app_source
        and "Black Hole 风险" in app_source
        and "Proto-Star 机会" in app_source
        and "proposal-only，不直接写长期记忆" in app_source
        and ".home-overview-view" in css_source
        and ".home-status-grid" in css_source
        and ".home-action-list" in css_source
        and ".home-topic-strip" in css_source,
        "memory_home_default_overview_ready",
        "Memory Atlas defaults to a Chinese-first overview with weather, state cards, next actions, preserved navigation, and proposal-only wording",
        "Memory Atlas default overview route, state cards, next actions, or proposal-only guard is missing",
    )

    require(
        checks,
        "Mini Starfield" in app_source
        and "River Pulse" in app_source
        and "Inspector Deep Link" in app_source
        and "function buildMiniStarfieldPreview" in app_source
        and "function buildRiverPulsePreview" in app_source
        and "function buildHomeInspectorLinks" in app_source
        and 'className="home-preview-card mini-starfield-preview"' in app_source
        and 'className="home-preview-card river-pulse-preview"' in app_source
        and 'className="home-inspector-link-list"' in app_source
        and 'jumpToPreview(model.miniStarfieldFocus, "galaxy")' in app_source
        and 'jumpToPreview(model.riverPulseFocus, "timeline")' in app_source
        and 'jumpToPreview(link.node, "search")' in app_source
        and "不加载 WebGL" in app_source
        and ".home-preview-grid" in css_source
        and ".home-preview-card" in css_source
        and ".river-pulse-row" in css_source
        and ".home-inspector-panel" in css_source
        and ".home-inspector-link-list" in css_source,
        "memory_home_preview_widgets_ready",
        "Home overview includes lightweight static starfield, recent river-pulse deltas, and Inspector deep links that preserve selected focus before switching boards",
        "Home overview preview widgets, focus-preserving deep links, or lightweight non-WebGL guard are missing",
    )

    require(
        checks,
        'const visualFocusViews: ViewKey[] = ["home", "galaxy", "notion", "roi", "obsidian", "timeline", "contribution", "wordcloud", "summary"]' in app_source
        and "const wideView = visualFocusViews.includes(activeView)" in app_source
        and "const workspaceClassName = wideView ? `workspace visual-focus-workspace ${activeView}-workspace` : \"workspace\"" in app_source
        and "const showSideInspector = activeView === \"contribution\" || !wideView" in app_source
        and "data-view={activeView}" in app_source
        and ".workspace.visual-focus-workspace" in css_source
        and ".workspace.contribution-workspace" in css_source
        and "grid-template-rows: auto auto minmax(0, 1fr);" in css_source
        and ".visual-workspace.contribution-view" in css_source
        and "grid-template-rows: auto auto auto minmax(0, 1fr) auto auto;" in css_source
        and '<div className="contribution-toolbar">' in contribution_grid
        and ".contribution-toolbar" in css_source
        and "<HeatLegend />" in contribution_grid
        and "function HeatLegend()" in app_source
        and ".heat-legend" in css_source
        and "heat-legend-gradient" in app_source
        and ".heat-legend-gradient" in css_source
        and "linear-gradient(90deg, #0f1116 0%, #17223a 10%, #1d3f77 24%, #1f6db2 40%, #1f9bd1 58%, #48c7e8 76%, #7ee0f8 90%, #a7ecff 100%)" in css_source
        and "grid-template-columns: auto 96px auto;" in css_source
        and "width: 96px;" in css_source
        and "热度从 0、低频、中频到高频逐步增强" in app_source
        and "const heatLevelAnchors" in app_source
        and "function heatCellStyle" in app_source
        and "function heatColorForScore" in app_source
        and "Math.log1p" in app_source
        and "白 → 灰 → 蓝" not in app_source
        and "白 → 灰 → 蓝" not in readme
        and "heat-legend-item" not in app_source
        and "@media (max-width: 720px)" in css_source
        and "grid-template-rows: auto minmax(0, 1fr);" in css_source
        and ".workspace.contribution-workspace" in css_source
        and "height: calc(100dvh - 55px);" in css_source
        and ".contribution-workspace .controls" in css_source
        and ".contribution-toolbar .scale-tabs" in css_source
        and "grid-template-columns: minmax(0, 1fr) auto;" in css_source
        and "overflow-x: auto;" in css_source,
        "contribution_grid_uses_full_scene_layout",
        "Contribution view switches to a compact workspace, merges controls, shows a heat scale, reserves the main grid row, and has mobile overflow guards",
        "Contribution view does not have the compact full-scene layout, heat-scale, or mobile guard contract",
    )
    require(
        checks,
        "selectedContributionPeriod" in app_source
        and "handleSelectNode" in app_source
        and "setSelectedContributionPeriod(null)" in app_source
        and "onSelectContributionPeriod" in app_source
        and "onSelectPeriod(selectedDetail)" in contribution_grid
        and "function ContributionPeriodInspector" in app_source
        and "buildContributionPeriodDetail" in app_source
        and "nodeMatchesContributionPeriod" in app_source
        and "selectionStillVisible" in app_source
        and "<ContributionPeriodInspector detail={selectedContributionPeriod} onSelectNode={handleSelectNode} />" in app_source
        and ('<NodeInspector atlas={scopedAtlas} node={selectedNode} edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)} />' in app_source
             or '<NodeInspector atlas={scopedAtlas} node={selectedNode} edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)} sharedState={sharedState} />' in app_source)
        and "grid-template-columns: minmax(0, 1fr) minmax(280px, 320px);" in css_source
        and ".content-grid.wide-view" in css_source
        and "grid-template-columns: 1fr;" in css_source
        and '.content-grid.wide-view[data-view="contribution"]' in css_source
        and "grid-template-columns: minmax(0, 1fr) minmax(260px, 300px);" in css_source
        and ".period-related-list" in css_source,
        "selection_updates_right_detail_panel",
        "Node selections keep detail routing in standard views; contribution cells preserve period drill-down while visual-first views reclaim the main scene area",
        "Selection detail routing or contribution period drill-down is missing, or visual-first views are still squeezed by the side inspector",
    )
    require(
        checks,
        'viewBox="0 0 1000 640"' in timeline_view
        and "display.eventTicks.map" in timeline_view
        and 'className="event-date-tick"' in timeline_view
        and 'className="event-axis-label"' in timeline_view
        and "function buildEventDateTicks" in app_source
        and "eventDateTick" in app_source
        and "formatAxisDate" in app_source
        and ".event-date-tick line" in css_source
        and ".event-axis-label" in css_source
        and "真实事件日期" in readme
        and "淡色月份网格只作为背景定位参考" in readme,
        "timeline_has_real_event_date_axis",
        "Timeline maps events by real event dates and exposes readable event-date labels on the horizontal axis with month ticks as context",
        "Timeline lacks real event-date axis labels or may only show abstract/month context labels",
    )
    require(
        checks,
        "const [timelineZoom, setTimelineZoom]" in timeline_view
        and "const [timelineCenter, setTimelineCenter]" in timeline_view
        and "const [timelineCursor, setTimelineCursor]" in timeline_view
        and "const [timelinePlaying, setTimelinePlaying]" in timeline_view
        and "buildTimelineLayout(timeline, nodeMap, { zoom: timelineZoom, center: timelineCenter, cursor: timelineCursor })" in timeline_view
        and 'className="timeline-control-bar"' in timeline_view
        and 'className="timeline-density-track"' in timeline_view
        and 'className="timeline-event-detail-strip"' in timeline_view
        and "onWheel={handleTimelineWheel}" in timeline_view
        and "display.densityBands.map" in timeline_view
        and "display.densityBars.map" in timeline_view
        and 'className="timeline-cursor"' in timeline_view
        and "function buildTimelineDensityBands" in app_source
        and "function buildTimelineDensityBackdrops" in app_source
        and ".timeline-control-bar" in css_source
        and ".timeline-density-track" in css_source
        and "grid-template-rows: auto auto auto auto auto auto minmax(0, 1fr) auto;" in css_source
        and ".timeline-map .timeline-canvas" in css_source
        and "min-height: 360px;" in css_source
        and ".timeline-cursor line" in css_source
        and ".timeline-event-detail-strip" in css_source
        and "动态窗口" in readme
        and "播放游标" in readme,
        "timeline_is_dynamic_interactive",
        "Timeline exposes zoom, window center, replay cursor, density track, density backdrops, hover detail strip, and wheel zoom",
        "Timeline is still static or lacks dynamic controls, density layers, replay cursor, or hover/detail interaction",
    )
    require(
        checks,
        'export type TimelineRendererMode = "memory-river" | "legacy"' in visual_flags_source
        and 'DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river"' in visual_flags_source
        and 'TIMELINE_RENDERER_STORAGE_KEY = "memory-atlas.timeline-renderer"' in visual_flags_source
        and "VITE_MEMORY_ATLAS_TIMELINE_RENDERER" in visual_flags_source
        and 'params.get("timelineRenderer") ?? params.get("timeline")' in visual_flags_source
        and "getInitialTimelineRendererMode" in timeline_view
        and "persistTimelineRendererMode" in timeline_view
        and 'className="timeline-renderer-toggle"' in timeline_view
        and "data-timeline-renderer={timelineRendererMode}" in timeline_view
        and 'className="memory-river-canvas timeline-canvas"' in timeline_view
        and 'data-utc-time-scale="true"' in timeline_view
        and "Macro / Meso / Micro" in timeline_view
        and "function parseTimelineUtcDay" in app_source
        and "function timelineUtcMs" in app_source
        and "function buildMemoryRiverLayout" in app_source
        and "function buildMemoryRiverPath" in app_source
        and "function memoryRiverMarkerKind" in app_source
        and "{ level: \"Macro\", note:" in app_source
        and "{ level: \"Meso\", note:" in app_source
        and "{ level: \"Micro\", note:" in app_source
        and ".timeline-renderer-toggle" in css_source
        and ".memory-river-canvas" in css_source
        and ".memory-river-level-label" in css_source
        and ".memory-river-lane-flow" in css_source
        and ".memory-river-marker" in css_source
        and "renderer_default: memory-river" in memory_river_params_source
        and "legacy_renderer: legacy" in memory_river_params_source
        and "use_utc_scale: true" in memory_river_params_source
        and "label: Macro" in memory_river_params_source
        and "label: Meso" in memory_river_params_source
        and "label: Micro" in memory_river_params_source,
        "timeline_stage5_1_river_rendering_ready",
        "Timeline defaults to Memory River behind a reversible renderer flag, uses explicit UTC scale helpers, and renders Macro/Meso/Micro lane paths with dedicated river markers",
        "Stage 5.1 Memory River rendering, UTC scale, Macro/Meso/Micro lanes, feature flag, or legacy rollback contract is missing",
    )
    require(
        checks,
        'type TimelineInteractionMode = "pan" | "brush"' in app_source
        and ("interface TimelineTimeRangeSelection" in app_source or "type TimelineTimeRangeSelection = SharedTimelineTimeRangeSelection" in app_source)
        and ("const [timelineTimeRange, setTimelineTimeRange]" in app_source or "const timelineTimeRange = sharedState.filters.timeRange" in app_source)
        and "handleMemoryRiverPointerDown" in timeline_view
        and "handleMemoryRiverPointerMove" in timeline_view
        and "handleMemoryRiverPointerUp" in timeline_view
        and "setPanDraft" in timeline_view
        and "setBrushDraft" in timeline_view
        and "buildTimelineRangeSelection" in app_source
        and "buildMemoryRiverRangeOverlay" in app_source
        and "buildMemoryRiverDraftOverlay" in app_source
        and "memory-river-interaction-bar" in timeline_view
        and "river-mode-tabs" in timeline_view
        and "memory-river-selected-range" in timeline_view
        and "memory-river-brush-draft" in timeline_view
        and "timeline-range-chip" in app_source
        and "timelineRangeSummary(timelineTimeRange)" in app_source
        and "时间河选择 · {timelineTimeRange.label}" in app_source
        and "lockedEventId" in timeline_view
        and "lockMemoryRiverEvent" in timeline_view
        and "memory-river-event-card" in timeline_view
        and 'data-event-card={lockedEvent ? "locked" : "hover"}' in timeline_view
        and "redacted derived event" in timeline_view
        and "同步 Inspector" in timeline_view
        and "interface TimelineFeedbackSettings" in app_source
        and "TIMELINE_FEEDBACK_SETTINGS_KEY" in app_source
        and "getInitialTimelineFeedbackSettings" in app_source
        and "persistTimelineFeedbackSettings" in app_source
        and "pseudoHaptic: false" in app_source
        and "audio: false" in app_source
        and "emitTimelineFeedback" in app_source
        and "navigator.vibrate" in app_source
        and "gain.gain.value = 0.018" in app_source
        and ".memory-river-interaction-bar" in css_source
        and ".river-mode-tabs" in css_source
        and ".memory-river-selected-range rect" in css_source
        and ".memory-river-brush-draft rect" in css_source
        and ".memory-river-event-card" in css_source
        and ".timeline-sync-pill" in css_source
        and ".filter-chip-row .timeline-range-chip" in css_source
        and 'stage: "5.3"' in memory_river_params_source
        and 'task: "5.3 Evidence Layers"' in memory_river_params_source
        and "pan_enabled: true" in memory_river_params_source
        and "brush_enabled: true" in memory_river_params_source
        and "click_event_card_enabled: true" in memory_river_params_source
        and "pseudo_haptic_default: false" in memory_river_params_source
        and "audio_feedback_default: false" in memory_river_params_source
        and "vibration_default: false" in memory_river_params_source,
        "timeline_stage5_2_river_interaction_ready",
        "Memory River supports pointer pan, brush range selection synced to Home/Galaxy/Interaction Lens, hover/click event cards, and safe reduced-motion/audio/haptic feedback settings",
        "Stage 5.2 Memory River pan, brush, event-card, sync, safe-feedback, or parameter contract is missing",
    )
    require(
        checks,
        'type MemoryRiverEvidenceKind = "black-hole-lifecycle" | "proto-star-lifecycle" | "stale-deprecated"' in app_source
        and "interface MemoryRiverEvidenceLayer" in app_source
        and "buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes)" in app_source
        and "buildBlackHoleLifecycleLayer" in app_source
        and "buildProtoStarLifecycleLayer" in app_source
        and "buildStaleDeprecatedLayer" in app_source
        and "isMemoryRiverBlackHoleEvent" in app_source
        and "isMemoryRiverProtoStarEvent" in app_source
        and "isMemoryRiverStaleDeprecatedEvent" in app_source
        and "isBlackHoleCandidate(event.node)" in app_source
        and "isProtoStarCandidate(event.node, recentStart, latest)" in app_source
        and "riverDisplay.evidenceLayers.map((layer)" in timeline_view
        and 'data-evidence-layer={layer.kind}' in timeline_view
        and 'data-evidence-segment={layer.kind}' in timeline_view
        and "redacted derived signals" in timeline_view
        and "black-hole-lifecycle" in timeline_view
        and "proto-star-lifecycle" in timeline_view
        and "stale-deprecated" in timeline_view
        and ".memory-river-evidence-layer.black-hole-lifecycle rect" in css_source
        and ".memory-river-evidence-layer.proto-star-lifecycle path" in css_source
        and ".memory-river-evidence-layer.stale-deprecated rect" in css_source
        and 'stage: "5.3"' in memory_river_params_source
        and "black_hole_lifecycle_enabled: true" in memory_river_params_source
        and "proto_star_lifecycle_enabled: true" in memory_river_params_source
        and "stale_deprecated_fade_enabled: true" in memory_river_params_source
        and "home_consistency_source: isBlackHoleCandidate / isProtoStarCandidate" in memory_river_params_source
        and "evidence_payload: redacted_derived_signal_only" in memory_river_params_source,
        "timeline_stage5_3_evidence_layers_ready",
        "Memory River renders Stage 5.3 black-hole lifecycle, proto-star lifecycle, and stale/deprecated fade layers from redacted derived signals consistent with Home overview semantics",
        "Stage 5.3 Memory River evidence layers, derived-signal mapping, CSS, parameters, or audit contract are missing",
    )
    shared_state_source = read_text(repo_root / "apps/memory-atlas/src/state/sharedAtlasState.ts")
    require(
        checks,
        "export interface SharedAtlasSelectionState" in shared_state_source
        and "export interface SharedAtlasFilterState" in shared_state_source
        and "export interface SharedAtlasFocusState" in shared_state_source
        and "export function sharedAtlasReducer" in shared_state_source
        and "clearSharedAtlasFilter" in shared_state_source
        and "roi: SharedAtlasRoiFilter" in shared_state_source
        and "loopGuard" in shared_state_source
        and "useReducer(" in app_source
        and "sharedAtlasReducer" in app_source
        and "const timelineTimeRange = sharedState.filters.timeRange" in app_source
        and "dispatchSharedState({ type: \"select_node\", node, source: activeView })" in app_source
        and "dispatchSharedState({ type: \"select_time_range\", range, source: \"timeline\" })" in app_source
        and "dispatchSharedState({ type: \"clear_filter\", key, source: activeView })" in app_source
        and "data-shared-state={sharedState.schema_version}" in app_source
        and "data-shared-focus-node={sharedState.focus.home.nodeId ?? \"\"}" in app_source
        and "data-shared-focus-node={sharedState.focus.galaxy.nodeId ?? \"\"}" in app_source
        and "data-shared-focus-node={sharedState.focus.timeline.nodeId ?? \"\"}" in app_source
        and "data-shared-focus-node={sharedState.focus.inspector.nodeId ?? \"\"}" in app_source
        and "data-sync-revision={sharedState.sync.revision}" in app_source
        and ".lens-state-strip" in css_source
        and ".home-shared-focus-strip" in css_source,
        "stage6_1_shared_state_store_ready",
        "Stage 6.1 uses a typed shared-state reducer for selection/filter/time range/focus and exposes shared focus across Home, Galaxy, Timeline and Inspector",
        "Stage 6.1 shared-state schema, reducer actions, focus bindings, or status UI evidence is missing",
    )
    require(
        checks,
        "interface InspectorExplanation" in app_source
        and "function buildInspectorExplanation" in app_source
        and "function InspectorExplanationPanel" in app_source
        and "memory_weight = tier*0.5 + importance*0.3 + confidence*0.2" in app_source
        and "leverage_score = max(0, memory_weight + decision_impact*0.15 - sensitivity_penalty)" in app_source
        and 'data-raw-display="false"' in app_source
        and 'data-default-raw-summary="hidden"' in app_source
        and 'data-debug-lite={debugOpen ? "open" : "closed"}' in app_source
        and 'data-debug-panel="true"' in app_source
        and "function buildWritebackProposalDraft" in app_source
        and 'proposalIdPrefix: "atlas_preview"' in app_source
        and 'data-proposal-only="true"' in app_source
        and 'data-active-memory-mutation="false"' in app_source
        and "JSON 提案预览" in app_source
        and "direct_frontend_mutation_of_active_memory: false" in app_source
        and "requires_agent_or_human_apply: true" in app_source
        and ".inspector-explanation-panel" in css_source
        and ".inspector-debug-panel" in css_source
        and ".writeback-json-preview" in css_source,
        "stage6_2_inspector_proposal_ready",
        "Stage 6.2 Inspector separates default formulas/evidence explanation from Debug fields and keeps writeback proposal-only JSON with active-memory mutation disabled",
        "Stage 6.2 Inspector explanation, Debug separation, proposal-only JSON, or safety contract is missing",
    )
    require(
        checks,
        '"validate:stage7-visual": "node scripts/validate_stage7_visual_acceptance.cjs"' in read_text(repo_root / "apps/memory-atlas/package.json")
        and "function validateGalaxyVisualAcceptance" in stage7_visual_source
        and "function validateMemoryRiverVisualAcceptance" in stage7_visual_source
        and "stage7-galaxy-desktop.png" in stage7_visual_source
        and "stage7-memory-river-desktop.png" in stage7_visual_source
        and "__memoryAtlasGalaxySignal" in stage7_visual_source
        and "signal.lit > 100" in stage7_visual_source
        and "signal.rendererMode === \"memory-starfield\"" in stage7_visual_source
        and "signal.fallbackMode !== \"legacy\"" in stage7_visual_source
        and ".memory-river-canvas" in stage7_visual_source
        and "black-hole-lifecycle" in stage7_visual_source
        and "proto-star-lifecycle" in stage7_visual_source
        and "stale-deprecated" in stage7_visual_source
        and "assertPortClosed" in stage7_visual_source
        and "Playwright" in stage7_visual_source,
        "stage7_1_visual_acceptance_ready",
        "Stage 7.1 has a real-browser visual acceptance gate for non-empty Galaxy canvas pixels, starfield screenshot quality, Memory River screenshot quality, and 4177 cleanup",
        "Stage 7.1 visual acceptance browser gate, screenshots, pixel checks, Memory River checks, or cleanup assertion is missing",
    )
    require(
        checks,
        '"validate:stage7-performance": "node scripts/validate_stage7_performance_acceptance.cjs"' in read_text(repo_root / "apps/memory-atlas/package.json")
        and "fps: latestPerformanceSnapshot.fps" in galaxy_source
        and "averageFrameMs: latestPerformanceSnapshot.averageFrameMs" in galaxy_source
        and "adaptiveQualityEnabled: latestPerformanceSnapshot.adaptiveQualityEnabled" in galaxy_source
        and "__memoryAtlasGalaxyLifecycle" in galaxy_source
        and "renderer.forceContextLoss()" in galaxy_source
        and "className=\"galaxy-performance-overlay\"" in galaxy_source
        and ".galaxy-performance-overlay" in css_source
        and "highMinFps: 45" in stage7_performance_source
        and "midMinFps: 30" in stage7_performance_source
        and "validateInitialAdaptiveOverlay" in stage7_performance_source
        and "validateLowQualityFallback" in stage7_performance_source
        and "validateCleanupHooks" in stage7_performance_source
        and "stage7-performance-report.json" in stage7_performance_source
        and "assertPortClosed" in stage7_performance_source,
        "stage7_2_performance_acceptance_ready",
        "Stage 7.2 has FPS metrics, adaptive quality controls, high/mid/low browser performance gates, cleanup lifecycle hooks, and 4177 cleanup",
        "Stage 7.2 performance metrics, adaptive quality, browser gate, cleanup lifecycle, or port cleanup assertion is missing",
    )
    require(
        checks,
        '"validate:stage7-privacy-accessibility": "node scripts/validate_stage7_privacy_accessibility.cjs"' in read_text(repo_root / "apps/memory-atlas/package.json")
        and 'data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}' in app_source
        and 'data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}' in app_source
        and 'data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? "opted-in" : "silent-by-default"}' in app_source
        and 'window.matchMedia?.("(prefers-reduced-motion: reduce)").matches' in app_source
        and "navigator.vibrate" in app_source
        and "new window.AudioContext()" in app_source
        and "runReleasePrivacyAudit" in stage7_privacy_accessibility_source
        and "inspectPublishArtifact" in stage7_privacy_accessibility_source
        and "validateReducedMotion" in stage7_privacy_accessibility_source
        and "validateSilentFeedbackDefaults" in stage7_privacy_accessibility_source
        and "stage7-privacy-accessibility-report.json" in stage7_privacy_accessibility_source
        and "reducedMotion: \"reduce\"" in stage7_privacy_accessibility_source
        and "silent-by-default" in stage7_privacy_accessibility_source
        and "navigator.vibrate" in stage7_privacy_accessibility_source
        and "AudioContext" in stage7_privacy_accessibility_source
        and "assertPortClosed" in stage7_privacy_accessibility_source,
        "stage7_3_privacy_accessibility_ready",
        "Stage 7.3 has a publish artifact privacy scan, reduced-motion browser gate, silent feedback defaults, vibration/audio probes, and 4177 cleanup",
        "Stage 7.3 privacy scan, reduced-motion browser gate, silent feedback defaults, feedback probes, or port cleanup assertion is missing",
    )
    require(
        checks,
        '"rollback_to_version"' in app_source
        and "function createRollbackProposal" in app_source
        and "function exportProposalHistory" in app_source
        and "function buildProposalDiff" in app_source
        and "function buildProposalReview" in app_source
        and 'className="writeback-diff-grid"' in app_source
        and 'className="writeback-version-chain"' in app_source
        and "生成回滚提案" in app_source
        and ".writeback-diff-grid" in css_source
        and ".writeback-version-chain" in css_source
        and "版本链" in readme
        and "rollback proposal" in readme,
        "writeback_has_version_diff_and_rollback",
        "Writeback proposals expose readable diffs, version-chain export, rollback proposal generation, and pending-agent apply policy",
        "Writeback proposals lack version chain, readable diff, rollback proposal, or explicit pending-agent apply contract",
    )
    require(
        checks,
        "Array.from({ length: daysInYear }" in app_source
        and "const startWeekday = mondayWeekdayIndex(yearStart)" in app_source
        and "const weekColumns = Math.ceil((daysInYear + startWeekday) / 7)" in app_source
        and "calendarWeekKey(year, weekColumn)" in app_source
        and "previousIsoWeekKey" not in app_source
        and 'const weekdayLabels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]' in app_source
        and 'className="weekday-label-column"' in contribution_grid
        and 'scale === "week"\n                ? periodData.weekCells.map' in contribution_grid
        and 'className={`week-cell level-${cell.activityLevel}${active ? " selected" : ""}`}' in contribution_grid
        and 'gridRow: "1 / span 7"' in contribution_grid
        and "cell.daySlots.map" in contribution_grid
        and "week-trend" in contribution_grid
        and "trendSegmentStyle(slot, periodData.dayMaxActivityScore)" in contribution_grid
        and "function trendSegmentStyle" in app_source
        and "同源同色阶的 7 个日段" in readme
        and "不是另一张表或单条大色块" in readme
        and "grid-template-rows: repeat(7, minmax(0, 1fr));" in css_source
        and "grid-template-columns: repeat(var(--week-columns), minmax(0, 1fr));" in css_source
        and ".weekday-label-column" in css_source
        and ".week-cell" in css_source
        and "aspect-ratio: 1 / 7;" in css_source
        and ".week-trend" in css_source
        and "grid-template-rows: repeat(7, minmax(0, 1fr));" in css_source
        and ".cell-trend .trend-segment" in css_source
        and "background: var(--heat-bg, transparent);" in css_source
        and ".year-heatmap.week-mode,\n  .week-label-row,\n  .month-heatmap,\n  .year-trend-grid" in css_source
        and "gap: 0.5px;" in css_source
        and ".level-0 {\n  background: var(--heat-bg, #0f1116);" in css_source
        and ".level-1 {\n  background: var(--heat-bg, #17223a);" in css_source
        and ".level-3 {\n  background: var(--heat-bg, #1f6db2);" in css_source
        and ".level-5 {\n  background: var(--heat-bg, #a7ecff);" in css_source
        and "W${index + 1}" in contribution_grid,
        "contribution_day_week_grid_contract",
        "Day mode keeps 365/366 square cells in Monday-to-Sunday rows; week mode uses selectable natural-week columns sharing the same coordinate plane with 7 internal day-granularity trend cells",
        "Day/week grid contract is missing Monday-first rows, weekday labels, natural week keys, shared-coordinate week columns, internal day trend cells, or week labels",
    )
    require(
        checks,
        'source: "all"' in app_source
        and "buildSourceOptions(atlas, memoryNodes)" in app_source
        and "分析对象" in app_source
        and "const sourceMemoryNodes = useMemo" in app_source
        and "buildSourceScopedAtlas(atlas, sourceMemoryNodes, filters.source)" in app_source
        and "getNodeMap(scopedAtlas)" in app_source
        and "getThemeNodes(scopedAtlas)" in app_source
        and "filterMemoryNodes(sourceMemoryNodes, filters)" in app_source
        and "buildFilteredSlice(scopedAtlas, filteredMemoryNodes, filters)" in app_source
        and "buildSourceScopedContribution" in app_source
        and "sourceMatchesNode" in app_source
        and "sourceDisplayLabel" in app_source
        and '.filter((source) => ["all", "memory_atlas", "codex"].includes(source.id))' in app_source
        and 'if (sourceId === "all") return "总数据源";' in app_source
        and 'if (sourceId === "memory_atlas") return "ChatGPT";' in app_source
        and 'if (sourceId === "codex") return "Codex";' in app_source
        and 'tier: "all"' in app_source
        and 'category: "all"' in app_source
        and 'theme: "all"' in app_source
        and "contributionYears(atlas, nodes)" in app_source
        and 'className="year-picker"' in contribution_grid
        and "availableYears.map" in contribution_grid
        and ".year-picker" in css_source,
        "source_and_year_controls_exist",
        "Memory Atlas exposes source selection, rebuilds a source-scoped atlas for every visualization, resets stale dependent filters, and keeps contribution year selection from available history years",
        "Source selector, source-scoped visualization refresh contract, or contribution year selector is missing",
    )
    require(
        checks,
        "Array.from({ length: 24 }" in app_source
        and "grid-template-columns: repeat(24, minmax(0, 1fr));" in css_source
        and ".month-cell" in css_source
        and "buildMonthDaySlots" in app_source
        and 'className="cell-trend month-trend smooth-trend"' in contribution_grid
        and 'className="cell-trend week-trend smooth-trend"' in contribution_grid
        and 'trendGradient(cell.daySlots, "180deg",' in contribution_grid
        and ".month-trend" in css_source
        and ".cell-trend.smooth-trend" in css_source
        and "--segment-color" in app_source
        and "fluidTrendIntensities" in app_source
        and "sampleCount = Math.max(anchors.length * 7, 18)" in app_source
        and "catmullRom" in app_source
        and "smoothStep" in app_source
        and ".cell-trend.smooth-trend .trend-segment" in css_source
        and "background: transparent;" in css_source
        and "color-mix(in srgb, var(--segment-color, transparent) 26%, transparent)" not in css_source
        and "filter: none;" in css_source
        and "grid-template-rows: repeat(var(--month-days), minmax(0, 1fr));" in css_source
        and "yearCells" in app_source
        and "monthSlots" in app_source
        and 'className="year-trend-grid year-comparison-trend"' in contribution_grid
        and 'className={`year-cell year-summary-card level-${cell.activityLevel}${active ? " selected" : ""}`}' in contribution_grid
        and 'className="year-card-header"' in contribution_grid
        and 'className="year-month-track"' in contribution_grid
        and 'className={`year-month-bar level-${slot.activityLevel}`}' in contribution_grid
        and 'className="year-month-axis"' in contribution_grid
        and 'className="year-card-footer"' in contribution_grid
        and "yearCellStyle(cell, periodData.yearMaxActivityScore)" in contribution_grid
        and "monthBarStyle(slot, cell.monthSlots)" in contribution_grid
        and "function monthBarStyle" in app_source
        and "startColumn" not in contribution_grid
        and "cell.monthSlots.map" in contribution_grid
        and "grid-auto-rows: minmax(62px, 1fr);" in css_source
        and "grid-auto-rows: minmax(142px, 1fr);" in css_source
        and ".year-trend-grid.year-comparison-trend" in css_source
        and "grid-template-columns: repeat(2, minmax(0, 1fr)) !important;" in css_source
        and "grid-template-rows: 1fr;" in css_source
        and "grid-auto-flow: column;" in css_source
        and "height: 100%;" in css_source
        and "aspect-ratio: auto;" in css_source
        and ".year-cell.year-summary-card" in css_source
        and "grid-template-rows: auto minmax(0, 1fr) auto auto;" in css_source
        and ".year-month-track" in css_source
        and ".year-month-bar" in css_source
        and ".year-month-axis" in css_source
        and ".year-month-bar em" not in css_source
        and "grid-template-columns: repeat(12, minmax(0, 1fr));" in css_source
        and "height: var(--month-height, 9%);" in css_source
        and "width: 100%;" in css_source
        and "max-width: 100%;" in css_source
        and "const periodKey = cell.date" in contribution_grid,
        "contribution_month_year_grid_contract",
        "Month mode keeps 24 selectable month columns with readable labels and smooth internal daily trends; year mode uses side-by-side selectable year comparison cards with left-to-right month bar trends, a clean quarter axis, and year summary metrics",
        "Month/year grid contract is missing 24 month columns, smooth internal daily trends, side-by-side year comparison cards, horizontal month bars, or year summary metrics",
    )
    require(
        checks,
        "title={contributionTitle(cell)}" in contribution_grid
        and contribution_grid.count("title={contributionTitle(cell)}") >= 2
        and "contributionTitle(bucket: PeriodCounts)" in app_source
        and "全局对话" in app_source
        and "筛选记忆" in app_source,
        "contribution_cells_have_hover_stats",
        "Heatmap cells expose time and count details through native hover titles",
        "Heatmap cells do not expose time/count hover details",
    )
    require(
        checks,
        '"wordcloud"' in app_source
        and 'label: "词云洞察"' in app_source
        and "function WordCloudView" in app_source
        and "buildSemanticInsights" in app_source
        and "SemanticInsight" in app_source
        and "SemanticMatrixCell" in app_source
        and "WordCloudItem" in app_source
        and "semantic-dashboard" in app_source
        and "semantic-heatmap" in app_source
        and "semantic-bubbles" in app_source
        and "semantic-cloud" in app_source
        and "Heatmap" in app_source
        and "Bubble Chart" in app_source
        and "Word Cloud" in app_source
        and "selectRepresentativeNode" in app_source
        and "jumpToBestNode" in app_source
        and ".semantic-dashboard" in css_source
        and ".semantic-heat-cell" in css_source
        and ".semantic-bubble-canvas" in css_source
        and ".word-cloud-field" in css_source
        and ".word-cloud-token" in css_source
        and "Word Cloud: 词云洞察是独立导航板块" in readme
        and "Heatmap 显示主题 x 记忆层级密度" in readme
        and "Bubble Chart 显示" in readme
        and "三层都必须可点击并同步右侧" in readme,
        "wordcloud_semantic_views_ready",
        "Word Cloud view exposes clickable semantic heatmap, ROI/recent bubble chart, and word cloud layers backed by current filtered memory nodes",
        "Word Cloud view, semantic heatmap, bubble chart, clickable tokens, or documentation is missing",
    )
    require(
        checks,
        "function InteractionLens" in app_source
        and "selectAdjacentNode" in app_source
        and "selectableLensNodes" in app_source
        and "activeFilterChips" in app_source
        and "onClearFilter" in app_source
        and "selectedContributionPeriod={activeView === \"contribution\" ? selectedContributionPeriod : null}" in app_source
        and "上一个焦点" in app_source
        and "下一个焦点" in app_source
        and "聚焦主题" in app_source
        and "重置筛选" in app_source
        and "全部数据" in app_source
        and ".interaction-lens" in css_source
        and ".filter-chip-row" in css_source
        and ".lens-stepper" in css_source
        and "grid-template-rows: auto auto auto minmax(0, 1fr);" in css_source
        and "Interaction Lens:" in readme
        and "active filter chips" in readme
        and "theme focus only changes the current browser view" in readme,
        "cross_view_interaction_lens",
        "Every visualization shares a compact interaction lens with current focus, adjacent selection, active filter chips, theme focus, reset controls, and mobile-safe layout",
        "Cross-view interaction lens, filter chip clearing, adjacent focus, or mobile-safe lens layout is missing",
    )
    require(
        checks,
        "function HumanOverviewPanel" in app_source
        and "function AgentRecommendationsPanel" in app_source
        and "目前记录了什么" in app_source
        and "需要做什么" in app_source
        and "记得做什么" in app_source
        and "机会/增长方向" in app_source
        and "dedupeNodesForDisplay" in app_source
        and "dedupeDisplayItems" in app_source
        and "humanNodeDisplayTitle" in app_source
        and "未来回答需要遵守的一条长期规则" not in app_source
        and "这条记忆说明了什么" in app_source
        and "为什么重要" in app_source
        and "未来应该怎么用" in app_source
        and ("Agent 结构化字段 / 原始摘要" in app_source or "Debug / Agent Inspector" in app_source)
        and "Memory / Personalization" in app_source
        and "Agents.md / 执行规则" in app_source
        and "降权/不再默认使用" in app_source
        and ".human-overview" in css_source
        and ".human-node-card" in css_source,
        "memory_atlas_has_human_facing_summary",
        "Inspector and search views expose human-readable topics, actions, reminders, opportunities, folded agent/source summaries, deduped display rows, and recommendation buckets",
        "Memory Atlas may still expose repeated template text or mostly agent/internal metadata instead of human-facing memory conclusions",
    )
    require(
        checks,
        '"summary"' in app_source
        and 'label: "总结与迭代"' in app_source
        and "function SummaryIterationView" in app_source
        and "function ConfigMemoryPanel" in app_source
        and "Personalization / Agents.md 建议" in app_source
        and "Memory / Personalization" in app_source
        and "Agents.md / 执行规则" in app_source
        and "config.toml / Memory" in app_source
        and "更新时间" in app_source
        and "buildIterationHighlights" in app_source
        and "summary-iteration-view" in app_source
        and ".summary-iteration-view" in css_source
        and ".visual-workspace.summary-iteration-view" in css_source
        and "flex-direction: column;" in css_source
        and ".summary-signal-grid" in css_source
        and ".summary-iteration-view > .summary-signal-grid" in css_source
        and ".summary-iteration-view > .human-overview" in css_source
        and ".summary-iteration-view > .iteration-panels" in css_source
        and "flex: 1 1 auto;" in css_source
        and "min-height: 88px;" in css_source
        and ".summary-iteration-view .human-overview-grid" in css_source
        and ".summary-iteration-view .human-lists" in css_source
        and "grid-template-columns: repeat(4, minmax(0, 1fr));" in css_source
        and ".iteration-panels" in css_source
        and "grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);" in css_source
        and "overflow: hidden;" in css_source
        and "overflow: auto;" in css_source
        and ".config-memory-panel" in css_source
        and ".config-memory-grid" in css_source
        and "overflow-wrap: anywhere;" in css_source
        and "white-space: normal;" in css_source
        and "Summary & Iteration" in readme
        and "总结与迭代是独立导航板块" in readme
        and "config.toml" in readme
        and "Personalization / Memory" in readme,
        "summary_iteration_view_ready",
        "Summary & Iteration exposes updated-at, human highlights, Personalization/Memory, Agents.md, config.toml, and Memory suggestions as a first-class navigation mode",
        "Summary & Iteration navigation mode, updated-at, or agent configuration suggestion panels are missing",
    )
    require(
        checks,
        "function MiniBarList" in app_source
        and "roi-visual-strip" in app_source
        and "roi-mini-bars" in app_source
        and "search-visual-summary" in app_source
        and "search-topic-bars" in app_source
        and "buildSearchVisualRows" in app_source
        and "remapValues" in app_source
        and "summary-signal-grid" in app_source
        and "semantic-dashboard" in app_source
        and "timeline-canvas" in app_source
        and "year-heatmap" in app_source
        and "year-trend-grid year-comparison-trend" in app_source
        and "ObsidianGraphScene" in obsidian_source
        and "GalaxyScene" in galaxy_source
        and ".roi-visual-strip" in css_source
        and ".roi-mini-bars" in css_source
        and ".search-visual-summary" in css_source
        and ".search-topic-bars" in css_source
        and ".mini-bar-list" in css_source
        and ".mini-bar-row" in css_source
        and "视觉化程度 80%+" in readme,
        "all_views_visual_density_at_least_80_contract",
        "All navigation views keep an evidence-bearing visual surface; ROI and Search include synchronized mini-bar summaries instead of pure list/table layouts",
        "One or more navigation views may still be primarily text/list/table without the 80%+ visual-density contract",
    )
    require(
        checks,
        "function clearTransientBrowserState" in app_source
        and "window.sessionStorage.clear()" in app_source
        and "TRANSIENT_STORAGE_PREFIXES" in app_source
        and "TRANSIENT_CACHE_PREFIXES" in app_source
        and "caches.keys()" in app_source
        and "serviceWorker.getRegistrations" in app_source
        and 'window.addEventListener("pagehide", handlePageRelease)' in app_source
        and 'window.addEventListener("beforeunload", handlePageRelease)' in app_source
        and 'release("react_unmount")' in app_source
        and "request_shutdown" in installer_source
        and "release_requested" in installer_source
        and "active_thread_count" in installer_source
        and "allow_reuse_address = True" in installer_source
        and '"-m http.server"' in installer_source
        and "last_seen_at = time.time() - max" not in installer_source
        and "关闭 tab" in readme
        and "清理临时浏览器缓存" in readme,
        "runtime_tab_close_cache_cleanup_contract",
        "Browser pagehide/beforeunload/react unmount release the local runtime, clear transient browser state, and the embedded server shuts down immediately instead of waiting for idle TTL",
        "Tab-close release, browser cache cleanup, or immediate embedded server shutdown contract is missing",
    )
    require(
        checks,
        "#ffd166" not in app_source
        and "#ffd166" not in css_source
        and "#ffd166" not in galaxy_source
        and "#ffd166" not in data_builder_source
        and "#ffd166" not in atlas_source
        and "#ff9f7a" not in app_source
        and "#ff9f7a" not in css_source
        and "#ff9f7a" not in galaxy_source
        and "#ff9f7a" not in data_builder_source
        and "#ff9f7a" not in atlas_source
        and "255, 209, 102" not in css_source
        and "255, 209, 102" not in galaxy_source
        and "#ffe6a3" not in galaxy_source,
        "memory_atlas_avoids_yellow_primary_palette",
        "Memory Atlas UI, galaxy renderer, and generated visualization data avoid yellow/orange primary accents and use the blue-forward palette",
        "Memory Atlas still has yellow/orange primary accents in UI, galaxy renderer, data generator, or generated atlas data",
    )
    require(
        checks,
        "{renderError ? (" in galaxy_source
        and "CanvasTexture" in galaxy_source
        and "PlaneGeometry" in galaxy_source
        and "createWebglGalaxyTexture()" in galaxy_source
        and "drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 48" in galaxy_source
        and "drawDustLane(ctx, centerX, centerY, scale, arm)" in galaxy_source
        and "drawNebulaCloud(ctx, x, y, armColors[arm]" in galaxy_source
        and "alpha: false" in galaxy_source
        and "renderer.setClearColor(0x020308, 1);" in galaxy_source
        and 'scene.background = new Color("#020308");' in galaxy_source
        and "renderer.clear(true, true, true);" in galaxy_source
        and '<div className="star-overlay"' in galaxy_source
        and galaxy_source.count('<div className="star-overlay"') == 1
        and '"star-dot"' in galaxy_source
        and 'item.node.id === selectedNode?.id ? "selected" : ""' in galaxy_source
        and 'selectedNeighborIds.has(item.node.id) ? "neighbor" : ""' in galaxy_source
        and "overlayPresent" not in galaxy_source
        and 'className = "galaxy-webgl-canvas"' in galaxy_source
        and ".galaxy-webgl-canvas" in css_source
        and ".star-dot {" in css_source
        and "opacity: 0;" in css_source
        and "box-shadow: none;" in css_source,
        "galaxy_webgl_has_no_visible_html_dot_overlay",
        "WebGL uses an opaque cleared canvas; HTML star-dot overlay is fallback-only and invisible by default",
        "Galaxy may still render visible HTML dots over the WebGL scene",
    )
    require(
        checks,
        "RotateCcw, ZoomIn, ZoomOut" in galaxy_source
        and "hoveredIdRef" in galaxy_source
        and "setHoverPreview" in galaxy_source
        and "pickNearestNode" in galaxy_source
        and "focusEdgeLines" in galaxy_source
        and "updateFocusEdgeHighlight" in galaxy_source
        and "Vector3" in galaxy_source
        and "updateCameraFocus" in galaxy_source
        and "camera.position.lerp(cameraTargetPosition" in galaxy_source
        and "camera.lookAt(cameraLookAt)" in galaxy_source
        and "neighborPulseGroup" in galaxy_source
        and "rebuildNeighborPulses" in galaxy_source
        and "updateNeighborPulse" in galaxy_source
        and "MAX_FOCUS_PRIMARY_NEIGHBORS" in galaxy_source
        and "MAX_FOCUS_SECONDARY_NEIGHBORS" in galaxy_source
        and "MAX_FOCUS_VISIBLE_NEIGHBORS" in galaxy_source
        and "function buildFocusedNeighborhood" in galaxy_source
        and "function localNeighborhoodPosition" in galaxy_source
        and 'layer: index < MAX_FOCUS_PRIMARY_NEIGHBORS ? "primary" as const : "secondary" as const' in galaxy_source
        and "activeFocusedNeighborhood.hiddenNeighborCount" in galaxy_source
        and "focusVisibleNeighborCount" in galaxy_source
        and "focusHiddenNeighborCount" in galaxy_source
        and "focusPrimaryNeighborCount" in galaxy_source
        and "focusSecondaryNeighborCount" in galaxy_source
        and "聚焦显示" in galaxy_source
        and "高连接保护" in galaxy_source
        and "折叠" in galaxy_source
        and 'className="galaxy-neighbor-cards"' in galaxy_source
        and "内环邻居" in galaxy_source
        and "primaryNeighborCards" in galaxy_source
        and "onClick={() => onSelectNode(node)}" in galaxy_source
        and ".galaxy-neighbor-cards" in css_source
        and ".neighbor-card-list button" in css_source
        and "directNeighborList" in galaxy_source
        and "selectedNeighborIds" in galaxy_source
        and "highlightedNeighborCount" in galaxy_source
        and "__memoryAtlasGalaxyDebugTargets" in galaxy_source
        and "readGalaxyDebugTargets" in galaxy_source
        and "projected.project(camera)" in galaxy_source
        and "degreeMap(edges)" in galaxy_source
        and 'className="galaxy-controls"' in galaxy_source
        and 'className="galaxy-hover-preview"' in galaxy_source
        and 'aria-label="重置银河视角"' in galaxy_source
        and 'aria-label="放大银河视角"' in galaxy_source
        and 'aria-label="缩小银河视角"' in galaxy_source
        and ".galaxy-controls" in css_source
        and ".galaxy-hover-preview" in css_source
        and ".star-dot.neighbor" in css_source
        and "@keyframes fallback-neighbor-pulse" in css_source
        and "pointer-events: none;" in css_source
        and "hover 最近星体预览" in readme
        and "点击选中后相机自动飞近并聚焦" in readme
        and "关联边高亮" in readme
        and "关联邻居节点脉冲高亮" in readme
        and "局部邻域布局" in readme
        and "primary layer" in readme
        and "secondary layer" in readme
        and "高连接主题节点只显示 Top 局部邻居和有限焦点边线" in readme
        and "折叠数量" in readme
        and "内环邻居小型详情卡" in readme
        and "可点击跳转到对应邻居节点" in readme
        and "视角重置和缩放按钮" in readme,
        "galaxy_interaction_controls_ready",
        "Galaxy supports nearest-star hover previews, selected-node camera fly-in focus, layered local-neighborhood focus, capped selected-node edge highlighting, folded high-degree neighbors, inner-neighbor detail cards, and reset/zoom controls without polluting fallback overlays",
        "Galaxy hover preview, selected camera focus, layered local-neighborhood display, capped edge highlight, folded high-degree neighbors, inner-neighbor cards, or reset/zoom controls are missing",
    )
    require(
        checks,
        "CanvasTexture" in galaxy_source
        and "PlaneGeometry(470, 330)" in galaxy_source
        and "galaxyPlane.renderOrder = -10" in galaxy_source
        and 'renderer.domElement.dataset.nebulaTexture = "spiral-dust-cloud";' in galaxy_source
        and "createWebglGalaxyTexture" in galaxy_source
        and "webgl-dust" in galaxy_source
        and "webgl-cloud" in galaxy_source,
        "galaxy_webgl_has_nebula_texture_layer",
        "Galaxy WebGL includes a procedural nebula texture with spiral arms, dust, and cloud knots behind interactive bodies",
        "Galaxy WebGL may still be only a point-cloud layer without a nebula/spiral substrate",
    )
    require(
        checks,
        'DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield"' in visual_flags_source
        and "VITE_MEMORY_ATLAS_GALAXY_RENDERER" in visual_flags_source
        and "GALAXY_RENDERER_STORAGE_KEY" in visual_flags_source
        and "galaxyRenderer" in visual_flags_source
        and "persistGalaxyRendererMode" in app_source
        and "galaxy-renderer-toggle" in app_source
        and 'aria-pressed={galaxyRendererMode === "memory-starfield"}' in app_source
        and 'aria-pressed={galaxyRendererMode === "legacy"}' in app_source
        and "rendererMode: GalaxyRendererMode" in galaxy_source
        and 'renderer.domElement.dataset.rendererMode = rendererMode' in galaxy_source
        and 'renderer.domElement.dataset.flowField = rendererMode === "memory-starfield" ? "enabled" : "legacy-off"' in galaxy_source
        and "STARFIELD_QUALITY_SETTINGS" in galaxy_source
        and "createFlowTrailSegments" in galaxy_source
        and "updateMemoryStarfieldFlow" in galaxy_source
        and "memory-starfield-flow-field-trajectories" in galaxy_source
        and "memoryStarfieldSignalKind" in galaxy_source
        and '"black-hole"' in galaxy_source
        and '"proto-star"' in galaxy_source
        and "fallbackMode: rendererMode === \"legacy\" ? \"legacy\" : starfieldQuality === \"low\" ? \"low-quality\" : \"webgl\"" in galaxy_source
        and "Flow Field quality selector" in galaxy_source
        and "低质量 fallback 模式" in galaxy_source
        and ".galaxy-renderer-toggle" in css_source
        and ".galaxy-quality-tabs" in css_source
        and ".galaxy-flow-control" in css_source,
        "galaxy_stage4_1_rendering_integration_ready",
        "Galaxy has a default Memory Starfield renderer behind a rollback flag, Flow Field trajectories, quality fallback controls, semantic signal markers, and legacy mode",
        "Galaxy Stage 4.1 feature flag, Flow Field renderer, quality fallback, semantic signal markers, or legacy rollback path is missing",
    )
    require(
        checks,
        "product_target: Memory Atlas v1.1.5" in model_params_source
        and "cluster_mass:" in model_params_source
        and "particle_attributes:" in model_params_source
        and "terrain:" in model_params_source
        and "recency_half_life_days" in model_params_source
        and "importance_to_mass_scale" in model_params_source
        and "quality_settings:" in model_params_source
        and "model_parameters.memory_starfield.yaml?raw" in starfield_params_source
        and "parseYamlScalarPaths" in starfield_params_source
        and "MEMORY_STARFIELD_PARAMS" in starfield_params_source
        and "MemoryTerrainType" in starfield_params_source
        and "STARFIELD_QUALITY_SETTINGS = MEMORY_STARFIELD_PARAMS.qualitySettings" in galaxy_source
        and "function memoryStarfieldMass" in galaxy_source
        and "memoryStarfieldRecencyScore" in galaxy_source
        and "memoryStarfieldConfidenceScore" in galaxy_source
        and "function memoryStarfieldParticleAttributes" in galaxy_source
        and "function memoryTerrainType" in galaxy_source
        and "function buildTerrainSummary" in galaxy_source
        and "memory-starfield-terrain-layer" in galaxy_source
        and "terrainFeatureCount" in galaxy_source
        and "parameterSource: MEMORY_STARFIELD_PARAMS.parameterSource" in galaxy_source
        and "starfieldMode === \"analysis\"" in galaxy_source
        and "Starfield mode selector" in galaxy_source
        and 'className="galaxy-terrain-panel"' in galaxy_source
        and ".galaxy-terrain-panel" in css_source
        and ".terrain-row[data-terrain-type=\"ridge\"]" in css_source
        and ".terrain-row[data-terrain-type=\"fault-line\"]" in css_source,
        "galaxy_stage4_2_data_mapping_ready",
        "Galaxy Stage 4.2 maps mass, particle attributes, trajectory strength, quality settings, and Memory Terrain from the v1.1.5 parameter file with an explainable terrain panel",
        "Galaxy Stage 4.2 data mapping may still be hardcoded or lack parameter-backed mass, particle attributes, terrain layer, analysis panel, or audit signal",
    )
    require(
        checks,
        "function updateHoverPreview" in galaxy_source
        and "hoveredIdRef.current = item.node.id" in galaxy_source
        and "setHoverPreview({" in galaxy_source
        and "function onPointerUp" in galaxy_source
        and "if (item) onSelectNode(item.node)" in galaxy_source
        and "function updateCameraFocus" in galaxy_source
        and "camera.position.lerp(cameraTargetPosition" in galaxy_source
        and "MAX_FOCUS_VISIBLE_NEIGHBORS" in galaxy_source
        and "hiddenNeighborCount" in galaxy_source
        and "primaryNeighborCards" in galaxy_source
        and "const [flowPaused, setFlowPaused]" in galaxy_source
        and "flowPausedRef" in galaxy_source
        and "dataset.flowFrozen" in galaxy_source
        and "Freeze Flow Field" in galaxy_source
        and "Resume Flow Field" in galaxy_source
        and "if (flowPausedRef.current) return;" in galaxy_source
        and "const frozen = rendererMode === \"memory-starfield\" && flowPausedRef.current" in galaxy_source
        and "type StarfieldViewMode = \"presentation\" | \"analysis\"" in galaxy_source
        and "Starfield mode selector" in galaxy_source
        and "Presentation Mode" in galaxy_source
        and "Analysis Mode" in galaxy_source
        and "starfieldMode === \"analysis\"" in galaxy_source
        and "Starfield formula summary" in galaxy_source
        and "Analysis inspector summary" in galaxy_source
        and "flowPaused:" in galaxy_source
        and "starfieldMode:" in galaxy_source
        and ".galaxy-mode-tabs" in css_source
        and ".terrain-formula-grid" in css_source
        and ".terrain-inspector-strip" in css_source,
        "galaxy_stage4_3_interaction_ready",
        "Galaxy Stage 4.3 preserves transient hover preview and capped click focus, adds Freeze/Resume Flow, and exposes Presentation/Analysis mode with formula, terrain legend and Inspector context",
        "Galaxy Stage 4.3 interaction may lack transient hover preview, capped click focus, Freeze/Resume Flow, Presentation/Analysis mode, formula legend or Inspector context",
    )
    require(
        checks,
        "sampleWidth" in galaxy_source
        and "sampleHeight" in galaxy_source
        and "gl.readPixels(sampleX, sampleY, sampleWidth, sampleHeight" in galaxy_source
        and "gl.finish()" not in galaxy_source,
        "galaxy_pixel_signal_is_sampled",
        "WebGL render signal uses bounded pixel sampling and avoids blocking gl.finish",
        "Galaxy render signal may still block on full-frame pixel reads",
    )
    require(
        checks,
        ".galaxy-hud {" in css_source
        and "flex-wrap: wrap;" in css_source
        and "max-width: calc(100% - 28px);" in css_source
        and ".galaxy-hud div" in css_source
        and "max-width: min(148px, calc(50% - 5px));" in css_source
        and "overflow: hidden;" in css_source
        and "overflow-wrap: anywhere;" in css_source
        and "@media (min-width: 721px) and (max-width: 1100px)" in css_source
        and "grid-template-columns: minmax(0, 1fr) minmax(260px, 300px);" in css_source
        and "@media (min-width: 721px) and (max-width: 1100px) and (max-height: 700px)" in css_source
        and "grid-template-rows: auto auto minmax(260px, 1fr);" in css_source
        and ".galaxy-view > .surface-heading" in css_source
        and ".galaxy-view > .delta-strip" in css_source
        and ".galaxy-scene {\n    min-height: 260px;" in css_source
        and "max-width: calc(100% - 20px);" in css_source,
        "galaxy_compact_layout_keeps_hud_visible",
        "Galaxy keeps a visible scene and wraps HUD cards inside the canvas on tablet-width and low-height viewports",
        "Galaxy compact layout may still collapse the scene or clip HUD cards on tablet/low-height viewports",
    )
    require(
        checks,
        "数据导图" in app_source
        and "function DataGuideMap" in app_source
        and "function buildDataGuideLayout" in app_source
        and "dataGuideFrameForNode" in app_source
        and "dataGuideEdgePath" in app_source
        and 'className="data-guide-canvas"' in app_source
        and 'aria-label="数据导图框架"' in app_source
        and '"source" | "profile" | "project" | "action"' in app_source
        and "<text" in data_guide_node
        and "data-guide-node-card" in data_guide_node
        and "data-guide-node-title" in data_guide_node
        and "aria-label={`${item.frameTitle} · ${item.typeLabel} · ${item.node.label}`}" in data_guide_node
        and ".data-guide-frame-title" in css_source
        and ".data-guide-node-card" in css_source
        and ".data-guide-links path" in css_source
        and "marker-end: url(\"#dataGuideArrow\")" in css_source
        and "数据导图" in readme
        and "来源、画像、项目决策和行动机会" in readme,
        "data_guide_framework_ready",
        "Data Guide uses a readable framework layout: source/theme, profile/preference, project/decision, and action/opportunity columns",
        "Data Guide framework layout, labels, links, styles, or README contract are missing",
    )
    require(
        checks,
        'const ObsidianGraphScene = lazy(() => import("./components/ObsidianGraphScene")' in app_source
        and "function ObsidianGraphScene" in obsidian_source
        and "function useObsidianForceGraph" in obsidian_source
        and "function stepObsidianForceSimulation" in obsidian_source
        and "buildObsidianDataset" in obsidian_source
        and "graphDepthMap" in obsidian_source
        and "creationOrderMap" in obsidian_source
        and 'role="application"' in obsidian_source
        and "onWheel={handleWheel}" in obsidian_source
        and "onPointerDown={handleCanvasPointerDown}" in obsidian_source
        and "onPointerMove={handleCanvasPointerMove}" in obsidian_source
        and "onContextMenu" in obsidian_source
        and "activeNeighborhood" in obsidian_source
        and "markerEnd={settings.showArrows" in obsidian_source
        and "文字淡出阈值" in obsidian_source
        and "节点大小" in obsidian_source
        and "连线粗细" in obsidian_source
        and "中心力" in obsidian_source
        and "排斥力" in obsidian_source
        and "链接力" in obsidian_source
        and "链接距离" in obsidian_source
        and "搜索文件" in obsidian_source
        and "标签" in obsidian_source
        and "附件" in obsidian_source
        and "仅现有文件" in obsidian_source
        and "孤立节点" in obsidian_source
        and "全局图" in obsidian_source
        and "局部图" in obsidian_source
        and "useState(false)" in obsidian_source
        and "obsidian-settings-collapsed" in obsidian_source
        and "onClose={() => setSettingsOpen(false)}" in obsidian_source
        and "Focus - Connectivity" in obsidian_source
        and "buildFocusConnectivity" in obsidian_source
        and "displayNodeLabel" in obsidian_source
        and "memoryKeyword" in obsidian_source
        and "层级" in obsidian_source
        and "主题" in obsidian_source
        and ".obsidian-graph-canvas" in css_source
        and ".obsidian-settings-panel" in css_source
        and ".obsidian-settings-collapsed" in css_source
        and ".obsidian-focus-connectivity" in css_source
        and ".obsidian-node-label" in css_source
        and ".obsidian-link.focused" in css_source
        and ".obsidian-context-menu" in css_source,
        "obsidian_graph_matches_core_graph_view_contract",
        "Obsidian Graph is a lazy-loaded force-directed scene with zoom, pan, drag, context menu, local depth, collapsible settings, Focus-Connectivity metrics, and level-theme-keyword node labels",
        "Obsidian Graph may still be a static SVG/list or may lack interaction, collapsible settings, Focus-Connectivity metrics, or level-theme-keyword labels",
    )
    require(
        checks,
        '"validate:stage9-obsidian": "node scripts/validate_stage9_obsidian_iteration.cjs"' in read_text(repo_root / "apps/memory-atlas/package.json")
        and "LOCAL_GRAPH_PRIMARY_NODE_LIMIT" in obsidian_source
        and "LOCAL_GRAPH_SECONDARY_NODE_LIMIT" in obsidian_source
        and "LOCAL_GRAPH_CLUSTER_MEMBER_LIMIT" in obsidian_source
        and "buildLocalGraphPlan" in obsidian_source
        and 'sharedFocus.sourceView === "galaxy"' in obsidian_source
        and "data-local-graph-mode" in obsidian_source
        and "data-galaxy-cluster-focus" in obsidian_source
        and "data-hidden-local-neighbors" in obsidian_source
        and "data-label-budget" in obsidian_source
        and "labelVisibilityRule" in obsidian_source
        and "data-label-rule" in obsidian_source
        and "Local Graph Budget" in obsidian_source
        and "sharedFocus={sharedState.focus}" in app_source
        and ".obsidian-local-budget" in css_source
        and '.obsidian-node-label[data-label-rule="local-neighbor"]' in css_source,
        "stage9_1_obsidian_graph_iteration_ready",
        "Stage 9.1 Obsidian Graph adds bounded local graph neighborhoods, zoom/focus label rules, and Galaxy cluster shared-focus synchronization",
        "Stage 9.1 Obsidian Graph local budget, label rules, Galaxy shared-focus sync, styles, or validator script are missing",
    )
    require(
        checks,
        '"validate:stage9-visual-semantics": "node scripts/validate_stage9_visual_semantics.cjs"' in read_text(repo_root / "apps/memory-atlas/package.json")
        and "Memory Weather v2" in app_source
        and "data-memory-weather-v2" in app_source
        and "buildMemoryWeatherV2" in app_source
        and "memory-river-roi-gradient" in app_source
        and "buildMemoryRiverRoiGradient" in app_source
        and 'data-roi-gradient="capability-growth"' in app_source
        and "Memory Terrain v2" in galaxy_source
        and "data-memory-terrain-v2" in galaxy_source
        and "buildGalaxyRoiGradientSummary" in galaxy_source
        and "galaxy-roi-gradient-panel" in galaxy_source
        and 'data-roi-gradient="galaxy-analysis"' in galaxy_source
        and ".home-weather-v2-scores" in css_source
        and ".galaxy-roi-gradient-panel" in css_source
        and ".memory-river-roi-gradient" in css_source,
        "stage9_2_visual_semantics_enrichment_ready",
        "Stage 9.2 adds explainable Memory Weather v2, Analysis-only Memory Terrain v2, Galaxy ROI gradient, and Memory River ROI/capability gradient",
        "Stage 9.2 visual semantic enrichment source, styles, or validator script are missing",
    )
    require(
        checks,
        "WebGL 正常时不叠加 HTML 点层" in readme
        and "不透明 WebGL 背景" in readme
        and "WebGL 内部程序化星云纹理" in readme
        and "贡献网格一屏优先" in readme
        and "短长方形连续渐变趋势条" in readme
        and "0、低频、中频、高频明显分离" in readme
        and "log 映射" in readme
        and "平滑蓝色系色带" in readme
        and "冷蓝灰" in readme
        and "深海蓝" in readme
        and "冰蓝" in readme
        and "避免黄色、橙色、脏绿和刺眼蓝紫断层" in readme
        and "宽度约等于日表格下 3 列" in readme
        and "日/周必须共用同一个全年 7 行 x 52-54 列坐标面" in readme
        and "月视图保留连续两年 24 列坐标面" in readme
        and "年视图使用左右并排的两张年度对比卡片" in readme
        and "同源同色阶的 7 个日段" in readme
        and "连续渐变实现" in readme
        and "周、月内部趋势保持从上到下读取" in readme
        and "月格内部按每日颗粒度纵向排列" in readme
        and "12 个月从左到右的横向热度条" in readme
        and "年度对比卡片" in readme
        and "季度轴" in readme
        and "不得在狭窄月柱内部显示" in readme
        and "不能退回" in readme
        and "大色块年视图" in readme
        and "尺度按钮和增量指标合并" in readme
        and "Galaxy 低高度视口保留最小画布高度" in readme
        and "HUD 自动换行且不裁切" in readme
        and "数据导图使用框架卡片" in readme
        and "来源、画像、项目决策和行动机会" in readme
        and "点击卡片、title、aria 和 Inspector" in readme
        and "Obsidian Graph 按 Obsidian Graph View 的文字淡出阈值显示节点标签" in readme
        and "hover 邻接高亮" in readme
        and "层级 · 主题 · 关键词" in readme
        and "Focus - Connectivity" in readme
        and "图谱设置必须可折叠" in readme
        and "center/repel/link force controls" in readme
        and "不能只显示模板句" in readme
        and "同类重复" in readme
        and "未来回答与个性化" in readme
        and "执行规则与验收标准" in readme
        and "降权/不再默认使用" in readme
        and "Word Cloud: 词云洞察是独立导航板块" in readme
        and "Heatmap" in readme
        and "Bubble Chart" in readme
        and "Word Cloud" in readme
        and "Summary & Iteration" in readme
        and "总结与迭代是独立导航板块" in readme
        and "frontend proposal refs" in readme
        and "sensitivity detail fields" in readme,
        "visual_requirements_documented",
        "README documents the no-ghost-layer, full-grid, Data Guide framework, Obsidian Graph View, slim visual snapshot, and Summary & Iteration contracts",
        "README does not document the current visual acceptance contracts",
    )

    failed = [check for check in checks if check["status"] != "PASS"]
    if failed:
        raise VisualAcceptanceError(json.dumps({"status": "FAIL", "checks": checks}, ensure_ascii=False, indent=2))
    return {"status": "PASS", "checks": checks}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas visual acceptance criteria.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = audit_visual_acceptance(args.repo_root)
    except VisualAcceptanceError as exc:
        print(exc, file=__import__("sys").stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
