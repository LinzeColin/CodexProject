#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const appSource = readFileSync(resolve(appRoot, "src/App.tsx"), "utf8");
const cssSource = readFileSync(resolve(appRoot, "src/styles.css"), "utf8");
const visualFlags = readFileSync(resolve(appRoot, "src/config/visualFlags.ts"), "utf8");
const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");
const modelParams = readFileSync(resolve(repoRoot, "config/visualization/model_parameters.memory_river.yaml"), "utf8");

const checks = [];

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

requireCheck(
  "timeline_renderer_feature_flag",
  hasAll(visualFlags, [
    'export type TimelineRendererMode = "memory-river" | "legacy"',
    'DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river"',
    'TIMELINE_RENDERER_STORAGE_KEY = "memory-atlas.timeline-renderer"',
    "getInitialTimelineRendererMode",
    "persistTimelineRendererMode",
    "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
    'params.get("timelineRenderer") ?? params.get("timeline")',
    'value === "memory-river" || value === "river" || value === "new"',
    'value === "legacy" || value === "old" || value === "timeline"',
  ]) && hasAll(appSource, [
    "getInitialTimelineRendererMode",
    "persistTimelineRendererMode",
    "timeline-renderer-toggle",
    "data-timeline-renderer={timelineRendererMode}",
    'updateTimelineRendererMode("memory-river")',
    'updateTimelineRendererMode("legacy")',
  ]),
  "timeline renderer supports memory-river default, legacy rollback, URL/env/localStorage flag paths, and in-app toggle",
  "timeline renderer feature flag, default, persistence, URL/env support, or legacy rollback toggle is missing",
);

requireCheck(
  "utc_time_scale_contract",
  hasAll(appSource, [
    "function parseTimelineUtcDay",
    "function timelineUtcMs",
    "parseTimelineUtcDay(event.date)",
    "timelineUtcMs(minAllDay)",
    "timelineUtcMs(maxAllDay)",
    "utcDate: toDayKey(event.day)",
    'data-utc-time-scale="true"',
    "UTC {display.cursorLabel}",
  ]),
  "timeline layout parses date-only values into UTC days and positions ticks, events, cursor and memory-river labels on UTC milliseconds",
  "UTC parse/helper evidence or memory-river UTC canvas contract is missing",
);

requireCheck(
  "macro_meso_micro_river_lanes",
  hasAll(appSource, [
    'type MemoryRiverLevel = "Macro" | "Meso" | "Micro"',
    "interface MemoryRiverLane",
    "function buildMemoryRiverLayout",
    "{ level: \"Macro\", note:",
    "{ level: \"Meso\", note:",
    "{ level: \"Micro\", note:",
    "memoryRiverGroup(event, spec.level)",
    "buildMemoryRiverPath",
    "memoryRiverMarkerKind",
    "memory-river-canvas",
    "memory-river-level",
    "memory-river-lane",
    "memory-river-marker",
  ]) && hasAll(cssSource, [
    ".memory-river-canvas",
    ".memory-river-level-label",
    ".memory-river-lane-flow",
    ".memory-river-lane-label",
    ".memory-river-marker",
    ".memory-river-marker.proto-star",
    ".memory-river-marker.black-hole",
  ]),
  "Memory River renders Macro/Meso/Micro levels, grouped lane paths, lane labels, and black-hole/proto-star/event markers with dedicated styles",
  "Memory River level/lane/marker implementation or styles are missing",
);

requireCheck(
  "acceptance_audit_is_wired",
  packageSource.includes('"validate:memory-river-rendering": "node scripts/validate_memory_river_rendering.mjs"')
    && visualAudit.includes("timeline_stage5_1_river_rendering_ready")
    && visualAudit.includes("memory-river-canvas")
    && visualAudit.includes("data-utc-time-scale")
    && visualAudit.includes("buildMemoryRiverLayout"),
  "package script and source-level visual acceptance audit both cover Stage 5.1 Memory River rendering",
  "package script or visual acceptance audit hook for Stage 5.1 Memory River rendering is missing",
);

requireCheck(
  "memory_river_parameters_match_phase",
  hasAll(modelParams, [
    "schema_version: memory_river_params.v1",
    'stage: "5.2"',
    'task: "5.2 Memory River Interaction"',
    "renderer_default: memory-river",
    "legacy_renderer: legacy",
    "use_utc_scale: true",
    "date_parse_contract:",
    "label: Macro",
    "label: Meso",
    "label: Micro",
    "marker_cap: 64",
    "pan_enabled: true",
    "brush_enabled: true",
    "click_event_card_enabled: true",
    "reduced_motion_suppresses_feedback: true",
  ]),
  "Memory River model parameters document the current Phase 5.2 renderer, UTC scale, lane grouping, marker cap, rollback, and enabled interaction boundaries",
  "Memory River model parameters are missing Phase 5.2 status, UTC/lane/marker values, rollback, or interaction boundaries",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
