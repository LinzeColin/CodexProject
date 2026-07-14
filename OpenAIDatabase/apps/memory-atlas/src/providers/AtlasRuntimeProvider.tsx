import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ViewKey } from "../types";
import {
  COMMAND_API_VERSION,
  COMMAND_PALETTE_VERSION,
  COMMAND_WORKFLOW_VERSION,
  LOCAL_APP_HANDOFF_URL,
  OWNER_DAILY_API_VERSION,
  OWNER_DAILY_UI_VERSION,
  PROPOSAL_API_VERSION,
  PROPOSAL_WORKFLOW_VERSION,
  S12_P1_PERSONALIZATION_COMMAND_ID,
  S12_P1_PERSONALIZATION_TARGETS,
  S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID,
  S12_P3_CHATGPT_DEEP_EXPLORE_VERSION,
  type CommandExecutionState,
  type CommandPaletteCommand,
  type CommandPaletteModel,
  type OwnerDailyResult,
  type ProposalReviewPayload,
  type S12P1CommandId,
} from "../shared/atlas/constants";
import type { RuntimeState } from "../shared/atlas/contracts";
import { INITIAL_COMMAND_EXECUTION_STATE, LOCAL_RUNTIME_HEARTBEAT_MS } from "../shared/atlas/runtimeConfig";
import {
  buildCommandPaletteModel,
  clearTransientBrowserState,
  isCommandWorkflowResult,
  isRecord,
  safeChatGPTPrefillUrl,
} from "../shared/runtime/operations";
import { useAtlasData } from "./AtlasDataProvider";
import { useAtlasWorkspace } from "./AtlasWorkspaceProvider";

export interface AtlasRuntimeContextValue {
  closeOwnerDaily: () => void;
  closeProposalReview: () => void;
  commandExecution: CommandExecutionState;
  commandPaletteModel: CommandPaletteModel;
  executeCommand: (command: CommandPaletteCommand) => Promise<void>;
  openOwnerDaily: () => void;
  ownerDailyResult: OwnerDailyResult | null;
  ownerDailyWorkspaceOpen: boolean;
  proposalReview: ProposalReviewPayload | null;
  runtimeState: RuntimeState;
  selectCommand: (command: CommandPaletteCommand) => void;
  selectedCommandId: S12P1CommandId;
  setOwnerDailyResult: (result: OwnerDailyResult | null) => void;
}

type RuntimeCapabilityState = Pick<RuntimeState, "serverMode" | "commandApiAvailable" | "proposalApiAvailable" | "ownerDailyApiAvailable">;

const AtlasRuntimeContext = createContext<AtlasRuntimeContextValue | null>(null);

export function AtlasRuntimeProvider({ children }: PropsWithChildren) {
  const { lifecycle, reloadAtlas, runStartedAt, snapshotLoadedAt } = useAtlasData();
  const { scopedAtlas, slice } = useAtlasWorkspace();
  const [capabilities, setCapabilities] = useState<RuntimeCapabilityState>({
    serverMode: "检测中",
    commandApiAvailable: false,
    proposalApiAvailable: false,
    ownerDailyApiAvailable: false,
  });
  const [selectedCommandId, setSelectedCommandId] = useState<S12P1CommandId>("sync_chatgpt");
  const [commandExecution, setCommandExecution] = useState<CommandExecutionState>(INITIAL_COMMAND_EXECUTION_STATE);
  const [proposalReview, setProposalReview] = useState<ProposalReviewPayload | null>(null);
  const [ownerDailyWorkspaceOpen, setOwnerDailyWorkspaceOpen] = useState(false);
  const [ownerDailyResult, setOwnerDailyResult] = useState<OwnerDailyResult | null>(null);
  const runtimeState = useMemo<RuntimeState>(() => ({
    runStartedAt,
    snapshotLoadedAt,
    lifecycle,
    ...capabilities,
  }), [capabilities, lifecycle, runStartedAt, snapshotLoadedAt]);
  const commandPaletteModel = useMemo(
    () => buildCommandPaletteModel(scopedAtlas, slice, runtimeState),
    [runtimeState, scopedAtlas, slice],
  );

  useEffect(() => {
    let cancelled = false;
    let heartbeatTimer = 0;
    let heartbeatEnabled = false;
    let released = false;

    const release = (reason: "page_release" | "react_unmount" = "page_release") => {
      if (!heartbeatEnabled || released) return;
      released = true;
      window.clearInterval(heartbeatTimer);
      void clearTransientBrowserState();
      const payload = new Blob([JSON.stringify({ reason, at: new Date().toISOString() })], { type: "application/json" });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/__memory_atlas_release", payload);
        return;
      }
      void fetch("/__memory_atlas_release", { method: "POST", body: payload, keepalive: true }).catch(() => undefined);
    };

    const handlePageRelease = () => release("page_release");
    const heartbeat = () => {
      if (!heartbeatEnabled) return;
      void fetch("/__memory_atlas_heartbeat", { method: "POST", cache: "no-store", keepalive: true }).catch(() => undefined);
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") heartbeat();
    };

    fetch("/__memory_atlas_runtime_state", { cache: "no-store" })
      .then(async (response) => {
        if (cancelled || !response.ok) return;
        const payload: unknown = await response.json().catch(() => null);
        if (!isRecord(payload) || payload.status !== "running") return;
        heartbeatEnabled = true;
        setCapabilities({
          serverMode: "本地自释放",
          commandApiAvailable: payload.command_api_version === COMMAND_API_VERSION,
          proposalApiAvailable: payload.proposal_api_version === PROPOSAL_API_VERSION,
          ownerDailyApiAvailable: payload.owner_daily_api_version === OWNER_DAILY_API_VERSION,
        });
        heartbeat();
        heartbeatTimer = window.setInterval(heartbeat, LOCAL_RUNTIME_HEARTBEAT_MS);
        window.addEventListener("pagehide", handlePageRelease);
        window.addEventListener("beforeunload", handlePageRelease);
        document.addEventListener("visibilitychange", handleVisibilityChange);
      })
      .catch(() => {
        if (!cancelled) setCapabilities({ serverMode: "静态托管", commandApiAvailable: false, proposalApiAvailable: false, ownerDailyApiAvailable: false });
      });

    const fallbackTimer = window.setTimeout(() => {
      if (!heartbeatEnabled && !cancelled) {
        setCapabilities({ serverMode: "静态托管", commandApiAvailable: false, proposalApiAvailable: false, ownerDailyApiAvailable: false });
      }
    }, 1200);

    return () => {
      cancelled = true;
      window.clearInterval(heartbeatTimer);
      window.clearTimeout(fallbackTimer);
      window.removeEventListener("pagehide", handlePageRelease);
      window.removeEventListener("beforeunload", handlePageRelease);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      release("react_unmount");
    };
  }, []);

  const selectCommand = useCallback((command: CommandPaletteCommand) => {
    setSelectedCommandId(command.id);
    setCommandExecution((current) => current.status === "running" ? current : INITIAL_COMMAND_EXECUTION_STATE);
  }, []);

  const executeCommand = useCallback(async (command: CommandPaletteCommand) => {
    if (commandExecution.status === "running") return;
    const proposalApiRequired = command.id === "view_pending_proposals";
    if (
      runtimeState.serverMode !== "本地自释放" ||
      !runtimeState.commandApiAvailable ||
      (proposalApiRequired && !runtimeState.proposalApiAvailable)
    ) {
      setCommandExecution({
        commandId: command.id,
        status: "local_required",
        title: runtimeState.serverMode === "本地自释放" ? "需要更新本地 app" : "需要本地 app",
        message: runtimeState.serverMode === "本地自释放"
          ? "当前本地运行服务不支持受控命令，请在最终交付后更新 Memory Atlas app。"
          : "此操作仅在本地 Memory Atlas app 执行。",
        outputs: [],
        inputHint: "",
        fallbackUrl: LOCAL_APP_HANDOFF_URL,
        navigationView: null,
      });
      return;
    }

    let chatgptWindow: Window | null = null;
    if (command.id === "chatgpt_deep_explore") {
      chatgptWindow = window.open("about:blank", "_blank");
      if (chatgptWindow) {
        try {
          chatgptWindow.opener = null;
          chatgptWindow.document.title = "正在准备 ChatGPT 深度探索";
          chatgptWindow.document.body.textContent = "正在准备仅预填的 ChatGPT 页面...";
        } catch {
          // The fallback link remains available if a browser blocks this temporary page.
        }
      }
    }

    setCommandExecution({
      commandId: command.id,
      status: "running",
      title: `正在执行：${command.label}`,
      message: "本地受控操作正在运行，请稍候。",
      outputs: [],
      inputHint: "",
      fallbackUrl: "",
      navigationView: null,
    });

    try {
      const response = await fetch("/__memory_atlas_command", {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command_id: command.id }),
      });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        const message = isRecord(payload) && typeof payload.message_zh === "string"
          ? payload.message_zh
          : `本地命令请求失败（HTTP ${response.status}）。`;
        throw new Error(message);
      }
      if (!isCommandWorkflowResult(payload) || payload.command_id !== command.id) {
        throw new Error("本地命令返回格式未通过校验，已停止后续动作。");
      }
      if (command.id === "view_pending_proposals" && payload.status === "success") {
        if (!payload.proposal_review) throw new Error("本地 proposal 复核资料缺失，已停止打开授权界面。");
        setProposalReview(payload.proposal_review);
      }

      let fallbackUrl = "";
      let navigationView: ViewKey | null = null;
      if (payload.status === "success" && payload.action?.type === "reload_atlas") await reloadAtlas();
      if (payload.status === "success" && payload.action?.type === "navigate_view" && payload.action.view) {
        navigationView = payload.action.view;
      }
      if (payload.status === "success" && payload.action?.type === "open_url") {
        const safeUrl = safeChatGPTPrefillUrl(payload.action.url);
        if (!safeUrl) throw new Error("ChatGPT 预填充地址未通过浏览器安全校验，已停止打开。");
        fallbackUrl = safeUrl;
        if (chatgptWindow && !chatgptWindow.closed) {
          chatgptWindow.location.replace(safeUrl);
          fallbackUrl = "";
        }
      } else if (chatgptWindow && !chatgptWindow.closed) {
        chatgptWindow.close();
      }

      setCommandExecution({
        commandId: command.id,
        status: payload.status,
        title: payload.title_zh,
        message: payload.message_zh,
        outputs: payload.outputs,
        inputHint: payload.input_hint_zh ?? "",
        fallbackUrl,
        navigationView,
      });
    } catch (error) {
      if (chatgptWindow && !chatgptWindow.closed) chatgptWindow.close();
      setCommandExecution({
        commandId: command.id,
        status: "error",
        title: "操作未完成",
        message: error instanceof Error ? error.message : "本地操作失败，请查看 Memory Atlas 本机日志。",
        outputs: [],
        inputHint: "",
        fallbackUrl: "",
        navigationView: null,
      });
    }
  }, [commandExecution.status, reloadAtlas, runtimeState]);

  useEffect(() => {
    window.__memoryAtlasS12Phase1 = () => ({
      commandPaletteVersion: COMMAND_PALETTE_VERSION,
      commandIds: [...commandPaletteModel.commandIds],
      commandCount: commandPaletteModel.commands.length,
      acceptedCoreCommandIds: [...commandPaletteModel.acceptedCoreCommandIds],
      personalizationCommandId: S12_P1_PERSONALIZATION_COMMAND_ID,
      personalizationTargets: [...S12_P1_PERSONALIZATION_TARGETS],
      userTriggerRequired: true,
      automaticSendEnabled: false,
      chatgptDeepExploreEnabled: false,
      unacceptedCommandCount: 0,
      selectedCommandId,
      pendingLaterWork: ["S12 P2", "S12 P3"],
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalApplyExecution: false, sendsCookiesTokensSecrets: false },
    });
    window.__memoryAtlasS12Phase3 = () => ({
      taskId: "MA-V12-S12P3",
      acceptanceId: "ACC-MA-V12-S12P3",
      contractVersion: S12_P3_CHATGPT_DEEP_EXPLORE_VERSION,
      commandId: S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID,
      commandVisible: commandPaletteModel.commandIds.includes(S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID),
      defaultMode: "prefill_only",
      allowedModes: ["prefill_only", "auto_submit"],
      dryRunCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --dry-run",
      openCommand: "python3 scripts/atlasctl.py chatgpt-deep-explore --mode prefill_only --open",
      userTriggerRequired: true,
      noSilentSend: true,
      autoSubmitRequiresExplicitConfig: true,
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalApplyExecution: false, sendsCookiesTokensSecrets: false },
    });
    return () => {
      delete window.__memoryAtlasS12Phase1;
      delete window.__memoryAtlasS12Phase3;
    };
  }, [commandPaletteModel, selectedCommandId]);

  useEffect(() => {
    window.__memoryAtlasR3CommandWorkflows = () => ({
      workflowVersion: COMMAND_WORKFLOW_VERSION,
      commandApiVersion: COMMAND_API_VERSION,
      commandIds: [...commandPaletteModel.commandIds],
      runtimeAvailable: runtimeState.serverMode === "本地自释放" && runtimeState.commandApiAvailable,
      selectedCommandId,
      executionStatus: commandExecution.status,
      hostedStaticReadOnly: runtimeState.serverMode === "静态托管",
      localAppHandoff: LOCAL_APP_HANDOFF_URL,
      noSilentSend: true,
      canonicalRepoMutation: false,
    });
    return () => { delete window.__memoryAtlasR3CommandWorkflows; };
  }, [commandExecution.status, commandPaletteModel.commandIds, runtimeState, selectedCommandId]);

  useEffect(() => {
    window.__memoryAtlasR4ProposalWorkflow = () => ({
      workflowVersion: PROPOSAL_WORKFLOW_VERSION,
      proposalApiVersion: PROPOSAL_API_VERSION,
      runtimeAvailable: runtimeState.serverMode === "本地自释放" && runtimeState.proposalApiAvailable,
      workspaceOpen: proposalReview !== null,
      proposalCount: proposalReview?.summary.proposal_count ?? 0,
      applyReadyCount: proposalReview?.summary.apply_ready_count ?? 0,
      humanApprovalRequired: true,
      rawMutation: false,
      canonicalRepoMutation: false,
      remotePush: false,
    });
    return () => { delete window.__memoryAtlasR4ProposalWorkflow; };
  }, [proposalReview, runtimeState.proposalApiAvailable, runtimeState.serverMode]);

  useEffect(() => {
    window.__memoryAtlasR5OwnerDaily = () => ({
      uiVersion: OWNER_DAILY_UI_VERSION,
      ownerDailyApiVersion: OWNER_DAILY_API_VERSION,
      runtimeAvailable: runtimeState.serverMode === "本地自释放" && runtimeState.ownerDailyApiAvailable,
      workspaceOpen: ownerDailyWorkspaceOpen,
      resultStatus: ownerDailyResult?.status ?? "idle",
      completedCount: ownerDailyResult?.completed_count ?? 0,
      failedCount: ownerDailyResult?.failed_count ?? 0,
      hostedStaticReadOnly: runtimeState.serverMode === "静态托管",
      canonicalRepoMutation: false,
      remotePush: false,
    });
    return () => { delete window.__memoryAtlasR5OwnerDaily; };
  }, [ownerDailyResult, ownerDailyWorkspaceOpen, runtimeState.ownerDailyApiAvailable, runtimeState.serverMode]);

  const value = useMemo<AtlasRuntimeContextValue>(() => ({
    closeOwnerDaily: () => setOwnerDailyWorkspaceOpen(false),
    closeProposalReview: () => setProposalReview(null),
    commandExecution,
    commandPaletteModel,
    executeCommand,
    openOwnerDaily: () => setOwnerDailyWorkspaceOpen(true),
    ownerDailyResult,
    ownerDailyWorkspaceOpen,
    proposalReview,
    runtimeState,
    selectCommand,
    selectedCommandId,
    setOwnerDailyResult,
  }), [commandExecution, commandPaletteModel, executeCommand, ownerDailyResult, ownerDailyWorkspaceOpen, proposalReview, runtimeState, selectCommand, selectedCommandId]);

  return <AtlasRuntimeContext.Provider value={value}>{children}</AtlasRuntimeContext.Provider>;
}

export function useAtlasRuntime(): AtlasRuntimeContextValue {
  const context = useContext(AtlasRuntimeContext);
  if (!context) throw new Error("useAtlasRuntime must be used within AtlasRuntimeProvider");
  return context;
}
