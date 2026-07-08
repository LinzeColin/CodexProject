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

const taskId = "MA-V12-S11P1";
const acceptanceId = "ACC-MA-V12-S11P1";
const status = "phase_s11_p1_clio_like_visuals_completed_pending_s11_p2";
const validatorName = "validate:v1.2-s11-p1";
const scriptName = "validate_memory_atlas_v1_2_s11_p1.cjs";
const visualVersion = "clio_like_visuals.v1_2_s11_p1";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s11_p1_clio_like_visuals.md";
const humanDocPath = "人类可读/27_ClioLike多维可视化说明.md";
const visualConfigPath = "机器治理/可视化配置/clio_like_visuals.v1_2_s11_p1.json";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_review.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py",
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
    "s11p1_open_diff_scope",
    "Open diff is limited to S11 P1 Clio-like visuals, validator and governance records",
    "S11 P1 has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validatePreviousGate() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s11p1_previous_s10_review_deferred_until_clean_tree", "S10 Review clean-tree validator will be re-run after S11 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s10_review.cjs"], { cwd: appRoot, timeout: 300000 }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S10-REVIEW",
    "s11p1_previous_s10_review",
    "S10 Review validator passes before accepting S11 P1 on a clean tree",
    "S10 Review validator did not pass before S11 P1",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s11p1_package_script",
    "package.json exposes the v1.2 S11 P1 validator",
    "package.json is missing the v1.2 S11 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateRuntimeContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(app, [
      `const CLIO_LIKE_VISUALS_VERSION = "${visualVersion}" as const;`,
      "data-s11-p1-clio-like-visuals={CLIO_LIKE_VISUALS_VERSION}",
      "__memoryAtlasS11Phase1",
      "buildClioLikeVisualModel(",
      "ClioLikeVisualPanel",
      "data-s11-p1-visual-id=\"cluster_tree\"",
      "data-s11-p1-visual-id=\"bubble_map\"",
      "data-s11-p1-visual-id=\"topic_cluster_explorer\"",
      "data-s11-p1-insight-header",
      "data-s11-p1-human-question",
      "data-s11-p1-action-value",
      "data-s11-p1-filter-source",
      "data-s11-p1-filter-time",
      "data-s11-p1-filter-project",
      "data-s11-p1-filter-task",
      "data-s11-p1-interactive=\"true\"",
    ]),
    "s11p1_runtime_contract",
    "App.tsx exposes S11 P1 Clio-like visual runtime contract, three visuals, Chinese headers and four filter dimensions",
    "App.tsx is missing the S11 P1 Clio-like visual runtime contract",
  );
  assertCondition(
    !hasAll(app, ["Task Treemap", "ROI Scatter", "Latent Radar", "Evidence Timeline"]),
    "s11p1_phase_boundary",
    "S11 P1 runtime does not implement S11 P2/P3 visual families",
    "S11 P1 appears to include later S11 visual families",
  );
  assertCondition(
    hasAll(styles, [
      ".clio-visual-panel",
      ".clio-visual-grid",
      ".clio-visual-card",
      ".cluster-tree-svg",
      ".bubble-map-svg",
      ".topic-cluster-explorer",
    ]),
    "s11p1_styles",
    "S11 P1 Clio-like visuals have dedicated styles for tree, bubble map and explorer",
    "S11 P1 visual styles are missing",
  );
}

function validateVisualConfig() {
  validateTextFile(visualConfigPath);
  const config = readJson(visualConfigPath);
  const visuals = Array.isArray(config.visuals) ? config.visuals : [];
  const byId = new Map(visuals.map((visual) => [visual.id, visual]));
  const required = ["cluster_tree", "bubble_map", "topic_cluster_explorer"];
  const missing = required.filter((id) => !byId.has(id));
  const invalid = visuals.filter((visual) => {
    const filters = Array.isArray(visual.filter_dimensions) ? visual.filter_dimensions : [];
    return (
      !required.includes(visual.id) ||
      !hasCjk(visual.insight_header_zh) ||
      !hasCjk(visual.human_question_zh) ||
      !hasCjk(visual.action_value_zh) ||
      visual.visual_roi_gate_pass !== true ||
      visual.static_decoration === true ||
      !["source", "time", "project", "task"].every((dimension) => filters.includes(dimension))
    );
  });
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.status === status &&
      config.schema_version === visualVersion &&
      missing.length === 0 &&
      invalid.length === 0,
    "s11p1_visual_config",
    "S11 P1 visual config defines three P0 Clio-like visuals with Chinese insight, question, action and four filter dimensions",
    "S11 P1 visual config is missing required visual contracts",
    { missing, invalid: invalid.map((item) => item.id) },
  );
}

function validateAtlasctlVisualRoi() {
  const payload = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit", "--check", "visual-roi"], { cwd: repoRoot }));
  assertCondition(
    payload.status === "PASS" && payload.check === "visual-roi" && payload.p0_visual_count >= 3 && payload.failed_p0_count === 0,
    "s11p1_visual_roi_audit",
    "atlasctl visual-roi audit passes before S11 P1 runtime visuals enter the UI",
    "atlasctl visual-roi audit does not pass",
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
    "Clio-like visuals",
    "cluster_tree",
    "bubble_map",
    "topic_cluster_explorer",
    "source/time/project/task",
    "No GitHub main upload in this phase",
    "pending S11 P2",
  ];
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, required),
    "s11p1_review_artifact",
    "S11 P1 review artifact records visual scope, filters, boundaries and pending S11 P2",
    "S11 P1 review artifact is missing required fragments",
  );
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "No GitHub main upload in this phase", "pending S11 P2"]),
      `s11p1_records_${relativePath}`,
      `${relativePath} records S11 P1 status, validator, no-upload boundary and next phase`,
      `${relativePath} is missing S11 P1 delivery record fragments`,
    );
  }
  assertCondition(
    hasAll(readRepoFile("人类可读/00_快速入口.md"), ["S11 P1 已完成", "Clio-like visuals", "下一步是 S11 P2"]),
    "s11p1_quick_entry",
    "Quick entry points to completed S11 P1 and pending S11 P2",
    "Quick entry does not point to completed S11 P1 and pending S11 P2",
  );
  assertCondition(
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [taskId, acceptanceId, status, validatorName, "S11 P1 产物", "S11 P2"]),
    "s11p1_run_gate",
    "Run gate README records S11 P1 artifact, validator and next phase",
    "Run gate README is missing S11 P1 gate records",
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
    "s11p1_no_raw_or_secret_open_changes",
    "S11 P1 open diff does not modify raw, private imports, credentials or secrets",
    "S11 P1 open diff modifies forbidden raw/private/secret paths",
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
  validateRecords();
  validateNoRawOrSecretChanges();
  console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_2_s11_p1",
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
