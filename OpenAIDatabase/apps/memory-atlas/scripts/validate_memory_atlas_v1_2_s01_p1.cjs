#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S01P1";
const acceptanceId = "ACC-MA-V12-S01P1";
const status = "phase_s01_p1_current_state_audited_pending_s01_p2";
const validatorName = "validate:v1.2-s01-p1";
const auditPath = "docs/reviews/memory_atlas_v1_2_s01_p1_current_state_audit.md";
const branchName = "codex/memory-atlas-v12-stage0-14-local";

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p1.cjs",
  `OpenAIDatabase/${auditPath}`,
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  "OpenAIDatabase/功能清单.md",
  "OpenAIDatabase/开发记录.md",
  "OpenAIDatabase/模型参数文件.md",
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

function getOpenChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all"], {
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_2_s01_p1.cjs",
    "s01p1_package_script",
    "package.json exposes the v1.2 S01 P1 validator",
    "package.json is missing the v1.2 S01 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateAuditArtifact() {
  validateTextFile(auditPath);
  const source = readRepoFile(auditPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S01 P1 Current State Audit",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S01 P1 Current State Audit",
      "S01 P2 not executed",
      "S01 P3 not executed",
      "S01 official stage count is S01-S14; no formal S00 in TaskPack",
      "TaskPack SHA256",
      "38e21ae3e94d860e6a40c70a629c8f7048f889164358df7b184bd8caf7bf2472",
      "Roadmap SHA256",
      "699a8fe5f99a5edc88fec1f8940c4339f7b9b291bd31830f946f521f80904a71",
      "OpenAIDatabase/AGENTS.md",
      "OpenAIDatabase/README.md",
      "OpenAIDatabase/功能清单.md",
      "OpenAIDatabase/开发记录.md",
      "OpenAIDatabase/模型参数文件.md",
      "apps/memory-atlas/package.json",
      "OpenAIDatabase/人类可读/ = missing before S01 P2",
      "OpenAIDatabase/机器治理/ = missing before S01 P2",
      "Do not commit raw OpenAI exports",
      "Do not automate ChatGPT login",
      "v1.2 replacement needed",
      "raw/transcript public backup allowed by user authorization",
      "credentials are not transcript",
      "No apps/scripts/tests/config move",
      "No AGENTS taskpack dump",
      "No GitHub main upload in this phase",
    ]),
    "s01p1_audit_artifact",
    "S01 P1 audit records inputs, repo baseline, current structure, old boundaries, v1.2 replacements and stop checks",
    "S01 P1 audit artifact is incomplete",
  );
}

function validateCurrentRepoFacts() {
  const requiredFiles = [
    "AGENTS.md",
    "README.md",
    "功能清单.md",
    "开发记录.md",
    "模型参数文件.md",
    "apps/memory-atlas/package.json",
  ];
  const requiredDirs = [
    "apps",
    "apps/memory-atlas",
    "scripts",
    "tests",
    "config",
    "data",
    "docs/governance",
  ];

  requiredFiles.forEach((relativePath) => {
    assertCondition(
      fs.existsSync(path.join(repoRoot, relativePath)),
      `s01p1_required_file_${relativePath}`,
      `${relativePath} exists for S01 P1 current-state audit`,
      `${relativePath} is missing`,
    );
  });

  requiredDirs.forEach((relativePath) => {
    assertCondition(
      fs.statSync(path.join(repoRoot, relativePath)).isDirectory(),
      `s01p1_required_dir_${relativePath}`,
      `${relativePath} directory exists and was not moved for S01 P1`,
      `${relativePath} directory is missing`,
    );
  });

  const agents = readRepoFile("AGENTS.md");
  const readme = readRepoFile("README.md");
  const agentsOldBoundary = hasAll(agents, ["Do not commit raw OpenAI exports", "Do not automate ChatGPT login"]);
  const agentsV12Bridge = hasAll(agents, [
    "v1.2 S01 P3 Bridge",
    "用户授权后 raw/transcript 可公开进入 GitHub",
    "cookies、session tokens、passwords、API keys、private keys、OAuth tokens",
  ]);
  const readmeOldBoundary = hasAll(readme, ["Do not automate ChatGPT login", "Do not commit raw", "full transcripts must not be committed"]);
  const readmeV12Bridge = hasAll(readme, [
    "v1.2 S01 P3 Requirements Freeze Bridge",
    "用户授权后，ChatGPT、Codex、后续其他 agent 的 raw data / transcript 可以明文公开进 GitHub",
    "凭证不是 transcript",
  ]);
  assertCondition(
    agentsOldBoundary || agentsV12Bridge,
    "s01p1_existing_agents_boundary_identified",
    "AGENTS.md contains either the audited v1.1.x boundary markers or the later S01 P3 bridge that replaced them",
    "AGENTS.md contains neither the original old-boundary markers nor the S01 P3 bridge",
  );
  assertCondition(
    readmeOldBoundary || readmeV12Bridge,
    "s01p1_existing_readme_boundary_identified",
    "README.md contains either the audited v1.1.x boundary markers or the later S01 P3 bridge that replaced them",
    "README.md contains neither the original old-boundary markers nor the S01 P3 bridge",
  );
}

function validateRecords() {
  const records = [
    ["CHANGELOG.md", readRepoFile("CHANGELOG.md")],
    ["功能清单.md", readRepoFile("功能清单.md")],
    ["开发记录.md", readRepoFile("开发记录.md")],
    ["模型参数文件.md", readRepoFile("模型参数文件.md")],
    ["docs/MEMORY_ATLAS_DELIVERY_RECORD.md", readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md")],
    ["docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md", readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md")],
  ];

  records.forEach(([name]) => validateTextFile(name));
  records.forEach(([name, source]) => {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "memory_atlas_v1_2_s01_p1_current_state_audit.md",
        "S01 P1",
        "No GitHub main upload in this phase",
      ]),
      `s01p1_records_${name}`,
      `${name} records v1.2 S01 P1 status, validator, evidence and no-upload boundary`,
      `${name} is missing v1.2 S01 P1 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s01p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s01p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S01 P1 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s01p1_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/人类可读/",
    "OpenAIDatabase/机器治理/",
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
    if (file === "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s01_p1.cjs") return false;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s01p1_open_diff_scope",
    "Open diff is limited to S01 P1 audit, validator and governance records",
    "Open diff contains files outside S01 P1 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s01p1_no_p2_p3_or_runtime_open_changes",
    "S01 P1 open diff does not create double-plane directories, move runtime dirs, touch raw archives, or edit runtime code",
    "S01 P1 open diff includes P2/P3/runtime/raw changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validateAuditArtifact();
  validateCurrentRepoFacts();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s01_p1",
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
    validator: "validate_memory_atlas_v1_2_s01_p1",
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
