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

const taskId = "MA-V12-S10P3";
const acceptanceId = "ACC-MA-V12-S10P3";
const status = "phase_s10_p3_machine_detail_folding_completed_pending_s10_review";
const validatorName = "validate:v1.2-s10-p3";
const scriptName = "validate_memory_atlas_v1_2_s10_p3.cjs";
const machineDetailVersion = "machine_detail_folding.v1_2_s10_p3";

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
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_review.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s11_p1_clio_like_visuals.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
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

function validateTextFile(relativePath) {
  const source = relativePath.startsWith("OpenAIDatabase/") || relativePath === "PRODUCT.md"
    ? readWorktreeFile(relativePath)
    : readRepoFile(relativePath);
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
    "s10p3_open_diff_scope",
    "Open diff is limited to S10 P3 machine detail folding, validator and governance records",
    "S10 P3 has unrelated OpenAIDatabase changes",
    { changed, outside },
  );
}

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s10p3_package_script",
    "package.json exposes the v1.2 S10 P3 validator",
    "package.json is missing the v1.2 S10 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateMachineDetailContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const copy = readRepoFile("apps/memory-atlas/src/i18n/zh-CN.ts");
  const styles = readRepoFile("apps/memory-atlas/src/styles.css");
  assertCondition(
    hasAll(app, [
      `const MACHINE_DETAIL_FOLDING_VERSION = "${machineDetailVersion}" as const;`,
      "data-s10-p3-machine-detail-folding={MACHINE_DETAIL_FOLDING_VERSION}",
      "__memoryAtlasS10Phase3",
      "machineFieldsDefaultCollapsed: true",
      "advancedDetailsEntryVisible: true",
      "defaultHumanReadableFirst: true",
      "data-s10-p3-machine-fields=\"collapsed-by-default\"",
    ]),
    "s10p3_runtime_contract",
    "App.tsx exposes the S10 P3 machine detail folding runtime contract",
    "App.tsx is missing the S10 P3 runtime contract",
  );

  assertCondition(
    hasAll(copy, [
      "高级详情：机器字段",
      "显示高级详情",
      "隐藏高级详情",
      "默认折叠，仅用于核验字段",
    ]),
    "s10p3_chinese_advanced_detail_copy",
    "Advanced machine detail entry copy is Chinese and explains default folding",
    "Advanced machine detail copy is missing or not Chinese-first",
  );

  const blockedVisibleMachineFragments = [
    "<h3>search_session_summary</h3>",
    "<dt>query</dt>",
    "<dt>dominant_topics</dt>",
    "<dt>proposal_candidate</dt>",
    "<h4>change_comparison</h4>",
    "<h4>stale_conflict_signals</h4>",
    "<h4>proposal_candidates</h4>",
    "<span>{summaryClosure.change_comparison.length} signals</span>",
    "<span>{summaryClosure.stale_conflict_signals.length} checks</span>",
    "<span>{summaryClosure.proposal_candidates.length} candidates</span>",
  ];
  const blockedPresent = blockedVisibleMachineFragments.filter((fragment) => app.includes(fragment));
  assertCondition(
    blockedPresent.length === 0,
    "s10p3_machine_fields_not_default_visible",
    "Known machine fields are no longer visible in default review/search/summary layers",
    "Known machine fields remain default-visible",
    { blockedPresent },
  );

  assertCondition(
    hasAll(styles, [
      ".machine-field-details",
      ".machine-field-help",
      ".inline-machine-field-details",
    ]),
    "s10p3_machine_detail_styles",
    "Machine detail folding styles exist for default-collapsed advanced details",
    "Machine detail folding styles are missing",
  );
}

function validateChineseUxAudit() {
  const result = run("python3", ["scripts/atlasctl.py", "audit", "--check", "chinese-ux"], { cwd: repoRoot });
  const payload = parseJsonFromStdout(result);
  assertCondition(
    payload.status === "PASS" &&
      payload.check === "chinese-ux" &&
      payload.task_id === taskId &&
      payload.acceptance_id === acceptanceId &&
      payload.details?.home_arrival_briefing === true &&
      payload.details?.s10_p2_global_chinese === true &&
      payload.details?.s10_p3_machine_detail_folding === true &&
      payload.details?.machine_fields_default_folded === true &&
      payload.details?.advanced_details_entry_visible === true,
    "s10p3_chinese_ux_audit",
    "atlasctl chinese-ux audit passes the S10 P3 machine detail folding gate",
    "atlasctl chinese-ux audit did not pass S10 P3",
    payload,
  );
}

function validateRecords() {
  const reviewPath = "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md";
  [
    "PRODUCT.md",
    reviewPath,
    "OpenAIDatabase/人类可读/26_机器字段高级详情说明.md",
    "OpenAIDatabase/功能清单.md",
    "OpenAIDatabase/开发记录.md",
    "OpenAIDatabase/模型参数文件.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
    "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
    "OpenAIDatabase/CHANGELOG.md",
    "OpenAIDatabase/人类可读/00_快速入口.md",
    "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
    "OpenAIDatabase/机器治理/README.md",
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
    "OpenAIDatabase/人类可读/00_快速入口.md",
    "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
    "OpenAIDatabase/机器治理/README.md",
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
      machineDetailVersion,
      "pending S10 Review",
      "机器字段默认折叠",
      "高级详情入口",
      "No GitHub main upload in this phase",
      "No proposal apply execution",
      "No raw mutation",
    ]),
    "s10p3_records",
    "S10 P3 review, feature, development, parameter, delivery and gate records are synchronized",
    "S10 P3 governance records are incomplete",
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
    "s10p3_raw_unchanged",
    "No raw archive changes are present in S10 P3",
    "S10 P3 changed raw archive paths",
    { stdout: result.stdout.slice(0, 1000), status: result.status },
  );
}

function main() {
  validateOpenDiffScope();
  validatePackageScript();
  validateMachineDetailContract();
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
