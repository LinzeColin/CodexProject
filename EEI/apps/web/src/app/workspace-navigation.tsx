"use client";

import {
  Activity,
  Bell,
  Boxes,
  Building2,
  CircleDollarSign,
  Clock3,
  Database,
  FileSearch,
  GitBranch,
  Landmark,
  ListChecks,
  Network,
  PackageSearch,
  Route,
  Scale,
  Settings2,
  ShieldCheck
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  WORKSPACE_MODULES,
  type WorkspaceModuleDefinition,
  type WorkspaceModuleId
} from "./workspace-context";

type WorkspaceNavigationRailProps = {
  activeLens: string;
  activeModuleId: WorkspaceModuleId;
  onLensTarget: (lens: string, moduleId: WorkspaceModuleId) => void;
  onSectionTarget: (sectionTestId: string, moduleId: WorkspaceModuleId) => void;
};

const moduleIconById: Record<WorkspaceModuleId, LucideIcon> = {
  business_map: Network,
  group_structure: Building2,
  business_segments: Boxes,
  supply_chain: PackageSearch,
  capital_network: CircleDollarSign,
  ma_transactions: GitBranch,
  control_relationships: ShieldCheck,
  policy_environment: Landmark,
  strategic_signals: Activity,
  time_evolution: Clock3,
  evidence_center: FileSearch,
  model_center: Settings2,
  data_center: Database,
  watchlist: Bell,
  exploration_history: Route,
  system_status: Scale
};

export function WorkspaceNavigationRail({
  activeLens,
  activeModuleId,
  onLensTarget,
  onSectionTarget
}: WorkspaceNavigationRailProps) {
  return (
    <aside className="navRail" aria-label="主导航">
      <div className="brandMark" aria-label="商域图谱">
        <span className="brandGlyph">E</span>
        <span>
          <strong>商域图谱</strong>
          <small>EEI</small>
        </span>
      </div>
      <nav aria-label="主导航" data-testid="primary-workspace-navigation">
        {WORKSPACE_MODULES.map((module) => (
          <WorkspaceNavigationItem
            activeLens={activeLens}
            activeModuleId={activeModuleId}
            key={module.id}
            module={module}
            onLensTarget={onLensTarget}
            onSectionTarget={onSectionTarget}
          />
        ))}
      </nav>
      <div className="systemNav" aria-label="系统模块">
        <span className="navGroupLabel">系统模块</span>
        <a
          className="navItem"
          data-testid="objects-scope-nav-link"
          href="/objects-scope"
          title="对象与范围"
        >
          <Database size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>对象与范围</span>
        </a>
        <a
          className="navItem"
          data-testid="development-status-nav-link"
          href="/development-status"
          title="开发状态"
        >
          <ListChecks size={18} strokeWidth={1.8} aria-hidden="true" />
          <span>开发状态</span>
        </a>
      </div>
    </aside>
  );
}

function WorkspaceNavigationItem({
  activeLens,
  activeModuleId,
  module,
  onLensTarget,
  onSectionTarget
}: {
  activeLens: string;
  activeModuleId: WorkspaceModuleId;
  module: WorkspaceModuleDefinition;
  onLensTarget: (lens: string, moduleId: WorkspaceModuleId) => void;
  onSectionTarget: (sectionTestId: string, moduleId: WorkspaceModuleId) => void;
}) {
  const Icon = moduleIconById[module.id];
  const commonData = {
    "data-acceptance-ids": module.acceptanceIds.join(","),
    "data-api-endpoints": (module.apiEndpoints ?? []).join(","),
    "data-control-kind": module.controlKind,
    "data-route-state": module.routeState,
    "data-testid": `main-nav-${module.id}`
  };
  const active =
    module.id === activeModuleId ||
    (module.controlKind === "lens" && module.controlTargetLens === activeLens);
  const className = `navItem ${active ? "active" : ""} ${module.controlKind}`.trim();

  if (module.controlKind === "route" && module.href) {
    return (
      <a
        {...commonData}
        aria-current={module.id === activeModuleId ? "page" : undefined}
        className={className}
        href={module.href}
        title={module.label}
      >
        <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
        <span>{module.label}</span>
      </a>
    );
  }

  if (module.controlKind === "lens" && module.controlTargetLens) {
    return (
      <button
        {...commonData}
        aria-pressed={module.controlTargetLens === activeLens}
        className={className}
        data-control-target={module.controlTargetLens}
        onClick={() => onLensTarget(module.controlTargetLens!, module.id)}
        title={module.subtitle}
        type="button"
      >
        <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
        <span>{module.label}</span>
      </button>
    );
  }

  if (module.controlKind === "section" && module.sectionTestId) {
    return (
      <button
        {...commonData}
        className={className}
        data-section-target={module.sectionTestId}
        onClick={() => onSectionTarget(module.sectionTestId!, module.id)}
        title={module.subtitle}
        type="button"
      >
        <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
        <span>{module.label}</span>
      </button>
    );
  }

  return (
    <button
      {...commonData}
      aria-disabled="true"
      className={className}
      data-disabled-reason={module.disabledReason}
      disabled
      title={module.disabledReason ?? module.subtitle}
      type="button"
    >
      <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
      <span>{module.label}</span>
    </button>
  );
}
