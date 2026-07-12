import { X } from "lucide-react";
import type { TopicClassificationDetail } from "../shared/atlas/contracts";

export type { TopicClassificationDetail } from "../shared/atlas/contracts";

interface ThemeDetailPanelProps {
  topic: TopicClassificationDetail | null;
  onClose: () => void;
  onOpenTarget: (topic: TopicClassificationDetail) => void;
}

export function ThemeDetailPanel({ topic, onClose, onOpenTarget }: ThemeDetailPanelProps) {
  if (!topic) return null;

  return (
    <aside
      aria-label="主题分类明细"
      className="theme-detail-panel"
      data-active-memory-mutation="false"
      data-proposal-only="true"
      data-theme-detail-panel={topic.topic_id}
    >
      <div className="theme-detail-panel-heading">
        <div>
          <span>{topic.topic_state} / {topic.parent_topic}</span>
          <h4>{topic.topic_label}</h4>
        </div>
        <button aria-label="关闭主题分类明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{topic.matched_reason}</p>

      <dl className="theme-detail-panel-grid">
        <div><dt>category</dt><dd>{topic.category}</dd></div>
        <div><dt>topic_strength</dt><dd>{formatTopicScore(topic.topic_strength)}</dd></div>
        <div><dt>trend</dt><dd>{topic.trend}</dd></div>
        <div><dt>roi_score</dt><dd>{formatTopicScore(topic.roi_score)}</dd></div>
        <div><dt>conflict_score</dt><dd>{formatTopicScore(topic.conflict_score)}</dd></div>
        <div><dt>confidence</dt><dd>{formatTopicScore(topic.confidence)}</dd></div>
        <div><dt>record_count</dt><dd>{topic.record_count.toLocaleString()}</dd></div>
        <div><dt>recent_count</dt><dd>{topic.recent_count.toLocaleString()}</dd></div>
      </dl>

      <section className="theme-detail-section" aria-label="关联资产与行动">
        <span>linked_asset_ids / linked_action_ids</span>
        <p>{joinOrEmpty(topic.linked_asset_ids)} / {joinOrEmpty(topic.linked_action_ids)}</p>
      </section>

      <section className="theme-detail-section" aria-label="跨板块交接">
        <span>Starfield handoff / River handoff</span>
        <p>{topic.starfield_handoff} / {topic.river_handoff}</p>
      </section>

      <section className="theme-detail-section" aria-label="代表记录">
        <span>representative_record_ids</span>
        <p>{joinOrEmpty(topic.representative_record_ids)}</p>
      </section>

      <section className="theme-detail-section" aria-label="证据引用">
        <span>evidence_refs</span>
        <ul className="theme-detail-evidence-list">
          {topic.evidence_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>

      <div className="theme-detail-safety-strip" aria-label="proposal-only topic safety contract">
        <span>{topic.proposal_hint}</span>
        <span>{topic.rollback_hint}</span>
        <span>proposal_only: {String(topic.proposal_only)}</span>
      </div>

      <button className="theme-detail-open-target" onClick={() => onOpenTarget(topic)} type="button">
        打开主题上下文
      </button>
    </aside>
  );
}

function formatTopicScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "none";
}
