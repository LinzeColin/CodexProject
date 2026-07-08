#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S01-REVIEW";
const acceptanceId = "ACC-MA-V12-S01-REVIEW";
const status = "stage_s01_review_passed_pending_s02_no_github_main_upload";
const validatorName = "validate:v1.2-s01-review";
const scriptName = "validate_memory_atlas_v1_2_s01_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s01_review.md";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const phaseValidators = [
  ["s01_p1_validator", "validate_memory_atlas_v1_2_s01_p1.cjs", "ACC-MA-V12-S01P1"],
  ["s01_p2_validator", "validate_memory_atlas_v1_2_s01_p2.cjs", "ACC-MA-V12-S01P2"],
  ["s01_p3_validator", "validate_memory_atlas_v1_2_s01_p3.cjs", "ACC-MA-V12-S01P3"],
];

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const allowedReviewChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p3.cjs",
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
    "s01_review_package_script",
    "package.json exposes the v1.2 S01 review validator",
    "package.json is missing the v1.2 S01 review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function currentStateIsS04P3() {
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  const s04p3State =
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

  const s04ReviewState =
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

  return s04p3State || s04ReviewState;
}

function validatePhaseValidators() {
  const changed = getOpenChangedPaths();
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));

  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s01_review_phase_validator_deferred_scope",
      "Phase validator execution is deferred only because open diff is limited to S01 review files",
      "Phase validator execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedReviewChangePaths },
    );

    phaseValidators.forEach(([name, script]) => {
      const scriptPath = path.join(appRoot, "scripts", script);
      const scriptRegistered = Object.values(packageJson.scripts || {}).some((command) => command.includes(script));
      assertCondition(
        fs.existsSync(scriptPath) && scriptRegistered,
        `${name}_registered_for_clean_tree_review`,
        `${script} exists and is registered for clean-tree execution after S01 review commit`,
        `${script} is missing or not registered`,
        { script, scriptRegistered },
      );
    });
    pass(
      "s01_review_phase_validators_deferred_until_clean_tree",
      "S01 phase validators enforce their own changed-path scopes; run S01 review validator again after commit to execute them on a clean tree",
      { changed },
    );
    return;
  }

  phaseValidators.forEach(([name, script, expectedAcceptanceId]) => {
    const result = run("node", [`scripts/${script}`], { cwd: appRoot, timeout: 120000 });
    const output = result.stdout.trim();
    const parsed = JSON.parse(output.slice(output.indexOf("{")));
    assertCondition(
      parsed.status === "PASS" && parsed.acceptance_id === expectedAcceptanceId,
      name,
      `${script} returned PASS for ${expectedAcceptanceId}`,
      `${script} did not return PASS for ${expectedAcceptanceId}`,
      { status: parsed.status, acceptance_id: parsed.acceptance_id },
    );
  });
}

function validateS01PassGate() {
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const freeze = JSON.parse(readRepoFile("机器治理/运行门禁/v1.2需求冻结清单.json"));
  const readme = readRepoFile("README.md");
  const agents = readRepoFile("AGENTS.md");

  ["人类可读/00_快速入口.md", "人类可读/01_v1.2四线14Stage升级总览.md", "README.md", "AGENTS.md"].forEach(validateTextFile);

  const s01ReviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S01 Review：S01 整体复审已通过",
      "不是跳转页",
      "旧隐私边界已被 v1.2 替换",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P1",
      "No GitHub main upload in this review",
  ]);
  const s02p1QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P1：数据源模型已定义",
      "S01 Review 已通过",
      "不是跳转页",
      "旧隐私边界已被 v1.2 替换",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P2",
      "No GitHub main upload in this phase",
  ]);
  const s02p2QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P2：source registry 已建立",
      "S01 Review 已通过",
      "不是跳转页",
      "旧隐私边界已被 v1.2 替换",
      "凭证不是 transcript",
      "下一步只允许进入 S02 P3",
      "No GitHub main upload in this phase",
  ]);
  const s02p3QuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 P3：人类同步说明已完成",
      "S01 Review 已通过",
      "不是跳转页",
      "旧隐私边界已被 v1.2 替换",
      "凭证不是 transcript",
      "下一步只允许进入 S02 Review",
      "No GitHub main upload in this phase",
  ]);
  const s02ReviewQuickEntry = hasAll(quickEntry, [
      "当前阶段是 S02 Review：S02 整体复审已通过",
      "S01 Review 已通过",
      "不是跳转页",
      "旧隐私边界已被 v1.2 替换",
      "凭证不是 transcript",
      "下一步只允许进入 S03 P1",
      "No GitHub main upload in this review",
  ]);
  const s04p3State = currentStateIsS04P3();
  assertCondition(
    s01ReviewQuickEntry || s02p1QuickEntry || s02p2QuickEntry || s02p3QuickEntry || s02ReviewQuickEntry || s04p3State,
    "s01_review_human_quick_entry",
    "Human quick entry is Chinese, not a jump page, and records S01 review result or later accepted state through S04 P3",
    "Human quick entry is missing S01 review, S02 states, S02 Review or S04 P3 status",
  );

  const s01ReviewOverview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "下一步是 S02 P1",
      "整体完成后才上传 GitHub main",
  ]);
  const s02p1Overview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "S02 P1 已完成",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "下一步是 S02 P2",
      "整体完成后才上传 GitHub main",
  ]);
  const s02p2Overview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "S02 P1 已完成",
      "S02 P2 已完成",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "下一步是 S02 P3",
      "整体完成后才上传 GitHub main",
  ]);
  const s02p3Overview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "S02 P1 已完成",
      "S02 P2 已完成",
      "S02 P3 已完成",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "下一步是 S02 Review",
      "整体完成后才上传 GitHub main",
  ]);
  const s02ReviewOverview = hasAll(overview, [
      "S01 整体复审已通过",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "S02 Review 已通过",
      "旧隐私边界替换为用户授权后的 raw/transcript 公开",
      "下一步是 S03 P1",
      "整体完成后才上传 GitHub main",
  ]);
  assertCondition(
    s01ReviewOverview || s02p1Overview || s02p2Overview || s02p3Overview || s02ReviewOverview || s04p3State,
    "s01_review_human_overview",
    "Human overview records S01 review result, phase coverage and later accepted state through S04 P3",
    "Human overview is missing S01 review result, phase coverage, later S02 state or S04 P3 state",
  );

  assertCondition(
    freeze.stage_count === 14 &&
      freeze.raw_public_authorization?.plaintext_public_github_allowed === true &&
      freeze.raw_public_authorization?.append_only === true &&
      freeze.credentials_exclusion?.includes("cookies") &&
      freeze.credentials_exclusion?.includes("api_keys") &&
      freeze.source_registry_extension?.supports_future_other_agents === true,
    "s01_review_freeze_config",
    "Requirements freeze config proves four-line / 14-stage / raw-public / credential-exclusion gate",
    "Requirements freeze config is incomplete for S01 review",
    {
      stage_count: freeze.stage_count,
      raw_public_authorization: freeze.raw_public_authorization,
      credentials_exclusion: freeze.credentials_exclusion,
      source_registry_extension: freeze.source_registry_extension,
    },
  );

  assertCondition(
    hasAll(readme, [
      "v1.2 S01 P3 Requirements Freeze Bridge",
      "旧的 raw/private 默认不入 GitHub 边界被 v1.2 替换",
      "凭证不是 transcript",
      "每次 run 最多只完成一个 phase",
    ]),
    "s01_review_readme_boundary",
    "README explains v1.2 boundary replacement and execution rule",
    "README is missing v1.2 S01 boundary bridge",
  );

  assertCondition(
    hasAll(agents, [
      "v1.2 S01 P3 Bridge",
      "不要把 taskpack 大段写入 AGENTS.md",
      "用户授权后 raw/transcript 可公开进入 GitHub",
      "每次 run 最多只完成一个 phase",
    ]),
    "s01_review_agents_boundary",
    "AGENTS.md keeps a compact bridge without taskpack dump",
    "AGENTS.md is missing compact S01 bridge or taskpack-dump guard",
  );

  ["功能清单.md", "开发记录.md", "模型参数文件.md"].forEach((relativePath) => {
    assertCondition(
      fs.existsSync(path.join(repoRoot, relativePath)),
      `s01_review_owner_file_${relativePath}`,
      `${relativePath} is preserved as a root owner door`,
      `${relativePath} is missing`,
    );
  });
}

function validateMachineGate() {
  ["机器治理/README.md", "机器治理/运行门禁/README.md"].forEach(validateTextFile);
  const machineReadme = readRepoFile("机器治理/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  const s01ReviewMachineReadme = hasAll(machineReadme, [
      "当前为 S01 Review",
      "S01 整体复审已通过",
      "下一步是 S02 P1",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p1MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P1",
      "S01 整体复审已通过",
      "数据源模型已定义",
      "下一步是 S02 P2",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p2MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P2",
      "S01 整体复审已通过",
      "source registry 已建立",
      "下一步是 S02 P3",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02p3MachineReadme = hasAll(machineReadme, [
      "当前为 S02 P3",
      "S01 整体复审已通过",
      "source registry 已建立",
      "人类同步说明已完成",
      "下一步是 S02 Review",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s02ReviewMachineReadme = hasAll(machineReadme, [
      "当前为 S02 Review",
      "S01 整体复审已通过",
      "source registry 已建立",
      "人类同步说明已完成",
      "S02 整体复审已通过",
      "下一步是 S03 P1",
      "不替代 apps/scripts/tests/config/data/docs/governance",
  ]);
  const s04p3State = currentStateIsS04P3();
  assertCondition(
    s01ReviewMachineReadme || s02p1MachineReadme || s02p2MachineReadme || s02p3MachineReadme || s02ReviewMachineReadme || s04p3State,
    "s01_review_machine_readme",
    "Machine README records S01 review result or later accepted state through S04 P3",
    "Machine README is missing S01 review, S02 states, S02 Review or S04 P3 result",
  );

  const s01ReviewRunGate = hasAll(runGateReadme, [
      "当前阶段是 S01 Review",
      taskId,
      acceptanceId,
      "validate:v1.2-s01-review",
      "下一步是 S02 P1",
      "No GitHub main upload in this review",
  ]);
  const s02p1RunGate = hasAll(runGateReadme, [
      "当前阶段是 S02 P1",
      taskId,
      acceptanceId,
      "validate:v1.2-s01-review",
      "MA-V12-S02P1",
      "下一步是 S02 P2",
      "No GitHub main upload in this phase",
  ]);
  const s02p2RunGate = hasAll(runGateReadme, [
      "当前阶段是 S02 P2",
      taskId,
      acceptanceId,
      "validate:v1.2-s01-review",
      "MA-V12-S02P2",
      "下一步是 S02 P3",
      "No GitHub main upload in this phase",
  ]);
  const s02p3RunGate = hasAll(runGateReadme, [
      "当前阶段是 S02 P3",
      taskId,
      acceptanceId,
      "validate:v1.2-s01-review",
      "MA-V12-S02P2",
      "MA-V12-S02P3",
      "下一步是 S02 Review",
      "No GitHub main upload in this phase",
  ]);
  const s02ReviewRunGate = hasAll(runGateReadme, [
      "当前阶段是 S02 Review",
      taskId,
      acceptanceId,
      "validate:v1.2-s01-review",
      "MA-V12-S02-REVIEW",
      "下一步是 S03 P1",
      "No GitHub main upload in this review",
  ]);
  assertCondition(
    s01ReviewRunGate || s02p1RunGate || s02p2RunGate || s02p3RunGate || s02ReviewRunGate || s04p3State,
    "s01_review_run_gate_readme",
    "Run gate README records S01 review validator, acceptance and later accepted state through S04 P3",
    "Run gate README is missing S01 review, S02 states, S02 Review or S04 P3 gate status",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      "Memory Atlas v1.2 S01 Review",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S01 is review-passed",
      "S01 P1",
      "S01 P2",
      "S01 P3",
      "validate:v1.2-s01-p1",
      "validate:v1.2-s01-p2",
      "validate:v1.2-s01-p3",
      "Pass Gate",
      "双平面存在",
      "需求冻结清单存在",
      "旧隐私边界已被明确替换",
      "No S02 work",
      "No GitHub main upload in this review",
      "No app reinstall",
      "No raw archive change",
      "pending S02 P1",
    ]),
    "s01_review_artifact",
    "S01 review artifact records phase coverage, pass gate, boundaries, validation and next gate",
    "S01 review artifact is incomplete",
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
        "memory_atlas_v1_2_s01_review.md",
        "S01 Review",
        "pending S02 P1",
        "No GitHub main upload in this review",
      ]),
      `s01_review_records_${name}`,
      `${name} records S01 review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S01 review record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s01_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s01_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S01 review branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s01_review_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedReviewChangePaths.includes(file));
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
    if (file === `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`) return false;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s01_review_open_diff_scope",
    "Open diff is limited to S01 review files",
    "Open diff contains files outside S01 review allowed scope",
    { changed, outside, allowedReviewChangePaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s01_review_no_runtime_or_raw_open_changes",
    "S01 review open diff does not move runtime dirs, touch raw archives, or edit runtime code",
    "S01 review open diff includes runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePhaseValidators();
  validateS01PassGate();
  validateMachineGate();
  validateReviewArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s01_review",
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
    validator: "validate_memory_atlas_v1_2_s01_review",
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
