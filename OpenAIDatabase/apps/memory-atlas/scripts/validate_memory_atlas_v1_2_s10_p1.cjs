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

const taskId = "MA-V12-S10P1";
const acceptanceId = "ACC-MA-V12-S10P1";
const status = "phase_s10_p1_home_arrival_briefing_completed_pending_s10_p2";
const validatorName = "validate:v1.2-s10-p1";
const scriptName = "validate_memory_atlas_v1_2_s10_p1.cjs";
const arrivalVersion = "home_arrival_briefing.v1_2_s10_p1";

const allowedOpenDiffPaths = [
  "PRODUCT.md",
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s11_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/i18n/types.ts",
  "OpenAIDatabase/apps/memory-atlas/src/i18n/zh-CN.ts",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p1_home_arrival_briefing.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_review.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s11_p1_clio_like_visuals.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/人类可读/24_首页上次来以后发生了什么说明.md",
  "OpenAIDatabase/人类可读/25_全局中文说明.md",
  "OpenAIDatabase/人类可读/26_机器字段高级详情说明.md",
  "OpenAIDatabase/人类可读/27_ClioLike多维可视化说明.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
  "OpenAIDatabase/机器治理/可视化配置/clio_like_visuals.v1_2_s11_p1.json",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py",
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
    maxBuffer: 64 * 1024 * 1024,
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

function validateTextFile(relativePath) {
  const source = relativePath.startsWith("OpenAIDatabase/")
    ? readWorktreeFile(relativePath)
    : readWorktreeFile(relativePath);
  assertCondition(source.endsWith("\n"), `${relativePath}:final_newline`, `${relativePath} has final newline`, `${relativePath} is missing final newline`);
  const badLines = [];
  source.split("\n").forEach((line, index) => {
    if (line.trimEnd() !== line) badLines.push(`${index + 1}:trailing`);
    if (line.includes("\u0000") || line.includes(String.fromCharCode(0xfffd))) badLines.push(`${index + 1}:blocked_char`);
  });
  assertCondition(
    badLines.length === 0,
    `${relativePath}:text_clean`,
    `${relativePath} has no trailing whitespace or blocked characters`,
    `${relativePath} contains trailing whitespace or blocked characters`,
    { badLines: badLines.slice(0, 20) },
  );
}

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all", "--", "PRODUCT.md", "OpenAIDatabase"], {
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
    "s10p1_open_diff_scope",
    "Open diff is limited to S10 P1 homepage, validator, product context and governance records",
    "S10 P1 has unrelated OpenAIDatabase changes",
    { changed, outside },
  );
}

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s10p1_package_script",
    "package.json exposes the v1.2 S10 P1 validator",
    "package.json is missing the v1.2 S10 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateHomeArrivalBriefing() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const copy = readRepoFile("apps/memory-atlas/src/i18n/zh-CN.ts");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  const sectionIndex = app.indexOf("data-home-section=\"arrival_briefing\"");
  const weatherIndex = app.indexOf("data-home-section=\"weather\"");
  const acceptedPendingProposalCopy =
    (app.includes("待授权 proposal") || app.includes("待授权提案"))
    && (copy.includes('pendingProposal: "待授权 proposal"') || copy.includes('pendingProposal: "待授权提案"'));
  assertCondition(
    sectionIndex >= 0 && weatherIndex >= 0 && sectionIndex < weatherIndex,
    "s10p1_arrival_briefing_first",
    "Arrival briefing is rendered before the older weather/galaxy-oriented sections",
    "Arrival briefing is missing or not the first home decision section",
    { sectionIndex, weatherIndex },
  );
  assertCondition(
    hasAll(app, [
      `const HOME_ARRIVAL_BRIEFING_VERSION = "${arrivalVersion}" as const;`,
      "data-s10-p1-home-arrival-briefing={HOME_ARRIVAL_BRIEFING_VERSION}",
      "data-home-arrival-question={uiCopy.overview.arrivalQuestion}",
      "buildHomeArrivalBriefing(atlas, nodes, model, deltaStats)",
      "新增重要资料",
      "增强结论",
      "减弱或过期结论",
      "同步失败",
    ]) && acceptedPendingProposalCopy,
    "s10p1_app_contract",
    "App.tsx contains the S10 P1 arrival briefing contract and required categories",
    "App.tsx is missing S10 P1 arrival briefing contract fragments",
  );
  assertCondition(
    hasAll(copy, [
      "arrivalQuestion: \"上次来以后发生了什么\"",
      "arrivalTitle: \"上次来以后发生了什么\"",
      "newMaterial: \"新增重要资料\"",
      "strengthened: \"增强结论\"",
      "weakened: \"减弱或过期结论\"",
      "syncFailure: \"同步失败\"",
    ]) && acceptedPendingProposalCopy,
    "s10p1_chinese_copy",
    "Chinese copy contains the arrival question and five required status categories",
    "Chinese copy is missing S10 P1 required labels",
  );
  assertCondition(
    hasAll(styles, [
      ".home-arrival-briefing",
      ".arrival-briefing-grid",
      ".arrival-briefing-card",
      ".arrival-briefing-next-step",
      ".arrival-briefing-machine-details",
    ]),
    "s10p1_styles",
    "S10 P1 homepage styles are present with folded machine details support",
    "S10 P1 homepage styles are missing",
  );
}

function validateChineseUxAudit() {
  const result = run("python3", ["scripts/atlasctl.py", "audit", "--check", "chinese-ux"], { cwd: repoRoot });
  const payload = JSON.parse(result.stdout.slice(result.stdout.indexOf("{")));
  const acceptedTaskIds = [taskId, "MA-V12-S10P2", "MA-V12-S10P3"];
  const acceptedAcceptanceIds = [acceptanceId, "ACC-MA-V12-S10P2", "ACC-MA-V12-S10P3"];
  assertCondition(
    payload.status === "PASS" &&
      payload.check === "chinese-ux" &&
      acceptedTaskIds.includes(payload.task_id) &&
      acceptedAcceptanceIds.includes(payload.acceptance_id) &&
      payload.details?.home_arrival_briefing === true,
    "s10p1_chinese_ux_audit",
    "atlasctl chinese-ux audit passes for S10 P1 arrival briefing through the current Chinese UX gate",
    "atlasctl chinese-ux audit did not pass S10 P1",
    payload,
  );
}

function validateRecords() {
  const reviewPath = "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p1_home_arrival_briefing.md";
  [
    "PRODUCT.md",
    reviewPath,
    "OpenAIDatabase/人类可读/24_首页上次来以后发生了什么说明.md",
    "OpenAIDatabase/功能清单.md",
    "OpenAIDatabase/开发记录.md",
    "OpenAIDatabase/模型参数文件.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "OpenAIDatabase/CHANGELOG.md",
    "OpenAIDatabase/机器治理/运行门禁/README.md",
  ].forEach(validateTextFile);

  const combined = [
    reviewPath,
    "OpenAIDatabase/功能清单.md",
    "OpenAIDatabase/开发记录.md",
    "OpenAIDatabase/模型参数文件.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "OpenAIDatabase/CHANGELOG.md",
    "OpenAIDatabase/机器治理/运行门禁/README.md",
  ]
    .map(readWorktreeFile)
    .join("\n");

  assertCondition(
    hasAll(combined, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      arrivalVersion,
      "pending S10 P2",
      "No GitHub main upload in this phase",
      "No proposal apply execution",
      "No raw mutation",
    ]),
    "s10p1_records",
    "S10 P1 review, feature, development, parameter, delivery and gate records are synchronized",
    "S10 P1 governance records are incomplete",
  );
}

function validateRawUnchanged() {
  const result = spawnSync("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
  });
  assertCondition(
    result.stdout.trim() === "",
    "s10p1_raw_unchanged",
    "No raw archive changes are present in S10 P1",
    "S10 P1 changed raw archive paths",
    { stdout: result.stdout.slice(0, 1000), status: result.status },
  );
}

function main() {
  validateOpenDiffScope();
  validatePackageScript();
  validateHomeArrivalBriefing();
  validateChineseUxAudit();
  validateRecords();
  validateRawUnchanged();

  console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(
    JSON.stringify(
      {
        status: "FAIL",
        task_id: taskId,
        acceptance_id: acceptanceId,
        message: error.message,
        details: error.details || {},
        stdout: error.stdout,
        stderr: error.stderr,
        checks,
      },
      null,
      2,
    ),
  );
  process.exit(1);
}
