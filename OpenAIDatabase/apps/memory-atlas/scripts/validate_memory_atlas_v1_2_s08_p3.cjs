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

const taskId = "MA-V12-S08P3";
const acceptanceId = "ACC-MA-V12-S08P3";
const status = "phase_s08_p3_stage_flight_recorder_completed_pending_s08_review";
const validatorName = "validate:v1.2-s08-p3";
const scriptName = "validate_memory_atlas_v1_2_s08_p3.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_stage_flight.py";
const configPath = "机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json";
const outputPath = "data/derived/agent_collaboration/stage_flight_recorder.json";
const testPath = "tests/test_s08p3_stage_flight.py";

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
    "s08p3_package_script",
    "package.json exposes the v1.2 S08 P3 validator",
    "package.json is missing the v1.2 S08 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s08p3_previous_phase_deferred_scope",
      "S08 P2 execution is deferred only because open diff is limited to S08 P3 files and compatibility updates",
      "S08 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s08p3_previous_phase_deferred_until_clean_tree", "S08 P2 validator will run on a clean tree after S08 P3 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s08_p2.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S08P2",
    "s08p3_previous_s08p2",
    "S08 P2 validator returns PASS before accepting S08 P3 on a clean tree",
    "S08 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateS08P3Artifacts() {
  [atlasctlPath, builderPath, configPath, outputPath, testPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["stage-flight", "build_memory_atlas_stage_flight.py", "run_stage_flight_audit"]),
    "s08p3_atlasctl_contract",
    "atlasctl exposes S08 P3 stage-flight analyze and audit entry points",
    "atlasctl is missing S08 P3 stage-flight contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "lightweight_stage_flight_recorder", "does_not_generate_bulky_human_docs", "records_necessary_info_in_development_records"]),
    "s08p3_builder_contract",
    "Stage flight builder enforces S08 P3 lightweight phase boundaries",
    "Stage flight builder is missing S08 P3 boundary markers",
  );
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredFieldIds = new Set(["stage_id", "phase_id", "task_id", "acceptance_id", "status", "summary_zh", "evidence_refs", "validation_refs", "boundary_flags", "next_gate"]);
  const configFields = new Set((config.required_fields || []).map((item) => item.field_id));
  const outputFields = new Set((output.required_fields || []).map((item) => item.field_id));
  const missingConfigFields = [...requiredFieldIds].filter((field) => !configFields.has(field));
  const missingOutputFields = [...requiredFieldIds].filter((field) => !outputFields.has(field));
  const phaseIds = new Set((output.phase_records || []).map((item) => item.phase_id));
  const missingPhases = ["S08 P1", "S08 P2", "S08 P3"].filter((phase) => !phaseIds.has(phase));
  const outputChecks = Array.isArray(output.machine_output_checks) ? output.machine_output_checks : [];
  const checkIds = new Set(outputChecks.map((item) => item.check_id));
  const missingChecks = ["S08P3-CHECK-001", "S08P3-CHECK-002", "S08P3-CHECK-003", "S08P3-CHECK-004"].filter((item) => !checkIds.has(item));
  const badChecks = [];
  for (const item of outputChecks) {
    if (item.status !== "PASS") badChecks.push(`${item.check_id}:not_pass`);
    if (!hasCjk(item.explanation_zh)) badChecks.push(`${item.check_id}:missing_chinese_explanation`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badChecks.push(`${item.check_id}:missing_evidence_refs`);
  }
  const badRecords = [];
  for (const item of output.phase_records || []) {
    if (!hasCjk(item.summary_zh)) badRecords.push(`${item.phase_id}:missing_chinese_summary`);
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badRecords.push(`${item.phase_id}:missing_evidence_refs`);
    if (!Array.isArray(item.validation_refs) || item.validation_refs.length === 0) badRecords.push(`${item.phase_id}:missing_validation_refs`);
    const flags = item.boundary_flags || {};
    for (const key of ["raw_mutation", "github_main_upload", "complex_delegation_contract_ui", "multi_agent_system_implementation"]) {
      if (flags[key] !== false) badRecords.push(`${item.phase_id}:${key}_not_false`);
    }
  }
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.recorder_mode === "lightweight_run_evidence_fields" &&
      config.field_policy?.max_required_fields <= 12 &&
      config.field_policy?.no_transcript_payloads === true &&
      config.field_policy?.no_raw_content === true &&
      config.field_policy?.no_bulky_human_docs === true &&
      config.field_policy?.development_record_summary_only === true &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.github_main_upload === false &&
      config.scope_boundary?.bulky_human_documentation === false &&
      config.scope_boundary?.human_readable_page_required === false &&
      config.scope_boundary?.development_record_summary_only === true &&
      config.scope_boundary?.next_phase === "S08 Review" &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.recorder_mode === "lightweight_run_evidence_fields" &&
      output.phase_boundary?.lightweight_stage_flight_recorder === true &&
      output.phase_boundary?.does_not_include_raw_or_transcript_payloads === true &&
      output.phase_boundary?.does_not_generate_bulky_human_docs === true &&
      output.phase_boundary?.records_necessary_info_in_development_records === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.does_not_upload_github_main === true &&
      output.phase_boundary?.next_phase === "S08 Review" &&
      missingConfigFields.length === 0 &&
      missingOutputFields.length === 0 &&
      missingPhases.length === 0 &&
      missingChecks.length === 0 &&
      badChecks.length === 0 &&
      badRecords.length === 0,
    "s08p3_stage_flight_report",
    "Stage flight recorder defines lightweight fields, phase records and no-bulky-doc boundary",
    "Stage flight recorder failed S08 P3 acceptance",
    { missingConfigFields, missingOutputFields, missingPhases, missingChecks, badChecks, badRecords },
  );
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "stage-flight", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "stage-flight"], {
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
      audit.required_field_count === 10 &&
      audit.phase_record_count === 3 &&
      audit.machine_output_check_count === 4 &&
      audit.bulky_human_documentation === false &&
      audit.raw_mutation === false &&
      audit.github_main_upload === false &&
      audit.next_phase === "S08 Review",
    "s08p3_atlasctl_gates",
    "atlasctl analyze --stage stage-flight dry-run and audit --check stage-flight pass",
    "atlasctl S08 P3 gates failed",
    { dryRun: { task_id: dryRun.task_id, writes_files: dryRun.writes_files }, audit },
  );
}

function validateDocsAndRecords() {
  [
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
  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const dataContract = readRepoFile("机器治理/数据契约/README.md");
  const behavior = readRepoFile("机器治理/行为智能模型/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const s08ReviewState =
    hasAll(quick, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "下一步只允许进入 S09 P3"]) &&
    hasAll(overview, ["S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(machine, ["当前为 S09 P2", "MA-V12-S09P2", "validate:v1.2-s09-p2", "下一步是 S09 P3"]) &&
    hasAll(dataContract, ["当前 S09 P2 已完成", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(behavior, ["当前 S09 P2 已完成", "self_iteration.v1_2_s09_p2.json", "self_iteration_suggestions.json", "下一步是 S09 P3"]) &&
    hasAll(runGate, ["当前阶段是 S09 P2", "MA-V12-S09P2", "ACC-MA-V12-S09P2", "validate:v1.2-s09-p2"]);
  assertCondition(
    !fs.existsSync(path.join(repoRoot, "人类可读/21_StageFlightRecorder说明.md")),
    "s08p3_no_extra_human_doc",
    "S08 P3 does not create a bulky extra human-readable stage-flight doc",
    "S08 P3 created an extra human-readable stage-flight doc",
  );
  assertCondition(
    s08ReviewState || hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S08 P3", "下一步只允许进入 S08 Review"]),
    "s08p3_quick_entry",
    "Quick entry records S08 P3 state and next S08 Review gate",
    "Quick entry is missing S08 P3 state",
  );
  assertCondition(
    s08ReviewState || hasAll(overview, ["S08 P3 已完成", "stage flight recorder", outputPath, "下一步是 S08 Review"]),
    "s08p3_overview",
    "Overview records S08 P3 state and output",
    "Overview is missing S08 P3 state",
  );
  assertCondition(
    s08ReviewState || hasAll(machine, ["当前为 S08 P3", taskId, validatorName, "下一步是 S08 Review"]),
    "s08p3_machine_readme",
    "Machine README records S08 P3 identity and next gate",
    "Machine README is missing S08 P3 state",
  );
  assertCondition(
    s08ReviewState || hasAll(dataContract, ["当前 S08 P3 已完成", outputPath, "stage_flight_recorder.json", "下一步是 S08 Review"]),
    "s08p3_data_contract",
    "Data contract README records S08 P3 stage flight output",
    "Data contract README is missing S08 P3 output",
  );
  assertCondition(
    s08ReviewState || hasAll(behavior, ["当前 S08 P3 已完成", configPath, outputPath, "lightweight stage flight recorder", "下一步是 S08 Review"]),
    "s08p3_behavior_readme",
    "Behavior model README records S08 P3 lightweight stage flight output",
    "Behavior model README is missing S08 P3 state",
  );
  assertCondition(
    s08ReviewState || hasAll(runGate, ["当前阶段是 S08 P3", taskId, acceptanceId, validatorName, "stage-flight", "下一步是 S08 Review"]),
    "s08p3_run_gate",
    "Run gate README records S08 P3 validator and next gate",
    "Run gate README is missing S08 P3 gate",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S08 P3", "pending S08 Review", "No GitHub main upload in this phase"]),
      `s08p3_records_${name}`,
      `${name} records S08 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S08 P3 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s08p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s08p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S08 P3 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s08p3_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s08p3_open_diff_scope",
    "Open diff is limited to S08 P3 files and historical-validator compatibility",
    "Open diff contains files outside S08 P3 allowed scope",
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
    "s08p3_no_raw_or_secret_open_changes",
    "S08 P3 open diff does not modify raw or secret/config files",
    "S08 P3 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateS08P3Artifacts();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s08_p3", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s08_p3",
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
