import { LayoutDashboard } from "lucide-react";
import type { CSSProperties } from "react";
import { useMemo, useState } from "react";
import type { AtlasEdge, AtlasNode, MemoryAtlas, ViewKey } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { ActionDetailDrawer } from "../../components/ActionDetailDrawer";
import { AssetDetailPanel } from "../../components/AssetDetailPanel";
import { ThemeDetailPanel } from "../../components/ThemeDetailPanel";
import { VisualWorkflowWorkbench } from "../../components/VisualWorkflowWorkbench";
import { BehaviorIntelligencePanel } from "./BehaviorIntelligencePanel";
import { buildHomeActionStatusChips, buildLevelAssetGroupChips, buildThemeCategoryChips, humanActionStatusLabel, humanEffortLabel, humanPriorityLabel, humanUrgencyLabel } from "./homePresentation";
import { HOME_ACTION_SECTION_VERSION, HOME_ARRIVAL_BRIEFING_VERSION, HOME_LEVEL_ASSET_SECTION_VERSION, HOME_THEME_CATEGORY_SECTION_VERSION, MEMORY_OVERVIEW_OPERATION_VERSION, MEMORY_OVERVIEW_SECTION_ORDER, MEMORY_OVERVIEW_STRUCTURE_VERSION, uiCopy } from "../../shared/atlas/constants";
import { DeltaStats, HomeAction, HomeActionDetail, HomeTierAsset, HomeTopicDetail, TierAssetDetail, TimelineTimeRangeSelection, TopicClassificationDetail } from "../../shared/atlas/contracts";
import { buildHomeArrivalBriefing, buildHomeOverviewModel } from "../../shared/atlas/homeOverviewModels";
import { humanNodeDisplayTitle } from "../../shared/atlas/semanticHuman";
import { timelineRangeSummary } from "../../shared/atlas/timelineInteraction";
import { formatScore, formatSigned } from "../../shared/atlas/utils";
import { MachineFieldDetails } from "../../shared/ui/display";
import { Metric, MiniBarList } from "../../shared/ui/primitives";



export function HomeOverviewView({
  atlas,
  nodes,
  graphEdges,
  deltaStats,
  selectedNode,
  sharedState,
  timelineTimeRange,
  onSelectNode,
  onSwitchView,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  deltaStats: DeltaStats;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedActionDetail, setSelectedActionDetail] = useState<HomeActionDetail | null>(null);
  const [selectedTierAsset, setSelectedTierAsset] = useState<TierAssetDetail | null>(null);
  const [selectedTopicDetail, setSelectedTopicDetail] = useState<TopicClassificationDetail | null>(null);
  const model = useMemo(
    () => buildHomeOverviewModel(nodes, graphEdges, deltaStats),
    [deltaStats, graphEdges, nodes],
  );
  const actionStatusChips = buildHomeActionStatusChips(model.actions);
  const levelAssetGroupChips = buildLevelAssetGroupChips(model.tierAssets);
  const themeCategoryChips = buildThemeCategoryChips(model.topicDetails);
  const behaviorIntelligence = atlas.behavior_intelligence;
  const arrivalBriefing = useMemo(
    () => buildHomeArrivalBriefing(atlas, nodes, model, deltaStats),
    [atlas, deltaStats, model, nodes],
  );

  function runAction(action: HomeActionDetail) {
    const runtimeAction = model.actions.find((item) => item.action_id === action.action_id);
    if (!runtimeAction) return;
    if (runtimeAction.node) onSelectNode(runtimeAction.node);
    onSwitchView(runtimeAction.targetView);
  }

  function openActionDetail(action: HomeAction) {
    setSelectedActionDetail(action);
  }

  function openActionTarget(action: HomeActionDetail) {
    runAction(action);
  }

  function closeActionDetail() {
    setSelectedActionDetail(null);
  }

  function openTierAsset(asset: HomeTierAsset) {
    setSelectedTierAsset(asset);
  }

  function openTierAssetTarget(asset: TierAssetDetail) {
    const runtimeAsset = model.tierAssets.find((item) => item.asset_id === asset.asset_id);
    if (!runtimeAsset) return;
    if (runtimeAsset.node) onSelectNode(runtimeAsset.node);
    onSwitchView(runtimeAsset.targetView);
  }

  function closeTierAsset() {
    setSelectedTierAsset(null);
  }

  function openTopicDetail(topic: HomeTopicDetail) {
    setSelectedTopicDetail(topic);
  }

  function openTopicTarget(topic: TopicClassificationDetail) {
    const runtimeTopic = model.topicDetails.find((item) => item.topic_id === topic.topic_id);
    if (!runtimeTopic) return;
    if (runtimeTopic.node) onSelectNode(runtimeTopic.node);
    onSwitchView(runtimeTopic.targetView);
  }

  function closeTopicDetail() {
    setSelectedTopicDetail(null);
  }

  function jumpToPreview(node: AtlasNode | null, targetView: ViewKey) {
    if (node) onSelectNode(node);
    onSwitchView(targetView);
  }

  return (
    <div
      className="home-overview-view visual-workspace"
      data-memory-overview-operations={MEMORY_OVERVIEW_OPERATION_VERSION}
      data-memory-overview-structure={MEMORY_OVERVIEW_STRUCTURE_VERSION}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.home.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.home.clusterId ?? ""}
      data-shared-time-range={sharedState.focus.home.timeRangeId ?? ""}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">{uiCopy.overview.eyebrow}</p>
          <h2>{uiCopy.overview.title}</h2>
        </div>
        <span>{timelineRangeSummary(timelineTimeRange) ?? `${nodes.length.toLocaleString()} 条筛选记忆 · ${uiCopy.overview.defaultEntry}`}</span>
      </div>
      <section
        className="home-arrival-briefing"
        aria-labelledby="home-arrival-briefing-title"
        data-home-arrival-question={uiCopy.overview.arrivalQuestion}
        data-home-section="arrival_briefing"
        data-s10-p1-home-arrival-briefing={HOME_ARRIVAL_BRIEFING_VERSION}
      >
        <div className="arrival-briefing-heading">
          <div>
            <span>{uiCopy.overview.arrivalQuestion}</span>
            <h3 id="home-arrival-briefing-title">{uiCopy.overview.arrivalTitle}</h3>
            <p>{uiCopy.overview.arrivalDescription}</p>
          </div>
          <button type="button" onClick={() => onSwitchView("summary")}>
            <LayoutDashboard size={16} />
            <span>{uiCopy.overview.arrivalSummaryAction}</span>
          </button>
        </div>
        <div className="arrival-briefing-grid">
          {arrivalBriefing.map((card) => {
            const Icon = card.icon;
            return (
              <button
                className={`arrival-briefing-card ${card.tone}`}
                data-home-arrival-category={card.id}
                data-home-arrival-machine-signal={card.machineSignal}
                key={card.id}
                onClick={() => jumpToPreview(card.node, card.targetView)}
                type="button"
              >
                <span className="arrival-briefing-card-label">
                  <Icon size={16} />
                  {card.label}
                </span>
                <strong>{card.value}</strong>
                <p>{card.summary}</p>
                <small>{card.evidence}</small>
                <em className="arrival-briefing-next-step">下一步：{card.nextStep}</em>
              </button>
            );
          })}
        </div>
        <MachineFieldDetails title={uiCopy.overview.arrivalMachineDetails} className="arrival-briefing-machine-details">
          <p className="machine-field-help">默认折叠。这里仅用于核验首页 arrival briefing 合约、快照时间和 no-apply 边界。</p>
          <dl>
            <div><dt>contract / 合约版本</dt><dd>{HOME_ARRIVAL_BRIEFING_VERSION}</dd></div>
            <div><dt>snapshot / 快照时间</dt><dd>{atlas.overview.generated_at || "not_loaded"}</dd></div>
            <div><dt>rawMutation / raw 修改</dt><dd>false</dd></div>
            <div><dt>proposalApply / 提案应用</dt><dd>false</dd></div>
          </dl>
        </MachineFieldDetails>
      </section>
      <nav className="home-structure-rail" aria-label="记忆总览默认页结构">
        {MEMORY_OVERVIEW_SECTION_ORDER.map((section) => (
          <span data-home-section-anchor={section.id} key={section.id}>{section.label}</span>
        ))}
      </nav>
      <section className="home-shared-focus-strip" aria-label="共享焦点" data-home-section="status_summary">
        <span>当前判断焦点</span>
        <strong>{selectedNode ? humanNodeDisplayTitle(selectedNode) : uiCopy.overview.defaultFocus}</strong>
        <small>{sharedState.focus.home.clusterId ?? uiCopy.overview.noTopic} · 证据已同步</small>
      </section>
      <section className="home-primary-band" aria-label="当前认知状态">
        <article
          className={`home-weather-panel ${model.weatherV2.tone}`}
          data-home-section="weather"
          data-memory-weather-v2="true"
          data-weather-confidence={model.weatherV2.confidenceScore.toFixed(2)}
          data-weather-risk={model.weatherV2.riskScore.toFixed(2)}
        >
          <span>{uiCopy.overview.weatherTitle}</span>
          <strong>{model.weatherV2.label}</strong>
          <p>{model.weatherV2.summary}</p>
          <dl className="home-weather-v2-scores" aria-label="记忆天气 v2 评分信号">
            <div><dt>稳定度</dt><dd>{formatScore(model.weatherV2.stabilityScore)}</dd></div>
            <div><dt>动量</dt><dd>{formatScore(model.weatherV2.momentumScore)}</dd></div>
            <div><dt>风险</dt><dd>{formatScore(model.weatherV2.riskScore)}</dd></div>
            <div><dt>机会</dt><dd>{formatScore(model.weatherV2.opportunityScore)}</dd></div>
          </dl>
          <ul className="home-weather-v2-signals">
            {model.weatherV2.signals.map((signal) => (
              <li key={signal}>{signal}</li>
            ))}
          </ul>
        </article>
        <div className="home-weather-metrics">
          <div data-home-section="themes"><Metric label="主导主题" value={model.topicRows[0]?.count ?? 0} /></div>
          <div data-home-section="proto_stars"><Metric label="上升机会" value={model.protoStarCount} /></div>
          <div data-home-section="black_holes"><Metric label="风险循环" value={model.blackHoleCount} /></div>
          <div data-home-section="status_summary"><Metric label="近期增量" value={deltaStats.recentCount} /></div>
        </div>
      </section>
      <section className="home-status-grid" aria-label="当前判断状态卡片">
        {model.signals.map((signal) => (
          <article className={`home-status-card ${signal.tone}`} key={signal.id}>
            <span>{signal.title}</span>
            <strong>{signal.value}</strong>
            <p>{signal.note}</p>
          </article>
        ))}
      </section>
      <BehaviorIntelligencePanel summary={behaviorIntelligence} />
      <VisualWorkflowWorkbench atlas={atlas} onSwitchView={onSwitchView} />
      <section className="home-preview-grid" aria-label={uiCopy.overview.previewAria} data-home-section="entry_points">
        <button
          className="home-preview-card mini-starfield-preview"
          onClick={() => jumpToPreview(model.miniStarfieldFocus, "galaxy")}
          type="button"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.overview.miniStarfieldTitle}</h3>
            <span>{uiCopy.overview.miniStarfieldAction}</span>
          </div>
          <svg viewBox="0 0 420 190" role="img" aria-label={uiCopy.overview.miniStarfieldAria}>
            <defs>
              <radialGradient id="homeStarfieldGlow" cx="50%" cy="50%" r="60%">
                <stop offset="0%" stopColor="rgba(126, 232, 212, 0.38)" />
                <stop offset="54%" stopColor="rgba(72, 199, 232, 0.11)" />
                <stop offset="100%" stopColor="rgba(2, 3, 8, 0)" />
              </radialGradient>
            </defs>
            <rect className="home-starfield-nebula" x="10" y="10" width="400" height="170" rx="18" />
            <ellipse className="home-starfield-disk" cx="210" cy="96" rx="170" ry="58" />
            {model.miniStarfieldPoints.map((point) => (
              <g className="home-star-point" key={point.id}>
                <title>{point.label}</title>
                <circle cx={point.x} cy={point.y} r={point.radius + 5} fill={point.color} opacity="0.08" />
                <circle cx={point.x} cy={point.y} r={point.radius} fill={point.color} />
              </g>
            ))}
          </svg>
          <small>{model.miniStarfieldSummary}</small>
        </button>
        <button
          className="home-preview-card river-pulse-preview"
          onClick={() => jumpToPreview(model.riverPulseFocus, "timeline")}
          type="button"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.overview.riverPulseTitle}</h3>
            <span>{uiCopy.overview.riverPulseAction}</span>
          </div>
          <div className="river-pulse-lanes" aria-label="近期主题增强和衰退">
            {model.riverPulseSegments.map((segment) => (
              <div className={segment.delta >= 0 ? "river-pulse-row rising" : "river-pulse-row declining"} key={segment.id}>
                <span>{segment.label}</span>
                <i style={{ "--pulse-width": `${segment.intensity}%` } as CSSProperties} aria-hidden="true" />
                <b>{formatSigned(segment.delta)}</b>
              </div>
            ))}
          </div>
          <small>{uiCopy.overview.riverPulseNote}</small>
        </button>
      </section>
      <section
        className="home-action-panel"
        aria-label="下一步行动建议"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="top_actions"
        data-home-section="suggested_actions"
        data-top-actions-section={HOME_ACTION_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>{uiCopy.overview.nextBestActionsTitle}</h3>
          <span>{uiCopy.overview.proposalOnlyLabel}</span>
        </div>
        <div className="home-section-summary-row" aria-label="Top Actions Section fields">
          <span className="home-operation-chip" data-top-actions-field="suggestion">
            <strong>建议</strong>
            <small>{model.actions.length.toLocaleString()} 条行动建议</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="reason">
            <strong>依据</strong>
            <small>来自当前快照的派生分析</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="priority">
            <strong>优先级</strong>
            <small>{humanPriorityLabel(model.actions[0]?.priority)}</small>
          </span>
          <span className="home-operation-chip" data-top-actions-field="status">
            <strong>状态</strong>
            <small>{actionStatusChips.map((chip) => `${chip.label}:${chip.count}`).join(" / ")}</small>
          </span>
        </div>
        <div className="home-action-list">
          {model.actions.map((action) => (
            <button
              data-next-action-card={action.action_id}
              data-next-action-detail-entry="ActionDetailDrawer"
              data-next-action-roi={action.roi_score.toFixed(2)}
              data-next-action-status={action.status}
              data-next-action-urgency={action.urgency}
              key={action.id}
              onClick={() => openActionDetail(action)}
              type="button"
            >
              <span>{humanPriorityLabel(action.priority)}</span>
              <strong>{action.title}</strong>
              <div className="home-action-meta-grid" aria-label="建议动作排序信号">
                <i>ROI {formatScore(action.roi_score)}</i>
                <i>{humanEffortLabel(action.effort_cost)}</i>
                <i>{humanUrgencyLabel(action.urgency)}</i>
                <i className="home-action-status">{humanActionStatusLabel(action.status)}</i>
                <i>{action.evidence_count} 证据</i>
              </div>
              <small>{action.reason}</small>
              <em className="home-action-next-step">{action.next_step}</em>
            </button>
          ))}
        </div>
        <div data-action-detail-drawer-host="true" data-top-action-detail-host="ActionDetailDrawer">
          <ActionDetailDrawer action={selectedActionDetail} onClose={closeActionDetail} onOpenTarget={openActionTarget} />
        </div>
      </section>
      <section className="home-inspector-panel" aria-label={uiCopy.overview.inspectorTitle} data-home-section="entry_points">
        <div className="panel-title-row">
          <h3>{uiCopy.overview.inspectorTitle}</h3>
          <span>{uiCopy.overview.inspectorHint}</span>
        </div>
        <div className="home-inspector-link-list">
          {model.inspectorLinks.map((link) => (
            <button key={link.id} onClick={() => jumpToPreview(link.node, "search")} type="button">
              <strong>{link.title}</strong>
              <span>{link.meta}</span>
            </button>
          ))}
        </div>
      </section>
      <section
        className="home-tier-asset-panel"
        aria-label="层级资产明细"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="level_assets"
        data-home-section="assets"
        data-level-assets-section={HOME_LEVEL_ASSET_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>层级资产明细</h3>
          <span>仅生成提案</span>
        </div>
        <div className="home-operation-chip-grid" aria-label="Level Assets Section groups">
          {levelAssetGroupChips.map((group) => (
            <span
              className="home-operation-chip"
              data-level-asset-count={group.count}
              data-level-asset-group={group.id}
              key={group.id}
            >
              <strong>{group.label}</strong>
              <small>{group.count.toLocaleString()} 项资产</small>
            </span>
          ))}
        </div>
        {model.tierAssets.length ? (
          <div className="home-tier-asset-grid">
            {model.tierAssets.map((asset) => (
              <button
                className="home-tier-asset-card"
                data-tier-asset-card={asset.asset_id}
                data-tier-asset-detail-entry="AssetDetailPanel"
                data-tier-asset-staleness={asset.staleness_status}
                data-tier-asset-value={asset.value_score.toFixed(2)}
                key={asset.id}
                onClick={() => openTierAsset(asset)}
                type="button"
              >
                <span>{asset.asset_tier}</span>
                <strong>{asset.title}</strong>
                <div className="tier-asset-meta-grid" aria-label="层级资产排序信号">
                  <i>{asset.theme}</i>
                  <i>价值 {formatScore(asset.value_score)}</i>
                  <i>{asset.importance}</i>
                  <i>{asset.staleness_status}</i>
                </div>
                <small>{asset.summary}</small>
                <em>{asset.evidence_count} 证据 · {asset.recommended_asset_action}</em>
              </button>
            ))}
          </div>
        ) : (
          <div className="home-tier-asset-empty">当前筛选下没有足够的层级资产明细；请放宽筛选或等待新的 redacted snapshot。</div>
        )}
        <div data-asset-detail-host="AssetDetailPanel" data-asset-detail-panel-host="true">
          <AssetDetailPanel asset={selectedTierAsset} onClose={closeTierAsset} onOpenTarget={openTierAssetTarget} />
        </div>
      </section>
      <section
        className="home-topic-detail-panel"
        aria-label="主题分类明细"
        data-home-operation-mode="proposal_only"
        data-home-operation-section="theme_categories"
        data-home-section="themes"
        data-theme-categories-section={HOME_THEME_CATEGORY_SECTION_VERSION}
      >
        <div className="panel-title-row">
          <h3>主题分类明细</h3>
          <span>仅生成提案</span>
        </div>
        <div className="home-operation-chip-grid" aria-label="Theme Categories Section states">
          {themeCategoryChips.map((state) => (
            <span
              className="home-operation-chip"
              data-theme-category-count={state.count}
              data-theme-category-state={state.id}
              key={state.id}
            >
              <strong>{state.label}</strong>
              <small>{state.count.toLocaleString()} 个主题</small>
            </span>
          ))}
        </div>
        {model.topicDetails.length ? (
          <div className="home-topic-detail-grid">
            {model.topicDetails.map((topic) => (
              <button
                className="home-topic-detail-card"
                data-theme-category-detail-entry="ThemeDetailPanel"
                data-topic-detail-card={topic.topic_id}
                data-topic-state={topic.topic_state}
                data-topic-strength={topic.topic_strength.toFixed(2)}
                key={topic.id}
                onClick={() => openTopicDetail(topic)}
                type="button"
              >
                <span>{topic.topic_state}</span>
                <strong>{topic.topic_label}</strong>
                <div className="topic-detail-meta-grid" aria-label="主题分类排序信号">
                  <i>{topic.category}</i>
                  <i>强度 {formatScore(topic.topic_strength)}</i>
                  <i>{topic.trend}</i>
                  <i>{topic.record_count} 条记录</i>
                </div>
                <small>{topic.matched_reason}</small>
                <em>{topic.evidence_refs.length} 证据 · {topic.starfield_handoff}</em>
              </button>
            ))}
          </div>
        ) : (
          <div className="home-tier-asset-empty">当前筛选下没有足够的主题分类明细；请放宽筛选或等待新的 redacted snapshot。</div>
        )}
        <div data-theme-category-detail-host="ThemeDetailPanel" data-theme-detail-panel-host="true">
          <ThemeDetailPanel topic={selectedTopicDetail} onClose={closeTopicDetail} onOpenTarget={openTopicTarget} />
        </div>
      </section>
      <section className="home-topic-strip" aria-label="主导主题趋势">
        <MiniBarList title={uiCopy.overview.dominantTopics} rows={model.topicRows} />
        <MiniBarList title={uiCopy.overview.memoryTiers} rows={model.tierRows} />
        <MiniBarList title={uiCopy.overview.semanticCategories} rows={model.categoryRows} />
      </section>
    </div>
  );
}
