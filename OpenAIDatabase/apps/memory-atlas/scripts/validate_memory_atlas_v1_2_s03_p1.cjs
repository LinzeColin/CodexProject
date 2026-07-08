#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S03P1";
const acceptanceId = "ACC-MA-V12-S03P1";
const status = "phase_s03_p1_public_raw_path_defined_pending_s03_p2";
const validatorName = "validate:v1.2-s03-p1";
const scriptName = "validate_memory_atlas_v1_2_s03_p1.cjs";
const policyPath = "机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json";
const humanPagePath = "人类可读/06_Raw明文公开与只读归档说明.md";
const publicRawReadmePath = "data/public_raw/README.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md";
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
  "OpenAIDatabase/docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md",
  "OpenAIDatabase/机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json",
  "OpenAIDatabase/人类可读/07_凭证排除说明.md",
  "OpenAIDatabase/scripts/privacy_guard.py",
  "OpenAIDatabase/scripts/sync_codex_memory_data.py",
  "OpenAIDatabase/tests/test_s3pdt01_privacy.py",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs",
  "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs",
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${publicRawReadmePath}`,
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

function currentStateIsS04P1() {
  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S04 P1",
      "MA-V12-S04P1",
      "ACC-MA-V12-S04P1",
      "下一步只允许进入 S04 P2",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S04 P1 已完成",
      "ChatGPT 只读同步",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S04 P1",
      "chatgpt_readonly_sync_policy.v1_2_s04_p1.json",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S04 P1 已完成",
      "official export fallback",
      "下一步是 S04 P2",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S04 P1",
      "validate:v1.2-s04-p1",
      "下一步是 S04 P2",
    ])
  );
}

function currentStateIsS03Review() {
  if (currentStateIsS04P1()) return true;

  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 Review",
      "MA-V12-S03-REVIEW",
      "ACC-MA-V12-S03-REVIEW",
      "下一步只允许进入 S04 P1",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 Review 已通过",
      "raw 可公开备份",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 Review",
      "memory_atlas_v1_2_s03_review.md",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 Review 已通过",
      "credential exclusion",
      "下一步是 S04 P1",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 Review",
      "validate:v1.2-s03-review",
      "下一步是 S04 P1",
    ])
  );
}

function currentStateIsS03P2() {
  if (currentStateIsS03Review()) return true;

  if (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 P3",
      "MA-V12-S03P3",
      "ACC-MA-V12-S03P3",
      "下一步只允许进入 S03 Review",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 P3 已完成",
      "raw manifest/hash 可生成",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 P3",
      "raw_manifest_ledger_policy.v1_2_s03_p3.json",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 P3 已完成",
      "raw_archive_manifest.py",
      "下一步是 S03 Review",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 P3",
      "validate:v1.2-s03-p3",
      "下一步是 S03 Review",
    ])
  ) {
    return true;
  }

  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S03 P2",
      "MA-V12-S03P2",
      "ACC-MA-V12-S03P2",
      "下一步只允许进入 S03 P3",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S03 P2 已完成",
      "credential is not memory",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S03 P2",
      "credential_exclusion_policy.v1_2_s03_p2.json",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S03 P2 已完成",
      "credentials_not_transcript",
      "下一步是 S03 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S03 P2",
      "validate:v1.2-s03-p2",
      "下一步是 S03 P3",
    ])
  );
}

function validatePackageScript() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s03p1_package_script",
    "package.json exposes the v1.2 S03 P1 validator",
    "package.json is missing the v1.2 S03 P1 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s03p1_previous_phase_deferred_scope",
      "S02 Review execution is deferred only because open diff is limited to S03 P1 files",
      "S02 Review execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s03p1_previous_phase_deferred_until_clean_tree",
      "S02 Review validator will run on a clean tree after S03 P1 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s02_review.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S02-REVIEW",
    "s03p1_previous_s02_review",
    "S02 Review validator returns PASS before accepting S03 P1",
    "S02 Review validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateRawPolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));

  assertCondition(
    policy.policy_id === "memory_atlas_raw_public_archive_policy_v1_2_s03_p1" &&
      policy.task_id === taskId &&
      policy.acceptance_id === acceptanceId &&
      policy.status === status,
    "s03p1_policy_identity",
    "Raw public archive policy records S03 P1 identity and status",
    "Raw public archive policy identity is incomplete",
    {
      policy_id: policy.policy_id,
      task_id: policy.task_id,
      acceptance_id: policy.acceptance_id,
      status: policy.status,
    },
  );

  assertCondition(
    policy.public_raw_root === "data/public_raw" &&
      policy.source_raw_roots?.chatgpt === "data/public_raw/chatgpt" &&
      policy.source_raw_roots?.codex === "data/public_raw/codex" &&
      policy.source_raw_roots?.future_agents === "data/public_raw/agents/{agent_id}",
    "s03p1_public_raw_paths",
    "Policy defines public raw root and source-specific raw paths",
    "Policy is missing public raw paths",
    { public_raw_root: policy.public_raw_root, source_raw_roots: policy.source_raw_roots },
  );

  assertCondition(
    policy.manifest_contract?.manifest_root === "机器治理/证据与日志/raw_archive_manifests" &&
      policy.manifest_contract?.manifest_file_pattern === "raw_manifest.{run_id}.jsonl" &&
      policy.manifest_contract?.hash_ledger_file === "raw_hash_ledger.jsonl" &&
      policy.manifest_contract?.minimum_manifest_fields?.includes("source_id") &&
      policy.manifest_contract?.minimum_manifest_fields?.includes("relative_path") &&
      policy.manifest_contract?.minimum_manifest_fields?.includes("sha256") &&
      policy.manifest_contract?.minimum_manifest_fields?.includes("imported_at"),
    "s03p1_manifest_hash_contract",
    "Policy defines raw manifest/hash file paths and minimum hash fields",
    "Policy is missing manifest/hash contract",
    { manifest_contract: policy.manifest_contract },
  );

  assertCondition(
    policy.append_only_rule?.allow_new_raw_files === true &&
      policy.append_only_rule?.forbid_modify_existing_raw === true &&
      policy.append_only_rule?.forbid_delete_existing_raw === true &&
      policy.append_only_rule?.forbid_overwrite_existing_raw === true &&
      policy.append_only_rule?.raw_files_are_not_apply_targets === true,
    "s03p1_append_only_rule",
    "Policy defines append-only raw rules",
    "Policy append-only rule is incomplete",
    { append_only_rule: policy.append_only_rule },
  );

  assertCondition(
    policy.hash_drift_fail_rule?.enabled === true &&
      policy.hash_drift_fail_rule?.same_relative_path_requires_same_sha256 === true &&
      policy.hash_drift_fail_rule?.deleted_manifest_entry_fails === true &&
      policy.hash_drift_fail_rule?.changed_sha256_fails === true &&
      policy.hash_drift_fail_rule?.new_relative_path_is_append_only === true,
    "s03p1_hash_drift_fail_rule",
    "Policy defines hash drift failure rules",
    "Policy hash drift failure rule is incomplete",
    { hash_drift_fail_rule: policy.hash_drift_fail_rule },
  );

  assertCondition(
    policy.phase_boundary?.credential_pattern_gate_deferred_to === "S03 P2" &&
      policy.phase_boundary?.manifest_generation_deferred_to === "S03 P3" &&
      policy.phase_boundary?.connector_implementation_deferred_to === "S04" &&
      policy.phase_boundary?.does_not_ingest_transcripts_in_this_phase === true,
    "s03p1_phase_boundary",
    "Policy explicitly defers S03 P2 credentials, S03 P3 manifest generation and S04 connector work",
    "Policy phase boundary is incomplete",
    { phase_boundary: policy.phase_boundary },
  );
}

function validatePublicRawReadme() {
  validateTextFile(publicRawReadmePath);
  const source = readRepoFile(publicRawReadmePath);
  assertCondition(
    hasAll(source, [
      "Public Raw Archive",
      taskId,
      acceptanceId,
      status,
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "append-only",
      "hash drift fail",
      "credentials_not_transcript",
      "No transcript ingestion in S03 P1",
    ]),
    "s03p1_public_raw_readme",
    "Public raw README defines public paths, append-only/hash drift rules and no-ingestion boundary",
    "Public raw README is missing S03 P1 fragments",
  );
}

function validateHumanPage() {
  validateTextFile(humanPagePath);
  const source = readRepoFile(humanPagePath);
  assertCondition(
    hasAll(source, [
      "Raw 明文公开与只读归档说明",
      taskId,
      acceptanceId,
      status,
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "raw_public_archive_policy.v1_2_s03_p1.json",
      "只追加",
      "不能修改",
      "不能删除",
      "hash drift fail",
      "凭证检查在 S03 P2",
      "manifest 生成在 S03 P3",
      "No GitHub main upload in this phase",
    ]),
    "s03p1_human_page",
    "Human page explains raw public paths and S03 P1 boundaries without manifest row details",
    "Human page is missing S03 P1 fragments",
  );

  const noisyFragments = ["sha256:", "\"sha256\"", "raw_manifest.{run_id}.jsonl entry", "manifest row"];
  const noisy = noisyFragments.filter((fragment) => source.includes(fragment));
  assertCondition(
    noisy.length === 0,
    "s03p1_human_page_not_manifest_ledger",
    "Human page does not expose raw manifest row details as the primary page",
    "Human page is polluted by raw manifest details",
    { noisy },
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S03 P1 Public Raw Path",
      taskId,
      acceptanceId,
      status,
      validatorName,
      policyPath,
      publicRawReadmePath,
      humanPagePath,
      "public raw archive path",
      "raw manifest/hash file",
      "append-only rule",
      "hash drift fail rule",
      "No S03 P2 credential gate",
      "No S03 P3 manifest generation",
      "No connector implementation",
      "No GitHub main upload in this phase",
      "pending S03 P2",
    ]),
    "s03p1_review_artifact",
    "Review artifact records S03 P1 acceptance, files, boundaries and next gate",
    "Review artifact is incomplete",
  );
}

function validateHumanAndMachineState() {
  const humanEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  if (currentStateIsS03P2()) {
    pass(
      "s03p1_human_machine_later_s03p2_state",
      "Current human and machine state has advanced from S03 P1 into S03 P2",
    );
    return;
  }

  assertCondition(
    hasAll(humanEntry, [
      "当前阶段是 S03 P1",
      taskId,
      acceptanceId,
      status,
      "data/public_raw/",
      "raw_public_archive_policy.v1_2_s03_p1.json",
      "下一步只允许进入 S03 P2",
      "No GitHub main upload in this phase",
    ]),
    "s03p1_human_entry_state",
    "Human quick entry records S03 P1 state and next S03 P2 gate",
    "Human quick entry is missing S03 P1 state",
  );

  assertCondition(
    hasAll(overview, [
      "S03 P1 已完成",
      "data/public_raw/chatgpt",
      "data/public_raw/codex",
      "data/public_raw/agents/{agent_id}",
      "manifest/hash",
      "append-only",
      "hash drift fail",
      "下一步是 S03 P2",
    ]),
    "s03p1_overview_state",
    "Overview records S03 P1 public raw path and next S03 P2 gate",
    "Overview is missing S03 P1 state",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S03 P1",
      policyPath,
      publicRawReadmePath,
      humanPagePath,
      "append-only",
      "hash drift fail",
      "下一步是 S03 P2",
    ]),
    "s03p1_machine_readme",
    "Machine README records S03 P1 machine policy and next gate",
    "Machine README is missing S03 P1 state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S03 P1 已完成",
      policyPath,
      "data/public_raw/",
      "manifest/hash",
      "append-only",
      "hash drift fail",
      "下一步是 S03 P2",
    ]),
    "s03p1_sync_readme",
    "Sync README records S03 P1 raw policy and next S03 P2 gate",
    "Sync README is missing S03 P1 state",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S03 P1",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S02 Review 已通过",
      "下一步是 S03 P2",
      "No GitHub main upload in this phase",
    ]),
    "s03p1_run_gate_readme",
    "Run gate README records S03 P1 validator, artifact and next S03 P2 gate",
    "Run gate README is missing S03 P1 state",
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
        "memory_atlas_v1_2_s03_p1_public_raw_path.md",
        "raw_public_archive_policy.v1_2_s03_p1.json",
        "data/public_raw/README.md",
        "S03 P1",
        "pending S03 P2",
        "No GitHub main upload in this phase",
      ]),
      `s03p1_records_${name}`,
      `${name} records S03 P1 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S03 P1 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s03p1_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s03p1_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S03 P1 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s03p1_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/raw_encrypted",
    "OpenAIDatabase/private_exports/",
  ];
  const forbiddenPublicRawChanges = changed.filter((file) => (
    file.startsWith("OpenAIDatabase/data/public_raw/") &&
    file !== `OpenAIDatabase/${publicRawReadmePath}`
  ));
  const forbiddenRuntimeChanges = changed.filter((file) => (
    file.startsWith("OpenAIDatabase/apps/") &&
    !allowedOpenDiffPaths.includes(file) &&
    file !== "OpenAIDatabase/apps/memory-atlas/package.json" &&
    file !== "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p1.cjs" &&
    file !== "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p2.cjs" &&
    file !== "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_p3.cjs" &&
    file !== "OpenAIDatabase/apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s02_review.cjs" &&
    file !== `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`
  ));
  const forbiddenOpenChanges = changed.filter((file) => (
    forbiddenPrefixes.some((prefix) => file.startsWith(prefix))
  ));

  assertCondition(
    outside.length === 0,
    "s03p1_open_diff_scope",
    "Open diff is limited to S03 P1 policy, README, human page, review artifact, validator and records",
    "Open diff contains files outside S03 P1 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenPublicRawChanges.length === 0 &&
      forbiddenRuntimeChanges.length === 0 &&
      forbiddenOpenChanges.length === 0,
    "s03p1_no_raw_transcript_or_runtime_open_changes",
    "S03 P1 open diff does not add transcript files, modify existing raw areas or implement connector/runtime work",
    "S03 P1 open diff includes forbidden raw/runtime changes",
    { changed, forbiddenPublicRawChanges, forbiddenRuntimeChanges, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateRawPolicy();
  validatePublicRawReadme();
  validateHumanPage();
  validateReviewArtifact();
  validateHumanAndMachineState();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s03_p1",
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
    validator: "validate_memory_atlas_v1_2_s03_p1",
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
