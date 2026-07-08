#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];

const taskId = "MA-V12-S03P2";
const acceptanceId = "ACC-MA-V12-S03P2";
const status = "phase_s03_p2_credential_exclusion_completed_pending_s03_p3";
const validatorName = "validate:v1.2-s03-p2";
const scriptName = "validate_memory_atlas_v1_2_s03_p2.cjs";
const policyPath = "机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json";
const rawPolicyPath = "机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json";
const humanPagePath = "人类可读/07_凭证排除说明.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md";
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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${humanPagePath}`,
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
  "OpenAIDatabase/scripts/privacy_guard.py",
  "OpenAIDatabase/scripts/sync_codex_memory_data.py",
  "OpenAIDatabase/tests/test_s3pdt01_privacy.py",
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

function currentStateIsS03P3() {
  if (currentStateIsS03Review()) return true;

  return (
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
  );
}

function validatePackageScript() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s03p2_package_script",
    "package.json exposes the v1.2 S03 P2 validator",
    "package.json is missing the v1.2 S03 P2 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s03p2_previous_phase_deferred_scope",
      "S03 P1 execution is deferred only because open diff is limited to S03 P2 files",
      "S03 P1 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s03p2_previous_phase_deferred_until_clean_tree",
      "S03 P1 validator will run on a clean tree after S03 P2 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s03_p1.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S03P1",
    "s03p2_previous_s03p1",
    "S03 P1 validator returns PASS before accepting S03 P2",
    "S03 P1 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateCredentialPolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));
  const categories = policy.credential_categories || [];
  assertCondition(
    policy.policy_id === "memory_atlas_credential_exclusion_policy_v1_2_s03_p2" &&
      policy.task_id === taskId &&
      policy.acceptance_id === acceptanceId &&
      policy.status === status,
    "s03p2_policy_identity",
    "Credential exclusion policy records S03 P2 identity and status",
    "Credential exclusion policy identity is incomplete",
    {
      policy_id: policy.policy_id,
      task_id: policy.task_id,
      acceptance_id: policy.acceptance_id,
      status: policy.status,
    },
  );

  assertCondition(
    hasAll(categories.join("\n"), [
      "cookies",
      "session_tokens",
      "passwords",
      "api_keys",
      "private_keys",
      "oauth_tokens",
      "browser_credential_store",
    ]) &&
      policy.boundary_rule?.credential_is_not_memory === true &&
      policy.boundary_rule?.ordinary_transcript_is_memory === true &&
      policy.boundary_rule?.block_credentials_only === true,
    "s03p2_policy_categories",
    "Policy distinguishes credentials from ordinary transcript and lists required credential categories",
    "Policy is missing credential categories or transcript boundary rules",
    { categories, boundary_rule: policy.boundary_rule },
  );

  assertCondition(
    policy.integration?.privacy_guard === "scripts/privacy_guard.py" &&
      policy.integration?.codex_sync === "scripts/sync_codex_memory_data.py" &&
      policy.integration?.audit_gate === "scan_repo_privacy" &&
      policy.phase_boundary?.manifest_generation_deferred_to === "S03 P3" &&
      policy.phase_boundary?.connector_implementation_deferred_to === "S04" &&
      policy.phase_boundary?.does_not_create_ui === true,
    "s03p2_policy_integration_boundary",
    "Policy integrates credential check into sync/audit and defers manifest, connector and UI work",
    "Policy integration or phase boundary is incomplete",
    { integration: policy.integration, phase_boundary: policy.phase_boundary },
  );
}

function validatePythonCredentialRuntime() {
  const snippet = String.raw`
import importlib.util
import json
from pathlib import Path

repo = Path.cwd()
script = repo / "scripts" / "privacy_guard.py"
spec = importlib.util.spec_from_file_location("privacy_guard", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

credential_text = "\n".join([
    "cookie: sessionid=" + "abcdef1234567890abcdef",
    "session_token = " + "sess_" + "abcdef1234567890",
    "password = " + "StrongPass1234",
    "api_key = " + "sk-" + "s03p2testsecret1234567890",
    "refresh_token = " + "rt_" + "abcdef1234567890abcdef",
    "private_key = " + "-----BEGIN " + "PRIVATE KEY-----\n" + "abcdef1234567890" + "\n-----END " + "PRIVATE KEY-----",
])
ordinary_transcript = (
    "User: token budget is high and the API key policy should be documented. "
    "Assistant: explain that credentials are excluded while ordinary transcript remains memory."
)
hits = module.credential_exclusion_hits(credential_text, source="synthetic_s03p2")
ordinary_hits = module.credential_exclusion_hits(ordinary_transcript, source="ordinary_transcript")
redacted, counts = module.redact_credentials_in_text(credential_text)
raised = False
try:
    module.assert_no_credentials(credential_text, source="synthetic_s03p2")
except module.PrivacyViolation:
    raised = True

print(json.dumps({
    "categories": sorted({hit["category"] for hit in hits}),
    "ordinary_hit_count": len(ordinary_hits),
    "redacted_includes_secret_marker": "[REDACTED_CREDENTIAL]" in redacted,
    "redaction_counts": counts,
    "assert_raises": raised,
}, ensure_ascii=False, sort_keys=True))
`;
  const result = run("python3", ["-c", snippet], { cwd: repoRoot, timeout: 60000 });
  const parsed = JSON.parse(result.stdout.trim());
  assertCondition(
    ["api_keys", "cookies", "oauth_tokens", "passwords", "private_keys", "session_tokens"].every((category) => parsed.categories.includes(category)) &&
      parsed.ordinary_hit_count === 0 &&
      parsed.redacted_includes_secret_marker === true &&
      parsed.assert_raises === true,
    "s03p2_python_credential_runtime",
    "privacy_guard blocks credential samples, redacts them and does not block ordinary transcript",
    "privacy_guard credential runtime behavior is incomplete",
    parsed,
  );
}

function validateSyncAuditIntegration() {
  validateTextFile("scripts/privacy_guard.py");
  validateTextFile("scripts/sync_codex_memory_data.py");
  const privacy = readRepoFile("scripts/privacy_guard.py");
  const sync = readRepoFile("scripts/sync_codex_memory_data.py");
  assertCondition(
    hasAll(privacy, [
      "credential_exclusion_hits",
      "assert_no_credentials",
      "redact_credentials_in_text",
      "scan_repo_privacy",
      "credential_is_not_memory",
    ]),
    "s03p2_privacy_guard_surface",
    "privacy_guard exposes credential exclusion scan, assertion, redaction and audit integration",
    "privacy_guard is missing S03 P2 credential exclusion surface",
  );

  assertCondition(
    hasAll(sync, [
      "credential_exclusion_hits",
      "redact_credentials_in_text",
      "credentials_not_transcript",
      "credential_boundary",
    ]),
    "s03p2_sync_integration",
    "Codex sync references the shared credential exclusion scanner while preserving transcript sync",
    "Codex sync is missing S03 P2 credential exclusion integration",
  );

  const scan = run("python3", ["scripts/privacy_guard.py", "--database-dir", ".", "--scan-only"], {
    cwd: repoRoot,
    timeout: 120000,
  });
  const parsed = JSON.parse(scan.stdout.trim().slice(scan.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.high_risk_secret_hit_count === 0,
    "s03p2_repo_audit_scan",
    "Repository privacy audit scan passes with no credential hits",
    "Repository privacy audit scan found credential hits",
    parsed,
  );
}

function validateHumanAndMachineState() {
  if (currentStateIsS03P3()) {
    pass(
      "s03p2_human_machine_later_s03p3_state",
      "Current human and machine state has advanced from S03 P2 into S03 P3",
    );
    return;
  }

  const humanEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  validateTextFile(humanPagePath);
  const humanPage = readRepoFile(humanPagePath);
  assertCondition(
    hasAll(humanPage, [
      "凭证排除说明",
      taskId,
      acceptanceId,
      status,
      "credential is not memory",
      "credentials_not_transcript",
      "普通 transcript 可以进入公开 raw",
      "cookie",
      "session token",
      "password",
      "api key",
      "private key",
      "oauth token",
      "browser credential store",
      "No GitHub main upload in this phase",
      "下一步是 S03 P3",
    ]),
    "s03p2_human_page",
    "Human page explains credentials-not-transcript boundary without raw manifest row details",
    "Human credential page is incomplete",
  );

  assertCondition(
    hasAll(humanEntry, [
      "当前阶段是 S03 P2",
      taskId,
      acceptanceId,
      status,
      "credential_exclusion_policy.v1_2_s03_p2.json",
      "credential is not memory",
      "普通 transcript",
      "下一步只允许进入 S03 P3",
      "No GitHub main upload in this phase",
    ]),
    "s03p2_human_entry_state",
    "Human quick entry records S03 P2 state and next S03 P3 gate",
    "Human quick entry is missing S03 P2 state",
  );

  assertCondition(
    hasAll(overview, [
      "S03 P2 已完成",
      "credential is not memory",
      "credentials_not_transcript",
      "普通 transcript",
      "凭证 pattern 导致 gate fail",
      "下一步是 S03 P3",
    ]),
    "s03p2_overview_state",
    "Overview records S03 P2 credential exclusion and next S03 P3 gate",
    "Overview is missing S03 P2 state",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S03 P2",
      policyPath,
      "scripts/privacy_guard.py",
      "scripts/sync_codex_memory_data.py",
      "credential is not memory",
      "下一步是 S03 P3",
    ]),
    "s03p2_machine_readme",
    "Machine README records S03 P2 machine policy and next gate",
    "Machine README is missing S03 P2 state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S03 P2 已完成",
      policyPath,
      "credential is not memory",
      "credentials_not_transcript",
      "普通 transcript",
      "下一步是 S03 P3",
    ]),
    "s03p2_sync_readme",
    "Sync README records S03 P2 credential exclusion and next S03 P3 gate",
    "Sync README is missing S03 P2 state",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S03 P2",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S03 P1 已通过",
      "下一步是 S03 P3",
      "No GitHub main upload in this phase",
    ]),
    "s03p2_run_gate_readme",
    "Run gate README records S03 P2 validator, artifact and next S03 P3 gate",
    "Run gate README is missing S03 P2 state",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S03 P2 Credential Exclusion",
      taskId,
      acceptanceId,
      status,
      validatorName,
      policyPath,
      humanPagePath,
      "credential is not memory",
      "credentials_not_transcript",
      "ordinary transcript is memory",
      "No complex UI",
      "No S03 P3 manifest generation",
      "No connector implementation",
      "No GitHub main upload in this phase",
      "pending S03 P3",
    ]),
    "s03p2_review_artifact",
    "Review artifact records S03 P2 acceptance, files, boundaries and next gate",
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
        "memory_atlas_v1_2_s03_p2_credential_exclusion.md",
        "credential_exclusion_policy.v1_2_s03_p2.json",
        "credential is not memory",
        "S03 P2",
        "pending S03 P3",
        "No GitHub main upload in this phase",
      ]),
      `s03p2_records_${name}`,
      `${name} records S03 P2 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S03 P2 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s03p2_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s03p2_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S03 P2 branch",
    { branch, branchName },
  );

  const remoteDev = run("git", ["ls-remote", "--heads", "origin", branchName], {
    cwd: worktreeRoot,
    timeout: 60000,
  }).stdout.trim();
  assertCondition(
    remoteDev === "",
    "s03p2_no_remote_development_branch",
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
    file.startsWith("OpenAIDatabase/data/public_raw/") && file !== "OpenAIDatabase/data/public_raw/README.md"
  ));
  const forbiddenUiChanges = changed.filter((file) => (
    file.startsWith("OpenAIDatabase/apps/memory-atlas/src/")
  ));
  const forbiddenOpenChanges = changed.filter((file) => forbiddenPrefixes.some((prefix) => file.startsWith(prefix)));

  assertCondition(
    outside.length === 0,
    "s03p2_open_diff_scope",
    "Open diff is limited to S03 P2 policy, privacy guard, sync/audit, human page, validator and records",
    "Open diff contains files outside S03 P2 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenPublicRawChanges.length === 0 &&
      forbiddenUiChanges.length === 0 &&
      forbiddenOpenChanges.length === 0,
    "s03p2_no_raw_or_ui_open_changes",
    "S03 P2 open diff does not add raw transcripts, modify raw archive files or create UI",
    "S03 P2 open diff includes forbidden raw/UI changes",
    { changed, forbiddenPublicRawChanges, forbiddenUiChanges, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateCredentialPolicy();
  validatePythonCredentialRuntime();
  validateSyncAuditIntegration();
  validateHumanAndMachineState();
  validateReviewArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s03_p2",
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
    validator: "validate_memory_atlas_v1_2_s03_p2",
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
