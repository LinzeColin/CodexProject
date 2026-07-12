import { useState } from "react";
import type { AtlasNode, MemoryAtlas, ViewKey } from "../../types";
import { CLIO_LIKE_VISUALS_VERSION, ECONOMIC_LIKE_VISUALS_VERSION } from "../../shared/atlas/constants";
import { ClioClusterDatum, ClioLikeVisualModel, ClioTreeBranch, EconomicLikeVisualModel, EconomicTaskDatum } from "../../shared/atlas/contracts";
import { formatScore } from "../../shared/atlas/utils";



export function BehaviorIntelligencePanel({ summary }: { summary: MemoryAtlas["behavior_intelligence"] }) {
  if (!summary || !summary.counts) return null;
  const clusters = summary.clusters.slice(0, 3);
  const loops = summary.low_value_loops.slice(0, 3);
  const opportunities = summary.opportunities.slice(0, 3);
  if (clusters.length === 0 && loops.length === 0 && opportunities.length === 0) return null;
  return (
    <section
      className="home-behavior-intelligence-panel"
      aria-label="S06 行为智能"
      data-home-section="behavior_intelligence"
      data-s06-review-display="behavior-clusters-low-value-loops-opportunities"
      data-s06-review-schema={summary.schema_version}
      data-s06-cluster-count={summary.counts.clusters}
      data-s06-loop-count={summary.counts.low_value_loops}
      data-s06-opportunity-count={summary.counts.opportunities}
    >
      <div className="panel-title-row">
        <h3>哪些行为模式值得调整</h3>
        <span>已完成行为归纳</span>
      </div>
      <div className="home-behavior-count-row" aria-label="S06 行为智能计数">
        <span><strong>{summary.counts.clusters.toLocaleString()}</strong>主题/层级簇</span>
        <span><strong>{summary.counts.low_value_loops.toLocaleString()}</strong>低价值循环</span>
        <span><strong>{summary.counts.opportunities.toLocaleString()}</strong>机会线索</span>
      </div>
      <div className="home-behavior-card-grid">
        <article className="home-behavior-card">
          <span>主题簇</span>
          {clusters.map((cluster) => (
            <div className="home-behavior-item" key={cluster.cluster_id}>
              <strong>{cluster.label_zh || cluster.cluster_id}</strong>
              <p>{cluster.summary_zh}</p>
              <small>{cluster.evidence_refs.length} 条证据引用 · {cluster.event_count.toLocaleString()} 条事件</small>
            </div>
          ))}
        </article>
        <article className="home-behavior-card">
          <span>低价值循环</span>
          {loops.map((loop) => (
            <div className="home-behavior-item" key={loop.loop_id}>
              <strong>{loop.label_zh || loop.loop_type}</strong>
              <p>{loop.summary_zh}</p>
              <small>{loop.decision_debt?.suggested_closure_question || `${loop.action_half_life_days ?? 0} 天行动半衰期`}</small>
            </div>
          ))}
        </article>
        <article className="home-behavior-card">
          <span>机会线索</span>
          {opportunities.map((opportunity) => (
            <div className="home-behavior-item" key={opportunity.opportunity_id}>
              <strong>{opportunity.label_zh || opportunity.opportunity_type}</strong>
              <p>{opportunity.summary_zh}</p>
              <small>{opportunity.next_step_zh || opportunity.why_not_now_card?.reason_zh}</small>
            </div>
          ))}
        </article>
      </div>
    </section>
  );
}



export function ClioLikeVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: ClioLikeVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedClusterId, setSelectedClusterId] = useState(model.clusters[0]?.id ?? "");
  const selectedCluster = model.clusters.find((cluster) => cluster.id === selectedClusterId) ?? model.clusters[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const treeCopy = visualCopyById.get("cluster_tree");
  const bubbleCopy = visualCopyById.get("bubble_map");
  const explorerCopy = visualCopyById.get("topic_cluster_explorer");

  function openCluster(cluster: ClioClusterDatum | ClioTreeBranch | null, targetView: ViewKey) {
    if (!cluster) return;
    setSelectedClusterId(cluster.id);
    if (cluster.node) onSelectNode(cluster.node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="clio-visual-panel"
      aria-label="S11 P1 Clio-like 多维可视化"
      data-home-section="clio_like_visuals"
      data-s11-p1-clio-like-visuals={CLIO_LIKE_VISUALS_VERSION}
      data-s11-p1-filter-source={model.activeFilters.source}
      data-s11-p1-filter-time={model.activeFilters.time}
      data-s11-p1-filter-project={model.activeFilters.project}
      data-s11-p1-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>主题如何聚合与变化</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.clusters.length.toLocaleString()} 个筛选后主题簇</span>
      </div>
      <div className="clio-filter-strip" aria-label="S11 P1 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="clio-visual-grid">
        <article
          className="clio-visual-card"
          data-s11-p1-action-value={treeCopy?.actionValue}
          data-s11-p1-human-question={treeCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="cluster_tree"
        >
          <div className="clio-visual-heading">
            <span>{treeCopy?.title}</span>
            <strong data-s11-p1-insight-header={treeCopy?.insightHeader}>{treeCopy?.insightHeader}</strong>
            <p>{treeCopy?.humanQuestion}</p>
            <em>{treeCopy?.actionValue}</em>
          </div>
          <svg className="cluster-tree-svg" viewBox="0 0 440 260" role="img" aria-label="层级簇树">
            <line className="cluster-tree-trunk" x1="70" y1="130" x2="174" y2="130" />
            <circle className="cluster-tree-root" cx="70" cy="130" r="30" />
            <text x="70" y="126" textAnchor="middle">当前</text>
            <text x="70" y="144" textAnchor="middle">筛选</text>
            {model.treeBranches.map((branch) => (
              <g
                className={branch.id === selectedCluster?.id ? "cluster-tree-branch active" : "cluster-tree-branch"}
                key={branch.id}
                onClick={() => openCluster(branch, "galaxy")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openCluster(branch, "galaxy");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${branch.label}，${branch.count} 条记忆`}</title>
                <line x1={branch.x1} y1={branch.y1} x2={branch.x2} y2={branch.y2} />
                <circle cx={branch.x2} cy={branch.y2} r={Math.max(14, Math.min(30, branch.count + 12))} />
                <text x={branch.x2 + 36} y={branch.y2 - 4}>{branch.label}</text>
                <text x={branch.x2 + 36} y={branch.y2 + 14}>{branch.count} 条</text>
              </g>
            ))}
          </svg>
        </article>

        <article
          className="clio-visual-card"
          data-s11-p1-action-value={bubbleCopy?.actionValue}
          data-s11-p1-human-question={bubbleCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="bubble_map"
        >
          <div className="clio-visual-heading">
            <span>{bubbleCopy?.title}</span>
            <strong data-s11-p1-insight-header={bubbleCopy?.insightHeader}>{bubbleCopy?.insightHeader}</strong>
            <p>{bubbleCopy?.humanQuestion}</p>
            <em>{bubbleCopy?.actionValue}</em>
          </div>
          <svg className="bubble-map-svg" viewBox="0 0 440 260" role="img" aria-label="Bubble Map">
            <line className="bubble-axis" x1="56" y1="210" x2="396" y2="210" />
            <line className="bubble-axis" x1="56" y1="42" x2="56" y2="210" />
            <text className="bubble-axis-label" x="260" y="238">近期活跃度</text>
            <text className="bubble-axis-label" x="20" y="132" transform="rotate(-90 20 132)">ROI</text>
            {model.clusters.map((cluster) => (
              <g
                className={cluster.id === selectedCluster?.id ? "semantic-bubble active" : "semantic-bubble"}
                key={cluster.id}
                onClick={() => openCluster(cluster, "galaxy")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openCluster(cluster, "galaxy");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${cluster.label}，ROI ${formatScore(cluster.roiScore)}，${cluster.count} 条记忆`}</title>
                <circle cx={cluster.x} cy={cluster.y} r={cluster.radius} fill={cluster.color} />
                <text x={cluster.x} y={cluster.y + cluster.radius + 14} textAnchor="middle">{cluster.label.slice(0, 8)}</text>
              </g>
            ))}
          </svg>
        </article>

        <article
          className="clio-visual-card topic-cluster-explorer"
          data-s11-p1-action-value={explorerCopy?.actionValue}
          data-s11-p1-human-question={explorerCopy?.humanQuestion}
          data-s11-p1-interactive="true"
          data-s11-p1-visual-id="topic_cluster_explorer"
        >
          <div className="clio-visual-heading">
            <span>{explorerCopy?.title}</span>
            <strong data-s11-p1-insight-header={explorerCopy?.insightHeader}>{explorerCopy?.insightHeader}</strong>
            <p>{explorerCopy?.humanQuestion}</p>
            <em>{explorerCopy?.actionValue}</em>
          </div>
          <div className="topic-cluster-explorer-list" aria-label="Topic Cluster Explorer">
            {model.explorerRows.map((cluster) => (
              <button
                className={cluster.id === selectedCluster?.id ? "active" : ""}
                data-clio-cluster-id={cluster.id}
                key={cluster.id}
                onClick={() => openCluster(cluster, "search")}
                type="button"
              >
                <strong>{cluster.label}</strong>
                <span>{cluster.count} 条 · ROI {formatScore(cluster.roiScore)}</span>
                <small>{cluster.dominantCategory} · {cluster.recentCount} 条近期 · {cluster.evidenceCount} 证据</small>
              </button>
            ))}
          </div>
          {selectedCluster ? (
            <div className="clio-selected-cluster" aria-label="选中簇行动说明">
              <span>{selectedCluster.label}</span>
              <strong>{selectedCluster.count} 条记忆，{selectedCluster.sourceCount} 个来源</strong>
              <p>下一步：打开查找与核对，复核代表记录后再比较投入回报。</p>
            </div>
          ) : null}
        </article>
      </div>
    </section>
  );
}



export function EconomicLikeVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: EconomicLikeVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedTaskId, setSelectedTaskId] = useState(model.taskRows[0]?.id ?? "");
  const selectedTask = model.taskRows.find((task) => task.id === selectedTaskId) ?? model.taskRows[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const treemapCopy = visualCopyById.get("task_treemap");
  const automationCopy = visualCopyById.get("automation_vs_augmentation");
  const scatterCopy = visualCopyById.get("roi_scatter");
  const radarCopy = visualCopyById.get("opportunity_radar");
  const radarPoints = model.radarAxes
    .map((axis, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, model.radarAxes.length)) * Math.PI * 2;
      const radius = 24 + axis.value * 76;
      return `${140 + Math.cos(angle) * radius},${120 + Math.sin(angle) * radius}`;
    })
    .join(" ");

  function openTask(task: EconomicTaskDatum | null, targetView: ViewKey) {
    if (!task) return;
    setSelectedTaskId(task.id);
    if (task.node) onSelectNode(task.node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="economic-visual-panel"
      aria-label="S11 P2 Economic-like 多维可视化"
      data-home-section="economic_like_visuals"
      data-s11-p2-economic-like-visuals={ECONOMIC_LIKE_VISUALS_VERSION}
      data-s11-p2-filter-source={model.activeFilters.source}
      data-s11-p2-filter-time={model.activeFilters.time}
      data-s11-p2-filter-project={model.activeFilters.project}
      data-s11-p2-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>时间和精力投在哪里</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.taskRows.length.toLocaleString()} 个筛选后任务面</span>
      </div>
      <div className="economic-filter-strip" aria-label="S11 P2 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="economic-visual-grid">
        <article
          className="economic-visual-card task-treemap-card"
          data-s11-p2-action-value={treemapCopy?.actionValue}
          data-s11-p2-human-question={treemapCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="task_treemap"
        >
          <div className="economic-visual-heading">
            <span>{treemapCopy?.title}</span>
            <strong data-s11-p2-insight-header={treemapCopy?.insightHeader}>{treemapCopy?.insightHeader}</strong>
            <p>{treemapCopy?.humanQuestion}</p>
            <em>{treemapCopy?.actionValue}</em>
          </div>
          <div className="task-treemap" role="list" aria-label="Task Treemap">
            {model.taskRows.map((task) => (
              <button
                className={task.id === selectedTask?.id ? "active" : ""}
                key={task.id}
                onClick={() => openTask(task, "roi")}
                style={{ flexBasis: `${task.width}px`, minHeight: `${task.height}px`, borderColor: task.color }}
                type="button"
              >
                <strong>{task.label}</strong>
                <span>{task.count} 条 · ROI {formatScore(task.roiScore)}</span>
                <small>{task.sourceCount} 来源 · {task.recentCount} 近期</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="economic-visual-card automation-augmentation-card"
          data-s11-p2-action-value={automationCopy?.actionValue}
          data-s11-p2-human-question={automationCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="automation_vs_augmentation"
        >
          <div className="economic-visual-heading">
            <span>{automationCopy?.title}</span>
            <strong data-s11-p2-insight-header={automationCopy?.insightHeader}>{automationCopy?.insightHeader}</strong>
            <p>{automationCopy?.humanQuestion}</p>
            <em>{automationCopy?.actionValue}</em>
          </div>
          <div className="automation-augmentation-chart" aria-label="Automation vs Augmentation">
            {model.taskRows.slice(0, 5).map((task) => (
              <button
                className={task.id === selectedTask?.id ? "active" : ""}
                key={task.id}
                onClick={() => openTask(task, "search")}
                type="button"
              >
                <strong>{task.label}</strong>
                <span>
                  <i style={{ width: `${Math.round(task.automationShare * 100)}%` }} />
                  <b style={{ width: `${Math.round(task.augmentationShare * 100)}%` }} />
                </span>
                <small>自动化 {formatScore(task.automationShare)} · 增强 {formatScore(task.augmentationShare)}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="economic-visual-card"
          data-s11-p2-action-value={scatterCopy?.actionValue}
          data-s11-p2-human-question={scatterCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="roi_scatter"
        >
          <div className="economic-visual-heading">
            <span>{scatterCopy?.title}</span>
            <strong data-s11-p2-insight-header={scatterCopy?.insightHeader}>{scatterCopy?.insightHeader}</strong>
            <p>{scatterCopy?.humanQuestion}</p>
            <em>{scatterCopy?.actionValue}</em>
          </div>
          <svg className="roi-scatter-svg" viewBox="0 0 440 260" role="img" aria-label="ROI Scatter">
            <line className="economic-axis" x1="58" y1="214" x2="398" y2="214" />
            <line className="economic-axis" x1="58" y1="44" x2="58" y2="214" />
            <text className="economic-axis-label" x="250" y="240">近期活跃度</text>
            <text className="economic-axis-label" x="22" y="132" transform="rotate(-90 22 132)">ROI</text>
            {model.scatterPoints.map((task) => (
              <g
                className={task.id === selectedTask?.id ? "roi-scatter-point active" : "roi-scatter-point"}
                key={task.id}
                onClick={() => openTask(task, "roi")}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") openTask(task, "roi");
                }}
                role="button"
                tabIndex={0}
              >
                <title>{`${task.label}，ROI ${formatScore(task.roiScore)}，机会 ${formatScore(task.opportunityScore)}`}</title>
                <circle cx={task.x} cy={task.y} fill={task.color} r={task.radius} />
              </g>
            ))}
          </svg>
        </article>

        <article
          className="economic-visual-card opportunity-radar-card"
          data-s11-p2-action-value={radarCopy?.actionValue}
          data-s11-p2-human-question={radarCopy?.humanQuestion}
          data-s11-p2-interactive="true"
          data-s11-p2-visual-id="opportunity_radar"
        >
          <div className="economic-visual-heading">
            <span>{radarCopy?.title}</span>
            <strong data-s11-p2-insight-header={radarCopy?.insightHeader}>{radarCopy?.insightHeader}</strong>
            <p>{radarCopy?.humanQuestion}</p>
            <em>{radarCopy?.actionValue}</em>
          </div>
          <svg className="opportunity-radar-svg" viewBox="0 0 280 240" role="img" aria-label="Opportunity Radar">
            <circle cx="140" cy="120" r="96" />
            <circle cx="140" cy="120" r="56" />
            <polygon points={radarPoints} />
            {model.radarAxes.map((axis, index) => {
              const angle = -Math.PI / 2 + (index / Math.max(1, model.radarAxes.length)) * Math.PI * 2;
              const x = 140 + Math.cos(angle) * 108;
              const y = 120 + Math.sin(angle) * 108;
              return (
                <g key={axis.id}>
                  <line x1="140" y1="120" x2={x} y2={y} />
                  <text x={x} y={y}>{axis.label}</text>
                </g>
              );
            })}
          </svg>
          {selectedTask ? (
            <button className="economic-selected-task" onClick={() => openTask(selectedTask, "summary")} type="button">
              <span>{selectedTask.label}</span>
              <strong>机会 {formatScore(selectedTask.opportunityScore)} · 风险 {formatScore(selectedTask.riskScore)}</strong>
              <small>打开总结闭环复核是否继续投入。</small>
            </button>
          ) : null}
        </article>
      </div>
    </section>
  );
}
