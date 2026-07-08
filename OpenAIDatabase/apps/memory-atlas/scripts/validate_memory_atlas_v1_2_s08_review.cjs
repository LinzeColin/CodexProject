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

const taskId = "MA-V12-S08-REVIEW";
const acceptanceId = "ACC-MA-V12-S08-REVIEW";
const status = "stage_s08_review_passed_pending_s09_no_github_main_upload";
const validatorName = "validate:v1.2-s08-review";
const scriptName = "validate_memory_atlas_v1_2_s08_review.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const collaborationConfigPath = "机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json";
const collaborationOutputPath = "data/derived/agent_collaboration/agent_collaboration_quality_report.json";
const authorizationConfigPath = "机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json";
const authorizationOutputPath = "data/derived/agent_collaboration/agent_authorization_boundary_report.json";
const stageFlightConfigPath = "机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json";
const stageFlightOutputPath = "data/derived/agent_collaboration/stage_flight_recorder.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s08_review.md";

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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s08_p3.cjs",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  ...historicalValidatorPaths,
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
    "s08_review_package_script",
    "package.json exposes the v1.2 S08 Review validator",
    "package.json is missing the v1.2 S08 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s08_review_previous_phase_deferred_scope",
      "S08 P3 execution is deferred only because open diff is limited to S08 Review files and compatibility updates",
      "S08 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s08_review_previous_phase_deferred_until_clean_tree", "S08 P3 validator will run on a clean tree after S08 Review commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s08_p3.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S08P3",
    "s08_review_previous_s08p3",
    "S08 P3 validator returns PASS before accepting S08 Review on a clean tree",
    "S08 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateCollaborationQuality() {
  [collaborationConfigPath, collaborationOutputPath, "docs/reviews/memory_atlas_v1_2_s08_p1_agent_collaboration.md", "人类可读/19_Agent协作质量指标说明.md"].forEach(validateTextFile);
  const config = readJson(collaborationConfigPath);
  const output = readJson(collaborationOutputPath);
  const metricKeys = new Set((output.overall_metrics || []).map((item) => item.metric_key));
  const requiredMetrics = ["planning_clarity", "execution_clarity", "review_burden", "rework_count", "scope_clarity", "testability", "rollbackability"];
  const missingMetrics = requiredMetrics.filter((key) => !metricKeys.has(key));
  const sourceIds = new Set((output.source_summaries || []).map((item) => item.source_id));
  const missingSources = ["chatgpt", "codex", "future_agent"].filter((source) => !sourceIds.has(source));
  const badMetrics = [];
  for (const item of output.overall_metrics || []) {
    const score = Number(item.score);
    if (!Number.isFinite(score) || score < 0 || score > 100) badMetrics.push(`${item.metric_key}:score_out_of_range`);
    if (!item.formula_id || item.formula_source !== collaborationConfigPath) badMetrics.push(`${item.metric_key}:missing_formula_source`);
    if (!hasCjk(item.explanation_zh)) badMetrics.push(`${item.metric_key}:missing_chinese_explanation`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badMetrics.push(`${item.metric_key}:missing_evidence_refs`);
  }
  assertCondition(
    config.task_id === "MA-V12-S08P1" &&
      config.acceptance_id === "ACC-MA-V12-S08P1" &&
      Array.isArray(config.metrics) &&
      config.metrics.length === 7 &&
      config.scope_boundary?.multi_agent_system_implementation === false &&
      config.scope_boundary?.complex_delegation_contract_ui === false &&
      output.task_id === "MA-V12-S08P1" &&
      output.acceptance_id === "ACC-MA-V12-S08P1" &&
      output.status === "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2" &&
      output.collaboration_quality_summary?.metric_count === 7 &&
      output.phase_boundary?.does_not_create_multi_agent_system === true &&
      output.phase_boundary?.does_not_implement_complex_delegation_contract_ui === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      missingMetrics.length === 0 &&
      missingSources.length === 0 &&
      badMetrics.length === 0,
    "s08_review_collaboration_quality",
    "S08 P1 explains ChatGPT/Codex/future agent collaboration quality with evidence-backed metrics",
    "S08 P1 collaboration quality failed S08 Review",
    { missingMetrics, missingSources, badMetrics },
  );
}

function validateAuthorizationBoundary() {
  [authorizationConfigPath, authorizationOutputPath, "docs/reviews/memory_atlas_v1_2_s08_p2_authorization_boundary.md", "人类可读/20_Agent授权边界说明.md"].forEach(validateTextFile);
  const config = readJson(authorizationConfigPath);
  const output = readJson(authorizationOutputPath);
  const checkIds = new Set((output.machine_output_checks || []).map((item) => item.check_id));
  const missingChecks = ["S08P2-CHECK-001", "S08P2-CHECK-002", "S08P2-CHECK-003", "S08P2-CHECK-004"].filter((id) => !checkIds.has(id));
  const badChecks = [];
  for (const item of output.machine_output_checks || []) {
    if (item.status !== "PASS") badChecks.push(`${item.check_id}:not_pass`);
    if (!hasCjk(item.explanation_zh) || !hasCjk(item.failure_action_zh)) badChecks.push(`${item.check_id}:missing_chinese_explanation`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badChecks.push(`${item.check_id}:missing_evidence_refs`);
  }
  assertCondition(
    config.task_id === "MA-V12-S08P2" &&
      config.acceptance_id === "ACC-MA-V12-S08P2" &&
      config.scope_boundary?.authorization_boundary_defined_as_machine_checks === true &&
      config.scope_boundary?.complex_delegation_contract_ui === false &&
      config.scope_boundary?.multi_agent_system_implementation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      config.scope_boundary?.raw_mutation === false &&
      output.task_id === "MA-V12-S08P2" &&
      output.acceptance_id === "ACC-MA-V12-S08P2" &&
      output.status === "phase_s08_p2_authorization_boundary_completed_pending_s08_p3" &&
      output.phase_boundary?.authorization_boundary_defined_as_machine_checks === true &&
      output.phase_boundary?.requires_human_approval_before_apply === true &&
      output.phase_boundary?.raw_is_never_apply_target === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.does_not_implement_complex_delegation_contract_ui === true &&
      output.phase_boundary?.does_not_create_multi_agent_system === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      missingChecks.length === 0 &&
      badChecks.length === 0,
    "s08_review_authorization_boundary",
    "S08 P2 keeps authorization as low-burden machine checks with human approval before apply and raw no-apply",
    "S08 P2 authorization boundary failed S08 Review",
    { missingChecks, badChecks },
  );
}

function validateStageFlightRecorder() {
  [stageFlightConfigPath, stageFlightOutputPath].forEach(validateTextFile);
  const config = readJson(stageFlightConfigPath);
  const output = readJson(stageFlightOutputPath);
  const phaseIds = new Set((output.phase_records || []).map((item) => item.phase_id));
  const missingPhases = ["S08 P1", "S08 P2", "S08 P3"].filter((phase) => !phaseIds.has(phase));
  const badRecords = [];
  for (const item of output.phase_records || []) {
    if (!hasCjk(item.summary_zh)) badRecords.push(`${item.phase_id}:missing_chinese_summary`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badRecords.push(`${item.phase_id}:missing_evidence_refs`);
    if (!Array.isArray(item.validation_refs) || item.validation_refs.length === 0) badRecords.push(`${item.phase_id}:missing_validation_refs`);
    for (const key of ["raw_mutation", "github_main_upload", "complex_delegation_contract_ui", "multi_agent_system_implementation"]) {
      if (item.boundary_flags?.[key] !== false) badRecords.push(`${item.phase_id}:${key}_not_false`);
    }
  }
  assertCondition(
    config.task_id === "MA-V12-S08P3" &&
      config.acceptance_id === "ACC-MA-V12-S08P3" &&
      config.recorder_mode === "lightweight_run_evidence_fields" &&
      config.field_policy?.max_required_fields <= 12 &&
      config.field_policy?.no_raw_content === true &&
      config.field_policy?.no_transcript_payloads === true &&
      config.field_policy?.no_bulky_human_docs === true &&
      output.task_id === "MA-V12-S08P3" &&
      output.acceptance_id === "ACC-MA-V12-S08P3" &&
      output.recorder_mode === "lightweight_run_evidence_fields" &&
      output.required_fields?.length === 10 &&
      output.machine_output_checks?.length === 4 &&
      output.phase_boundary?.lightweight_stage_flight_recorder === true &&
      output.phase_boundary?.does_not_include_raw_or_transcript_payloads === true &&
      output.phase_boundary?.does_not_generate_bulky_human_docs === true &&
      output.phase_boundary?.does_not_upload_github_main === true &&
      missingPhases.length === 0 &&
      badRecords.length === 0,
    "s08_review_stage_flight_recorder",
    "S08 P3 provides lightweight stage flight evidence for all S08 phases without raw payloads or bulky docs",
    "S08 P3 stage flight recorder failed S08 Review",
    { missingPhases, badRecords },
  );
}

function validateAtlasctlGates() {
  const collaboration = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "agent-collaboration", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const authorization = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "agent-authorization", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const stageFlight = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "stage-flight", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const collaborationAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "agent-collaboration"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const authorizationAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "agent-authorization"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const stageFlightAudit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "stage-flight"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    collaboration.task_id === "MA-V12-S08P1" &&
      authorization.task_id === "MA-V12-S08P2" &&
      stageFlight.task_id === "MA-V12-S08P3" &&
      collaboration.writes_files === false &&
      authorization.writes_files === false &&
      stageFlight.writes_files === false &&
      collaborationAudit.status === "PASS" &&
      authorizationAudit.status === "PASS" &&
      stageFlightAudit.status === "PASS" &&
      Array.isArray(collaborationAudit.bad_items) &&
      collaborationAudit.bad_items.length === 0 &&
      Array.isArray(authorizationAudit.bad_items) &&
      authorizationAudit.bad_items.length === 0 &&
      Array.isArray(stageFlightAudit.bad_items) &&
      stageFlightAudit.bad_items.length === 0,
    "s08_review_atlasctl_gates",
    "atlasctl S08 analyze dry-runs and collaboration/authorization/stage-flight audits pass",
    "atlasctl S08 gates failed Review",
    { collaborationAudit, authorizationAudit, stageFlightAudit },
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
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
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "Codex/Agent 协作质量",
      "授权边界",
      "stage flight recorder",
      "No GitHub main upload in this phase",
      "pending S09 P1",
    ]),
    "s08_review_artifact",
    "S08 Review artifact records stage acceptance, S08 P1/P2/P3 outputs and no-upload boundary",
    "S08 Review artifact is incomplete",
  );
  assertCondition(
    hasAll(quick, ["当前阶段是 S09 P1", "MA-V12-S09P1", "ACC-MA-V12-S09P1", "下一步只允许进入 S09 P2"]),
    "s08_review_quick_entry",
    "Quick entry has advanced to S09 P1 while preserving S08 Review records",
    "Quick entry is missing S09 P1 current state",
  );
  assertCondition(
    hasAll(overview, ["S09 P1 已完成", "latent_signals.json", "下一步是 S09 P2"]),
    "s08_review_overview",
    "Overview has advanced to S09 P1 while preserving S08 Review records",
    "Overview is missing S09 P1 current state",
  );
  assertCondition(
    hasAll(machine, ["当前为 S09 P1", "MA-V12-S09P1", "ACC-MA-V12-S09P1", "validate:v1.2-s09-p1", "下一步是 S09 P2"]),
    "s08_review_machine_readme",
    "Machine README has advanced to S09 P1 while preserving S08 Review records",
    "Machine README is missing S09 P1 current state",
  );
  assertCondition(
    hasAll(dataContract, ["当前 S09 P1 已完成", "latent_signals.json", "下一步是 S09 P2"]),
    "s08_review_data_contract",
    "Data contract README has advanced to S09 P1 while preserving S08 Review records",
    "Data contract README is missing S09 P1 current state",
  );
  assertCondition(
    hasAll(behavior, ["当前 S09 P1 已完成", "latent_signals.v1_2_s09_p1.json", "latent_signals.json", "下一步是 S09 P2"]),
    "s08_review_behavior_readme",
    "Behavior model README has advanced to S09 P1 while preserving S08 Review records",
    "Behavior model README is missing S09 P1 current state",
  );
  assertCondition(
    hasAll(runGate, ["当前阶段是 S09 P1", "MA-V12-S09P1", "ACC-MA-V12-S09P1", "validate:v1.2-s09-p1"]),
    "s08_review_run_gate",
    "Run gate README has advanced to S09 P1 while preserving S08 Review records",
    "Run gate README is missing S09 P1 current state",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S08 Review", "pending S09 P1", "No GitHub main upload in this phase"]),
      `s08_review_records_${name}`,
      `${name} records S08 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S08 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s08_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s08_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S08 Review branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s08_review_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s08_review_open_diff_scope",
    "Open diff is limited to S08 Review files and historical-validator compatibility",
    "Open diff contains files outside S08 Review allowed scope",
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
    "s08_review_no_raw_or_secret_open_changes",
    "S08 Review open diff does not modify raw or secret/config files",
    "S08 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateCollaborationQuality();
    validateAuthorizationBoundary();
    validateStageFlightRecorder();
    validateAtlasctlGates();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s08_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s08_review",
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
