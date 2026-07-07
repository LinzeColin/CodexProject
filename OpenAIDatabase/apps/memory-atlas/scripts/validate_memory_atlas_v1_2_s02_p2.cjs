#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S02P2";
const acceptanceId = "ACC-MA-V12-S02P2";
const status = "phase_s02_p2_source_registry_completed_pending_s02_p3";
const validatorName = "validate:v1.2-s02-p2";
const scriptName = "validate_memory_atlas_v1_2_s02_p2.cjs";
const registryPath = "机器治理/同步与备份/sync_source_registry.json";
const modelPath = "机器治理/数据契约/source_data_model.v1_2_s02_p1.json";
const artifactPath = "docs/reviews/memory_atlas_v1_2_s02_p2_source_registry.md";
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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${artifactPath}`,
  `OpenAIDatabase/${registryPath}`,
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
    "s02p2_package_script",
    "package.json exposes the v1.2 S02 P2 validator",
    "package.json is missing the v1.2 S02 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s02p2_previous_phase_deferred_scope",
      "S02 P1 execution is deferred only because open diff is limited to S02 P2 files and later-state validator compatibility",
      "S02 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s02p2_previous_phase_deferred_until_clean_tree",
      "S02 P1 validator will run on a clean tree after S02 P2 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s02_p1.cjs"], {
    cwd: appRoot,
    timeout: 180000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S02P1",
    "s02p2_previous_s02p1",
    "S02 P1 validator returns PASS before accepting S02 P2",
    "S02 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSourceRegistry() {
  validateTextFile(registryPath);
  const registry = JSON.parse(readRepoFile(registryPath));
  const sourceModel = JSON.parse(readRepoFile(modelPath));
  const requiredFields = sourceModel.required_fields || [];
  const credentialForbidden = sourceModel.credential_boundary?.forbidden_content || [];

  assertCondition(
    registry.registry_id === "memory_atlas_sync_source_registry_v1_2_s02_p2" &&
      registry.task_id === taskId &&
      registry.acceptance_id === acceptanceId &&
      registry.status === status &&
      registry.model_ref === modelPath,
    "s02p2_registry_identity",
    "Source registry records S02 P2 identity, status and S02 P1 model reference",
    "Source registry identity is incomplete",
    {
      registry_id: registry.registry_id,
      task_id: registry.task_id,
      acceptance_id: registry.acceptance_id,
      status: registry.status,
      model_ref: registry.model_ref,
    },
  );

  assertCondition(
    Array.isArray(registry.sources) && registry.sources.length >= 3,
    "s02p2_sources_array",
    "Source registry contains at least ChatGPT, Codex and future agent template sources",
    "Source registry is missing sources",
    { sources: registry.sources },
  );

  const byId = Object.fromEntries(registry.sources.map((source) => [source.source_id, source]));
  const chatgpt = byId.chatgpt;
  const codex = byId.codex;
  const future = byId.future_agent_template;

  assertCondition(
    chatgpt && codex && future,
    "s02p2_required_source_ids",
    "Source registry includes chatgpt, codex and future_agent_template",
    "Source registry is missing one of chatgpt/codex/future_agent_template",
    { source_ids: registry.sources.map((source) => source.source_id) },
  );

  assertCondition(
    registry.sources.some((source) => source.source_type === "other_agent") &&
      registry.sources.some((source) => source.source_type === "chatgpt") &&
      registry.sources.some((source) => source.source_type === "codex"),
    "s02p2_not_hardcoded_two_sources",
    "Source registry is not only ChatGPT/Codex hardcoded and supports other_agent",
    "Source registry lacks future other_agent source type",
    { source_types: registry.sources.map((source) => source.source_type) },
  );

  registry.sources.forEach((source) => {
    assertCondition(
      requiredFields.every((field) => Object.hasOwn(source, field)),
      `s02p2_required_fields_${source.source_id}`,
      `${source.source_id} includes all S02 P1 required fields`,
      `${source.source_id} is missing S02 P1 required fields`,
      { source, requiredFields },
    );
    assertCondition(
      source.public_backup_mode === "plaintext_public",
      `s02p2_public_backup_mode_${source.source_id}`,
      `${source.source_id} records plaintext public backup mode`,
      `${source.source_id} is missing plaintext public backup mode`,
      { source_id: source.source_id, public_backup_mode: source.public_backup_mode },
    );
    assertCondition(
      source.transcript_boundary?.rule === "transcript_is_not_credential" &&
        source.credential_boundary?.rule === "credentials_not_transcript" &&
        credentialForbidden.every((item) => source.credential_boundary?.forbidden_content?.includes(item)),
      `s02p2_transcript_credential_boundary_${source.source_id}`,
      `${source.source_id} separates transcript and credential data`,
      `${source.source_id} is missing transcript/credential boundary`,
      { source_id: source.source_id, transcript_boundary: source.transcript_boundary, credential_boundary: source.credential_boundary },
    );
  });

  assertCondition(
    chatgpt.connector_type === "browser_readonly_plus_export_fallback" &&
      chatgpt.connector_capability?.includes("browser_readonly") &&
      chatgpt.connector_capability?.includes("official_export_fallback") &&
      chatgpt.allowed_actions?.includes("read_conversation") &&
      chatgpt.forbidden_actions?.includes("capture_cookie") &&
      chatgpt.forbidden_actions?.includes("send_message_without_human_trigger"),
    "s02p2_chatgpt_connector",
    "ChatGPT source includes browser readonly connector and official export fallback with safety boundaries",
    "ChatGPT source is missing connector capability or safety boundaries",
    chatgpt,
  );

  assertCondition(
    codex.connector_type === "local_session_sync" &&
      codex.connector_capability?.includes("local_session_sync") &&
      codex.allowed_actions?.includes("read_session_transcripts") &&
      codex.forbidden_actions?.includes("capture_tokens") &&
      codex.forbidden_actions?.includes("modify_raw_logs"),
    "s02p2_codex_connector",
    "Codex source includes local session sync with token/raw modification boundaries",
    "Codex source is missing local sync capability or safety boundaries",
    codex,
  );

  assertCondition(
    future.source_type === "other_agent" &&
      future.connector_type === "future_agent_adapter" &&
      future.connector_capability?.includes("local_file") &&
      future.connector_capability?.includes("api") &&
      future.raw_root === "data/public_raw/agents/{agent_id}" &&
      future.allowed_actions?.includes("register_source") &&
      future.forbidden_actions?.includes("capture_credentials"),
    "s02p2_future_agent_template",
    "Future agent template is present with adapter capabilities and credential boundary",
    "Future agent template is incomplete",
    future,
  );

  assertCondition(
    registry.phase_boundary?.does_not_create_human_sync_page === true &&
      registry.phase_boundary?.does_not_touch_raw_archive === true &&
      registry.phase_boundary?.does_not_implement_connector === true &&
      registry.phase_boundary?.next_phase === "S02 P3 human sync explanation",
    "s02p2_phase_boundary",
    "Source registry records S02 P2 boundaries and pending S02 P3",
    "Source registry phase boundary is incomplete",
    { phase_boundary: registry.phase_boundary },
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

  const s02p2QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P2：source registry 已建立",
      "S02 P1 数据源模型已完成",
      "ChatGPT browser connector",
      "official export fallback",
      "Codex local sync",
      "future_agent_template",
      "下一步只允许进入 S02 P3",
      "No GitHub main upload in this phase",
  ]);
  const s02p3QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P3：人类同步说明已完成",
      "S02 P1 数据源模型已完成",
      "S02 P2 已把 ChatGPT、Codex",
      "future_agent_template",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步只允许进入 S02 Review",
      "No GitHub main upload in this phase",
  ]);
  const s02ReviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 Review：S02 整体复审已通过",
      "S02 P1 数据源模型已完成",
      "S02 P2 已把 ChatGPT、Codex",
      "future_agent_template",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步只允许进入 S03 P1",
      "No GitHub main upload in this review",
  ]);
  assertCondition(
    s02p2QuickEntry || s02p3QuickEntry || s02ReviewQuickEntry,
    "s02p2_human_quick_entry",
    "Human quick entry records S02 P2 registry completion or later S02 P3/S02 Review state",
    "Human quick entry is missing S02 P2, S02 P3 or S02 Review state boundaries",
  );

  const s02p2Overview = hasAll(overview, [
      "S02 P1 已完成",
      "S02 P2 已完成",
      "sync_source_registry.json",
      "chatgpt",
      "codex",
      "future_agent_template",
      "plaintext_public",
      "transcript/credential",
      "下一步是 S02 P3",
  ]);
  const s02p3Overview = hasAll(overview, [
      "S02 P1 已完成",
      "S02 P2 已完成",
      "S02 P3 已完成",
      "sync_source_registry.json",
      "future_agent_template",
      "transcript/credential",
      "下一步是 S02 Review",
  ]);
  const s02ReviewOverview = hasAll(overview, [
      "S02 Review 已通过",
      "S02 P1 已完成",
      "S02 P2 已完成",
      "S02 P3 已完成",
      "sync_source_registry.json",
      "future_agent_template",
      "transcript/credential",
      "下一步是 S03 P1",
  ]);
  assertCondition(
    s02p2Overview || s02p3Overview || s02ReviewOverview,
    "s02p2_human_overview",
    "Human overview records S02 P2 registry sources or later S02 P3/S02 Review state",
    "Human overview is missing S02 P2, S02 P3 or S02 Review registry details",
  );

  const s02p2MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P2",
      "source registry 已建立",
      "下一步是 S02 P3",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p3MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P3",
      "source registry 已建立",
      "人类同步说明已完成",
      "下一步是 S02 Review",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02ReviewMachineReadme = hasAll(machineReadme, [
      "当前为 S02 Review",
      "source registry 已建立",
      "人类同步说明已完成",
      "S02 整体复审已通过",
      "下一步是 S03 P1",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  assertCondition(
    s02p2MachineReadme || s02p3MachineReadme || s02ReviewMachineReadme,
    "s02p2_machine_readme",
    "Machine README records S02 P2 state or later S02 P3/S02 Review state",
    "Machine README is missing S02 P2, S02 P3 or S02 Review state",
  );

  const s02p2SyncReadme = hasAll(syncReadme, [
      "当前 S02 P2",
      "sync_source_registry.json",
      "ChatGPT browser connector",
      "official export fallback",
      "Codex local sync",
      "future_agent_template",
      "S02 P3",
  ]);
  const s02p3SyncReadme = hasAll(syncReadme, [
      "当前 S02 P3",
      "sync_source_registry.json",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步是 S02 Review",
  ]);
  const s02ReviewSyncReadme = hasAll(syncReadme, [
      "当前 S02 Review",
      "sync_source_registry.json",
      "ChatGPT、Codex、后续其他 agent 数据备份进 GitHub",
      "下一步是 S03 P1",
  ]);
  assertCondition(
    s02p2SyncReadme || s02p3SyncReadme || s02ReviewSyncReadme,
    "s02p2_sync_readme",
    "Sync README points to the S02 P2 source registry or later S02 P3/S02 Review state",
    "Sync README is missing S02 P2, S02 P3 or S02 Review registry reference",
  );

  const s02p2RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 P2",
      taskId,
      acceptanceId,
      validatorName,
      registryPath,
      "下一步是 S02 P3",
      "No GitHub main upload in this phase",
      "不创建人类同步说明页",
  ]);
  const s02p3RunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 P3",
      taskId,
      acceptanceId,
      validatorName,
      "MA-V12-S02P3",
      "validate:v1.2-s02-p3",
      "人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md",
      "下一步是 S02 Review",
      "No GitHub main upload in this phase",
  ]);
  const s02ReviewRunGateReadme = hasAll(runGateReadme, [
      "当前阶段是 S02 Review",
      taskId,
      acceptanceId,
      validatorName,
      "MA-V12-S02P3",
      "validate:v1.2-s02-p3",
      "docs/reviews/memory_atlas_v1_2_s02_review.md",
      "下一步是 S03 P1",
      "No GitHub main upload in this review",
  ]);
  assertCondition(
    s02p2RunGateReadme || s02p3RunGateReadme || s02ReviewRunGateReadme,
    "s02p2_run_gate_readme",
    "Run gate README records S02 P2 validator, registry and later S02 P3/S02 Review gate",
    "Run gate README is missing S02 P2, S02 P3 or S02 Review status",
  );
}

function validateArtifact() {
  validateTextFile(artifactPath);
  const source = readRepoFile(artifactPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S02 P2 Source Registry",
      taskId,
      acceptanceId,
      status,
      validatorName,
      registryPath,
      "sync_source_registry.json",
      "ChatGPT browser connector",
      "official export fallback",
      "Codex local sync",
      "future_agent_template",
      "other_agent",
      "plaintext_public",
      "transcript/credential",
      "No human sync page in this phase",
      "No connector implementation in this phase",
      "No GitHub main upload in this phase",
      "No raw archive change",
      "pending S02 P3",
    ]),
    "s02p2_artifact",
    "S02 P2 artifact records registry sources, boundaries and next gate",
    "S02 P2 artifact is incomplete",
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
        "memory_atlas_v1_2_s02_p2_source_registry.md",
        "sync_source_registry.json",
        "S02 P2",
        "pending S02 P3",
        "No GitHub main upload in this phase",
      ]),
      `s02p2_records_${name}`,
      `${name} records S02 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S02 P2 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s02p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s02p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S02 P2 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s02p2_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenExact = [
    "OpenAIDatabase/人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md",
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
  const forbiddenOpenChanges = changed.filter((file) => {
    if (file === "OpenAIDatabase/apps/memory-atlas/package.json") return false;
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs") return false;
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs") return false;
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs") return false;
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs") return false;
    if (file === `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`) return false;
    if (forbiddenExact.includes(file)) return true;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s02p2_open_diff_scope",
    "Open diff is limited to S02 P2 source registry, validator, state docs and governance records",
    "Open diff contains files outside S02 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s02p2_no_human_sync_runtime_or_raw_open_changes",
    "S02 P2 open diff does not create the S02 P3 human sync page, runtime changes or raw changes",
    "S02 P2 open diff includes human-sync/runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateSourceRegistry();
  validateHumanAndMachineState();
  validateArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s02_p2",
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
    validator: "validate_memory_atlas_v1_2_s02_p2",
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
