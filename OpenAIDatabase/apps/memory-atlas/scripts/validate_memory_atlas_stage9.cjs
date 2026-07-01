#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const port = Number(process.env.MEMORY_ATLAS_STAGE9_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;

const packagePath = path.join(appRoot, "package.json");
const changelogPath = path.join(repoRoot, "CHANGELOG.md");
const deliveryRecordPath = path.join(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
const modelParametersPath = path.join(repoRoot, "docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
const stage9ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage9_review.md");
const stage91ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage9_1_review.md");
const stage92ReviewPath = path.join(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage9_2_review.md");
const visualAcceptancePath = path.join(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py");

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

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
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
    throw new Error(`port ${port} still responds after Stage 9 validation`);
  } catch (error) {
    if (String(error.message || "").includes("still responds")) throw error;
  }
  pass("stage9_preview_cleanup", `Port ${port} is not responding after Stage 9 whole-stage validation`);
}

function validateDocsAndContracts() {
  const packageSource = fs.readFileSync(packagePath, "utf8");
  const changelog = fs.readFileSync(changelogPath, "utf8");
  const delivery = fs.readFileSync(deliveryRecordPath, "utf8");
  const model = fs.readFileSync(modelParametersPath, "utf8");
  const stage9Review = fs.readFileSync(stage9ReviewPath, "utf8");
  const stage91Review = fs.readFileSync(stage91ReviewPath, "utf8");
  const stage92Review = fs.readFileSync(stage92ReviewPath, "utf8");
  const visualAcceptance = fs.readFileSync(visualAcceptancePath, "utf8");

  assertCondition(
    hasAll(packageSource, [
      '"validate:stage9-obsidian": "node scripts/validate_stage9_obsidian_iteration.cjs"',
      '"validate:stage9-visual-semantics": "node scripts/validate_stage9_visual_semantics.cjs"',
      '"validate:stage9": "node scripts/validate_memory_atlas_stage9.cjs"',
    ]),
    "stage9_package_scripts_current",
    "Package scripts expose Stage 9.1, Stage 9.2, and whole-stage validators",
    "Stage 9 package scripts are incomplete",
  );
  assertCondition(
    hasAll(stage91Review, [
      "Stage 9.1 is review-passed",
      "9.1.1 Local Graph",
      "9.1.2 Label Rules",
      "9.1.3 Galaxy Sync",
      "No raw/private/cookie/session/secret fields were introduced",
    ]) && hasAll(stage92Review, [
      "Stage 9.2 is review-passed",
      "9.2.1 Memory Terrain v2",
      "9.2.2 Memory Weather v2",
      "9.2.3 ROI Visual Gradient",
      "No direct frontend writeback was added",
    ]),
    "stage9_phase_reviews_complete",
    "Stage 9.1 and Stage 9.2 phase reviews both record PASS boundaries",
    "Stage 9 phase review docs are incomplete",
  );
  assertCondition(
    hasAll(stage9Review, [
      "Stage 9 is review-passed",
      "9.1 Obsidian Graph E Iteration",
      "9.2 Visual Semantics Enrichment",
      "validate:stage9-obsidian",
      "validate:stage9-visual-semantics",
      "validate:stage9",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No direct frontend writeback",
      "GitHub main upload",
    ]),
    "stage9_review_doc_current",
    "Stage 9 whole-stage review records phase coverage, validation, boundaries, and upload gate",
    "Stage 9 whole-stage review doc is incomplete",
  );
  assertCondition(
    hasAll(model, [
      "stage_9_1_obsidian_graph_iteration_passed",
      "stage_9_2_visual_semantics_enrichment_passed",
      "stage_9_whole_stage_review_passed",
      "validate:stage9",
      "validate:stage9-obsidian",
      "validate:stage9-visual-semantics",
      "direct_frontend_mutation_of_active_memory == false",
    ]),
    "stage9_model_parameters_current",
    "Model parameters record Stage 9 whole-stage review thresholds and safety boundaries",
    "Model parameters lack Stage 9 whole-stage review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Stage 9.1 Obsidian Graph E Iteration",
      "完成 Memory Atlas v1.1.5 Stage 9.2 Visual Semantics Enrichment",
      "完成 Memory Atlas v1.1.5 Stage 9 整体复审",
      "Stage 9 整阶段复审通过",
      "GitHub main 上传",
    ]),
    "stage9_delivery_record_current",
    "Delivery record marks Stage 9 phases and whole-stage review complete",
    "Delivery record does not mark Stage 9 whole-stage review complete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Stage 9 Whole-Stage Review",
      "Completed the Stage 9 whole-stage review",
      "`validate:stage9`",
      "No Cloudflare live deploy",
      "No raw/private data access",
      "No direct writeback",
    ]),
    "stage9_changelog_current",
    "Changelog records Stage 9 whole-stage review and preserves non-goal boundaries",
    "Changelog lacks Stage 9 whole-stage review status or boundary statement",
  );
  assertCondition(
    hasAll(visualAcceptance, [
      "stage9_1_obsidian_graph_iteration_ready",
      "stage9_2_visual_semantics_enrichment_ready",
    ]),
    "stage9_visual_acceptance_hooks_current",
    "Visual acceptance audit covers both Stage 9.1 and Stage 9.2 hooks",
    "Visual acceptance audit does not cover both Stage 9 phase hooks",
  );
}

(async () => {
  try {
    const stage91 = runStageValidator("stage9_1_validator_passed", "validate_stage9_obsidian_iteration.cjs");
    const stage92 = runStageValidator("stage9_2_validator_passed", "validate_stage9_visual_semantics.cjs");
    const visualAcceptance = runPythonAudit(
      "stage9_visual_acceptance_passed",
      ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot],
      "Visual acceptance passed with Stage 9.1 and Stage 9.2 hooks",
    );
    const release = runPythonAudit(
      "stage9_release_audit_passed",
      ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")],
      "Release audit passed on production dist generated by Stage 9 validators",
    );
    const acceptance = runPythonAudit(
      "stage9_overall_acceptance_passed",
      ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")],
      "Overall Memory Atlas acceptance passed after Stage 9 whole-stage review",
    );
    validateDocsAndContracts();
    await assertPortClosed();
    console.log(JSON.stringify({
      status: "PASS",
      stage: "9",
      outputDir: {
        stage9_1: stage91.outputDir,
        stage9_2: stage92.outputDir,
      },
      checks,
      visualAcceptanceChecks: visualAcceptance.checks?.length ?? null,
      releaseFileCount: release.file_count ?? null,
      overallAcceptanceChecks: acceptance.checks?.length ?? null,
    }, null, 2));
  } catch (error) {
    checks.push({
      name: "stage9_whole_stage_review",
      status: "FAIL",
      evidence: error.message,
      details: error.details || { stdout: error.stdout, stderr: error.stderr },
    });
    console.error(JSON.stringify({ status: "FAIL", stage: "9", checks }, null, 2));
    process.exitCode = 1;
  }
})();
