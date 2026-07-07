#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S01P2";
const acceptanceId = "ACC-MA-V12-S01P2";
const status = "phase_s01_p2_double_plane_created_pending_s01_p3";
const validatorName = "validate:v1.2-s01-p2";
const auditPath = "docs/reviews/memory_atlas_v1_2_s01_p2_double_plane_creation.md";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const humanFiles = [
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
];

const machineFiles = [
  "机器治理/README.md",
  "机器治理/参数与公式/README.md",
  "机器治理/数据契约/README.md",
  "机器治理/同步与备份/README.md",
  "机器治理/可视化配置/README.md",
  "机器治理/行为智能模型/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/测试与验收/README.md",
  "机器治理/证据与日志/README.md",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
  `OpenAIDatabase/${auditPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  ...humanFiles.map((file) => `OpenAIDatabase/${file}`),
  ...machineFiles.map((file) => `OpenAIDatabase/${file}`),
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

function readRepoFile(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
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
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .sort();
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(
    source.endsWith("\n"),
    `${relativePath}:final_newline`,
    `${relativePath} has a final newline`,
    `${relativePath} is missing a final newline`,
  );

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
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
    "s01p2_package_script",
    "package.json exposes the v1.2 S01 P2 validator",
    "package.json is missing the v1.2 S01 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateAuditArtifact() {
  validateTextFile(auditPath);
  const source = readRepoFile(auditPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S01 P2 Double Plane Creation",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S01 P2 Double Plane Creation",
      "S01 P1 completed",
      "S01 P3 not executed",
      "OpenAIDatabase/人类可读/00_快速入口.md",
      "OpenAIDatabase/机器治理/README.md",
      "root owner three files preserved",
      "No apps/scripts/tests/config move",
      "No v1.2 requirements freeze config in this phase",
      "No GitHub main upload in this phase",
    ]),
    "s01p2_audit_artifact",
    "S01 P2 audit records double-plane creation, P1 continuity, P3 deferral and no-upload/runtime boundaries",
    "S01 P2 audit artifact is incomplete",
  );
}

function validateHumanPlane() {
  humanFiles.forEach(validateTextFile);
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");

  assertCondition(
    hasAll(quickEntry, [
      "结论",
      "当前阶段",
      "S01 P2",
      "下一步",
      "S01 P3",
      "不是跳转页",
      "ChatGPT、Codex、后续其他 agent",
      "凭证不是 transcript",
      "No GitHub main upload in this phase",
    ]),
    "s01p2_human_quick_entry",
    "Human quick entry is Chinese, conclusion-first and independently useful",
    "Human quick entry is missing S01 P2 required content",
  );

  assertCondition(
    hasAll(overview, [
      "四线",
      "14 Stage",
      "Anthropic 化行为智能",
      "信息 ROI",
      "ChatGPT、Codex、后续其他 agent",
      "UIUX",
      "每次 run 最多只完成一个 phase",
      "整体完成后才上传 GitHub main",
    ]),
    "s01p2_human_overview",
    "Human overview records v1.2 four-line / 14-stage execution frame",
    "Human overview is missing v1.2 four-line / 14-stage content",
  );
}

function validateMachinePlane() {
  machineFiles.forEach(validateTextFile);
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  assertCondition(
    hasAll(machineReadme, [
      "机器治理",
      "参数与公式",
      "数据契约",
      "同步与备份",
      "可视化配置",
      "行为智能模型",
      "运行门禁",
      "测试与验收",
      "证据与日志",
      "不替代 apps/scripts/tests/config/data/docs/governance",
    ]),
    "s01p2_machine_readme",
    "Machine governance README records all v1.2 machine-plane subdirectories and non-replacement boundary",
    "Machine governance README is incomplete",
  );

  const p2Deferral = hasAll(runGateReadme, [
    "S01 P2",
    "S01 P3",
    "v1.2需求冻结清单",
    "本 phase 不写入需求冻结配置",
    "No GitHub main upload in this phase",
  ]);
  const p3Completion = hasAll(runGateReadme, [
    "当前阶段是 S01 P3",
    "v1.2需求冻结清单",
    "MA-V12-S01P3",
    "下一步是 S01 整体复审",
    "No GitHub main upload in this phase",
  ]);
  assertCondition(
    p2Deferral || p3Completion,
    "s01p2_machine_run_gate_readme",
    "Run gate README records either the original S01 P2 deferral or the later S01 P3 freeze completion",
    "Run gate README is missing S01 P2 deferral and S01 P3 completion markers",
  );

  const freezeConfig = path.join(repoRoot, "机器治理/运行门禁/v1.2需求冻结清单.json");
  const freezeConfigValid =
    !fs.existsSync(freezeConfig) ||
    hasAll(readRepoFile("机器治理/运行门禁/v1.2需求冻结清单.json"), [
      "v1.2 四线14Stage升级",
      "raw_public_authorization",
      "credentials_exclusion",
    ]);
  assertCondition(
    freezeConfigValid,
    "s01p2_no_requirements_freeze_config",
    "Requirements freeze config is either absent during S01 P2 or present as the later S01 P3 artifact",
    "Requirements freeze config exists but is not a valid S01 P3 freeze artifact",
  );
}

function validateRuntimeAndOwnerBoundary() {
  const requiredFiles = ["功能清单.md", "开发记录.md", "模型参数文件.md"];
  const requiredDirs = ["apps", "apps/memory-atlas", "scripts", "tests", "config", "data", "docs/governance"];
  requiredFiles.forEach((relativePath) => {
    assertCondition(
      fs.existsSync(path.join(repoRoot, relativePath)),
      `s01p2_owner_file_${relativePath}`,
      `${relativePath} is preserved as a root owner door`,
      `${relativePath} is missing`,
    );
  });
  requiredDirs.forEach((relativePath) => {
    assertCondition(
      fs.statSync(path.join(repoRoot, relativePath)).isDirectory(),
      `s01p2_runtime_dir_${relativePath}`,
      `${relativePath} directory still exists and was not moved`,
      `${relativePath} directory is missing`,
    );
  });
}

function validateRecords() {
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  records.forEach(([name]) => validateTextFile(name));
  records.forEach(([name, source]) => {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "memory_atlas_v1_2_s01_p2_double_plane_creation.md",
        "S01 P2",
        "No GitHub main upload in this phase",
      ]),
      `s01p2_records_${name}`,
      `${name} records v1.2 S01 P2 status, validator, evidence and no-upload boundary`,
      `${name} is missing v1.2 S01 P2 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s01p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s01p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S01 P2 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s01p2_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/apps/",
    "OpenAIDatabase/scripts/",
    "OpenAIDatabase/tests/",
    "OpenAIDatabase/config/",
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/public_raw",
    "OpenAIDatabase/private_exports/",
  ];
  const forbiddenOpenChanges = changed.filter((file) => {
    if (file === "OpenAIDatabase/apps/memory-atlas/package.json") return false;
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs") return false;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s01p2_open_diff_scope",
    "Open diff is limited to S01 P2 double-plane files, validator and governance records",
    "Open diff contains files outside S01 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s01p2_no_runtime_or_raw_open_changes",
    "S01 P2 open diff does not move runtime dirs, touch raw archives, or edit runtime code",
    "S01 P2 open diff includes runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validateAuditArtifact();
  validateHumanPlane();
  validateMachinePlane();
  validateRuntimeAndOwnerBoundary();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s01_p2",
    task_id: taskId,
    acceptance_id: acceptanceId,
    checks,
  }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_2_s01_p2",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-6000),
      stderr: error.stderr?.slice(-6000),
    },
    checks,
  }, null, 2));
  process.exit(1);
}
