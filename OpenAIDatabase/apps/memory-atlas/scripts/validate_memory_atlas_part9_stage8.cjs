#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];
const requireLocalAppReinstall = process.env.MEMORY_ATLAS_PART9_REINSTALL_LOCAL_APP === "1";

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

function currentGitHead() {
  return run("git", ["rev-parse", "HEAD"], { cwd: worktreeRoot }).stdout.trim();
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

function validateStage8Reviews() {
  const stage81 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage8_1_review.md");
  const stage82 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage8_2_review.md");
  const stage8 = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage8_review.md");

  assertCondition(
    hasAll(stage81, [
      "Stage 8.1 is review-passed",
      "8.1.1 local build",
      "8.1.2 launcher check",
      "8.1.3 default route check",
      "validate:stage8-local-app",
      "Runtime safety",
      "memory_atlas_build.json",
      "No raw/private/cookie/session/secret fields were introduced",
      "No direct frontend writeback was added",
      "Stage 8.2: Release Safety",
    ]),
    "part9_phase_8_1_review_current",
    "Stage 8.1 review proves local build, launcher, default route, runtime manifest, cleanup and safety boundaries",
    "Stage 8.1 review is incomplete",
  );
  assertCondition(
    hasAll(stage82, [
      "Stage 8.2 is review-passed",
      "feature flag rollback",
      "acceptance audit",
      "release notes",
      "validate:stage8-release-safety",
      "No Cloudflare deployment or Access policy change was performed",
      "No raw/private/cookie/session/secret fields were introduced",
      "No direct frontend writeback was added",
      "Stage 8 whole-stage review",
    ]),
    "part9_phase_8_2_review_current",
    "Stage 8.2 review proves rollback, acceptance audit, release notes and safety boundaries",
    "Stage 8.2 review is incomplete",
  );
  assertCondition(
    hasAll(stage8, [
      "Stage 8 is review-passed",
      "8.1 Local App Packaging",
      "8.2 Release Safety",
      "validate:stage8-local-app",
      "validate:stage8-release-safety",
      "validate:stage8",
      "Cloudflare preflight is offline-only",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No direct frontend writeback",
      "GitHub main upload",
    ]),
    "part9_stage8_overall_review_current",
    "Stage 8 overall review proves 8.1/8.2 coverage, offline deploy readiness, cleanup and safety boundaries",
    "Stage 8 overall review is incomplete",
  );
}

function validateStage8Contracts() {
  const installer = readRepoFile("scripts/install_memory_atlas_app.py");
  const acceptance = readRepoFile("scripts/audit_memory_atlas_acceptance.py");
  const visualFlags = readAppFile("src/config/visualFlags.ts");
  const app = readAppFile("src/App.tsx");

  assertCondition(
    hasAll(installer, [
      "memory_atlas_build.json",
      "\"git_commit\"",
      "MEMORY_ATLAS_PID_FILE",
      "path.unlink()",
      "CODEX_NODE_BIN",
      "pnpm --dir",
      "Memory Atlas.app",
    ]) && hasAll(acceptance, [
      "local_app_bundles_present",
      "local_runtime_matches_current_git",
      "local static runtime build manifest matches current git HEAD",
    ]),
    "part9_stage8_local_app_runtime_contracts",
    "Installer and acceptance audit preserve app bundle, runtime manifest, pid cleanup and current-HEAD checks",
    "Stage 8 local app runtime contracts are incomplete",
  );
  assertCondition(
    hasAll(visualFlags, [
      'DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield"',
      'DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river"',
      'GALAXY_RENDERER_STORAGE_KEY = "memory-atlas.galaxy-renderer"',
      'TIMELINE_RENDERER_STORAGE_KEY = "memory-atlas.timeline-renderer"',
      "VITE_MEMORY_ATLAS_GALAXY_RENDERER",
      "VITE_MEMORY_ATLAS_TIMELINE_RENDERER",
      'params.get("galaxyRenderer") ?? params.get("galaxy")',
      'params.get("timelineRenderer") ?? params.get("timeline")',
    ]) && hasAll(app, [
      'aria-label="Galaxy renderer feature flag"',
      'aria-label="Timeline renderer feature flag"',
      'updateGalaxyRendererMode("legacy")',
      'updateTimelineRendererMode("legacy")',
      'data-timeline-renderer={timelineRendererMode}',
      '<GalaxyScene nodes={graphNodes} edges={graphEdges} rendererMode={galaxyRendererMode}',
    ]),
    "part9_stage8_release_safety_runtime_contracts",
    "Visual flags and UI preserve default renderers, rollback paths and persistence contracts",
    "Stage 8 release-safety runtime contracts are incomplete",
  );
}

function validateStage8DocsAndModel() {
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const acceptance = readRepoFile("docs/acceptance/memory_atlas_v1_1_5_stage8_2_release_safety.md");
  const releaseNotes = readRepoFile("docs/release_notes/memory_atlas_v1_1_5_stage8_release_notes.md");

  assertCondition(
    hasAll(model, [
      "stage_8_1_local_app_packaging_passed",
      "stage_8_2_release_safety_passed",
      "stage_8_whole_stage_review_passed",
      "validate:stage8-local-app",
      "validate:stage8-release-safety",
      "validate:stage8",
      "offline Cloudflare Pages + Access preflight",
      "direct_frontend_mutation_of_active_memory == false",
      "Runtime manifest 的具体 `git_commit` 不在模型参数中硬编码",
      "commit is validated by audit, not hard-coded",
    ]) && !model.includes("bb4cbd9d4eedbdfe9d95a5850994a293488fa742"),
    "part9_stage8_model_parameters_current",
    "Model parameters record Stage 8 gates and no longer hard-code an old runtime git commit",
    "Stage 8 model parameters are missing review state or still hard-code an old runtime commit",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Stage 8.1 Local App Packaging",
      "完成 Memory Atlas v1.1.5 Stage 8.2 Release Safety",
      "完成 Memory Atlas v1.1.5 Stage 8 整体复审",
      "validate:stage8",
      "Stage 8 整阶段复审通过",
    ]),
    "part9_stage8_delivery_record_current",
    "Delivery record records Stage 8.1, Stage 8.2 and Stage 8 overall completion",
    "Delivery record does not record Stage 8 completion",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Stage 8 Whole-Stage Review",
      "Memory Atlas v1.1.5 Stage 8.2 Release Safety",
      "Memory Atlas v1.1.5 Stage 8.1 Local App Packaging",
      "`validate:stage8`",
      "No Cloudflare live deploy",
      "No raw/private data access",
      "No direct writeback",
    ]),
    "part9_stage8_changelog_current",
    "Changelog records Stage 8.1, Stage 8.2, Stage 8 overall and non-goal boundaries",
    "Changelog lacks Stage 8 records or boundaries",
  );
  assertCondition(
    hasAll(acceptance, [
      "Stage 8.2 Release Safety Acceptance",
      "8.2.1 Feature Flag Rollback",
      "8.2.2 Acceptance Audit",
      "8.2.3 Release Notes",
      "No Cloudflare live deploy",
      "No GitHub main upload yet",
    ]) && hasAll(releaseNotes, [
      "Memory Atlas v1.1.5 Stage 8 Release Notes",
      "Stage 8 整体复审已完成",
      "回滚",
      "Cloudflare",
      "proposal-only",
    ]),
    "part9_stage8_acceptance_and_release_notes_current",
    "Stage 8 acceptance and release notes preserve rollback, audit, safety and not-yet-uploaded boundaries",
    "Stage 8 acceptance or release notes are incomplete",
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
    "part9_production_experiment_isolation",
    "Production src files do not import or reference isolated experiment directories",
    "Production source references isolated experiment directories",
    { offendingRefs },
  );
}

function validateStage8Gates() {
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage8_local_app_packaging.cjs")], { cwd: appRoot });
  pass("part9_stage8_local_app_packaging_passed", "validate_stage8_local_app_packaging.cjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_stage8_release_safety.cjs")], { cwd: appRoot });
  pass("part9_stage8_release_safety_passed", "validate_stage8_release_safety.cjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_atlas_stage8.cjs")], { cwd: appRoot });
  pass("part9_stage8_integrated_passed", "validate_memory_atlas_stage8.cjs passed for current repo state");
}

function validateInstalledLocalAppRuntime() {
  if (!requireLocalAppReinstall) {
    pass(
      "part9_local_app_reinstall_deferred",
      "Local app reinstall is deferred by default; set MEMORY_ATLAS_PART9_REINSTALL_LOCAL_APP=1 to refresh installed app/runtime on a prepared machine",
      { requireLocalAppReinstall },
    );
    return;
  }

  run("python3", ["scripts/install_memory_atlas_app.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part9_local_app_reinstalled", "install_memory_atlas_app.py refreshed Downloads app, Applications app and Application Support runtime");

  const runtimeDir = path.join(process.env.HOME || "", "Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime");
  const buildInfoPath = path.join(runtimeDir, "memory_atlas_build.json");
  const buildInfo = JSON.parse(fs.readFileSync(buildInfoPath, "utf8"));
  const head = currentGitHead();
  assertCondition(
    buildInfo.schema_version === "memory_atlas_build.v1" && buildInfo.git_commit === head,
    "part9_local_runtime_manifest_matches_head",
    "Local runtime memory_atlas_build.json matches current git HEAD",
    "Local runtime manifest does not match current git HEAD",
    { buildInfoPath, buildInfoGitCommit: buildInfo.git_commit, head },
  );

  const audit = run("python3", [
    "scripts/audit_memory_atlas_acceptance.py",
    "--repo-root",
    repoRoot,
    "--publish-dir",
    runtimeDir,
    "--require-local-apps",
  ], { cwd: repoRoot });
  const parsed = parseJsonOutput(audit.stdout);
  const passedChecks = new Set((parsed?.checks || []).filter((check) => check.status === "PASS").map((check) => check.name));
  assertCondition(
    parsed?.status === "PASS"
      && passedChecks.has("local_app_bundles_present")
      && passedChecks.has("local_runtime_matches_current_git"),
    "part9_local_app_acceptance_passed",
    "Local app acceptance passed with Downloads/Applications bundles present and runtime matching current git HEAD",
    "Local app acceptance did not pass required app bundle/runtime checks",
    { stdout: audit.stdout.slice(-4000), stderr: audit.stderr.slice(-4000) },
  );
}

function validatePart9DocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part9_stage8_review.md");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");

  assertCondition(
    packageSource.includes('"validate:part9-stage8": "node scripts/validate_memory_atlas_part9_stage8.cjs"'),
    "part9_package_script_current",
    "Package scripts expose validate:part9-stage8",
    "Package script validate:part9-stage8 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 9 is review-passed",
      "Stage 8.1",
      "Stage 8.2",
      "Stage 8 overall",
      "validate:part9-stage8",
      "/Applications/Memory Atlas.app",
      "runtime manifest",
      "No Part 10 review",
      "No Stage 9 review",
      "No GitHub main upload",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
    ]),
    "part9_review_doc_current",
    "Part 9 review doc records phase coverage, local app/runtime fixes, validator and boundaries",
    "Part 9 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 9 Stage 8 Review",
      "`validate:part9-stage8`",
      "Stage 8.1 / 8.2 / Stage 8 overall",
      "/Applications/Memory Atlas.app",
      "runtime manifest",
      "No Part 10 review",
      "No GitHub main upload",
    ]),
    "part9_changelog_current",
    "Changelog records Part 9 review, validator, local app/runtime fix and non-goals",
    "Changelog does not record Part 9 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 9 复审",
      "Stage 8.1 / 8.2 / Stage 8 overall",
      "validate:part9-stage8",
      "/Applications/Memory Atlas.app",
      "runtime manifest",
      "未进入 Part 10",
      "未上传 GitHub main",
    ]),
    "part9_delivery_record_current",
    "Delivery record records Part 9 review status, local app/runtime fix and next boundary",
    "Delivery record does not record Part 9 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 30. Part 9 Stage 8 复审门槛",
      "状态：`part_9_stage_8_review_passed`",
      "validate:part9-stage8",
      "Stage 8.1 Local App Packaging",
      "Stage 8.2 Release Safety",
      "Stage 8 overall review",
      "不进入 Part 10",
    ]),
    "part9_model_parameters_current",
    "Model parameters record Part 9 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 9 review gate",
  );
}

try {
  validateStage8Reviews();
  validateStage8Contracts();
  validateStage8DocsAndModel();
  validateProductionDoesNotImportExperiments();
  validateStage8Gates();
  validateInstalledLocalAppRuntime();
  validatePart9DocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "9", scope: ["8.1", "8.2", "stage8"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part9_stage8_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "9", scope: ["8.1", "8.2", "stage8"], checks }, null, 2));
  process.exit(1);
}
