#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S02-REVIEW";
const acceptanceId = "ACC-MA-V12-S02-REVIEW";
const status = "stage_s02_review_passed_pending_s03_no_github_main_upload";
const validatorName = "validate:v1.2-s02-review";
const scriptName = "validate_memory_atlas_v1_2_s02_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s02_review.md";
const modelPath = "机器治理/数据契约/source_data_model.v1_2_s02_p1.json";
const registryPath = "机器治理/同步与备份/sync_source_registry.json";
const humanPagePath = "人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md";
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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${reviewPath}`,
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

function currentStateIsS03Review() {
  if (currentStateIsS04P1()) return true;

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
    "s02_review_package_script",
    "package.json exposes the v1.2 S02 review validator",
    "package.json is missing the v1.2 S02 review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s02_review_previous_phase_deferred_scope",
      "S02 P3 execution is deferred only because open diff is limited to S02 Review files and later-state validator compatibility",
      "S02 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s02_review_previous_phase_deferred_until_clean_tree",
      "S02 P3 validator will run on a clean tree after S02 Review commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s02_p3.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S02P3",
    "s02_review_previous_s02p3",
    "S02 P3 validator returns PASS before accepting S02 Review",
    "S02 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateStageArtifacts() {
  [modelPath, registryPath, humanPagePath].forEach(validateTextFile);
  const model = JSON.parse(readRepoFile(modelPath));
  const registry = JSON.parse(readRepoFile(registryPath));
  const humanPage = readRepoFile(humanPagePath);

  assertCondition(
    model.source_type_enum?.includes("chatgpt") &&
      model.source_type_enum?.includes("codex") &&
      model.source_type_enum?.includes("other_agent") &&
      model.required_fields?.includes("source_id") &&
      model.required_fields?.includes("public_backup_mode") &&
      model.required_fields?.includes("connector_capability") &&
      model.transcript_boundary?.rule === "transcript_is_not_credential" &&
      model.credential_boundary?.rule === "credentials_not_transcript",
    "s02_review_p1_source_model",
    "S02 P1 source model supports ChatGPT, Codex, other_agent and transcript/credential boundary",
    "S02 P1 source model is incomplete",
    {
      source_type_enum: model.source_type_enum,
      required_fields: model.required_fields,
      transcript_boundary: model.transcript_boundary,
      credential_boundary: model.credential_boundary,
    },
  );

  const byId = Object.fromEntries((registry.sources || []).map((source) => [source.source_id, source]));
  const requiredSourceIds = ["chatgpt", "codex", "future_agent_template"];
  const missingSources = requiredSourceIds.filter((sourceId) => !byId[sourceId]);
  assertCondition(
    missingSources.length === 0 &&
      registry.sources?.length >= 3 &&
      byId.future_agent_template?.source_type === "other_agent" &&
      byId.future_agent_template?.connector_type === "future_agent_adapter",
    "s02_review_p2_registry_sources",
    "S02 P2 source registry is not hardcoded to ChatGPT/Codex and includes future_agent_template",
    "S02 P2 source registry is missing future-agent coverage",
    { missingSources, sources: registry.sources?.map((source) => source.source_id) },
  );

  const boundaryFailures = (registry.sources || []).filter((source) => (
    source.public_backup_mode !== "plaintext_public" ||
    source.transcript_boundary?.rule !== "transcript_is_not_credential" ||
    source.credential_boundary?.rule !== "credentials_not_transcript" ||
    !source.credential_boundary?.forbidden_content?.includes("cookies") ||
    !source.credential_boundary?.forbidden_content?.includes("session_tokens") ||
    !source.credential_boundary?.forbidden_content?.includes("api_keys")
  ));
  assertCondition(
    boundaryFailures.length === 0,
    "s02_review_registry_boundaries",
    "Every S02 source has plaintext public backup mode and transcript/credential boundary",
    "A S02 source lacks public backup mode or credential boundary",
    { boundaryFailures },
  );

  assertCondition(
    hasAll(humanPage, [
      "ChatGPT 与 Codex 及其他 Agent 自动同步说明",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "future_agent_template",
      "future_agent_adapter",
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "plaintext_public",
      "transcript/credential",
      "credentials_not_transcript",
      "永远不能提交",
      "No connector implementation",
      "No raw archive change",
    ]),
    "s02_review_p3_human_page",
    "S02 P3 human page explains source scope, future-agent access, GitHub payloads and credential exclusions",
    "S02 P3 human page is incomplete",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S02 Review",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S02 P1",
      "S02 P2",
      "S02 P3",
      modelPath,
      registryPath,
      humanPagePath,
      "source registry 不是仅 chatgpt/codex 硬编码",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "transcript/credential",
      "public_backup_mode",
      "future_agent_template",
      "No GitHub main upload in this review",
      "No connector implementation",
      "No raw archive change",
      "pending S03 P1",
    ]),
    "s02_review_artifact",
    "S02 Review artifact records phase coverage, acceptance, stop-condition audit and next S03 gate",
    "S02 Review artifact is incomplete",
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
      "s02_review_human_machine_later_s03p2_state",
      "Current human and machine state has advanced through S02 Review into S03 P2",
    );
    return;
  }

  const s02ReviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 Review：S02 整体复审已通过",
      "已完成：S02 Review",
      "下一步只允许进入 S03 P1",
      "No GitHub main upload in this review",
      "不实现 connector",
      "不修改 raw archive",
  ]);
  const s03p1QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S03 P1",
      "MA-V12-S03P1",
      "ACC-MA-V12-S03P1",
      "phase_s03_p1_public_raw_path_defined_pending_s03_p2",
      "S02 Review 已通过",
      "下一步只允许进入 S03 P2",
  ]);
  assertCondition(
    s02ReviewQuickEntry || s03p1QuickEntry,
    "s02_review_human_quick_entry",
    "Human quick entry records S02 Review pass state or later S03 P1 state",
    "Human quick entry is missing S02 Review or S03 P1 state",
  );

  const s02ReviewOverview = hasAll(overview, [
      "S02 Review 已通过",
      "S02 P1",
      "S02 P2",
      "S02 P3",
      "source registry",
      "future_agent_template",
      "transcript/credential",
      "下一步是 S03 P1",
      "整体完成后才上传 GitHub main",
  ]);
  const s03p1Overview = hasAll(overview, [
      "S02 Review 已通过",
      "S03 P1 已完成",
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "下一步是 S03 P2",
      "整体完成后才上传 GitHub main",
  ]);
  assertCondition(
    s02ReviewOverview || s03p1Overview,
    "s02_review_human_overview",
    "Human overview records S02 Review pass state or later S03 P1 state",
    "Human overview is missing S02 Review or S03 P1 state",
  );

  const s02ReviewMachineReadme = hasAll(machineReadme, [
      "当前为 S02 Review",
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
    s02ReviewMachineReadme || s03p1MachineReadme,
    "s02_review_machine_readme",
    "Machine README records S02 Review pass state or later S03 P1 state",
    "Machine README is missing S02 Review or S03 P1 state",
  );

  const s02ReviewSyncReadme = hasAll(syncReadme, [
      "当前 S02 Review",
      "S02 整体复审已通过",
      "sync_source_registry.json",
      humanPagePath,
      "下一步是 S03 P1",
  ]);
  const s03p1SyncReadme = hasAll(syncReadme, [
      "当前 S03 P1 已完成",
      "S02 整体复审已通过",
      "sync_source_registry.json",
      "raw_public_archive_policy.v1_2_s03_p1.json",
      "下一步是 S03 P2",
  ]);
  assertCondition(
    s02ReviewSyncReadme || s03p1SyncReadme,
    "s02_review_sync_readme",
    "Sync README records S02 Review state or later S03 P1 state",
    "Sync README is missing S02 Review or S03 P1 state",
  );

  const s02ReviewRunGate = hasAll(runGateReadme, [
      "当前阶段是 S02 Review",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S02 P3 已通过",
      "下一步是 S03 P1",
      "No GitHub main upload in this review",
      "不进入 S03",
  ]);
  const s03p1RunGate = hasAll(runGateReadme, [
      "当前阶段是 S03 P1",
      "MA-V12-S03P1",
      "ACC-MA-V12-S03P1",
      "validate:v1.2-s03-p1",
      reviewPath,
      "前置 S02 Review 已通过",
      "下一步是 S03 P2",
      "No GitHub main upload in this phase",
  ]);
  assertCondition(
    s02ReviewRunGate || s03p1RunGate,
    "s02_review_run_gate_readme",
    "Run gate README records S02 Review validator or later S03 P1 gate state",
    "Run gate README is missing S02 Review or S03 P1 state",
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
        "memory_atlas_v1_2_s02_review.md",
        "S02 Review",
        "pending S03 P1",
        "No GitHub main upload in this review",
      ]),
      `s02_review_records_${name}`,
      `${name} records S02 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S02 Review record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s02_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s02_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S02 Review branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s02_review_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
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
    "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
    `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  ]);
  const forbiddenOpenChanges = changed.filter((file) => {
    if (allowedOpenDiffPaths.includes(file)) return false;
    if (allowedAppFiles.has(file)) return false;
    if (file.startsWith("OpenAIDatabase/apps/")) return true;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s02_review_open_diff_scope",
    "Open diff is limited to S02 Review artifact, validator, state docs and governance records",
    "Open diff contains files outside S02 Review allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s02_review_no_runtime_or_raw_open_changes",
    "S02 Review open diff does not enter S03, runtime connector work or raw archive changes",
    "S02 Review open diff includes runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateStageArtifacts();
  validateReviewArtifact();
  validateHumanAndMachineState();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s02_review",
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
    validator: "validate_memory_atlas_v1_2_s02_review",
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
