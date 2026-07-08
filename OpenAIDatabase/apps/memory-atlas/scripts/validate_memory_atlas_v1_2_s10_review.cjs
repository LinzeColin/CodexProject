#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

process.env.GIT_TERMINAL_PROMPT = process.env.GIT_TERMINAL_PROMPT || "0";
process.env.GIT_SSH_COMMAND =
  process.env.GIT_SSH_COMMAND || "ssh -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=1";

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S10-REVIEW";
const acceptanceId = "ACC-MA-V12-S10-REVIEW";
const status = "stage_s10_review_passed_pending_s11_no_github_main_upload";
const validatorName = "validate:v1.2-s10-review";
const scriptName = "validate_memory_atlas_v1_2_s10_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s10_review.md";

const phaseValidators = [
  ["validate:v1.2-s10-p1", "validate_memory_atlas_v1_2_s10_p1.cjs", "MA-V12-S10P1", "ACC-MA-V12-S10P1"],
  ["validate:v1.2-s10-p2", "validate_memory_atlas_v1_2_s10_p2.cjs", "MA-V12-S10P2", "ACC-MA-V12-S10P2"],
  ["validate:v1.2-s10-p3", "validate_memory_atlas_v1_2_s10_p3.cjs", "MA-V12-S10P3", "ACC-MA-V12-S10P3"],
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const textFiles = [
  reviewPath,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s09_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s10_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  "OpenAIDatabase/apps/memory-atlas/src/App.tsx",
  "OpenAIDatabase/apps/memory-atlas/src/i18n/zh-CN.ts",
  "OpenAIDatabase/apps/memory-atlas/src/styles.css",
  "OpenAIDatabase/scripts/atlasctl.py",
  "OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py",
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
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
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
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

function readJson(relativePath) {
  return JSON.parse(readRepoFile(relativePath));
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
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
    "s10_review_open_diff_scope",
    "Open diff is limited to S10 Review files and S10 review fix surfaces",
    "S10 Review has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s10_review_package_script",
    "package.json exposes the v1.2 S10 Review validator",
    "package.json is missing the v1.2 S10 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateReviewArtifact() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "validate:v1.2-s10-p1",
      "validate:v1.2-s10-p2",
      "validate:v1.2-s10-p3",
      "首页能回答上次来以后发生了什么",
      "核心 UI 默认中文",
      "机器字段默认折叠",
      "Chinese UX linter",
      "结论 / 变化 / 证据 / 行动",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "No proposal apply execution",
      "pending S11 P1",
    ]),
    "s10_review_artifact",
    "S10 Review artifact records phase chain, pass gate, boundaries and pending S11 P1",
    "S10 Review artifact is missing required review evidence",
  );
}

function validatePhaseValidators() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  const details = {};
  for (const [script, file, phaseTaskId, phaseAcceptanceId] of phaseValidators) {
    assertCondition(
      packageJson.scripts?.[script] === `node scripts/${file}`,
      `s10_review_phase_script_${script}`,
      `${script} is registered`,
      `${script} is missing from package.json`,
      { script: packageJson.scripts?.[script] },
    );
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 120000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === phaseTaskId && result.acceptance_id === phaseAcceptanceId,
      `s10_review_phase_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("s10_review_phase_validator_chain", "S10 P1/P2/P3 validators pass in sequence", details);
}

function validateChineseUxAndVisualAudits() {
  const chineseUx = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "audit", "--check", "chinese-ux"], { cwd: repoRoot }));
  assertCondition(
    chineseUx.status === "PASS" &&
      chineseUx.task_id === "MA-V12-S10P3" &&
      chineseUx.acceptance_id === "ACC-MA-V12-S10P3" &&
      chineseUx.details?.home_arrival_briefing === true &&
      chineseUx.details?.s10_p2_global_chinese === true &&
      chineseUx.details?.s10_p3_machine_detail_folding === true &&
      chineseUx.details?.default_visible_machine_fragments_removed === true,
    "s10_review_chinese_ux_audit",
    "atlasctl chinese-ux audit covers S10 P1/P2/P3 and passes",
    "atlasctl chinese-ux audit does not prove S10 P1/P2/P3",
    chineseUx,
  );
  const visual = parseJsonFromStdout(run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", "."], { cwd: repoRoot, timeout: 120000 }));
  const humanSummary = (visual.checks || []).find((check) => check.name === "memory_atlas_has_human_facing_summary");
  assertCondition(
    visual.status === "PASS" && humanSummary?.status === "PASS",
    "s10_review_visual_acceptance_audit",
    "Visual acceptance audit confirms the human-facing summary layer after S10 Review",
    "Visual acceptance audit does not confirm human-facing S10 UI",
    { status: visual.status, humanSummary },
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    "validate:v1.2-s10-review",
    "S10 P1",
    "S10 P2",
    "S10 P3",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "No proposal apply",
    "S11 P1",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s10_review_records_${relativePath}`,
      `${relativePath} records S10 Review status, validator, boundaries and next phase`,
      `${relativePath} is missing S10 Review record fragments`,
      { missing },
    );
  }
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S10 Review 已完成", "下一步是 S11 P1", "No GitHub main upload"]),
    "s10_review_quick_entry",
    "Quick entry points to completed S10 Review and pending S11 P1",
    "Quick entry does not point to completed S10 Review and pending S11 P1",
  );
  assertCondition(
    hasAll(overview, ["S10 Review 已完成", "首页能回答上次来以后发生了什么", "核心 UI 默认中文", "机器字段默认折叠", "下一步是 S11 P1"]),
    "s10_review_overview",
    "Human overview records S10 Review pass gate and pending S11 P1",
    "Human overview is missing S10 Review pass gate",
  );
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, "validate:v1.2-s10-review", "S11 P1"]),
    "s10_review_machine_readme",
    "Machine README records S10 Review as current gate",
    "Machine README is missing S10 Review current gate",
  );
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, "validate:v1.2-s10-review", "S10 Review 产物", "S11 P1"]),
    "s10_review_run_gate",
    "Run gate README records S10 Review artifact, validator and next phase",
    "Run gate README is missing S10 Review gate",
  );
}

function validateNoRawOrForbiddenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.includes("secrets") ||
      file.includes("credentials"),
  );
  const publicRawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff.length === 0,
    "s10_review_no_raw_or_secret_open_changes",
    "S10 Review open diff does not modify raw, private imports, credentials or secrets",
    "S10 Review has forbidden raw or secret changes",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    for (const file of textFiles) validateTextFile(file);
    validateReviewArtifact();
    validatePhaseValidators();
    validateChineseUxAndVisualAudits();
    validateRecords();
    validateNoRawOrForbiddenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.error(JSON.stringify({
      status: "FAIL",
      validator: scriptName.replace(/\.cjs$/, ""),
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || {},
      stdout: error.stdout,
      stderr: error.stderr,
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
