import type { MemoryAtlas } from "../../types";

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
