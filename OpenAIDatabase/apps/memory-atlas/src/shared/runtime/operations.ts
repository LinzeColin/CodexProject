import type { MemoryAtlas } from "../../types";
import { COMMAND_PALETTE_VERSION, CommandPaletteCommand, CommandPaletteModel, CommandWorkflowAction, CommandWorkflowResult, OWNER_DAILY_API_VERSION, OWNER_DAILY_RESULT_VERSION, OWNER_DAILY_STEP_IDS, OwnerDailyResult, OwnerDailyStepId, OwnerDailyStepResult, PROPOSAL_API_VERSION, ProposalActionResult, ProposalReviewPayload, S12P1CommandId, S12_P1_ACCEPTED_CORE_COMMAND_IDS, S12_P1_COMMAND_IDS, S12_P1_PERSONALIZATION_TARGETS, views } from "../atlas/constants";
import { FilteredAtlasSlice, RuntimeState } from "../atlas/contracts";
import { TRANSIENT_CACHE_PREFIXES, TRANSIENT_STORAGE_PREFIXES, WRITEBACK_QUEUE_KEY } from "../atlas/runtimeConfig";
import { addDays, formatChineseDate, formatUpdatedAt, parseDay } from "../atlas/utils";



export function buildCommandPaletteModel(atlas: MemoryAtlas, slice: FilteredAtlasSlice, runtimeState: RuntimeState): CommandPaletteModel {
  const pendingProposalCount = slice.memoryNodes.filter((node) => {
    const text = `${node.label} ${node.statement ?? ""} ${node.category ?? ""}`.toLowerCase();
    return node.category === "pending_proposal" || /proposal|待授权|提案|pending/.test(text);
  }).length;
  const latestDate = parseDay(slice.deltaStats.latestDate);
  const latestDateLabel = latestDate ? formatChineseDate(latestDate) : formatUpdatedAt(atlas.overview.generated_at);
  const weeklyReportNodeCount = slice.memoryNodes.filter((node) => {
    const day = parseDay(node.date);
    if (!day || !latestDate) return false;
    return day >= addDays(latestDate, -6) && day <= latestDate;
  }).length || slice.deltaStats.recentCount;
  const sourceCount = new Map((atlas.data_sources ?? []).map((source) => [source.id, source.node_count]));
  const commands: CommandPaletteCommand[] = [
    {
      id: "sync_chatgpt",
      label: "同步 ChatGPT",
      description: "从固定本地导入箱读取一个官方导出，并刷新脱敏后的页面数据。",
      humanAction: "只接受 Application Support 导入箱中的一个官方 ZIP；不读取浏览器 cookies、tokens 或登录状态。",
      dryRunCommand: "python3 scripts/atlasctl.py sync --source chatgpt --official-export <fixed-local-inbox> --dry-run",
      status: `${(sourceCount.get("memory_atlas") ?? 0).toLocaleString()} 条 ChatGPT/Memory Atlas 节点可复核`,
      viewTarget: null,
    },
    {
      id: "sync_codex",
      label: "同步 Codex",
      description: "读取本机 Codex sessions 的脱敏摘要，并刷新当前页面快照。",
      humanAction: "只读取 sessions 与 session index；不读取 auth、cookies 或明文凭据文件。",
      dryRunCommand: "python3 scripts/atlasctl.py sync --source codex --codex-home <configured-local-home> --dry-run",
      status: `${(sourceCount.get("codex") ?? 0).toLocaleString()} 条 Codex 节点可复核`,
      viewTarget: null,
    },
    {
      id: "generate_weekly_report",
      label: "生成本周报告",
      description: "从当前脱敏快照汇总近七天变化、决策、提案与建议。",
      humanAction: "用户明确执行后，只在本地安装副本生成一份 Markdown 周报。",
      dryRunCommand: "python3 scripts/build_memory_atlas_weekly_report.py --database-dir <installed-source>",
      status: `${weeklyReportNodeCount.toLocaleString()} 条近周/近期节点 · 最新 ${latestDateLabel}`,
      viewTarget: "summary",
    },
    {
      id: "view_pending_proposals",
      label: "查看待授权提案",
      description: "集中查看待授权提案候选；这里只做判断，不直接应用变更。",
      humanAction: "读取 proposal 状态机并打开总结视图；不会执行 apply 或 rollback。",
      dryRunCommand: "python3 scripts/atlasctl.py proposals --dry-run",
      status: `${pendingProposalCount.toLocaleString()} 条候选线索需要人工判断`,
      viewTarget: "summary",
    },
    {
      id: "generate_personalization_prompt",
      label: "生成个性化提示",
      description: "准备供 ChatGPT、Codex 和其他 agent 使用的最新个性化提示入口。",
      humanAction: "在本地安装副本生成 ChatGPT、Codex 和其他 agent 的中文说明及机器可复制文本。",
      dryRunCommand: "python3 scripts/atlasctl.py generate-personalization-prompt --target all --dry-run",
      status: `覆盖 ChatGPT / Codex / 其他代理 · 运行状态 ${runtimeState.lifecycle}`,
      viewTarget: "summary",
      personalizationTargets: S12_P1_PERSONALIZATION_TARGETS,
    },
    {
      id: "chatgpt_deep_explore",
      label: "打开 ChatGPT 深度探索",
      description: "把最新记忆分析报告和探索提示转成 ChatGPT 预填充入口。",
      humanAction: "用户明确执行后生成最新提示，并由浏览器打开仅预填页面；不会自动发送。",
      dryRunCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run",
      status: "默认仅预填 · 自动发送受控",
      viewTarget: null,
    },
  ];
  return {
    version: COMMAND_PALETTE_VERSION,
    commands,
    commandIds: [...S12_P1_COMMAND_IDS],
    acceptedCoreCommandIds: [...S12_P1_ACCEPTED_CORE_COMMAND_IDS],
    personalizationTargets: S12_P1_PERSONALIZATION_TARGETS,
    pendingProposalCount,
    weeklyReportNodeCount,
    latestDateLabel,
  };
}



export function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}



export function isProposalReviewPayload(value: unknown): value is ProposalReviewPayload {
  if (!isRecord(value) || value.schema_version !== "memory_atlas_proposal_review.v1_2_r4" || value.status !== "success") return false;
  if (value.proposal_api_version !== PROPOSAL_API_VERSION || !Array.isArray(value.proposals) || !Array.isArray(value.transactions)) return false;
  if (!isRecord(value.summary) || !isRecord(value.safety)) return false;
  const summary = value.summary;
  const summaryFields = ["proposal_count", "apply_ready_count", "review_only_count", "rollback_available_count", "interrupted_recovery_count", "manual_recovery_required_count"];
  if (!summaryFields.every((field) => Number.isInteger(summary[field]) && Number(summary[field]) >= 0)) return false;
  if (value.safety.raw_mutation !== false || value.safety.canonical_repo_mutation !== false || value.safety.remote_push !== false || value.safety.operation_content_returned !== false) return false;
  const proposalsValid = value.proposals.every((proposal) => {
    if (!isRecord(proposal) || typeof proposal.proposal_id !== "string" || typeof proposal.apply_ready !== "boolean") return false;
    if (!Array.isArray(proposal.target_files) || !proposal.target_files.every((item) => typeof item === "string")) return false;
    if (!Array.isArray(proposal.validation_ids) || !proposal.validation_ids.every((item) => typeof item === "string")) return false;
    const narrator = proposal.narrator;
    if (!isRecord(narrator)) return false;
    return ["what_changed_zh", "why_changed_zh", "affected_surfaces_zh", "how_to_verify_zh", "how_to_rollback_zh"]
      .every((field) => typeof narrator[field] === "string");
  });
  const transactionsValid = value.transactions.every((transaction) => (
    isRecord(transaction)
    && typeof transaction.transaction_id === "string"
    && typeof transaction.proposal_id === "string"
    && (transaction.state === "committed" || transaction.state === "manual_rollback_required")
    && Array.isArray(transaction.target_files)
    && transaction.target_files.every((item) => typeof item === "string")
    && typeof transaction.rollback_token === "string"
  ));
  return proposalsValid && transactionsValid;
}



export function isProposalActionResult(value: unknown): value is ProposalActionResult {
  if (!isRecord(value) || value.schema_version !== "memory_atlas_proposal_result.v1_2_r4") return false;
  if (!(value.action === "approve_apply" || value.action === "rollback")) return false;
  if (!(value.status === "success" || value.status === "validation_failed_rolled_back")) return false;
  if (!(value.state === "committed" || value.state === "rollback_or_needs_revision" || value.state === "rolled_back_by_human")) return false;
  if (typeof value.proposal_id !== "string" || typeof value.transaction_id !== "string" || typeof value.message_zh !== "string") return false;
  if (!isRecord(value.safety)) return false;
  return value.safety.human_approval_required === true
    && value.safety.raw_mutation === false
    && value.safety.canonical_repo_mutation === false
    && value.safety.remote_push === false;
}



export function isCommandWorkflowResult(value: unknown): value is CommandWorkflowResult {
  if (!isRecord(value) || value.schema_version !== "memory_atlas_command_result.v1_2_r3") return false;
  if (!S12_P1_COMMAND_IDS.includes(value.command_id as S12P1CommandId)) return false;
  if (!(["success", "needs_input", "error"] as const).includes(value.status as "success" | "needs_input" | "error")) return false;
  if (typeof value.title_zh !== "string" || typeof value.message_zh !== "string" || !Array.isArray(value.outputs)) return false;
  if (!isRecord(value.safety) || value.safety.sends_to_chatgpt !== false) return false;
  if (!value.outputs.every((output) => typeof output === "string")) return false;
  if (value.action !== undefined) {
    if (!isRecord(value.action)) return false;
    const action = value.action;
    if (!(["reload_atlas", "navigate_view", "open_url"] as const).includes(action.type as CommandWorkflowAction["type"])) return false;
    if (action.type === "navigate_view" && (typeof action.view !== "string" || !views.some((view) => view.key === action.view))) return false;
    if (action.type === "open_url" && typeof action.url !== "string") return false;
  }
  if (value.proposal_review !== undefined && !isProposalReviewPayload(value.proposal_review)) return false;
  return true;
}



export function isOwnerDailyMetricValue(value: unknown): boolean {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return true;
  return Array.isArray(value)
    && value.length <= 8
    && value.every((item) => typeof item === "string" || typeof item === "number" || typeof item === "boolean");
}



export function isOwnerDailyStepResult(value: unknown): value is OwnerDailyStepResult {
  if (!isRecord(value) || !OWNER_DAILY_STEP_IDS.includes(value.step_id as OwnerDailyStepId)) return false;
  if (!(value.status === "pass" || value.status === "failed")) return false;
  if (
    typeof value.order !== "number"
    || typeof value.label_zh !== "string"
    || typeof value.conclusion_zh !== "string"
    || typeof value.failure_zh !== "string"
    || typeof value.retryable !== "boolean"
    || typeof value.duration_ms !== "number"
  ) return false;
  if (!Array.isArray(value.invocation) || !value.invocation.every((item) => typeof item === "string")) return false;
  if (
    value.invocation[0] !== "python3"
    || value.invocation[1] !== "scripts/atlasctl.py"
    || !value.invocation.includes("--dry-run")
    || value.invocation.length > 8
  ) return false;
  if (!isRecord(value.metrics) || !Object.values(value.metrics).every(isOwnerDailyMetricValue)) return false;
  return value.status === "failed" ? value.retryable && Boolean(value.failure_zh.trim()) : !value.retryable;
}



export function isOwnerDailyResult(value: unknown): value is OwnerDailyResult {
  if (
    !isRecord(value)
    || value.schema_version !== OWNER_DAILY_RESULT_VERSION
    || value.api_version !== OWNER_DAILY_API_VERSION
    || !(value.action === "run" || value.action === "retry")
    || !(value.status === "PASS" || value.status === "PARTIAL_FAILURE")
    || value.profile !== "owner-daily"
    || value.dry_run !== true
    || typeof value.conclusion_zh !== "string"
    || typeof value.completed_count !== "number"
    || typeof value.failed_count !== "number"
    || !Array.isArray(value.retryable_step_ids)
    || !Array.isArray(value.steps)
    || !value.steps.every(isOwnerDailyStepResult)
    || !isRecord(value.safety)
  ) return false;
  if (
    value.safety.writes_files !== false
    || value.safety.remote_push !== false
    || value.safety.raw_mutation !== false
    || value.safety.sends_to_chatgpt !== false
    || value.safety.proposal_apply_execution !== false
    || value.safety.canonical_repo_mutation !== false
  ) return false;
  const stepIds = value.steps.map((step) => step.step_id);
  const failedIds = value.steps.filter((step) => step.status === "failed").map((step) => step.step_id);
  if (value.completed_count + value.failed_count !== value.steps.length || value.failed_count !== failedIds.length) return false;
  if (value.status === "PASS" ? failedIds.length !== 0 : failedIds.length === 0) return false;
  if (JSON.stringify(value.retryable_step_ids) !== JSON.stringify(failedIds)) return false;
  if (value.action === "run") return JSON.stringify(stepIds) === JSON.stringify(OWNER_DAILY_STEP_IDS);
  return OWNER_DAILY_STEP_IDS.includes(value.requested_step_id as OwnerDailyStepId)
    && stepIds.length === 1
    && stepIds[0] === value.requested_step_id;
}



export function mergeOwnerDailyRetry(current: OwnerDailyResult, retry: OwnerDailyResult): OwnerDailyResult {
  if (retry.action !== "retry" || !retry.requested_step_id || retry.steps.length !== 1) return current;
  const replacement = retry.steps[0];
  const steps = current.steps.map((step) => step.step_id === retry.requested_step_id ? replacement : step);
  const failedIds = steps.filter((step) => step.status === "failed").map((step) => step.step_id);
  const completedCount = steps.length - failedIds.length;
  return {
    ...current,
    status: failedIds.length === 0 ? "PASS" : "PARTIAL_FAILURE",
    conclusion_zh: failedIds.length === 0
      ? `Owner Daily 已完成 ${completedCount} 项 no-write 检查，没有发现步骤失败。`
      : `Owner Daily 已完成 ${completedCount} 项，${failedIds.length} 项未通过；可只重试失败步骤。`,
    completed_count: completedCount,
    failed_count: failedIds.length,
    retryable_step_ids: failedIds,
    steps,
  };
}



export function safeChatGPTPrefillUrl(value: string | undefined): string {
  if (!value) return "";
  try {
    const url = new URL(value);
    if (
      url.protocol !== "https:"
      || url.hostname !== "chatgpt.com"
      || url.port
      || url.username
      || url.password
      || (url.pathname !== "/" && url.pathname !== "")
      || url.hash
      || !url.searchParams.get("q")?.trim()
    ) {
      return "";
    }
    return url.toString();
  } catch {
    return "";
  }
}



export async function clearTransientBrowserState(): Promise<void> {
  try {
    window.sessionStorage.clear();
  } catch {
    // Browser privacy settings may block storage access during page release.
  }
  try {
    for (let index = window.localStorage.length - 1; index >= 0; index -= 1) {
      const key = window.localStorage.key(index);
      if (!key || key === WRITEBACK_QUEUE_KEY) continue;
      if (TRANSIENT_STORAGE_PREFIXES.some((prefix) => key.startsWith(prefix))) {
        window.localStorage.removeItem(key);
      }
    }
  } catch {
    // Keep release best-effort; the server shutdown signal is still sent.
  }
  try {
    if ("caches" in window) {
      const cacheKeys = await caches.keys();
      await Promise.all(
        cacheKeys
          .filter((key) => TRANSIENT_CACHE_PREFIXES.some((prefix) => key.startsWith(prefix)))
          .map((key) => caches.delete(key)),
      );
    }
  } catch {
    // Cache Storage may be unavailable for static previews or blocked profiles.
  }
  try {
    if ("serviceWorker" in navigator) {
      const registrations = await navigator.serviceWorker.getRegistrations();
      await Promise.all(
        registrations
          .filter((registration) => registration.scope.includes("memory-atlas") || registration.scope.includes("127.0.0.1"))
          .map((registration) => registration.unregister()),
      );
    }
  } catch {
    // Memory Atlas does not depend on a service worker; unregister is best-effort cleanup.
  }
}
