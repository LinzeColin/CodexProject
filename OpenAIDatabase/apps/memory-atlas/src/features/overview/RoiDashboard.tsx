import { metricValues } from "../../data/atlas";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { DeltaStats } from "../../shared/atlas/contracts";
import { filteredMetricValues, topEntry } from "../../shared/atlas/contributionModels";
import { countBy, humanCategoryLabel, remapValues, topRows } from "../../shared/atlas/semanticHuman";
import { formatScore, formatSigned, sumValues, translateAction, translateStaleness } from "../../shared/atlas/utils";
import { InsightCard, MiniBarList } from "../../shared/ui/primitives";



export function RoiDashboard({
  atlas,
  nodes,
  deltaStats,
  onSelectNode,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const tierValues = filteredMetricValues(nodes, "memory_tier");
  const categoryValues = filteredMetricValues(nodes, "category");
  const globalTierValues = metricValues(atlas, "tier");
  const tierRows = topRows(tierValues, 4);
  const categoryRows = topRows(remapValues(categoryValues, humanCategoryLabel), 8);
  const actionRows = topRows(countBy(nodes, (node) => translateAction(node.metrics?.roi?.recommended_action)), 5);
  const highLeverage = [...nodes]
    .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 12);
  return (
    <div className="dashboard-grid">
      <InsightCard title="当前切片密度" value={nodes.length} note={`全库 ${atlas.overview.active_memory_count.toLocaleString()} 条中的筛选结果`} />
      <InsightCard title="长期资产密度" value={sumValues(tierValues, ["核心画像", "一般"])} note="当前筛选中的核心画像 + 一般" />
      <InsightCard title="临时信息池" value={tierValues["临时"] ?? 0} note={`全局临时 ${globalTierValues["临时"] ?? 0} 条；保留但低权重召回`} />
      <InsightCard title="近期增量" value={deltaStats.recentCount} note={`近 30 天较前 30 天 ${formatSigned(deltaStats.deltaCount)} 条`} />
      <section className="wide-panel roi-visual-strip" aria-label="ROI 视觉密度分布">
        <div className="panel-title-row">
          <h2>ROI 视觉分布</h2>
          <span>层级、分类和建议动作同步当前筛选</span>
        </div>
        <div className="roi-mini-bars">
          <MiniBarList title="层级资产" rows={tierRows} />
          <MiniBarList title="主题分类" rows={categoryRows} />
          <MiniBarList title="建议动作" rows={actionRows} />
        </div>
      </section>
      <section className="wide-panel">
        <div className="panel-title-row">
          <h2>优先观察的高杠杆记忆</h2>
          <span>当前分类热点：{topEntry(categoryValues)?.[0] ?? "暂无"}</span>
        </div>
        <ol>
          {highLeverage.map((node) => (
            <li key={node.id}>
              <button onClick={() => onSelectNode(node)} type="button">
                <strong>{formatScore(node.metrics?.roi?.leverage_score)}</strong>
                <span>{node.label}</span>
                <small>{translateAction(node.metrics?.roi?.recommended_action)} / {translateStaleness(node.metrics?.roi?.staleness_status)}</small>
              </button>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
