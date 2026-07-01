#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");

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

function hasAll(source, fragments) {
  return fragments.every((fragment) => source.includes(fragment));
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

function validatePhase01ScopeFreeze() {
  const source = readRepoFile("docs/product/memory_atlas_visual_scope.md");
  assertCondition(
    hasAll(source, [
      "Phase: 0.1 Scope & Naming Freeze",
      "## Scope Freeze",
      "记忆总览",
      "记忆星系",
      "记忆时间河",
      "Universe State Snapshot",
      "不接入新的外部知识源",
      "不读取 raw export",
      "不在 Stage 0 直接替换生产 Galaxy 或 Timeline",
      "默认入口",
      "本 phase 不改路由",
      "## Rollback",
    ]),
    "phase_0_1_scope_naming_freeze",
    "Phase 0.1 scope freeze records modules, Chinese naming, default-entry decision, privacy boundary, non-routing boundary, and rollback",
    "Phase 0.1 scope freeze is incomplete",
  );
}

function validatePhase02ProductContracts() {
  const overview = readRepoFile("docs/product/memory_overview_product_contract.md");
  const starfield = readRepoFile("docs/product/memory_starfield_visual_contract.md");
  const river = readRepoFile("docs/product/memory_river_interaction_contract.md");
  const universe = readRepoFile("docs/architecture/universe_state_snapshot.md");
  const scores = readRepoFile("docs/architecture/memory_weather_black_hole_proto_star.md");

  assertCondition(
    hasAll(overview, [
      "记忆总览",
      "Universe State Snapshot",
      "Memory Weather",
      "Black Hole",
      "Proto-Star",
      "Next Actions",
      "Mini Starfield",
      "River Pulse",
      "Inspector",
      "proposal-only",
      "不直接读取 raw transcript",
      "No interaction may directly apply writeback",
    ]),
    "phase_0_2_memory_overview_contract",
    "Memory Overview contract covers shared state, weather, risk/opportunity signals, next actions, previews, Inspector handoff, and proposal-only writeback boundary",
    "Memory Overview contract is incomplete",
  );
  assertCondition(
    hasAll(starfield, [
      "记忆星系",
      "Deep-Space Nebula",
      "Flow Field",
      "Gravitational Disk",
      "Black Hole",
      "Proto-Star",
      "Memory Terrain",
      "Presentation Mode",
      "Analysis Mode",
      "普通 node-link graph",
      "static scatter",
      "random small light dots",
      "raw transcript",
      "No WebGL spike implementation",
    ]),
    "phase_0_2_memory_starfield_contract",
    "Memory Starfield contract freezes nebula/flow/disk/risk/opportunity/terrain semantics, Presentation/Analysis modes, anti-regression boundaries, and privacy limits",
    "Memory Starfield contract is incomplete",
  );
  assertCondition(
    hasAll(river, [
      "记忆时间河",
      "dynamic time river",
      "Zoom",
      "Brush",
      "Theme Lanes",
      "Black Hole Band",
      "Proto-Star Marker",
      "Pseudo-Haptic Feedback",
      "Reduced Motion",
      "静态事件列表",
      "表格型流水账",
      "static scatter",
      "raw transcript",
    ]),
    "phase_0_2_memory_river_contract",
    "Memory River contract freezes zoom, brush, lanes, risk/opportunity markers, pseudo-haptic, reduced-motion, anti-list/table boundaries, and privacy limits",
    "Memory River contract is incomplete",
  );
  assertCondition(
    hasAll(universe, [
      "Universe State Snapshot",
      "memory_weather",
      "dominant_clusters",
      "rising_clusters",
      "declining_clusters",
      "black_holes",
      "proto_stars",
      "river_pulse",
      "mini_starfield",
      "recommended_next_actions",
      "data/derived/visualization/memory_atlas.json",
      "Raw OpenAI exports",
    ]) && hasAll(scores, [
      "black_hole_score",
      "proto_star_score",
      "stale_score",
      "Memory Weather",
      "storm_conflict",
      "black_hole_warning",
      "proto_star_cloud",
      "Memory Terrain",
      "No score may use raw transcript text",
    ]),
    "phase_0_2_universe_state_contracts",
    "Universe State and scoring contracts define shared state fields, formulas, weather labels, terrain mapping, and raw/private exclusions",
    "Universe State architecture or scoring contract is incomplete",
  );
}

function validatePhase03SpikeScaffold() {
  const starfieldReadme = readRepoFile("apps/memory-atlas/src/experiments/memory-starfield-spike/README.md");
  const riverReadme = readRepoFile("apps/memory-atlas/src/experiments/memory-river-spike/README.md");
  const starfieldFixture = readRepoFile("apps/memory-atlas/src/experiments/memory-starfield-spike/fixture.ts");
  const riverFixture = readRepoFile("apps/memory-atlas/src/experiments/memory-river-spike/fixture.ts");

  assertCondition(
    hasAll(starfieldReadme, [
      "Phase 0.3 Scaffold Continuity",
      "## Goal",
      "## Boundary",
      "## Input Fixture Contract",
      "## Acceptance Criteria",
      "## Rollback",
      "The production app does not import this directory",
      "raw/private/session/cookie/secret",
    ]) && hasAll(riverReadme, [
      "Phase 0.3 Scaffold Continuity",
      "## Goal",
      "## Boundary",
      "## Input Fixture Contract",
      "## Acceptance Criteria",
      "## Rollback",
      "The production app does not import this directory",
      "raw/private/session/cookie/secret",
    ]),
    "phase_0_3_spike_scaffold_readmes",
    "Both isolated spike README files preserve Phase 0.3 scaffold continuity, goal, boundary, fixture, acceptance, rollback, production-isolation, and safety sections",
    "Spike scaffold README evidence is incomplete",
  );
  assertCondition(
    hasAll(starfieldFixture, [
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
    ]) && hasAll(riverFixture, [
      "rawPrivateDataIncluded: false",
      "plaintextSecretsIncluded: false",
      "localAbsolutePathsIncluded: false",
      "writebackAllowed: false",
    ]),
    "phase_0_3_redacted_fixtures",
    "Spike fixtures explicitly mark raw/private, plaintext secrets, local absolute paths, and river writeback as false",
    "Spike fixture safety flags are incomplete",
  );
  const productionFiles = walkFiles(path.join(appRoot, "src"), new Set(["experiments", "node_modules"]));
  const offendingRefs = [];
  for (const filePath of productionFiles) {
    const source = fs.readFileSync(filePath, "utf8");
    if (source.includes("memory-starfield-spike") || source.includes("memory-river-spike")) {
      offendingRefs.push(path.relative(repoRoot, filePath));
    }
  }
  assertCondition(
    offendingRefs.length === 0,
    "phase_0_3_production_isolation",
    "Production src files outside experiments do not reference isolated spike directories",
    "Production source references isolated spike directories",
    { offendingRefs },
  );
}

function validateParameterTemplatesAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part1_stage0_review.md");
  const parameterFiles = [
    "config/visualization/model_parameters.memory_starfield.yaml",
    "config/visualization/model_parameters.memory_river.yaml",
    "config/visualization/model_parameters.universe_state.yaml",
  ];

  for (const relativePath of parameterFiles) {
    const source = readRepoFile(relativePath);
    assertCondition(
      hasAll(source, [
        "schema_version:",
        "product_target: Memory Atlas v1.1.5",
        "raw_private_data_allowed: false",
        "plaintext_secrets_allowed: false",
        "local_absolute_paths_allowed: false",
        "writeback_allowed: false",
        "validation_hints:",
      ]),
      `part1_parameter_boundary_${path.basename(relativePath, ".yaml")}`,
      `${relativePath} preserves schema, product target, privacy/writeback boundary, and validation hints`,
      `${relativePath} lacks required Part 1 parameter boundary markers`,
    );
  }
  assertCondition(
    hasAll(packageSource, [
      '"validate:part1-stage0": "node scripts/validate_memory_atlas_part1_stage0.cjs"',
    ]),
    "part1_package_script_current",
    "Package scripts expose validate:part1-stage0",
    "Package script validate:part1-stage0 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 1 is review-passed",
      "Phase 0.1",
      "Phase 0.2",
      "Phase 0.3",
      "validate:part1-stage0",
      "No Cloudflare live deploy",
      "No raw/private/cookie/session/secret",
      "No production React/Three/D3 integration was changed",
      "No GitHub main upload",
    ]),
    "part1_review_doc_current",
    "Part 1 review doc records phase coverage, validator, boundaries, and upload non-goal",
    "Part 1 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 1 Stage 0 Review",
      "`validate:part1-stage0`",
      "Phase 0.3 scaffold continuity",
      "No Part 2 review",
      "No GitHub main upload",
    ]),
    "part1_changelog_current",
    "Changelog records Part 1 review, validator, scaffold continuity fix, and non-goals",
    "Changelog does not record Part 1 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 1 复审",
      "Phase 0.1 / 0.2 / 0.3",
      "validate:part1-stage0",
      "未进入 Part 2",
      "未上传 GitHub main",
    ]),
    "part1_delivery_record_current",
    "Delivery record records Part 1 review status and next boundary",
    "Delivery record does not record Part 1 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 22. Part 1 Stage 0 复审门槛",
      "状态：`part_1_stage_0_review_passed`",
      "validate:part1-stage0",
      "Phase 0.3 scaffold continuity",
      "不进入 Part 2",
    ]),
    "part1_model_parameters_current",
    "Model parameters record Part 1 review gate, validator, scaffold continuity, and non-goals",
    "Model parameters do not record Part 1 review gate",
  );
}

try {
  validatePhase01ScopeFreeze();
  validatePhase02ProductContracts();
  validatePhase03SpikeScaffold();
  validateParameterTemplatesAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "1", phases: ["0.1", "0.2", "0.3"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part1_stage0_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {},
  });
  console.error(JSON.stringify({ status: "FAIL", part: "1", phases: ["0.1", "0.2", "0.3"], checks }, null, 2));
  process.exit(1);
}
