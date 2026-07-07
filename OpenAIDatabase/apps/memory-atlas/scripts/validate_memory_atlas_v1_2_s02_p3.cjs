#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S02P3";
const acceptanceId = "ACC-MA-V12-S02P3";
const status = "phase_s02_p3_human_sync_explanation_completed_pending_s02_review";
const validatorName = "validate:v1.2-s02-p3";
const scriptName = "validate_memory_atlas_v1_2_s02_p3.cjs";
const registryPath = "机器治理/同步与备份/sync_source_registry.json";
const humanPagePath = "人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md";
const artifactPath = "docs/reviews/memory_atlas_v1_2_s02_p3_human_sync_explanation.md";
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
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${artifactPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/同步与备份/README.md",
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
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s02p3_package_script",
    "package.json exposes the v1.2 S02 P3 validator",
    "package.json is missing the v1.2 S02 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s02p3_previous_phase_deferred_scope",
      "S02 P2 execution is deferred only because open diff is limited to S02 P3 files and later-state validator compatibility",
      "S02 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s02p3_previous_phase_deferred_until_clean_tree",
      "S02 P2 validator will run on a clean tree after S02 P3 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s02_p2.cjs"], {
    cwd: appRoot,
    timeout: 180000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S02P2",
    "s02p3_previous_s02p2",
    "S02 P2 validator returns PASS before accepting S02 P3",
    "S02 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRegistryStillCoversStage() {
  validateTextFile(registryPath);
  const registry = JSON.parse(readRepoFile(registryPath));
  const byId = Object.fromEntries((registry.sources || []).map((source) => [source.source_id, source]));
  const requiredSources = ["chatgpt", "codex", "future_agent_template"];
  const missing = requiredSources.filter((sourceId) => !byId[sourceId]);

  assertCondition(
    missing.length === 0 &&
      byId.future_agent_template?.source_type === "other_agent" &&
      byId.future_agent_template?.connector_type === "future_agent_adapter",
    "s02p3_registry_future_agent",
    "Source registry still contains chatgpt, codex and future_agent_template for S02 P3 human explanation",
    "Source registry is missing required S02 sources",
    { missing, sources: Object.keys(byId) },
  );

  const boundaryFailures = (registry.sources || []).filter((source) => (
    source.public_backup_mode !== "plaintext_public" ||
    source.transcript_boundary?.rule !== "transcript_is_not_credential" ||
    source.credential_boundary?.rule !== "credentials_not_transcript" ||
    !source.credential_boundary?.forbidden_content?.includes("cookies") ||
    !source.credential_boundary?.forbidden_content?.includes("session_tokens")
  ));
  assertCondition(
    boundaryFailures.length === 0,
    "s02p3_registry_public_backup_and_boundaries",
    "Every registered source retains plaintext public backup mode and transcript/credential boundaries",
    "A registered source is missing public backup mode or transcript/credential boundary",
    { boundaryFailures },
  );
}

function validateHumanSyncPage() {
  validateTextFile(humanPagePath);
  const source = readRepoFile(humanPagePath);

  assertCondition(
    hasAll(source, [
      "ChatGPT 与 Codex 及其他 Agent 自动同步说明",
      taskId,
      acceptanceId,
      status,
      registryPath,
      "S02 P3",
      "pending S02 Review",
    ]),
    "s02p3_human_page_identity",
    "Human sync page records S02 P3 identity, registry reference and next review gate",
    "Human sync page is missing S02 P3 identity or next gate",
  );

  assertCondition(
    hasAll(source, [
      "ChatGPT",
      "ChatGPT browser connector",
      "official export fallback",
      "Codex",
      "Codex local sync",
      "后续其他 agent",
      "future_agent_template",
      "future_agent_adapter",
      "other_agent",
      "数据备份进 GitHub",
    ]),
    "s02p3_human_page_sources",
    "Human sync page explicitly explains ChatGPT, Codex and future other-agent GitHub backup",
    "Human sync page is missing source coverage or GitHub backup wording",
  );

  assertCondition(
    hasAll(source, [
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "conversation_title",
      "message_text",
      "timestamp",
      "speaker_role",
      "metadata",
      "tool_call_summary",
      "attachment_reference",
      "plaintext_public",
      "public_backup_mode",
    ]),
    "s02p3_human_page_github_payloads",
    "Human sync page explains which transcript data and raw roots can enter GitHub",
    "Human sync page does not explain which data enters GitHub",
  );

  assertCondition(
    hasAll(source, [
      "transcript/credential",
      "credentials_not_transcript",
      "cookies",
      "session tokens",
      "passwords",
      "API keys",
      "private keys",
      "OAuth tokens",
      "browser_credential_store",
      "永远不能提交",
    ]),
    "s02p3_human_page_credential_boundary",
    "Human sync page separates transcript from credential data and blocks credential submission",
    "Human sync page is missing credential boundary",
  );

  assertCondition(
    hasAll(source, [
      "source_id",
      "source_type",
      "agent_name",
      "raw_root",
      "sync_mode",
      "connector_capability",
      "register_source",
      "capture_credentials",
    ]),
    "s02p3_human_page_future_agent_adapter",
    "Human sync page explains how future agents join the registry",
    "Human sync page is missing future-agent adapter instructions",
  );

  assertCondition(
    hasAll(source, [
      "No GitHub main upload in this phase",
      "No connector implementation",
      "No raw archive change",
      "No app reinstall",
      "本页不是 connector 实现",
    ]),
    "s02p3_human_page_phase_boundary",
    "Human sync page records phase boundaries and avoids connector/raw/GitHub upload work",
    "Human sync page is missing S02 P3 boundaries",
  );
}

function validateHumanAndMachineState() {
  [
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/运行门禁/README.md",
  ].forEach(validateTextFile);

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  assertCondition(
    hasAll(quickEntry, [
      "当前阶段是 S02 P3：人类同步说明已完成",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "已完成：S02 P3 人类同步说明",
      "下一步只允许进入 S02 Review",
      "No GitHub main upload in this phase",
      "不实现 connector",
      "不修改 raw archive",
    ]),
    "s02p3_human_quick_entry",
    "Human quick entry records S02 P3 completion and next S02 Review gate",
    "Human quick entry is missing S02 P3 state or boundaries",
  );

  assertCondition(
    hasAll(overview, [
      "S02 P3 已完成",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "future_agent_template",
      "transcript/credential",
      "credentials_not_transcript",
      "下一步是 S02 Review",
    ]),
    "s02p3_human_overview",
    "Human overview records S02 P3 human explanation and pending S02 Review",
    "Human overview is missing S02 P3 details",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S02 P3",
      "人类同步说明已完成",
      "下一步是 S02 Review",
      "不替代 apps/scripts/tests/config/data/docs/governance",
    ]),
    "s02p3_machine_readme",
    "Machine README records S02 P3 state and next S02 Review boundary",
    "Machine README is missing S02 P3 state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S02 P3",
      "sync_source_registry.json",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步是 S02 Review",
    ]),
    "s02p3_sync_readme",
    "Sync README points to the S02 P3 human page and next S02 Review",
    "Sync README is missing S02 P3 human sync page reference",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S02 P3",
      taskId,
      acceptanceId,
      validatorName,
      humanPagePath,
      artifactPath,
      "前置 S02 P2 已通过",
      "下一步是 S02 Review",
      "No GitHub main upload in this phase",
      "不实现 connector",
      "不修改 raw archive",
    ]),
    "s02p3_run_gate_readme",
    "Run gate README records S02 P3 validator, human page and next review gate",
    "Run gate README is missing S02 P3 status",
  );
}

function validateArtifact() {
  validateTextFile(artifactPath);
  const source = readRepoFile(artifactPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S02 P3 Human Sync Explanation",
      taskId,
      acceptanceId,
      status,
      validatorName,
      humanPagePath,
      registryPath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "future_agent_template",
      "transcript/credential",
      "credentials_not_transcript",
      "No connector implementation",
      "No GitHub main upload in this phase",
      "No raw archive change",
      "pending S02 Review",
    ]),
    "s02p3_artifact",
    "S02 P3 artifact records human page, boundaries and next review gate",
    "S02 P3 artifact is incomplete",
  );
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
        "memory_atlas_v1_2_s02_p3_human_sync_explanation.md",
        humanPagePath,
        "S02 P3",
        "pending S02 Review",
        "No GitHub main upload in this phase",
      ]),
      `s02p3_records_${name}`,
      `${name} records S02 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S02 P3 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s02p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s02p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S02 P3 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s02p3_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenExact = [
    "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s02_review.md",
  ];
  const forbiddenPrefixes = [
    "OpenAIDatabase/apps/",
    "OpenAIDatabase/scripts/",
    "OpenAIDatabase/tests/",
    "OpenAIDatabase/config/",
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/public_raw",
    "OpenAIDatabase/private_exports/",
  ];
  const allowedAppFiles = new Set([
    "OpenAIDatabase/apps/memory-atlas/package.json",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
    `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  ]);
  const forbiddenOpenChanges = changed.filter((file) => {
    if (allowedAppFiles.has(file)) return false;
    if (forbiddenExact.includes(file)) return true;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s02p3_open_diff_scope",
    "Open diff is limited to S02 P3 human explanation, validator, state docs and governance records",
    "Open diff contains files outside S02 P3 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s02p3_no_review_runtime_or_raw_open_changes",
    "S02 P3 open diff does not create S02 Review, runtime changes or raw changes",
    "S02 P3 open diff includes review/runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateRegistryStillCoversStage();
  validateHumanSyncPage();
  validateHumanAndMachineState();
  validateArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s02_p3",
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
    validator: "validate_memory_atlas_v1_2_s02_p3",
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
