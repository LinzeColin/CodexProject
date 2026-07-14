import { useEffect, useMemo, useState } from "react";
import type { AtlasEdge, AtlasNode } from "../../types";
import { ProposalEditor } from "../../components/ProposalEditor";
import { DATA_MAP_DETAIL_PANEL_VERSION, DATA_MAP_PROPOSAL_ENTRY_VERSION, DATA_MAP_RELATION_EXPLANATION_VERSION, DATA_MAP_STRUCTURE_MODEL_VERSION } from "../../shared/atlas/constants";
import { DeltaStats } from "../../shared/atlas/contracts";
import { buildDataGuideLayout, buildDataMapNodeDetail } from "../../shared/atlas/dataGuideModels";
import { DATA_MAP_STRUCTURE_LAYERS, DataGuideEdge } from "../../shared/atlas/layoutContracts";
import { humanNodeDisplayTitle } from "../../shared/atlas/semanticHuman";
import { isActivationKey, translateKind } from "../../shared/atlas/utils";
import { DataGuideSvgNode, DeltaStrip, GraphUsageStrip, LegendItem } from "../../shared/ui/primitives";



export function DataGuideMap({
  nodes,
  edges,
  selectedNode,
  deltaStats,
  parentSnapshotId,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  deltaStats: DeltaStats;
  parentSnapshotId: string;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const display = useMemo(() => buildDataGuideLayout(nodes, edges, 64), [nodes, edges]);
  const [selectedDataMapRelationId, setSelectedDataMapRelationId] = useState<string | null>(null);
  const selectedRelation = useMemo(
    () => display.edges.find((edge) => edge.id === selectedDataMapRelationId) ?? null,
    [display.edges, selectedDataMapRelationId],
  );

  useEffect(() => {
    window.__memoryAtlasStage6Phase1 = () => ({
      structureModelVersion: DATA_MAP_STRUCTURE_MODEL_VERSION,
      relationExplanationVersion: DATA_MAP_RELATION_EXPLANATION_VERSION,
      layers: DATA_MAP_STRUCTURE_LAYERS.map((layer) => layer.id),
      visibleNodeCount: display.visibleNodeCount,
      relationCount: display.edgeCount,
      selectedRelationId: selectedDataMapRelationId,
      defaultCollapsed: true,
      boundary: "No Phase 6.2 editing",
      rawPrivateDataIncluded: false,
      directActiveMemoryWriteback: false,
      proposalWrite: false,
    });
    return () => {
      delete window.__memoryAtlasStage6Phase1;
    };
  }, [display.edgeCount, display.visibleNodeCount, selectedDataMapRelationId]);

  useEffect(() => {
    window.__memoryAtlasStage6Phase2 = () => ({
      detailPanelVersion: DATA_MAP_DETAIL_PANEL_VERSION,
      proposalEntryVersion: DATA_MAP_PROPOSAL_ENTRY_VERSION,
      selectedNodeId: selectedNode?.id ?? null,
      selectedNodeKind: selectedNode?.kind ?? null,
      detailFields: ["asset", "theme", "suggested_action", "importance", "priority"],
      proposalOnly: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage6Phase2;
    };
  }, [selectedNode?.id, selectedNode?.kind]);

  return (
    <div
      className="visual-workspace data-guide-map"
      data-data-map-structure-model={DATA_MAP_STRUCTURE_MODEL_VERSION}
      data-data-map-relation-version={DATA_MAP_RELATION_EXPLANATION_VERSION}
      data-default-collapsed="true"
      data-no-phase-6-2="No Phase 6.2 editing"
      data-proposal-write="false"
      data-direct-active-memory-writeback="false"
      data-raw-private-data-included="false"
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">数据导图 / 框架关系 / 行动入口</p>
          <h2>把当前数据切片整理成来源、画像、项目决策和下一步行动的框架导图</h2>
        </div>
        <span>{display.visibleNodeCount} 个可见节点 / {display.edgeCount} 条框架连接</span>
      </div>
      <GraphUsageStrip
        items={[
          { label: "读法", value: "从左到右" },
          { label: "框架", value: "来源 → 画像 → 项目 → 行动" },
          { label: "点击关系", value: "解释为什么连接" },
        ]}
      />
      <div className="data-map-layer-strip" aria-label="Stage 6 Phase 6.1 四层结构">
        {DATA_MAP_STRUCTURE_LAYERS.map((layer) => (
          <span key={layer.id} data-data-map-layer={layer.id}>
            <b>{layer.label}</b>
            <em>{layer.nodeTypes.join(" / ")}</em>
          </span>
        ))}
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <svg className="data-guide-canvas" viewBox="0 0 1000 620" role="img" aria-label="数据导图框架">
        <defs>
          <filter id="dataGuideGlow">
            <feGaussianBlur stdDeviation="2.2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <marker id="dataGuideArrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="4">
            <path d="M0,0 L8,4 L0,8 Z" fill="rgba(244, 241, 232, 0.42)" />
          </marker>
        </defs>
        <path className="data-guide-flow" d="M78 76 C260 46 420 46 594 76 S824 108 930 78" />
        {display.frames.map((frame) => (
          <g
            className="data-guide-frame"
            key={frame.id}
            data-data-map-layer={frame.structureLayerId}
            data-node-types={frame.nodeTypes.join(",")}
            data-fields={frame.fields.join(",")}
            data-interaction={frame.interaction}
            data-detail-entry={frame.detailEntry}
          >
            <rect x={frame.x} y={frame.y} width={frame.w} height={frame.h} rx="14" fill={frame.color} opacity="0.035" />
            <rect x={frame.x} y={frame.y} width={frame.w} height={frame.h} rx="14" fill="none" stroke={frame.color} opacity="0.34" />
            <text x={frame.x + 18} y={frame.y + 30} className="data-guide-frame-title">{frame.title}</text>
            <text x={frame.x + 18} y={frame.y + 52} className="data-guide-frame-subtitle">{frame.subtitle}</text>
            <text x={frame.x + frame.w - 18} y={frame.y + 30} textAnchor="end" className="data-guide-frame-count">{frame.count}</text>
          </g>
        ))}
        <g className="data-guide-links">
          {display.edges.map((edge) => {
            const selected = edge.id === selectedDataMapRelationId;
            return (
              <g key={edge.id}>
                <path
                  className={selected ? "data-guide-link selected" : "data-guide-link"}
                  d={edge.path}
                  stroke={edge.color}
                  strokeWidth={edge.strokeWidth}
                />
                <path
                  className="data-guide-relation-hitbox"
                  d={edge.path}
                  role="button"
                  tabIndex={0}
                  aria-label={`关系解释：${edge.explanation.sourceLabel} 到 ${edge.explanation.targetLabel}`}
                  data-data-map-relation-explanation={DATA_MAP_RELATION_EXPLANATION_VERSION}
                  data-selected={selected ? "true" : "false"}
                  data-relation-source={edge.explanation.source}
                  data-relation-strength={edge.explanation.strength}
                  data-relation-evidence={edge.explanation.evidence}
                  data-relation-time={edge.explanation.time}
                  onClick={() => setSelectedDataMapRelationId(edge.id)}
                  onKeyDown={(event) => {
                    if (isActivationKey(event)) setSelectedDataMapRelationId(edge.id);
                  }}
                >
                  <title>{edge.explanation.reason}</title>
                </path>
              </g>
            );
          })}
        </g>
        {display.nodes.map((item) => (
          <DataGuideSvgNode
            key={item.node.id}
            item={item}
            selected={item.node.id === selectedNode?.id}
            onSelectNode={onSelectNode}
          />
        ))}
      </svg>
      <div className="map-legend">
        <LegendItem color="#8fd3ff" label="数据源与主题" />
        <LegendItem color="#7ee8d4" label="个人画像与偏好" />
        <LegendItem color="#f48fb1" label="项目、决策、规则" />
        <LegendItem color="#94a3b8" label="行动、机会、待整理" />
      </div>
      <DataMapRelationPanel relation={selectedRelation} />
      <DataMapNodeDetailPanel node={selectedNode} edges={edges} parentSnapshotId={parentSnapshotId} />
    </div>
  );
}



export function DataMapRelationPanel({ relation }: { relation: DataGuideEdge | null }) {
  const explanation = relation?.explanation;
  return (
    <section
      className={relation ? "data-map-relation-panel active" : "data-map-relation-panel"}
      aria-label="关系解释"
      data-selected-relation-id={relation?.id ?? ""}
      data-relation-source={explanation?.source ?? "默认折叠"}
      data-relation-strength={explanation?.strength ?? "默认折叠"}
      data-relation-evidence={explanation?.evidence ?? "默认折叠"}
      data-relation-time={explanation?.time ?? "默认折叠"}
    >
      <div className="panel-title-row">
        <h2>关系解释</h2>
        <span>为什么连接 / source / strength / evidence / time</span>
      </div>
      {explanation ? (
        <>
          <p className="data-map-relation-reason">{explanation.reason}</p>
          <div className="data-map-relation-grid">
            <span>
              <b>来源</b>
              <em>{explanation.source}</em>
            </span>
            <span>
              <b>强度</b>
              <em>{explanation.strength}</em>
            </span>
            <span>
              <b>证据</b>
              <em>{explanation.evidence}</em>
            </span>
            <span>
              <b>时间</b>
              <em>{explanation.time}</em>
            </span>
          </div>
        </>
      ) : (
        <p className="data-map-relation-reason">默认折叠。点击任意关系线查看为什么连接、来源、强度、证据和时间。</p>
      )}
      <p className="data-map-relation-safe-flags">
        No Phase 6.2 editing · proposalWrite: false · directActiveMemoryWriteback: false · rawPrivateDataIncluded: false
      </p>
    </section>
  );
}



export function DataMapNodeDetailPanel({
  node,
  edges,
  parentSnapshotId,
}: {
  node: AtlasNode | null;
  edges: AtlasEdge[];
  parentSnapshotId: string;
}) {
  const detail = useMemo(() => buildDataMapNodeDetail(node, edges), [edges, node]);
  return (
    <section
      className={node ? "data-map-node-detail-panel active" : "data-map-node-detail-panel"}
      aria-label="数据导图详情面板"
      data-data-map-detail-panel={DATA_MAP_DETAIL_PANEL_VERSION}
      data-selected-node-id={node?.id ?? ""}
      data-node-kind={node?.kind ?? ""}
      data-asset={detail.asset}
      data-theme={detail.theme}
      data-suggested-action={detail.suggestedAction}
      data-importance={detail.importance}
      data-priority={detail.priority}
      data-evidence-count={detail.evidenceRefs.length}
    >
      <div className="panel-title-row">
        <h2>数据导图详情面板</h2>
        <span>{DATA_MAP_DETAIL_PANEL_VERSION}</span>
      </div>
      {node ? (
        <>
          <div className="data-map-node-detail-heading">
            <span>{translateKind(node.kind)} / {detail.layerLabel}</span>
            <h3>{humanNodeDisplayTitle(node)}</h3>
            <p>{detail.summary}</p>
          </div>
          <dl className="data-map-node-detail-grid">
            <div><dt>资产</dt><dd>{detail.asset}</dd></div>
            <div><dt>主题</dt><dd>{detail.theme}</dd></div>
            <div><dt>建议动作</dt><dd>{detail.suggestedAction}</dd></div>
            <div><dt>重要性</dt><dd>{detail.importance}</dd></div>
            <div><dt>优先级</dt><dd>{detail.priority}</dd></div>
            <div><dt>状态</dt><dd>{detail.status}</dd></div>
          </dl>
          <section className="data-map-node-detail-section" aria-label="证据摘要">
            <span>证据</span>
            <ul className="data-map-node-evidence-list">
              {detail.evidenceRefs.map((ref) => (
                <li key={ref}>{ref}</li>
              ))}
            </ul>
          </section>
          <div className="data-map-detail-safety-strip" aria-label="Data Map Phase 6.2 safety">
            <span>仅生成提案</span>
            <span>不直接写长期记忆</span>
            <span>不执行 Stage 6 review</span>
          </div>
          <div
            className="data-map-proposal-entry"
            data-data-map-proposal-entry={DATA_MAP_PROPOSAL_ENTRY_VERSION}
            data-proposal-mode="proposal_only"
            data-proposal-only="true"
            data-active-memory-mutation="false"
            data-direct-active-memory-writeback="false"
            data-source-surface="data_guide_detail_panel"
          >
            <div className="panel-title-row">
              <h3>数据导图 proposal 入口</h3>
              <span>{DATA_MAP_PROPOSAL_ENTRY_VERSION}</span>
            </div>
            <ProposalEditor
              node={node}
              parentSnapshotId={parentSnapshotId}
              sourceSurface="data_guide_detail_panel"
            />
          </div>
        </>
      ) : (
        <p className="data-map-node-detail-empty">点击数据导图节点查看资产、主题、建议动作、重要性和优先级；编辑入口只导出 proposal。</p>
      )}
    </section>
  );
}
