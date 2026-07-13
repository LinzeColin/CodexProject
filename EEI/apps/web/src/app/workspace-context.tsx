"use client";

import { createContext, useContext, type ReactNode } from "react";

import type { AnalysisContext } from "./analysis-contract";

export const WORKSPACE_CONTEXT_VERSION = "workspace-context-v1";
export const WORKSPACE_STATE_STORAGE_KEY = "eei.workspaceState.v1";
export const SAVED_VIEW_STORAGE_KEY = "eei.savedView.current.v1";

export type WorkspaceModuleId =
  | "business_map"
  | "group_structure"
  | "business_segments"
  | "supply_chain"
  | "capital_network"
  | "ma_transactions"
  | "control_relationships"
  | "policy_environment"
  | "strategic_signals"
  | "time_evolution"
  | "evidence_center"
  | "model_center"
  | "data_center"
  | "watchlist"
  | "exploration_history"
  | "system_status";

export type WorkspaceControlKind = "route" | "lens" | "section" | "planned";

export type WorkspaceModuleDefinition = {
  id: WorkspaceModuleId;
  label: string;
  subtitle: string;
  controlKind: WorkspaceControlKind;
  routeState: "active" | "available" | "partial" | "planned";
  acceptanceIds: string[];
  href?: string;
  apiEndpoints?: string[];
  controlTargetLens?: string;
  sectionTestId?: string;
  disabledReason?: string;
};

export type WorkspaceRuntimeState = {
  focusKey: string;
  selectedKey: string;
  path: string[];
  activeLens: string;
  semanticZoom: string;
  asOf: string;
  analysisContext: AnalysisContext;
};

export type WorkspaceContextValue = {
  contextVersion: typeof WORKSPACE_CONTEXT_VERSION;
  modules: readonly WorkspaceModuleDefinition[];
  runtimeState: WorkspaceRuntimeState;
  queryKeys: readonly string[];
  persistenceTargets: readonly string[];
  serverEndpoints: readonly string[];
  implementedRouteIds: WorkspaceModuleId[];
  realControlIds: WorkspaceModuleId[];
  disabledUnfinishedIds: WorkspaceModuleId[];
};

export const WORKSPACE_QUERY_KEYS = ["subject", "selected", "lens", "zoom", "asOf", "path"] as const;
export const WORKSPACE_PERSISTENCE_TARGETS = [
  "url",
  "sessionStorage",
  "localStorage"
] as const;

export const WORKSPACE_MODULES: readonly WorkspaceModuleDefinition[] = [
  {
    id: "business_map",
    label: "商业版图",
    subtitle: "当前主体的完整企业生态关系图",
    controlKind: "route",
    routeState: "active",
    href: "/",
    apiEndpoints: ["/v1/explore", "/v1/explore/reroot", "/v1/explore/expand"],
    acceptanceIds: ["A203", "A211"]
  },
  {
    id: "group_structure",
    label: "集团结构",
    subtitle: "母公司、子公司、控股公司、合资企业和业务集团",
    controlKind: "lens",
    controlTargetLens: "business_segments",
    routeState: "partial",
    apiEndpoints: ["/v1/entities/{entityId}/empire"],
    acceptanceIds: ["A202", "A211"]
  },
  {
    id: "business_segments",
    label: "业务板块",
    subtitle: "产品线、技术平台、收入板块和市场布局",
    controlKind: "lens",
    controlTargetLens: "business_segments",
    routeState: "partial",
    apiEndpoints: ["/v1/entities/{entityId}/empire"],
    acceptanceIds: ["A203", "A211"]
  },
  {
    id: "supply_chain",
    label: "供应链",
    subtitle: "原材料、设备、制造、封装、系统、渠道和客户",
    controlKind: "lens",
    controlTargetLens: "supply_chain",
    routeState: "partial",
    apiEndpoints: ["/v1/explore", "/v1/explore/expand"],
    acceptanceIds: ["A203", "A211"]
  },
  {
    id: "capital_network",
    label: "资本网络",
    subtitle: "股权、投资、融资、基金、回购和资本支出",
    controlKind: "route",
    href: "/capital",
    routeState: "available",
    apiEndpoints: ["/v1/events", "/v1/events/amount-summary", "/v1/evidence/event/{eventId}"],
    acceptanceIds: ["A108", "A109", "A110", "A203", "A211"]
  },
  {
    id: "ma_transactions",
    label: "并购交易",
    subtitle: "收购、出售、拆分、合并和战略投资",
    controlKind: "planned",
    routeState: "planned",
    disabledReason: "Requires reviewed M&A transaction facts from T1301/T1302 before public UI activation.",
    acceptanceIds: ["A202", "A203", "A211"]
  },
  {
    id: "control_relationships",
    label: "控制关系",
    subtitle: "投票权、经济权益、董事席位和实际控制路径",
    controlKind: "planned",
    routeState: "planned",
    disabledReason: "Requires reviewed control-path facts and confidence explanations before activation.",
    acceptanceIds: ["A202", "A203", "A211"]
  },
  {
    id: "policy_environment",
    label: "政策环境",
    subtitle: "补贴、合同、监管、出口管制和游说关系",
    controlKind: "lens",
    controlTargetLens: "policy_risk",
    routeState: "partial",
    apiEndpoints: ["/v1/explore"],
    acceptanceIds: ["A203", "A211"]
  },
  {
    id: "strategic_signals",
    label: "战略信号",
    subtitle: "招聘、资本支出、专利、合作和管理层表态",
    controlKind: "planned",
    routeState: "planned",
    disabledReason: "Requires signal ingestion handlers and source review before activation.",
    acceptanceIds: ["A202", "A206", "A211"]
  },
  {
    id: "time_evolution",
    label: "时间演变",
    subtitle: "历史关系、事件变化和商业版图演进",
    controlKind: "section",
    sectionTestId: "timeline-controls",
    routeState: "available",
    apiEndpoints: ["/v1/explore"],
    acceptanceIds: ["A205", "A211"]
  },
  {
    id: "evidence_center",
    label: "证据中心",
    subtitle: "来源、原始文件、证据片段和可信度",
    controlKind: "section",
    sectionTestId: "evidence-center",
    routeState: "partial",
    apiEndpoints: ["/v1/evidence", "/v1/audit-logs"],
    acceptanceIds: ["A202", "A211"]
  },
  {
    id: "model_center",
    label: "模型中心",
    subtitle: "公式、权重、阈值、时间衰减和模型版本",
    controlKind: "section",
    sectionTestId: "model-preview-panel",
    routeState: "partial",
    apiEndpoints: [
      "/v1/scoring/active-context",
      "/v1/scoring/profiles",
      "/v1/scoring/recompute"
    ],
    acceptanceIds: ["A204", "A205", "A211"]
  },
  {
    id: "data_center",
    label: "数据中心",
    subtitle: "数据来源、更新时间、覆盖率和异常状态",
    controlKind: "route",
    routeState: "partial",
    href: "/objects-scope",
    apiEndpoints: ["/v1/catalogs/relationship", "/v1/catalogs/domain-object"],
    acceptanceIds: ["A172", "A211"]
  },
  {
    id: "watchlist",
    label: "我的关注",
    subtitle: "Watchlist、保存视图和告警",
    controlKind: "section",
    sectionTestId: "home-watchlist",
    routeState: "partial",
    apiEndpoints: ["/v1/watchlists", "/v1/saved-views"],
    acceptanceIds: ["A207", "A211"]
  },
  {
    id: "exploration_history",
    label: "探索记录",
    subtitle: "用户递归探索路径及历史主体",
    controlKind: "section",
    sectionTestId: "home-recent-explorations",
    routeState: "available",
    apiEndpoints: ["/v1/explore/reroot"],
    acceptanceIds: ["A203", "A211"]
  },
  {
    id: "system_status",
    label: "系统状态",
    subtitle: "数据任务、模型刷新和数据库状态",
    controlKind: "route",
    routeState: "available",
    href: "/development-status",
    apiEndpoints: ["/health", "/v1/audit-logs"],
    acceptanceIds: ["A174", "A211"]
  }
];

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function createWorkspaceContextValue(
  runtimeState: WorkspaceRuntimeState
): WorkspaceContextValue {
  return {
    contextVersion: WORKSPACE_CONTEXT_VERSION,
    modules: WORKSPACE_MODULES,
    runtimeState,
    queryKeys: WORKSPACE_QUERY_KEYS,
    persistenceTargets: WORKSPACE_PERSISTENCE_TARGETS,
    serverEndpoints: sortedUnique(
      WORKSPACE_MODULES.flatMap((module) => module.apiEndpoints ?? []).concat([
        "/v1/saved-views",
        "/v1/scoring/active-context",
        "/v1/scoring/recompute"
      ])
    ),
    implementedRouteIds: WORKSPACE_MODULES.filter((module) => module.controlKind === "route").map(
      (module) => module.id
    ),
    realControlIds: WORKSPACE_MODULES.filter((module) => module.controlKind !== "planned").map(
      (module) => module.id
    ),
    disabledUnfinishedIds: WORKSPACE_MODULES.filter((module) => module.controlKind === "planned").map(
      (module) => module.id
    )
  };
}

export function WorkspaceContextProvider({
  children,
  value
}: {
  children: ReactNode;
  value: WorkspaceContextValue;
}) {
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspaceContext() {
  const value = useContext(WorkspaceContext);
  if (!value) {
    throw new Error("WorkspaceContextProvider is required");
  }
  return value;
}

export function getWorkspaceModule(moduleId: WorkspaceModuleId) {
  return WORKSPACE_MODULES.find((module) => module.id === moduleId);
}

export function WorkspaceContextContractMarker() {
  const context = useWorkspaceContext();
  return (
    <div
      hidden
      data-context-version={context.contextVersion}
      data-disabled-unfinished={context.disabledUnfinishedIds.join(",")}
      data-implemented-routes={context.implementedRouteIds.join(",")}
      data-module-count={context.modules.length}
      data-query-keys={context.queryKeys.join(",")}
      data-real-controls={context.realControlIds.join(",")}
      data-saved-view-storage-key={SAVED_VIEW_STORAGE_KEY}
      data-server-endpoints={context.serverEndpoints.join(",")}
      data-state-persistence={context.persistenceTargets.join(",")}
      data-testid="workspace-context-contract"
      data-workspace-state-storage-key={WORKSPACE_STATE_STORAGE_KEY}
    />
  );
}

function sortedUnique(values: string[]) {
  return [...new Set(values)].sort();
}
