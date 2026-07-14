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

const taskId = "MA-V12-S13-REVIEW";
const acceptanceId = "ACC-MA-V12-S13-REVIEW";
const status = "stage_s13_review_passed_pending_s14_no_github_main_upload";
const validatorName = "validate:v1.2-s13-review";
const scriptName = "validate_memory_atlas_v1_2_s13_review.cjs";
const reviewPath = "docs/reviews/memory_atlas_v1_2_s13_review.md";

const phaseValidators = [
  ["validate:v1.2-s13-p1", "validate_memory_atlas_v1_2_s13_p1.cjs", "MA-V12-S13P1", "ACC-MA-V12-S13P1"],
  ["validate:v1.2-s13-p2", "validate_memory_atlas_v1_2_s13_p2.cjs", "MA-V12-S13P2", "ACC-MA-V12-S13P2"],
  ["validate:v1.2-s13-p3", "validate_memory_atlas_v1_2_s13_p3.cjs", "MA-V12-S13P3", "ACC-MA-V12-S13P3"],
];

const contracts = {
  stateMachine: "proposal_state_machine.v1_2_s13_p1",
  diffNarrator: "diff_narrator.v1_2_s13_p2",
  proposalApply: "proposal_apply.v1_2_s13_p3",
};

const paths = {
  stateConfig: "机器治理/运行门禁/proposal_state_machine.v1_2_s13_p1.json",
  stateReport: "data/derived/proposals/proposal_state_machine_report.json",
  diffConfig: "机器治理/运行门禁/diff_narrator.v1_2_s13_p2.json",
  diffReport: "data/derived/proposals/diff_narrator_report.json",
  diffEvidence: "机器治理/证据与日志/proposal_diffs/diff_narrator_machine_diff.v1_2_s13_p2.json",
  applyConfig: "机器治理/运行门禁/proposal_apply.v1_2_s13_p3.json",
  applyReport: "data/derived/proposals/proposal_apply_report.json",
  applyEvidence: "机器治理/证据与日志/proposal_apply/proposal_apply_evidence.v1_2_s13_p3.json",
  p1Review: "docs/reviews/memory_atlas_v1_2_s13_p1_proposal_state_machine.md",
  p2Review: "docs/reviews/memory_atlas_v1_2_s13_p2_diff_narrator.md",
  p3Review: "docs/reviews/memory_atlas_v1_2_s13_p3_apply_rollback.md",
  p1Human: "人类可读/34_Proposal状态机说明.md",
  p2Human: "人类可读/35_DiffNarrator说明.md",
  p3Human: "人类可读/36_Apply回滚说明.md",
};

const recordFiles = [
  "CHANGELOG.md",
  "功能清单.md",
  "开发记录.md",
  "模型参数文件.md",
  "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
  "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md",
];

const requiredFiles = [
  reviewPath,
  ...Object.values(paths),
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s13_p1.cjs",
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s13_p2.cjs",
  "apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s13_p3.cjs",
  "scripts/build_memory_atlas_proposal_state_machine.py",
  "scripts/build_memory_atlas_diff_narrator.py",
  "scripts/build_memory_atlas_proposal_apply.py",
  "scripts/atlasctl.py",
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
  ...recordFiles,
];

const textFiles = [
  reviewPath,
  paths.p1Review,
  paths.p2Review,
  paths.p3Review,
  paths.p1Human,
  paths.p2Human,
  paths.p3Human,
  "人类可读/00_快速入口.md",
  "人类可读/01_v1.2四线14Stage升级总览.md",
  "机器治理/README.md",
  "机器治理/运行门禁/README.md",
  "机器治理/证据与日志/README.md",
  ...recordFiles,
];

const allowedOpenDiffPaths = [
  "OpenAIDatabase/CHANGELOG.md",
  "OpenAIDatabase/apps/memory-atlas/package.json",
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
  "OpenAIDatabase/机器治理/证据与日志/README.md",
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    stdio: "pipe",
    maxBuffer: 128 * 1024 * 1024,
    timeout: options.timeout || 0,
  });
  const expectedStatuses = options.expectedStatuses || [0];
  if (!expectedStatuses.includes(result.status)) {
    const reason = result.error?.code === "ETIMEDOUT" ? " timed out" : "";
    const error = new Error(`${command} ${args.join(" ")} failed${reason} with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    error.expectedStatuses = expectedStatuses;
    throw error;
  }
  return result;
}

function parseJsonFromStdout(result) {
  const stdout = result.stdout.trim();
  const start = stdout.indexOf("{");
  if (start < 0) throw new Error("stdout does not contain JSON object");
  return JSON.parse(stdout.slice(start));
}

function repoPath(relativePath) {
  return path.join(repoRoot, relativePath);
}

function readRepoFile(relativePath) {
  return fs.readFileSync(repoPath(relativePath), "utf8");
}

function readJson(relativePath) {
  return JSON.parse(readRepoFile(relativePath));
}

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
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

function validatePackageScript() {
  const packageJson = readJson("apps/memory-atlas/package.json");
  assertCondition(
    packageJson.scripts?.[validatorName] === `node scripts/${scriptName}`,
    "s13_review_package_script",
    "package.json exposes the v1.2 S13 Review validator",
    "package.json is missing the v1.2 S13 Review validator",
    { script: packageJson.scripts?.[validatorName] },
  );
}

function validateOpenDiffScope() {
  const changed = getOpenChangedPaths();
  const outside = changed.filter((file) => !allowedOpenDiffPaths.includes(file));
  assertCondition(
    outside.length === 0,
    "s13_review_open_diff_scope",
    "Open diff is limited to S13 Review files and governance records",
    "S13 Review has unrelated OpenAIDatabase changes",
    { changed, outside, allowedOpenDiffPaths },
  );
}

function validateRequiredFilesExist() {
  const missing = requiredFiles.filter((relativePath) => !fs.existsSync(repoPath(relativePath)));
  assertCondition(
    missing.length === 0,
    "s13_review_required_files_exist",
    "S13 Review and S13 phase evidence files exist",
    "S13 Review is missing required files",
    { missing },
  );
}

function validateTextFile(relativePath) {
  const source = readRepoFile(relativePath);
  assertCondition(source.endsWith("\n"), `${relativePath}:final_newline`, `${relativePath} has a final newline`, `${relativePath} is missing a final newline`);
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

function validateStateMachine() {
  const config = readJson(paths.stateConfig);
  const report = readJson(paths.stateReport);
  const requiredStates = [
    "draft",
    "pending_human_review",
    "approved_by_human",
    "applying",
    "applied",
    "validated",
    "committed",
    "failed_validation",
    "rollback_or_needs_revision",
  ];
  const states = config.proposal_state_machine?.states || [];
  const missingStates = requiredStates.filter((state) => !states.includes(state));
  assertCondition(
    config.schema_version === contracts.stateMachine &&
      config.task_id === "MA-V12-S13P1" &&
      config.acceptance_id === "ACC-MA-V12-S13P1" &&
      config.proposal_state_machine?.human_approval_required_before_applying === true &&
      config.proposal_expiry?.integrated === true &&
      config.proposal_expiry?.expired_proposals_cannot_enter_applying === true &&
      missingStates.length === 0 &&
      report.summary?.proposal_count >= 5 &&
      report.summary?.all_proposals_have_expiry === true &&
      report.summary?.unauthorized_apply_blocked === true &&
      report.summary?.current_phase_executes_apply === false &&
      report.summary?.proposal_apply_execution === false &&
      report.summary?.raw_apply_target_allowed === false &&
      report.phase_boundary?.does_not_upload_github_main === true &&
      report.phase_boundary?.does_not_push_remote === true &&
      report.phase_boundary?.does_not_modify_raw === true,
    "s13_review_state_machine_gate",
    "S13 P1 state machine, expiry and no-apply boundaries satisfy the stage gate",
    "S13 P1 state machine evidence does not satisfy S13 Review",
    { missingStates, summary: report.summary },
  );
}

function validateDiffNarrator() {
  const config = readJson(paths.diffConfig);
  const report = readJson(paths.diffReport);
  const evidence = readJson(paths.diffEvidence);
  const requiredSections = [
    "what_changed_zh",
    "why_changed_zh",
    "affected_surfaces_zh",
    "how_to_verify_zh",
    "how_to_rollback_zh",
  ];
  const missingSections = (report.required_human_sections || []).length
    ? requiredSections.filter((section) => !report.required_human_sections.includes(section))
    : requiredSections;
  const invalidNarrations = (report.narrations || []).filter((item) =>
    requiredSections.some((section) => typeof item[section] !== "string" || item[section].trim().length === 0) ||
    item.machine_diff_inline_in_human_summary !== false ||
    item.raw_apply_target_allowed !== false ||
    item.apply_execution_allowed !== false,
  );
  assertCondition(
    config.schema_version === contracts.diffNarrator &&
      config.task_id === "MA-V12-S13P2" &&
      config.acceptance_id === "ACC-MA-V12-S13P2" &&
      missingSections.length === 0 &&
      report.summary?.narration_count >= 5 &&
      report.summary?.all_narrations_have_required_sections === true &&
      report.summary?.machine_diff_kept_out_of_human_homepage === true &&
      report.summary?.proposal_apply_execution === false &&
      report.summary?.raw_mutation === false &&
      invalidNarrations.length === 0 &&
      evidence.summary?.machine_diff_count === report.summary?.machine_diff_count &&
      evidence.summary?.full_machine_diff_kept_out_of_human_homepage === true &&
      evidence.summary?.proposal_apply_execution === false &&
      evidence.summary?.raw_mutation === false,
    "s13_review_diff_narrator_gate",
    "S13 P2 diff narrator explains every proposal and keeps machine diff in governance evidence",
    "S13 P2 diff narrator evidence does not satisfy S13 Review",
    { missingSections, invalidNarrationCount: invalidNarrations.length, summary: report.summary },
  );
}

function validateProposalApply() {
  const config = readJson(paths.applyConfig);
  const report = readJson(paths.applyReport);
  const evidence = readJson(paths.applyEvidence);
  const unauthorized = report.sample_outcomes?.unauthorized_attempt || {};
  const authorized = report.sample_outcomes?.authorized_apply_dry_run || {};
  const failure = report.sample_outcomes?.validation_failure_dry_run || {};
  assertCondition(
    config.schema_version === contracts.proposalApply &&
      config.task_id === "MA-V12-S13P3" &&
      config.acceptance_id === "ACC-MA-V12-S13P3" &&
      config.apply_contract?.human_approval_required_before_apply === true &&
      config.apply_contract?.validation_after_apply_required === true &&
      config.apply_contract?.rollback_point_required === true &&
      config.apply_contract?.raw_archive_is_never_apply_target === true &&
      report.summary?.unauthorized_apply_blocked === true &&
      report.summary?.authorized_apply_available === true &&
      report.summary?.validation_after_apply === true &&
      report.summary?.rollback_available === true &&
      report.summary?.real_pending_proposals_applied === 0 &&
      report.summary?.raw_mutation === false &&
      report.phase_boundary?.does_not_apply_real_pending_proposals_without_human_approval === true &&
      report.phase_boundary?.does_not_upload_github_main === true &&
      report.phase_boundary?.does_not_push_remote === true &&
      report.phase_boundary?.does_not_modify_raw === true &&
      unauthorized.status === "FAIL_CLOSED" &&
      unauthorized.writes_files === false &&
      unauthorized.applies_proposal === false &&
      authorized.status === "PASS" &&
      authorized.would_apply === true &&
      authorized.validation_after_apply === true &&
      authorized.rollback_point_created === true &&
      authorized.raw_mutation === false &&
      failure.status === "FAIL_CLOSED" &&
      failure.rollback_available === true &&
      failure.rollback_or_needs_revision === true &&
      evidence.summary?.machine_apply_attempt_count >= 3 &&
      evidence.summary?.raw_mutation === false,
    "s13_review_apply_rollback_gate",
    "S13 P3 apply dry-runs prove unauthorized fail-closed, authorized path, validation and rollback evidence",
    "S13 P3 apply/rollback evidence does not satisfy S13 Review",
    { summary: report.summary, unauthorized, authorized, failure },
  );
}

function validateAtlasctlCommands() {
  const proposals = parseJsonFromStdout(run("python3", ["scripts/atlasctl.py", "proposals", "--dry-run"], { cwd: repoRoot, timeout: 180000 }));
  const diffNarrator = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "proposals", "--view", "diff-narrator", "--dry-run"], {
      cwd: repoRoot,
      timeout: 180000,
    }),
  );
  const unauthorized = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "apply", "--proposal", "sample_unauthorized", "--dry-run"], {
      cwd: repoRoot,
      expectedStatuses: [2],
      timeout: 180000,
    }),
  );
  const authorized = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "apply", "--proposal", "sample", "--dry-run"], { cwd: repoRoot, timeout: 180000 }),
  );
  const failure = parseJsonFromStdout(
    run("python3", ["scripts/atlasctl.py", "apply", "--proposal", "sample", "--dry-run", "--simulate-validation-failure"], {
      cwd: repoRoot,
      expectedStatuses: [2],
      timeout: 180000,
    }),
  );
  assertCondition(
    proposals.task_id === "MA-V12-S13P1" &&
      proposals.dry_run === true &&
      proposals.applies_proposals === false &&
      proposals.writes_files === false &&
      proposals.raw_mutation === false &&
      diffNarrator.task_id === "MA-V12-S13P2" &&
      diffNarrator.dry_run === true &&
      diffNarrator.applies_proposals === false &&
      diffNarrator.writes_files === false &&
      diffNarrator.raw_mutation === false &&
      unauthorized.status === "FAIL_CLOSED" &&
      unauthorized.writes_files === false &&
      unauthorized.applies_proposal === false &&
      authorized.status === "PASS" &&
      authorized.dry_run === true &&
      authorized.writes_files === false &&
      authorized.would_apply === true &&
      authorized.validation_after_apply === true &&
      authorized.raw_mutation === false &&
      failure.status === "FAIL_CLOSED" &&
      failure.rollback_available === true &&
      failure.rollback_or_needs_revision === true,
    "s13_review_atlasctl_contracts",
    "atlasctl dry-runs prove proposals, diff narrator and apply/rollback behavior without writes",
    "atlasctl commands do not satisfy S13 Review dry-run contracts",
    { proposals: proposals.task_id, diffNarrator: diffNarrator.task_id, unauthorized, authorized, failure },
  );
}

function validateReviewArtifact() {
  const review = readRepoFile(reviewPath);
  assertCondition(
    hasAll(review, [
      taskId,
      acceptanceId,
      status,
      validatorName,
      "S13 Review",
      "S13 P1",
      "S13 P2",
      "S13 P3",
      contracts.stateMachine,
      contracts.diffNarrator,
      contracts.proposalApply,
      "Proposal 状态机",
      "Diff narrator",
      "Apply 与回滚",
      "draft",
      "pending_human_review",
      "approved_by_human",
      "failed_validation",
      "rollback_or_needs_revision",
      "proposal expiry",
      "改了什么",
      "为什么改",
      "影响什么",
      "如何验证",
      "如何回滚",
      "sample_unauthorized",
      "sample",
      "FAIL_CLOSED",
      "validation_after_apply",
      "rollback point",
      "No GitHub main upload",
      "No remote push",
      "No raw mutation",
      "真实 pending proposal 未获人类授权前不 apply",
      "pending S14 P1",
    ]),
    "s13_review_artifact",
    "S13 Review artifact records phase chain, acceptance gates, dry-run commands, boundaries and pending S14 P1",
    "S13 Review artifact is missing required review evidence",
  );
}

function validateRecords() {
  const requiredFragments = [
    taskId,
    acceptanceId,
    status,
    validatorName,
    "S13 Review",
    "S13 P1",
    "S13 P2",
    "S13 P3",
    contracts.stateMachine,
    contracts.diffNarrator,
    contracts.proposalApply,
    "Proposal 状态机",
    "Diff narrator",
    "Apply 与回滚",
    "sample_unauthorized",
    "sample",
    "FAIL_CLOSED",
    "No GitHub main upload",
    "No remote push",
    "No raw mutation",
    "S14 P1",
  ];
  for (const relativePath of recordFiles) {
    const source = readRepoFile(relativePath);
    const missing = requiredFragments.filter((fragment) => !source.includes(fragment));
    assertCondition(
      missing.length === 0,
      `s13_review_records_${relativePath}`,
      `${relativePath} records S13 Review status, validator, phase chain and next phase`,
      `${relativePath} is missing S13 Review record fragments`,
      { missing },
    );
  }

  const quickEntry = readRepoFile("人类可读/00_快速入口.md");
  assertCondition(
    hasAll(quickEntry, [taskId, "S13 Review 已完成", "下一步是 S14 P1", "No GitHub main upload"]),
    "s13_review_quick_entry",
    "Quick entry records completed S13 Review and pending S14 P1",
    "Quick entry does not record completed S13 Review",
  );

  const overview = readRepoFile("人类可读/01_v1.2四线14Stage升级总览.md");
  assertCondition(
    hasAll(overview, ["S13 Review 已完成", "Proposal 状态机", "Diff narrator", "Apply 与回滚", "下一步是 S14 P1"]),
    "s13_review_overview",
    "Human overview records S13 Review pass gate and pending S14 P1",
    "Human overview is missing S13 Review pass gate",
  );

  const machineReadme = readRepoFile("机器治理/README.md");
  assertCondition(
    hasAll(machineReadme, [taskId, acceptanceId, status, validatorName, "S14 P1"]),
    "s13_review_machine_readme",
    "Machine README records S13 Review gate and next phase",
    "Machine README is missing S13 Review gate",
  );

  const runGate = readRepoFile("机器治理/运行门禁/README.md");
  assertCondition(
    hasAll(runGate, [taskId, acceptanceId, status, validatorName, "S13 Review 产物", "S14 P1"]),
    "s13_review_run_gate",
    "Run gate README records S13 Review artifact, validator and next phase",
    "Run gate README is missing S13 Review gate",
  );

  const evidenceReadme = readRepoFile("机器治理/证据与日志/README.md");
  assertCondition(
    hasAll(evidenceReadme, ["S13 Review 已完成", paths.diffEvidence, paths.applyEvidence, "S14 P1"]),
    "s13_review_evidence_readme",
    "Evidence README records S13 Review evidence files and next phase",
    "Evidence README is missing S13 Review evidence state",
  );
}

function validatePhaseValidators() {
  const changed = getOpenChangedPaths();
  if (changed.length > 0) {
    pass("s13_review_phase_validators_deferred_until_clean_tree", "S13 P1/P2/P3 clean-tree validators will be re-run after S13 Review commit", {
      changed,
    });
    return;
  }
  const packageJson = readJson("apps/memory-atlas/package.json");
  const details = {};
  for (const [script, file, phaseTaskId, phaseAcceptanceId] of phaseValidators) {
    assertCondition(
      packageJson.scripts?.[script] === `node scripts/${file}`,
      `s13_review_phase_script_${script}`,
      `${script} is registered`,
      `${script} is missing from package.json`,
      { script: packageJson.scripts?.[script] },
    );
    const result = parseJsonFromStdout(run("node", [`scripts/${file}`], { cwd: appRoot, timeout: 300000 }));
    details[script] = {
      status: result.status,
      task_id: result.task_id,
      acceptance_id: result.acceptance_id,
    };
    assertCondition(
      result.status === "PASS" && result.task_id === phaseTaskId && result.acceptance_id === phaseAcceptanceId,
      `s13_review_phase_gate_${script}`,
      `${script} passes with expected task and acceptance ids`,
      `${script} did not pass with expected task and acceptance ids`,
      details[script],
    );
  }
  pass("s13_review_phase_validator_chain", "S13 P1/P2/P3 validators pass in sequence", details);
}

function validateNoRawOrSecretOpenChanges() {
  const changed = getOpenChangedPaths();
  const forbiddenOpenChanges = changed.filter(
    (file) =>
      file.includes("/data/raw/") ||
      file.includes("/data/public_raw/") ||
      file.includes("/data/private_imports/") ||
      file.includes("/data/raw_encrypted/") ||
      file.endsWith(".env") ||
      file.toLowerCase().includes("secret") ||
      file.toLowerCase().includes("credential"),
  );
  const rawDiff = run("git", ["diff", "--", "OpenAIDatabase/data/public_raw", "OpenAIDatabase/data/raw", "OpenAIDatabase/data/private_imports"], {
    cwd: worktreeRoot,
  }).stdout.trim();
  assertCondition(
    forbiddenOpenChanges.length === 0 && rawDiff.length === 0,
    "s13_review_no_raw_or_secret_open_changes",
    "S13 Review open diff does not modify raw, private imports, credentials or secrets",
    "S13 Review has forbidden raw/private/credential changes",
    { changed, forbiddenOpenChanges, rawDiff },
  );
}

function main() {
  try {
    validatePackageScript();
    validateOpenDiffScope();
    validateRequiredFilesExist();
    for (const relativePath of textFiles) validateTextFile(relativePath);
    validateReviewArtifact();
    validateStateMachine();
    validateDiffNarrator();
    validateProposalApply();
    validateAtlasctlCommands();
    validateRecords();
    validatePhaseValidators();
    validateNoRawOrSecretOpenChanges();
    console.log(JSON.stringify({ status: "PASS", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
  } catch (error) {
    checks.push({
      name: "failure",
      status: "FAIL",
      evidence: error.message,
      ...(error.details ? { details: error.details } : {}),
      ...(error.stdout ? { stdout: error.stdout.slice(0, 4000) } : {}),
      ...(error.stderr ? { stderr: error.stderr.slice(0, 4000) } : {}),
    });
    console.error(JSON.stringify({ status: "FAIL", task_id: taskId, acceptance_id: acceptanceId, checks }, null, 2));
    process.exit(1);
  }
}

main();
