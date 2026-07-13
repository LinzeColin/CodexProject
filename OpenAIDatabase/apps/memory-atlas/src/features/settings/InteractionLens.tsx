import { ChevronLeft, ChevronRight, Crosshair, FilterX } from "lucide-react";
import { useMemo } from "react";
import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasFilters, AtlasNode, ViewKey } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION, views } from "../../shared/atlas/constants";
import { ContributionPeriodDetail, FilterKey, FilteredAtlasSlice, SourceOption, TimelineTimeRangeSelection } from "../../shared/atlas/contracts";
import { scaleLabel } from "../../shared/atlas/contributionModels";
import { humanCategoryLabel, humanNodeDisplayTitle } from "../../shared/atlas/semanticHuman";
import { selectableLensNodes } from "../../shared/atlas/sourceSlice";
import { formatSigned } from "../../shared/atlas/utils";
import { MachineFieldDetails } from "../../shared/ui/display";
import { activeFilterChips } from "../../shared/ui/visualStyles";



export function InteractionLens({
  activeView,
  filters,
  sharedState,
  selectedContributionPeriod,
  selectedNode,
  slice,
  sourceOptions,
  timelineTimeRange,
  onClearFilter,
  onClearTimelineRange,
  onFocusTheme,
  onResetFilters,
  onSelectAdjacent,
}: {
  activeView: ViewKey;
  filters: AtlasFilters;
  sharedState: SharedAtlasState;
  selectedContributionPeriod: ContributionPeriodDetail | null;
  selectedNode: AtlasNode | null;
  slice: FilteredAtlasSlice;
  sourceOptions: SourceOption[];
  timelineTimeRange: TimelineTimeRangeSelection | null;
  onClearFilter: (key: FilterKey) => void;
  onClearTimelineRange: () => void;
  onFocusTheme: () => void;
  onResetFilters: () => void;
  onSelectAdjacent: (direction: -1 | 1) => void;
}) {
  const candidates = useMemo(() => selectableLensNodes(slice, selectedNode), [selectedNode, slice]);
  const selectedIndex = selectedNode ? candidates.findIndex((node) => node.id === selectedNode.id) : -1;
  const canStep = selectedIndex >= 0 && candidates.length > 1;
  const chips = useMemo(() => activeFilterChips(filters, sourceOptions), [filters, sourceOptions]);
  const focusTheme = selectedNode?.visual?.cluster;
  const viewLabel = views.find((view) => view.key === activeView)?.label ?? "当前视图";
  const focusTitle = selectedContributionPeriod
    ? `${scaleLabel(selectedContributionPeriod.scale)} · ${selectedContributionPeriod.bucket.label}`
    : selectedNode
      ? humanNodeDisplayTitle(selectedNode)
      : "暂无焦点";
  const focusMeta = selectedContributionPeriod
    ? `活动 ${selectedContributionPeriod.bucket.activityScore.toLocaleString()} / 筛选记忆 ${selectedContributionPeriod.bucket.filteredMemoryCount.toLocaleString()} / 环比 ${formatSigned(selectedContributionPeriod.bucket.delta ?? 0)}`
    : selectedNode
      ? `${normalizeMemoryTier(selectedNode.memory_tier)} / ${humanCategoryLabel(selectedNode.category)} / ${selectedNode.date || "未知日期"}`
      : "选择节点、事件或时间格后同步更新";

  return (
    <section
      className="interaction-lens"
      aria-label="当前交互焦点"
      data-shared-state={sharedState.schema_version}
      data-stage9-phase1-shared-state={CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION}
      data-stage9-synchronized-filters="shared_state_filters synchronized_filters"
      data-sync-revision={sharedState.sync.revision}
      data-sync-source={sharedState.sync.updatedBy}
      data-sync-action={sharedState.sync.lastAction}
      data-shared-focus-node={sharedState.focus.inspector.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.inspector.clusterId ?? ""}
      data-shared-time-range={sharedState.focus.inspector.timeRangeId ?? ""}
    >
      <div className="lens-focus">
        <span className="lens-badge">{viewLabel}</span>
        <div>
          <strong>{focusTitle}</strong>
          <span>{focusMeta}</span>
        </div>
      </div>
      <div className="lens-stepper" aria-label="焦点切换">
        <button aria-label="上一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(-1)} title="上一个焦点" type="button">
          <ChevronLeft size={16} />
        </button>
        <span>{selectedIndex >= 0 ? `${selectedIndex + 1}/${candidates.length}` : `0/${candidates.length}`}</span>
        <button aria-label="下一个焦点" disabled={!canStep} onClick={() => onSelectAdjacent(1)} title="下一个焦点" type="button">
          <ChevronRight size={16} />
        </button>
      </div>
      <div className="lens-actions">
        <button disabled={!focusTheme || filters.theme === focusTheme} onClick={onFocusTheme} type="button">
          <Crosshair size={15} />
          <span>聚焦主题</span>
        </button>
        <button disabled={!chips.length} onClick={onResetFilters} type="button">
          <FilterX size={15} />
          <span>重置筛选</span>
        </button>
      </div>
      <MachineFieldDetails title="焦点技术详情" className="lens-technical-details">
        <div className="lens-state-strip" aria-label="宇宙状态（Universe State）快照">
          <span>宇宙状态（Universe State）</span>
          <strong>信号 {sharedState.selection.signal}</strong>
          <em>来源 {sharedState.sync.updatedBy} · r{sharedState.sync.revision}</em>
        </div>
      </MachineFieldDetails>
      <div className="filter-chip-row" aria-label="活跃筛选">
        {chips.length || timelineTimeRange ? (
          <>
          {timelineTimeRange ? (
            <button className="timeline-range-chip" onClick={onClearTimelineRange} title="清除时间河选择" type="button">
              <span>时间河</span>
              <strong>{timelineTimeRange.label}</strong>
              <em aria-hidden="true">×</em>
            </button>
          ) : null}
          {chips.map((chip) => (
            <button key={chip.key} onClick={() => onClearFilter(chip.key)} title={`清除${chip.label}`} type="button">
              <span>{chip.label}</span>
              <strong>{chip.value}</strong>
              <em aria-hidden="true">×</em>
            </button>
          ))}
          </>
        ) : (
          <span className="filter-empty">全部数据</span>
        )}
      </div>
    </section>
  );
}
