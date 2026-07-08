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

const taskId = "MA-V12-S09-REVIEW";
const acceptanceId = "ACC-MA-V12-S09-REVIEW";
const status = "stage_s09_review_passed_pending_s10_no_github_main_upload";
const validatorName = "validate:v1.2-s09-review";
const scriptName = "validate_memory_atlas_v1_2_s09_review.cjs";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const latentConfigPath = "机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json";
const latentOutputPath = "data/derived/behavior_intelligence/latent_signals.json";
const selfIterationConfigPath = "机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json";
const selfIterationOutputPath = "data/derived/behavior_intelligence/self_iteration_suggestions.json";
const decisionDebtConfigPath = "机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json";
const decisionDebtOutputPath = "data/derived/behavior_intelligence/decision_debt_ledger.json";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s09_review.md";

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
    "s09_review_package_script",
    "package.json exposes the v1.2 S09 Review validator",
    "package.json is missing the v1.2 S09 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s09_review_previous_phase_deferred_scope",
      "S09 P3 execution is deferred only because open diff is limited to S09 Review files",
      "S09 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s09_review_previous_phase_deferred_until_clean_tree", "S09 P3 persisted artifacts will be checked on a clean tree after S09 Review commit", { changed });
    return;
  }
  const packageJson = readJson("apps/memory-atlas/package.json");
  const output = readJson(decisionDebtOutputPath);
  assertCondition(
    packageJson.scripts?.["validate:v1.2-s09-p3"] === "node scripts/validate_memory_atlas_v1_2_s09_p3.cjs" &&
      output.task_id === "MA-V12-S09P3" &&
      output.acceptance_id === "ACC-MA-V12-S09P3" &&
      output.status === "phase_s09_p3_decision_debt_completed_pending_s09_review" &&
      output.phase_boundary?.next_phase === "S09 Review",
    "s09_review_previous_s09p3_artifacts",
    "S09 P3 persisted artifacts and validator registration are present before accepting S09 Review on a clean tree",
    "S09 P3 persisted artifacts are incomplete",
    {
      script: packageJson.scripts?.["validate:v1.2-s09-p3"],
      task_id: output.task_id,
      acceptance_id: output.acceptance_id,
      status: output.status,
      next_phase: output.phase_boundary?.next_phase,
    },
  );
}

function validateLatentSignals() {
  [latentConfigPath, latentOutputPath, "docs/reviews/memory_atlas_v1_2_s09_p1_latent_signals.md", "人类可读/21_潜性信号说明.md"].forEach(validateTextFile);
  const config = readJson(latentConfigPath);
  const output = readJson(latentOutputPath);
  const badSignals = [];
  for (const signal of output.latent_signals || []) {
    if (!Array.isArray(signal.supporting_evidence_refs) || signal.supporting_evidence_refs.length === 0) badSignals.push(`${signal.signal_id}:missing_supporting_evidence`);
    if (!Array.isArray(signal.contradicting_evidence_refs) || signal.contradicting_evidence_refs.length === 0) badSignals.push(`${signal.signal_id}:missing_contradicting_evidence`);
    if (!signal.alternative_explanation_zh || !hasCjk(signal.alternative_explanation_zh)) badSignals.push(`${signal.signal_id}:missing_alternative_explanation`);
    if (!["A", "B", "C", "D"].includes(signal.evidence_strength_badge)) badSignals.push(`${signal.signal_id}:invalid_badge`);
    if (signal.not_psychological_diagnosis !== true || signal.not_personality_label !== true) badSignals.push(`${signal.signal_id}:safety_boundary_missing`);
    if (signal.falsifiable !== true || !signal.next_validation_zh) badSignals.push(`${signal.signal_id}:missing_next_validation`);
  }
  assertCondition(
    config.task_id === "MA-V12-S09P1" &&
      config.acceptance_id === "ACC-MA-V12-S09P1" &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.psychological_diagnosis === false &&
      config.scope_boundary?.personality_label === false &&
      output.task_id === "MA-V12-S09P1" &&
      output.acceptance_id === "ACC-MA-V12-S09P1" &&
      output.status === "phase_s09_p1_latent_signals_completed_pending_s09_p2" &&
      output.signal_count >= 4 &&
      (output.safety_audit?.bad_items || []).length === 0 &&
      output.phase_boundary?.does_not_modify_raw === true &&
      output.phase_boundary?.does_not_output_psychological_diagnosis === true &&
      output.phase_boundary?.does_not_output_personality_label === true &&
      badSignals.length === 0,
    "s09_review_latent_signals",
    "S09 P1 latent signals retain evidence, counter-evidence, badges, next validation and safety boundaries",
    "S09 P1 latent signals failed S09 Review",
    { badSignals, signal_count: output.signal_count },
  );
}

function validateSelfIteration() {
  [selfIterationConfigPath, selfIterationOutputPath, "docs/reviews/memory_atlas_v1_2_s09_p2_self_iteration.md", "人类可读/22_自我迭代建议说明.md"].forEach(validateTextFile);
  const config = readJson(selfIterationConfigPath);
  const output = readJson(selfIterationOutputPath);
  const targets = new Set((output.self_iteration_suggestions || []).map((item) => item.target_type));
  const missingTargets = ["memory", "config", "AGENTS", "style", "personalization"].filter((target) => !targets.has(target));
  const badSuggestions = [];
  for (const item of output.self_iteration_suggestions || []) {
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badSuggestions.push(`${item.suggestion_id}:missing_evidence`);
    if (Number(item.action_half_life_days || 0) <= 0) badSuggestions.push(`${item.suggestion_id}:invalid_action_half_life`);
    if (item.not_pressure_list !== true || item.not_applied !== true) badSuggestions.push(`${item.suggestion_id}:boundary_missing`);
    const proposal = item.proposal || {};
    if (proposal.state !== "pending_human_review") badSuggestions.push(`${item.suggestion_id}:proposal_not_pending`);
    if (proposal.apply_execution_allowed !== false || proposal.raw_apply_target_allowed !== false) badSuggestions.push(`${item.suggestion_id}:proposal_apply_allowed`);
    if (!proposal.expires_at || proposal.not_permanent_pending !== true) badSuggestions.push(`${item.suggestion_id}:expiry_missing`);
  }
  assertCondition(
    config.task_id === "MA-V12-S09P2" &&
      config.acceptance_id === "ACC-MA-V12-S09P2" &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      output.task_id === "MA-V12-S09P2" &&
      output.acceptance_id === "ACC-MA-V12-S09P2" &&
      output.status === "phase_s09_p2_self_iteration_completed_pending_s09_p3" &&
      output.suggestion_count >= 5 &&
      missingTargets.length === 0 &&
      output.proposal_expiry_summary?.all_proposals_have_expiry === true &&
      output.proposal_expiry_summary?.all_suggestions_have_action_half_life === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      badSuggestions.length === 0,
    "s09_review_self_iteration",
    "S09 P2 self-iteration suggestions cover required targets with proposal expiry, half-life and no-apply boundaries",
    "S09 P2 self-iteration suggestions failed S09 Review",
    { missingTargets, badSuggestions, suggestion_count: output.suggestion_count },
  );
}

function validateDecisionDebt() {
  [decisionDebtConfigPath, decisionDebtOutputPath, "docs/reviews/memory_atlas_v1_2_s09_p3_decision_debt.md", "人类可读/23_决策债说明.md"].forEach(validateTextFile);
  const config = readJson(decisionDebtConfigPath);
  const output = readJson(decisionDebtOutputPath);
  const badItems = [];
  for (const item of output.decision_debt_ledger || []) {
    if (!Array.isArray(item.evidence_refs) || item.evidence_refs.length === 0) badItems.push(`${item.decision_debt_id}:missing_evidence`);
    if (!Array.isArray(item.linked_self_iteration_suggestion_ids) || item.linked_self_iteration_suggestion_ids.length === 0) badItems.push(`${item.decision_debt_id}:missing_linked_suggestion`);
    const step = item.minimal_next_step || {};
    if (!step.step_zh || !step.expected_artifact_zh || !step.stop_condition_zh) badItems.push(`${item.decision_debt_id}:missing_minimal_next_step`);
    if (Number(step.effort_minutes_max || 0) <= 0) badItems.push(`${item.decision_debt_id}:invalid_effort`);
    if (item.not_pressure_list !== true || item.not_applied !== true) badItems.push(`${item.decision_debt_id}:boundary_missing`);
  }
  assertCondition(
    config.task_id === "MA-V12-S09P3" &&
      config.acceptance_id === "ACC-MA-V12-S09P3" &&
      config.ledger_policy?.pressure_list_allowed === false &&
      config.scope_boundary?.raw_mutation === false &&
      config.scope_boundary?.proposal_apply_execution === false &&
      output.task_id === "MA-V12-S09P3" &&
      output.acceptance_id === "ACC-MA-V12-S09P3" &&
      output.status === "phase_s09_p3_decision_debt_completed_pending_s09_review" &&
      output.decision_debt_count >= Number(config.ledger_policy?.min_entries || 3) &&
      output.safety_summary?.all_items_have_minimal_next_step === true &&
      output.safety_summary?.pressure_list_created === false &&
      output.safety_summary?.proposal_apply_execution === false &&
      output.safety_summary?.raw_mutation === false &&
      output.phase_boundary?.does_not_generate_pressure_list === true &&
      output.phase_boundary?.does_not_apply_proposals === true &&
      output.phase_boundary?.does_not_modify_raw === true &&
      badItems.length === 0,
    "s09_review_decision_debt",
    "S09 P3 decision debt ledger keeps minimal next steps, no pressure list and no-apply boundaries",
    "S09 P3 decision debt ledger failed S09 Review",
    { badItems, decision_debt_count: output.decision_debt_count },
  );
}

function validateAtlasctlGates() {
  const python = process.env.PYTHON || "python3";
  const latent = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "analyze", "--stage", "latent", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const selfIteration = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "analyze", "--stage", "self-iteration", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const decisionDebt = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "analyze", "--stage", "decision-debt", "--dry-run"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const latentAudit = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "audit", "--check", "latent-safety"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const selfIterationAudit = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "audit", "--check", "self-iteration-safety"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  const decisionDebtAudit = parseJsonFromStdout(run(python, ["scripts/atlasctl.py", "audit", "--check", "decision-debt-safety"], {
    cwd: repoRoot,
    timeout: 300000,
  }));
  assertCondition(
    latent.task_id === "MA-V12-S09P1" &&
      selfIteration.task_id === "MA-V12-S09P2" &&
      decisionDebt.task_id === "MA-V12-S09P3" &&
      latent.writes_files === false &&
      selfIteration.writes_files === false &&
      decisionDebt.writes_files === false &&
      latentAudit.status === "PASS" &&
      selfIterationAudit.status === "PASS" &&
      decisionDebtAudit.status === "PASS" &&
      (latentAudit.bad_items || []).length === 0 &&
      (selfIterationAudit.bad_items || []).length === 0 &&
      (decisionDebtAudit.bad_items || []).length === 0,
    "s09_review_atlasctl_gates",
    "atlasctl S09 analyze dry-runs and latent/self-iteration/decision-debt safety audits pass",
    "atlasctl S09 gates failed Review",
    { latentAudit, selfIterationAudit, decisionDebtAudit },
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
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
      validatorName,
      latentOutputPath,
      selfIterationOutputPath,
      decisionDebtOutputPath,
      "No GitHub main upload in this phase",
      "pending S10 P1",
    ]),
    "s09_review_artifact",
    "S09 Review artifact records stage acceptance, S09 P1/P2/P3 outputs and no-upload boundary",
    "S09 Review artifact is incomplete",
  );
  assertCondition(
    hasAll(quick, ["当前阶段是 S09 Review", taskId, acceptanceId, status, "下一步只允许进入 S10 P1"]),
    "s09_review_quick_entry",
    "Quick entry has advanced to S09 Review and pending S10 P1",
    "Quick entry is missing S09 Review current state",
  );
  assertCondition(
    hasAll(overview, ["S09 Review 已完成", "latent_signals.json", "self_iteration_suggestions.json", "decision_debt_ledger.json", "下一步是 S10 P1"]),
    "s09_review_overview",
    "Overview records S09 Review completion and pending S10 P1",
    "Overview is missing S09 Review current state",
  );
  assertCondition(
    hasAll(machine, ["当前为 S09 Review", taskId, acceptanceId, validatorName, "下一步是 S10 P1"]),
    "s09_review_machine_readme",
    "Machine README records S09 Review current state",
    "Machine README is missing S09 Review current state",
  );
  assertCondition(
    hasAll(dataContract, ["当前 S09 Review 已完成", latentOutputPath, selfIterationOutputPath, decisionDebtOutputPath, "下一步是 S10 P1"]),
    "s09_review_data_contract",
    "Data contract README records S09 Review outputs",
    "Data contract README is missing S09 Review outputs",
  );
  assertCondition(
    hasAll(behavior, ["当前 S09 Review 已完成", latentConfigPath, selfIterationConfigPath, decisionDebtConfigPath, "下一步是 S10 P1"]),
    "s09_review_behavior_readme",
    "Behavior model README records S09 Review model outputs",
    "Behavior model README is missing S09 Review model outputs",
  );
  assertCondition(
    hasAll(runGate, ["当前阶段是 S09 Review", taskId, acceptanceId, validatorName, "下一步是 S10 P1"]),
    "s09_review_run_gate",
    "Run gate README records S09 Review validator and next gate",
    "Run gate README is missing S09 Review gate",
  );
  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S09 Review", "pending S10 P1", "No GitHub main upload in this phase"]),
      `s09_review_records_${name}`,
      `${name} records S09 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S09 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s09_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );
  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s09_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S09 Review branch",
    { branch, branchName },
  );
  const remoteDevOrigin = spawnSync("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    encoding: "utf8",
    stdio: "pipe",
    timeout: 30000,
  });
  const githubHttpsRemote = "https://github.com/LinzeColin/CodexProject.git";
  const remoteDev =
    remoteDevOrigin.status === 0
      ? {
          method: "origin",
          status: remoteDevOrigin.status,
          stdout: remoteDevOrigin.stdout.trim(),
          stderr: remoteDevOrigin.stderr.trim(),
        }
      : (() => {
          const fallback = spawnSync("git", ["ls-remote", "--heads", githubHttpsRemote, branchName], {
            cwd: worktreeRoot,
            encoding: "utf8",
            stdio: "pipe",
            timeout: 30000,
          });
          return {
            method: "https_fallback",
            status: fallback.status,
            stdout: fallback.stdout.trim(),
            stderr: fallback.stderr.trim(),
            origin_status: remoteDevOrigin.status,
            origin_stderr: remoteDevOrigin.stderr.trim(),
          };
        })();
  assertCondition(
    remoteDev.status === 0 && remoteDev.stdout === "",
    "s09_review_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists or remote branch check failed",
    { branchName, remoteDev },
  );
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s09_review_open_diff_scope",
    "Open diff is limited to S09 Review files",
    "Open diff contains files outside S09 Review allowed scope",
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
    "s09_review_no_raw_or_secret_open_changes",
    "S09 Review open diff does not modify raw or secret/config files",
    "S09 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges, publicRawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateLatentSignals();
    validateSelfIteration();
    validateDecisionDebt();
    validateAtlasctlGates();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s09_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s09_review",
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
