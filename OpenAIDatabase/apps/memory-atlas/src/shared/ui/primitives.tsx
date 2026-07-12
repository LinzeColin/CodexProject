import type { CSSProperties } from "react";
import { useMemo } from "react";
import type { AtlasNode } from "../../types";
import { DATA_MAP_DETAIL_PANEL_VERSION, uiCopy } from "../atlas/constants";
import { DeltaStats } from "../atlas/contracts";
import { isGraphParentNode } from "../atlas/contributionModels";
import { dataMapPriorityForNode } from "../atlas/dataGuideModels";
import { DataGuideNode, LayoutNode } from "../atlas/layoutContracts";
import { buildHumanOverview } from "../atlas/sourceSlice";
import { formatSigned, isActivationKey, translateKind } from "../atlas/utils";



export function MiniBarList({ title, rows }: { title: string; rows: Array<{ label: string; count: number }> }) {
  const max = Math.max(1, ...rows.map((row) => row.count));
  return (
    <div className="mini-bar-list">
      <strong>{title}</strong>
      {rows.length ? (
        rows.map((row) => (
          <div className="mini-bar-row" key={`${title}-${row.label}`}>
            <span>{row.label}</span>
            <i style={{ "--bar-width": `${Math.max(4, Math.round((row.count / max) * 100))}%` } as CSSProperties} aria-hidden="true" />
            <b>{row.count.toLocaleString()}</b>
          </div>
        ))
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}



export function DeltaStrip({ stats, compact = false }: { stats: DeltaStats; compact?: boolean }) {
  return (
    <div className={compact ? "delta-strip compact" : "delta-strip"}>
      <div>
        <span>当前切片</span>
        <strong>{stats.totalFiltered.toLocaleString()}</strong>
      </div>
      <div>
        <span>近 30 天</span>
        <strong>{stats.recentCount.toLocaleString()}</strong>
      </div>
      <div>
        <span>较前 30 天</span>
        <strong className={stats.deltaCount >= 0 ? "positive" : "negative"}>{formatSigned(stats.deltaCount)}</strong>
      </div>
      <div>
        <span>新增决策/核心</span>
        <strong>{stats.recentDecisionCount}/{stats.recentCoreCount}</strong>
      </div>
      <div>
        <span>热点分类</span>
        <strong>{stats.topCategory}</strong>
      </div>
    </div>
  );
}



export function HumanOverviewPanel({
  nodes,
  deltaStats,
  compact = false,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  compact?: boolean;
}) {
  const overview = useMemo(() => buildHumanOverview(nodes, deltaStats), [nodes, deltaStats]);
  return (
    <section className={compact ? "human-overview compact" : "human-overview"} aria-label="人类可读记忆摘要">
      <div className="panel-title-row">
        <h3>目前记录了什么</h3>
        <span>{nodes.length.toLocaleString()} 条</span>
      </div>
      <div className="human-overview-grid">
        <div>
          <strong>主要话题</strong>
          <HumanPillList rows={overview.topicRows} />
        </div>
        <div>
          <strong>记忆层级</strong>
          <HumanPillList rows={overview.tierRows} />
        </div>
      </div>
      <div className="human-lists">
        <HumanBulletList title="需要做什么" items={overview.actionItems} />
        <HumanBulletList title="记得做什么" items={overview.rememberItems} />
        <HumanBulletList title="机会/增长方向" items={overview.opportunityItems} />
        <HumanBulletList title="需要留意" items={overview.riskItems} />
      </div>
    </section>
  );
}



export function HumanPillList({ rows }: { rows: Array<{ label: string; count: number }> }) {
  return (
    <div className="human-pill-list">
      {rows.slice(0, 5).map((row) => (
        <span key={row.label}>
          {row.label}
          <b>{row.count}</b>
        </span>
      ))}
    </div>
  );
}



export function HumanBulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="human-bullet-list">
      <strong>{title}</strong>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}



export function GraphSvgNode({
  item,
  selected,
  onSelectNode,
}: {
  item: LayoutNode;
  selected: boolean;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const radius = selected ? item.r + 5 : item.r;
  const isParent = isGraphParentNode(item.node);
  return (
    <g
      className={`${selected ? "graph-node selected" : "graph-node"}${isParent ? " parent-node" : ""}`}
      aria-label={`${translateKind(item.node.kind)} · ${item.node.label}`}
      role="button"
      tabIndex={0}
      onClick={() => onSelectNode(item.node)}
      onKeyDown={(event) => {
        if (isActivationKey(event)) onSelectNode(item.node);
      }}
    >
      <title>{`${translateKind(item.node.kind)} · ${item.node.label}`}</title>
      <circle className="graph-node-halo" cx={item.x} cy={item.y} r={radius + (isParent ? 8 : 5)} fill={item.color} opacity={isParent ? 0.1 : 0.045} />
      <circle className="graph-node-core" cx={item.x} cy={item.y} r={radius} fill={item.color} filter="url(#softGlow)" />
    </g>
  );
}



export function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}



export function SelectFilter({
  label,
  value,
  options,
  formatOption = (option) => option,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  formatOption?: (option: string) => string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="select-filter">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="all">{uiCopy.filters.allOption}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {formatOption(option)}
          </option>
        ))}
      </select>
    </label>
  );
}



export function InsightCard({ title, value, note }: { title: string; value: number; note: string }) {
  return (
    <article className="insight-card">
      <span>{title}</span>
      <strong>{value.toLocaleString()}</strong>
      <p>{note}</p>
    </article>
  );
}



export function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span>
      <i style={{ background: color }} />
      {label}
    </span>
  );
}



export function GraphUsageStrip({ items }: { items: Array<{ label: string; value: string }> }) {
  return (
    <div className="graph-usage-strip" aria-label="图谱读法">
      {items.map((item) => (
        <span key={`${item.label}-${item.value}`}>
          <b>{item.label}</b>
          <em>{item.value}</em>
        </span>
      ))}
    </div>
  );
}



export function DataGuideSvgNode({
  item,
  selected,
  onSelectNode,
}: {
  item: DataGuideNode;
  selected: boolean;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <g
      className={selected ? "data-guide-node selected" : "data-guide-node"}
      aria-label={`${item.frameTitle} · ${item.typeLabel} · ${item.node.label}`}
      role="button"
      tabIndex={0}
      data-data-map-node-detail-entry={DATA_MAP_DETAIL_PANEL_VERSION}
      data-node-id={item.node.id}
      data-node-kind={item.node.kind}
      data-node-importance={item.node.importance ?? ""}
      data-node-priority={dataMapPriorityForNode(item.node)}
      onClick={() => onSelectNode(item.node)}
      onKeyDown={(event) => {
        if (isActivationKey(event)) onSelectNode(item.node);
      }}
    >
      <title>{`${item.frameTitle} · ${item.typeLabel} · ${item.node.label}`}</title>
      <rect className="data-guide-node-card" x={item.x} y={item.y} width={item.w} height={item.h} rx="8" fill={item.color} />
      <rect className="data-guide-node-border" x={item.x} y={item.y} width={item.w} height={item.h} rx="8" fill="none" stroke={item.color} />
      <text x={item.x + 9} y={item.y + 15} className="data-guide-node-type">{item.typeLabel}</text>
      <text x={item.x + 9} y={item.y + 32} className="data-guide-node-title">{item.title}</text>
      <text x={item.x + 9} y={item.y + 48} className="data-guide-node-meta">{item.meta}</text>
      <circle cx={item.x + item.w - 12} cy={item.y + 13} r={Math.max(3, item.signalRadius)} fill={item.color} filter="url(#dataGuideGlow)" />
    </g>
  );
}
