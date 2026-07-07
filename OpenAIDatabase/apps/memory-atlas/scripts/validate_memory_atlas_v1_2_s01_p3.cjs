#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S01P3";
const acceptanceId = "ACC-MA-V12-S01P3";
const status = "phase_s01_p3_requirements_freeze_completed_pending_s01_review";
const validatorName = "validate:v1.2-s01-p3";
const scriptName = "validate_memory_atlas_v1_2_s01_p3.cjs";
const auditPath = "docs/reviews/memory_atlas_v1_2_s01_p3_requirements_freeze.md";
const freezePath = "机器治理/运行门禁/v1.2需求冻结清单.json";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/README.md",
  "OpenAIDatabase/AGENTS.md",
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${auditPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/运行门禁/README.md",
  `OpenAIDatabase/${freezePath}`,
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

function validatePackageScript() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s01p3_package_script",
    "package.json exposes the v1.2 S01 P3 validator",
    "package.json is missing the v1.2 S01 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateFreezeConfig() {
  validateTextFile(freezePath);
  const freeze = JSON.parse(readRepoFile(freezePath));
  const raw = freeze.raw_public_authorization || {};
  const credentials = freeze.credentials_exclusion || [];
  const sourceRegistry = freeze.source_registry_extension || {};

  assertCondition(
    freeze.task_name === "v1.2 四线14Stage升级" &&
      freeze.stage_count === 14 &&
      freeze.single_integrated_taskpack === true &&
      Array.isArray(freeze.four_lines) &&
      freeze.four_lines.length === 4,
    "s01p3_freeze_core_identity",
    "Requirements freeze records task name, 14-stage count, integrated taskpack and four-line scope",
    "Requirements freeze core identity is incomplete",
    { task_name: freeze.task_name, stage_count: freeze.stage_count, four_lines: freeze.four_lines },
  );

  assertCondition(
    hasAll(freeze.four_lines.join("\n"), [
      "Anthropic化行为智能",
      "信息ROI_全中文_多维可视化",
      "ChatGPT_Codex_后续其他agent自动同步备份进GitHub",
      "UIUX多模态交互_参数公式模型治理_维护简化",
    ]),
    "s01p3_four_lines_frozen",
    "Four v1.2 lines are frozen in machine-readable config",
    "Four-line v1.2 scope is missing required fragments",
    { four_lines: freeze.four_lines },
  );

  assertCondition(
    raw.chatgpt === true &&
      raw.codex === true &&
      raw.future_other_agents === true &&
      raw.plaintext_public_github_allowed === true &&
      raw.raw_readonly === true &&
      raw.append_only === true &&
      raw.no_overwrite === true &&
      raw.no_delete_or_modify_existing_raw === true,
    "s01p3_raw_public_authorization",
    "Raw public authorization is frozen for ChatGPT, Codex and future agents with readonly append-only constraints",
    "Raw public authorization is incomplete",
    raw,
  );

  assertCondition(
    [
      "cookies",
      "session_tokens",
      "passwords",
      "api_keys",
      "private_keys",
      "oauth_tokens",
      "browser_credential_store",
    ].every((item) => credentials.includes(item)),
    "s01p3_credentials_exclusion",
    "Credential exclusion list blocks account-control secrets from GitHub",
    "Credential exclusion list is incomplete",
    { credentials },
  );

  assertCondition(
    sourceRegistry.supports_chatgpt === true &&
      sourceRegistry.supports_codex === true &&
      sourceRegistry.supports_future_other_agents === true &&
      [
        "source_id",
        "source_type",
        "agent_name",
        "connector_type",
        "raw_root",
        "public_backup_mode",
        "transcript_schema",
        "credential_boundary",
        "sync_frequency",
        "derived_outputs",
      ].every((field) => sourceRegistry.required_fields?.includes(field)),
    "s01p3_future_agent_source_registry",
    "Future other-agent data source expansion rules are frozen through source registry fields",
    "Future other-agent source registry extension is incomplete",
    sourceRegistry,
  );

  assertCondition(
    freeze.stage_execution === "one_phase_per_run_stage_review_after_all_phases_final_upload_after_overall_review" &&
      freeze.github_main_upload === "after_overall_review_and_fix_only" &&
      freeze.app_entry_reinstall === "after_overall_review_and_github_main_sync_only",
    "s01p3_execution_freeze",
    "Execution freeze preserves one-phase runs, stage review after all phases, and final-only upload/app reinstall",
    "Stage execution freeze is incomplete",
    {
      stage_execution: freeze.stage_execution,
      github_main_upload: freeze.github_main_upload,
      app_entry_reinstall: freeze.app_entry_reinstall,
    },
  );
}

function validateHumanAndReadmeBridge() {
  ["README.md", "AGENTS.md", "人类可读/00_快速入口.md", "人类可读/01_v1.2四线14Stage升级总览.md"].forEach(validateTextFile);
  const readme = readRepoFile("README.md");
  const agents = readRepoFile("AGENTS.md");
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");

  assertCondition(
    hasAll(readme, [
      "v1.2 S01 P3 Requirements Freeze Bridge",
      "旧的 raw/private 默认不入 GitHub 边界被 v1.2 替换",
      "用户授权后，ChatGPT、Codex、后续其他 agent 的 raw data / transcript 可以明文公开进 GitHub",
      "raw 只读、只追加、不覆盖、不增删改",
      "凭证不是 transcript",
      "cookies",
      "每次 run 最多只完成一个 phase",
      "整体复审并修复后才上传 GitHub main",
    ]),
    "s01p3_readme_bridge",
    "README explains the v1.2 boundary replacement without dumping the taskpack",
    "README is missing v1.2 S01 P3 boundary bridge",
  );

  assertCondition(
    hasAll(agents, [
      "v1.2 S01 P3 Bridge",
      "不要把 taskpack 大段写入 AGENTS.md",
      "用户授权后 raw/transcript 可公开进入 GitHub",
      "raw 只读、只追加、不覆盖、不增删改",
      "cookies、session tokens、passwords、API keys、private keys、OAuth tokens",
      "每次 run 最多只完成一个 phase",
    ]),
    "s01p3_agents_bridge",
    "AGENTS.md contains a compact v1.2 bridge and credential/raw guardrails",
    "AGENTS.md is missing compact v1.2 S01 P3 bridge",
  );

  const p3QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S01 P3：需求冻结已写入",
      "旧隐私边界已被 v1.2 替换",
      "用户授权后，ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub",
      "凭证不是 transcript",
      "下一步只允许进入 S01 整体复审",
      "No GitHub main upload in this phase",
      "不进入 S02",
  ]);
  const reviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S01 Review：S01 整体复审已通过",
      "旧隐私边界已被 v1.2 替换",
      "用户授权后，ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P1",
      "No GitHub main upload in this review",
  ]);
  const s02p1QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P1：数据源模型已定义",
      "S01 Review 已通过",
      "旧隐私边界已被 v1.2 替换",
      "用户授权后，ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P2",
      "No GitHub main upload in this phase",
  ]);
  const s02p2QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P2：source registry 已建立",
      "S01 Review 已通过",
      "旧隐私边界已被 v1.2 替换",
      "用户授权后，ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P3",
      "No GitHub main upload in this phase",
  ]);
  assertCondition(
    p3QuickEntry || reviewQuickEntry || s02p1QuickEntry || s02p2QuickEntry,
    "s01p3_human_quick_entry",
    "Human quick entry explains S01 P3 completion, S01 review pass state, S02 P1 state, or S02 P2 state with raw authorization and next gate",
    "Human quick entry is missing S01 P3 freeze, S01 review, S02 P1 or S02 P2 status boundaries",
  );

  const p3Overview = hasAll(overview, [
      "S01 P3 已完成",
      "需求冻结配置",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "凭证排除",
      "S01 整体复审尚未执行",
      "整体完成后才上传 GitHub main",
  ]);
  const reviewOverview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P3",
      "需求冻结清单",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "凭证排除",
      "下一步是 S02 P1",
      "整体完成后才上传 GitHub main",
  ]);
  const s02p1Overview = hasAll(overview, [
      "S01 整体复审已通过",
      "S02 P1 已完成",
      "数据源模型",
      "需求冻结清单",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "凭证排除",
      "下一步是 S02 P2",
      "整体完成后才上传 GitHub main",
  ]);
  const s02p2Overview = hasAll(overview, [
      "S01 整体复审已通过",
      "S02 P1 已完成",
      "S02 P2 已完成",
      "需求冻结清单",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "凭证排除",
      "下一步是 S02 P3",
      "整体完成后才上传 GitHub main",
  ]);
  assertCondition(
    p3Overview || reviewOverview || s02p1Overview || s02p2Overview,
    "s01p3_human_overview",
    "Human overview records S01 P3 completion, S01 review pass state, S02 P1 state, or S02 P2 state",
    "Human overview is missing S01 P3 completion, S01 review, S02 P1 or S02 P2 boundary",
  );
}

function validateMachineBridge() {
  ["机器治理/README.md", "机器治理/运行门禁/README.md"].forEach(validateTextFile);
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  const p3MachineReadme = hasAll(machineReadme, [
      "当前为 S01 P3",
      "v1.2需求冻结清单",
      "四线范围",
      "raw 公开授权",
      "凭证排除",
      "后续其他 agent 数据源扩展规则",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const reviewMachineReadme = hasAll(machineReadme, [
      "当前为 S01 Review",
      "S01 整体复审已通过",
      "v1.2需求冻结清单",
      "四线范围",
      "raw 公开授权",
      "凭证排除",
      "后续其他 agent 数据源扩展规则",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p1MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P1",
      "数据源模型已定义",
      "v1.2需求冻结清单",
      "四线范围",
      "raw 公开授权",
      "凭证排除",
      "后续其他 agent 数据源扩展规则",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p2MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P2",
      "source registry 已建立",
      "v1.2需求冻结清单",
      "四线范围",
      "raw 公开授权",
      "凭证排除",
      "后续其他 agent 数据源扩展规则",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  assertCondition(
    p3MachineReadme || reviewMachineReadme || s02p1MachineReadme || s02p2MachineReadme,
    "s01p3_machine_readme",
    "Machine governance README records S01 P3 freeze contents, S01 review pass state, S02 P1 state, or S02 P2 state and non-replacement boundary",
    "Machine governance README is missing S01 P3 freeze, S01 review, S02 P1 or S02 P2 bridge",
  );

  const p3RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S01 P3",
      "v1.2需求冻结清单",
      "MA-V12-S01P3",
      "ACC-MA-V12-S01P3",
      "下一步是 S01 整体复审",
      "No GitHub main upload in this phase",
      "不进入 S02",
  ]);
  const reviewRunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S01 Review",
      "v1.2需求冻结清单",
      "MA-V12-S01-REVIEW",
      "ACC-MA-V12-S01-REVIEW",
      "下一步是 S02 P1",
      "No GitHub main upload in this review",
  ]);
  const s02p1RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 P1",
      "v1.2需求冻结清单",
      "MA-V12-S02P1",
      "ACC-MA-V12-S02P1",
      "下一步是 S02 P2",
      "No GitHub main upload in this phase",
  ]);
  const s02p2RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 P2",
      "v1.2需求冻结清单",
      "MA-V12-S02P2",
      "ACC-MA-V12-S02P2",
      "下一步是 S02 P3",
      "No GitHub main upload in this phase",
  ]);
  assertCondition(
    p3RunGateReadme || reviewRunGateReadme || s02p1RunGateReadme || s02p2RunGateReadme,
    "s01p3_machine_run_gate_readme",
    "Run gate README records freeze config status and next review, S02 P1, S02 P2, or S02 P3 boundary",
    "Run gate README is missing S01 P3, S01 review, S02 P1 or S02 P2 gate status",
  );
}

function validateAuditArtifact() {
  validateTextFile(auditPath);
  const source = readRepoFile(auditPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S01 P3 Requirements Freeze",
      taskId,
      acceptanceId,
      status,
      validatorName,
      freezePath,
      "S01 P1 completed",
      "S01 P2 completed",
      "S01 review not executed",
      "No S02",
      "No GitHub main upload in this phase",
      "No raw archive change",
      "No AGENTS taskpack dump",
    ]),
    "s01p3_audit_artifact",
    "S01 P3 audit records freeze, prior-phase continuity, review deferral and no-upload/raw boundaries",
    "S01 P3 audit artifact is incomplete",
  );
}

function validateRuntimeAndOwnerBoundary() {
  ["功能清单.md", "开发记录.md", "模型参数文件.md"].forEach((relativePath) => {
    assertCondition(
      fs.existsSync(path.join(repoRoot, relativePath)),
      `s01p3_owner_file_${relativePath}`,
      `${relativePath} is preserved as a root owner door`,
      `${relativePath} is missing`,
    );
  });
  ["apps", "apps/memory-atlas", "scripts", "tests", "config", "data", "docs/governance"].forEach((relativePath) => {
    assertCondition(
      fs.statSync(path.join(repoRoot, relativePath)).isDirectory(),
      `s01p3_runtime_dir_${relativePath}`,
      `${relativePath} directory still exists and was not moved`,
      `${relativePath} directory is missing`,
    );
  });
}

function validateRecords() {
  recordFiles.forEach(validateTextFile);
  recordFiles.forEach((name) => {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "memory_atlas_v1_2_s01_p3_requirements_freeze.md",
        "S01 P3",
        "v1.2需求冻结清单.json",
        "No GitHub main upload in this phase",
      ]),
      `s01p3_records_${name}`,
      `${name} records v1.2 S01 P3 status, validator, evidence and no-upload boundary`,
      `${name} is missing v1.2 S01 P3 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s01p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s01p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S01 P3 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s01p3_no_remote_development_branch",
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
    if (file === `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`) return false;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s01p3_open_diff_scope",
    "Open diff is limited to S01 P3 freeze, bridge, validator and governance records",
    "Open diff contains files outside S01 P3 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s01p3_no_runtime_or_raw_open_changes",
    "S01 P3 open diff does not move runtime dirs, touch raw archives, or edit runtime code",
    "S01 P3 open diff includes runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validateFreezeConfig();
  validateHumanAndReadmeBridge();
  validateMachineBridge();
  validateAuditArtifact();
  validateRuntimeAndOwnerBoundary();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s01_p3",
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
    validator: "validate_memory_atlas_v1_2_s01_p3",
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
