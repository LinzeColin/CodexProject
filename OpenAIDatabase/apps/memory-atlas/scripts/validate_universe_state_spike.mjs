import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  generateUniverseStateSnapshot,
  adaptUniverseStateFixture,
} from "../src/models/universeState.ts";
import {
  DEFAULT_UNIVERSE_STATE_PARAMETERS,
  blackHoleScore,
  protoStarScore,
  staleScore,
} from "../src/utils/universeStateScores.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(here, "..");
const repoRoot = path.resolve(appRoot, "../..");
const inputPath = path.join(appRoot, "src/fixtures/universe_state.input.fixture.json");
const samplePath = path.join(appRoot, "src/fixtures/universe_state.sample.json");
const schemaPath = path.join(appRoot, "src/fixtures/universe_state.schema.json");
const paramsPath = path.join(repoRoot, "config/visualization/model_parameters.universe_state.yaml");

const input = readJson(inputPath);
const schema = readJson(schemaPath);
const generated = generateUniverseStateSnapshot(input, DEFAULT_UNIVERSE_STATE_PARAMETERS);

if (process.argv.includes("--write-sample")) {
  fs.writeFileSync(samplePath, `${JSON.stringify(generated, null, 2)}\n`);
}

const sample = fs.existsSync(samplePath) ? readJson(samplePath) : generated;
const failures = [];

unitTestAdapter(failures);
unitTestScoreFunctions(failures);
validateSchema(sample, schema, failures);
validateGeneratedMatchesSample(generated, sample, failures);
validateParameterDrift(failures);
validatePrivacy(sample, failures);

if (failures.length) {
  console.error(JSON.stringify({ ok: false, failures }, null, 2));
  process.exit(1);
}

console.log(
  JSON.stringify(
    {
      ok: true,
      generated_at: sample.generated_at,
      weather: sample.state.memory_weather.label,
      dominant_count: sample.state.dominant_clusters.length,
      rising_count: sample.state.rising_clusters.length,
      declining_count: sample.state.declining_clusters.length,
      conflict_count: sample.state.conflict_zones.length,
      black_hole_count: sample.state.black_holes.length,
      proto_star_count: sample.state.proto_stars.length,
      stale_count: sample.state.stale_orbits.length,
      parameter_source: sample.diagnostics.parameter_source,
      privacy_status: sample.diagnostics.privacy_status,
    },
    null,
    2,
  ),
);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function unitTestAdapter(failures) {
  const adapted = adaptUniverseStateFixture(input);
  if (adapted.clusters.length !== 5) failures.push("adapter did not parse 5 clusters");
  if (adapted.conflictZones.length !== 1) failures.push("adapter did not parse conflict zone");
  if (adapted.blackHoleCandidates.length !== 1) failures.push("adapter did not parse black hole candidate");
  if (adapted.protoStarCandidates.length !== 2) failures.push("adapter did not parse proto star candidates");
  if (adapted.clusters.some((cluster) => cluster.mass_score < 0 || cluster.mass_score > 1)) {
    failures.push("adapter did not clamp cluster mass scores");
  }
}

function unitTestScoreFunctions(failures) {
  const blackHole = blackHoleScore({
    interactionSignal: 0.82,
    recencySignal: 0.8312,
    repetitionSignal: 0.74,
    roiPenaltySignal: 0.46,
    growthPenaltySignal: 0.42,
  });
  if (blackHole < 0.7 || blackHole > 0.73) failures.push(`black hole score outside expected range: ${blackHole}`);

  const protoStar = protoStarScore({
    recencyGrowthSignal: 0.86,
    crossSignal: 0.72,
    capabilityRelationSignal: 0.82,
    roiPotentialSignal: 0.8,
    uncertaintyPenalty: 0.28,
  });
  if (protoStar < 0.74 || protoStar > 0.76) failures.push(`proto star score outside expected range: ${protoStar}`);

  const stale = staleScore({
    inactiveDaysSignal: 0.5333,
    lowRecentUsageSignal: 0.76,
    confidenceDecaySignal: 0.26,
  });
  if (stale < 0.53 || stale > 0.54) failures.push(`stale score outside expected range: ${stale}`);
}

function validateGeneratedMatchesSample(generatedValue, sampleValue, failures) {
  if (JSON.stringify(generatedValue) !== JSON.stringify(sampleValue)) {
    failures.push("sample JSON does not match deterministic generator output");
  }
}

function validateSchema(value, schemaNode, failures, pointer = "#") {
  if (schemaNode.type === "object" && !isRecord(value)) {
    failures.push(`${pointer} expected object`);
    return;
  }
  if (schemaNode.type === "array" && !Array.isArray(value)) {
    failures.push(`${pointer} expected array`);
    return;
  }
  if (schemaNode.type === "string" && typeof value !== "string") {
    failures.push(`${pointer} expected string`);
    return;
  }
  if ("const" in schemaNode && value !== schemaNode.const) {
    failures.push(`${pointer} expected const ${schemaNode.const}`);
  }
  if (Array.isArray(schemaNode.required)) {
    for (const key of schemaNode.required) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) failures.push(`${pointer} missing ${key}`);
    }
  }
  if (typeof schemaNode.minItems === "number" && Array.isArray(value) && value.length < schemaNode.minItems) {
    failures.push(`${pointer} expected minItems ${schemaNode.minItems}`);
  }
  if (schemaNode.properties && isRecord(value)) {
    for (const [key, childSchema] of Object.entries(schemaNode.properties)) {
      if (Object.prototype.hasOwnProperty.call(value, key)) {
        validateSchema(value[key], childSchema, failures, `${pointer}/${key}`);
      }
    }
  }
}

function validateParameterDrift(failures) {
  const yaml = fs.readFileSync(paramsPath, "utf8");
  const expected = {
    interaction_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.blackHole.interactionWeight,
    recency_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.blackHole.recencyWeight,
    repetition_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.blackHole.repetitionWeight,
    roi_penalty_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.blackHole.roiPenaltyWeight,
    growth_penalty_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.blackHole.growthPenaltyWeight,
    recency_growth_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.protoStar.recencyGrowthWeight,
    cross_signal_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.protoStar.crossSignalWeight,
    capability_relation_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.protoStar.capabilityRelationWeight,
    roi_potential_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.protoStar.roiPotentialWeight,
    uncertainty_penalty_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.protoStar.uncertaintyPenaltyWeight,
    inactive_days_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.stale.inactiveDaysWeight,
    low_recent_usage_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.stale.lowRecentUsageWeight,
    confidence_decay_weight: DEFAULT_UNIVERSE_STATE_PARAMETERS.scores.stale.confidenceDecayWeight,
    storm_conflict_threshold: DEFAULT_UNIVERSE_STATE_PARAMETERS.weather.stormConflictThreshold,
    black_hole_warning_threshold: DEFAULT_UNIVERSE_STATE_PARAMETERS.weather.blackHoleWarningThreshold,
    proto_star_notice_threshold: DEFAULT_UNIVERSE_STATE_PARAMETERS.weather.protoStarNoticeThreshold,
  };
  for (const [key, value] of Object.entries(expected)) {
    const match = yaml.match(new RegExp(`${key}:\\s*([0-9.]+)`));
    if (!match) {
      failures.push(`parameter missing for ${key}`);
      continue;
    }
    if (Math.abs(Number(match[1]) - value) > 0.0001) {
      failures.push(`parameter drift for ${key}: yaml=${match[1]} code=${value}`);
    }
  }
  for (const group of sample.diagnostics.score_weight_sums) {
    if (Math.abs(group.sum - 1) > 0.0001) failures.push(`weight group ${group.name} does not sum to 1`);
  }
}

function validatePrivacy(value, failures) {
  const text = JSON.stringify(value);
  const forbiddenPatterns = [
    /sk-[A-Za-z0-9_-]{10,}/,
    /ghp_[A-Za-z0-9_]{10,}/,
    /-----BEGIN [A-Z ]+PRIVATE KEY-----/,
    /\/Users\/[^"]+/,
    /raw transcript/i,
    /plaintext secret/i,
  ];
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(text)) failures.push(`privacy forbidden pattern matched: ${pattern}`);
  }
  const privacy = value.diagnostics?.privacy_status;
  if (!privacy) {
    failures.push("missing privacy_status");
    return;
  }
  if (
    privacy.raw_private_data_included ||
    privacy.plaintext_secrets_included ||
    privacy.local_absolute_paths_included ||
    privacy.writeback_allowed
  ) {
    failures.push("privacy status is not fully false");
  }
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
