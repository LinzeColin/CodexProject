import type { CSSProperties } from "react";
import { useState } from "react";
import type { AtlasNode, ViewKey } from "../../types";
import { HUMAN_QUESTION_MAP_VERSION, WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION } from "../../shared/atlas/constants";
import { HumanQuestionMapFamilyId, HumanQuestionMapModel, WorkflowLatentGovernanceVisualModel } from "../../shared/atlas/contracts";
import { formatScore } from "../../shared/atlas/utils";
import { workflowHeatColor } from "../../shared/atlas/workflowQuestionModels";
import { MachineFieldDetails } from "../../shared/ui/display";



export function WorkflowLatentGovernanceVisualPanel({
  model,
  onSelectNode,
  onSwitchView,
}: {
  model: WorkflowLatentGovernanceVisualModel;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [selectedAxisId, setSelectedAxisId] = useState(model.latentAxes[0]?.id ?? "");
  const selectedAxis = model.latentAxes.find((axis) => axis.id === selectedAxisId) ?? model.latentAxes[0] ?? null;
  const visualCopyById = new Map(model.visualCopy.map((visual) => [visual.id, visual]));
  const sankeyCopy = visualCopyById.get("agent_decision_sankey");
  const heatmapCopy = visualCopyById.get("friction_heatmap");
  const radarCopy = visualCopyById.get("latent_radar");
  const timelineCopy = visualCopyById.get("evidence_timeline");
  const formulaCopy = visualCopyById.get("formula_explorer");
  const radarPoints = model.latentAxes
    .map((axis, index) => {
      const angle = -Math.PI / 2 + (index / Math.max(1, model.latentAxes.length)) * Math.PI * 2;
      const radius = 28 + axis.value * 78;
      return `${150 + Math.cos(angle) * radius},${126 + Math.sin(angle) * radius}`;
    })
    .join(" ");

  function openNode(node: AtlasNode | null, targetView: ViewKey) {
    if (node) onSelectNode(node);
    onSwitchView(targetView);
  }

  return (
    <section
      className="workflow-governance-visual-panel"
      aria-label="S11 P3 Workflow/latent/governance 多维可视化"
      data-home-section="workflow_latent_governance_visuals"
      data-s11-p3-workflow-latent-governance-visuals={WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION}
      data-s11-p3-filter-source={model.activeFilters.source}
      data-s11-p3-filter-time={model.activeFilters.time}
      data-s11-p3-filter-project={model.activeFilters.project}
      data-s11-p3-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>执行链路哪里需要治理</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.visualCopy.length.toLocaleString()} 张决策图</span>
      </div>
      <div className="workflow-governance-filter-strip" aria-label="S11 P3 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="workflow-governance-visual-grid">
        <article
          className="workflow-governance-visual-card sankey-card"
          data-s11-p3-action-value={sankeyCopy?.actionValue}
          data-s11-p3-human-question={sankeyCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="agent_decision_sankey"
        >
          <div className="workflow-governance-visual-heading">
            <span>{sankeyCopy?.title}</span>
            <strong data-s11-p3-insight-header={sankeyCopy?.insightHeader}>{sankeyCopy?.insightHeader}</strong>
            <p>{sankeyCopy?.humanQuestion}</p>
            <em>{sankeyCopy?.actionValue}</em>
          </div>
          <svg className="workflow-sankey-svg" viewBox="0 0 520 250" role="img" aria-label="Codex/Agent Decision Sankey">
            <text x="24" y="36">人类目标</text>
            <text x="160" y="36">Codex 执行</text>
            <text x="300" y="36">验证复审</text>
            <text x="426" y="36">治理/授权</text>
            {model.sankeyLinks.map((link, index) => {
              const y = link.y;
              const startX = 48 + index * 78;
              const endX = startX + 124;
              return (
                <g
                  className="workflow-sankey-link"
                  key={link.id}
                  onClick={() => openNode(link.node, "summary")}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") openNode(link.node, "summary");
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <title>{`${link.sourceLabel} 到 ${link.targetLabel}：${link.value} 条证据`}</title>
                  <path
                    d={`M ${startX} ${y} C ${startX + 48} ${y - 34}, ${endX - 48} ${y + 34}, ${endX} ${y}`}
                    stroke={link.color}
                    strokeWidth={link.width}
                  />
                  <circle cx={startX} cy={y} r="7" />
                  <circle cx={endX} cy={y} r="7" />
                  <text x={startX - 16} y={y + 31}>{link.sourceLabel}</text>
                  <text x={endX - 18} y={y - 22}>{link.targetLabel}</text>
                </g>
              );
            })}
          </svg>
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={heatmapCopy?.actionValue}
          data-s11-p3-human-question={heatmapCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="friction_heatmap"
        >
          <div className="workflow-governance-visual-heading">
            <span>{heatmapCopy?.title}</span>
            <strong data-s11-p3-insight-header={heatmapCopy?.insightHeader}>{heatmapCopy?.insightHeader}</strong>
            <p>{heatmapCopy?.humanQuestion}</p>
            <em>{heatmapCopy?.actionValue}</em>
          </div>
          <div className="friction-heatmap-grid" aria-label="Friction Heatmap">
            {model.frictionCells.map((cell) => (
              <button
                key={cell.id}
                onClick={() => openNode(cell.node, "search")}
                style={{ "--heat": cell.intensity, "--cell-color": workflowHeatColor(cell.intensity) } as CSSProperties}
                type="button"
              >
                <strong>{cell.rowLabel}</strong>
                <span>{cell.columnLabel}</span>
                <small>{cell.count} 条 · {cell.action}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="workflow-governance-visual-card latent-radar-card"
          data-s11-p3-action-value={radarCopy?.actionValue}
          data-s11-p3-human-question={radarCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="latent_radar"
        >
          <div className="workflow-governance-visual-heading">
            <span>{radarCopy?.title}</span>
            <strong data-s11-p3-insight-header={radarCopy?.insightHeader}>{radarCopy?.insightHeader}</strong>
            <p>{radarCopy?.humanQuestion}</p>
            <em>{radarCopy?.actionValue}</em>
          </div>
          <svg className="latent-radar-svg" viewBox="0 0 300 260" role="img" aria-label="Latent Radar">
            <circle cx="150" cy="126" r="106" />
            <circle cx="150" cy="126" r="66" />
            <polygon points={radarPoints} />
            {model.latentAxes.map((axis, index) => {
              const angle = -Math.PI / 2 + (index / Math.max(1, model.latentAxes.length)) * Math.PI * 2;
              const x = 150 + Math.cos(angle) * 118;
              const y = 126 + Math.sin(angle) * 118;
              return (
                <g
                  className={axis.id === selectedAxis?.id ? "latent-radar-axis active" : "latent-radar-axis"}
                  key={axis.id}
                  onClick={() => {
                    setSelectedAxisId(axis.id);
                    openNode(axis.node, "summary");
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      setSelectedAxisId(axis.id);
                      openNode(axis.node, "summary");
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <line x1="150" y1="126" x2={x} y2={y} />
                  <text x={x} y={y}>{axis.label}</text>
                </g>
              );
            })}
          </svg>
          {selectedAxis ? (
            <button className="latent-radar-selected" onClick={() => openNode(selectedAxis.node, "summary")} type="button">
              <span>{selectedAxis.label}</span>
              <strong>{formatScore(selectedAxis.value)} · {selectedAxis.confidenceLabel} · 证据 {selectedAxis.evidenceBadge}</strong>
              <small>打开总结闭环，验证或降权这条潜性信号。</small>
            </button>
          ) : null}
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={timelineCopy?.actionValue}
          data-s11-p3-human-question={timelineCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="evidence_timeline"
        >
          <div className="workflow-governance-visual-heading">
            <span>{timelineCopy?.title}</span>
            <strong data-s11-p3-insight-header={timelineCopy?.insightHeader}>{timelineCopy?.insightHeader}</strong>
            <p>{timelineCopy?.humanQuestion}</p>
            <em>{timelineCopy?.actionValue}</em>
          </div>
          <div className="evidence-timeline-track" aria-label="Evidence Timeline">
            {model.evidenceEvents.map((event) => (
              <button
                key={event.id}
                onClick={() => openNode(event.node, "timeline")}
                style={{ left: `${event.x}%` }}
                type="button"
              >
                <strong>{event.dateLabel}</strong>
                <span>{event.label}</span>
                <small>{event.sourceLabel} · 证据 {event.evidenceCount}</small>
              </button>
            ))}
          </div>
        </article>

        <article
          className="workflow-governance-visual-card"
          data-s11-p3-action-value={formulaCopy?.actionValue}
          data-s11-p3-human-question={formulaCopy?.humanQuestion}
          data-s11-p3-interactive="true"
          data-s11-p3-visual-id="formula_explorer"
        >
          <div className="workflow-governance-visual-heading">
            <span>{formulaCopy?.title}</span>
            <strong data-s11-p3-insight-header={formulaCopy?.insightHeader}>{formulaCopy?.insightHeader}</strong>
            <p>{formulaCopy?.humanQuestion}</p>
            <em>{formulaCopy?.actionValue}</em>
          </div>
          <MachineFieldDetails title="查看公式参数与来源" className="formula-technical-details">
            <div className="formula-explorer-list" aria-label="Formula Explorer/Parameter Inspector">
              {model.formulaRows.map((row) => (
                <button key={row.id} onClick={() => openNode(row.node, "roi")} type="button">
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                  <small>{row.description}</small>
                  <em>{row.sourcePath}</em>
                </button>
              ))}
            </div>
          </MachineFieldDetails>
        </article>
      </div>
    </section>
  );
}



export function HumanQuestionMapPanel({
  model,
  onSwitchView,
}: {
  model: HumanQuestionMapModel;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [familyFilter, setFamilyFilter] = useState<HumanQuestionMapFamilyId | "all">("all");
  const visibleEntries = familyFilter === "all" ? model.entries : model.entries.filter((entry) => entry.familyId === familyFilter);
  const familyOptions: Array<{ id: HumanQuestionMapFamilyId | "all"; label: string; count: number }> = [
    { id: "all", label: "全部问题", count: model.entries.length },
    { id: "clio_like", label: "主题/簇", count: model.entries.filter((entry) => entry.familyId === "clio_like").length },
    { id: "economic_like", label: "ROI/任务", count: model.entries.filter((entry) => entry.familyId === "economic_like").length },
    { id: "workflow_governance", label: "工作流/治理", count: model.entries.filter((entry) => entry.familyId === "workflow_governance").length },
  ];

  return (
    <section
      className="human-question-map-panel"
      aria-label="S11 P4 Human Question Map"
      data-home-section="human_question_map"
      data-s11-p4-human-question-map={HUMAN_QUESTION_MAP_VERSION}
      data-s11-p4-filter-source={model.activeFilters.source}
      data-s11-p4-filter-time={model.activeFilters.time}
      data-s11-p4-filter-project={model.activeFilters.project}
      data-s11-p4-filter-task={model.activeFilters.task}
    >
      <div className="panel-title-row">
        <div>
          <h3>问题如何连接到行动</h3>
          <p>{model.summary}</p>
        </div>
        <span>{model.p0VisualCount.toLocaleString()} 张可行动图谱</span>
      </div>
      <div className="human-question-map-gate-row" aria-label="S11 P4 Visual ROI Gate 汇总">
        <span><strong>{model.p0VisualCount.toLocaleString()}</strong>已纳入</span>
        <span><strong>{model.failedP0Count.toLocaleString()}</strong>未通过</span>
        <span><strong>{model.excludedCandidates.length.toLocaleString()}</strong>候选排除</span>
        <span><strong>{model.strongestGateLabel}</strong>最强决策族</span>
      </div>
      <div className="human-question-map-filter-strip" aria-label="S11 P4 图谱过滤维度">
        <span><strong>来源</strong>{model.activeFilters.source}</span>
        <span><strong>时间</strong>{model.activeFilters.time}</span>
        <span><strong>项目</strong>{model.activeFilters.project}</span>
        <span><strong>任务</strong>{model.activeFilters.task}</span>
      </div>
      <div className="human-question-map-family-tabs" aria-label="Human Question Map family filter">
        {familyOptions.map((option) => (
          <button
            className={familyFilter === option.id ? "active" : ""}
            key={option.id}
            onClick={() => setFamilyFilter(option.id)}
            type="button"
          >
            <span>{option.label}</span>
            <strong>{option.count.toLocaleString()}</strong>
          </button>
        ))}
      </div>
      <div className="human-question-map-grid">
        {visibleEntries.map((entry) => (
          <button
            className="human-question-map-entry"
            data-s11-p4-action-value={entry.actionValue}
            data-s11-p4-family={entry.familyId}
            data-s11-p4-human-question={entry.humanQuestion}
            data-s11-p4-interactive="true"
            data-s11-p4-map-entry="true"
            data-s11-p4-p0-included={entry.p0Included ? "true" : "false"}
            data-s11-p4-visual-id={entry.id}
            data-s11-p4-visual-roi-gate={entry.visualRoiGatePass ? "pass" : "fail"}
            key={entry.id}
            onClick={() => onSwitchView(entry.targetView)}
            type="button"
          >
            <span>{entry.familyLabel}</span>
            <strong>{entry.title}</strong>
            <em>{entry.insightHeader}</em>
            <p>{entry.humanQuestion}</p>
            <small>{entry.actionValue}</small>
            <b>{entry.gateReason}</b>
          </button>
        ))}
      </div>
      <div className="human-question-map-exclusion-list" aria-label="Visual ROI Gate 未进 P0 候选">
        {model.excludedCandidates.map((candidate) => (
          <span data-s11-p4-p0-included="false" data-s11-p4-visual-roi-gate="fail" key={candidate.id}>
            <strong>{candidate.title}</strong>
            <small>{candidate.reason}</small>
          </span>
        ))}
      </div>
    </section>
  );
}
