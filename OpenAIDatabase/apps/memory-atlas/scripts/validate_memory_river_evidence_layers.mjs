#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const appSource = readFileSync(resolve(appRoot, "src/App.tsx"), "utf8");
const cssSource = readFileSync(resolve(appRoot, "src/styles.css"), "utf8");
const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");
const modelParams = readFileSync(resolve(repoRoot, "config/visualization/model_parameters.memory_river.yaml"), "utf8");

const checks = [];

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

requireCheck(
  "black_hole_lifecycle_layer",
  hasAll(appSource, [
    'type MemoryRiverEvidenceKind = "black-hole-lifecycle" | "proto-star-lifecycle" | "stale-deprecated"',
    "buildBlackHoleLifecycleLayer",
    "isMemoryRiverBlackHoleEvent",
    "isBlackHoleCandidate(event.node)",
    "memory-river-black-hole-lifecycle",
    "black-hole-lifecycle",
    "与首页风险循环一致",
  ]) && hasAll(cssSource, [
    ".memory-river-evidence-layer.black-hole-lifecycle rect",
    ".memory-river-evidence-layer.black-hole-lifecycle path",
    ".memory-river-evidence-layer.black-hole-lifecycle circle",
  ]),
  "Memory River renders a home-consistent black-hole lifecycle band from stale/deprecated/temporary redacted derived signals",
  "Black-hole lifecycle evidence band or home-consistent signal mapping is missing",
);

requireCheck(
  "proto_star_lifecycle_layer",
  hasAll(appSource, [
    "buildProtoStarLifecycleLayer",
    "isMemoryRiverProtoStarEvent",
    "isProtoStarCandidate(event.node, recentStart, latest)",
    "memory-river-proto-star-lifecycle",
    "proto-star-lifecycle",
    "机会生命周期",
    "memoryRiverEvidencePath(points)",
  ]) && hasAll(cssSource, [
    ".memory-river-evidence-layer.proto-star-lifecycle path",
    ".memory-river-evidence-layer.proto-star-lifecycle circle",
  ]),
  "Memory River renders a proto-star lifecycle growth path using opportunity, decision, project and high-leverage derived signals",
  "Proto-star lifecycle path, markers, or opportunity signal mapping is missing",
);

requireCheck(
  "stale_deprecated_fade_layer",
  hasAll(appSource, [
    "buildStaleDeprecatedLayer",
    "isMemoryRiverStaleDeprecatedEvent",
    "stale_short_term",
    "deprecated_info",
    "temporary_or_sensitive",
    "memory-river-stale-deprecated-layer",
    "stale-deprecated",
    "冷却/废弃层",
  ]) && hasAll(cssSource, [
    ".memory-river-evidence-layer.stale-deprecated rect",
    ".memory-river-evidence-layer.stale-deprecated rect:nth-of-type(3n + 1)",
    ".memory-river-evidence-layer.stale-deprecated rect:nth-of-type(3n + 2)",
  ]),
  "Memory River renders a stale/deprecated fade layer that keeps cooling status readable without exposing raw data",
  "Stale/deprecated fade layer or cooling-state signal mapping is missing",
);

requireCheck(
  "evidence_layers_rendered_in_memory_river",
  hasAll(appSource, [
    "interface MemoryRiverEvidenceLayer",
    "evidenceLayers: MemoryRiverEvidenceLayer[]",
    "buildMemoryRiverEvidenceLayers(events, laneLookup, visibleLanes)",
    "riverDisplay.evidenceLayers.map((layer)",
    'data-evidence-layer={layer.kind}',
    'data-evidence-segment={layer.kind}',
    "redacted derived signals",
  ]),
  "Memory River layout carries evidence layers and renders them as SVG groups with explicit data-evidence-layer markers",
  "Memory River evidence layer data structure or SVG render hook is missing",
);

requireCheck(
  "evidence_parameters_and_audit_wired",
  packageSource.includes('"validate:memory-river-evidence": "node scripts/validate_memory_river_evidence_layers.mjs"')
    && visualAudit.includes("timeline_stage5_3_evidence_layers_ready")
    && hasAll(modelParams, [
      'stage: "5.3"',
      'task: "5.3 Evidence Layers"',
      "black_hole_lifecycle_enabled: true",
      "proto_star_lifecycle_enabled: true",
      "stale_deprecated_fade_enabled: true",
      "home_consistency_source: isBlackHoleCandidate / isProtoStarCandidate",
      "evidence_payload: redacted_derived_signal_only",
    ]),
  "Package script, visual audit, and Memory River parameters cover Stage 5.3 evidence-layer contracts",
  "Stage 5.3 package script, visual audit hook, or Memory River parameters are missing",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
