import { CircleHelp, GitBranch, Search } from "lucide-react";
import type { PropsWithChildren } from "react";
import { useEffect } from "react";
import { ErrorState } from "../components/ErrorState";
import { MemoryAtlasHelpPanel } from "../components/help/MemoryAtlasHelpPanel";
import { ProposalWorkspace, WritebackProposalPanel } from "../features/actions";
import { ContributionPeriodInspector, InteractionLens, NodeInspector } from "../features/settings";
import { CommandPalettePanel, OwnerDailyEntry, OwnerDailyWorkspace } from "../features/sync";
import { useAtlasData } from "../providers/AtlasDataProvider";
import { useAtlasRuntime } from "../providers/AtlasRuntimeProvider";
import { useAtlasWorkspace } from "../providers/AtlasWorkspaceProvider";
import {
  COMMAND_PALETTE_VERSION,
  COMMAND_WORKFLOW_VERSION,
  CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION,
  CROSS_BOARD_SHARED_STATE_SURFACES,
  DEFAULT_MEMORY_ATLAS_VIEW,
  GLOBAL_CHINESE_UX_VERSION,
  INSPECTOR_EXPLANATION_LAYER_VERSION,
  MACHINE_DETAIL_FOLDING_VERSION,
  OWNER_DAILY_UI_VERSION,
  PRODUCT_IDENTITY_VERSION,
  PROPOSAL_WORKFLOW_VERSION,
  S12_P3_CHATGPT_DEEP_EXPLORE_VERSION,
  navigationGroups,
  uiCopy,
  views,
  visualFocusViews,
} from "../shared/atlas/constants";
import { buildInspectorExplanation } from "../shared/atlas/inspectorWriteback";
import { edgeCountFor } from "../shared/atlas/utils";
import { humanCategoryLabel } from "../shared/atlas/semanticHuman";
import { MachineFieldDetails } from "../shared/ui/display";
import { Metric, SelectFilter } from "../shared/ui/primitives";

export function MemoryAtlasShell({ children }: PropsWithChildren) {
  const { atlas, loadError, loadState } = useAtlasData();
  const {
    activeView,
    categories,
    clearFilter,
    clearTimelineRange,
    closeHelp,
    filters,
    focusSelectedTheme,
    helpOpen,
    nodeMap,
    openHelp,
    openHelpView,
    resetFilters,
    scopedAtlas,
    selectAdjacentNode,
    selectNode,
    selectedContributionPeriod,
    selectedNode,
    sharedState,
    slice,
    sourceOptions,
    switchView,
    themeOptions,
    tiers,
    timelineTimeRange,
    updateFilters,
  } = useAtlasWorkspace();
  const {
    closeOwnerDaily,
    closeProposalReview,
    commandExecution,
    commandPaletteModel,
    executeCommand,
    openOwnerDaily,
    ownerDailyResult,
    ownerDailyWorkspaceOpen,
    proposalReview,
    runtimeState,
    selectCommand,
    selectedCommandId,
    setOwnerDailyResult,
  } = useAtlasRuntime();

  const generatedAt = atlas.overview.generated_at
    ? new Date(atlas.overview.generated_at).toLocaleString("zh-CN")
    : uiCopy.states.notLoaded;
  const loadedAt = runtimeState.snapshotLoadedAt ? runtimeState.snapshotLoadedAt.toLocaleString("zh-CN") : uiCopy.states.loading;
  const runtimeStatus = `${runtimeState.lifecycle} / ${runtimeState.serverMode}`;
  const selectedTitle = views.find((view) => view.key === activeView)?.label ?? uiCopy.app.fallbackTitle;
  const wideView = visualFocusViews.includes(activeView);
  const workspaceClassName = wideView ? `workspace visual-focus-workspace ${activeView}-workspace` : "workspace";
  const showSideInspector = activeView === "contribution" || !wideView;
  const stage9InspectorExplanation = selectedNode
    ? buildInspectorExplanation(selectedNode, edgeCountFor(selectedNode.id, scopedAtlas.edges), sharedState)
    : null;

  useEffect(() => {
    window.__memoryAtlasStage9Phase1 = () => ({
      runtimeVersion: CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION,
      inspectorLayerVersion: INSPECTOR_EXPLANATION_LAYER_VERSION,
      sharedStateSchemaVersion: sharedState.schema_version,
      activeView,
      surfaces: [...CROSS_BOARD_SHARED_STATE_SURFACES],
      surfaceCount: CROSS_BOARD_SHARED_STATE_SURFACES.length,
      synchronizedFilters: sharedState.filters,
      shared_state_filters: true,
      synchronized_filters: true,
      focus: sharedState.focus,
      sync: sharedState.sync,
      visibleNodeCount: slice.memoryNodes.length,
      selectedNodeId: selectedNode?.id ?? null,
      inspector_explanation_layer: {
        mounted: Boolean(stage9InspectorExplanation),
        formulaCount: stage9InspectorExplanation?.formulas.length ?? 0,
        evidenceCount: stage9InspectorExplanation?.evidence.length ?? 0,
        safetyNoteCount: stage9InspectorExplanation?.safetyNotes.length ?? 0,
        source: "redacted_derived_snapshot",
      },
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasStage9Phase1; };
  }, [activeView, selectedNode?.id, sharedState, slice.memoryNodes.length, stage9InspectorExplanation]);

  useEffect(() => {
    window.__memoryAtlasS10Phase2 = () => ({
      globalChineseUxVersion: GLOBAL_CHINESE_UX_VERSION,
      coreUiDefaultChinese: true,
      machineTermsRequireChineseExplanation: true,
      chineseUxAudit: "atlasctl audit --check chinese-ux",
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS10Phase2; };
  }, []);

  useEffect(() => {
    window.__memoryAtlasS10Phase3 = () => ({
      machineDetailFoldingVersion: MACHINE_DETAIL_FOLDING_VERSION,
      defaultHumanReadableFirst: true,
      machineFieldsDefaultCollapsed: true,
      advancedDetailsEntryVisible: true,
      foldedSurfaces: ["home_arrival", "search_session", "search_result", "review_session", "summary_closure", "inspector"],
      safety: { rawPrivateDataIncluded: false, directActiveMemoryWriteback: false, proposalWrite: false },
    });
    return () => { delete window.__memoryAtlasS10Phase3; };
  }, []);

  return (
    <div
      className="app-shell"
      data-default-route-view={DEFAULT_MEMORY_ATLAS_VIEW}
      data-memory-overview-default-route="true"
      data-r2-release-identity={PRODUCT_IDENTITY_VERSION}
      data-s10-p2-global-chinese-ux={GLOBAL_CHINESE_UX_VERSION}
      data-s10-p3-machine-detail-folding={MACHINE_DETAIL_FOLDING_VERSION}
      data-stage9-phase1-shared-state={CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION}
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-stage9-synchronized-filters="shared_state_filters synchronized_filters inspector_explanation_layer"
      data-stage9-safety-boundary="No direct active-memory writeback; No proposal queue write"
      data-stage9-surface-count={CROSS_BOARD_SHARED_STATE_SURFACES.length}
      data-s12-p1-command-palette={COMMAND_PALETTE_VERSION}
      data-s12-p3-chatgpt-deep-explore={S12_P3_CHATGPT_DEEP_EXPLORE_VERSION}
      data-s12-p3-chatgpt-deep-explore-boundary="prefill_only default; auto_submit gated; No silent send; No cookie/token/secret export"
      data-r3-command-workflows={COMMAND_WORKFLOW_VERSION}
      data-r3-command-api-available={runtimeState.commandApiAvailable ? "true" : "false"}
      data-r4-proposal-workflow={PROPOSAL_WORKFLOW_VERSION}
      data-r4-proposal-api-available={runtimeState.proposalApiAvailable ? "true" : "false"}
      data-r5-owner-daily={OWNER_DAILY_UI_VERSION}
      data-r5-owner-daily-api-available={runtimeState.ownerDailyApiAvailable ? "true" : "false"}
    >
      <aside className="sidebar" aria-label={uiCopy.app.navigationAria}>
        <div className="brand">
          <GitBranch size={22} />
          <div>
            <strong>{uiCopy.app.brandTitle}</strong>
            <span>{uiCopy.app.productName}</span>
          </div>
        </div>
        <nav className="nav-list">
          {navigationGroups.map((group) => (
            <div className="nav-group" data-nav-question-group={group.id} key={group.id}>
              <div className="nav-group-heading">
                <span className="nav-group-label">{group.label}</span>
                <small className="nav-group-question">{group.question}</small>
              </div>
              <div className="nav-group-items">
                {group.viewKeys.map((viewKey) => {
                  const view = views.find((candidate) => candidate.key === viewKey);
                  if (!view) return null;
                  const Icon = view.icon;
                  return (
                    <button
                      aria-label={view.label}
                      className={activeView === view.key ? "nav-item active" : "nav-item"}
                      data-nav-view={view.key}
                      key={view.key}
                      onClick={() => switchView(view.key)}
                      onFocus={(event) => event.currentTarget.scrollIntoView({ block: "nearest", inline: "nearest" })}
                      title={view.label}
                      type="button"
                    >
                      <Icon size={18} />
                      <span>{view.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <MachineFieldDetails title="数据状态" className="sidebar-data-status">
            <dl>
              <div><dt>{uiCopy.app.snapshotGeneratedAt}</dt><dd>{generatedAt}</dd></div>
              <div><dt>{uiCopy.app.snapshotLoadedAt}</dt><dd>{loadedAt}</dd></div>
              <div><dt>{uiCopy.app.runtimeStatus}</dt><dd>{runtimeStatus}</dd></div>
            </dl>
          </MachineFieldDetails>
          <a className="homehub-return" data-homehub-return href="https://home.linzezhang.com" rel="noreferrer">
            返回 LinzeHomeHub
          </a>
        </div>
      </aside>

      <main className={workspaceClassName}>
        <header className="topbar">
          <div>
            <p className="eyebrow">{uiCopy.app.topbarEyebrow}</p>
            <h1>{selectedTitle}</h1>
          </div>
          <div className="topbar-actions">
            <div className="stat-strip" aria-label="星图总览">
              <Metric label={uiCopy.metrics.memory} value={scopedAtlas.overview.active_memory_count} />
              <Metric label={uiCopy.metrics.nodes} value={scopedAtlas.overview.node_count} />
              <Metric label={uiCopy.metrics.edges} value={scopedAtlas.overview.edge_count} />
              <Metric label={uiCopy.metrics.activity} value={scopedAtlas.overview.conversation_count} />
            </div>
            <button className="help-launch-button" onClick={openHelp} title={uiCopy.help.buttonLabel} type="button">
              <CircleHelp size={17} />
              <span>{uiCopy.help.buttonLabel}</span>
            </button>
          </div>
        </header>

        {loadState === "error" ? (
          <ErrorState
            compact
            className="load-banner"
            dataState="load-failed-banner"
            description={uiCopy.states.loadFailedDescription}
            details={loadError}
            title={uiCopy.states.loadFailedTitle}
          />
        ) : null}

        <section className="controls" aria-label={uiCopy.filters.ariaLabel}>
          <label className="search-box">
            <Search size={18} />
            <input
              value={filters.query}
              onChange={(event) => updateFilters((current) => ({ ...current, query: event.target.value }))}
              placeholder={uiCopy.filters.searchPlaceholder}
            />
          </label>
          <label className="select-filter source-filter">
            <span>{uiCopy.filters.sourceLabel}</span>
            <select
              value={filters.source}
              onChange={(event) => updateFilters((current) => ({ ...current, source: event.target.value, tier: "all", category: "all", theme: "all" }))}
            >
              {sourceOptions.map((source) => <option key={source.id} value={source.id}>{source.label}</option>)}
            </select>
          </label>
          <SelectFilter label={uiCopy.filters.tierLabel} value={filters.tier} options={tiers} onChange={(value) => updateFilters((current) => ({ ...current, tier: value }))} />
          <SelectFilter
            label={uiCopy.filters.categoryLabel}
            value={filters.category}
            options={categories}
            formatOption={humanCategoryLabel}
            onChange={(value) => updateFilters((current) => ({ ...current, category: value }))}
          />
          <label className="select-filter">
            <span>{uiCopy.filters.topicLabel}</span>
            <select value={filters.theme} onChange={(event) => updateFilters((current) => ({ ...current, theme: event.target.value }))}>
              <option value="all">{uiCopy.filters.allOption}</option>
              {themeOptions.map((theme) => <option key={theme.id} value={theme.id}>{theme.label}</option>)}
            </select>
          </label>
        </section>

        <InteractionLens
          activeView={activeView}
          filters={filters}
          sharedState={sharedState}
          selectedContributionPeriod={activeView === "contribution" ? selectedContributionPeriod : null}
          selectedNode={selectedNode}
          slice={slice}
          sourceOptions={sourceOptions}
          timelineTimeRange={timelineTimeRange}
          onClearFilter={clearFilter}
          onClearTimelineRange={clearTimelineRange}
          onFocusTheme={focusSelectedTheme}
          onResetFilters={resetFilters}
          onSelectAdjacent={selectAdjacentNode}
        />

        <CommandPalettePanel
          execution={commandExecution}
          model={commandPaletteModel}
          onExecuteCommand={executeCommand}
          onNavigateView={switchView}
          ownerDailyEntry={(
            <OwnerDailyEntry
              available={runtimeState.serverMode === "本地自释放" && runtimeState.ownerDailyApiAvailable}
              onOpen={openOwnerDaily}
              serverMode={runtimeState.serverMode}
            />
          )}
          selectedCommandId={selectedCommandId}
          onSelectCommand={selectCommand}
        />

        <div className={wideView ? "content-grid wide-view" : "content-grid"} data-view={activeView}>
          <section className="view-surface">{children}</section>
          {showSideInspector ? (
            activeView === "contribution" && selectedContributionPeriod ? (
              <ContributionPeriodInspector detail={selectedContributionPeriod} onSelectNode={selectNode} />
            ) : (
              <NodeInspector
                atlas={scopedAtlas}
                node={selectedNode}
                edgeCount={edgeCountFor(selectedNode?.id, scopedAtlas.edges)}
                sharedState={sharedState}
                writebackPanel={selectedNode ? <WritebackProposalPanel atlas={scopedAtlas} node={selectedNode} /> : null}
              />
            )
          ) : null}
        </div>
        <MemoryAtlasHelpPanel copy={uiCopy.help} onClose={closeHelp} onSelectView={openHelpView} open={helpOpen} />
      </main>
      {proposalReview ? <ProposalWorkspace onClose={closeProposalReview} review={proposalReview} /> : null}
      {ownerDailyWorkspaceOpen ? (
        <OwnerDailyWorkspace onClose={closeOwnerDaily} onResultChange={setOwnerDailyResult} result={ownerDailyResult} />
      ) : null}
    </div>
  );
}
