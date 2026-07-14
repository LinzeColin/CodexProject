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

const taskId = "MA-V12-S03P3";
const acceptanceId = "ACC-MA-V12-S03P3";
const status = "phase_s03_p3_machine_ledger_completed_pending_s03_review";
const validatorName = "validate:v1.2-s03-p3";
const scriptName = "validate_memory_atlas_v1_2_s03_p3.cjs";
const rawManifestScript = "scripts/raw_archive_manifest.py";
const policyPath = "机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json";
const manifestRoot = "机器治理/证据与日志/raw_archive_manifests";
const baselineManifestPath = `${manifestRoot}/raw_manifest.s03_p3_baseline.jsonl`;
const hashLedgerPath = `${manifestRoot}/raw_hash_ledger.jsonl`;
const humanPagePath = "人类可读/08_Raw机器账本说明.md";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s03_p3_machine_ledger.md";
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
  `OpenAIDatabase/apps/memory-atlas/scripts/${scriptName}`,
  `OpenAIDatabase/${rawManifestScript}`,
  `OpenAIDatabase/${policyPath}`,
  `OpenAIDatabase/${baselineManifestPath}`,
  `OpenAIDatabase/${hashLedgerPath}`,
  `OpenAIDatabase/${humanPagePath}`,
  `OpenAIDatabase/${reviewPath}`,
  "OpenAIDatabase/tests/test_s03p3_raw_manifest.py",
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


function currentStateIsS03Review() {
  if (currentStateIsS04P1() || currentStateIsS04P2() || currentStateIsS04P3()) return true;

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

function validatePackageScript() {
  const packageJson = JSON.parse(readRepoFile("apps/memory-atlas/package.json"));
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s03p3_package_script",
    "package.json exposes the v1.2 S03 P3 validator",
    "package.json is missing the v1.2 S03 P3 validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validatePreviousPhaseGate() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  if (changed.length > 0) {
    assertCondition(
      outside.length === 0,
      "s03p3_previous_phase_deferred_scope",
      "S03 P2 execution is deferred only because open diff is limited to S03 P3 files",
      "S03 P2 execution cannot be deferred with unrelated OpenAIDatabase changes",
      { changed, outside, allowedOpenDiffPaths },
    );
    pass(
      "s03p3_previous_phase_deferred_until_clean_tree",
      "S03 P2 validator will run on a clean tree after S03 P3 commit",
      { changed },
    );
    return;
  }

  const result = run("node", ["scripts/validate_memory_atlas_v1_2_s03_p2.cjs"], {
    cwd: appRoot,
    timeout: 240000,
  });
  const parsed = JSON.parse(result.stdout.trim().slice(result.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" && parsed.acceptance_id === "ACC-MA-V12-S03P2",
    "s03p3_previous_s03p2",
    "S03 P2 validator returns PASS before accepting S03 P3",
    "S03 P2 validator did not return PASS",
    { status: parsed.status, acceptance_id: parsed.acceptance_id },
  );
}

function validateLedgerPolicy() {
  validateTextFile(policyPath);
  const policy = JSON.parse(readRepoFile(policyPath));
  assertCondition(
    policy.policy_id === "memory_atlas_raw_manifest_ledger_policy_v1_2_s03_p3" &&
      policy.task_id === taskId &&
      policy.acceptance_id === acceptanceId &&
      policy.status === status,
    "s03p3_policy_identity",
    "Raw manifest ledger policy records S03 P3 identity and status",
    "Raw manifest ledger policy identity is incomplete",
    {
      policy_id: policy.policy_id,
      task_id: policy.task_id,
      acceptance_id: policy.acceptance_id,
      status: policy.status,
    },
  );

  assertCondition(
    policy.manifest_root === manifestRoot &&
      policy.baseline_manifest === baselineManifestPath &&
      policy.hash_ledger === hashLedgerPath &&
      policy.minimum_manifest_fields?.includes("source_id") &&
      policy.minimum_manifest_fields?.includes("relative_path") &&
      policy.minimum_manifest_fields?.includes("sha256") &&
      policy.minimum_manifest_fields?.includes("imported_at") &&
      policy.audit_contract?.hash_drift_fails === true &&
      policy.audit_contract?.deleted_manifest_entry_fails === true,
    "s03p3_policy_manifest_contract",
    "Policy defines machine manifest/hash ledger paths, minimum row fields and fail-closed audit rules",
    "Policy is missing S03 P3 manifest/hash/audit contract",
    { policy },
  );

  assertCondition(
    policy.phase_boundary?.previous_phase_required === "S03 P2" &&
      policy.phase_boundary?.next_gate === "S03 Review" &&
      policy.phase_boundary?.connector_implementation_deferred_to === "S04" &&
      policy.phase_boundary?.does_not_ingest_transcripts_in_this_phase === true &&
      policy.phase_boundary?.raw_manifest_is_machine_file_not_human_primary_page === true &&
      policy.phase_boundary?.no_github_main_upload === true,
    "s03p3_policy_phase_boundary",
    "Policy keeps S03 P3 bounded to machine ledger work and defers review/connector/upload",
    "Policy phase boundary is incomplete",
    { phase_boundary: policy.phase_boundary },
  );
}

function validateRawManifestRuntime() {
  validateTextFile(rawManifestScript);
  const testResult = run("python", ["-B", "-m", "unittest", "OpenAIDatabase.tests.test_s03p3_raw_manifest", "-q"], {
    cwd: worktreeRoot,
    timeout: 120000,
  });
  assertCondition(
    testResult.stdout.includes("OK") || testResult.stderr.includes("OK"),
    "s03p3_python_unit_tests",
    "S03 P3 raw manifest unit tests pass",
    "S03 P3 raw manifest unit tests did not report OK",
    { stdout: testResult.stdout.slice(-2000), stderr: testResult.stderr.slice(-2000) },
  );

  const audit = run("python3", [rawManifestScript, "audit", "--database-dir", "."], {
    cwd: repoRoot,
    timeout: 120000,
  });
  const parsed = JSON.parse(audit.stdout.trim().slice(audit.stdout.indexOf("{")));
  assertCondition(
    parsed.status === "PASS" &&
      parsed.hash_drift_count === 0 &&
      parsed.deleted_manifest_entry_count === 0,
    "s03p3_repo_append_only_audit",
    "Repository raw append-only audit passes with no hash drift or deleted manifest entries",
    "Repository raw append-only audit found drift or deleted entries",
    parsed,
  );
}

function validateMachineLedgerFiles() {
  const manifestRows = parseJsonl(baselineManifestPath);
  const ledgerRows = parseJsonl(hashLedgerPath);
  assertCondition(
    JSON.stringify(manifestRows) === JSON.stringify(ledgerRows),
    "s03p3_baseline_manifest_matches_hash_ledger",
    "Baseline raw manifest and hash ledger are generated from the same rows",
    "Baseline raw manifest and hash ledger differ",
    {
      baseline_manifest_rows: manifestRows.length,
      hash_ledger_rows: ledgerRows.length,
    },
  );

  const invalidRows = manifestRows.filter((row) => !(
    row.source_id &&
    row.relative_path &&
    /^[0-9a-f]{64}$/.test(String(row.sha256 || "")) &&
    row.imported_at
  ));
  assertCondition(
    invalidRows.length === 0,
    "s03p3_manifest_rows_minimum_fields",
    "Every raw manifest row maps source/file/hash/imported_at; empty baseline is allowed when no raw transcript exists",
    "Raw manifest rows are missing source_id, relative_path, sha256 or imported_at",
    { row_count: manifestRows.length, invalidRows: invalidRows.slice(0, 5) },
  );
}

function validateHumanAndMachineState() {
  if (currentStateIsS03Review()) {
    pass(
      "s03p3_human_machine_later_s03_review_state",
      "Current human and machine state has advanced from S03 P3 into S03 Review",
    );
    return;
  }

  const humanEntry = readRepoFile("人类可读/00_快速入口.md");
  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  const machineReadme = readRepoFile("机器治理/README.md");
  const syncReadme = readRepoFile("机器治理/同步与备份/README.md");
  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  const runGateReadme = readRepoFile("机器治理/运行门禁/README.md");

  validateTextFile(humanPagePath);
  const humanPage = readRepoFile(humanPagePath);
  assertCondition(
    hasAll(humanPage, [
      "Raw机器账本说明",
      taskId,
      acceptanceId,
      status,
      "raw manifest",
      "hash ledger",
      "source/file/hash/imported_at",
      "机器文件",
      "不是人类主要页面",
      "No GitHub main upload in this phase",
      "下一步是 S03 Review",
    ]),
    "s03p3_human_page",
    "Human page explains machine ledger without exposing raw manifest row details as the primary page",
    "Human S03 P3 page is incomplete",
  );

  assertCondition(
    !humanPage.includes('"sha256"') && !humanPage.includes("raw_manifest.s03_p3_baseline.jsonl row"),
    "s03p3_human_page_not_manifest_row_dump",
    "Human page avoids raw manifest row dumps",
    "Human S03 P3 page exposes manifest row details",
  );

  assertCondition(
    hasAll(humanEntry, [
      "当前阶段是 S03 P3",
      taskId,
      acceptanceId,
      status,
      "raw_manifest.s03_p3_baseline.jsonl",
      "raw_hash_ledger.jsonl",
      "下一步只允许进入 S03 Review",
      "No GitHub main upload in this phase",
    ]),
    "s03p3_human_entry_state",
    "Human quick entry records S03 P3 state and next S03 Review gate",
    "Human quick entry is missing S03 P3 state",
  );

  assertCondition(
    hasAll(overview, [
      "S03 P3 已完成",
      "raw manifest/hash 可生成",
      "source/file/hash/imported_at",
      "修改已有 raw 文件导致 validation fail",
      "下一步是 S03 Review",
    ]),
    "s03p3_overview_state",
    "Overview records S03 P3 machine ledger and next S03 Review gate",
    "Overview is missing S03 P3 state",
  );

  assertCondition(
    hasAll(machineReadme, [
      "当前为 S03 P3",
      policyPath,
      rawManifestScript,
      hashLedgerPath,
      "下一步是 S03 Review",
    ]),
    "s03p3_machine_readme",
    "Machine README records S03 P3 ledger policy and next gate",
    "Machine README is missing S03 P3 state",
  );

  assertCondition(
    hasAll(syncReadme, [
      "当前 S03 P3 已完成",
      policyPath,
      rawManifestScript,
      "raw manifest/hash",
      "下一步是 S03 Review",
    ]),
    "s03p3_sync_readme",
    "Sync README records S03 P3 raw manifest/hash ledger",
    "Sync README is missing S03 P3 state",
  );

  assertCondition(
    hasAll(evidenceReadme, [
      "当前 S03 P3 已完成",
      baselineManifestPath,
      hashLedgerPath,
      "source/file/hash/imported_at",
      "机器文件",
    ]),
    "s03p3_evidence_readme",
    "Evidence README records S03 P3 machine ledger files",
    "Evidence README is missing S03 P3 ledger state",
  );

  assertCondition(
    hasAll(runGateReadme, [
      "当前阶段是 S03 P3",
      taskId,
      acceptanceId,
      validatorName,
      reviewPath,
      "前置 S03 P2 已通过",
      "下一步是 S03 Review",
      "No GitHub main upload in this phase",
    ]),
    "s03p3_run_gate_readme",
    "Run gate README records S03 P3 validator, artifact and next S03 Review gate",
    "Run gate README is missing S03 P3 state",
  );
}

function validateReviewArtifact() {
  validateTextFile(reviewPath);
  const source = readRepoFile(reviewPath);
  assertCondition(
    hasAll(source, [
      "Memory Atlas v1.2 S03 P3 Machine Ledger",
      taskId,
      acceptanceId,
      status,
      validatorName,
      policyPath,
      rawManifestScript,
      baselineManifestPath,
      hashLedgerPath,
      "raw manifest/hash can be generated",
      "source/file/hash/imported_at",
      "Hash drift or deleted manifest entries fail validation",
      "No GitHub main upload in this phase",
      "pending S03 Review",
    ]),
    "s03p3_review_artifact",
    "Review artifact records S03 P3 acceptance, files, boundaries and next gate",
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
        "memory_atlas_v1_2_s03_p3_machine_ledger.md",
        "raw_manifest_ledger_policy.v1_2_s03_p3.json",
        "raw_archive_manifest.py",
        "S03 P3",
        "pending S03 Review",
        "No GitHub main upload in this phase",
      ]),
      `s03p3_records_${name}`,
      `${name} records S03 P3 status, acceptance, validator and no-upload boundary`,
      `${name} is missing S03 P3 record fragments`,
    );
  });
}

function validateGitBoundary() {
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    remote === "git@github.com:LinzeColin/CodexProject.git",
    "s03p3_canonical_remote",
    "origin points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );

  const branch = run("git", ["branch", "--show-current"], { cwd: worktreeRoot }).stdout.trim();
  assertCondition(
    branch === branchName || branch === "main",
    "s03p3_local_branch",
    "Current branch is either the local v1.2 work branch or main for final reconciliation",
    "Current branch is not an approved S03 P3 branch",
    { branch, branchName },
  );

  const remoteDevQuery = queryRemoteDevBranch();
  const remoteDev = remoteDevQuery.output;
  assertCondition(
    remoteDev === "",
    "s03p3_no_remote_development_branch",
    "No remote v1.2 development branch exists",
    "Remote v1.2 development branch exists",
    { branchName, remoteDev, remote_query_method: remoteDevQuery.method, origin_error: remoteDevQuery.originError, origin_stderr: remoteDevQuery.originStderr },
  );
}

function validateOpenDiffBoundary() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  const forbiddenPrefixes = [
    "OpenAIDatabase/data/raw",
    "OpenAIDatabase/data/raw_encrypted",
    "OpenAIDatabase/private_exports/",
    "OpenAIDatabase/apps/memory-atlas/src/",
  ];
  const forbiddenPublicRawChanges = changed.filter((file) => file.startsWith("OpenAIDatabase/data/public_raw/"));
  const forbiddenOpenChanges = changed.filter((file) => forbiddenPrefixes.some((prefix) => file.startsWith(prefix)));

  assertCondition(
    outside.length === 0,
    "s03p3_open_diff_scope",
    "Open diff is limited to S03 P3 machine ledger, audit script, validator and records",
    "Open diff contains files outside S03 P3 allowed scope",
    { changed, outside, allowedOpenDiffPaths },
  );

  assertCondition(
    forbiddenPublicRawChanges.length === 0 && forbiddenOpenChanges.length === 0,
    "s03p3_no_raw_or_ui_open_changes",
    "S03 P3 open diff does not modify public raw files, private raw areas or UI",
    "S03 P3 open diff includes forbidden raw/UI changes",
    { changed, forbiddenPublicRawChanges, forbiddenOpenChanges },
  );
}

function main() {
  validatePackageScript();
  validatePreviousPhaseGate();
  validateLedgerPolicy();
  validateRawManifestRuntime();
  validateMachineLedgerFiles();
  validateHumanAndMachineState();
  validateReviewArtifact();
  validateRecords();
  validateGitBoundary();
  validateOpenDiffBoundary();
  console.log(JSON.stringify({
    status: "PASS",
    validator: "validate_memory_atlas_v1_2_s03_p3",
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
    validator: "validate_memory_atlas_v1_2_s03_p3",
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
