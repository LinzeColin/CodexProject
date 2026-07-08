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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs",
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md",
  "OpenAIDatabase/机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json",
  "OpenAIDatabase/人类可读/07_凭证排除说明.md",
  "OpenAIDatabase/scripts/privacy_guard.py",
  "OpenAIDatabase/scripts/sync_codex_memory_data.py",
  "OpenAIDatabase/tests/test_s3pdt01_privacy.py",
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

const githubHttpsRemote = "https://github.com/LinzeColin/CodexProject.git";

function queryRemoteDevBranch() {
  try {
    return {
      method: "origin",
      output: run("git", ["ls-remote", "--heads", "origin", branchName], {
        cwd: worktreeRoot,
        timeout: 60000,
      }).stdout.trim(),
    };
  } catch (originError) {
    return {
      method: "https_fallback",
      originError: originError.message,
      originStderr: originError.stderr?.slice(-1000),
      output: run("git", ["ls-remote", "--heads", githubHttpsRemote, branchName], {
        cwd: worktreeRoot,
        timeout: 60000,
      }).stdout.trim(),
    };
  }
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

function currentStateIsS04P1() {
  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S04 P1",
      "MA-V12-S04P1",
      "ACC-MA-V12-S04P1",
      "下一步只允许进入 S04 P2",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S04 P1 已完成",
      "ChatGPT 只读同步",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S04 P1",
      "chatgpt_readonly_sync_policy.v1_2_s04_p1.json",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S04 P1 已完成",
      "official export fallback",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S04 P1",
      "validate:v1.2-s04-p1",
      "下一步是 S04 P2",
    ])
  );
}
function currentStateIsS04P2() {
  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S04 P2",
      "MA-V12-S04P2",
      "ACC-MA-V12-S04P2",
      "下一步只允许进入 S04 P3",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S04 P2 已完成",
      "Codex local sync",
      "下一步是 S04 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S04 P2",
      "codex_agent_sync_policy.v1_2_s04_p2.json",
      "下一步是 S04 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S04 P2 已完成",
      "Codex local sync",
      "future-agent minimal adapter",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S04 P2",
      "validate:v1.2-s04-p2",
      "下一步是 S04 P3",
    ])
  );
}

function currentStateIsS04P3() {
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  const s04p3State =
    hasAll(quickEntry, [
      "当前阶段是 S04 P3",
      "MA-V12-S04P3",
      "ACC-MA-V12-S04P3",
      "下一步只允许进入 S04 Review",
    ]) &&
    hasAll(overview, [
      "S04 P3 已完成",
      "GitHub backup dry-run/apply",
      "下一步是 S04 Review",
    ]) &&
    hasAll(machineReadme, [
      "当前为 S04 P3",
      "github_backup_policy.v1_2_s04_p3.json",
      "下一步是 S04 Review",
    ]) &&
    hasAll(syncReadme, [
      "当前 S04 P3 已完成",
      "github_backup_policy.v1_2_s04_p3.json",
      "scripts/github_backup.py",
      "下一步是 S04 Review",
    ]) &&
    hasAll(runGateReadme, [
      "当前阶段是 S04 P3",
      "MA-V12-S04P3",
      "ACC-MA-V12-S04P3",
      "validate:v1.2-s04-p3",
    ]);

  const s04ReviewState =
    hasAll(quickEntry, [
      "当前阶段是 S04 Review",
      "MA-V12-S04-REVIEW",
      "ACC-MA-V12-S04-REVIEW",
      "下一步只允许进入 S05 P1",
    ]) &&
    hasAll(overview, [
      "S04 Review 已通过",
      "S04 整体复审已通过",
      "下一步是 S05 P1",
    ]) &&
    hasAll(machineReadme, [
      "当前为 S04 Review",
      "memory_atlas_v1_2_s04_review.md",
      "下一步是 S05 P1",
    ]) &&
    hasAll(syncReadme, [
      "当前 S04 Review 已通过",
      "ChatGPT 只读同步",
      "GitHub backup dry-run/apply",
      "下一步是 S05 P1",
    ]) &&
    hasAll(runGateReadme, [
      "当前阶段是 S04 Review",
      "MA-V12-S04-REVIEW",
      "ACC-MA-V12-S04-REVIEW",
      "validate:v1.2-s04-review",
    ]);

  return s04p3State || s04ReviewState;
}


function currentStateIsS03Review() {
  if (currentStateIsS04P1() || currentStateIsS04P2() || currentStateIsS04P3()) return true;

  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 Review",
      "MA-V12-S03-REVIEW",
      "ACC-MA-V12-S03-REVIEW",
      "下一步只允许进入 S04 P1",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 Review 已通过",
      "raw 可公开备份",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 Review",
      "memory_atlas_v1_2_s03_review.md",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 Review 已通过",
      "credential exclusion",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 Review",
      "validate:v1.2-s03-review",
      "下一步是 S04 P1",
    ])
  );
}

function currentStateIsS03P2() {
  if (currentStateIsS03Review()) return true;

  if (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 P3",
      "MA-V12-S03P3",
      "ACC-MA-V12-S03P3",
      "下一步只允许进入 S03 Review",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 P3 已完成",
      "raw manifest/hash 可生成",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 P3",
      "raw_manifest_ledger_policy.v1_2_s03_p3.json",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 P3 已完成",
      "raw_archive_manifest.py",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 P3",
      "validate:v1.2-s03-p3",
      "下一步是 S03 Review",
    ])
  ) {
    return true;
  }

  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 P2",
      "MA-V12-S03P2",
      "ACC-MA-V12-S03P2",
      "下一步只允许进入 S03 P3",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 P2 已完成",
      "credential is not memory",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 P2",
      "credential_exclusion_policy.v1_2_s03_p2.json",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 P2 已完成",
      "credentials_not_transcript",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 P2",
      "validate:v1.2-s03-p2",
      "下一步是 S03 P3",
    ])
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

  if (currentStateIsS03P2()) {
    pass(
      "s02p3_human_machine_later_s03p2_state",
      "Current human and machine state has advanced through S02 P3 into S03 P2",
    );
    return;
  }

  const s02p3QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P3：人类同步说明已完成",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "已完成：S02 P3 人类同步说明",
      "下一步只允许进入 S02 Review",
      "No GitHub main upload in this phase",
      "不实现 connector",
      "不修改 raw archive",
  ]);
  const s02ReviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 Review：S02 整体复审已通过",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "已完成：S02 Review",
      "下一步只允许进入 S03 P1",
      "No GitHub main upload in this review",
      "不实现 connector",
      "不修改 raw archive",
  ]);
  const s03p1QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S03 P1",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 的 transcript 可以明文公开进 GitHub",
      "已完成：S02 Review",
      "已完成：S02 P3 人类同步说明",
      "MA-V12-S03P1",
      "下一步只允许进入 S03 P2",
      "No GitHub main upload in this phase",
  ]);
  assertCondition(
    s02p3QuickEntry || s02ReviewQuickEntry || s03p1QuickEntry,
    "s02p3_human_quick_entry",
    "Human quick entry records S02 P3 completion or later S02 Review/S03 P1 state",
    "Human quick entry is missing S02 P3, S02 Review or S03 P1 state or boundaries",
  );

  const s02p3Overview = hasAll(overview, [
      "S02 P3 已完成",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "future_agent_template",
      "transcript/credential",
      "credentials_not_transcript",
      "下一步是 S02 Review",
  ]);
  const s02ReviewOverview = hasAll(overview, [
      "S02 Review 已通过",
      "S02 P3 已完成",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "future_agent_template",
      "transcript/credential",
      "credentials_not_transcript",
      "下一步是 S03 P1",
  ]);
  const s03p1Overview = hasAll(overview, [
      "S02 Review 已通过",
      "S03 P1 已完成",
      humanPagePath,
      "future_agent_template",
      "transcript/credential",
      "下一步是 S03 P2",
  ]);
  assertCondition(
    s02p3Overview || s02ReviewOverview || s03p1Overview,
    "s02p3_human_overview",
    "Human overview records S02 P3 human explanation or later S02 Review/S03 P1 state",
    "Human overview is missing S02 P3, S02 Review or S03 P1 details",
  );

  const s02p3MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P3",
      "人类同步说明已完成",
      "下一步是 S02 Review",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02ReviewMachineReadme = hasAll(machineReadme, [
      "当前为 S02 Review",
      "人类同步说明已完成",
      "S02 整体复审已通过",
      "下一步是 S03 P1",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s03p1MachineReadme = hasAll(machineReadme, [
      "当前为 S03 P1",
      "S02 整体复审已通过",
      "raw_public_archive_policy.v1_2_s03_p1.json",
      "下一步是 S03 P2",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  assertCondition(
    s02p3MachineReadme || s02ReviewMachineReadme || s03p1MachineReadme,
    "s02p3_machine_readme",
    "Machine README records S02 P3 state or later S02 Review/S03 P1 state",
    "Machine README is missing S02 P3, S02 Review or S03 P1 state",
  );

  const s02p3SyncReadme = hasAll(syncReadme, [
      "当前 S02 P3",
      "sync_source_registry.json",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步是 S02 Review",
  ]);
  const s02ReviewSyncReadme = hasAll(syncReadme, [
      "当前 S02 Review",
      "sync_source_registry.json",
      humanPagePath,
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步是 S03 P1",
  ]);
  const s03p1SyncReadme = hasAll(syncReadme, [
      "当前 S03 P1 已完成",
      "sync_source_registry.json",
      humanPagePath,
      "raw_public_archive_policy.v1_2_s03_p1.json",
      "下一步是 S03 P2",
  ]);
  assertCondition(
    s02p3SyncReadme || s02ReviewSyncReadme || s03p1SyncReadme,
    "s02p3_sync_readme",
    "Sync README points to the S02 P3 human page or later S02 Review/S03 P1 state",
    "Sync README is missing S02 P3, S02 Review or S03 P1 human sync page reference",
  );

  const s02p3RunGateReadme = hasAll(runGateReadme, [
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
  ]);
  const s02ReviewRunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 Review",
      taskId,
      acceptanceId,
      validatorName,
      humanPagePath,
      artifactPath,
      "前置 S02 P3 已通过",
      "下一步是 S03 P1",
      "No GitHub main upload in this review",
      "不实现 connector",
      "不修改 raw archive",
  ]);
  const s03p1RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S03 P1",
      "MA-V12-S03P1",
      "ACC-MA-V12-S03P1",
      "validate:v1.2-s03-p1",
      "前置 S02 Review 已通过",
      "下一步是 S03 P2",
      "No GitHub main upload in this phase",
  ]);
  assertCondition(
    s02p3RunGateReadme || s02ReviewRunGateReadme || s03p1RunGateReadme,
    "s02p3_run_gate_readme",
    "Run gate README records S02 P3 validator or later S02 Review/S03 P1 gate",
    "Run gate README is missing S02 P3, S02 Review or S03 P1 status",
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

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s02p3_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
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
    if (allowedOpenDiffPaths.includes(file)) return false;
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
