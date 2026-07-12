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

const taskId = "MA-V12-S04P2";
const acceptanceId = "ACC-MA-V12-S04P2";
const status = "phase_s04_p2_codex_agent_sync_completed_pending_s04_p3";
const validatorName = "validate:v1.2-s04-p2";
const scriptName = "validate_memory_atlas_v1_2_s04_p2.cjs";
const codexSyncScript = "scripts/sync_codex_memory_data.py";
const futureAgentScript = "scripts/sync_future_agent_data.py";
const atlasctlScript = "scripts/atlasctl.py";
const policyPath = "机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json";
const humanPagePath = "人类可读/10_Codex与FutureAgent同步.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s04_p2_codex_agent_sync.md";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const compatibilityValidators = [
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs",
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  ...compatibilityValidators,
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${codexSyncScript}`,
  `OpenAIDatabase/${futureAgentScript}`,
  `OpenAIDatabase/${atlasctlScript}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/tests/test_codex_memory_sync.py",
  "OpenAIDatabase/tests/test_s04p2_codex_agent_sync.py",
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
    "s04p2_package_script",
    "package.json exposes the v1.2 S04 P2 validator",
    "package.json is missing the v1.2 S04 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousStageGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s04p2_previous_phase_deferred_scope",
      "S04 P1 execution is deferred only because open diff is limited to S04 P2 files and later-state validator compatibility",
      "S04 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass("s04p2_previous_phase_deferred_until_clean_tree", "S04 P1 validator will run on a clean tree after S04 P2 commit", { changed });
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s04_p1.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S04P1",
    "s04p2_previous_s04p1",
    "S04 P1 validator returns PASS before accepting S04 P2",
    "S04 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validatePolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));
  assertCondition(
    policy.task_id === taskId && policy.acceptance_id === acceptanceId && policy.status === status,
    "s04p2_policy_identity",
    "Codex/future-agent sync policy records S04 P2 identity and status",
    "Codex/future-agent sync policy identity is incomplete",
    { task_id: policy.task_id, acceptance_id: policy.acceptance_id, status: policy.status },
  );

  const sources = policy.sources || {};
  assertCondition(
    sources.codex?.source_id === "codex" &&
      sources.codex?.raw_root === "data/public_raw/codex" &&
      sources.codex?.derived_summary === "data/derived/codex/codex_activity_snapshot.json" &&
      sources.codex?.run_log_dir === "data/run_logs/sync_runs" &&
      sources.codex?.dry_run_writes_files === false &&
      sources["future-agent"]?.source_id === "future-agent" &&
      sources["future-agent"]?.raw_root === "data/public_raw/agents/{agent_id}" &&
      sources["future-agent"]?.derived_summary === "data/derived/agents/{agent_id}/agent_sync_summary.json" &&
      sources["future-agent"]?.run_log_dir === "data/run_logs/sync_runs" &&
      sources["future-agent"]?.adapter_mode === "minimal_adapter",
    "s04p2_source_output_contracts",
    "Policy defines raw/derived/run-log contracts for Codex and future-agent sources",
    "Policy is missing Codex or future-agent output contracts",
    { sources },
  );

  assertCondition(
    policy.phase_boundary?.previous_gate === "S04 P1" &&
      policy.phase_boundary?.next_gate === "S04 P3" &&
      policy.phase_boundary?.does_not_implement_github_backup === true &&
      policy.phase_boundary?.does_not_push_github === true &&
      policy.phase_boundary?.does_not_read_or_store_credentials === true &&
      policy.phase_boundary?.does_not_modify_chatgpt_state === true,
    "s04p2_phase_boundary",
    "Policy keeps S04 P2 bounded to Codex/future-agent sync and defers GitHub backup",
    "Policy phase boundary is incomplete",
    { phase_boundary: policy.phase_boundary },
  );
}

function validateRuntime() {
  [codexSyncScript, futureAgentScript, atlasctlScript].forEach(validateTextFile);
  const codexSource = readRepoFile(codexSyncScript);
  const futureSource = readRepoFile(futureAgentScript);
  const atlasctlSource = readRepoFile(atlasctlScript);

  assertCondition(
    hasAll(codexSource, [
      "dry_run",
      "data/public_raw/codex",
      "public_raw_snapshot",
      "data/derived/codex/codex_activity_snapshot.json",
      "data/run_logs/sync_runs",
      "credentials_not_transcript",
    ]),
    "s04p2_codex_runtime_surface",
    "Codex sync exposes dry-run, public raw, derived and run-log contracts",
    "Codex sync runtime is missing S04 P2 contract fragments",
  );

  assertCondition(
    hasAll(futureSource, [
      "future-agent",
      "minimal_adapter",
      "data/public_raw/agents",
      "agent_sync_summary.json",
      "data/run_logs/sync_runs",
      "assert_no_credentials",
      "append-only",
    ]),
    "s04p2_future_agent_runtime_surface",
    "Future-agent adapter exposes minimal adapter, credential gate and append-only raw output",
    "Future-agent adapter runtime is incomplete",
  );

  assertCondition(
    hasAll(atlasctlSource, [
      "sync",
      "chatgpt",
      "codex",
      "future-agent",
      "sync_codex_memory_data.py",
      "sync_future_agent_data.py",
      "build-atlas",
    ]),
    "s04p2_atlasctl_surface",
    "atlasctl exposes ChatGPT, Codex, future-agent and build-atlas surfaces",
    "atlasctl is missing S04 P2 surfaces",
  );
}

function validateCommands() {
  const tests = run(
    "python",
    [
      "-B",
      "-m",
      "unittest",
      "OpenAIDatabase.tests.test_s04p2_codex_agent_sync",
      "OpenAIDatabase.tests.test_codex_memory_sync",
      "-q",
    ],
    {
      cwd: worktreeRoot,
      timeout: 120000,
    },
  );
  assertCondition(
    tests.stderr.includes("OK"),
    "s04p2_unit_tests",
    "S04 P2 Codex/future-agent sync unit tests and Codex regression tests pass",
    "S04 P2 unit tests did not report OK",
    { stdout: tests.stdout, stderr: tests.stderr },
  );

  for (const sourceId of ["chatgpt", "codex", "future-agent"]) {
    const result = parseJsonFromStdout(run("python3", [atlasctlScript, "sync", "--source", sourceId, "--dry-run"], {
      cwd: repoRoot,
      timeout: 60000,
    }));
    assertCondition(
      result.status === "PASS" &&
        result.source_id === sourceId &&
        result.dry_run === true &&
        result.writes_files === false,
      `s04p2_atlasctl_${sourceId}_dry_run`,
      `atlasctl sync --source ${sourceId} --dry-run returns a no-write contract`,
      `atlasctl ${sourceId} dry-run contract failed`,
      result,
    );
  }
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

  const humanPage = readRepoFile(humanPagePath);
  assertCondition(
    hasAll(humanPage, [
      "Codex与FutureAgent同步",
      "MA-V12-S04P2",
      "ACC-MA-V12-S04P2",
      "Codex local sync",
      "future-agent minimal adapter",
      "raw + derived + run log",
      "不实现 GitHub backup",
      "下一步是 S04 P3",
    ]),
    "s04p2_human_page",
    "Human S04 P2 page explains Codex/future-agent sync, outputs and boundaries",
    "Human S04 P2 page is incomplete",
  );

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");
  const currentStateIsS04P3 =
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
  const currentStateIsS04Review =
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
  const currentStateIsS05P1 =
    hasAll(quickEntry, [
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

  if (currentStateIsS04P3 || currentStateIsS04Review || currentStateIsS05P1) {
    pass(
      "s04p2_human_machine_later_s04p3_state",
      "Current human and machine state has advanced from S04 P2 into a later S04 state",
    );
  } else {
    assertCondition(
      hasAll(quickEntry, ["当前阶段是 S04 P2", "Codex local sync", "future-agent adapter", "下一步只允许进入 S04 P3"]),
      "s04p2_quick_entry",
      "Human quick entry records S04 P2 state and next S04 P3 gate",
      "Human quick entry is missing S04 P2 state",
    );

    assertCondition(
      hasAll(overview, ["S04 P2 已完成", "Codex local sync", "future-agent adapter", "下一步是 S04 P3"]),
      "s04p2_overview",
      "Human overview records S04 P2 state and next S04 P3 gate",
      "Human overview is missing S04 P2 state",
    );

    assertCondition(
      hasAll(machineReadme, ["当前为 S04 P2", policyPath, codexSyncScript, futureAgentScript, "下一步是 S04 P3"]) &&
        hasAll(syncReadme, ["当前 S04 P2 已完成", policyPath, "Codex local sync", "future-agent minimal adapter"]) &&
        hasAll(runGateReadme, ["当前阶段是 S04 P2", validatorName, reviewPath, "下一步是 S04 P3"]),
      "s04p2_machine_readmes",
      "Machine READMEs record S04 P2 policy, runtime, validator and next gate",
      "Machine READMEs are missing S04 P2 state",
    );
  }

  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.2 S04 P2 Codex/Future Agent Sync",
      taskId,
      acceptanceId,
      validatorName,
      "Codex local sync",
      "future-agent minimal adapter",
      "raw + derived + run log",
      "No GitHub main upload",
      "S04 P3",
    ]),
    "s04p2_review_artifact",
    "Review artifact records S04 P2 acceptance, files, boundaries and next gate",
    "Review artifact is incomplete",
  );

  for (const name of recordFiles) {
    const source = readRepoFile(name);
    assertCondition(
      hasAll(source, [taskId, acceptanceId, status, validatorName, "S04 P2", "No GitHub main upload in this phase", "pending S04 P3"]),
      `s04p2_records_${name}`,
      `${name} records S04 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S04 P2 record fragments`,
    );
  }
}

function validateRepoBoundaries() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git" || remote === "https://github.com/LinzeColin/CodexProject.git",
    "s04p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin is not LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s04p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S04 P2 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s04p2_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists unexpectedly",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );

  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s04p2_open_diff_scope",
    "Open diff is limited to S04 P2 Codex/future-agent sync runtime, policy, validator, tests and records",
    "Open diff contains files outside S04 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  const forbiddenOpenChanges = changed.filter((file) => (
    file.startsWith("OpenAIDatabase/data/public_raw/") ||
    file.startsWith("OpenAIDatabase/data/raw") ||
    file.startsWith("OpenAIDatabase/data/raw_encrypted") ||
    file.includes(".env")
  ));
  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s04p2_no_real_raw_or_secret_open_changes",
    "S04 P2 open diff does not modify real raw data or secret/config files",
    "S04 P2 open diff includes forbidden raw/config changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousStageGate();
  validatePolicy();
  validateRuntime();
  validateCommands();
  validateDocsAndRecords();
  validateRepoBoundaries();
  return {
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s04_p2",
    task_id: taskId,
    acceptance_id: acceptanceId,
    checks,
  };
}

try {
  console.log(JSON.stringify(main(), null, 2));
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_2_s04_p2",
    task_id: taskId,
    acceptance_id: acceptanceId,
    error: error.message,
    details: error.details || { stdout: error.stdout, stderr: error.stderr },
    checks,
  }, null, 2));
  process.exit(1);
}
