#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(scriptDir, "..");
const repoRoot = resolve(appRoot, "../..");

const packageSource = readFileSync(resolve(appRoot, "package.json"), "utf8");
const visualAudit = readFileSync(resolve(repoRoot, "scripts/audit_memory_atlas_visual_acceptance.py"), "utf8");
const params = readFileSync(resolve(repoRoot, "config/visualization/model_parameters.memory_river.yaml"), "utf8");
const deliveryRecord = readFileSync(resolve(repoRoot, "docs/MEMORY_ATLAS_DELIVERY_RECORD.md"), "utf8");
const changelog = readFileSync(resolve(repoRoot, "CHANGELOG.md"), "utf8");
const stageReview = readFileSync(resolve(repoRoot, "docs/reviews/memory_atlas_v1_1_5_stage5_review.md"), "utf8");
const phaseReviews = [
  "memory_atlas_v1_1_5_stage5_1_review.md",
  "memory_atlas_v1_1_5_stage5_2_review.md",
  "memory_atlas_v1_1_5_stage5_3_review.md",
].map((name) => readFileSync(resolve(repoRoot, `docs/reviews/${name}`), "utf8"));

const checks = [];

function requireCheck(name, condition, evidence, failure) {
  checks.push({ name, status: condition ? "PASS" : "FAIL", evidence: condition ? evidence : failure });
}

function hasAll(source, needles) {
  return needles.every((needle) => source.includes(needle));
}

requireCheck(
  "stage5_phase_reviews_complete",
  phaseReviews.every((source, index) => source.includes(`Stage 5.${index + 1} is review-passed`))
    && hasAll(stageReview, [
      "Stage 5 is review-passed",
      "5.1 River Rendering",
      "5.2 River Interaction",
      "5.3 Evidence Layers",
      "No raw/private/cookie/session/secret fields were introduced",
      "No Cloudflare deployment or Access policy change was performed",
    ]),
  "Stage 5.1/5.2/5.3 phase reviews and the whole-stage review all record PASS boundaries",
  "Stage 5 phase review or whole-stage review PASS evidence is missing",
);

requireCheck(
  "stage5_validators_and_visual_audit_cover_all_phases",
  hasAll(packageSource, [
    '"validate:memory-river-rendering": "node scripts/validate_memory_river_rendering.mjs"',
    '"validate:memory-river-interaction": "node scripts/validate_memory_river_interaction.mjs"',
    '"validate:memory-river-evidence": "node scripts/validate_memory_river_evidence_layers.mjs"',
    '"validate:memory-river-stage5": "node scripts/validate_memory_river_stage5.mjs"',
  ]) && hasAll(visualAudit, [
    "timeline_stage5_1_river_rendering_ready",
    "timeline_stage5_2_river_interaction_ready",
    "timeline_stage5_3_evidence_layers_ready",
  ]),
  "Package scripts and visual acceptance audit cover Stage 5.1 rendering, Stage 5.2 interaction, and Stage 5.3 evidence layers",
  "Stage 5 validators or visual audit hooks do not cover every phase",
);

requireCheck(
  "stage5_model_parameters_reviewed",
  hasAll(params, [
    "stage: \"5.3\"",
    "task: \"5.3 Evidence Layers\"",
    "review_status: stage_5_whole_stage_review_passed",
    "renderer_default: memory-river",
    "legacy_renderer: legacy",
    "pan_enabled: true",
    "brush_enabled: true",
    "black_hole_lifecycle_enabled: true",
    "proto_star_lifecycle_enabled: true",
    "stale_deprecated_fade_enabled: true",
    "raw_private_data_allowed: false",
    "writeback_allowed: false",
  ]),
  "Memory River parameters preserve rollback, interaction, evidence-layer and data-boundary settings after whole-stage review",
  "Stage 5 model parameters lack whole-stage review status or required safety/feature settings",
);

requireCheck(
  "stage5_delivery_record_current",
  hasAll(deliveryRecord, [
    "完成 Memory Atlas v1.1.5 Stage 5 整体复审",
    "Stage 5 整阶段复审通过",
    "Stage 5.3 已支持 black-hole lifecycle band",
  ]) && !deliveryRecord.includes("Timeline 增加 Stage 5.3 evidence layers、多阶段聚类摘要、相邻时间段差异解释。"),
  "Delivery record no longer lists Stage 5.3 evidence layers as pending and records the whole-stage review",
  "Delivery record still contains stale Stage 5.3 pending status or lacks whole-stage review evidence",
);

requireCheck(
  "stage5_changelog_current",
  hasAll(changelog, [
    "Memory Atlas v1.1.5 Stage 5 Whole-Stage Review",
    "Completed the Stage 5 whole-stage review",
    "No ingestion, raw/private data access, direct writeback",
    "Cloudflare live",
    "deploy, or external account operation was added.",
  ]),
  "Changelog records Stage 5 whole-stage review and preserves non-goal boundaries",
  "Changelog lacks Stage 5 whole-stage review status or boundary statement",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
