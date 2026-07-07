import { GitBranch } from "lucide-react";

export interface ProposalDiffPreviewChange {
  field: "importance" | "priority" | "status" | "theme_override" | "action_state" | "note";
  original_value: string;
  proposed_value: string;
  impact_summary: string;
  rollback_metadata: {
    rollback_field: string;
    rollback_value: string;
    rollback_hint: string;
  };
}

interface ProposalDiffPreviewProps {
  changes: ProposalDiffPreviewChange[];
  exportSchemaVersion: "memory_atlas_proposal_export.v1";
}

export function ProposalDiffPreview({ changes, exportSchemaVersion }: ProposalDiffPreviewProps) {
  const visibleChanges = changes.slice(0, 6);
  return (
    <section
      aria-label="proposal diff preview"
      className="proposal-diff-preview"
      data-proposal-diff-preview={exportSchemaVersion}
      data-proposal-only="true"
    >
      <div className="panel-title-row">
        <h4>Proposal Diff Preview</h4>
        <span>{visibleChanges.length} changes</span>
      </div>

      {visibleChanges.length ? (
        <div className="proposal-diff-grid">
          {visibleChanges.map((change) => (
            <article key={change.field}>
              <div className="proposal-diff-field">
                <strong>{change.field}</strong>
                <span>impact_summary</span>
              </div>
              <dl>
                <div><dt>original_value</dt><dd>{change.original_value || "empty"}</dd></div>
                <div><dt>proposed_value</dt><dd>{change.proposed_value || "empty"}</dd></div>
              </dl>
              <p>{change.impact_summary}</p>
              <div className="proposal-rollback-metadata" aria-label="rollback metadata">
                <GitBranch size={14} />
                <span>
                  rollback_metadata: {change.rollback_metadata.rollback_field} -&gt; {change.rollback_metadata.rollback_value || "empty"}
                </span>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="proposal-diff-empty">当前没有本地调整；选择 importance 或 priority 后会显示原值、新值和影响说明。</p>
      )}

      <div className="proposal-diff-safety" aria-label="proposal apply safety">
        <span>requires_conflict_check: true</span>
        <span>requires_agent_or_human_apply: true</span>
        <span>active memory mutation: false</span>
      </div>
    </section>
  );
}
