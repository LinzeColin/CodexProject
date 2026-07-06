#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
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
  });
  if (result.status !== 0) {
    const error = new Error(`${command} ${args.join(" ")} failed with ${result.status}`);
    error.stdout = result.stdout;
    error.stderr = result.stderr;
    throw error;
  }
  return result;
}

function walkFiles(rootDir, skipNames = new Set()) {
  const result = [];
  for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
    if (skipNames.has(entry.name)) continue;
    const fullPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      result.push(...walkFiles(fullPath, skipNames));
    } else {
      result.push(fullPath);
    }
  }
  return result;
}

function validateStage61Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage6_1_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 6.1 is review-passed",
      "6.1.1 Selection Schema",
      "6.1.2 Filter Schema",
      "6.1.3 Sync Actions",
      "Loop Guard",
      "SharedAtlasSelectionState",
      "SharedAtlasFilterState",
      "sharedAtlasReducer",
      "stage6_1_shared_state_store_ready",
      "Stage 6.1 did not",
    ]),
    "part7_phase_6_1_review_current",
    "Stage 6.1 review proves typed shared-state selection/filter/focus schema, sync actions, loop guard, validation evidence and safety boundaries",
    "Stage 6.1 review is incomplete",
  );
}

function validateStage62Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage6_2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 6.2 is review-passed",
      "6.2.1 Explanation Panel",
      "6.2.2 Proposal-only Writeback",
      "6.2.3 Debug Separation",
      "InspectorExplanationPanel",
      "buildWritebackProposalDraft",
      "data-proposal-only=true",
      "data-active-memory-mutation=false",
      "data-debug-lite=closed",
      "stage6_2_inspector_proposal_ready",
      "Stage 6.2 did not",
    ]),
    "part7_phase_6_2_review_current",
    "Stage 6.2 review proves Inspector explanation, proposal-only writeback, Debug separation, validation evidence and safety boundaries",
    "Stage 6.2 review is incomplete",
  );
}

function validateStage6OverallReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage6_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 6 is review-passed",
      "6.1 Shared State Store",
      "6.2 Inspector and Proposal",
      "Integrated Stage 6 Gate",
      "Data boundary",
      "Writeback boundary",
      "validate:shared-state",
      "validate:inspector-proposal",
      "validate:stage6",
      "stage6_1_shared_state_store_ready",
      "stage6_2_inspector_proposal_ready",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
      "No direct frontend writeback was added",
      "The reviewed Stage 6 state is ready to upload",
    ]),
    "part7_stage6_overall_review_current",
    "Stage 6 overall review proves 6.1/6.2 inclusion, integrated acceptance, data/writeback safety boundaries and historical upload gate",
    "Stage 6 overall review is incomplete",
  );
}

function validateSharedStateRuntime() {
  const app = readAppFile("src/App.tsx");
  const css = readAppFile("src/styles.css");
  const state = readAppFile("src/state/sharedAtlasState.ts");

  assertCondition(
    hasAll(state, [
      "export interface SharedAtlasSelectionState",
      "export interface SharedAtlasFilterState",
      "export interface SharedAtlasFocusState",
      "export function sharedAtlasReducer",
      "clearSharedAtlasFilter",
      "roi: SharedAtlasRoiFilter",
      "loopGuard",
      "single-dispatch-reducer",
    ]) && hasAll(app, [
      "useReducer(",
      "sharedAtlasReducer",
      "const timelineTimeRange = sharedState.filters.timeRange",
      "dispatchSharedState({ type: \"select_node\", node, source: activeView })",
      "dispatchSharedState({ type: \"select_time_range\", range, source: \"timeline\" })",
      "dispatchSharedState({ type: \"clear_filter\", key, source: activeView })",
      "data-shared-state={sharedState.schema_version}",
      "data-shared-focus-node={sharedState.focus.home.nodeId ?? \"\"}",
      "data-shared-focus-node={sharedState.focus.galaxy.nodeId ?? \"\"}",
      "data-shared-focus-node={sharedState.focus.timeline.nodeId ?? \"\"}",
      "data-shared-focus-node={sharedState.focus.inspector.nodeId ?? \"\"}",
      "data-sync-revision={sharedState.sync.revision}",
    ]) && hasAll(css, [
      ".lens-state-strip",
      ".home-shared-focus-strip",
    ]),
    "part7_stage6_1_shared_state_runtime",
    "Current runtime exposes shared selection/filter/time-range/focus reducer, action dispatches, data attributes and status UI",
    "Stage 6.1 shared-state runtime contract is incomplete",
  );
}

function validateInspectorProposalRuntime() {
  const app = readAppFile("src/App.tsx");
  const i18nPath = path.join(appRoot, "src/i18n/zh-CN.ts");
  const i18n = fs.existsSync(i18nPath) ? fs.readFileSync(i18nPath, "utf8") : "";
  const uiSource = `${app}\n${i18n}`;
  const css = readAppFile("src/styles.css");

  assertCondition(
    hasAll(app, [
      "interface InspectorExplanation",
      "function buildInspectorExplanation",
      "function InspectorExplanationPanel",
      "memory_weight = tier*0.5 + importance*0.3 + confidence*0.2",
      "leverage_score = max(0, memory_weight + decision_impact*0.15 - sensitivity_penalty)",
      "sharedAtlasReducer -> focus(inspector/home/galaxy/timeline/roi)",
      "data-raw-display=\"false\"",
      "脱敏派生快照",
    ]) && hasAll(css, [
      ".inspector-explanation-panel",
      ".inspector-formula-grid",
      ".inspector-formula-card",
      ".inspector-evidence-grid",
      ".inspector-safety-list",
    ]),
    "part7_stage6_2_explanation_runtime",
    "Current Inspector runtime exposes formulas, parameters, redacted evidence and no-raw explanation panel",
    "Stage 6.2 Inspector explanation runtime contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "interface WritebackProposalDraftInput",
      "function buildWritebackProposalDraft",
      "proposalIdPrefix: \"atlas_preview\"",
      "data-proposal-only=\"true\"",
      "data-active-memory-mutation=\"false\"",
      "proposalJsonPreview",
      "direct_frontend_mutation_of_active_memory: false",
      "requires_agent_or_human_apply: true",
      "requires_conflict_check: true",
    ]) && hasAll(uiSource, [
      "JSON 提案预览",
      "保存 JSON 提案",
    ]) && hasAll(css, [
      ".writeback-safety-strip",
      ".writeback-json-preview",
      ".writeback-json-preview pre",
    ]),
    "part7_stage6_2_proposal_runtime",
    "Current writeback runtime remains proposal-only JSON with direct active-memory mutation disabled",
    "Stage 6.2 proposal-only runtime contract is incomplete",
  );

  assertCondition(
    hasAll(app, [
      "const [debugOpen, setDebugOpen] = useState(false)",
      "data-debug-lite={debugOpen ? \"open\" : \"closed\"}",
      "data-default-raw-summary=\"hidden\"",
      "className=\"inspector-debug-toggle\"",
      "data-debug-panel=\"true\"",
    ]) && hasAll(uiSource, [
      "隐藏 Debug",
      "显示 Debug",
    ]) && hasAll(css, [
      ".inspector-debug-toggle",
      ".inspector-debug-panel",
    ]),
    "part7_stage6_2_debug_runtime",
    "Current Inspector runtime keeps debug/agent fields default-closed and explicitly separated from the default explanation",
    "Stage 6.2 Debug separation runtime contract is incomplete",
  );
}

function validateVisualAcceptanceHooks() {
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  assertCondition(
    hasAll(visualAudit, [
      "stage6_1_shared_state_store_ready",
      "stage6_2_inspector_proposal_ready",
      "export interface SharedAtlasSelectionState",
      "export interface SharedAtlasFilterState",
      "export interface SharedAtlasFocusState",
      "export function sharedAtlasReducer",
      "function InspectorExplanationPanel",
      "function buildWritebackProposalDraft",
      "data-proposal-only=\"true\"",
      "data-active-memory-mutation=\"false\"",
      "data-debug-lite={debugOpen ? \"open\" : \"closed\"}",
    ]),
    "part7_visual_acceptance_hooks_current",
    "Visual acceptance script contains Stage 6 shared-state and Inspector/Proposal hooks",
    "Visual acceptance script lacks Stage 6 hooks",
  );
}

function validateModelAndRecords() {
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  assertCondition(
    hasAll(model, [
      "Shared State Store 状态模型",
      "Inspector 解释与 Proposal 安全模型",
      "review_status: `stage_6_whole_stage_review_passed`",
      "Stage 6 整体复审已确认",
      "direct_frontend_mutation_of_active_memory = false",
      "requires_agent_or_human_apply = true",
    ]),
    "part7_stage6_model_parameters_current",
    "Model parameters preserve Stage 6 whole-review status, shared-state contract and fail-closed proposal-only safety",
    "Stage 6 model parameters are missing whole-review status or safety settings",
  );
}

function validateProductionDoesNotImportExperiments() {
  const productionFiles = walkFiles(path.join(appRoot, "src"), new Set(["experiments", "node_modules"]));
  const offendingRefs = [];
  const forbidden = [
    "memory-starfield-spike",
    "memory-river-spike",
    "universe-state-generator-spike",
  ];
  for (const filePath of productionFiles) {
    const source = fs.readFileSync(filePath, "utf8");
    for (const needle of forbidden) {
      if (source.includes(needle)) offendingRefs.push(`${path.relative(repoRoot, filePath)} -> ${needle}`);
    }
  }
  assertCondition(
    offendingRefs.length === 0,
    "part7_production_experiment_isolation",
    "Production src files do not import or reference isolated experiment directories",
    "Production source references isolated experiment directories",
    { offendingRefs },
  );
}

function validateBuildAndAcceptance() {
  const tsc = path.join(appRoot, "node_modules/typescript/bin/tsc");
  const vite = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(
    fs.existsSync(tsc) && fs.existsSync(vite),
    "part7_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, ["--experimental-strip-types", path.join(appRoot, "scripts/validate_shared_state_store.mjs")], { cwd: appRoot });
  pass("part7_shared_state_passed", "validate_shared_state_store.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_inspector_proposal.mjs")], { cwd: appRoot });
  pass("part7_inspector_proposal_passed", "validate_inspector_proposal.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_atlas_stage6.mjs")], { cwd: appRoot });
  pass("part7_stage6_passed", "validate_memory_atlas_stage6.mjs passed for current repo state");
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part7_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part7_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_release.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part7_release_acceptance_passed", "audit_memory_atlas_release.py passed against current production dist");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part7_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part7_stage6_review.md");

  assertCondition(
    packageSource.includes('"validate:part7-stage6": "node scripts/validate_memory_atlas_part7_stage6.cjs"'),
    "part7_package_script_current",
    "Package scripts expose validate:part7-stage6",
    "Package script validate:part7-stage6 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 7 is review-passed",
      "Stage 6.1",
      "Stage 6.2",
      "Stage 6 overall",
      "validate:part7-stage6",
      "No Part 8 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part7_review_doc_current",
    "Part 7 review doc records phase coverage, validator, boundaries and upload non-goal",
    "Part 7 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 7 Stage 6 Review",
      "`validate:part7-stage6`",
      "Stage 6.1 / 6.2 / Stage 6 overall",
      "No Part 8 review",
      "No GitHub main upload",
    ]),
    "part7_changelog_current",
    "Changelog records Part 7 review, validator, stage coverage and non-goals",
    "Changelog does not record Part 7 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 7 复审",
      "Stage 6.1 / 6.2 / Stage 6 overall",
      "validate:part7-stage6",
      "未进入 Part 8",
      "未上传 GitHub main",
    ]),
    "part7_delivery_record_current",
    "Delivery record records Part 7 review status and next boundary",
    "Delivery record does not record Part 7 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 28. Part 7 Stage 6 复审门槛",
      "状态：`part_7_stage_6_review_passed`",
      "validate:part7-stage6",
      "Stage 6.1 Shared State Store",
      "Stage 6.2 Inspector and Proposal",
      "Stage 6 overall review",
      "不进入 Part 8",
    ]),
    "part7_model_parameters_current",
    "Model parameters record Part 7 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 7 review gate",
  );
}

try {
  validateStage61Review();
  validateStage62Review();
  validateStage6OverallReview();
  validateSharedStateRuntime();
  validateInspectorProposalRuntime();
  validateVisualAcceptanceHooks();
  validateModelAndRecords();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "7", scope: ["6.1", "6.2", "stage6"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part7_stage6_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "7", scope: ["6.1", "6.2", "stage6"], checks }, null, 2));
  process.exit(1);
}
