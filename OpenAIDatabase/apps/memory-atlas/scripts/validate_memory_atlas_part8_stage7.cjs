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

function validateStage71Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage7_1_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 7.1 is review-passed",
      "7.1.1 Canvas Pixel Check",
      "7.1.2 Starfield Quality",
      "7.1.3 River Quality",
      "Runtime Cleanup",
      "validate_stage7_visual_acceptance.cjs",
      "stage7_1_visual_acceptance_ready",
      "4177",
      "Stage 7.1 did not",
    ]),
    "part8_phase_7_1_review_current",
    "Stage 7.1 review proves browser screenshots, Galaxy pixel signal, Memory River structure and 4177 cleanup boundaries",
    "Stage 7.1 review is incomplete",
  );
}

function validateStage72Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage7_2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 7.2 is review-passed",
      "7.2.1 FPS Measurement",
      "7.2.2 Adaptive Quality",
      "7.2.3 Resource Cleanup",
      "validate:stage7-performance",
      "stage7_2_performance_acceptance_ready",
      "cleanup lifecycle",
      "Stage 7.2 did not",
    ]),
    "part8_phase_7_2_review_current",
    "Stage 7.2 review proves FPS thresholds, adaptive quality fallback/recovery, cleanup lifecycle and validation boundaries",
    "Stage 7.2 review is incomplete",
  );
}

function validateStage73Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage7_3_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 7.3 is review-passed",
      "7.3.1 Artifact Scan",
      "7.3.2 Reduced Motion",
      "7.3.3 Feedback Defaults",
      "validate:stage7-privacy-accessibility",
      "stage7_3_privacy_accessibility_ready",
      "public_redacted_read_only_visualization",
      "silent-by-default",
      "Stage 7.3 did not",
    ]),
    "part8_phase_7_3_review_current",
    "Stage 7.3 review proves release privacy scan, reduced motion, silent feedback defaults and safety boundaries",
    "Stage 7.3 review is incomplete",
  );
}

function validateStage7OverallReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage7_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 7 is review-passed",
      "7.1 Visual Acceptance",
      "7.2 Performance Acceptance",
      "7.3 Privacy and Accessibility",
      "Integrated Stage 7 Gate",
      "Data boundary",
      "Deployment boundary",
      "validate:stage7",
      "stage7_1_visual_acceptance_ready",
      "stage7_2_performance_acceptance_ready",
      "stage7_3_privacy_accessibility_ready",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
      "No direct frontend writeback was added",
      "The reviewed Stage 7 state is ready to upload",
    ]),
    "part8_stage7_overall_review_current",
    "Stage 7 overall review proves 7.1/7.2/7.3 inclusion, integrated gate, data/deployment/writeback boundaries and upload readiness",
    "Stage 7 overall review is incomplete",
  );
}

function validateRuntimeContracts() {
  const galaxy = readAppFile("src/components/GalaxyScene.tsx");
  const app = readAppFile("src/App.tsx");
  assertCondition(
    hasAll(galaxy, [
      "__memoryAtlasGalaxySignal",
      "GalaxyPerformanceSnapshot",
      "__memoryAtlasGalaxyLifecycle",
      "className=\"galaxy-performance-overlay\"",
      "renderer.forceContextLoss()",
    ]) && hasAll(app, [
      'data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? "opted-in" : "silent-by-default"}',
      'data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}',
      'data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}',
      'window.matchMedia?.("(prefers-reduced-motion: reduce)").matches',
      "navigator.vibrate",
      "new window.AudioContext()",
    ]),
    "part8_stage7_runtime_contracts_current",
    "Galaxy visual/performance cleanup contracts and Timeline reduced-motion/silent-feedback contracts remain intact",
    "Stage 7 runtime contracts for visual, performance, cleanup, reduced motion or silent feedback are missing",
  );
}

function validateVisualAcceptanceHooks() {
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  assertCondition(
    hasAll(visualAudit, [
      "stage7_1_visual_acceptance_ready",
      "stage7_2_performance_acceptance_ready",
      "stage7_3_privacy_accessibility_ready",
      "__memoryAtlasGalaxySignal",
      "fps: latestPerformanceSnapshot.fps",
      "averageFrameMs: latestPerformanceSnapshot.averageFrameMs",
      "adaptiveQualityEnabled: latestPerformanceSnapshot.adaptiveQualityEnabled",
      "__memoryAtlasGalaxyLifecycle",
      "data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? \"opted-in\" : \"silent-by-default\"}",
      "data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? \"enabled\" : \"disabled\"}",
      "data-feedback-audio={feedbackSettings.audio ? \"enabled\" : \"disabled\"}",
    ]),
    "part8_visual_acceptance_hooks_current",
    "Visual acceptance audit contains Stage 7 visual, performance and privacy/accessibility hooks",
    "Visual acceptance script lacks Stage 7 hooks",
  );
}

function validateModelAndRecords() {
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  assertCondition(
    hasAll(model, [
      "Stage 7.1 视觉验收模型",
      "Stage 7.2 性能验收模型",
      "Stage 7.3 隐私与无障碍验收模型",
      "stage_7_whole_stage_review_passed",
      "Stage 7 整体复审已确认",
      "source_contract.mode == \"public_redacted_read_only_visualization\"",
      "direct_frontend_mutation_of_active_memory == false",
    ]) && !model.includes("Stage 7 整体复审未完成"),
    "part8_stage7_model_parameters_current",
    "Model parameters record Stage 7 phase models and whole-stage review status without stale incomplete-state text",
    "Stage 7 model parameters are missing whole-review status or still contain stale incomplete-state text",
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
    "part8_production_experiment_isolation",
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
    "part8_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part8_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage7_visual_acceptance.cjs")], { cwd: appRoot });
  pass("part8_stage7_visual_passed", "validate_stage7_visual_acceptance.cjs passed for current production build");
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage7_performance_acceptance.cjs")], { cwd: appRoot });
  pass("part8_stage7_performance_passed", "validate_stage7_performance_acceptance.cjs passed for current production build");
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage7_privacy_accessibility.cjs")], { cwd: appRoot });
  pass("part8_stage7_privacy_accessibility_passed", "validate_stage7_privacy_accessibility.cjs passed for current production build");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_atlas_stage7.mjs")], { cwd: appRoot });
  pass("part8_stage7_integrated_passed", "validate_memory_atlas_stage7.mjs passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part8_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part8_release_acceptance_passed", "audit_memory_atlas_release.py passed against current production dist");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part8_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part8_stage7_review.md");

  assertCondition(
    packageSource.includes('"validate:part8-stage7": "node scripts/validate_memory_atlas_part8_stage7.cjs"'),
    "part8_package_script_current",
    "Package scripts expose validate:part8-stage7",
    "Package script validate:part8-stage7 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 8 is review-passed",
      "Stage 7.1",
      "Stage 7.2",
      "Stage 7.3",
      "Stage 7 overall",
      "validate:part8-stage7",
      "Stage 7 整体复审未完成",
      "No Part 9 review",
      "No Stage 8 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part8_review_doc_current",
    "Part 8 review doc records phase coverage, validator, stale-status fix, boundaries and upload non-goal",
    "Part 8 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 8 Stage 7 Review",
      "`validate:part8-stage7`",
      "Stage 7.1 / 7.2 / 7.3 / Stage 7 overall",
      "Stage 7 整体复审未完成",
      "No Part 9 review",
      "No GitHub main upload",
    ]),
    "part8_changelog_current",
    "Changelog records Part 8 review, validator, stale-status fix, stage coverage and non-goals",
    "Changelog does not record Part 8 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 8 复审",
      "Stage 7.1 / 7.2 / 7.3 / Stage 7 overall",
      "validate:part8-stage7",
      "Stage 7 整体复审未完成",
      "未进入 Part 9",
      "未上传 GitHub main",
    ]),
    "part8_delivery_record_current",
    "Delivery record records Part 8 review status, stale-status fix and next boundary",
    "Delivery record does not record Part 8 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 29. Part 8 Stage 7 复审门槛",
      "状态：`part_8_stage_7_review_passed`",
      "validate:part8-stage7",
      "Stage 7.1 Visual Acceptance",
      "Stage 7.2 Performance Acceptance",
      "Stage 7.3 Privacy and Accessibility",
      "Stage 7 overall review",
      "不进入 Part 9",
    ]),
    "part8_model_parameters_current",
    "Model parameters record Part 8 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 8 review gate",
  );
}

try {
  validateStage71Review();
  validateStage72Review();
  validateStage73Review();
  validateStage7OverallReview();
  validateRuntimeContracts();
  validateVisualAcceptanceHooks();
  validateModelAndRecords();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "8", scope: ["7.1", "7.2", "7.3", "stage7"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part8_stage7_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "8", scope: ["7.1", "7.2", "7.3", "stage7"], checks }, null, 2));
  process.exit(1);
}
