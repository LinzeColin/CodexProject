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

function validateStage41Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage4_1_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 4.1 is review-passed",
      "4.1.1 新旧 Galaxy Feature Flag",
      "4.1.2 集成 Flow Field Renderer",
      "4.1.3 WebGL Fallback",
      "DEFAULT_GALAXY_RENDERER_MODE = \"memory-starfield\"",
      "memory-starfield-flow-field-trajectories",
      "Flow Field quality selector",
      "低质量 fallback 模式",
      "galaxy_stage4_1_rendering_integration_ready",
      "Port `4177` had no listener",
      "Stage 4.1 did not",
    ]),
    "part5_phase_4_1_review_current",
    "Stage 4.1 review proves default Memory Starfield renderer, rollback flag, Flow Field trajectories, quality fallback, visual audit evidence and safety boundaries",
    "Stage 4.1 review is incomplete",
  );
}

function validateStage42Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage4_2_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 4.2 is review-passed",
      "4.2.1 Cluster Mass Mapping",
      "4.2.2 Particle Attribute Mapping",
      "4.2.3 Memory Terrain Layer Mapping",
      "model_parameters.memory_starfield.yaml",
      "memoryStarfieldMass",
      "memoryStarfieldParticleAttributes",
      "memoryTerrainType",
      "galaxy_stage4_2_data_mapping_ready",
      "Port `4177` had no listener",
      "Stage 4.2 did not",
    ]),
    "part5_phase_4_2_review_current",
    "Stage 4.2 review proves parameter-backed mass, particle attributes, terrain mapping, visual audit evidence and safety boundaries",
    "Stage 4.2 review is incomplete",
  );
}

function validateStage43Review() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage4_3_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 4.3 is review-passed",
      "4.3.1 Hover Preview",
      "4.3.2 Click Focus",
      "4.3.3 Freeze / Resume Flow",
      "4.3.4 Presentation / Analysis Mode",
      "updateHoverPreview",
      "buildFocusedNeighborhood",
      "Freeze Flow Field",
      "Resume Flow Field",
      "Starfield mode selector",
      "galaxy_stage4_3_interaction_ready",
      "Stage 4.3 did not",
    ]),
    "part5_phase_4_3_review_current",
    "Stage 4.3 review proves transient hover, capped click focus, Freeze/Resume Flow, Presentation/Analysis mode, browser evidence and safety boundaries",
    "Stage 4.3 review is incomplete",
  );
}

function validateStage4OverallReview() {
  const source = readRepoFile("docs/reviews/memory_atlas_v1_1_5_stage4_review.md");
  assertCondition(
    hasAll(source, [
      "Stage 4 is review-passed",
      "记忆星系生产集成",
      "4.1 Rendering Integration",
      "4.2 Data Mapping",
      "4.3 Starfield Interaction",
      "New/old Galaxy feature flag and rollback",
      "Production Flow Field renderer",
      "Cluster mass mapping",
      "Particle attribute mapping",
      "Memory Terrain layer",
      "Hover preview",
      "Click focus",
      "Freeze / Resume Flow",
      "Presentation / Analysis mode",
      "Chrome CDP desktop evidence",
      "Chrome CDP visible-mobile evidence",
      "Port `4177` had no listener",
      "Stage 4 did not",
      "Stage 5 may start only after",
    ]),
    "part5_stage4_overall_review_current",
    "Stage 4 overall review proves 4.1/4.2/4.3 inclusion, runtime/browser evidence, safety boundary and next-stage gate",
    "Stage 4 overall review is incomplete",
  );
}

function validateStarfieldRuntime() {
  const app = readAppFile("src/App.tsx");
  const galaxy = readAppFile("src/components/GalaxyScene.tsx");
  const flags = readAppFile("src/config/visualFlags.ts");
  const paramsModule = readAppFile("src/config/memoryStarfieldParameters.ts");
  const css = readAppFile("src/styles.css");
  const params = readRepoFile("config/visualization/model_parameters.memory_starfield.yaml");

  assertCondition(
    hasAll(flags, [
      "export type GalaxyRendererMode = \"memory-starfield\" | \"legacy\"",
      "DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = \"memory-starfield\"",
      "VITE_MEMORY_ATLAS_GALAXY_RENDERER",
      "GALAXY_RENDERER_STORAGE_KEY",
    ]) && hasAll(app, [
      "persistGalaxyRendererMode",
      "galaxy-renderer-toggle",
      "aria-pressed={galaxyRendererMode === \"memory-starfield\"}",
      "aria-pressed={galaxyRendererMode === \"legacy\"}",
    ]),
    "part5_stage4_1_feature_flag_runtime",
    "Current runtime keeps memory-starfield as default Galaxy renderer and preserves legacy rollback controls",
    "Stage 4.1 feature flag or rollback runtime contract is incomplete",
  );

  assertCondition(
    hasAll(galaxy, [
      "rendererMode: GalaxyRendererMode",
      "renderer.domElement.dataset.rendererMode = rendererMode",
      "renderer.domElement.dataset.flowField = rendererMode === \"memory-starfield\" ? \"enabled\" : \"legacy-off\"",
      "STARFIELD_QUALITY_SETTINGS",
      "createFlowTrailSegments",
      "updateMemoryStarfieldFlow",
      "memory-starfield-flow-field-trajectories",
      "memoryStarfieldSignalKind",
      "\"black-hole\"",
      "\"proto-star\"",
      "fallbackMode: rendererMode === \"legacy\" ? \"legacy\" : starfieldQuality === \"low\" ? \"low-quality\" : \"webgl\"",
      "Flow Field quality selector",
      "低质量 fallback 模式",
    ]) && hasAll(css, [
      ".galaxy-renderer-toggle",
      ".galaxy-quality-tabs",
      ".galaxy-flow-control",
    ]),
    "part5_stage4_1_rendering_runtime",
    "Current Galaxy runtime exposes Flow Field trajectories, signal markers, quality selector and low-quality fallback",
    "Stage 4.1 rendering runtime contract is incomplete",
  );

  assertCondition(
    hasAll(params, [
      "product_target: Memory Atlas v1.1.5",
      "cluster_mass:",
      "particle_attributes:",
      "terrain:",
      "importance_to_mass_scale",
      "recency_half_life_days",
      "interaction_density_scale",
      "confidence_noise_amplitude",
      "quality_settings:",
    ]) && hasAll(paramsModule, [
      "model_parameters.memory_starfield.yaml?raw",
      "parseYamlScalarPaths",
      "mapping.cluster_mass.tier_core",
      "mapping.particle_attributes.base_size",
      "mapping.terrain.ridge_roi_threshold",
      "performance.quality_settings.",
    ]) && hasAll(galaxy, [
      "function memoryStarfieldMass",
      "const params = MEMORY_STARFIELD_PARAMS.mapping.clusterMass",
      "function memoryStarfieldParticleAttributes",
      "memoryStarfieldRecencyScore",
      "memoryStarfieldConfidenceScore",
      "function memoryTerrainType",
      "function buildTerrainSummary",
      "memory-starfield-terrain-layer",
      "parameterSource: MEMORY_STARFIELD_PARAMS.parameterSource",
      "terrainFeatureCount",
      "className=\"galaxy-terrain-panel\"",
    ]),
    "part5_stage4_2_mapping_runtime",
    "Current Galaxy runtime maps mass, particle attributes, terrain and quality settings from model_parameters.memory_starfield.yaml",
    "Stage 4.2 mapping runtime contract is incomplete",
  );

  assertCondition(
    hasAll(galaxy, [
      "function updateHoverPreview",
      "hoveredIdRef.current = item.node.id",
      "setHoverPreview({",
      "function onPointerUp",
      "if (item) onSelectNode(item.node)",
      "function updateCameraFocus",
      "buildFocusedNeighborhood",
      "MAX_FOCUS_VISIBLE_NEIGHBORS",
      "hiddenNeighborCount",
      "primaryNeighborCards",
      "const [flowPaused, setFlowPaused]",
      "flowPausedRef",
      "dataset.flowFrozen",
      "Freeze Flow Field",
      "Resume Flow Field",
      "if (flowPausedRef.current) return;",
      "const frozen = rendererMode === \"memory-starfield\" && flowPausedRef.current",
      "type StarfieldViewMode = \"presentation\" | \"analysis\"",
      "Starfield mode selector",
      "Presentation Mode",
      "Analysis Mode",
      "Starfield formula summary",
      "Analysis inspector summary",
    ]) && hasAll(css, [
      ".galaxy-mode-tabs",
      ".terrain-formula-grid",
      ".terrain-inspector-strip",
    ]),
    "part5_stage4_3_interaction_runtime",
    "Current Galaxy runtime preserves transient hover, capped click focus, Freeze/Resume Flow and Presentation/Analysis mode",
    "Stage 4.3 interaction runtime contract is incomplete",
  );
}

function validateVisualAcceptanceHooks() {
  const visualAudit = readRepoFile("scripts/audit_memory_atlas_visual_acceptance.py");
  assertCondition(
    hasAll(visualAudit, [
      "galaxy_stage4_1_rendering_integration_ready",
      "galaxy_stage4_2_data_mapping_ready",
      "galaxy_stage4_3_interaction_ready",
      "DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = \"memory-starfield\"",
      "memory-starfield-flow-field-trajectories",
      "function memoryStarfieldMass",
      "function memoryStarfieldParticleAttributes",
      "function memoryTerrainType",
      "Freeze Flow Field",
      "Starfield mode selector",
    ]),
    "part5_visual_acceptance_hooks_current",
    "Visual acceptance script contains Stage 4 rendering, mapping and interaction hooks",
    "Visual acceptance script lacks Stage 4 hooks",
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
    "part5_production_experiment_isolation",
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
    "part5_dependencies_ready",
    "TypeScript and Vite CLIs are available in node_modules",
    "TypeScript or Vite CLI missing from app node_modules",
  );
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_starfield_mapping.mjs")], { cwd: appRoot });
  pass("part5_starfield_mapping_passed", "validate_memory_starfield_mapping.mjs passed for current repo state");
  run(process.execPath, [path.join(appRoot, "scripts/validate_memory_starfield_interaction.mjs")], { cwd: appRoot });
  pass("part5_starfield_interaction_passed", "validate_memory_starfield_interaction.mjs passed for current repo state");
  run(process.execPath, [tsc, "-b", "--pretty", "false"], { cwd: appRoot });
  run(process.execPath, [vite, "build", "--emptyOutDir"], { cwd: appRoot });
  assertCondition(
    fs.existsSync(path.join(appRoot, "dist/index.html")) && fs.existsSync(path.join(appRoot, "dist/memory_atlas.json")),
    "part5_build_ready",
    "Production build created dist/index.html and dist/memory_atlas.json",
    "Production build did not create expected release files",
  );
  run("python3", ["scripts/audit_memory_atlas_visual_acceptance.py", "--repo-root", repoRoot], { cwd: repoRoot });
  pass("part5_visual_acceptance_passed", "audit_memory_atlas_visual_acceptance.py passed for current repo state");
  run("python3", ["scripts/audit_memory_atlas_acceptance.py", "--repo-root", repoRoot, "--publish-dir", path.join(appRoot, "dist")], { cwd: repoRoot });
  pass("part5_overall_acceptance_passed", "audit_memory_atlas_acceptance.py passed against current production dist");
}

function validateDocsAndRecords() {
  const packageSource = readRepoFile("apps/memory-atlas/package.json");
  const changelog = readRepoFile("CHANGELOG.md");
  const delivery = readRepoFile("docs/MEMORY_ATLAS_DELIVERY_RECORD.md");
  const model = readRepoFile("docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md");
  const review = readRepoFile("docs/reviews/memory_atlas_v1_1_5_part5_stage4_review.md");

  assertCondition(
    packageSource.includes('"validate:part5-stage4": "node scripts/validate_memory_atlas_part5_stage4.cjs"'),
    "part5_package_script_current",
    "Package scripts expose validate:part5-stage4",
    "Package script validate:part5-stage4 is missing",
  );
  assertCondition(
    hasAll(review, [
      "Part 5 is review-passed",
      "Stage 4.1",
      "Stage 4.2",
      "Stage 4.3",
      "Stage 4 overall",
      "validate:part5-stage4",
      "No Part 6 review",
      "No GitHub main upload",
      "No production runtime feature work was added",
      "No raw/private/cookie/session/secret",
    ]),
    "part5_review_doc_current",
    "Part 5 review doc records phase coverage, validator, boundaries and upload non-goal",
    "Part 5 review doc is incomplete",
  );
  assertCondition(
    hasAll(changelog, [
      "Memory Atlas v1.1.5 Part 5 Stage 4 Review",
      "`validate:part5-stage4`",
      "Stage 4.1 / 4.2 / 4.3 / Stage 4 overall",
      "No Part 6 review",
      "No GitHub main upload",
    ]),
    "part5_changelog_current",
    "Changelog records Part 5 review, validator, stage coverage and non-goals",
    "Changelog does not record Part 5 review status",
  );
  assertCondition(
    hasAll(delivery, [
      "完成 Memory Atlas v1.1.5 Part 5 复审",
      "Stage 4.1 / 4.2 / 4.3 / Stage 4 overall",
      "validate:part5-stage4",
      "未进入 Part 6",
      "未上传 GitHub main",
    ]),
    "part5_delivery_record_current",
    "Delivery record records Part 5 review status and next boundary",
    "Delivery record does not record Part 5 review status",
  );
  assertCondition(
    hasAll(model, [
      "## 26. Part 5 Stage 4 复审门槛",
      "状态：`part_5_stage_4_review_passed`",
      "validate:part5-stage4",
      "Stage 4.1 Rendering Integration",
      "Stage 4.2 Data Mapping",
      "Stage 4.3 Starfield Interaction",
      "Stage 4 overall review",
      "不进入 Part 6",
    ]),
    "part5_model_parameters_current",
    "Model parameters record Part 5 review gate, validator, stage coverage and non-goals",
    "Model parameters do not record Part 5 review gate",
  );
}

try {
  validateStage41Review();
  validateStage42Review();
  validateStage43Review();
  validateStage4OverallReview();
  validateStarfieldRuntime();
  validateVisualAcceptanceHooks();
  validateProductionDoesNotImportExperiments();
  validateBuildAndAcceptance();
  validateDocsAndRecords();
  console.log(JSON.stringify({ status: "PASS", part: "5", scope: ["4.1", "4.2", "4.3", "stage4"], checks }, null, 2));
} catch (error) {
  checks.push({
    name: "part5_stage4_review",
    status: "FAIL",
    evidence: error.message,
    details: error.details || {
      stdout: error.stdout?.slice(-4000),
      stderr: error.stderr?.slice(-4000),
    },
  });
  console.error(JSON.stringify({ status: "FAIL", part: "5", scope: ["4.1", "4.2", "4.3", "stage4"], checks }, null, 2));
  process.exit(1);
}
