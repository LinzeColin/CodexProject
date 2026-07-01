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

function validateStage31Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage3_1_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 3.1 is review-passed",
      "3.1.1 Home page skeleton",
      "3.1.2 Universe State cards",
      "3.1.3 Next Best Actions",
      "`ViewKey` includes `home`",
      "`activeView` defaults to `home`",
      "Memory Weather",
      "Black Hole risk",
      "Proto-Star opportunity",
      "proposal-only action cards",
      "memory_home_default_overview_ready",
      "Read raw exports",
      "cookies, sessions",
      "Stage 3.1 did not",
    ]),
    "part4_phase_3_1_review_current",
    "Stage 3.1 review proves default Home skeleton, Universe State cards, proposal-only actions, validation evidence and safety boundaries",
    "Stage 3.1 review is incomplete",
  );
}

function validateStage32Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage3_2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 3.2 is review-passed",
      "3.2.1 Mini Starfield Preview",
      "3.2.2 River Pulse Preview",
      "3.2.3 Inspector Deep Link",
      "preserves the selected memory focus",
      "static SVG",
      "jumpToPreview",
      "\"galaxy\"",
      "Timeline",
      "\"search\"",
      "memory_home_preview_widgets_ready",
      "Read raw exports",
      "cookies, sessions",
      "Stage 3.2 did not",
    ]),
    "part4_phase_3_2_review_current",
    "Stage 3.2 review proves Mini Starfield, River Pulse, Inspector Deep Link, focus-preserving navigation, visual audit evidence and safety boundaries",
    "Stage 3.2 review is incomplete",
  );
}

function validateStage3OverallReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage3_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 3 is review-passed",
      "Stage 3.1 made `记忆总览` the default startup board",
      "Stage 3.2 added preview widgets",
      "Default Home board",
      "Universe State and next actions",
      "Preview widgets",
      "Focus consistency",
      "Safety boundary",
      "audit_memory_atlas_visual_acceptance.py",
      "audit_memory_atlas_acceptance.py",
      "Port `4177` had no listener",
      "Stage 3 did not",
      "Next Stage Gate",
    ]),
    "part4_stage3_overall_review_current",
    "Stage 3 overall review proves phase inclusion, acceptance matrix, validation evidence, boundary review and next-stage gate",
    "Stage 3 overall review is incomplete",
  );
}

function validateHomeRuntime() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const css = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(app, [
      "{ key: \"home\", label: \"记忆总览\", icon: Home }",
      "createSharedAtlasState({ activeView: \"home\"",
      "function HomeOverviewView",
      "buildHomeOverviewModel",
      "Memory Weather v2",
      "Black Hole",
      "Proto-Star",
      "model.actions.map",
      "proposal-only",
      "Mini Starfield",
      "River Pulse",
      "Inspector Deep Link",
      "home-preview-card mini-starfield-preview",
      "home-preview-card river-pulse-preview",
      "jumpToPreview(model.miniStarfieldFocus, \"galaxy\")",
      "jumpToPreview(model.riverPulseFocus, \"timeline\")",
      "jumpToPreview(link.node, \"search\")",
    ]) && hasAll(css, [
      ".home-overview-view",
      ".home-preview-grid",
      ".home-preview-card",
      ".home-starfield-nebula",
      ".river-pulse-lanes",
      ".home-inspector-panel",
    ]),
    "part4_home_runtime_contract",
    "Current Home runtime exposes default Home view, weather/risk/opportunity cards, proposal-only actions, preview widgets, focus-preserving deep links and CSS surfaces",
    "Home runtime contract is incomplete",
  );
}

function validateVisualAcceptanceHooks() {
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  assertCondition(
    hasAll(visualAudit, [
      "memory_home_default_overview_ready",
      "memory_home_preview_widgets_ready",
      "{ key: \"home\", label: \"记忆总览\", icon: Home }",
      "const activeView = sharedState.mode.activeView",
      "if (activeView === \"home\")",
      "function HomeOverviewView",
      "function buildHomeOverviewModel",
      "Mini Starfield",
      "River Pulse",
      "Inspector Deep Link",
      "home-preview-card mini-starfield-preview",
      "home-preview-card river-pulse-preview",
    ]),
    "part4_visual_acceptance_hooks_current",
    "Visual acceptance script contains Stage 3 default Home and preview-widget hooks",
    "Visual acceptance script lacks Stage 3 hooks",
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
    "part4_production_experiment_isolation",
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
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part4_stage3_review.md");

  assertCondition(
    packageSource.includes('"validate:part4-stage3": "node scripts/validate_memory_atlas_part4_stage3.cjs"'),
    "part4_package_script_current",
    "Package scripts expose validate:part4-stage3",
    "Package script validate:part4-stage3 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 4 is review-passed",
      "Stage 3.1",
      "Stage 3.2",
      "Stage 3 overall",
      "validate:part4-stage3",
      "No Part 5 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part4_review_doc_current",
    "Part 4 review doc records phase coverage, validator, boundaries and upload non-goal",
    "Part 4 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 4 Stage 3 Review",
      "`validate:part4-stage3`",
      "Stage 3.1 / 3.2 / Stage 3 overall",
      "No Part 5 review",
      "No GitHub main upload",
    ]),
    "part4_changelog_current",
    "Changelog records Part 4 review, validator, stage coverage and non-goals",
    "Changelog does not record Part 4 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 4 复审",
      "Stage 3.1 / 3.2 / Stage 3 overall",
      "validate:part4-stage3",
      "未进入 Part 5",
      "未上传 GitHub main",
    ]),
    "part4_delivery_record_current",
    "Delivery record records Part 4 review status and next boundary",
    "Delivery record does not record Part 4 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 25. Part 4 Stage 3 复审门槛",
      "状态：`part_4_stage_3_review_passed`",
      "validate:part4-stage3",
      "Stage 3.1 Home Information Architecture",
      "Stage 3.2 Preview Widgets",
      "Stage 3 overall review",
      "不进入 Part 5",
    ]),
    "part4_model_parameters_current",
    "Model parameters record Part 4 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 4 review gate",
  );
}

function validateBuildAndAcceptance() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "part4_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part4_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part4_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part4_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

try {
  validateStage31Review();
  validateStage32Review();
  validateStage3OverallReview();
  validateHomeRuntime();
  validateVisualAcceptanceHooks();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "4", scope: ["3.1", "3.2", "stage3"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part4_stage3_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "4", scope: ["3.1", "3.2", "stage3"], checks }, null, 2));
  process.exit(1);
}
