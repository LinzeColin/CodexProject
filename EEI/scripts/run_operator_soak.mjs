#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";

const ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const SOAK_SCRIPT = path.join(ROOT, "scripts/run_soak_smoke.mjs");
const DEFAULT_CI_DURATION_SECONDS = 3;
const DEFAULT_OPERATOR_WINDOW_SECONDS = 300;

function usage() {
  return [
    "Usage: node scripts/run_operator_soak.mjs [options]",
    "",
    "Options:",
    "  --mode <name>                 Run label, e.g. ci_smoke, operator_4h, operator_24h",
    "  --duration-seconds <number>   Total requested duration in seconds",
    "  --duration-hours <number>     Total requested duration in hours",
    "  --window-seconds <number>     Per-window child harness duration",
    "  --output <path>               Summary JSON output path",
    "  --checkpoint <path>           JSONL checkpoint path for resume/audit",
    "  --resume                      Continue from successful windows in checkpoint",
    "  --fail-on-budget              Exit non-zero when a child window fails budgets",
    "  --quiet                       Suppress JSON summary stdout"
  ].join("\n");
}

function parseArgs(argv) {
  const args = {
    mode: "ci_smoke",
    durationSeconds: null,
    durationHours: null,
    windowSeconds: null,
    output: "/tmp/eei-operator-soak.json",
    checkpoint: "/tmp/eei-operator-soak.checkpoints.jsonl",
    resume: false,
    failOnBudget: false,
    quiet: false
  };
  for (let index = 2; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--mode") {
      args.mode = argv[++index];
    } else if (item === "--duration-seconds") {
      args.durationSeconds = Number.parseFloat(argv[++index]);
    } else if (item === "--duration-hours") {
      args.durationHours = Number.parseFloat(argv[++index]);
    } else if (item === "--window-seconds") {
      args.windowSeconds = Number.parseFloat(argv[++index]);
    } else if (item === "--output") {
      args.output = argv[++index];
    } else if (item === "--checkpoint") {
      args.checkpoint = argv[++index];
    } else if (item === "--resume") {
      args.resume = true;
    } else if (item === "--fail-on-budget") {
      args.failOnBudget = true;
    } else if (item === "--quiet") {
      args.quiet = true;
    } else if (item === "--help" || item === "-h") {
      console.log(usage());
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${item}`);
    }
  }
  if (args.durationSeconds !== null && args.durationHours !== null) {
    throw new Error("Use only one of --duration-seconds or --duration-hours");
  }
  if (args.durationHours !== null) {
    args.durationSeconds = args.durationHours * 3600;
  }
  if (args.durationSeconds === null) {
    args.durationSeconds = DEFAULT_CI_DURATION_SECONDS;
  }
  if (!Number.isFinite(args.durationSeconds) || args.durationSeconds <= 0) {
    throw new Error("--duration-seconds/--duration-hours must be positive");
  }
  if (args.windowSeconds === null) {
    args.windowSeconds = args.durationSeconds <= DEFAULT_CI_DURATION_SECONDS ? args.durationSeconds : null;
  }
  if (
    args.windowSeconds !== null &&
    (!Number.isFinite(args.windowSeconds) || args.windowSeconds <= 0)
  ) {
    throw new Error("--window-seconds must be positive");
  }
  return args;
}

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

async function readSoakParameters() {
  const catalog = await readFile(path.join(ROOT, "data/parameter_catalog.csv"), "utf8");
  const lines = catalog.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const header = parseCsvLine(lines[0]);
  const keyIndex = header.indexOf("parameter_key");
  const valueIndex = header.indexOf("default_value");
  const values = {};
  for (const line of lines.slice(1)) {
    const row = parseCsvLine(line);
    if (row[keyIndex] === "soak.short_duration_hours") {
      values.short_duration_hours = Number.parseFloat(row[valueIndex]);
    }
    if (row[keyIndex] === "soak.long_duration_hours") {
      values.long_duration_hours = Number.parseFloat(row[valueIndex]);
    }
    if (row[keyIndex] === "soak.operator_window_seconds") {
      values.operator_window_seconds = Number.parseFloat(row[valueIndex]);
    }
  }
  if (!values.short_duration_hours || !values.long_duration_hours) {
    throw new Error("Missing soak duration parameters");
  }
  if (!values.operator_window_seconds) {
    values.operator_window_seconds = DEFAULT_OPERATOR_WINDOW_SECONDS;
  }
  return values;
}

function displayPath(filePath) {
  const absolutePath = path.resolve(ROOT, filePath);
  const relativePath = path.relative(ROOT, absolutePath);
  if (!relativePath.startsWith("..") && !path.isAbsolute(relativePath)) {
    return relativePath;
  }
  return absolutePath;
}

function numberOrNull(value, digits = 4) {
  return Number.isFinite(value) ? Number(value.toFixed(digits)) : null;
}

function maxExpectedWallSeconds(measuredDurationSeconds) {
  if (!Number.isFinite(measuredDurationSeconds) || measuredDurationSeconds <= 0) {
    return null;
  }
  return measuredDurationSeconds + Math.max(60, measuredDurationSeconds * 0.25);
}

async function readJsonIfPresent(filePath) {
  try {
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function readCheckpointEntries(checkpointPath) {
  try {
    const content = await readFile(checkpointPath, "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line));
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return [];
    }
    throw error;
  }
}

function isSuccessfulWindow(entry) {
  return entry?.window?.status === "PASS";
}

function summarizeChildPayload(payload) {
  if (!payload) {
    return {
      child_status: "NO_OUTPUT",
      measured_duration_seconds: 0,
      browser_heap_growth_bytes: null,
      browser_dom_node_growth: null,
      browser_slices_completed: null,
      browser_measurement_error: null,
      worker_jobs_completed: null,
      worker_jobs_total: null,
      worker_event_loop_lag_p95_ms: null
    };
  }
  return {
    child_status: payload.status,
    measured_duration_seconds: payload.measured_duration_seconds,
    browser_heap_growth_bytes: payload.browser?.heap_growth_bytes ?? null,
    browser_dom_node_growth: payload.browser?.dom_node_growth ?? null,
    browser_slices_completed: payload.browser?.slices_completed ?? null,
    browser_measurement_error: payload.browser?.measurement_error?.message ?? null,
    worker_jobs_completed: payload.worker?.jobs_completed ?? null,
    worker_jobs_total: payload.worker?.jobs_total ?? null,
    worker_event_loop_lag_p95_ms: payload.worker?.event_loop_lag_ms?.p95 ?? null
  };
}

async function runWindow({ args, index, durationSeconds }) {
  const startedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const outputPath = path.join(os.tmpdir(), `eei-operator-soak-${process.pid}-${index}.json`);
  const childArgs = [
    SOAK_SCRIPT,
    "--mode",
    `${args.mode}:window-${index}`,
    "--duration-seconds",
    String(durationSeconds),
    "--output",
    outputPath,
    "--fail-on-budget",
    "--quiet"
  ];
  const startMs = performance.now();
  const result = spawnSync(process.execPath, childArgs, {
    cwd: ROOT,
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 8
  });
  const elapsedSeconds = (performance.now() - startMs) / 1000;
  const endedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const childPayload = await readJsonIfPresent(outputPath);
  const childSummary = summarizeChildPayload(childPayload);
  const maxWallSeconds = maxExpectedWallSeconds(childSummary.measured_duration_seconds);
  const wallClockWithinBudget =
    maxWallSeconds !== null && Number.isFinite(elapsedSeconds) && elapsedSeconds <= maxWallSeconds;
  const status =
    result.status === 0 &&
    childPayload &&
    childPayload.status !== "FAIL" &&
    wallClockWithinBudget
      ? "PASS"
      : "FAIL";
  return {
    schema_version: "eei-operator-soak-checkpoint-v1",
    task_id: "T1307",
    acceptance_ids: ["A209"],
    generated_at: endedAt,
    window: {
      index,
      status,
      child_status: childSummary.child_status,
      requested_duration_seconds: numberOrNull(durationSeconds),
      measured_duration_seconds: numberOrNull(childSummary.measured_duration_seconds),
      elapsed_wall_seconds: numberOrNull(elapsedSeconds),
      started_at: startedAt,
      ended_at: endedAt,
      output_path: displayPath(outputPath),
      browser_heap_growth_bytes: childSummary.browser_heap_growth_bytes,
      browser_dom_node_growth: childSummary.browser_dom_node_growth,
      browser_slices_completed: childSummary.browser_slices_completed,
      browser_measurement_error: childSummary.browser_measurement_error,
      worker_jobs_completed: childSummary.worker_jobs_completed,
      worker_jobs_total: childSummary.worker_jobs_total,
      worker_event_loop_lag_p95_ms: childSummary.worker_event_loop_lag_p95_ms
    },
    child_harness: {
      script: "scripts/run_soak_smoke.mjs",
      exit_status: result.status,
      signal: result.signal,
      wall_clock_within_budget: wallClockWithinBudget,
      max_expected_wall_seconds: numberOrNull(maxWallSeconds),
      stderr_tail: result.stderr ? result.stderr.slice(-2000) : ""
    },
    child_payload: childPayload
      ? {
          schema_version: childPayload.schema_version,
          status: childPayload.status,
          mode: childPayload.mode,
          budgets: childPayload.budgets,
          coverage: childPayload.coverage,
          worker_supervisor_binding: childPayload.worker_supervisor_binding
        }
      : null
  };
}

function buildCommands(args, outputPath, checkpointPath) {
  return {
    ci_readiness:
      "node scripts/run_operator_soak.mjs --mode ci_smoke --duration-seconds 3 --window-seconds 3 --output /tmp/eei-operator-soak.json --checkpoint /tmp/eei-operator-soak.checkpoints.jsonl --fail-on-budget --quiet",
    operator_4h:
      "node scripts/run_operator_soak.mjs --mode operator_4h --duration-hours 4 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_4h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl --fail-on-budget",
    operator_24h:
      "node scripts/run_operator_soak.mjs --mode operator_24h --duration-hours 24 --window-seconds 300 --output artifacts/tests/a209/t1307_operator_soak_24h.json --checkpoint artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl --fail-on-budget",
    resume_current: `node scripts/run_operator_soak.mjs --mode ${args.mode} --duration-seconds ${args.durationSeconds} --window-seconds ${args.windowSeconds} --output ${displayPath(outputPath)} --checkpoint ${displayPath(checkpointPath)} --resume --fail-on-budget`
  };
}

function buildSummary({ args, parameters, checkpointPath, outputPath, windows, startedAt, endedAt }) {
  const completedDurationSeconds = windows
    .filter((window) => window.status === "PASS")
    .reduce((total, window) => total + (window.measured_duration_seconds || 0), 0);
  const failedWindows = windows.filter((window) => window.status === "FAIL");
  const shortTargetSeconds = parameters.short_duration_hours * 3600;
  const longTargetSeconds = parameters.long_duration_hours * 3600;
  const coversShortTarget = completedDurationSeconds >= shortTargetSeconds;
  const coversLongTarget = completedDurationSeconds >= longTargetSeconds;
  const firstPayload =
    windows.find((window) => window.child_payload)?.child_payload || null;
  const workerSupervisorBinding =
    firstPayload?.worker_supervisor_binding ||
    windows
      .map((window) => window.worker_supervisor_binding)
      .find((binding) => binding && binding.status) ||
    null;
  const status = failedWindows.length === 0 ? "PASS" : "FAIL";
  return {
    schema_version: "eei-operator-soak-runner-v1",
    system_name: "EEI",
    task_id: "T1307",
    acceptance_ids: ["A209"],
    status,
    mode: args.mode,
    generated_at: endedAt,
    environment: {
      node: process.version,
      platform: `${os.platform()}-${os.release()}-${os.arch()}`,
      cpu_count: os.cpus().length
    },
    configured_targets: {
      short_duration_hours: parameters.short_duration_hours,
      long_duration_hours: parameters.long_duration_hours,
      operator_window_seconds: parameters.operator_window_seconds
    },
    runner: {
      script: "scripts/run_operator_soak.mjs",
      child_harness: "scripts/run_soak_smoke.mjs",
      requested_duration_seconds: numberOrNull(args.durationSeconds),
      window_seconds: numberOrNull(args.windowSeconds),
      completed_duration_seconds: numberOrNull(completedDurationSeconds),
      windows_completed: windows.filter((window) => window.status === "PASS").length,
      windows_failed: failedWindows.length,
      resume_requested: args.resume,
      checkpoint_path: displayPath(checkpointPath),
      output_path: displayPath(outputPath),
      started_at: startedAt,
      ended_at: endedAt
    },
    coverage: {
      browser_soak_measured: windows.some((window) => window.status === "PASS"),
      worker_soak_measured: windows.some((window) => window.status === "PASS"),
      checkpoint_resume_supported: true,
      windowed_operator_run_supported: true,
      covers_4h_target: coversShortTarget,
      covers_24h_target: coversLongTarget,
      full_4h_24h_measured: coversShortTarget && coversLongTarget,
      worker_supervisor_binding_available:
        workerSupervisorBinding?.status === "PASS" &&
        workerSupervisorBinding?.process_manager === "docker_compose"
    },
    a209_release_gate: {
      status:
        status === "FAIL"
          ? "FAILED"
          : coversShortTarget && coversLongTarget
            ? "EVIDENCE_READY_FOR_RELEASE_MANAGER_REVIEW"
            : "PARTIAL_UNTIL_4H_24H_OPERATOR_EVIDENCE",
      release_gate_closed_by_runner: false,
      closure_rule:
        "A209 stays IN PROGRESS until both 4h and 24h operator artifacts are committed, referenced in release evidence, and validated by CI.",
      required_operator_artifacts: [
        "artifacts/tests/a209/t1307_operator_soak_4h.json",
        "artifacts/tests/a209/t1307_operator_soak_4h.checkpoints.jsonl",
        "artifacts/tests/a209/t1307_operator_soak_24h.json",
        "artifacts/tests/a209/t1307_operator_soak_24h.checkpoints.jsonl"
      ]
    },
    worker_supervisor_binding: workerSupervisorBinding,
    windows: windows.map((window) => ({
      index: window.index,
      status: window.status,
      child_status: window.child_status,
      requested_duration_seconds: window.requested_duration_seconds,
      measured_duration_seconds: window.measured_duration_seconds,
      elapsed_wall_seconds: window.elapsed_wall_seconds,
      started_at: window.started_at,
      ended_at: window.ended_at,
      output_path: window.output_path,
      browser_heap_growth_bytes: window.browser_heap_growth_bytes,
      browser_dom_node_growth: window.browser_dom_node_growth,
      browser_slices_completed: window.browser_slices_completed,
      browser_measurement_error: window.browser_measurement_error,
      worker_jobs_completed: window.worker_jobs_completed,
      worker_jobs_total: window.worker_jobs_total,
      worker_event_loop_lag_p95_ms: window.worker_event_loop_lag_p95_ms
    })),
    commands: buildCommands(args, outputPath, checkpointPath),
    rollback: [
      "Stop any long-running operator soak process with Ctrl-C; resume later with --resume using the same checkpoint.",
      "Run docker compose --profile worker stop worker if the worker process-manager binding is active.",
      "Do not promote A209; leave task and acceptance statuses IN PROGRESS until committed 4h and 24h evidence exists."
    ],
    remaining_to_close_a209:
      status === "FAIL"
        ? ["Fix failing budget/window evidence and rerun the operator soak from the checkpoint."]
        : coversShortTarget && coversLongTarget
          ? [
              "Commit the 4h and 24h operator artifacts.",
              "Regenerate release evidence and only then request A209 closure review."
            ]
          : [
              "Run the 4h operator soak command and commit the JSON plus checkpoint JSONL.",
              "Run the 24h operator soak command and commit the JSON plus checkpoint JSONL.",
              "Regenerate release evidence and keep A209 IN PROGRESS until CI validates the committed artifacts."
            ]
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const parameters = await readSoakParameters();
  if (args.windowSeconds === null) {
    args.windowSeconds = parameters.operator_window_seconds;
  }
  if (args.windowSeconds > args.durationSeconds) {
    args.windowSeconds = args.durationSeconds;
  }
  const outputPath = path.resolve(ROOT, args.output);
  const checkpointPath = path.resolve(ROOT, args.checkpoint);
  await mkdir(path.dirname(outputPath), { recursive: true });
  await mkdir(path.dirname(checkpointPath), { recursive: true });

  let checkpointEntries = [];
  if (args.resume) {
    checkpointEntries = await readCheckpointEntries(checkpointPath);
  } else {
    await writeFile(checkpointPath, "");
  }

  const windows = checkpointEntries
    .filter(isSuccessfulWindow)
    .map((entry) => ({
      ...entry.window,
      child_payload: entry.child_payload
    }));
  let completedDurationSeconds = windows.reduce(
    (total, window) => total + (window.measured_duration_seconds || 0),
    0
  );
  let nextWindowIndex = windows.length + 1;
  const startedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

  while (completedDurationSeconds < args.durationSeconds) {
    const remainingSeconds = args.durationSeconds - completedDurationSeconds;
    const windowDuration = Math.min(args.windowSeconds, remainingSeconds);
    const entry = await runWindow({
      args,
      index: nextWindowIndex,
      durationSeconds: windowDuration
    });
    await appendFile(checkpointPath, `${JSON.stringify(entry)}\n`, "utf8");
    windows.push({
      ...entry.window,
      child_payload: entry.child_payload
    });
    if (entry.window.status === "FAIL") {
      break;
    }
    completedDurationSeconds += entry.window.measured_duration_seconds || windowDuration;
    nextWindowIndex += 1;
  }

  const endedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const payload = buildSummary({
    args,
    parameters,
    checkpointPath,
    outputPath,
    windows,
    startedAt,
    endedAt
  });
  await writeFile(outputPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
  if (!args.quiet) {
    console.log(JSON.stringify(payload, null, 2));
  }
  if (args.failOnBudget && payload.status === "FAIL") {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
