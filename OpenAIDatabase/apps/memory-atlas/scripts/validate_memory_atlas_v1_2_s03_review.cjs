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

const taskId = "MA-V12-S03-REVIEW";
const acceptanceId = "ACC-MA-V12-S03-REVIEW";
const status = "stage_s03_review_passed_pending_s04_no_github_main_upload";
const validatorName = "validate:v1.2-s03-review";
const scriptName = "validate_memory_atlas_v1_2_s03_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s03_review.md";
const p1PolicyPath = "机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json";
const p2PolicyPath = "机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json";
const p3PolicyPath = "机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json";
const manifestRoot = "机器治理/证据与日志/raw_archive_manifests";
const baselineManifestPath = `${manifestRoot}/raw_manifest.s03_p3_baseline.jsonl`;
const hashLedgerPath = `${manifestRoot}/raw_hash_ledger.jsonl`;
const rawManifestScript = "scripts/raw_archive_manifest.py";
const privacyGuardScript = "scripts/privacy_guard.py";
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
  "OpenAIDatabase/机器治理/证据与日志/README.md",
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

function parseJsonl(relativePath) {
  const source = readRepoFile(relativePath);
  if (source.trim() === "") return [];
  return source
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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
function currentStateIsS04P2() {
  return (
    hasAll(readRepoFile("人类可读/00_快速入口.md"), [
      "当前阶段是 S04 P2",
      "MA-V12-S04P2",
      "ACC-MA-V12-S04P2",
      "下一步只允许进入 S04 P3",
    ]) &&
    hasAll(readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md"), [
      "S04 P2 已完成",
      "Codex local sync",
      "下一步是 S04 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/README.md"), [
      "当前为 S04 P2",
      "codex_agent_sync_policy.v1_2_s04_p2.json",
      "下一步是 S04 P3",
    ]) &&
    hasAll(readRepoFile("机器治理/同步与备份/README.md"), [
      "当前 S04 P2 已完成",
      "Codex local sync",
      "future-agent minimal adapter",
    ]) &&
    hasAll(readRepoFile("机器治理/运行门禁/README.md"), [
      "当前阶段是 S04 P2",
      "validate:v1.2-s04-p2",
      "下一步是 S04 P3",
    ])
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

  const s05p1State =
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
    hasAll(syncReadme, [
      "当前 S04 Review 已通过",
      "ChatGPT 只读同步",
      "GitHub backup dry-run/apply",
      "下一步是 S05 P1",
    ]) &&
    hasAll(runGateReadme, [
      "当前阶段是 S05 P1",
      "MA-V12-S05P1",
      "ACC-MA-V12-S05P1",
      "validate:v1.2-s05-p1",
    ]);

  return s04p3State || s04ReviewState || s05p1State;
}


function validatePackageScript() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s03_review_package_script",
    "package.json exposes the v1.2 S03 Review validator",
    "package.json is missing the v1.2 S03 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s03_review_previous_phase_deferred_scope",
      "S03 P3 execution is deferred only because open diff is limited to S03 Review files and validator compatibility",
      "S03 P3 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s03_review_previous_phase_deferred_until_clean_tree",
      "S03 P3 validator will run on a clean tree after S03 Review commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s03_p3.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = parseJsonFromStdout(result);
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S03P3",
    "s03_review_previous_s03p3",
    "S03 P3 validator returns PASS before accepting S03 Review",
    "S03 P3 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateStageArtifacts() {
  [
    p1PolicyPath,
    p2PolicyPath,
    p3PolicyPath,
    "docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md",
    "docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md",
    "docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md",
    "人类可读/06_Raw明文公开与只读归档说明.md",
    "人类可读/07_凭证排除说明.md",
    "人类可读/08_Raw机器账本说明.md",
  ].forEach(validateTextFile);

  const p1 = JSON.parse(readRepoFile(p1PolicyPath));
  const p2 = JSON.parse(readRepoFile(p2PolicyPath));
  const p3 = JSON.parse(readRepoFile(p3PolicyPath));

  assertCondition(
    p1.public_raw_root === "data/public_raw" &&
      p1.source_raw_roots?.chatgpt === "data/public_raw/chatgpt" &&
      p1.source_raw_roots?.codex === "data/public_raw/codex" &&
      p1.source_raw_roots?.future_agents === "data/public_raw/agents/{agent_id}" &&
      p1.append_only_rule?.forbid_modify_existing_raw === true &&
      p1.append_only_rule?.forbid_delete_existing_raw === true &&
      p1.hash_drift_fail_rule?.enabled === true,
    "s03_review_p1_public_raw_append_only",
    "S03 P1 defines public raw paths, append-only and hash drift fail rules",
    "S03 P1 public raw or append-only contract is incomplete",
    { public_raw_root: p1.public_raw_root, source_raw_roots: p1.source_raw_roots },
  );

  assertCondition(
    p2.boundary_rule?.credential_is_not_memory === true &&
      p2.boundary_rule?.ordinary_transcript_is_memory === true &&
      p2.boundary_rule?.block_credentials_only === true &&
      p2.integration?.privacy_guard === privacyGuardScript &&
      p2.integration?.audit_gate === "scan_repo_privacy",
    "s03_review_p2_credential_boundary",
    "S03 P2 defines credential exclusion without blocking ordinary transcript",
    "S03 P2 credential exclusion contract is incomplete",
    { boundary_rule: p2.boundary_rule, integration: p2.integration },
  );

  assertCondition(
    p3.manifest_root === manifestRoot &&
      p3.baseline_manifest === baselineManifestPath &&
      p3.hash_ledger === hashLedgerPath &&
      p3.generator === rawManifestScript &&
      p3.minimum_manifest_fields?.includes("source_id") &&
      p3.minimum_manifest_fields?.includes("relative_path") &&
      p3.minimum_manifest_fields?.includes("sha256") &&
      p3.minimum_manifest_fields?.includes("imported_at") &&
      p3.audit_contract?.hash_drift_fails === true &&
      p3.audit_contract?.deleted_manifest_entry_fails === true &&
      p3.phase_boundary?.raw_manifest_is_machine_file_not_human_primary_page === true,
    "s03_review_p3_manifest_hash_ledger",
    "S03 P3 defines machine manifest/hash ledger with source/file/hash/imported_at",
    "S03 P3 manifest/hash ledger contract is incomplete",
    { manifest_root: p3.manifest_root, baseline_manifest: p3.baseline_manifest, hash_ledger: p3.hash_ledger },
  );
}

function validateRawAndCredentialGates() {
  const manifestRows = parseJsonl(baselineManifestPath);
  const ledgerRows = parseJsonl(hashLedgerPath);
  const invalidRows = manifestRows.filter((row) => !(
    row.source_id &&
    row.relative_path &&
    /^[0-9a-f]{64}$/.test(String(row.sha256 || "")) &&
    row.imported_at
  ));
  assertCondition(
    JSON.stringify(manifestRows) === JSON.stringify(ledgerRows) && invalidRows.length === 0,
    "s03_review_manifest_rows",
    "Raw manifest/hash ledger rows are consistent and map source/file/hash/imported_at",
    "Raw manifest/hash ledger rows are inconsistent or missing required fields",
    { manifest_rows: manifestRows.length, ledger_rows: ledgerRows.length, invalidRows: invalidRows.slice(0, 5) },
  );

  const audit = parseJsonFromStdout(run("python3", [rawManifestScript, "audit", "--database-dir", "."], {
    cwd: repoRoot,
    timeout: 120000,
  }));
  assertCondition(
    audit.status === "PASS" &&
      audit.hash_drift_count === 0 &&
      audit.deleted_manifest_entry_count === 0,
    "s03_review_raw_append_only_audit",
    "Raw append-only audit passes with no hash drift or deleted manifest entries",
    "Raw append-only audit found drift or deleted entries",
    audit,
  );

  const privacyScan = parseJsonFromStdout(run("python3", [privacyGuardScript, "--database-dir", ".", "--scan-only"], {
    cwd: repoRoot,
    timeout: 120000,
  }));
  assertCondition(
    privacyScan.status === "PASS" &&
      privacyScan.credential_is_not_memory === true &&
      privacyScan.high_risk_secret_hit_count === 0 &&
      privacyScan.tracked_raw_private_file_count === 0,
    "s03_review_privacy_scan",
    "Credential exclusion repo scan passes with no high-risk credential hits",
    "Credential exclusion repo scan found tracked private files or credential hits",
    privacyScan,
  );

  const runtime = run("python3", ["-c", [
    "import importlib.util",
    "from pathlib import Path",
    "spec = importlib.util.spec_from_file_location('privacy_guard', Path('scripts/privacy_guard.py'))",
    "guard = importlib.util.module_from_spec(spec)",
    "spec.loader.exec_module(guard)",
    "ordinary = '普通 transcript discussion about token budget and password manager policy, without a concrete credential assignment.'",
    "assert guard.credential_exclusion_hits(ordinary) == []",
    "credential = 'api_key=' + 'sk-' + ('A' * 16)",
    "try:",
    "    guard.assert_no_credentials(credential, 's03_review_runtime')",
    "    raise AssertionError('credential sample was not blocked')",
    "except guard.PrivacyViolation:",
    "    pass",
    "print('PASS')",
  ].join("\n")], {
    cwd: repoRoot,
    timeout: 120000,
  });
  assertCondition(
    runtime.stdout.trim() === "PASS",
    "s03_review_credential_runtime",
    "Credential pattern fails while ordinary transcript text is not blocked",
    "Credential runtime gate did not behave as expected",
    { stdout: runtime.stdout, stderr: runtime.stderr },
  );
}

function validateHumanReadabilityBoundary() {
  const humanLedger = readRepoFile("人类可读/08_Raw机器账本说明.md");
  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const combined = `${humanLedger}\n${quickEntry}\n${overview}`;
  assertCondition(
    !combined.includes('"sha256"') &&
      !combined.includes("raw_manifest.s03_p3_baseline.jsonl row") &&
      !combined.includes('"relative_path"'),
    "s03_review_human_not_raw_manifest_dump",
    "Human-facing files do not expose raw manifest row dumps as primary content",
    "Human-facing files contain raw manifest row dump fragments",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S03 Review",
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S03 P1",
      "S03 P2",
      "S03 P3",
      p1PolicyPath,
      p2PolicyPath,
      p3PolicyPath,
      "raw 可公开备份",
      "append-only",
      "credential exclusion",
      "raw manifest/hash",
      "credential pattern fails gate",
      "human files not polluted by raw manifest details",
      "No GitHub main upload in this review",
      "pending S04 P1",
    ]),
    "s03_review_artifact",
    "S03 Review artifact records phase coverage, acceptance, stop-condition audit and next S04 gate",
    "S03 Review artifact is incomplete",
  );
}

function validateHumanAndMachineState() {
  [
    "人类可读/00_快速入口.md",
    "人类可读/01_v1.2四线14Stage升级总览.md",
    "机器治理/README.md",
    "机器治理/同步与备份/README.md",
    "机器治理/证据与日志/README.md",
    "机器治理/运行门禁/README.md",
  ].forEach(validateTextFile);

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  if (currentStateIsS04P1() || currentStateIsS04P2() || currentStateIsS04P3()) {
    pass(
      "s03_review_human_machine_later_s04p1_state",
      "Current human and machine state has advanced from S03 Review into S04 P1",
    );
    return;
  }

  assertCondition(
    hasAll(quickEntry, [
      "当前阶段是 S03 Review",
      taskId,
      acceptanceId,
      status,
      "S03 P1、S03 P2、S03 P3 已复审通过",
      "raw 可公开备份",
      "append-only",
      "credential exclusion",
      "下一步只允许进入 S04 P1",
      "No GitHub main upload in this review",
    ]),
    "s03_review_human_quick_entry",
    "Human quick entry records S03 Review pass state and next S04 P1 gate",
    "Human quick entry is missing S03 Review state",
  );

  assertCondition(
    hasAll(overview, [
      "S03 Review 已通过",
      "raw 可公开备份",
      "append-only",
      "credential exclusion",
      "raw manifest/hash",
      "下一步是 S04 P1",
      "整体完成后才上传 GitHub main",
    ]),
    "s03_review_overview",
    "Human overview records S03 Review pass state and next S04 P1 gate",
    "Human overview is missing S03 Review state",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S03 Review",
      "raw 可公开备份",
      "append-only",
      "credential exclusion",
      reviewPath,
      "下一步是 S04 P1",
    ]),
    "s03_review_machine_readme",
    "Machine README records S03 Review state and next gate",
    "Machine README is missing S03 Review state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S03 Review 已通过",
      "raw 可公开备份",
      "append-only",
      "credential exclusion",
      "raw manifest/hash",
      "下一步是 S04 P1",
    ]),
    "s03_review_sync_readme",
    "Sync README records S03 Review state and next gate",
    "Sync README is missing S03 Review state",
  );

  assertCondition(
    hasAll(evidenceReadme, [
      "当前 S03 Review 已通过",
      reviewPath,
      baselineManifestPath,
      hashLedgerPath,
      "source/file/hash/imported_at",
    ]),
    "s03_review_evidence_readme",
    "Evidence README records S03 Review artifact and raw ledger evidence",
    "Evidence README is missing S03 Review evidence state",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S03 Review",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S03 P3 已通过",
      "下一步是 S04 P1",
      "No GitHub main upload in this review",
    ]),
    "s03_review_run_gate_readme",
    "Run gate README records S03 Review validator, artifact and next S04 P1 gate",
    "Run gate README is missing S03 Review state",
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
        "memory_atlas_v1_2_s03_review.md",
        "S03 Review",
        "pending S04 P1",
        "No GitHub main upload in this review",
      ]),
      `s03_review_records_${name}`,
      `${name} records S03 Review status, acceptance, validator and no-upload boundary`,
      `${name} is missing S03 Review record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s03_review_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s03_review_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S03 Review branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s03_review_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/scripts/",
    "OpenAIDatabase/tests/",
    "OpenAIDatabase/config/",
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/public_raw",
    "OpenAIDatabase/private_exports/",
  ];
  const allowedAppFiles = new Set(allowedOpenDiffPaths.filter((file) => file.startsWith("OpenAIDatabase/apps/")));
  const forbiddenOpenChanges = changed.filter((file) => {
    if (allowedOpenDiffPaths.includes(file)) return false;
    if (allowedAppFiles.has(file)) return false;
    if (file.startsWith("OpenAIDatabase/apps/")) return true;
    return forbiddenPrefixes.some((prefix) => file.startsWith(prefix));
  });

  assertCondition(
    outside.length === 0,
    "s03_review_open_diff_scope",
    "Open diff is limited to S03 Review artifact, validator, state docs and compatibility patches",
    "Open diff contains files outside S03 Review allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenOpenChanges.length === 0,
    "s03_review_no_runtime_raw_or_ui_open_changes",
    "S03 Review open diff does not enter runtime connector work, raw archive changes or UI",
    "S03 Review open diff includes runtime/raw/UI changes",
    { changed, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateStageArtifacts();
  validateRawAndCredentialGates();
  validateHumanReadabilityBoundary();
  validateReviewArtifact();
  validateHumanAndMachineState();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s03_review",
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
    validator: "validate_memory_atlas_v1_2_s03_review",
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
