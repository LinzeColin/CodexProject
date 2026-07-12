import { Download, GitBranch, RotateCcw, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { ErrorState } from "../../components/ErrorState";
import { ProposalEditor } from "../../components/ProposalEditor";
import { uiCopy } from "../../shared/atlas/constants";
import { WritebackAction, WritebackProposal } from "../../shared/atlas/contracts";
import { buildProposalDiff, buildWritebackProposalDraft, compactTimestamp, downloadJson, loadWritebackProposals, saveWritebackProposals, stableHash } from "../../shared/atlas/inspectorWriteback";
import { writebackActionLabels } from "../../shared/atlas/runtimeConfig";



export function WritebackProposalPanel({ atlas, node }: { atlas: MemoryAtlas; node: AtlasNode }) {
  const [action, setAction] = useState<WritebackAction>("update_statement");
  const [draftText, setDraftText] = useState(node.statement ?? node.label);
  const [reason, setReason] = useState("");
  const [proposals, setProposals] = useState<WritebackProposal[]>(() => loadWritebackProposals());

  const policy = atlas.source_contract.writeback_policy;
  const editable = policy.frontend_can_request_writeback && policy.writeback_must_use_proposals && !policy.direct_frontend_mutation_of_active_memory;
  const nodeProposals = useMemo(
    () => proposals.filter((proposal) => proposal.target_ref.node_id === node.id),
    [node.id, proposals],
  );
  const latest = nodeProposals[nodeProposals.length - 1] ?? null;
  const previous = nodeProposals[nodeProposals.length - 2] ?? null;
  const baseText = node.statement ?? node.label;
  const draftDiff = useMemo(() => buildProposalDiff(baseText, draftText), [baseText, draftText]);
  const versionChain = useMemo(() => [...nodeProposals].reverse().slice(0, 6), [nodeProposals]);
  const proposalPreview = useMemo(
    () => buildWritebackProposalDraft({
      policy,
      node,
      action,
      proposedText: draftText,
      reason,
      baseText,
      latest,
      proposalCount: nodeProposals.length,
      now: new Date().toISOString(),
      proposalIdPrefix: "atlas_preview",
    }),
    [action, baseText, draftText, latest, node, nodeProposals.length, policy, reason],
  );
  const proposalJsonPreview = useMemo(() => JSON.stringify(proposalPreview, null, 2), [proposalPreview]);

  useEffect(() => {
    setDraftText(node.statement ?? node.label);
    setReason("");
    setAction("update_statement");
  }, [node.id, node.label, node.statement]);

  function persist(next: WritebackProposal[]) {
    setProposals(next);
    saveWritebackProposals(next);
  }

  function saveProposal() {
    const text = draftText.trim();
    if (!editable || !text) return;
    const now = new Date().toISOString();
    const proposal = buildWritebackProposalDraft({
      policy,
      node,
      action,
      proposedText: text,
      reason,
      baseText,
      latest,
      proposalCount: nodeProposals.length,
      now,
      proposalIdPrefix: "atlas",
    });
    persist([...proposals, proposal]);
  }

  function createRollbackProposal() {
    if (!editable || !latest) return;
    const target = previous ?? latest;
    const now = new Date().toISOString();
    const rollbackText = target.payload.proposed_text || baseText;
    const rollbackReason = `回滚到版本 ${target.version.revision}：${target.proposal_id}`;
    const proposal: WritebackProposal = {
      schema_version: policy.proposal_schema_version || "memory_change_proposal.v1",
      proposal_id: `atlas_${compactTimestamp(now)}_${stableHash(`${node.id}:rollback:${latest.proposal_id}:${nodeProposals.length + 1}`)}`,
      created_at: now,
      status: "draft_pending_agent_apply",
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
        source_file: node.source_label ?? node.data_source ?? "visual_snapshot",
        base_date: node.date ?? "",
      },
      action: "rollback_to_version",
      payload: {
        proposed_text: rollbackText,
        reason: rollbackReason,
        current_tier: normalizeMemoryTier(node.memory_tier),
        current_category: node.category ?? "",
      },
      diff: buildProposalDiff(latest.payload.proposed_text || baseText, rollbackText),
      version: {
        revision: (latest.version.revision ?? 0) + 1,
        parent_proposal_id: latest.proposal_id,
        rollback_unit: policy.rollback_unit || "per_memory_version",
        supersedes_proposal_id: latest.proposal_id,
      },
      rollback: {
        rollback_to_proposal_id: target.proposal_id,
        rollback_to_revision: target.version.revision,
        rollback_text: rollbackText,
        rollback_reason: rollbackReason,
      },
      review: {
        human_summary: `建议把当前写回提案回滚到版本 ${target.version.revision}。`,
        agent_next_step: "重新读取当前主动记忆库，核对冲突与敏感字段后，写入提案历史，并用 git commit 建立回滚点。",
        conflict_policy: "若当前库已存在更新版本，先生成冲突报告，不可直接覆盖。",
        apply_status: "proposal_only_pending_agent_apply",
      },
      safety: {
        direct_frontend_mutation_of_active_memory: false,
        requires_conflict_check: true,
        requires_agent_or_human_apply: true,
        forbidden_payload: policy.frontend_payload_contract?.forbidden_payload ?? [
          "plaintext secrets",
          "raw conversation text",
          "record hashes",
          "local absolute paths",
        ],
      },
    };
    persist([...proposals, proposal]);
  }

  function rollbackDraft() {
    if (!previous) return;
    setAction(previous.action);
    setDraftText(previous.payload.proposed_text);
    setReason(`回滚到 ${previous.proposal_id}`);
  }

  function exportLatest() {
    if (!latest) return;
    downloadJson(`${latest.proposal_id}.json`, latest);
  }

  function exportProposalHistory() {
    if (!nodeProposals.length) return;
    downloadJson(`memory_atlas_writeback_history_${node.id}.json`, {
      schema_version: "memory_atlas_writeback_history.v1",
      exported_at: new Date().toISOString(),
      target_ref: {
        node_id: node.id,
        memory_id: node.memory_id ?? node.id,
        label: node.label,
      },
      proposals: nodeProposals,
    });
  }

  return (
    <section
      className="writeback-panel"
      aria-label="长期记忆写回提案"
      data-proposal-only="true"
      data-active-memory-mutation="false"
      data-proposal-schema={policy.proposal_schema_version || "memory_change_proposal.v1"}
    >
      <div className="panel-title-row">
        <h3>{uiCopy.proposal.panelTitle}</h3>
        <span>{nodeProposals.length} {uiCopy.proposal.versionSuffix}</span>
      </div>
      <p>{uiCopy.proposal.description}</p>
      <div className="writeback-safety-strip" aria-label="proposal-only safety contract">
        <span>{uiCopy.proposal.safetyProposalOnly}</span>
        <span>{uiCopy.proposal.safetyNoDirectMutation}</span>
        <span>{uiCopy.proposal.safetyNeedsApply}</span>
      </div>
      <ProposalEditor
        node={node}
        parentSnapshotId={atlas.overview.generated_at || atlas.schema_version}
        sourceSurface="inspector_writeback_panel"
      />
      {!editable ? (
        <ErrorState
          compact
          className="proposal-unavailable-state"
          dataState="proposal-not-writable"
          description={uiCopy.states.proposalUnavailableDescription}
          details={uiCopy.states.proposalUnavailableAction}
          title={uiCopy.states.proposalUnavailableTitle}
        />
      ) : null}
      <div className="writeback-diff-grid" aria-label="当前草稿差异">
        <div><span>{uiCopy.proposal.diffLength}</span><strong>{draftDiff.length_delta > 0 ? "+" : ""}{draftDiff.length_delta}</strong></div>
        <div><span>{uiCopy.proposal.diffSegments}</span><strong>{draftDiff.changed_segments}</strong></div>
        <div><span>{uiCopy.proposal.rollbackUnit}</span><strong>{policy.rollback_unit || "per_memory_version"}</strong></div>
      </div>
      <label>
        {uiCopy.proposal.actionLabel}
        <select value={action} onChange={(event) => setAction(event.target.value as WritebackAction)} disabled={!editable}>
          {(Object.keys(writebackActionLabels) as WritebackAction[]).map((key) => (
            <option key={key} value={key}>{writebackActionLabels[key]}</option>
          ))}
        </select>
      </label>
      <label>
        {uiCopy.proposal.draftLabel}
        <textarea
          value={draftText}
          onChange={(event) => setDraftText(event.target.value)}
          disabled={!editable}
          rows={5}
        />
      </label>
      <label>
        {uiCopy.proposal.reasonLabel}
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          disabled={!editable}
          rows={3}
          placeholder={uiCopy.proposal.reasonPlaceholder}
        />
      </label>
      <div className="writeback-actions">
        <button type="button" onClick={saveProposal} disabled={!editable || !draftText.trim()}>
          <Save size={15} />
          {uiCopy.proposal.buttons.save}
        </button>
        <button type="button" onClick={exportLatest} disabled={!latest}>
          <Download size={15} />
          {uiCopy.proposal.buttons.exportLatest}
        </button>
        <button type="button" onClick={exportProposalHistory} disabled={!nodeProposals.length}>
          <GitBranch size={15} />
          {uiCopy.proposal.buttons.exportHistory}
        </button>
        <button type="button" onClick={rollbackDraft} disabled={!previous}>
          <RotateCcw size={15} />
          {uiCopy.proposal.buttons.loadPrevious}
        </button>
        <button type="button" onClick={createRollbackProposal} disabled={!latest}>
          <RotateCcw size={15} />
          {uiCopy.proposal.buttons.createRollback}
        </button>
      </div>
      <details className="writeback-json-preview">
        <summary>
          <GitBranch size={14} />
          {uiCopy.proposal.buttons.jsonPreview}
        </summary>
        <pre>{proposalJsonPreview}</pre>
      </details>
      {versionChain.length ? (
        <div className="writeback-version-chain" aria-label="写回提案版本链">
          {versionChain.map((proposal) => (
            <button key={proposal.proposal_id} onClick={() => {
              setAction(proposal.action);
              setDraftText(proposal.payload.proposed_text);
              setReason(proposal.payload.reason);
            }} type="button">
              <strong>v{proposal.version.revision} · {writebackActionLabels[proposal.action]}</strong>
              <span>{proposal.diff?.summary ?? "旧版本无差异摘要"} · {new Date(proposal.created_at).toLocaleString("zh-CN")}</span>
              <small>{proposal.version.parent_proposal_id ? `parent ${proposal.version.parent_proposal_id}` : "root proposal"}</small>
            </button>
          ))}
        </div>
      ) : null}
      <small>
        {latest
          ? `${uiCopy.proposal.latestVersionPrefix} ${latest.version.revision} · ${new Date(latest.created_at).toLocaleString("zh-CN")} · 待受控代理应用`
          : uiCopy.proposal.emptyVersion}
      </small>
    </section>
  );
}
