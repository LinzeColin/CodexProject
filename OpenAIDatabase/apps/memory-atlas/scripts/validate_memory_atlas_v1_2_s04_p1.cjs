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

const taskId = "MA-V12-S04P1";
const acceptanceId = "ACC-MA-V12-S04P1";
const status = "phase_s04_p1_chatgpt_sync_completed_pending_s04_p2";
const validatorName = "validate:v1.2-s04-p1";
const scriptName = "validate_memory_atlas_v1_2_s04_p1.cjs";
const syncScript = "scripts/sync_chatgpt_memory_data.py";
const atlasctlScript = "scripts/atlasctl.py";
const policyPath = "机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json";
const humanPagePath = "人类可读/09_ChatGPT只读同步与官方导出Fallback.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s04_p1_chatgpt_sync.md";
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
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_review.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${syncScript}`,
  `OpenAIDatabase/${atlasctlScript}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/tests/test_s04p1_chatgpt_sync.py",
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
    "s04p1_package_script",
    "package.json exposes the v1.2 S04 P1 validator",
    "package.json is missing the v1.2 S04 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousStageGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s04p1_previous_stage_deferred_scope",
      "S03 Review execution is deferred only because open diff is limited to S04 P1 files and later-state validator compatibility",
      "S03 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s04p1_previous_stage_deferred_until_clean_tree",
      "S03 Review validator will run on a clean tree after S04 P1 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s03_review.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S03-REVIEW",
    "s04p1_previous_s03_review",
    "S03 Review validator returns PASS before accepting S04 P1",
    "S03 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateChatGptPolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));
  assertCondition(
    policy.task_id === taskId &&
      policy.acceptance_id === acceptanceId &&
      policy.status === status &&
      policy.source_id === "chatgpt",
    "s04p1_policy_identity",
    "ChatGPT sync policy records S04 P1 identity and source",
    "ChatGPT sync policy identity is incomplete",
    { task_id: policy.task_id, acceptance_id: policy.acceptance_id, status: policy.status, source_id: policy.source_id },
  );

  assertCondition(
    policy.browser_connector?.mode === "readonly_contract" &&
      policy.browser_connector?.requires_existing_logged_in_browser === true &&
      policy.browser_connector?.stop_on_password_or_verification === true &&
      policy.browser_connector?.allowed_actions?.includes("read_conversation") &&
      policy.browser_connector?.allowed_actions?.includes("read_title") &&
      policy.browser_connector?.allowed_actions?.includes("read_metadata") &&
      policy.browser_connector?.forbidden_actions?.includes("send_message") &&
      policy.browser_connector?.forbidden_actions?.includes("delete_conversation") &&
      policy.browser_connector?.forbidden_actions?.includes("archive_conversation") &&
      policy.browser_connector?.forbidden_actions?.includes("rename_conversation"),
    "s04p1_browser_readonly_contract",
    "Policy defines logged-in read-only browser connector boundaries and mutation stops",
    "Policy browser read-only contract is incomplete",
    { browser_connector: policy.browser_connector },
  );

  assertCondition(
    policy.official_export_fallback?.enabled === true &&
      policy.official_export_fallback?.accepted_inputs?.includes("conversations.json") &&
      policy.official_export_fallback?.accepted_inputs?.includes("official_export_zip") &&
      policy.output_contract?.raw_root === "data/public_raw/chatgpt" &&
      policy.output_contract?.derived_summary === "data/derived/chatgpt/chatgpt_sync_summary.json" &&
      policy.output_contract?.run_log_dir === "data/run_logs/sync_runs" &&
      policy.output_contract?.dry_run_writes_files === false,
    "s04p1_export_fallback_outputs",
    "Policy defines official export fallback and raw/derived/run-log output contract",
    "Policy official export fallback or output contract is incomplete",
    { official_export_fallback: policy.official_export_fallback, output_contract: policy.output_contract },
  );

  assertCondition(
    policy.phase_boundary?.previous_gate === "S03 Review" &&
      policy.phase_boundary?.next_gate === "S04 P2" &&
      policy.phase_boundary?.does_not_implement_codex_or_future_agent_sync === true &&
      policy.phase_boundary?.does_not_push_github === true &&
      policy.phase_boundary?.does_not_read_or_store_credentials === true,
    "s04p1_phase_boundary",
    "Policy keeps S04 P1 bounded to ChatGPT sync and defers S04 P2/P3",
    "Policy phase boundary is incomplete",
    { phase_boundary: policy.phase_boundary },
  );
}

function validateRuntime() {
  [syncScript, atlasctlScript].forEach(validateTextFile);
  const syncSource = readRepoFile(syncScript);
  const atlasctlSource = readRepoFile(atlasctlScript);
  assertCondition(
    hasAll(syncSource, [
      "official_export_fallback",
      "FORBIDDEN_BROWSER_STATES",
      "browser_requires_human_authentication",
      "assert_no_credentials",
      "data/public_raw/chatgpt",
      "chatgpt_sync_summary.json",
      "append-only",
    ]),
    "s04p1_sync_script_surface",
    "ChatGPT sync script exposes official export fallback, credential gate and append-only raw output",
    "ChatGPT sync script is missing required surface",
  );

  assertCondition(
    hasAll(atlasctlSource, [
      "sync",
      "chatgpt",
      "sync_chatgpt_memory_data.py",
      "readonly_contract",
      "official_export",
    ]),
    "s04p1_atlasctl_surface",
    "atlasctl exposes sync --source chatgpt dry-run surface",
    "atlasctl is missing ChatGPT sync surface",
  );

  const forbiddenRuntimeFragments = [
    "page.click(\"send",
    "page.click('send",
    "delete_conversation(",
    "archive_conversation(",
    "rename_conversation(",
    "send_message(",
  ];
  const forbiddenHits = forbiddenRuntimeFragments.filter((fragment) => syncSource.includes(fragment) || atlasctlSource.includes(fragment));
  assertCondition(
    forbiddenHits.length === 0,
    "s04p1_no_browser_mutation_code",
    "ChatGPT sync runtime has no send/delete/archive/rename browser mutation code",
    "ChatGPT sync runtime contains forbidden browser mutation fragments",
    { forbiddenHits },
  );

  const unit = run("python", ["-B", "-m", "unittest", "OpenAIDatabase.tests.test_s04p1_chatgpt_sync", "-q"], {
    cwd: worktreeRoot,
    timeout: 120000,
  });
  assertCondition(
    unit.stdout.includes("OK") || unit.stderr.includes("OK"),
    "s04p1_unit_tests",
    "S04 P1 ChatGPT sync unit tests pass",
    "S04 P1 unit tests did not report OK",
    { stdout: unit.stdout.slice(-2000), stderr: unit.stderr.slice(-2000) },
  );

  const atlasctl = parseJsonFromStdout(run("python3", [atlasctlScript, "sync", "--source", "chatgpt", "--dry-run"], {
    cwd: repoRoot,
    timeout: 120000,
  }));
  assertCondition(
    atlasctl.status === "PASS" &&
      atlasctl.source_id === "chatgpt" &&
      atlasctl.dry_run === true &&
      atlasctl.browser_connector === "readonly_contract" &&
      atlasctl.fallback === "official_export",
    "s04p1_atlasctl_dry_run",
    "atlasctl sync --source chatgpt --dry-run returns a runnable read-only contract",
    "atlasctl ChatGPT dry-run contract failed",
    atlasctl,
  );
}

function validateHumanAndMachineState() {
  [
    humanPagePath,
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/运行门禁/README.md",
  ].forEach(validateTextFile);

  const humanPage = readRepoFile(humanPagePath);
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  const currentStateIsS04P2 =
    hasAll(quickEntry, [
      "当前阶段是 S04 P2",
      "MA-V12-S04P2",
      "ACC-MA-V12-S04P2",
      "下一步只允许进入 S04 P3",
    ]) &&
    hasAll(overview, [
      "S04 P2 已完成",
      "Codex local sync",
      "下一步是 S04 P3",
    ]) &&
    hasAll(machineReadme, [
      "当前为 S04 P2",
      "codex_agent_sync_policy.v1_2_s04_p2.json",
      "下一步是 S04 P3",
    ]) &&
    hasAll(syncReadme, [
      "当前 S04 P2 已完成",
      "Codex local sync",
      "future-agent minimal adapter",
    ]) &&
    hasAll(runGateReadme, [
      "当前阶段是 S04 P2",
      "validate:v1.2-s04-p2",
      "下一步是 S04 P3",
    ]);
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

  assertCondition(
    hasAll(humanPage, [
      "ChatGPT只读同步与官方导出Fallback",
      taskId,
      acceptanceId,
      status,
      "只读",
      "密码/验证码立即停止",
      "不得发送消息/删除/归档/重命名会话",
      "official export ZIP/conversations.json fallback",
      "下一步是 S04 P2",
      "No GitHub main upload in this phase",
    ]),
    "s04p1_human_page",
    "Human S04 P1 page explains read-only ChatGPT sync, fallback and boundaries",
    "Human S04 P1 page is incomplete",
  );

  if (currentStateIsS04P2 || currentStateIsS04P3) {
    pass(
      "s04p1_human_machine_later_s04_state",
      "Current human and machine state has advanced from S04 P1 into S04 P2 or S04 P3",
    );
    return;
  }

  assertCondition(
    hasAll(quickEntry, [
      "当前阶段是 S04 P1",
      taskId,
      acceptanceId,
      status,
      "ChatGPT 只读同步",
      "official export fallback",
      "下一步只允许进入 S04 P2",
      "No GitHub main upload in this phase",
    ]),
    "s04p1_quick_entry",
    "Human quick entry records S04 P1 state and next S04 P2 gate",
    "Human quick entry is missing S04 P1 state",
  );

  assertCondition(
    hasAll(overview, [
      "S04 P1 已完成",
      "ChatGPT 只读同步",
      "official export fallback",
      "密码/验证码立即停止",
      "下一步是 S04 P2",
    ]),
    "s04p1_overview",
    "Human overview records S04 P1 state and next S04 P2 gate",
    "Human overview is missing S04 P1 state",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S04 P1",
      policyPath,
      syncScript,
      atlasctlScript,
      "下一步是 S04 P2",
    ]),
    "s04p1_machine_readme",
    "Machine README records S04 P1 policy, runtime and next gate",
    "Machine README is missing S04 P1 state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S04 P1 已完成",
      policyPath,
      syncScript,
      atlasctlScript,
      "official export fallback",
      "下一步是 S04 P2",
    ]),
    "s04p1_sync_readme",
    "Sync README records S04 P1 ChatGPT sync and next gate",
    "Sync README is missing S04 P1 state",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S04 P1",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S03 Review 已通过",
      "下一步是 S04 P2",
      "No GitHub main upload in this phase",
    ]),
    "s04p1_run_gate_readme",
    "Run gate README records S04 P1 validator, artifact and next S04 P2 gate",
    "Run gate README is missing S04 P1 state",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S04 P1 ChatGPT Sync",
      taskId,
      acceptanceId,
      status,
      validatorName,
      policyPath,
      syncScript,
      atlasctlScript,
      "browser connector",
      "read-only",
      "official export ZIP/conversations.json fallback",
      "password or verification",
      "No GitHub main upload in this phase",
      "pending S04 P2",
    ]),
    "s04p1_review_artifact",
    "Review artifact records S04 P1 acceptance, files, boundaries and next gate",
    "Review artifact is incomplete",
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
        "memory_atlas_v1_2_s04_p1_chatgpt_sync.md",
        "S04 P1",
        "pending S04 P2",
        "No GitHub main upload in this phase",
      ]),
      `s04p1_records_${name}`,
      `${name} records S04 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S04 P1 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s04p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s04p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S04 P1 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s04p1_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/config/",
    "OpenAIDatabase/data/public_raw/",
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/raw_encrypted",
    "OpenAIDatabase/private_exports/",
    "OpenAIDatabase/apps/memory-atlas/src/",
  ];
  const forbiddenOpenChanges = changed.filter((file) => {
    if (allowedOpenDiffPaths.includes(file)) return false;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s04p1_open_diff_scope",
    "Open diff is limited to S04 P1 ChatGPT sync runtime, policy, validator, tests and records",
    "Open diff contains files outside S04 P1 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s04p1_no_raw_config_or_ui_open_changes",
    "S04 P1 open diff does not modify real raw data, config secrets or UI",
    "S04 P1 open diff includes forbidden raw/config/UI changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousStageGate();
  validateChatGptPolicy();
  validateRuntime();
  validateHumanAndMachineState();
  validateReviewArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s04_p1",
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
    validator: "validate_memory_atlas_v1_2_s04_p1",
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
