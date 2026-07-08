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

const taskId = "MA-V12-S08P1";
const acceptanceId = "ACC-MA-V12-S08P1";
const status = "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2";
const validatorName = "validate:v1.2-s08-p1";
const scriptName = "validate_memory_atlas_v1_2_s08_p1.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const atlasctlPath = "scripts/atlasctl.py";
const builderPath = "scripts/build_memory_atlas_agent_collaboration.py";
const configPath = "机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json";
const outputPath = "data/derived/agent_collaboration/agent_collaboration_quality_report.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s08_p1_agent_collaboration.md";
const humanDocPath = "人类可读/19_Agent协作质量指标说明.md";
const testPath = "tests/test_s08p1_agent_collaboration.py";

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
    "s08p1_package_script",
    "package.json exposes the v1.2 S08 P1 validator",
    "package.json is missing the v1.2 S08 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s08p1_previous_phase_deferred_scope",
      "S07 Review execution is deferred only because open diff is limited to S08 P1 files and compatibility updates",
      "S07 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s08p1_previous_phase_deferred_until_clean_tree", "S07 Review validator will run on a clean tree after S08 P1 commit", { changed });
    return;
  }
  const parsed = parseJsonFromStdout(run("node", ["scripts/validate_memory_atlas_v1_2_s07_review.cjs"], {
    cwd: appRoot,
    timeout: 300000,
  }));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S07-REVIEW",
    "s08p1_previous_s07_review",
    "S07 Review validator returns PASS before accepting S08 P1 on a clean tree",
    "S07 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateS08P1Artifacts() {
  [atlasctlPath, builderPath, configPath, outputPath, testPath].forEach(validateTextFile);
  const atlasctl = readRepoFile(atlasctlPath);
  const builder = readRepoFile(builderPath);
  assertCondition(
    hasAll(atlasctl, ["agent-collaboration", "build_memory_atlas_agent_collaboration.py", "run_agent_collaboration_audit", "agent-collaboration"]),
    "s08p1_atlasctl_contract",
    "atlasctl exposes S08 P1 agent-collaboration analyze and audit entry points",
    "atlasctl is missing S08 P1 agent-collaboration contract",
  );
  assertCondition(
    hasAll(builder, [taskId, acceptanceId, "does_not_create_multi_agent_system", "does_not_implement_complex_delegation_contract_ui", "does_not_generate_stage_flight_recorder"]),
    "s08p1_builder_contract",
    "Agent collaboration builder enforces S08 P1 phase boundaries",
    "Agent collaboration builder is missing S08 P1 boundary markers",
  );
  const config = readJson(configPath);
  const output = readJson(outputPath);
  const requiredMetrics = new Set([
    "planning_clarity",
    "execution_clarity",
    "review_burden",
    "rework_count",
    "scope_clarity",
    "testability",
    "rollbackability",
  ]);
  const configMetricKeys = new Set((config.metrics || []).map((item) => item.metric_key));
  const outputMetricKeys = new Set((output.overall_metrics || []).map((item) => item.metric_key));
  const missing = [...requiredMetrics].filter((key) => !configMetricKeys.has(key) || !outputMetricKeys.has(key));
  const badItems = [];
  for (const metric of output.overall_metrics || []) {
    const score = Number(metric.score);
    if (!Number.isFinite(score) || score < 0 || score > 100) badItems.push(`${metric.metric_key}:score_out_of_range`);
    if (!metric.formula_id || metric.formula_source !== configPath) badItems.push(`${metric.metric_key}:missing_formula_source`);
    if (!hasCjk(metric.explanation_zh)) badItems.push(`${metric.metric_key}:missing_chinese_explanation`);
    if (!Array.isArray(metric.evidence_refs) || metric.evidence_refs.length === 0) badItems.push(`${metric.metric_key}:missing_evidence_refs`);
  }
  const sourceTypes = new Set((output.source_summaries || []).map((item) => item.source_type));
  const missingSourceTypes = ["chatgpt", "codex", "other_agent"].filter((item) => !sourceTypes.has(item));
  assertCondition(
    config.task_id === taskId &&
      config.acceptance_id === acceptanceId &&
      config.scope_boundary?.multi_agent_system_implementation === false &&
      config.scope_boundary?.complex_delegation_contract_ui === false &&
      output.task_id === taskId &&
      output.acceptance_id === acceptanceId &&
      output.status === status &&
      output.phase_boundary?.does_not_create_multi_agent_system === true &&
      output.phase_boundary?.does_not_implement_complex_delegation_contract_ui === true &&
      output.phase_boundary?.does_not_define_authorization_apply_boundary === true &&
      output.phase_boundary?.does_not_generate_stage_flight_recorder === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      missing.length === 0 &&
      badItems.length === 0 &&
      missingSourceTypes.length === 0,
    "s08p1_collaboration_report",
    "Agent collaboration report defines evidence-backed metrics, Chinese explanations and shared source fields",
    "Agent collaboration report failed S08 P1 acceptance",
    { metric_count: (output.overall_metrics || []).length, badItems, missing, missingSourceTypes },
  );
  const summary = output.chinese_summary || {};
  assertCondition(
    hasCjk(summary.summary_zh) &&
      hasAll(summary.human_responsibility_zh || "", ["人负责"]) &&
      hasAll(summary.agent_responsibility_zh || "", ["Agent 负责"]) &&
      hasCjk(summary.rework_sources_zh) &&
      hasCjk(summary.agent_fit_zh) &&
      hasCjk(summary.human_judgment_zh),
    "s08p1_chinese_summary",
    "Collaboration report includes a Chinese human/agent responsibility summary",
    "Collaboration report Chinese summary is incomplete",
    summary,
  );
  const dryRun = parseJsonFromStdout(run("python", [atlasctlPath, "analyze", "--stage", "agent-collaboration", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const audit = parseJsonFromStdout(run("python", [atlasctlPath, "audit", "--check", "agent-collaboration"], {
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
      audit.metric_count === 7 &&
      audit.complex_delegation_contract_ui === false &&
      audit.multi_agent_system_implementation === false &&
      audit.raw_mutation === false,
    "s08p1_atlasctl_gates",
    "atlasctl analyze --stage agent-collaboration dry-run and audit --check agent-collaboration pass",
    "atlasctl S08 P1 gates failed",
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
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, "planning_clarity", "execution_clarity", "review_burden", outputPath, "No GitHub main upload in this phase", "pending S08 P2"]),
    "s08p1_review_artifact",
    "S08 P1 review artifact records collaboration metrics, output and no-upload boundary",
    "S08 P1 review artifact is incomplete",
  );
  assertCondition(
    hasAll(human, [taskId, acceptanceId, "人负责", "Agent 负责", "返工来自哪里", "复杂 Delegation Contract UI", "下一步只允许进入 S08 P2"]),
    "s08p1_human_doc",
    "Human doc explains collaboration quality metrics in Chinese",
    "S08 P1 human doc is incomplete",
  );
  assertCondition(
    hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S08 P1", "下一步只允许进入 S08 P2"]),
    "s08p1_quick_entry",
    "Quick entry records S08 P1 state and next S08 P2 gate",
    "Quick entry is missing S08 P1 state",
  );
  assertCondition(
    hasAll(overview, ["S08 P1 已完成", "Codex/Agent 协作质量", outputPath, "下一步是 S08 P2"]),
    "s08p1_overview",
    "Overview records S08 P1 state and output",
    "Overview is missing S08 P1 state",
  );
  assertCondition(
    hasAll(machine, ["当前为 S08 P1", taskId, validatorName, "下一步是 S08 P2"]),
    "s08p1_machine_readme",
    "Machine README records S08 P1 identity and next gate",
    "Machine README is missing S08 P1 state",
  );
  assertCondition(
    hasAll(dataContract, ["当前 S08 P1 已完成", outputPath, "agent_collaboration_quality_report.json", "下一步是 S08 P2"]),
    "s08p1_data_contract",
    "Data contract README records S08 P1 collaboration output",
    "Data contract README is missing S08 P1 output",
  );
  assertCondition(
    hasAll(behavior, ["当前 S08 P1 已完成", configPath, outputPath, "planning_clarity", "rollbackability", "下一步是 S08 P2"]),
    "s08p1_behavior_readme",
    "Behavior model README records S08 P1 metrics config and output",
    "Behavior model README is missing S08 P1 state",
  );
  assertCondition(
    hasAll(runGate, ["当前阶段是 S08 P1", taskId, acceptanceId, validatorName, "agent-collaboration", "下一步是 S08 P2"]),
    "s08p1_run_gate",
    "Run gate README records S08 P1 validator and next gate",
    "Run gate README is missing S08 P1 gate",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S08 P1", "pending S08 P2", "No GitHub main upload in this phase"]),
      `s08p1_records_${name}`,
      `${name} records S08 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S08 P1 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s08p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s08p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S08 P1 branch",
    { branch, branchName },
  );
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(remoteDev === "", "s08p1_no_remote_development_branch", "No remote v1.2 development branch exists", "Remote v1.2 development branch exists unexpectedly", {
    branchName,
    remoteDev,
  });
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s08p1_open_diff_scope",
    "Open diff is limited to S08 P1 files and historical-validator compatibility",
    "Open diff contains files outside S08 P1 allowed scope",
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
    "s08p1_no_raw_or_secret_open_changes",
    "S08 P1 open diff does not modify raw or secret/config files",
    "S08 P1 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateS08P1Artifacts();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s08_p1", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s08_p1",
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
