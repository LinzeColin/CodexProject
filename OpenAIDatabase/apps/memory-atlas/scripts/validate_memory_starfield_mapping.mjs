#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const modelParams = readFileSync(resolve(repoRoot, "config/visualization/model_parameters.memory_starfield.yaml"), "utf8");
const paramsModule = readFileSync(resolve(appRoot, "src/config/memoryStarfieldParameters.ts"), "utf8");
const galaxyScene = readFileSync(resolve(appRoot, "src/components/GalaxyScene.tsx"), "utf8");

const checks = [];

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

requireCheck(
  "parameter_file_has_stage4_2_sections",
  hasAll(modelParams, [
    "product_target: Memory Atlas v1.1.5",
    "cluster_mass:",
    "particle_attributes:",
    "terrain:",
    "importance_to_mass_scale",
    "recency_half_life_days",
    "interaction_density_scale",
    "confidence_noise_amplitude",
    "quality_settings:",
  ]),
  "model_parameters.memory_starfield.yaml exposes v1.1.5 mass, particle, terrain and quality settings",
  "model_parameters.memory_starfield.yaml is missing one or more Stage 4.2 mapping sections",
);

requireCheck(
  "frontend_reads_parameter_yaml",
  hasAll(paramsModule, [
    "model_parameters.memory_starfield.yaml?raw",
    "parseYamlScalarPaths",
    "mapping.cluster_mass.tier_core",
    "mapping.particle_attributes.base_size",
    "mapping.terrain.ridge_roi_threshold",
    "performance.quality_settings.",
  ]),
  "frontend parameter module imports the YAML as raw text and maps scalar paths into typed config",
  "frontend parameter module does not read the YAML source or expose required typed mapping paths",
);

requireCheck(
  "mass_formula_uses_parameter_config",
  hasAll(galaxyScene, [
    "const params = MEMORY_STARFIELD_PARAMS.mapping.clusterMass",
    "params.roiMultiplier",
    "params.importanceHigh",
    "params.recencyMultiplier",
    "params.usageSqrtMultiplier",
    "MEMORY_STARFIELD_PARAMS.mapping.importanceToMassScale",
  ]) && !galaxyScene.includes('tier === "核心画像" ? 8 : tier === "一般" ? 4.8 : 1.6'),
  "cluster mass formula uses tier, kind, ROI, importance, recency and usage values from MEMORY_STARFIELD_PARAMS",
  "cluster mass formula may still be hardcoded instead of parameter-backed",
);

requireCheck(
  "particle_attributes_use_parameter_config",
  hasAll(galaxyScene, [
    "function memoryStarfieldParticleAttributes",
    "memoryStarfieldRecencyScore",
    "memoryStarfieldConfidenceScore",
    "params.massSizeScale",
    "params.recencyBrightnessBoost",
    "params.confidenceColorDesaturation",
    "params.interactionTrailScale",
  ]),
  "particle size, color, brightness and trail strength use recency, confidence and interaction mapping parameters",
  "particle attributes may not use parameter-backed recency, confidence and interaction signals",
);

requireCheck(
  "terrain_mapping_is_explainable",
  hasAll(galaxyScene, [
    "function memoryTerrainType",
    "function buildTerrainSummary",
    "memory-starfield-terrain-layer",
    "Memory Terrain analysis panel",
    "terrainFeatureCount",
    "parameterSource: MEMORY_STARFIELD_PARAMS.parameterSource",
  ]),
  "terrain type mapping drives a subtle renderer layer plus an Analysis explanation panel and debug signal",
  "terrain mapping lacks renderer layer, explanation panel or debug signal evidence",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
