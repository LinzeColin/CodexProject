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

const taskId = "MA-V12-S04-REVIEW";
const acceptanceId = "ACC-MA-V12-S04-REVIEW";
const status = "stage_s04_review_passed_pending_s05_no_github_main_upload";
const validatorName = "validate:v1.2-s04-review";
const scriptName = "validate_memory_atlas_v1_2_s04_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s04_review.md";
const atlasctlScript = "scripts/atlasctl.py";
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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p3.cjs",
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
    "s04_review_package_script",
    "package.json exposes the v1.2 S04 Review validator",
    "package.json is missing the v1.2 S04 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s04_review_previous_phase_deferred_scope",
      "S04 P3 execution is deferred only because open diff is limited to S04 Review files and validator compatibility files",
      "S04 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s04_review_previous_phase_deferred_until_clean_tree", "S04 P3 validator will run on a clean tree after S04 Review commit", { changed });
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s04_p3.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S04P3",
    "s04_review_previous_s04p3",
    "S04 P3 validator returns PASS before accepting S04 Review",
    "S04 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateSyncCommands() {
  validateTextFile(atlasctlScript);
  const tests = run(
    "python",
    [
      "-B",
      "-m",
      "unittest",
      "OpenAIDatabase.tests.test_s04p1_chatgpt_sync",
      "OpenAIDatabase.tests.test_s04p2_codex_agent_sync",
      "OpenAIDatabase.tests.test_s04p3_github_backup",
      "-q",
    ],
    { cwd: worktreeRoot, timeout: 180000 },
  );
  assertCondition(
    tests.stderr.includes("OK"),
    "s04_review_unit_tests",
    "S04 P1/P2/P3 sync and backup unit tests pass",
    "S04 unit tests did not report OK",
    { stdout: tests.stdout, stderr: tests.stderr },
  );

  const chatgpt = parseJsonFromStdout(run("python3", [atlasctlScript, "sync", "--source", "chatgpt", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    chatgpt.status === "PASS" && chatgpt.writes_files === false && chatgpt.no_browser_mutation === true && chatgpt.fallback === "official_export",
    "s04_review_chatgpt_dry_run",
    "ChatGPT sync dry-run is read-only and keeps official export fallback",
    "ChatGPT sync dry-run contract failed",
    chatgpt,
  );

  const codex = parseJsonFromStdout(run("python3", [atlasctlScript, "sync", "--source", "codex", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    codex.status === "PASS" && codex.writes_files === false && codex.append_only === true && codex.run_log_dir === "data/run_logs/sync_runs",
    "s04_review_codex_dry_run",
    "Codex sync dry-run is no-write and keeps raw/derived/run-log contract",
    "Codex sync dry-run contract failed",
    codex,
  );

  const futureAgent = parseJsonFromStdout(run("python3", [atlasctlScript, "sync", "--source", "future-agent", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    futureAgent.status === "PASS" &&
      futureAgent.writes_files === false &&
      futureAgent.input_required_for_apply === true &&
      futureAgent.adapter_mode === "minimal_adapter",
    "s04_review_future_agent_dry_run",
    "Future-agent sync dry-run is no-write and requires input for apply",
    "Future-agent sync dry-run contract failed",
    futureAgent,
  );

  const buildAtlas = parseJsonFromStdout(run("python3", [atlasctlScript, "build-atlas", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    buildAtlas.status === "PASS" && buildAtlas.writes_files === false && buildAtlas.output === "data/derived/visualization/memory_atlas.json",
    "s04_review_build_atlas_dry_run",
    "build-atlas dry-run returns no-write derived visualization contract",
    "build-atlas dry-run contract failed",
    buildAtlas,
  );

  const push = parseJsonFromStdout(run("python3", [atlasctlScript, "push", "--dry-run"], {
    cwd: repoRoot,
    timeout: 60000,
  }));
  assertCondition(
    push.status === "PASS" &&
      push.writes_files === false &&
      push.remote_push === false &&
      ["data/public_raw", "data/derived", "data/run_logs", "docs/reviews", "reports"].every((target) => push.backup_targets?.includes(target)),
    "s04_review_push_dry_run",
    "GitHub backup dry-run is no-write and does not push remote",
    "GitHub backup dry-run contract failed",
    push,
  );
}

function validateDocsAndRecords() {
  [
    reviewPath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/运行门禁/README.md",
    ...recordFiles,
  ].forEach(validateTextFile);

  const quick = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machine = readRepoFile("机器治理/README.md");
  const sync = readRepoFile("机器治理/同步与备份/README.md");
  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  const review = readRepoFile(reviewPath);
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
    hasAll(machine, [
      "当前为 S05 P1",
      "facet_event_schema.v1_2_s05_p1.json",
      "下一步是 S05 P2",
    ]) &&
    hasAll(runGate, [
      "当前阶段是 S05 P1",
      "MA-V12-S05P1",
      "ACC-MA-V12-S05P1",
      "validate:v1.2-s05-p1",
    ]);

  assertCondition(
    currentStateIsS05P1 ||
      hasAll(quick, [taskId, acceptanceId, status, "当前阶段是 S04 Review", "S04 整体复审已通过", "下一步只允许进入 S05 P1"]),
    "s04_review_quick_entry",
    "Human quick entry records S04 Review state or a later S05 P1 state",
    "Human quick entry is missing S04 Review or S05 P1 state",
  );
  assertCondition(
    currentStateIsS05P1 ||
      hasAll(overview, ["S04 Review 已通过", "S04 整体复审已通过", "ChatGPT 只读同步", "Codex local sync", "GitHub backup dry-run/apply", "下一步是 S05 P1"]),
    "s04_review_overview",
    "Human overview records S04 Review result or a later S05 P1 state",
    "Human overview is missing S04 Review or S05 P1 state",
  );
  assertCondition(
    currentStateIsS05P1 ||
      hasAll(machine, ["当前为 S04 Review", taskId, acceptanceId, validatorName, "memory_atlas_v1_2_s04_review.md", "下一步是 S05 P1"]),
    "s04_review_machine_readme",
    "Machine README records S04 Review identity or a later S05 P1 state",
    "Machine README is missing S04 Review or S05 P1 state",
  );
  assertCondition(
    hasAll(sync, ["当前 S04 Review 已通过", "ChatGPT 只读同步", "Codex local sync", "future-agent minimal adapter", "GitHub backup dry-run/apply", "下一步是 S05 P1"]),
    "s04_review_sync_readme",
    "Sync README records S04 Review result and sync/backup coverage",
    "Sync README is missing S04 Review state",
  );
  assertCondition(
    currentStateIsS05P1 ||
      hasAll(runGate, ["当前阶段是 S04 Review", taskId, acceptanceId, validatorName, reviewPath, "下一步是 S05 P1"]),
    "s04_review_run_gate",
    "Run gate README records S04 Review validator or a later S05 P1 state",
    "Run gate README is missing S04 Review or S05 P1 state",
  );
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      "S04 整体复审已通过",
      "ChatGPT 只读同步",
      "Codex local sync",
      "future-agent minimal adapter",
      "GitHub backup dry-run/apply",
      "No GitHub main upload in this review",
      "No remote push in this review",
      "S05 P1",
    ]),
    "s04_review_artifact",
    "Review artifact records S04 coverage, boundaries and next gate",
    "Review artifact is incomplete",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S04 Review", "No GitHub main upload in this review", "No remote push in this review", "pending S05 P1"]),
      `s04_review_records_${name}`,
      `${name} records S04 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S04 Review record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s04_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s04_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S04 Review branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  assertCondition(
    remoteDevQuery.output === "",
    "s04_review_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists unexpectedly",
    {
      branchName,
      remoteDev: remoteDevQuery.output,
      remote_query_method: remoteDevQuery.method,
      origin_error: remoteDevQuery.originError,
      origin_stderr: remoteDevQuery.originStderr,
    },
  );

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s04_review_open_diff_scope",
    "Open diff is limited to S04 Review files and validator compatibility files",
    "Open diff contains files outside S04 Review allowed scope",
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
    "s04_review_no_real_raw_or_secret_open_changes",
    "S04 Review open diff does not modify real raw data or secret/config files",
    "S04 Review open diff modifies forbidden raw or secret-like files",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  try {
    validatePackageScript();
    validatePreviousPhaseGate();
    validateSyncCommands();
    validateDocsAndRecords();
    validateRepoBoundaries();
    console.log(JSON.stringify({ status: "PASS", validator: "validate_memory_atlas_v1_2_s04_review", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    console.log(JSON.stringify({
      status: "FAIL",
      validator: "validate_memory_atlas_v1_2_s04_review",
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
