#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V117-FINAL-UPLOAD";
const acceptanceId = "ACC-MA-V117-FINAL-GITHUB-MAIN";
const status = "final_github_main_upload_completed";
const validatorName = "validate:v1.1.7-final-upload";
const finalUploadPath = "docs/reviews/memory_atlas_v1_1_7_final_github_main_upload.md";
const branchName = "codex/memory-atlas-v117-stage0-10-local";
const requireRemoteMain = process.env.MEMORY_ATLAS_REQUIRE_REMOTE_MAIN === "1";

const allowedFinalUploadChangePaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_1_7_final_upload.cjs",
  "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  "OpenAIDatabase/docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "OpenAIDatabase/docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
  `OpenAIDatabase/${finalUploadPath}`,
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
    maxBuffer: 32 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function getChangedPaths() {
  const result = run("git", ["-c", "core.quotepath=false", "status", "--short", "--untracked-files=all"], {
    cwd: worktreeRoot,
  });
  return result.stdout
    .split("\n")
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean);
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
    packageJson.scripts?.[validatorName] === "node scripts/validate_memory_atlas_v1_1_7_final_upload.cjs",
    "final_upload_package_script",
    "package.json exposes the final GitHub main upload validator",
    "package.json is missing the final GitHub main upload validator script",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateFinalUploadArtifact() {
  validateTextFile(finalUploadPath);
  const source = readRepoFile(finalUploadPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.1.7 Final GitHub Main Upload",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "validate:v1.1.7-stage10",
      "GitHub main points at the final upload commit",
      "LinzeColin/CodexProject",
      "OpenAIDatabase",
      "Stage 0-10",
      "No intermediate GitHub upload",
      "No remote development branch",
      "No open pull request",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret data access",
    ]),
    "final_upload_artifact",
    "Final upload artifact records task, acceptance, validators, GitHub main evidence and no-branch/no-PR boundaries",
    "Final upload artifact is incomplete",
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
    ["config/visualization/model_parameters.universe_state.yaml", readRepoFile("config/visualization/model_parameters.universe_state.yaml")],
  ];

  for (const [name, source] of records) {
    assertCondition(
      hasAll(source, [
        taskId,
        acceptanceId,
        status,
        validatorName,
        "validate:v1.1.7-stage10",
        "GitHub main points at the final upload commit",
        "No remote development branch",
        "No open pull request",
      ]),
      `final_upload_records_${name}`,
      `${name} records final GitHub main upload status, validator and branch/PR boundaries`,
      `${name} is missing final upload record fragments`,
    );
  }
}

function validateLocalGitState() {
  const changed = getChangedPaths();
  if (changed.length > 0) {
    const outside = changed.filter((file) => !allowedFinalUploadChangePaths.includes(file));
    assertCondition(
      outside.length === 0,
      "final_upload_clean_worktree_deferred_scope",
      "Clean-tree proof is deferred only because the open diff is limited to final GitHub main upload records and validator files",
      "Open diff contains files outside the final GitHub main upload allowed scope",
      { changed, outside, allowedFinalUploadChangePaths },
    );
  } else {
    pass(
      "final_upload_clean_worktree",
      "Worktree is clean for final upload validation",
      { changed },
    );
  }

  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote.includes("LinzeColin/CodexProject.git"),
    "final_upload_canonical_remote",
    "origin remote points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );
}

function validateRemoteState() {
  const head = run("git", ["rev-parse", "HEAD"], { cwd: worktreeRoot }).stdout.trim();
  const remoteMain = run("git", ["ls-remote", "--heads", "origin", "main"], { cwd: worktreeRoot }).stdout.trim();
  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], { cwd: worktreeRoot }).stdout.trim();
  const remoteMainSha = remoteMain.split(/\s+/)[0] || "";

  assertCondition(
    remoteDev === "",
    "final_upload_no_remote_development_branch",
    "No remote Stage 0-10 development branch exists",
    "Remote development branch still exists",
    { branchName, remoteDev },
  );

  if (requireRemoteMain) {
    assertCondition(
      remoteMainSha === head,
      "final_upload_remote_main_matches_head",
      "GitHub main points at the final upload commit",
      "GitHub main does not point at local HEAD",
      { head, remoteMainSha, remoteMain },
    );
    return;
  }

  pass(
    "final_upload_remote_main_check_deferred",
    "Remote main equality check is deferred until after push; set MEMORY_ATLAS_REQUIRE_REMOTE_MAIN=1 for post-upload proof",
    { head, remoteMainSha },
  );
}

function main() {
  validatePackageScript();
  validateFinalUploadArtifact();
  validateRecords();
  validateLocalGitState();
  validateRemoteState();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_1_7_final_upload",
    task_id: taskId,
    acceptance_id: acceptanceId,
    require_remote_main: requireRemoteMain,
    checks,
  }, null, 2));
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    status: "FAIL",
    validator: "validate_memory_atlas_v1_1_7_final_upload",
    task_id: taskId,
    acceptance_id: acceptanceId,
    require_remote_main: requireRemoteMain,
    error: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-6000),
      stderr: error.stderr?.slice(-6000),
    },
    checks,
  }, null, 2));
  process.exit(1);
}
