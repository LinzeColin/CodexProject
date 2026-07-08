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

const taskId = "MA-V12-S04P3";
const acceptanceId = "ACC-MA-V12-S04P3";
const status = "phase_s04_p3_github_backup_completed_pending_s04_review";
const validatorName = "validate:v1.2-s04-p3";
const scriptName = "validate_memory_atlas_v1_2_s04_p3.cjs";
const backupScript = "scripts/github_backup.py";
const atlasctlScript = "scripts/atlasctl.py";
const policyPath = "机器治理/同步与备份/github_backup_policy.v1_2_s04_p3.json";
const humanPagePath = "人类可读/11_GitHub备份DryRun与Apply.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s04_p3_github_backup.md";
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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${backupScript}`,
  `OpenAIDatabase/${atlasctlScript}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/tests/test_s04p3_github_backup.py",
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

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  return JSON.parse(stdout.slice(stdout.indexOf("{")));
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
    "s04p3_package_script",
    "package.json exposes the v1.2 S04 P3 validator",
    "package.json is missing the v1.2 S04 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s04p3_previous_phase_deferred_scope",
      "S04 P2 execution is deferred only because open diff is limited to S04 P3 files and validator-chain compatibility files",
      "S04 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s04p3_previous_phase_deferred_until_clean_tree", "S04 P2 validator will run on a clean tree after S04 P3 compatibility commit", { changed });
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s04_p2.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S04P2",
    "s04p3_previous_s04p2",
    "S04 P2 validator returns PASS before accepting S04 P3",
    "S04 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validatePolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));
  assertCondition(
    policy.task_id === taskId && policy.acceptance_id === acceptanceId && policy.status === status,
    "s04p3_policy_identity",
    "GitHub backup policy records S04 P3 identity and status",
    "GitHub backup policy identity is incomplete",
    { task_id: policy.task_id, acceptance_id: policy.acceptance_id, status: policy.status },
  );
  assertCondition(
    ["data/public_raw", "data/derived", "data/run_logs", "docs/reviews", "reports"].every((target) =>
      policy.backup_targets?.includes(target),
    ) &&
      policy.command_contracts?.dry_run?.writes_files === false &&
      policy.command_contracts?.apply?.commits_locally === true &&
      policy.command_contracts?.apply?.pushes_remote === false &&
      policy.failure_contract?.chinese_reason_required === true &&
      policy.failure_contract?.fallback_suggestion_required === true,
    "s04p3_backup_contract",
    "Policy defines backup targets, dry-run/apply contracts, Chinese fallback and no remote push",
    "GitHub backup policy contract is incomplete",
    policy,
  );
  assertCondition(
    policy.phase_boundary?.does_not_push_github_main === true &&
      policy.phase_boundary?.does_not_reinstall_app === true &&
      policy.phase_boundary?.does_not_modify_chatgpt_state === true &&
      policy.phase_boundary?.next_gate === "S04 Review",
    "s04p3_phase_boundary",
    "Policy keeps S04 P3 bounded to local backup and pending S04 Review",
    "S04 P3 phase boundary is incomplete",
    policy.phase_boundary,
  );
}

function validateRuntime() {
  [backupScript, atlasctlScript].forEach(validateTextFile);
  const backupSource = readRepoFile(backupScript);
  const atlasctlSource = readRepoFile(atlasctlScript);
  assertCondition(
    hasAll(backupSource, [
      "BACKUP_TARGETS",
      "data/public_raw",
      "data/derived",
      "data/run_logs",
      "docs/reviews",
      "reports",
      "remote_push",
      "中文原因",
      "fallback建议",
      "not_git_worktree",
    ]),
    "s04p3_backup_runtime_surface",
    "github_backup.py exposes backup targets, no-remote contract and Chinese fallback",
    "github_backup.py runtime surface is incomplete",
  );
  assertCondition(
    hasAll(atlasctlSource, ["push", "github_backup.py", "--dry-run", "--apply", "--message"]),
    "s04p3_atlasctl_push_surface",
    "atlasctl exposes push dry-run/apply surface",
    "atlasctl push surface is incomplete",
  );
}

function validateCommands() {
  const tests = run("python", ["-B", "-m", "unittest", "OpenAIDatabase.tests.test_s04p3_github_backup", "-q"], {
    cwd: worktreeRoot,
    timeout: 120000,
  });
  assertCondition(
    tests.stderr.includes("OK"),
    "s04p3_unit_tests",
    "S04 P3 GitHub backup unit tests pass",
    "S04 P3 unit tests did not report OK",
    { stdout: tests.stdout, stderr: tests.stderr },
  );

  const dryRun = parseJsonFromStdout(run("python3", [atlasctlScript, "push", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    dryRun.status === "PASS" &&
      dryRun.command === "push" &&
      dryRun.dry_run === true &&
      dryRun.writes_files === false &&
      dryRun.remote_push === false &&
      ["data/public_raw", "data/derived", "data/run_logs", "docs/reviews", "reports"].every((target) =>
        dryRun.backup_targets?.includes(target),
      ),
    "s04p3_atlasctl_push_dry_run",
    "atlasctl push --dry-run returns a no-write backup contract",
    "atlasctl push --dry-run contract failed",
    dryRun,
  );
}

function validateDocsAndRecords() {
  [
    humanPagePath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/运行门禁/README.md",
    reviewPath,
    ...recordFiles,
  ].forEach(validateTextFile);

  const human = readRepoFile(humanPagePath);
  assertCondition(
    hasAll(human, [
      taskId,
      acceptanceId,
      status,
      "python scripts/atlasctl.py push --dry-run",
      "python scripts/atlasctl.py push --apply",
      "No GitHub main upload in this phase",
      "不执行远端 push",
      "S04 Review",
    ]),
    "s04p3_human_page",
    "Human S04 P3 page explains backup commands, scope, boundaries and next gate",
    "Human S04 P3 page is incomplete",
  );

  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");
  const currentStateIsS04Review =
    hasAll(quick, [
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
  const currentStateIsS05P1 =
    hasAll(quick, [
      "当前阶段是 S05 P1",
      "MA-V12-S05P1",
      "ACC-MA-V12-S05P1",
      "下一步只允许进入 S05 P2",
    ]) &&
    hasAll(overview, [
      "S05 P1 已完成",
      "Facet schema",
      "下一步是 S05 P2",
    ]) &&
    hasAll(machineReadme, [
      "当前为 S05 P1",
      "facet_event_schema.v1_2_s05_p1.json",
      "下一步是 S05 P2",
    ]) &&
    hasAll(runGateReadme, [
      "当前阶段是 S05 P1",
      "MA-V12-S05P1",
      "ACC-MA-V12-S05P1",
      "validate:v1.2-s05-p1",
    ]);
  assertCondition(
    currentStateIsS04Review ||
      currentStateIsS05P1 ||
      hasAll(quick, [taskId, acceptanceId, status, "S04 P3 已建立", "下一步只允许进入 S04 Review"]),
    "s04p3_quick_entry",
    "Human quick entry records S04 P3 state or a later S04 Review state",
    "Human quick entry is missing S04 P3 or S04 Review state",
  );
  assertCondition(
    currentStateIsS04Review || currentStateIsS05P1 || hasAll(overview, ["S04 P3 已完成", "scripts/github_backup.py", "下一步是 S04 Review"]),
    "s04p3_overview",
    "Human overview records S04 P3 state or a later S04 Review state",
    "Human overview is missing S04 P3 or S04 Review state",
  );

  const machine = [
    machineReadme,
    syncReadme,
    runGateReadme,
  ].join("\n");
  assertCondition(
    hasAll(machine, [taskId, acceptanceId, validatorName, "github_backup_policy.v1_2_s04_p3.json", "github_backup.py"]),
    "s04p3_machine_readmes",
    "Machine READMEs record S04 P3 policy, runtime and validator",
    "Machine READMEs are missing S04 P3 state",
  );

  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [taskId, acceptanceId, status, "No GitHub main upload in this phase", "No remote push in this phase", "S04 Review"]),
    "s04p3_review_artifact",
    "Review artifact records S04 P3 acceptance, boundaries and next gate",
    "Review artifact is incomplete",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S04 P3", "No GitHub main upload in this phase", "No remote push in this phase", "pending S04 Review"]),
      `s04p3_records_${name}`,
      `${name} records S04 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S04 P3 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s04p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s04p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S04 P3 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s04p3_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists unexpectedly",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s04p3_open_diff_scope",
    "Open diff is limited to S04 P3 GitHub backup files and validator-chain compatibility files",
    "Open diff contains files outside S04 P3 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  const forbiddenOpenChanges = changed.filter((file) =>
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    file.includes(".env") ||
    file.includes("cookies") ||
    file.includes("session_token"),
  );
  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s04p3_no_real_raw_or_secret_open_changes",
    "S04 P3 open diff does not modify real raw data or secret/config files",
    "S04 P3 open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validatePolicy();
    validateRuntime();
    validateCommands();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s04_p3", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s04_p3",
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
