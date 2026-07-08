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

const taskId = "MA-V12-S10P2";
const acceptanceId = "ACC-MA-V12-S10P2";
const status = "phase_s10_p2_global_chinese_ux_completed_pending_s10_p3";
const validatorName = "validate:v1.2-s10-p2";
const scriptName = "validate_memory_atlas_v1_2_s10_p2.cjs";
const globalChineseVersion = "global_chinese_ux.v1_2_s10_p2";

const allowedOpenDiffPaths = [
  "PRODUCT.md",
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/i18n/types.ts",
  "OpenAIDatabase/apps/memory-atlas/src/i18n/zh-CN.ts",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p3_machine_detail_folding.md",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_review.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/人类可读/25_全局中文说明.md",
  "OpenAIDatabase/人类可读/26_机器字段高级详情说明.md",
  "OpenAIDatabase/机器治理/README.md",
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

function hasCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
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
    "s10p2_open_diff_scope",
    "Open diff is limited to S10 P2 global Chinese UX, linter, validator and governance records",
    "S10 P2 has unrelated OpenAIDatabase changes",
    { changed, outside },
  );
}

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s10p2_package_script",
    "package.json exposes the v1.2 S10 P2 validator",
    "package.json is missing the v1.2 S10 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateGlobalChineseContract() {
  const app = readRepoFile("apps/memory-atlas/src/App.tsx");
  const copy = readRepoFile("apps/memory-atlas/src/i18n/zh-CN.ts");
  const types = readRepoFile("apps/memory-atlas/src/i18n/types.ts");
  assertCondition(
    hasAll(app, [
      `const GLOBAL_CHINESE_UX_VERSION = "${globalChineseVersion}" as const;`,
      "data-s10-p2-global-chinese-ux={GLOBAL_CHINESE_UX_VERSION}",
      "__memoryAtlasS10Phase2",
      "coreUiDefaultChinese: true",
      "machineTermsRequireChineseExplanation: true",
      "atlasctl audit --check chinese-ux",
    ]),
    "s10p2_app_contract",
    "App.tsx exposes the S10 P2 global Chinese UX runtime contract",
    "App.tsx is missing the S10 P2 global Chinese UX contract",
  );
  assertCondition(
    hasAll(types, [
      "weatherTitle: string;",
      "miniStarfieldTitle: string;",
      "riverPulseTitle: string;",
      "nextBestActionsTitle: string;",
      "proposalOnlyLabel: string;",
      "inspectorTitle: string;",
    ]),
    "s10p2_i18n_shape",
    "Chinese UI copy type covers the core S10 P2 homepage labels",
    "Chinese UI copy type is missing S10 P2 label fields",
  );

  const requiredCopy = [
    ["weatherTitle", "记忆天气"],
    ["miniStarfieldTitle", "轻量星图"],
    ["riverPulseTitle", "时间脉冲"],
    ["nextBestActionsTitle", "下一步行动"],
    ["proposalOnlyLabel", "仅生成提案"],
    ["inspectorTitle", "证据入口"],
    ["inspectorHint", "同步焦点"],
  ];
  const badCopy = [];
  for (const [key, required] of requiredCopy) {
    const match = copy.match(new RegExp(`${key}:\\s*"([^"]+)"`));
    const value = match?.[1] || "";
    if (!value.includes(required) || !hasCjk(value)) badCopy.push(`${key}:${value || "missing"}`);
  }
  for (const exactEnglish of [
    'weatherTitle: "Memory Weather v2"',
    'miniStarfieldTitle: "Mini Starfield"',
    'riverPulseTitle: "River Pulse"',
    'nextBestActionsTitle: "Next Best Actions"',
    'inspectorTitle: "Inspector Deep Link"',
  ]) {
    if (copy.includes(exactEnglish)) badCopy.push(`exact_english:${exactEnglish}`);
  }
  assertCondition(
    badCopy.length === 0,
    "s10p2_chinese_copy_defaults",
    "Core homepage titles, insight headers and proposal boundary labels default to Chinese",
    "Core homepage copy is still English-first",
    { badCopy },
  );

  const blockedVisibleFragments = [
    "<dt>Stable</dt>",
    "<dt>Momentum</dt>",
    "<dt>Risk</dt>",
    "<dt>Opportunity</dt>",
    "top actions</small>",
    "top actions=",
    "<small>Universe State derived</small>",
    "<span>proposal-only</span>",
    " assets</small>",
    " themes</small>",
    "<i>Value ",
    "<i>Strength ",
    " records</i>",
    "day half-life",
  ];
  const blockedPresent = blockedVisibleFragments.filter((fragment) => app.includes(fragment));
  assertCondition(
    blockedPresent.length === 0,
    "s10p2_no_english_first_home_fragments",
    "Known English-first homepage labels have Chinese defaults or Chinese explanations",
    "Known homepage labels remain English-first",
    { blockedPresent },
  );
}

function validateChineseUxAudit() {
  const result = run("python3", ["scripts/atlasctl.py", "audit", "--check", "chinese-ux"], { cwd: repoRoot });
  const payload = parseJsonFromStdout(result);
  const acceptedTaskIds = [taskId, "MA-V12-S10P3"];
  const acceptedAcceptanceIds = [acceptanceId, "ACC-MA-V12-S10P3"];
  assertCondition(
    payload.status === "PASS" &&
      payload.check === "chinese-ux" &&
      acceptedTaskIds.includes(payload.task_id) &&
      acceptedAcceptanceIds.includes(payload.acceptance_id) &&
      payload.details?.home_arrival_briefing === true &&
      payload.details?.s10_p2_global_chinese === true &&
      payload.details?.core_ui_default_chinese === true &&
      payload.details?.machine_terms_with_chinese_explanation === true,
    "s10p2_chinese_ux_audit",
    "atlasctl chinese-ux audit passes the S10 P2 global Chinese UX gate",
    "atlasctl chinese-ux audit did not pass S10 P2",
    payload,
  );
}

function validateRecords() {
  const reviewPath = "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s10_p2_global_chinese_ux.md";
  [
    "PRODUCT.md",
    reviewPath,
    "OpenAIDatabase/人类可读/25_全局中文说明.md",
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
      globalChineseVersion,
      "pending S10 P3",
      "No GitHub main upload in this phase",
      "No proposal apply execution",
      "No raw mutation",
      "Chinese UX linter",
    ]),
    "s10p2_records",
    "S10 P2 review, feature, development, parameter, delivery and gate records are synchronized",
    "S10 P2 governance records are incomplete",
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
    "s10p2_raw_unchanged",
    "No raw archive changes are present in S10 P2",
    "S10 P2 changed raw archive paths",
    { stdout: result.stdout.slice(0, 1000), status: result.status },
  );
}

function main() {
  validateOpenDiffScope();
  validatePackageScript();
  validateGlobalChineseContract();
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
