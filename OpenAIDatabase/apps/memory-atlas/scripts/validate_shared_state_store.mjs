#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  atlasFiltersFromSharedState,
  clearSharedAtlasFilter,
  createSharedAtlasState,
  sharedAtlasReducer,
} from "../src/state/sharedAtlasState.ts";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const runtimeSourcePaths = [
  "src/providers/AtlasWorkspaceProvider.tsx",
  "src/features/settings/InteractionLens.tsx",
  "src/features/settings/InspectorWorkspace.tsx",
  "src/features/overview/HomeOverviewView.tsx",
  "src/features/assets/GalaxyView.tsx",
  "src/features/assets/TimelineView.tsx",
];
const appSource = runtimeSourcePaths
  .map((relativePath) => readFileSync(resolve(appRoot, relativePath), "utf8"))
  .join("\n");
const stateSource = readFileSync(resolve(appRoot, "src/state/sharedAtlasState.ts"), "utf8");
const cssSource = readFileSync(resolve(appRoot, "src/styles.css"), "utf8");
const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");

const failures = [];

unitTestSelectionSchema(failures);
unitTestFilterSchema(failures);
unitTestSyncActions(failures);
validateSourceContracts(failures);

if (failures.length) {
  console.error(JSON.stringify({ ok: false, failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  ok: true,
  schema_version: "memory_atlas_shared_state.v1",
  checks: [
    "selection schema keeps node, cluster, record, time range and signal",
    "filter schema clears one filter without mutating source data",
    "sync actions share focus across home, galaxy, timeline, inspector and ROI dashboard",
    "Runtime surfaces expose shared-state data attributes for interaction verification",
  ],
}, null, 2));

function unitTestSelectionSchema(failures) {
  const node = sampleNode();
  const state = createSharedAtlasState({ activeView: "home", filters: sampleFilters() });
  const selected = sharedAtlasReducer(state, { type: "select_node", node, source: "galaxy" });
  if (selected.selection.nodeId !== node.id) failures.push("selection schema did not store selected node id");
  if (selected.selection.clusterId !== "cluster-agent-governance") failures.push("selection schema did not store selected cluster id");
  if (selected.selection.recordId !== node.memory_id) failures.push("selection schema did not store selected record id");
  if (selected.selection.signal !== "record") failures.push("selection schema did not record node signal");
  if (selected.sync.updatedBy !== "galaxy") failures.push("selection action did not record source view");
  if (selected.sync.loopGuard.mode !== "single-dispatch-reducer") failures.push("loop guard is not single-dispatch reducer");
}

function unitTestFilterSchema(failures) {
  const initialFilters = {
    query: "agent",
    source: "codex",
    tier: "核心画像",
    category: "decision",
    theme: "cluster-agent-governance",
  };
  const state = createSharedAtlasState({ activeView: "home", filters: initialFilters });
  const cleared = clearSharedAtlasFilter(state.filters, "source");
  if (cleared.source !== "all") failures.push("clearing source filter did not reset source to all");
  if (cleared.tier !== "核心画像" || cleared.category !== "decision" || cleared.theme !== "cluster-agent-governance") {
    failures.push("clearing source filter unexpectedly changed unrelated filters");
  }
  const afterAction = sharedAtlasReducer(state, { type: "clear_filter", key: "theme", source: "home" });
  const atlasFilters = atlasFiltersFromSharedState(afterAction);
  if (atlasFilters.theme !== "all") failures.push("clear_filter action did not reset theme");
  if (atlasFilters.source !== "codex") failures.push("clear_filter action mutated source unexpectedly");
  if (state.filters.theme !== "cluster-agent-governance") failures.push("clear_filter mutated the previous state object");
}

function unitTestSyncActions(failures) {
  const node = sampleNode();
  const range = sampleTimeRange();
  const state = createSharedAtlasState({ activeView: "home", filters: sampleFilters() });
  const selected = sharedAtlasReducer(state, { type: "select_node", node, source: "galaxy" });
  const ranged = sharedAtlasReducer(selected, { type: "select_time_range", range, source: "timeline" });
  for (const target of ["home", "galaxy", "timeline", "inspector", "roiDashboard"]) {
    if (ranged.focus[target].nodeId !== node.id) failures.push(`sync target ${target} lost node focus`);
    if (ranged.focus[target].clusterId !== "cluster-agent-governance") failures.push(`sync target ${target} lost cluster focus`);
    if (ranged.focus[target].timeRangeId !== range.id) failures.push(`sync target ${target} lost time range`);
  }
  if (ranged.selection.signal !== "time_range") failures.push("time range action did not mark time_range signal");
  if (ranged.sync.revision !== 2) failures.push(`sync revision expected 2, got ${ranged.sync.revision}`);
  const switched = sharedAtlasReducer(ranged, { type: "switch_view", view: "home", source: "timeline" });
  if (switched.focus.home.nodeId !== node.id || switched.mode.activeView !== "home") {
    failures.push("switch_view broke shared focus or active view state");
  }
}

function validateSourceContracts(failures) {
  const requiredStateNeedles = [
    "export interface SharedAtlasSelectionState",
    "export interface SharedAtlasFilterState",
    "export interface SharedAtlasFocusState",
    "export function sharedAtlasReducer",
    "clearSharedAtlasFilter",
    "roi: SharedAtlasRoiFilter",
    "loopGuard",
  ];
  const requiredAppNeedles = [
    "useReducer(",
    "sharedAtlasReducer",
    "data-shared-state={sharedState.schema_version}",
    "data-shared-focus-node={sharedState.focus.home.nodeId ?? \"\"}",
    "data-shared-focus-node={sharedState.focus.galaxy.nodeId ?? \"\"}",
    "data-shared-focus-node={sharedState.focus.timeline.nodeId ?? \"\"}",
    "data-shared-focus-node={sharedState.focus.inspector.nodeId ?? \"\"}",
    "data-sync-revision={sharedState.sync.revision}",
    "dispatchSharedState({ type: \"select_node\", node, source: activeView })",
    "dispatchSharedState({ type: \"select_time_range\", range, source: \"timeline\" })",
    "dispatchSharedState({ type: \"clear_filter\", key, source: activeView })",
  ];
  const requiredCssNeedles = [
    ".lens-state-strip",
    ".home-shared-focus-strip",
  ];
  if (!hasAll(stateSource, requiredStateNeedles)) failures.push("shared-state source lacks required schema/reducer/filter contracts");
  if (!hasAll(appSource, requiredAppNeedles)) failures.push("Runtime modules do not expose all shared-state sync bindings");
  if (!hasAll(cssSource, requiredCssNeedles)) failures.push("shared-state UI status styles are missing");
  if (!packageSource.includes('"validate:shared-state": "node --experimental-strip-types scripts/validate_shared_state_store.mjs"')) {
    failures.push("package.json lacks validate:shared-state script");
  }
  if (!visualAudit.includes("stage6_1_shared_state_store_ready")) {
    failures.push("visual acceptance audit lacks Stage 6.1 shared-state hook");
  }
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

function sampleFilters() {
  return {
    query: "",
    source: "all",
    tier: "all",
    category: "all",
    theme: "all",
  };
}

function sampleNode() {
  return {
    id: "memory-agent-governance-001",
    kind: "memory",
    label: "Agent governance",
    memory_id: "mem-agent-governance-001",
    category: "decision",
    memory_tier: "核心画像",
    visual: {
      cluster: "cluster-agent-governance",
    },
  };
}

function sampleTimeRange() {
  return {
    id: "range-2026-06",
    source: "memory-river-brush",
    startDate: "2026-06-01",
    endDate: "2026-06-30",
    label: "2026-06-01 - 2026-06-30",
    eventCount: 9,
    decisionCount: 3,
    coreMemoryCount: 2,
    topTheme: "agent-governance",
  };
}
