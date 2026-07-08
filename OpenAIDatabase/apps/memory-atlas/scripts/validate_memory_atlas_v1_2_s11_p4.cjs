#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

process.env.GIT_TERMINAL_PROMPT = process.env.GIT_TERMINAL_PROMPT || "0";

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S11P4";
const acceptanceId = "ACC-MA-V12-S11P4";
const status = "phase_s11_p4_human_question_map_completed_pending_s11_review";
const validatorName = "validate:v1.2-s11-p4";
const scriptName = "validate_memory_atlas_v1_2_s11_p4.cjs";
const mapVersion = "human_question_map.v1_2_s11_p4";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s11_p4_human_question_map.md";
const humanDocPath = "人类可读/30_HumanQuestionMap说明.md";
const visualConfigPath = "机器治理/可视化配置/human_question_map.v1_2_s11_p4.json";

const requiredVisualIds = [
  "cluster_tree",
  "bubble_map",
  "topic_cluster_explorer",
  "task_treemap",
  "automation_vs_augmentation",
  "roi_scatter",
  "opportunity_radar",
  "agent_decision_sankey",
  "friction_heatmap",
  "latent_radar",
  "evidence_timeline",
  "formula_explorer",
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  `OpenAIDatabase/${visualConfigPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
];

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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  return JSON.parse(stdout.slice(stdout.indexOf("{")));
}

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function readWorktreeFile(relativePath) {
  return fs.readFileSync(path.join(worktreeRoot, relativePath), "utf8");
}

function readJson(relativePath) {
  return JSON.parse(readRepoFile(relativePath));
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
}

function hasCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
}

function validateTextFile(relativePath) {
  const source = relativePath.startsWith("OpenAIDatabase/") ? readWorktreeFile(relativePath) : readRepoFile(relativePath);
  assertCondition(source.endsWith("\n"), `${relativePath}:final_newline`, `${relativePath} has a final newline`, `${relativePath} is missing a final newline`);
  const blocked = [String.fromCharCode(0xfffd), String.fromCharCode(0x00c2), String.fromCharCode(0x00c3), "\u0000"];
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (blocked.some((char) => line.includes(char))) badLines.push(`${index + 1}:mojibake`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no blocked mojibake characters, null bytes or trailing whitespace`,
    `${relativePath} contains blocked characters, null bytes or trailing whitespace`,
    { badLines: badLines.slice(0, 20) },
  );
}

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all", "--", "OpenAIDatabase"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .sort();
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s11p4_open_diff_scope",
    "Open diff is limited to S11 P4 Human Question Map, previous validator compatibility and governance records",
    "S11 P4 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s11p4_previous_s11p3_deferred_until_clean_tree", "S11 P3 clean-tree validator will be re-run after S11 P4 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s11_p3.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S11P3",
    "s11p4_previous_s11p3",
    "S11 P3 validator passes before accepting S11 P4 on a clean tree",
    "S11 P3 validator did not pass before S11 P4",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s11p4_package_script",
    "package.json exposes the v1.2 S11 P4 validator",
    "package.json is missing the v1.2 S11 P4 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateRuntimeContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(app, [
      `const HUMAN_QUESTION_MAP_VERSION = "${mapVersion}" as const;`,
      "data-s11-p4-human-question-map={HUMAN_QUESTION_MAP_VERSION}",
      "__memoryAtlasS11Phase4",
      "buildHumanQuestionMapModel(",
      "HumanQuestionMapPanel",
      "data-s11-p4-map-entry",
      "data-s11-p4-human-question",
      "data-s11-p4-action-value",
      "data-s11-p4-visual-roi-gate",
      "data-s11-p4-p0-included",
      "data-s11-p4-filter-source",
      "data-s11-p4-filter-time",
      "data-s11-p4-filter-project",
      "data-s11-p4-filter-task",
      "data-s11-p4-interactive=\"true\"",
      "data-s11-p4-visual-id={entry.id}",
      ...requiredVisualIds.map((id) => `id: "${id}"`),
    ]),
    "s11p4_runtime_contract",
    "App.tsx exposes S11 P4 Human Question Map contract for all P1-P3 visuals, ROI gate flags and four filter dimensions",
    "App.tsx is missing the S11 P4 Human Question Map runtime contract",
  );
  assertCondition(
    hasAll(styles, [
      ".human-question-map-panel",
      ".human-question-map-grid",
      ".human-question-map-entry",
      ".human-question-map-gate-row",
      ".human-question-map-exclusion-list",
    ]),
    "s11p4_styles",
    "S11 P4 Human Question Map has dedicated responsive styles",
    "S11 P4 Human Question Map styles are missing",
  );
}

function validateVisualConfig() {
  validateTextFile(visualConfigPath);
  const config = readJson(visualConfigPath);
  const visuals = Array.isArray(config.visuals) ? config.visuals : [];
  const excluded = Array.isArray(config.excluded_candidates) ? config.excluded_candidates : [];
  const byId = new Map(visuals.map((visual) => [visual.id, visual]));
  const missing = requiredVisualIds.filter((id) => !byId.has(id));
  const invalid = visuals.filter((visual) => {
    const filters = Array.isArray(visual.filter_dimensions) ? visual.filter_dimensions : [];
    return (
      !requiredVisualIds.includes(visual.id) ||
      !hasCjk(visual.human_question_zh) ||
      !hasCjk(visual.action_value_zh) ||
      !hasCjk(visual.insight_header_zh) ||
      visual.visual_roi_gate_pass !== true ||
      visual.p0_included !== true ||
      visual.static_decoration === true ||
      !["source", "time", "project", "task"].every((dimension) => filters.includes(dimension))
    );
  });
  const forbiddenP0 = excluded.filter((candidate) => candidate.visual_roi_gate_pass !== false || candidate.p0_included !== false);
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      config.schema_version === mapVersion &&
      missing.length === 0 &&
      invalid.length === 0 &&
      excluded.length >= 2 &&
      forbiddenP0.length === 0,
    "s11p4_human_question_map_config",
    "S11 P4 config maps all P0 visuals to Chinese questions/actions and excludes failing Visual ROI candidates from P0",
    "S11 P4 Human Question Map config is missing required map or ROI gate contracts",
    { missing, invalid: invalid.map((item) => item.id), forbiddenP0: forbiddenP0.map((item) => item.id) },
  );
}

function validateAtlasctlVisualRoi() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit", "--check", "visual-roi"], { cwd: repoRoot }));
  assertCondition(
    payload.status === "PASS" && payload.check === "visual-roi" && payload.p0_visual_count >= 10 && payload.failed_p0_count === 0,
    "s11p4_visual_roi_audit",
    "atlasctl visual-roi audit passes with legacy S07 P0 gate and no failed P0 visuals; S11 P4 config adds the 12-visual Human Question Map",
    "atlasctl visual-roi audit does not pass for S11 P4",
    payload,
  );
}

function validateVisualAcceptanceAudit() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", "."], { cwd: repoRoot }));
  assertCondition(
    payload.status === "PASS",
    "s11p4_visual_acceptance_audit",
    "visual acceptance audit passes after Human Question Map",
    "visual acceptance audit does not pass after S11 P4",
    payload,
  );
}

function validateRecords() {
  [
    reviewPath,
    humanDocPath,
    "机器治理/可视化配置/README.md",
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);

  const required = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "Human Question Map",
    "Visual ROI Gate",
    "source/time/project/task",
    "No GitHub main upload in this phase",
    "pending S11 Review",
  ];
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [...required, ...requiredVisualIds]),
    "s11p4_review_artifact",
    "S11 P4 review artifact records all visual ids, questions, ROI gate and pending S11 Review",
    "S11 P4 review artifact is missing required fragments",
  );
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "No GitHub main upload in this phase", "pending S11 Review"]),
      `s11p4_records_${relativePath}`,
      `${relativePath} records S11 P4 status, validator, no-upload boundary and next review gate`,
      `${relativePath} is missing S11 P4 delivery record fragments`,
    );
  }
  assertCondition(
    hasAll(readRepoFile("人类可读/00_快速入口.md"), ["S11 P4 已完成", "Human Question Map", "下一步是 S11 Review"]),
    "s11p4_quick_entry",
    "Quick entry points to completed S11 P4 and pending S11 Review",
    "Quick entry does not point to completed S11 P4 and pending S11 Review",
  );
  assertCondition(
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [taskId, acceptanceId, status, validatorName, "S11 P4 产物", "S11 Review"]),
    "s11p4_run_gate",
    "Run gate README records S11 P4 artifact, validator and next stage review",
    "Run gate README is missing S11 P4 gate records",
  );
}

function validateNoRawOrSecretChanges() {
  const changed = getOpenChangedPaths();
  const forbidden = changed.filter((file) => (
    file.includes("/data/public_raw/") ||
    file.includes("/data/raw/") ||
    file.includes("/private_imports/") ||
    file.includes(".env") ||
    file.includes("secret") ||
    file.includes("token")
  ));
  assertCondition(
    forbidden.length === 0,
    "s11p4_no_raw_or_secret_open_changes",
    "S11 P4 open diff does not modify raw, private imports, credentials or secrets",
    "S11 P4 open diff modifies forbidden raw/private/secret paths",
    { changed, forbidden },
  );
}

function main() {
  validatePackageScript();
  validateOpenDiffScope();
  validatePreviousGate();
  validateRuntimeContract();
  validateVisualConfig();
  validateAtlasctlVisualRoi();
  validateVisualAcceptanceAudit();
  validateRecords();
  validateNoRawOrSecretChanges();
  console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_2_s11_p4",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details,
    stdout: error.stdout,
    stderr: error.stderr,
    checks,
  }, null, 2));
  process.exit(1);
}
