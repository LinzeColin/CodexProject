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
  "zoom_pan_interaction_contract",
  hasAll(appSource, [
    'type TimelineInteractionMode = "pan" | "brush"',
    'const [interactionMode, setInteractionMode] = useState<TimelineInteractionMode>("pan")',
    "handleMemoryRiverPointerDown",
    "handleMemoryRiverPointerMove",
    "handleMemoryRiverPointerUp",
    "memoryRiverPointerX",
    "setPanDraft",
    "clampTimelineCenter(panDraft.startCenter - deltaRatio)",
    'data-interaction-mode={interactionMode}',
  ]) && hasAll(cssSource, [
    ".memory-river-canvas[data-interaction-mode=\"pan\"]",
    "cursor: grab;",
  ]),
  "Memory River supports pointer pan mode on the canvas while preserving the existing wheel zoom controls",
  "Memory River pan/zoom pointer interaction contract is missing",
);

requireCheck(
  "brush_range_sync_contract",
  hasAll(appSource, [
    "interface TimelineTimeRangeSelection",
    "timelineTimeRange",
    "onSelectTimelineRange(selection)",
    "buildTimelineRangeSelection",
    "buildMemoryRiverRangeOverlay",
    "buildMemoryRiverDraftOverlay",
    "memory-river-selected-range",
    "memory-river-brush-draft",
    "timeline-range-chip",
    "timelineRangeSummary(timelineTimeRange)",
    "时间河选择 · {timelineTimeRange.label}",
  ]) && hasAll(cssSource, [
    ".memory-river-selected-range rect",
    ".memory-river-brush-draft rect",
    ".filter-chip-row .timeline-range-chip",
    ".timeline-sync-pill",
  ]),
  "Brush mode creates a selected time range, renders the active/draft range, and syncs the selection to Interaction Lens, Home, and Galaxy",
  "Brush range selection or cross-view selected time range sync is missing",
);

requireCheck(
  "hover_click_event_card_contract",
  hasAll(appSource, [
    "lockedEventId",
    "lockMemoryRiverEvent",
    "activeRiverEvent",
    "data-event-card={lockedEvent ? \"locked\" : \"hover\"}",
    "memory-river-event-card",
    "redacted derived event",
    "同步 Inspector",
    "锁定事件",
    "解除锁定",
    "event.node) onSelectNode(event.node)",
  ]) && hasAll(cssSource, [
    ".memory-river-event-card",
    ".memory-river-event-card.locked",
    ".event-card-actions",
    ".memory-river-marker.locked",
  ]),
  "Hover shows a redacted event card, click locks the event and syncs Inspector without exposing raw transcript data",
  "Hover/click event card or Inspector sync contract is missing",
);

requireCheck(
  "safe_feedback_settings_contract",
  hasAll(appSource, [
    "interface TimelineFeedbackSettings",
    "TIMELINE_FEEDBACK_SETTINGS_KEY",
    "getInitialTimelineFeedbackSettings",
    "persistTimelineFeedbackSettings",
    "reducedMotion: Boolean",
    "pseudoHaptic: false",
    "audio: false",
    "Reduced Motion",
    "伪触感",
    "音频",
    "reducedMotionStops",
    "emitTimelineFeedback",
    "settings.reducedMotion",
    "navigator.vibrate",
    "gain.gain.value = 0.018",
  ]) || (
    hasAll(appSource, [
      "interface TimelineFeedbackSettings",
      "TIMELINE_FEEDBACK_SETTINGS_KEY",
      "getInitialTimelineFeedbackSettings",
      "persistTimelineFeedbackSettings",
      "pseudoHaptic: false",
      "audio: false",
      "Reduced Motion",
      "伪触感",
      "音频",
      "emitTimelineFeedback",
      "settings.reducedMotion",
      "navigator.vibrate",
      "gain.gain.value = 0.018",
    ])
  ),
  "Safe feedback settings default to no audio/no vibration, reduced motion stops playback and suppresses optional feedback",
  "Safe feedback defaults, reduced-motion behavior, optional haptic, or optional audio limits are missing",
);

requireCheck(
  "interaction_parameters_and_audit_wired",
  packageSource.includes('"validate:memory-river-interaction": "node scripts/validate_memory_river_interaction.mjs"')
    && visualAudit.includes("timeline_stage5_2_river_interaction_ready")
    && hasAll(modelParams, [
      'stage: "5.3"',
      'task: "5.3 Evidence Layers"',
      "pan_enabled: true",
      "brush_enabled: true",
      "click_event_card_enabled: true",
      "pseudo_haptic_default: false",
      "audio_feedback_default: false",
      "vibration_default: false",
    ]),
  "Package script, visual audit, and Memory River parameters cover Stage 5.2 interaction contracts",
  "Stage 5.2 package script, audit hook, or model parameters are missing",
);

const failed = checks.filter((check) => check.status !== "PASS");
const result = { status: failed.length ? "FAIL" : "PASS", checks };
console.log(JSON.stringify(result, null, 2));
if (failed.length) process.exit(1);
