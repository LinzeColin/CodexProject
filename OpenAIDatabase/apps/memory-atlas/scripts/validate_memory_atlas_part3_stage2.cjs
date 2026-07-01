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

function validateDefaultHomePlan() {
  const source = readRepoFile("docs/product/memory_atlas_default_home_integration_plan.md");
  assertCondition(
    hasAll(source, [
      "Stage 2.1 Default Home Integration Plan",
      "integration planning only",
      "default view remains `galaxy`",
      "Make `记忆总览` the default startup board",
      "Memory Weather",
      "Black Hole",
      "Proto-Star",
      "Next Best Actions",
      "Mini Starfield",
      "River Pulse",
      "Stage 3.1.1 Home Page Skeleton",
      "Stage 3.1.2 Universe State Cards",
      "Stage 3.1.3 Next Actions and Deep Links",
      "Startup H1 is `记忆总览`",
      "Rollback",
      "Validation Plan",
      "Stop Conditions",
      "Stage 2.1 Completion Criteria",
      "Runtime default-home behavior remains a later Stage 3 implementation item.",
    ]),
    "part3_phase_2_1_default_home_plan",
    "Default-home plan preserves target UX, implementation sequence, rollback, validation, stop conditions and Stage 3 deferral",
    "Default-home planning contract is incomplete",
  );
}

function validateGalaxyPlan() {
  const source = readRepoFile("docs/product/memory_atlas_galaxy_replacement_plan.md");
  assertCondition(
    hasAll(source, [
      "Stage 2.2 Galaxy Replacement Plan",
      "integration planning only",
      "existing `GalaxyScene` remains active",
      "new `记忆星系` starfield experience",
      "feature flag",
      "MemoryStarfieldScene",
      "LegacyGalaxyScene",
      "apps/memory-atlas/src/config/visualFeatureFlags.ts",
      "memoryStarfield.enabled",
      "Stage 4.1.1 New/Old Galaxy Feature Flag",
      "Stage 4.1.2 Flow Field Renderer Integration",
      "Stage 4.1.3 WebGL Fallback and LOD",
      "Data Mapping Plan",
      "`AtlasNode.metrics.weight_score`",
      "`UniverseStateSnapshot.black_holes`",
      "`UniverseStateSnapshot.proto_stars`",
      "`UniverseStateSnapshot.memory_terrain`",
      "Validation Plan",
      "Stop Conditions",
      "Stage 2.2 Completion Criteria",
      "Runtime Galaxy replacement remains a later Stage 4 implementation item.",
    ]),
    "part3_phase_2_2_galaxy_plan",
    "Galaxy replacement plan preserves feature flag strategy, safe sequence, data mapping, rollback, validation and Stage 4 deferral",
    "Galaxy replacement planning contract is incomplete",
  );
}

function validateTimelinePlan() {
  const source = readRepoFile("docs/product/memory_atlas_timeline_replacement_plan.md");
  assertCondition(
    hasAll(source, [
      "Stage 2.3 Timeline Replacement Plan",
      "integration planning only",
      "existing `TimelineView` remains active",
      "new `记忆时间河` experience",
      "feature flag",
      "MemoryRiverView",
      "LegacyTimelineView",
      "d3.scaleUtc",
      "d3.zoom",
      "d3.brushX",
      "memoryRiver.enabled",
      "memoryRiver.feedbackEnabled",
      "Stage 5.1.1 Timeline Feature Flag",
      "Stage 5.1.2 UTC Time Scale",
      "Stage 5.1.3 Theme River Lanes",
      "Stage 5.2 Zoom, Brush and Event Cards",
      "Stage 5.3 Evidence Layers and Safe Feedback",
      "Data Mapping Plan",
      "`MemoryAtlas.timeline[].date`",
      "`UniverseStateSnapshot.river_pulse`",
      "`UniverseStateSnapshot.black_holes`",
      "`UniverseStateSnapshot.proto_stars`",
      "Validation Plan",
      "Stop Conditions",
      "Stage 2.3 Completion Criteria",
      "Runtime Timeline replacement remains a later Stage 5 implementation item.",
    ]),
    "part3_phase_2_3_timeline_plan",
    "Timeline replacement plan preserves feature flag strategy, UTC scale, lanes, zoom/brush, evidence layers, rollback, validation and Stage 5 deferral",
    "Timeline replacement planning contract is incomplete",
  );
}

function validateStage2HistoricalReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 2 is review-passed",
      "Task 2.1 Default Home Integration Plan",
      "Task 2.2 Galaxy Replacement Plan",
      "Task 2.3 Timeline Replacement Plan",
      "Planning acceptance evidence",
      "Runtime default remains `galaxy`",
      "actual default-home implementation is deferred to Stage 3",
      "actual replacement is deferred to Stage 4",
      "actual replacement is deferred to Stage 5",
      "Stage 2 historical runtime note",
      "Current repo state may include",
      "later Stage 3-9 runtime changes",
    ]),
    "part3_stage2_review_historical_boundary",
    "Stage 2 review records all planning tasks and now marks its runtime assertions as historical, not current-state truth",
    "Stage 2 review lacks Part 3 historical-runtime boundary",
  );
}

function validateCurrentRuntimeIsLaterStage() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  assertCondition(
    hasAll(app, [
      "{ key: \"home\", label: \"记忆总览\"",
      "createSharedAtlasState({ activeView: \"home\"",
      "function GalaxyView",
      "GalaxyRendererMode",
      "memory-starfield",
      "TimelineRendererMode",
      "memory-river",
      "function TimelineView",
      "selectedTimelineRange",
    ]),
    "part3_current_runtime_advanced_beyond_stage2",
    "Current App.tsx has later-stage home, Galaxy renderer toggle and Memory River runtime markers, so Stage 2 runtime notes must be treated as historical",
    "Current runtime markers do not match expected later-stage state",
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
    "part3_production_experiment_isolation",
    "Production src files do not import or reference isolated experiment directories",
    "Production source references isolated experiment directories",
    { offendingRefs },
  );
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part3_stage2_review.md");

  assertCondition(
    packageSource.includes('"validate:part3-stage2": "node scripts/validate_memory_atlas_part3_stage2.cjs"'),
    "part3_package_script_current",
    "Package scripts expose validate:part3-stage2",
    "Package script validate:part3-stage2 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 3 is review-passed",
      "Phase 2.1",
      "Phase 2.2",
      "Phase 2.3",
      "validate:part3-stage2",
      "Stage 2 historical runtime note",
      "No Part 4 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part3_review_doc_current",
    "Part 3 review doc records phase coverage, validator, historical-runtime note, boundaries and upload non-goal",
    "Part 3 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 3 Stage 2 Review",
      "`validate:part3-stage2`",
      "Phase 2.1 / 2.2 / 2.3",
      "Stage 2 historical runtime note",
      "No Part 4 review",
      "No GitHub main upload",
    ]),
    "part3_changelog_current",
    "Changelog records Part 3 review, validator, phase coverage, historical-runtime note and non-goals",
    "Changelog does not record Part 3 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 3 复审",
      "Phase 2.1 / 2.2 / 2.3",
      "validate:part3-stage2",
      "Stage 2 historical runtime note",
      "未进入 Part 4",
      "未上传 GitHub main",
    ]),
    "part3_delivery_record_current",
    "Delivery record records Part 3 review status and next boundary",
    "Delivery record does not record Part 3 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 24. Part 3 Stage 2 复审门槛",
      "状态：`part_3_stage_2_review_passed`",
      "validate:part3-stage2",
      "Phase 2.1 Default Home Integration Plan",
      "Phase 2.2 Galaxy Replacement Plan",
      "Phase 2.3 Timeline Replacement Plan",
      "Stage 2 historical runtime note",
      "不进入 Part 4",
    ]),
    "part3_model_parameters_current",
    "Model parameters record Part 3 review gate, validator, phase coverage, historical-runtime note and non-goals",
    "Model parameters do not record Part 3 review gate",
  );
}

function validateBuildAndAcceptance() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "part3_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part3_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part3_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part3_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

try {
  validateDefaultHomePlan();
  validateGalaxyPlan();
  validateTimelinePlan();
  validateStage2HistoricalReview();
  validateCurrentRuntimeIsLaterStage();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "3", phases: ["2.1", "2.2", "2.3"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part3_stage2_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "3", phases: ["2.1", "2.2", "2.3"], checks }, null, 2));
  process.exit(1);
}
