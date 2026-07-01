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

function parseJsonOutput(stdout) {
  const trimmed = stdout.trim();
  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace < 0 || lastBrace < firstBrace) return null;
  return JSON.parse(trimmed.slice(firstBrace, lastBrace + 1));
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

function validateStage9Reviews() {
  const stage91 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage9_1_review.md");
  const stage92 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage9_2_review.md");
  const stage9 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage9_review.md");

  assertCondition(
    hasAll(stage91, [
      "Stage 9.1 is review-passed",
      "9.1.1 Local Graph",
      "9.1.2 Label Rules",
      "9.1.3 Galaxy Sync",
      "validate:stage9-obsidian",
      "No raw/private/cookie/session/secret fields were introduced",
      "No direct frontend writeback was added",
      "Stage 9.2: Visual Semantics Enrichment",
    ]),
    "part10_phase_9_1_review_current",
    "Stage 9.1 review proves Obsidian local graph, label rules, Galaxy sync, visual acceptance and safety boundaries",
    "Stage 9.1 review is incomplete",
  );
  assertCondition(
    hasAll(stage92, [
      "Stage 9.2 is review-passed",
      "9.2.1 Memory Terrain v2",
      "9.2.2 Memory Weather v2",
      "9.2.3 ROI Visual Gradient",
      "validate:stage9-visual-semantics",
      "No raw/private/cookie/session/secret fields were introduced",
      "No direct frontend writeback was added",
      "Stage 9 whole-stage review",
    ]),
    "part10_phase_9_2_review_current",
    "Stage 9.2 review proves Memory Terrain v2, Memory Weather v2, ROI gradients, visual acceptance and safety boundaries",
    "Stage 9.2 review is incomplete",
  );
  assertCondition(
    hasAll(stage9, [
      "Stage 9 is review-passed",
      "9.1 Obsidian Graph E Iteration",
      "9.2 Visual Semantics Enrichment",
      "validate:stage9-obsidian",
      "validate:stage9-visual-semantics",
      "validate:stage9",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No direct frontend writeback",
      "whole-project review",
      "GitHub main upload",
    ]),
    "part10_stage9_overall_review_current",
    "Stage 9 overall review records phase coverage, validation, boundaries, whole-project review gate and upload gate",
    "Stage 9 whole-stage review doc is incomplete",
  );
}

function validateStage9RuntimeContracts() {
  const obsidian = readAppFile("src/components/ObsidianGraphScene.tsx");
  const app = readAppFile("src/App.tsx");
  const galaxy = readAppFile("src/components/GalaxyScene.tsx");
  const css = readAppFile("src/styles.css");
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");

  assertCondition(
    hasAll(obsidian, [
      "LOCAL_GRAPH_PRIMARY_NODE_LIMIT",
      "LOCAL_GRAPH_SECONDARY_NODE_LIMIT",
      "LOCAL_GRAPH_CLUSTER_MEMBER_LIMIT",
      "buildLocalGraphPlan",
      "sharedFocus.sourceView === \"galaxy\"",
      "data-local-graph-mode",
      "data-galaxy-cluster-focus",
      "data-hidden-local-neighbors",
      "data-label-budget",
      "labelVisibilityRule",
      "data-label-rule",
      "Local Graph Budget",
    ]) && hasAll(app, [
      "sharedFocus={sharedState.focus}",
      "sharedState: SharedAtlasState",
    ]) && hasAll(css, [
      ".obsidian-local-budget",
      ".obsidian-node-label[data-label-rule=\"local-neighbor\"]",
    ]),
    "part10_stage9_1_runtime_contracts",
    "Obsidian runtime preserves local graph budget, label rules and Galaxy shared-focus sync",
    "Stage 9.1 runtime contracts are incomplete",
  );
  assertCondition(
    hasAll(app, [
      "Memory Weather v2",
      "data-memory-weather-v2",
      "buildMemoryWeatherV2",
      "memory-river-roi-gradient",
      "buildMemoryRiverRoiGradient",
      "data-roi-gradient=\"capability-growth\"",
    ]) && hasAll(galaxy, [
      "Memory Terrain v2",
      "data-memory-terrain-v2",
      "buildGalaxyRoiGradientSummary",
      "galaxy-roi-gradient-panel",
      "data-roi-gradient=\"galaxy-analysis\"",
    ]) && hasAll(css, [
      ".home-weather-v2-scores",
      ".galaxy-roi-gradient-panel",
      ".memory-river-roi-gradient",
    ]),
    "part10_stage9_2_runtime_contracts",
    "Visual semantics runtime preserves Memory Weather v2, Terrain v2, Galaxy ROI gradient and Memory River ROI gradient",
    "Stage 9.2 runtime contracts are incomplete",
  );
  assertCondition(
    hasAll(visualAudit, [
      "stage9_1_obsidian_graph_iteration_ready",
      "stage9_2_visual_semantics_enrichment_ready",
      "data-galaxy-cluster-focus",
      "data-label-rule",
      "data-memory-weather-v2",
      "data-memory-terrain-v2",
      "data-roi-gradient",
    ]),
    "part10_stage9_visual_acceptance_hooks_current",
    "Visual acceptance audit covers Stage 9.1 Obsidian hooks and Stage 9.2 visual semantics hooks",
    "Stage 9 visual acceptance hooks are incomplete",
  );
}

function validateStage9DocsAndModel() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const changelog = readRepoFile("CHANGELOG.md");

  assertCondition(
    hasAll(packageSource, [
      '"validate:stage9-obsidian": "node scripts/validate_stage9_obsidian_iteration.cjs"',
      '"validate:stage9-visual-semantics": "node scripts/validate_stage9_visual_semantics.cjs"',
      '"validate:stage9": "node scripts/validate_memory_atlas_stage9.cjs"',
    ]),
    "part10_stage9_package_scripts_current",
    "Package scripts expose Stage 9.1, Stage 9.2 and Stage 9 whole-stage validators",
    "Stage 9 package scripts are incomplete",
  );
  assertCondition(
    hasAll(model, [
      "stage_9_1_obsidian_graph_iteration_passed",
      "stage_9_2_visual_semantics_enrichment_passed",
      "stage_9_whole_stage_review_passed",
      "validate:stage9-obsidian",
      "validate:stage9-visual-semantics",
      "validate:stage9",
      "direct_frontend_mutation_of_active_memory == false",
      "整项目复审与修复",
      "GitHub main 上传",
    ]),
    "part10_stage9_model_parameters_current",
    "Model parameters record Stage 9 states, validators, safety boundaries and whole-project-review-before-upload gate",
    "Stage 9 model parameters are missing status, validators or next-gate boundary",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Stage 9.1 Obsidian Graph E Iteration",
      "完成 Memory Atlas v1.1.5 Stage 9.2 Visual Semantics Enrichment",
      "完成 Memory Atlas v1.1.5 Stage 9 整体复审",
      "Stage 9 整阶段复审通过",
      "整项目复审",
      "GitHub main 上传",
    ]),
    "part10_stage9_delivery_record_current",
    "Delivery record records Stage 9 phases, whole-stage review and whole-project-review-before-upload boundary",
    "Delivery record does not record Stage 9 completion or next gate",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Stage 9 Whole-Stage Review",
      "Completed the Stage 9 whole-stage review",
      "`validate:stage9`",
      "No Cloudflare live deploy",
      "No raw/private data access",
      "No direct writeback",
      "whole-project review",
      "GitHub main upload",
    ]),
    "part10_stage9_changelog_current",
    "Changelog records Stage 9 review and preserves the whole-project-review-before-upload boundary",
    "Changelog lacks Stage 9 status or next-gate boundary",
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
    "part10_production_experiment_isolation",
    "Production src files do not import or reference isolated experiment directories",
    "Production source references isolated experiment directories",
    { offendingRefs },
  );
}

function validateStage9Gates() {
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage9_obsidian_iteration.cjs")], { cwd: appRoot });
  pass("part10_stage9_obsidian_passed", "validate_stage9_obsidian_iteration.cjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage9_visual_semantics.cjs")], { cwd: appRoot });
  pass("part10_stage9_visual_semantics_passed", "validate_stage9_visual_semantics.cjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_atlas_stage9.cjs")], { cwd: appRoot });
  pass("part10_stage9_integrated_passed", "validate_memory_atlas_stage9.cjs passed for current repo state");
  const visual = run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  const visualParsed = parseJsonOutput(visual.stdout);
  assertCondition(
    visualParsed?.status === "PASS",
    "part10_visual_acceptance_passed",
    "audit_memory_atlas_visual_acceptance.py passed with Stage 9 hooks",
    "Visual acceptance audit did not return PASS",
    { stdout: visual.stdout.slice(-4000), stderr: visual.stderr.slice(-4000) },
  );
  const release = run("python3", ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  const releaseParsed = parseJsonOutput(release.stdout);
  assertCondition(
    releaseParsed?.status === "PASS",
    "part10_release_audit_passed",
    "audit_memory_atlas_release.py passed against current production dist",
    "Release audit did not return PASS",
    { stdout: release.stdout.slice(-4000), stderr: release.stderr.slice(-4000) },
  );
  const acceptance = run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  const acceptanceParsed = parseJsonOutput(acceptance.stdout);
  assertCondition(
    acceptanceParsed?.status === "PASS",
    "part10_overall_acceptance_passed",
    "audit_memory_atlas_acceptance.py passed against current production dist",
    "Overall acceptance audit did not return PASS",
    { stdout: acceptance.stdout.slice(-4000), stderr: acceptance.stderr.slice(-4000) },
  );
}

function validatePart10DocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part10_stage9_review.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");

  assertCondition(
    packageSource.includes('"validate:part10-stage9": "node scripts/validate_memory_atlas_part10_stage9.cjs"'),
    "part10_package_script_current",
    "Package scripts expose validate:part10-stage9",
    "Package script validate:part10-stage9 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 10 is review-passed",
      "Stage 9.1",
      "Stage 9.2",
      "Stage 9 overall",
      "validate:part10-stage9",
      "whole-project review",
      "No GitHub main upload",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
    ]),
    "part10_review_doc_current",
    "Part 10 review doc records Stage 9 coverage, validator, whole-project-review gate and boundaries",
    "Part 10 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 10 Stage 9 Review",
      "`validate:part10-stage9`",
      "Stage 9.1 / 9.2 / Stage 9 overall",
      "whole-project review",
      "No GitHub main upload",
    ]),
    "part10_changelog_current",
    "Changelog records Part 10 review, validator, Stage 9 coverage and non-goals",
    "Changelog does not record Part 10 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 10 复审",
      "Stage 9.1 / 9.2 / Stage 9 overall",
      "validate:part10-stage9",
      "整项目复审",
      "未上传 GitHub main",
    ]),
    "part10_delivery_record_current",
    "Delivery record records Part 10 review status and next whole-project review boundary",
    "Delivery record does not record Part 10 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 31. Part 10 Stage 9 复审门槛",
      "状态：`part_10_stage_9_review_passed`",
      "validate:part10-stage9",
      "Stage 9.1 Obsidian Graph E Iteration",
      "Stage 9.2 Visual Semantics Enrichment",
      "Stage 9 overall review",
      "进入整项目复审",
    ]),
    "part10_model_parameters_current",
    "Model parameters record Part 10 review gate, validator, Stage 9 coverage and next whole-project review gate",
    "Model parameters do not record Part 10 review gate",
  );
}

try {
  validateStage9Reviews();
  validateStage9RuntimeContracts();
  validateStage9DocsAndModel();
  validateProductionDoesNotImportExperiments();
  validateStage9Gates();
  validatePart10DocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "10", scope: ["9.1", "9.2", "stage9"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part10_stage9_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "10", scope: ["9.1", "9.2", "stage9"], checks }, null, 2));
  process.exit(1);
}
