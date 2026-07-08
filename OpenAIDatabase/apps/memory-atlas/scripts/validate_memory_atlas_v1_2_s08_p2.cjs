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

const taskId = "MA-V12-S08P2";
const acceptanceId = "ACC-MA-V12-S08P2";
const status = "phase_s08_p2_authorization_boundary_completed_pending_s08_p3";
const validatorName = "validate:v1.2-s08-p2";
const scriptName = "validate_memory_atlas_v1_2_s08_p2.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_agent_authorization.py";
const configPath = "机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json";
const outputPath = "data/derived/agent_collaboration/agent_authorization_boundary_report.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s08_p2_authorization_boundary.md";
const humanDocPath = "人类可读/20_Agent授权边界说明.md";
const testPath = "tests/test_s08p2_agent_authorization.py";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const historicalValidatorPaths = [
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s05_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s06_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p1.cjs",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  ...historicalValidatorPaths,
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${atlasctlPath}`,
  `OpenAIDatabase/${builderPath}`,
  `OpenAIDatabase/${configPath}`,
  `OpenAIDatabase/${outputPath}`,
  `OpenAIDatabase/${reviewPath}`,
  `OpenAIDatabase/${humanDocPath}`,
  `OpenAIDatabase/${testPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
  "OpenAIDatabase/人类可读/00_快速入口.md",
  "OpenAIDatabase/人类可读/01_v1.2四线14Stage升级总览.md",
  "OpenAIDatabase/机器治理/README.md",
  "OpenAIDatabase/机器治理/参数与公式/README.md",
  "OpenAIDatabase/机器治理/可视化配置/README.md",
  "OpenAIDatabase/机器治理/数据契约/README.md",
  "OpenAIDatabase/机器治理/行为智能模型/README.md",
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

function hasCjk(value) {
  return /[\u3400-\u9fff]/.test(String(value || ""));
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
    "s08p2_package_script",
    "package.json exposes the v1.2 S08 P2 validator",
    "package.json is missing the v1.2 S08 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s08p2_previous_phase_deferred_scope",
      "S08 P1 execution is deferred only because open diff is limited to S08 P2 files and compatibility updates",
      "S08 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s08p2_previous_phase_deferred_until_clean_tree", "S08 P1 validator will run on a clean tree after S08 P2 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s08_p1.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S08P1",
    "s08p2_previous_s08p1",
    "S08 P1 validator returns PASS before accepting S08 P2 on a clean tree",
    "S08 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateS08P2Artifacts() {
  [atlasctlPath, builderPath, configPath, outputPath, testPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["agent-authorization", "build_memory_atlas_agent_authorization.py", "run_agent_authorization_audit"]),
    "s08p2_atlasctl_contract",
    "atlasctl exposes S08 P2 agent-authorization analyze and audit entry points",
    "atlasctl is missing S08 P2 agent-authorization contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "does_not_apply_proposals", "does_not_implement_complex_delegation_contract_ui", "does_not_generate_stage_flight_recorder"]),
    "s08p2_builder_contract",
    "Agent authorization builder enforces S08 P2 phase boundaries",
    "Agent authorization builder is missing S08 P2 boundary markers",
  );
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredStates = new Set([
    "draft",
    "pending_human_review",
    "approved_by_human",
    "applying",
    "applied",
    "validated",
    "committed",
    "failed_validation",
    "rollback_or_needs_revision",
  ]);
  const states = new Set(config.proposal_state_machine?.states || []);
  const requiredFields = new Set(["proposal_id", "target_type", "target_files", "approval", "validation_commands", "rollback_plan"]);
  const configFields = new Set(config.proposal_required_fields || []);
  const missingStates = [...requiredStates].filter((state) => !states.has(state));
  const missingFields = [...requiredFields].filter((field) => !configFields.has(field));
  const outputChecks = Array.isArray(output.machine_output_checks) ? output.machine_output_checks : [];
  const checkIds = new Set(outputChecks.map((item) => item.check_id));
  const missingChecks = ["S08P2-CHECK-001", "S08P2-CHECK-002", "S08P2-CHECK-003", "S08P2-CHECK-004"].filter((item) => !checkIds.has(item));
  const badChecks = [];
  for (const item of outputChecks) {
    if (item.status !== "PASS") badChecks.push(`${item.check_id}:not_pass`);
    if (!hasCjk(item.explanation_zh)) badChecks.push(`${item.check_id}:missing_chinese_explanation`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badChecks.push(`${item.check_id}:missing_evidence_refs`);
  }
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.boundary_mode === "machine_config_and_output_checks" &&
      config.delegation_contract_ui?.complex_ui_required === false &&
      config.proposal_state_machine?.human_approval_required === true &&
      config.proposal_state_machine?.current_phase_executes_apply === false &&
      config.proposal_state_machine?.apply_execution_deferred_to === "S13" &&
      (config.apply_forbidden_targets || []).includes("public_raw") &&
      (config.apply_forbidden_targets || []).includes("credentials") &&
      (config.forbidden_path_prefixes || []).includes("data/public_raw/") &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.phase_boundary?.authorization_boundary_defined_as_machine_checks === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.requires_human_approval_before_apply === true &&
      output.phase_boundary?.raw_is_never_apply_target === true &&
      output.phase_boundary?.does_not_implement_complex_delegation_contract_ui === true &&
      output.phase_boundary?.does_not_generate_stage_flight_recorder === true &&
      output.phase_boundary?.next_phase === "S08 P3" &&
      missingStates.length === 0 &&
      missingFields.length === 0 &&
      missingChecks.length === 0 &&
      badChecks.length === 0,
    "s08p2_authorization_report",
    "Agent authorization boundary report defines machine checks, human approval gate and raw no-apply boundary",
    "Agent authorization boundary report failed S08 P2 acceptance",
    { missingStates, missingFields, missingChecks, badChecks },
  );
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "agent-authorization", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "agent-authorization"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    dryRun.task_id === taskId &&
      dryRun.acceptance_id === acceptanceId &&
      dryRun.writes_files === false &&
      audit.status === "PASS" &&
      audit.task_id === taskId &&
      audit.acceptance_id === acceptanceId &&
      Array.isArray(audit.bad_items) &&
      audit.bad_items.length === 0 &&
      audit.machine_output_check_count === 4 &&
      audit.human_approval_required === true &&
      audit.raw_apply_target_allowed === false &&
      audit.proposal_apply_execution === false &&
      audit.complex_delegation_contract_ui === false &&
      audit.stage_flight_recorder === "deferred_to_s08_p3",
    "s08p2_atlasctl_gates",
    "atlasctl analyze --stage agent-authorization dry-run and audit --check agent-authorization pass",
    "atlasctl S08 P2 gates failed",
    { dryRun: { task_id: dryRun.task_id, writes_files: dryRun.writes_files }, audit },
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    humanDocPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/参数与公式/README.md",
    "机器治理/可视化配置/README.md",
    "机器治理/数据契约/README.md",
    "机器治理/行为智能模型/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);
  const review = readRepoFile(reviewPath);
  const human = readRepoFile(humanDocPath);
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s08ReviewState =
    hasAll(quick, ["当前阶段是 S08 Review", "MA-V12-S08-REVIEW", "ACC-MA-V12-S08-REVIEW", "下一步只允许进入 S09 P1"]) &&
    hasAll(overview, ["S08 Review 已完成", "Codex/Agent 协作质量", "stage flight recorder", "下一步是 S09 P1"]) &&
    hasAll(machine, ["当前为 S08 Review", "MA-V12-S08-REVIEW", "validate:v1.2-s08-review", "下一步是 S09 P1"]) &&
    hasAll(dataContract, ["当前 S08 Review 已完成", "agent_collaboration_quality_report.json", "agent_authorization_boundary_report.json", "stage_flight_recorder.json", "下一步是 S09 P1"]) &&
    hasAll(behavior, ["当前 S08 Review 已完成", "Codex/Agent 协作质量", "授权边界", "stage flight recorder", "下一步是 S09 P1"]) &&
    hasAll(runGate, ["当前阶段是 S08 Review", "MA-V12-S08-REVIEW", "ACC-MA-V12-S08-REVIEW", "validate:v1.2-s08-review"]);
  const s08p3State =
    hasAll(quick, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "下一步只允许进入 S08 Review"]) &&
    hasAll(overview, ["S08 P3 已完成", "stage flight recorder", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(machine, ["当前为 S08 P3", "MA-V12-S08P3", "validate:v1.2-s08-p3", "下一步是 S08 Review"]) &&
    hasAll(dataContract, ["当前 S08 P3 已完成", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(behavior, ["当前 S08 P3 已完成", "stage_flight_recorder_fields.v1_2_s08_p3.json", "stage_flight_recorder.json", "下一步是 S08 Review"]) &&
    hasAll(runGate, ["当前阶段是 S08 P3", "MA-V12-S08P3", "ACC-MA-V12-S08P3", "validate:v1.2-s08-p3"]);
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, "raw 不可修改", "approved_by_human", outputPath, "No GitHub main upload in this phase", "pending S08 P3"]),
    "s08p2_review_artifact",
    "S08 P2 review artifact records authorization boundary, output and no-upload boundary",
    "S08 P2 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, "人类授权后才能 apply", "raw 不可修改", "复杂 Delegation Contract UI", "下一步只允许进入 S08 P3"]),
    "s08p2_human_doc",
    "Human doc explains authorization boundary in Chinese",
    "S08 P2 human doc is incomplete",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S08 P2", "下一步只允许进入 S08 P3"]),
    "s08p2_quick_entry",
    "Quick entry records S08 P2 state and next S08 P3 gate",
    "Quick entry is missing S08 P2 state",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(overview, ["S08 P2 已完成", "授权边界", outputPath, "下一步是 S08 P3"]),
    "s08p2_overview",
    "Overview records S08 P2 state and output",
    "Overview is missing S08 P2 state",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(machine, ["当前为 S08 P2", taskId, validatorName, "下一步是 S08 P3"]),
    "s08p2_machine_readme",
    "Machine README records S08 P2 identity and next gate",
    "Machine README is missing S08 P2 state",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(dataContract, ["当前 S08 P2 已完成", outputPath, "agent_authorization_boundary_report.json", "下一步是 S08 P3"]),
    "s08p2_data_contract",
    "Data contract README records S08 P2 authorization output",
    "Data contract README is missing S08 P2 output",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(behavior, ["当前 S08 P2 已完成", configPath, outputPath, "approved_by_human", "raw 不可修改", "下一步是 S08 P3"]),
    "s08p2_behavior_readme",
    "Behavior model README records S08 P2 authorization config and output",
    "Behavior model README is missing S08 P2 state",
  );
  assertCondition(
    s08ReviewState || s08p3State || hasAll(runGate, ["当前阶段是 S08 P2", taskId, acceptanceId, validatorName, "agent-authorization", "下一步是 S08 P3"]),
    "s08p2_run_gate",
    "Run gate README records S08 P2 validator and next gate",
    "Run gate README is missing S08 P2 gate",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S08 P2", "pending S08 P3", "No GitHub main upload in this phase"]),
      `s08p2_records_${name}`,
      `${name} records S08 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S08 P2 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s08p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s08p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S08 P2 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s08p2_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s08p2_open_diff_scope",
    "Open diff is limited to S08 P2 files and historical-validator compatibility",
    "Open diff contains files outside S08 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );
  const publicRawDiff = run("git", ["diff", "--name-only", "--", "OpenAIDatabase/data/public_raw"], { cwd: worktreeRoot }).stdout.trim();
  const forbiddenOpenChanges = changed.filter((file) =>
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    file.includes(".env") ||
    file.includes("cookies") ||
    file.includes("session_token") ||
    file.includes("password"),
  );
  assertCondition(
    forbiddenOpenChanges.length === 0 && publicRawDiff === "",
    "s08p2_no_raw_or_secret_open_changes",
    "S08 P2 open diff does not modify raw or secret/config files",
    "S08 P2 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateS08P2Artifacts();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s08_p2", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s08_p2",
      task_id: taskId,
      acceptance_id: acceptanceId,
      error: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
      checks,
    }, null, 2));
    process.exit(1);
  }
}

main();
