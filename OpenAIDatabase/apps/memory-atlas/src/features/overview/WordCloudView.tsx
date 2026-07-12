import { useMemo } from "react";
import type { AtlasNode } from "../../types";
import { DeltaStats } from "../../shared/atlas/contracts";
import { buildSemanticInsights, selectRepresentativeNode, semanticColor, semanticHeatStyle, wordCloudStyle } from "../../shared/atlas/semanticHuman";
import { isActivationKey, stableUnit, truncate } from "../../shared/atlas/utils";
import { DeltaStrip } from "../../shared/ui/primitives";



export function WordCloudView({
  nodes,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const semantic = useMemo(() => buildSemanticInsights(nodes), [nodes]);
  const maxTopicCount = Math.max(1, ...semantic.topics.map((topic) => topic.count));
  const maxWordScore = Math.max(1, ...semantic.wordCloud.map((item) => item.score));

  function jumpToBestNode(candidates: AtlasNode[]) {
    const target = selectRepresentativeNode(candidates);
    if (target) onSelectNode(target);
  }

  return (
    <div className="visual-workspace semantic-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">词云 / 语义热力 / 主题气泡</p>
          <h2>把当前筛选切片转成可点击的主题密度、关键词和机会信号</h2>
        </div>
        <span>{nodes.length.toLocaleString()} 条记忆 / {semantic.topics.length.toLocaleString()} 个主题</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="semantic-dashboard" aria-label="词云洞察">
        <section className="semantic-panel semantic-heatmap" aria-label="主题层级热力图">
          <div className="panel-title-row">
            <h3>主题 x 层级 Heatmap</h3>
            <span>{semantic.tiers.join(" / ")}</span>
          </div>
          <div
            className="semantic-matrix"
            style={{ gridTemplateColumns: `minmax(76px, 1.1fr) repeat(${semantic.tiers.length}, minmax(42px, 0.7fr))` }}
          >
            <span className="semantic-axis-corner" aria-hidden="true" />
            {semantic.tiers.map((tier) => (
              <strong className="semantic-axis-label" key={tier}>{tier}</strong>
            ))}
            {semantic.matrixRows.map((topic) => (
              <div className="semantic-row" key={topic}>
                <b title={topic}>{topic}</b>
                {semantic.tiers.map((tier) => {
                  const cell = semantic.matrix.get(`${topic}::${tier}`) ?? { topic, tier, count: 0, nodes: [] };
                  return (
                    <button
                      aria-label={`${topic} / ${tier} / ${cell.count} 条`}
                      className="semantic-heat-cell"
                      disabled={!cell.nodes.length}
                      key={`${topic}-${tier}`}
                      onClick={() => jumpToBestNode(cell.nodes)}
                      style={semanticHeatStyle(cell.count, maxTopicCount)}
                      title={`${topic} · ${tier} · ${cell.count} 条`}
                      type="button"
                    >
                      <span>{cell.count}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </section>

        <section className="semantic-panel semantic-bubbles" aria-label="主题气泡图">
          <div className="panel-title-row">
            <h3>Bubble Chart</h3>
            <span>横轴 ROI / 纵轴近期增量</span>
          </div>
          <svg className="semantic-bubble-canvas" viewBox="0 0 520 330" role="img" aria-label="主题 ROI 与近期增量气泡图">
            <line x1="48" x2="494" y1="286" y2="286" />
            <line x1="48" x2="48" y1="28" y2="286" />
            <text x="494" y="312" textAnchor="end">ROI</text>
            <text x="12" y="38" transform="rotate(-90 12 38)">近期</text>
            {semantic.topics.slice(0, 18).map((topic, index) => {
              const radius = 10 + Math.sqrt(topic.count / maxTopicCount) * 28;
              const x = 62 + Math.min(1, Math.max(0, topic.roiScore)) * 406;
              const y = 270 - Math.min(1, topic.recentCount / Math.max(1, deltaStats.recentCount || topic.count)) * 218 - stableUnit(topic.label, "bubble-y") * 18;
              const color = semanticColor(index);
              return (
                <g
                  className="semantic-bubble"
                  key={topic.label}
                  role="button"
                  tabIndex={0}
                  onClick={() => jumpToBestNode(topic.nodes)}
                  onKeyDown={(event) => {
                    if (isActivationKey(event)) jumpToBestNode(topic.nodes);
                  }}
                >
                  <title>{`${topic.label} · ${topic.count} 条 · ROI ${topic.roiScore.toFixed(2)} · 近期 ${topic.recentCount}`}</title>
                  <circle cx={x} cy={y} r={radius} fill={color} />
                  <text x={x} y={y + 3} textAnchor="middle">{truncate(topic.label, radius > 28 ? 8 : 5)}</text>
                </g>
              );
            })}
          </svg>
        </section>

        <section className="semantic-panel semantic-cloud" aria-label="词云">
          <div className="panel-title-row">
            <h3>Word Cloud</h3>
            <span>点击词条跳转代表记忆</span>
          </div>
          <div className="word-cloud-field">
            {semantic.wordCloud.map((item) => (
              <button
                className="word-cloud-token"
                key={item.label}
                onClick={() => jumpToBestNode(item.nodes)}
                style={wordCloudStyle(item, maxWordScore)}
                title={`${item.label} · ${item.count} 条`}
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
