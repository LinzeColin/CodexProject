import { X } from "lucide-react";

export interface HomeActionDetail {
  action_id: string;
  title: string;
  action_type: "continue" | "review" | "consolidate" | "explore" | "defer";
  priority: string;
  reason: string;
  roi_score: number;
  effort_cost: "low" | "medium" | "high";
  urgency: "low" | "medium" | "high";
  confidence: number;
  source: string;
  status: "proposed" | "review" | "blocked" | "done_safe";
  evidence_count: number;
  evidence_refs: string[];
  matched_reason: string;
  linked_topic_ids: string[];
  linked_asset_ids: string[];
  next_step: string;
  recommended_time_window: "now" | "today" | "this_week" | "later";
  proposal_hint: "proposal_recommended" | "proposal_not_needed";
  rollback_hint: string;
  proposal_only: true;
}

interface ActionDetailDrawerProps {
  action: HomeActionDetail | null;
  onClose: () => void;
  onOpenTarget: (action: HomeActionDetail) => void;
}

export function ActionDetailDrawer({ action, onClose, onOpenTarget }: ActionDetailDrawerProps) {
  if (!action) return null;

  return (
    <aside
      aria-label="建议动作明细"
      className="action-detail-drawer"
      data-action-detail-drawer={action.action_id}
      data-active-memory-mutation="false"
      data-proposal-only="true"
    >
      <div className="action-detail-drawer-heading">
        <div>
          <span>{action.priority} / {action.action_type}</span>
          <h4>{action.title}</h4>
        </div>
        <button aria-label="关闭建议动作明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{action.reason}</p>

      <dl className="action-detail-drawer-grid">
        <div><dt>roi_score</dt><dd>{formatActionScore(action.roi_score)}</dd></div>
        <div><dt>effort_cost</dt><dd>{action.effort_cost}</dd></div>
        <div><dt>urgency</dt><dd>{action.urgency}</dd></div>
        <div><dt>confidence</dt><dd>{formatActionScore(action.confidence)}</dd></div>
        <div><dt>source</dt><dd>{action.source}</dd></div>
        <div><dt>status</dt><dd>{action.status}</dd></div>
        <div><dt>evidence_count</dt><dd>{action.evidence_count.toLocaleString()}</dd></div>
        <div><dt>recommended_time_window</dt><dd>{action.recommended_time_window}</dd></div>
      </dl>

      <section className="action-detail-section" aria-label="为什么命中">
        <span>matched_reason</span>
        <p>{action.matched_reason}</p>
      </section>

      <section className="action-detail-section" aria-label="下一步">
        <span>next_step</span>
        <p>{action.next_step}</p>
      </section>

      <section className="action-detail-section" aria-label="关联主题与资产">
        <span>linked_topic_ids / linked_asset_ids</span>
        <p>{joinOrEmpty(action.linked_topic_ids)} / {joinOrEmpty(action.linked_asset_ids)}</p>
      </section>

      <section className="action-detail-section" aria-label="证据引用">
        <span>evidence_refs</span>
        <ul className="action-detail-evidence-list">
          {action.evidence_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>

      <div className="action-detail-safety-strip" aria-label="proposal-only safety contract">
        <span>{action.proposal_hint}</span>
        <span>{action.rollback_hint}</span>
        <span>proposal_only: {String(action.proposal_only)}</span>
      </div>

      <button className="action-detail-open-target" onClick={() => onOpenTarget(action)} type="button">
        打开关联视图
      </button>
    </aside>
  );
}

function formatActionScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "none";
}
