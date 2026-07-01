#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE8_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;

const packagePath = path.join(appRoot, "package.json");
const changelogPath = path.join(repoRoot, "CHANGELOG.md");
const deliveryRecordPath = path.join(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
const modelParametersPath = path.join(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
const releaseNotesPath = path.join(repoRoot, "docs/release_notes/memory_atlas_v1_1_5_stage8_release_notes.md");
const stage8ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage8_review.md");
const stage81ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage8_1_review.md");
const stage82ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage8_2_review.md");
const stage82AcceptancePath = path.join(repoRoot, "docs/acceptance/memory_atlas_v1_1_5_stage8_2_release_safety.md");

const checks = [];

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
    env: options.env || process.env,
    encoding: "utf8",
    stdio: "pipe",
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function parseJsonOutput(stdout) {
  const trimmed = stdout.trim();
  if (!trimmed) return null;
  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace < 0 || lastBrace < firstBrace) return null;
  return JSON.parse(trimmed.slice(firstBrace, lastBrace + 1));
}

function runStageValidator(name, scriptName) {
  const result = run(process.execPath, [path.join(appRoot, "scripts", scriptName)], { cwd: appRoot });
  const parsed = parseJsonOutput(result.stdout);
  assertCondition(
    parsed?.status === "PASS",
    name,
    `${scriptName} passed with ${parsed?.checks?.length ?? "unknown"} checks`,
    `${scriptName} did not return PASS JSON`,
    { stdout: result.stdout.slice(-4000), stderr: result.stderr.slice(-4000) },
  );
  return parsed;
}

function runPythonAudit(name, args, evidence) {
  const result = run("python3", args, { cwd: repoRoot });
  const parsed = parseJsonOutput(result.stdout);
  assertCondition(
    parsed?.status === "PASS",
    name,
    evidence,
    `${args.join(" ")} did not return PASS JSON`,
    { stdout: result.stdout.slice(-4000), stderr: result.stderr.slice(-4000) },
  );
  return parsed;
}

async function httpGet(url, timeoutMs = 800) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode || 0));
    });
    request.setTimeout(timeoutMs, () => request.destroy(new Error(`timeout waiting for ${url}`)));
    request.on("error", reject);
  });
}

async function assertPortClosed() {
  try {
    await httpGet(targetUrl);
    throw new Error(`port ${port} still responds after Stage 8 validation`);
  } catch (error) {
    if (String(error.message || "").includes("still responds")) throw error;
  }
  pass("stage8_preview_cleanup", `Port ${port} is not responding after Stage 8 whole-stage validation`);
}

function validateDocsAndContracts() {
  const packageSource = fs.readFileSync(packagePath, "utf8");
  const changelog = fs.readFileSync(changelogPath, "utf8");
  const delivery = fs.readFileSync(deliveryRecordPath, "utf8");
  const model = fs.readFileSync(modelParametersPath, "utf8");
  const releaseNotes = fs.readFileSync(releaseNotesPath, "utf8");
  const stage8Review = fs.readFileSync(stage8ReviewPath, "utf8");
  const stage81Review = fs.readFileSync(stage81ReviewPath, "utf8");
  const stage82Review = fs.readFileSync(stage82ReviewPath, "utf8");
  const stage82Acceptance = fs.readFileSync(stage82AcceptancePath, "utf8");

  assertCondition(
    hasAll(packageSource, [
      '"validate:stage8-local-app": "node scripts/validate_stage8_local_app_packaging.cjs"',
      '"validate:stage8-release-safety": "node scripts/validate_stage8_release_safety.cjs"',
      '"validate:stage8": "node scripts/validate_memory_atlas_stage8.cjs"',
    ]),
    "stage8_package_scripts_current",
    "Package scripts expose Stage 8.1, Stage 8.2, and whole-stage validators",
    "Stage 8 package scripts are incomplete",
  );
  assertCondition(
    hasAll(stage81Review, [
      "Stage 8.1 is review-passed",
      "8.1.1 local build",
      "8.1.2 launcher check",
      "8.1.3 default route check",
      "No raw/private/cookie/session/secret fields were introduced",
    ]) && hasAll(stage82Review, [
      "Stage 8.2 is review-passed",
      "feature flag rollback",
      "acceptance audit",
      "release notes",
      "No direct frontend writeback was added",
    ]),
    "stage8_phase_reviews_complete",
    "Stage 8.1 and Stage 8.2 phase reviews both record PASS boundaries",
    "Stage 8 phase review docs are incomplete",
  );
  assertCondition(
    hasAll(stage82Acceptance, [
      "8.2.1 Feature Flag Rollback",
      "8.2.2 Acceptance Audit",
      "8.2.3 Release Notes",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
    ]),
    "stage8_acceptance_doc_current",
    "Stage 8.2 acceptance doc records rollback, audit, notes, and safety boundaries",
    "Stage 8.2 acceptance doc is incomplete",
  );
  assertCondition(
    hasAll(stage8Review, [
      "Stage 8 is review-passed",
      "8.1 Local App Packaging",
      "8.2 Release Safety",
      "validate:stage8-local-app",
      "validate:stage8-release-safety",
      "Cloudflare preflight is offline-only",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No direct frontend writeback",
      "GitHub main upload",
    ]),
    "stage8_review_doc_current",
    "Stage 8 whole-stage review records phase coverage, validation, boundaries, and next upload gate",
    "Stage 8 whole-stage review doc is incomplete",
  );
  assertCondition(
    hasAll(model, [
      "stage_8_whole_stage_review_passed",
      "validate:stage8",
      "validate:stage8-local-app",
      "validate:stage8-release-safety",
      "offline Cloudflare Pages + Access preflight",
      "direct_frontend_mutation_of_active_memory == false",
    ]),
    "stage8_model_parameters_current",
    "Model parameters record Stage 8 whole-stage review thresholds and safety boundaries",
    "Model parameters lack Stage 8 whole-stage review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Stage 8 整体复审",
      "Stage 8 整阶段复审通过",
      "Stage 9 后续增强迭代",
    ]),
    "stage8_delivery_record_current",
    "Delivery record marks Stage 8 reviewed and moves the next product gate to Stage 9",
    "Delivery record does not mark Stage 8 whole-stage review complete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Stage 8 Whole-Stage Review",
      "Completed the Stage 8 whole-stage review",
      "`validate:stage8`",
      "No Cloudflare live deploy",
      "No raw/private data access",
      "No direct writeback",
    ]),
    "stage8_changelog_current",
    "Changelog records Stage 8 whole-stage review and preserves non-goal boundaries",
    "Changelog lacks Stage 8 whole-stage review status or boundary statement",
  );
  assertCondition(
    hasAll(releaseNotes, [
      "Memory Atlas v1.1.5 Stage 8 Release Notes",
      "Stage 8 整体复审已完成",
      "回滚",
      "Cloudflare",
      "proposal-only",
    ]),
    "stage8_release_notes_current",
    "Release notes state Stage 8 review completion and retain rollback and safety guidance",
    "Release notes are missing Stage 8 completion or rollback guidance",
  );
}

(async () => {
  try {
    const stage81 = runStageValidator("stage8_1_validator_passed", "validate_stage8_local_app_packaging.cjs");
    const stage82 = runStageValidator("stage8_2_validator_passed", "validate_stage8_release_safety.cjs");
    const preflight = runPythonAudit(
      "stage8_cloudflare_preflight_offline_passed",
      ["scripts/preflight_cloudflare_pages_access.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")],
      "Offline Cloudflare Pages + Access preflight passed on production dist without live deploy env",
    );
    validateDocsAndContracts();
    await assertPortClosed();
    console.log(JSON.stringify({
      status: "PASS",
      outputDir: {
        stage8_1: stage81.outputDir,
        stage8_2: stage82.outputDir,
      },
      checks,
      cloudflarePreflightChecks: preflight.checks?.length ?? null,
    }, null, 2));
  } catch (error) {
    checks.push({
      name: "stage8_whole_stage_review",
      status: "FAIL",
      evidence: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
    });
    console.error(JSON.stringify({ status: "FAIL", checks }, null, 2));
    process.exitCode = 1;
  }
})();

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}
