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
    obsidian_source = read_text(repo_root / "apps/memory-atlas/src/components/ObsidianGraphScene.tsx")
    css_source = read_text(repo_root / "apps/memory-atlas/src/styles.css")
    data_builder_source = read_text(repo_root / "scripts/build_memory_atlas_data.py")
    readme = read_text(repo_root / "README.md")
    atlas_path = repo_root / "data/derived/visualization/memory_atlas.json"
    atlas_source = atlas_path.read_text(encoding="utf-8") if atlas_path.exists() else ""

    graph_node = function_block(app_source, "GraphSvgNode", "Metric")
    timeline_view = function_block(app_source, "TimelineView", "ContributionGrid")
    contribution_grid = function_block(app_source, "ContributionGrid", "SearchReview")

    require(
        checks,
        'const wideView = activeView === "contribution"' in app_source
        and 'className={wideView ? "workspace contribution-workspace" : "workspace"}' in app_source
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
        and '<NodeInspector atlas={scopedAtlas} node={selectedNode} edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)} />' in app_source
        and "grid-template-columns: minmax(0, 1fr) 340px;" in css_source
        and ".content-grid.wide-view {\n    grid-template-columns: 1fr;" in css_source
        and ".period-related-list" in css_source,
        "selection_updates_right_detail_panel",
        "All visualization selections route into the right detail panel; contribution cells expose period details and related memory drill-downs",
        "Selection state does not consistently update the right detail panel for nodes, filters, or contribution grid cells",
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
        and 'className="year-trend-grid vertical-year-trend"' in contribution_grid
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
        and ".year-trend-grid.vertical-year-trend" in css_source
        and "height: 100%;" in css_source
        and "aspect-ratio: auto;" in css_source
        and ".year-cell.year-summary-card" in css_source
        and ".year-month-track" in css_source
        and ".year-month-bar" in css_source
        and ".year-month-axis" in css_source
        and ".year-month-bar em" not in css_source
        and "grid-template-rows: repeat(12, minmax(0, 1fr));" in css_source
        and "width: var(--month-height, 9%);" in css_source
        and "const periodKey = cell.date" in contribution_grid,
        "contribution_month_year_grid_contract",
        "Month mode keeps 24 selectable month columns with readable labels and smooth internal daily trends; year mode uses vertically stacked selectable year comparison cards with month bar trends, a clean quarter axis, and year summary metrics",
        "Month/year grid contract is missing 24 month columns, smooth internal daily trends, vertically stacked year comparison cards, month bars, or year summary metrics",
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
        and "Agent 结构化字段 / 原始摘要" in app_source
        and "未来回答与个性化" in app_source
        and "执行规则与验收标准" in app_source
        and "降权/不再默认使用" in app_source
        and ".human-overview" in css_source
        and ".human-node-card" in css_source,
        "memory_atlas_has_human_facing_summary",
        "Inspector and search views expose human-readable topics, actions, reminders, opportunities, folded agent/source summaries, deduped display rows, and recommendation buckets",
        "Memory Atlas may still expose repeated template text or mostly agent/internal metadata instead of human-facing memory conclusions",
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
        "<text" not in graph_node
        and ".graph-node-label" not in app_source
        and ".graph-node-label" not in css_source
        and "isGraphParentNode(item.node)" in graph_node
        and "function isGraphParentNode" in app_source
        and 'node.kind === "theme" || node.kind === "project" || node.kind === "category" || node.kind === "tier"' in app_source
        and "aria-label={`${translateKind(item.node.kind)} · ${item.node.label}`}" in graph_node
        and "<title>{`${translateKind(item.node.kind)} · ${item.node.label}`}</title>" in graph_node
        and "className=\"graph-node-halo\"" in graph_node
        and "className=\"graph-node-core\"" in graph_node
        and graph_node.count("<circle") == 2
        and "stdDeviation=\"1.25\"" in app_source
        and '<g opacity="0.13">' in app_source
        and ".graph-node.parent-node .graph-node-core" in css_source,
        "graph_nodes_have_no_internal_text_labels",
        "Notion map graph nodes keep the picture clean: no internal text labels; details stay in title, aria, and Inspector",
        "Notion graph nodes may still render internal text labels or may lack title/aria/detail affordances",
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
        and ".obsidian-graph-canvas" in css_source
        and ".obsidian-settings-panel" in css_source
        and ".obsidian-node-label" in css_source
        and ".obsidian-link.focused" in css_source
        and ".obsidian-context-menu" in css_source,
        "obsidian_graph_matches_core_graph_view_contract",
        "Obsidian Graph is a lazy-loaded force-directed interactive scene with zoom, pan, drag, context menu, local depth, filters, groups, display controls, and force controls",
        "Obsidian Graph may still be a static SVG/list or may lack core Graph View interaction/settings contracts",
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
        and "年视图改为上下纵向排列的两张年度对比卡片" in readme
        and "同源同色阶的 7 个日段" in readme
        and "连续渐变实现" in readme
        and "周、月、年内部趋势必须从上到下读取" in readme
        and "月格内部按每日颗粒度纵向排列" in readme
        and "12 个月纵向热度带" in readme
        and "年度对比卡片" in readme
        and "季度轴" in readme
        and "不得在狭窄月柱内部显示" in readme
        and "不能退回" in readme
        and "大色块年视图" in readme
        and "尺度按钮和增量指标合并" in readme
        and "Galaxy 低高度视口保留最小画布高度" in readme
        and "HUD 自动换行且不裁切" in readme
        and "图内节点不渲染文字标签" in readme
        and "详情通过 title、aria 和 Inspector 查看" in readme
        and "Obsidian Graph 按 Obsidian Graph View 的文字淡出阈值显示节点标签" in readme
        and "hover 邻接高亮" in readme
        and "center/repel/link force controls" in readme
        and "不能只显示模板句" in readme
        and "同类重复" in readme
        and "未来回答与个性化" in readme
        and "执行规则与验收标准" in readme
        and "降权/不再默认使用" in readme
        and "Word Cloud: 词云洞察是独立导航板块" in readme
        and "Heatmap" in readme
        and "Bubble Chart" in readme
        and "Word Cloud" in readme,
        "visual_requirements_documented",
        "README documents the no-ghost-layer, full-grid, Notion no-label, and Obsidian Graph View interaction contracts",
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
