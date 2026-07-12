import { Search } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { getMemoryNodes, normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { INSPECTOR_EXPLANATION_LAYER_VERSION, uiCopy } from "../../shared/atlas/constants";
import { ContributionPeriodDetail, InspectorExplanation } from "../../shared/atlas/contracts";
import { periodImpactLine, periodMeaningLine, scaleLabel } from "../../shared/atlas/contributionModels";
import { buildInspectorExplanation } from "../../shared/atlas/inspectorWriteback";
import { buildHumanNodeSummary, humanCategoryLabel, humanNodeTitle, humanizeStatement } from "../../shared/atlas/semanticHuman";
import { buildDeltaStats } from "../../shared/atlas/sourceSlice";
import { formatScore, formatSigned, translateKind } from "../../shared/atlas/utils";
import { HumanOverviewPanel } from "../../shared/ui/primitives";



export function NodeInspector({
  atlas,
  node,
  edgeCount,
  sharedState,
  writebackPanel,
}: {
  atlas: MemoryAtlas;
  node: AtlasNode | null;
  edgeCount: number;
  sharedState: SharedAtlasState;
  writebackPanel: ReactNode;
}) {
  const [debugOpen, setDebugOpen] = useState(false);
  const memoryNodes = useMemo(() => getMemoryNodes(atlas), [atlas]);
  const overviewNodes = memoryNodes.length ? memoryNodes : atlas.nodes;
  useEffect(() => {
    setDebugOpen(false);
  }, [node?.id]);
  if (!node) {
    return (
      <aside
        className="inspector"
        data-shared-state={sharedState.schema_version}
        data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
        data-shared-focus-node=""
        data-shared-cluster=""
      >
        <h2>{uiCopy.inspector.emptyTitle}</h2>
        <p>{uiCopy.inspector.emptyDescription}</p>
        <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      </aside>
    );
  }
  const humanNode = buildHumanNodeSummary(node, edgeCount);
  const explanation = buildInspectorExplanation(node, edgeCount, sharedState);
  return (
    <aside
      className="inspector"
      data-shared-state={sharedState.schema_version}
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-shared-focus-node={sharedState.focus.inspector.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.inspector.clusterId ?? ""}
      data-shared-record={sharedState.focus.inspector.recordId ?? ""}
      data-debug-lite={debugOpen ? "open" : "closed"}
      data-default-raw-summary="hidden"
    >
      <HumanOverviewPanel nodes={overviewNodes} deltaStats={buildDeltaStats(atlas, memoryNodes)} compact />
      <p className="eyebrow">{humanNode.scope}</p>
      <h2>{humanNode.title}</h2>
      <p className="human-node-subtitle">{humanNode.subtitle}</p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>{uiCopy.inspector.meaningTitle}</strong>
          <ul>
            {humanNode.meaning.map((item, index) => (
              <li key={`meaning-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.impactTitle}</strong>
          <p>{humanNode.impact}</p>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.futureUseTitle}</strong>
          <ul>
            {humanNode.futureUse.map((item, index) => (
              <li key={`future-${index}-${item}`}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="human-node-section">
          <strong>{uiCopy.inspector.relatedTopicsTitle}</strong>
          <div className="human-node-topics">
            {humanNode.topics.map((topic, index) => (
              <span key={`topic-${index}-${topic}`}>{topic}</span>
            ))}
          </div>
        </div>
      </section>
      <InspectorExplanationPanel explanation={explanation} />
      <dl className="human-node-status">
        {humanNode.statusRows.map((row, index) => (
          <div key={`status-${index}-${row.label}`}><dt>{row.label}</dt><dd>{row.value}</dd></div>
        ))}
      </dl>
      <button
        className="inspector-debug-toggle"
        type="button"
        aria-expanded={debugOpen}
        aria-controls="inspector-debug-panel"
        aria-label="显示或隐藏高级详情机器字段"
        data-s10-p3-machine-fields="collapsed-by-default"
        data-s10-p3-advanced-details-entry="inspector"
        onClick={() => setDebugOpen((open) => !open)}
      >
        <Search size={15} />
        {debugOpen ? uiCopy.inspector.debugHide : uiCopy.inspector.debugShow}
      </button>
      {debugOpen ? (
        <section
          id="inspector-debug-panel"
          className="agent-structured-fields inspector-debug-panel"
          data-debug-panel="true"
          data-s10-p3-machine-fields="advanced-details-open"
        >
          <div className="panel-title-row">
            <h3>{uiCopy.inspector.debugTitle}</h3>
            <span>{uiCopy.inspector.debugDefaultHidden}</span>
          </div>
          <div className="agent-field-grid">
            <section>
              <strong>Memory（给 ChatGPT / Codex Personalization）</strong>
              <p>{humanNode.agentMemory}</p>
            </section>
            <section>
              <strong>Meta Data（给 ChatGPT / Codex Agents.md）</strong>
              <p>{humanNode.agentMeta}</p>
            </section>
          </div>
          {node.statement ? (
            <div className="raw-summary-inline">
              <strong>{uiCopy.inspector.lowSensitivitySummary}</strong>
              <p>{node.statement}</p>
            </div>
          ) : null}
          <dl>
            <div><dt>类型</dt><dd>{translateKind(node.kind)}</dd></div>
            <div><dt>连接数</dt><dd>{edgeCount.toLocaleString()}</dd></div>
            <div><dt>日期</dt><dd>{node.date || "未知"}</dd></div>
            <div><dt>分类</dt><dd>{node.category || "未知"}</dd></div>
            <div><dt>重要性</dt><dd>{node.importance || "未知"}</dd></div>
            <div><dt>有效期</dt><dd>{node.validity || "未知"}</dd></div>
            <div><dt>置信度</dt><dd>{node.confidence || "未知"}</dd></div>
            <div><dt>ROI</dt><dd>{formatScore(node.metrics?.roi?.leverage_score)}</dd></div>
          </dl>
        </section>
      ) : null}
      {writebackPanel}
    </aside>
  );
}



export function InspectorExplanationPanel({ explanation }: { explanation: InspectorExplanation }) {
  return (
    <section
      className="inspector-explanation-panel"
      data-stage9-inspector-explanation={INSPECTOR_EXPLANATION_LAYER_VERSION}
      data-inspector-layer-marker="inspector_explanation_layer"
      data-raw-display="false"
      aria-label="解释面板"
    >
      <div className="panel-title-row">
        <h3>{uiCopy.inspector.explanationTitle}</h3>
        <span>{uiCopy.inspector.explanationMeta}</span>
      </div>
      <p>{explanation.summary}</p>
      <div className="inspector-formula-grid" aria-label="公式与参数">
        {explanation.formulas.map((row) => (
          <article key={row.label} className="inspector-formula-card">
            <span>{row.label}</span>
            <strong>{row.value}</strong>
            <code>{row.formula}</code>
            <small>{row.parameters}</small>
          </article>
        ))}
      </div>
      <dl className="inspector-evidence-grid" aria-label="脱敏证据摘要">
        {explanation.evidence.map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        ))}
      </dl>
      <ul className="inspector-safety-list" aria-label="安全边界">
        {explanation.safetyNotes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </section>
  );
}



export function ContributionPeriodInspector({
  detail,
  onSelectNode,
}: {
  detail: ContributionPeriodDetail;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const bucket = detail.bucket;
  const relatedNodes = detail.relatedNodes.slice(0, 18);
  const periodLabel = scaleLabel(detail.scale);
  return (
    <aside className="inspector contribution-period-inspector">
      <p className="eyebrow">时间段详情 · {periodLabel}</p>
      <h2>{bucket.label}</h2>
      <p>
        这个对象来自贡献网格，重点是看某个时间单位里的交互强度、记忆增量、决策密度和环比变化。
      </p>
      <section className="human-node-card">
        <div className="human-node-section">
          <strong>这段时间说明了什么</strong>
          <ul>
            <li>{periodMeaningLine(bucket, detail.scale)}</li>
            <li>当前筛选命中 {bucket.filteredMemoryCount.toLocaleString()} 条记忆，其中决策 {bucket.filteredDecisionCount.toLocaleString()} 条，核心画像 {bucket.filteredCoreCount.toLocaleString()} 条。</li>
            <li>全局交互包含 {bucket.conversationCount.toLocaleString()} 个对话、{bucket.messageCount.toLocaleString()} 条消息。</li>
          </ul>
        </div>
        <div className="human-node-section">
          <strong>为什么重要</strong>
          <p>{periodImpactLine(bucket, detail.relatedNodes.length)}</p>
        </div>
        <div className="human-node-section">
          <strong>建议怎么用</strong>
          <ul>
            <li>把这个时间段和相邻周期对比，判断是一次性高峰、持续投入，还是记忆整理遗漏。</li>
            <li>优先点开下方相关记忆，查看具体话题、决策和需要继续做的事情。</li>
          </ul>
        </div>
      </section>
      <dl className="human-node-status">
        <div><dt>活动得分</dt><dd>{bucket.activityScore.toLocaleString()}</dd></div>
        <div><dt>环比变化</dt><dd>{formatSigned(bucket.delta ?? 0)} / {bucket.previousLabel ?? "上一周期"}</dd></div>
        <div><dt>全局消息</dt><dd>{bucket.messageCount.toLocaleString()}</dd></div>
        <div><dt>工具调用</dt><dd>{(bucket.toolCallCount ?? 0).toLocaleString()}</dd></div>
        <div><dt>筛选记忆</dt><dd>{bucket.filteredMemoryCount.toLocaleString()}</dd></div>
        <div><dt>核心画像</dt><dd>{bucket.filteredCoreCount.toLocaleString()}</dd></div>
        <div><dt>决策</dt><dd>{bucket.filteredDecisionCount.toLocaleString()}</dd></div>
        <div><dt>错误/中断</dt><dd>{(bucket.errorEventCount ?? 0).toLocaleString()} / {(bucket.abortCount ?? 0).toLocaleString()}</dd></div>
      </dl>
      <section className="period-related-list" aria-label="这个时间段对应的记忆">
        <div className="panel-title-row">
          <h3>对应记忆</h3>
          <span>{detail.relatedNodes.length.toLocaleString()} 条</span>
        </div>
        {relatedNodes.length ? (
          relatedNodes.map((node) => (
            <button key={node.id} onClick={() => onSelectNode(node)} type="button">
              <strong>{humanNodeTitle(node)}</strong>
              <span>{humanizeStatement(node.statement) || node.label}</span>
              <small>{normalizeMemoryTier(node.memory_tier)} / {humanCategoryLabel(node.category)} / {node.date || "未知日期"}</small>
            </button>
          ))
        ) : (
          <p>当前筛选下没有具体记忆节点；这个格子主要来自全局交互统计。切换筛选条件或年份后可继续查看。</p>
        )}
      </section>
    </aside>
  );
}
