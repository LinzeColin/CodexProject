#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const worktreeRoot = path.resolve(repoRoot, "..");
const checks = [];
const requireLocalApps = process.env.MEMORY_ATLAS_REQUIRE_LOCAL_APPS === "1";
const port = Number(process.env.MEMORY_ATLAS_WHOLE_PROJECT_PORT || 4177);

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

function readAppFile(relativePath) {
  return fs.readFileSync(path.join(appRoot, relativePath), "utf8");
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
    maxBuffer: 64 * 1024 * 1024,
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

function outputTail(result) {
  return {
    stdout: result.stdout.slice(-6000),
    stderr: result.stderr.slice(-6000),
  };
}

function findPython() {
  const candidates = [
    process.env.MEMORY_ATLAS_PYTHON,
    path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
    "python3",
  ].filter(Boolean);
  for (const candidate of candidates) {
    const result = spawnSync(candidate, ["--version"], { encoding: "utf8", stdio: "pipe" });
    if (result.status === 0) return candidate;
  }
  throw new Error("No usable Python executable found");
}

const python = findPython();

function runJsonAudit(name, args, evidence) {
  const result = run(python, args, { cwd: repoRoot });
  const parsed = parseJsonOutput(result.stdout);
  assertCondition(
    parsed?.status === "PASS",
    name,
    evidence,
    `${args.join(" ")} did not return PASS JSON`,
    outputTail(result),
  );
  return parsed;
}

function runPartValidators() {
  const validators = [
    ["part1_stage0", "validate_memory_atlas_part1_stage0.cjs"],
    ["part2_stage1", "validate_memory_atlas_part2_stage1.cjs"],
    ["part3_stage2", "validate_memory_atlas_part3_stage2.cjs"],
    ["part4_stage3", "validate_memory_atlas_part4_stage3.cjs"],
    ["part5_stage4", "validate_memory_atlas_part5_stage4.cjs"],
    ["part6_stage5", "validate_memory_atlas_part6_stage5.cjs"],
    ["part7_stage6", "validate_memory_atlas_part7_stage6.cjs"],
    ["part8_stage7", "validate_memory_atlas_part8_stage7.cjs"],
    ["part9_stage8", "validate_memory_atlas_part9_stage8.cjs"],
    ["part10_stage9", "validate_memory_atlas_part10_stage9.cjs"],
  ];

  for (const [name, scriptName] of validators) {
    const result = run(process.execPath, [path.join(appRoot, "scripts", scriptName)], { cwd: appRoot });
    const parsed = parseJsonOutput(result.stdout);
    assertCondition(
      parsed?.status === "PASS",
      `whole_project_${name}_passed`,
      `${scriptName} returned PASS`,
      `${scriptName} did not return PASS JSON`,
      {
        checkCount: parsed?.checks?.length ?? null,
        part: parsed?.part ?? null,
        stage: parsed?.stage ?? null,
        scope: parsed?.scope ?? parsed?.phases ?? null,
      },
    );
  }
}

function runFrontendBuild() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "whole_project_frontend_dependencies_ready",
    "TypeScript and Vite CLIs are present in app node_modules",
    "TypeScript or Vite CLI is missing from app node_modules",
    { tsc, vite },
  );
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "whole_project_frontend_build_passed",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create required dist files",
  );
}

function runPythonValidation() {
  run(python, [
    "-m",
    "py_compile",
    "scripts/build_agent_context_pack.py",
    "scripts/sync_codex_memory_data.py",
    "scripts/build_memory_atlas_data.py",
    "scripts/audit_memory_atlas_release.py",
    "scripts/audit_memory_atlas_acceptance.py",
    "scripts/audit_memory_atlas_visual_acceptance.py",
  ], { cwd: repoRoot });
  pass("whole_project_python_compile_passed", "Core OpenAIDatabase and Memory Atlas scripts compile under the selected Python runtime", { python });

  const testResult = run(python, ["-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], { cwd: repoRoot });
  pass("whole_project_unittest_discover_passed", "OpenAIDatabase unittest discover completed successfully", outputTail(testResult));
}

function runReleaseAudits() {
  const publishDir = path.join(appRoot, "dist");
  const visual = runJsonAudit(
    "whole_project_visual_acceptance_passed",
    ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot],
    "Visual acceptance passed across Memory Atlas final visual surfaces",
  );
  const release = runJsonAudit(
    "whole_project_release_audit_passed",
    ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", publishDir],
    "Release audit passed against current production dist",
  );
  const acceptanceArgs = ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", publishDir];
  if (requireLocalApps) acceptanceArgs.push("--require-local-apps");
  const acceptance = runJsonAudit(
    requireLocalApps ? "whole_project_acceptance_with_local_apps_passed" : "whole_project_acceptance_passed",
    acceptanceArgs,
    requireLocalApps
      ? "Overall acceptance passed and installed local apps/runtime match current git HEAD"
      : "Overall acceptance passed against current production dist",
  );
  const cloudflare = runJsonAudit(
    "whole_project_cloudflare_offline_preflight_passed",
    ["scripts/preflight_cloudflare_pages_access.py", "--repo-root", repoRoot, "--publish-dir", publishDir],
    "Cloudflare Pages + Access offline preflight passed without live deploy",
  );

  pass("whole_project_release_audit_summary", "Release/visual/overall/offline Cloudflare gates completed", {
    visualChecks: visual.checks?.length ?? null,
    releaseFileCount: release.file_count ?? null,
    overallChecks: acceptance.checks?.length ?? null,
    cloudflareChecks: cloudflare.checks?.length ?? null,
    requireLocalApps,
  });
}

function validateRoadmapFinalAcceptanceCoverage() {
  const app = readAppFile("src/App.tsx");
  const i18nPath = path.join(appRoot, "src/i18n/zh-CN.ts");
  const i18n = fs.existsSync(i18nPath) ? fs.readFileSync(i18nPath, "utf8") : "";
  const uiSource = `${app}\n${i18n}`;
  const galaxy = readAppFile("src/components/GalaxyScene.tsx");
  const obsidian = readAppFile("src/components/ObsidianGraphScene.tsx");
  const visualFlags = readAppFile("src/config/visualFlags.ts");
  const css = readAppFile("src/styles.css");
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  const releaseAudit = readRepoFile("scripts/audit_memory_atlas_release.py");
  const acceptanceAudit = readRepoFile("scripts/audit_memory_atlas_acceptance.py");
  const homeNavigationReady =
    app.includes('{ key: "home", label: "记忆总览", icon: Home }') ||
    (app.includes('{ key: "home", label: uiCopy.navigation.views.home, icon: Home }') &&
      i18n.includes('home: "记忆总览"'));

  assertCondition(
    homeNavigationReady && hasAll(app, [
      "function HomeOverviewView",
      "Memory Weather",
      "层级资产",
      "主题分类",
      "priority",
      "function SearchReview",
      "总结与迭代",
      "data-proposal-only=\"true\"",
      "proposal_only_pending_agent_apply",
    ]) && hasAll(uiSource, [
      "Next Best Actions",
    ]) && hasAll(galaxy, [
      "Production Memory Starfield Flow Field",
      "Flow Field",
      "Memory Terrain v2",
      "galaxy-roi-gradient-panel",
    ]) && hasAll(obsidian, [
      "Local Graph Budget",
      "data-label-rule",
    ]) && hasAll(visualFlags, [
      'DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield"',
      'DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river"',
      '"legacy"',
    ]) && hasAll(css, [
      ".home-overview-view",
      ".data-guide-canvas",
      ".memory-river-canvas",
      ".galaxy-roi-gradient-panel",
    ]),
    "whole_project_roadmap_final_acceptance_runtime_covered",
    "Runtime covers default overview, help/action/detail surfaces, proposal-only adjustments, search/review/summary, visual data map, Memory River, Memory Starfield, Obsidian, ROI gradients, and rollback flags",
    "Runtime does not cover one or more roadmap final acceptance surfaces",
  );
  assertCondition(
    hasAll(visualAudit, [
      "memory_home_default_overview_ready",
      "memory_home_preview_widgets_ready",
      "data_guide_framework_ready",
      "stage9_1_obsidian_graph_iteration_ready",
      "stage9_2_visual_semantics_enrichment_ready",
    ]) && hasAll(releaseAudit, [
      "public_redacted_read_only_visualization",
      "direct_frontend_mutation_of_active_memory",
      "FORBIDDEN_TEXT_PATTERNS",
      "PRIVATE KEY",
      "sk-[A-Za-z0-9_-]{20,}",
    ]) && hasAll(acceptanceAudit, [
      "writeback_proposal_only",
      "memory_atlas_visual_acceptance",
      "cloudflare_pages_access_preflight",
      "local_app_launcher_contract",
    ]),
    "whole_project_roadmap_final_acceptance_audited",
    "Visual, release, and overall audits cover the roadmap final acceptance and safety boundaries",
    "Audit coverage is missing roadmap final acceptance or safety boundary checks",
  );
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_whole_project_review.md");

  for (let part = 1; part <= 10; part += 1) {
    assertCondition(
      packageSource.includes(`"validate:part${part}-`) && fs.existsSync(path.join(repoRoot, "docs/reviews", part === 10 ? "memory_atlas_v1_1_5_part10_stage9_review.md" : `memory_atlas_v1_1_5_part${part}_stage${part - 1}_review.md`)),
      `whole_project_part${part}_review_gate_registered`,
      `Part ${part} package script and review document are present`,
      `Part ${part} package script or review document is missing`,
    );
  }

  assertCondition(
    packageSource.includes('"validate:whole-project": "node scripts/validate_memory_atlas_whole_project.cjs"'),
    "whole_project_package_script_current",
    "Package scripts expose validate:whole-project",
    "validate:whole-project package script is missing",
  );
  assertCondition(
    hasAll(review, [
      "Whole-project review is review-passed",
      "validate:whole-project",
      "Part 1-10",
      "Roadmap v2 final acceptance",
      "No GitHub main upload",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No direct active-memory writeback",
      "final remote ancestry",
    ]),
    "whole_project_review_doc_current",
    "Whole-project review doc records full scope, validation, safety boundaries, runtime finding, and upload gate",
    "Whole-project review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Whole-Project Review",
      "`validate:whole-project`",
      "Part 1-10",
      "Roadmap v2 final acceptance",
      "No GitHub main upload",
    ]),
    "whole_project_changelog_current",
    "Changelog records whole-project review status and non-goals",
    "Changelog does not record whole-project review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 整项目复审",
      "validate:whole-project",
      "Part 1-10",
      "本地 app runtime",
      "未上传 GitHub main",
    ]),
    "whole_project_delivery_record_current",
    "Delivery record records whole-project review and local runtime follow-up gate",
    "Delivery record does not record whole-project review status",
  );
  assertCondition(
    hasAll(model, [
      "## 32. Whole-Project 整项目复审门槛",
      "状态：`whole_project_review_passed`",
      "validate:whole-project",
      "Part 1-10",
      "Roadmap v2 final acceptance",
      "Application Support runtime",
      "final remote ancestry",
    ]),
    "whole_project_model_parameters_current",
    "Model parameters record whole-project review gate, runtime requirement, safety boundaries, and final upload gate",
    "Model parameters do not record whole-project review gate",
  );
}

function runGovernanceChangedOnlySync() {
  const scriptPath = path.join(worktreeRoot, "scripts/validate_governance_sync.py");
  if (!fs.existsSync(scriptPath)) {
    pass("whole_project_governance_changed_only_skipped", "Root governance sync script is not expanded in this sparse checkout");
    return;
  }
  const result = run("python3", ["scripts/validate_governance_sync.py", "--changed-only", "--base-ref", "origin/main", "--semantic"], { cwd: worktreeRoot });
  pass("whole_project_governance_changed_only_sync_passed", "Diff-driven governance sync validation passed for OpenAIDatabase changes", outputTail(result));
}

function validateGitAndUploadBoundary() {
  const head = run("git", ["rev-parse", "HEAD"], { cwd: worktreeRoot }).stdout.trim();
  const status = run("git", ["status", "--short", "--branch"], { cwd: worktreeRoot }).stdout.trim();
  const remote = run("git", ["remote", "get-url", "origin"], { cwd: worktreeRoot }).stdout.trim();
  const aheadBehind = run("git", ["rev-list", "--left-right", "--count", "HEAD...origin/main"], { cwd: worktreeRoot }).stdout.trim();
  const [ahead, behind] = aheadBehind.split(/\s+/).map((value) => Number(value));
  assertCondition(
    remote.includes("LinzeColin/CodexProject.git"),
    "whole_project_canonical_remote",
    "origin remote points at LinzeColin/CodexProject",
    "origin remote is not canonical LinzeColin/CodexProject",
    { remote },
  );
  pass("whole_project_git_upload_boundary_recorded", "GitHub main upload remains blocked until final clean tree and remote ancestry checks", {
    head,
    status,
    ahead,
    behind,
  });
}

function httpGet(url, timeoutMs = 800) {
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
    await httpGet(`http://127.0.0.1:${port}`);
    throw new Error(`port ${port} still responds after whole-project validation`);
  } catch (error) {
    if (String(error.message || "").includes("still responds")) throw error;
  }
  pass("whole_project_preview_cleanup", `Port ${port} is not responding after whole-project validation`);
}

(async () => {
  try {
    runPartValidators();
    runFrontendBuild();
    runPythonValidation();
    runReleaseAudits();
    validateRoadmapFinalAcceptanceCoverage();
    validateDocsAndRecords();
    runGovernanceChangedOnlySync();
    validateGitAndUploadBoundary();
    await assertPortClosed();
    console.log(JSON.stringify({
      status: "PASS",
      scope: "Memory Atlas v1.1.5 whole-project review",
      requireLocalApps,
      checks,
    }, null, 2));
  } catch (error) {
    checks.push({
      name: "whole_project_review",
      status: "FAIL",
      evidence: error.message,
      details: error.details || {
        stdout: error.stdout?.slice(-6000),
        stderr: error.stderr?.slice(-6000),
      },
    });
    console.error(JSON.stringify({
      status: "FAIL",
      scope: "Memory Atlas v1.1.5 whole-project review",
      requireLocalApps,
      checks,
    }, null, 2));
    process.exit(1);
  }
})();
