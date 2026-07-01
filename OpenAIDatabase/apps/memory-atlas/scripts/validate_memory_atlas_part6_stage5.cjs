#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const checks = [];

function pass(name, evidence, details) {
  checks.push({ name, status: "PASS", evidence, ...(details ? { details } : {}) });
}

function assertCondition(condition, name, evidence, failure, details = {}) {
  if (condition) {
    pass(name, evidence, details);
    return;
  }
  const error = new Error(failure);
  error.details = details;
  throw error;
}

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function readAppFile(relativePath) {
  return fs.readFileSync(path.join(appRoot, relativePath), "utf8");
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    env: options.env || process.env,
    encoding: "utf8",
    stdio: "pipe",
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function walkFiles(rootDir, skipNames = new Set()) {
  const result = [];
  for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
    if (skipNames.has(entry.name)) continue;
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      result.push(...walkFiles(fullPath, skipNames));
    } else {
      result.push(fullPath);
    }
  }
  return result;
}

function validateStage51Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage5_1_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 5.1 is review-passed",
      "5.1.1 Timeline Feature Flag",
      "5.1.2 UTC Time Scale",
      "5.1.3 Theme River Lanes",
      "memory-river",
      "legacy",
      "rollback",
      "parseTimelineUtcDay",
      "timelineUtcMs",
      "Macro / Meso / Micro",
      "timeline_stage5_1_river_rendering_ready",
      "Preview cleanup",
      "Stage 5.1 did not",
    ]),
    "part6_phase_5_1_review_current",
    "Stage 5.1 review proves Memory River default renderer, legacy rollback, UTC scale, river lanes, browser evidence and safety boundaries",
    "Stage 5.1 review is incomplete",
  );
}

function validateStage52Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage5_2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 5.2 is review-passed",
      "5.2.1 Zoom / Pan",
      "5.2.2 Brush Range Selection",
      "5.2.3 Hover / Click Event Card",
      "5.2.4 Multimodal Feedback",
      "Pan",
      "Brush",
      "redacted derived event",
      "Reduced Motion",
      "timeline_stage5_2_river_interaction_ready",
      "Preview cleanup",
      "Stage 5.2 did not",
    ]),
    "part6_phase_5_2_review_current",
    "Stage 5.2 review proves pan/brush, selected-range sync, redacted event cards, safe feedback settings, browser evidence and safety boundaries",
    "Stage 5.2 review is incomplete",
  );
}

function validateStage53Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage5_3_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 5.3 is review-passed",
      "5.3.1 Black Hole Lifecycle",
      "5.3.2 Proto-Star Lifecycle",
      "5.3.3 Stale / Deprecated Layer",
      "black-hole-lifecycle",
      "proto-star-lifecycle",
      "stale-deprecated",
      "timeline_stage5_3_evidence_layers_ready",
      "redacted timeline/node snapshot",
      "Preview cleanup",
      "Stage 5.3 did not",
    ]),
    "part6_phase_5_3_review_current",
    "Stage 5.3 review proves black-hole lifecycle, proto-star lifecycle, stale/deprecated fade layer, browser evidence and safety boundaries",
    "Stage 5.3 review is incomplete",
  );
}

function validateStage5OverallReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage5_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 5 is review-passed",
      "5.1 River Rendering",
      "5.2 River Interaction",
      "5.3 Evidence Layers",
      "production Timeline now defaults to Memory River",
      "legacy renderer rollback path",
      "timeline_stage5_1_river_rendering_ready",
      "timeline_stage5_2_river_interaction_ready",
      "timeline_stage5_3_evidence_layers_ready",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
      "No direct frontend writeback was added",
      "The reviewed Stage 5 state is ready to upload",
    ]),
    "part6_stage5_overall_review_current",
    "Stage 5 overall review proves 5.1/5.2/5.3 inclusion, integrated acceptance, safety boundary and historical upload gate",
    "Stage 5 overall review is incomplete",
  );
}

function validateMemoryRiverRuntime() {
  const app = readAppFile("src/App.tsx");
  const css = readAppFile("src/styles.css");
  const flags = readAppFile("src/config/visualFlags.ts");
  const params = readRepoFile("config/visualization/model_parameters.memory_river.yaml");

  assertCondition(
    hasAll(flags, [
      "export type TimelineRendererMode = \"memory-river\" | \"legacy\"",
      "DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = \"memory-river\"",
      "TIMELINE_RENDERER_STORAGE_KEY = \"memory-atlas.timeline-renderer\"",
      "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
      "getInitialTimelineRendererMode",
      "persistTimelineRendererMode",
    ]) && hasAll(app, [
      "getInitialTimelineRendererMode",
      "persistTimelineRendererMode",
      "timeline-renderer-toggle",
      "data-timeline-renderer={timelineRendererMode}",
      "updateTimelineRendererMode(\"memory-river\")",
      "updateTimelineRendererMode(\"legacy\")",
    ]),
    "part6_stage5_1_renderer_flag_runtime",
    "Current Timeline runtime keeps memory-river as default renderer and preserves legacy rollback controls",
    "Stage 5.1 renderer flag or rollback runtime contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "function parseTimelineUtcDay",
      "function timelineUtcMs",
      "parseTimelineUtcDay(event.date)",
      "data-utc-time-scale=\"true\"",
      "type MemoryRiverLevel = \"Macro\" | \"Meso\" | \"Micro\"",
      "function buildMemoryRiverLayout",
      "function buildMemoryRiverPath",
      "function memoryRiverMarkerKind",
      "memory-river-canvas",
      "memory-river-level",
      "memory-river-lane",
      "memory-river-marker",
    ]) && hasAll(css, [
      ".memory-river-canvas",
      ".memory-river-level-label",
      ".memory-river-lane-flow",
      ".memory-river-lane-label",
      ".memory-river-marker",
    ]),
    "part6_stage5_1_rendering_runtime",
    "Current Timeline runtime exposes UTC scale, Macro/Meso/Micro river lanes and Memory River markers",
    "Stage 5.1 Memory River rendering runtime contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "type TimelineInteractionMode = \"pan\" | \"brush\"",
      "handleMemoryRiverPointerDown",
      "handleMemoryRiverPointerMove",
      "handleMemoryRiverPointerUp",
      "buildTimelineRangeSelection",
      "buildMemoryRiverRangeOverlay",
      "buildMemoryRiverDraftOverlay",
      "memory-river-selected-range",
      "memory-river-brush-draft",
      "timeline-range-chip",
      "lockedEventId",
      "lockMemoryRiverEvent",
      "memory-river-event-card",
      "redacted derived event",
      "interface TimelineFeedbackSettings",
      "pseudoHaptic: false",
      "audio: false",
      "Reduced Motion",
      "emitTimelineFeedback",
    ]) && hasAll(css, [
      ".memory-river-interaction-bar",
      ".river-mode-tabs",
      ".memory-river-selected-range rect",
      ".memory-river-brush-draft rect",
      ".memory-river-event-card",
      ".timeline-sync-pill",
    ]),
    "part6_stage5_2_interaction_runtime",
    "Current Timeline runtime exposes pan/brush, selected-range sync, redacted event card and safe feedback controls",
    "Stage 5.2 interaction runtime contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "type MemoryRiverEvidenceKind = \"black-hole-lifecycle\" | \"proto-star-lifecycle\" | \"stale-deprecated\"",
      "interface MemoryRiverEvidenceLayer",
      "buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes)",
      "buildBlackHoleLifecycleLayer",
      "buildProtoStarLifecycleLayer",
      "buildStaleDeprecatedLayer",
      "isMemoryRiverBlackHoleEvent",
      "isMemoryRiverProtoStarEvent",
      "isMemoryRiverStaleDeprecatedEvent",
      "isBlackHoleCandidate(event.node)",
      "isProtoStarCandidate(event.node, recentStart, latest)",
      "data-evidence-layers=\"black-hole-lifecycle proto-star-lifecycle stale-deprecated roi-gradient\"",
      "redacted derived signals",
    ]) && hasAll(css, [
      ".memory-river-evidence-layer.black-hole-lifecycle rect",
      ".memory-river-evidence-layer.proto-star-lifecycle path",
      ".memory-river-evidence-layer.stale-deprecated rect",
    ]),
    "part6_stage5_3_evidence_runtime",
    "Current Timeline runtime exposes black-hole lifecycle, proto-star lifecycle and stale/deprecated fade layers from redacted derived signals",
    "Stage 5.3 evidence-layer runtime contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "stage: \"5.3\"",
      "task: \"5.3 Evidence Layers\"",
      "review_status: stage_5_whole_stage_review_passed",
      "renderer_default: memory-river",
      "legacy_renderer: legacy",
      "use_utc_scale: true",
      "pan_enabled: true",
      "brush_enabled: true",
      "click_event_card_enabled: true",
      "black_hole_lifecycle_enabled: true",
      "proto_star_lifecycle_enabled: true",
      "stale_deprecated_fade_enabled: true",
      "raw_private_data_allowed: false",
      "writeback_allowed: false",
    ]),
    "part6_stage5_model_parameters_current",
    "Memory River parameters preserve Stage 5 whole-review status, rollback, interaction, evidence-layer and safety settings",
    "Memory River parameters are missing Stage 5 whole-review status or required safety/feature settings",
  );
}

function validateVisualAcceptanceHooks() {
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  assertCondition(
    hasAll(visualAudit, [
      "timeline_stage5_1_river_rendering_ready",
      "timeline_stage5_2_river_interaction_ready",
      "timeline_stage5_3_evidence_layers_ready",
      "DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = \"memory-river\"",
      "memory-river-canvas",
      "data-utc-time-scale",
      "memory-river-interaction-bar",
      "memory-river-selected-range",
      "memory-river-event-card",
      "buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes)",
      "black-hole-lifecycle",
      "proto-star-lifecycle",
      "stale-deprecated",
    ]),
    "part6_visual_acceptance_hooks_current",
    "Visual acceptance script contains Stage 5 rendering, interaction and evidence-layer hooks",
    "Visual acceptance script lacks Stage 5 hooks",
  );
}

function validateProductionDoesNotImportExperiments() {
  const productionFiles = walkFiles(path.join(appRoot, "src"), new Set(["experiments", "node_modules"]));
  const offendingRefs = [];
  const forbidden = [
    "memory-starfield-spike",
    "memory-river-spike",
    "universe-state-generator-spike",
  ];
  for (const filePath of productionFiles) {
    const source = fs.readFileSync(filePath, "utf8");
    for (const needle of forbidden) {
      if (source.includes(needle)) offendingRefs.push(`${path.relative(repoRoot, filePath)} -> ${needle}`);
    }
  }
  assertCondition(
    offendingRefs.length === 0,
    "part6_production_experiment_isolation",
    "Production src files do not import or reference isolated experiment directories",
    "Production source references isolated experiment directories",
    { offendingRefs },
  );
}

function validateBuildAndAcceptance() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "part6_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_river_rendering.mjs")], { cwd: appRoot });
  pass("part6_memory_river_rendering_passed", "validate_memory_river_rendering.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_river_interaction.mjs")], { cwd: appRoot });
  pass("part6_memory_river_interaction_passed", "validate_memory_river_interaction.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_river_evidence_layers.mjs")], { cwd: appRoot });
  pass("part6_memory_river_evidence_passed", "validate_memory_river_evidence_layers.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_river_stage5.mjs")], { cwd: appRoot });
  pass("part6_memory_river_stage5_passed", "validate_memory_river_stage5.mjs passed for current repo state");
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part6_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part6_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part6_release_acceptance_passed", "audit_memory_atlas_release.py passed against current production dist");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part6_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part6_stage5_review.md");

  assertCondition(
    packageSource.includes('"validate:part6-stage5": "node scripts/validate_memory_atlas_part6_stage5.cjs"'),
    "part6_package_script_current",
    "Package scripts expose validate:part6-stage5",
    "Package script validate:part6-stage5 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 6 is review-passed",
      "Stage 5.1",
      "Stage 5.2",
      "Stage 5.3",
      "Stage 5 overall",
      "validate:part6-stage5",
      "No Part 7 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part6_review_doc_current",
    "Part 6 review doc records phase coverage, validator, boundaries and upload non-goal",
    "Part 6 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 6 Stage 5 Review",
      "`validate:part6-stage5`",
      "Stage 5.1 / 5.2 / 5.3 / Stage 5 overall",
      "No Part 7 review",
      "No GitHub main upload",
    ]),
    "part6_changelog_current",
    "Changelog records Part 6 review, validator, stage coverage and non-goals",
    "Changelog does not record Part 6 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 6 复审",
      "Stage 5.1 / 5.2 / 5.3 / Stage 5 overall",
      "validate:part6-stage5",
      "未进入 Part 7",
      "未上传 GitHub main",
    ]),
    "part6_delivery_record_current",
    "Delivery record records Part 6 review status and next boundary",
    "Delivery record does not record Part 6 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 27. Part 6 Stage 5 复审门槛",
      "状态：`part_6_stage_5_review_passed`",
      "validate:part6-stage5",
      "Stage 5.1 River Rendering",
      "Stage 5.2 River Interaction",
      "Stage 5.3 Evidence Layers",
      "Stage 5 overall review",
      "不进入 Part 7",
    ]),
    "part6_model_parameters_current",
    "Model parameters record Part 6 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 6 review gate",
  );
}

try {
  validateStage51Review();
  validateStage52Review();
  validateStage53Review();
  validateStage5OverallReview();
  validateMemoryRiverRuntime();
  validateVisualAcceptanceHooks();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "6", scope: ["5.1", "5.2", "5.3", "stage5"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part6_stage5_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "6", scope: ["5.1", "5.2", "5.3", "stage5"], checks }, null, 2));
  process.exit(1);
}
