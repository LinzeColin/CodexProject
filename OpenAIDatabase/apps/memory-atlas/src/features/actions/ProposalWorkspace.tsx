import { CheckCircle2, FileCheck2, RefreshCw, RotateCcw, ShieldCheck, X } from "lucide-react";
import type { KeyboardEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "../../components/EmptyState";
import { PROPOSAL_WORKFLOW_VERSION, ProposalActionResult, ProposalNarrator, ProposalReviewPayload } from "../../shared/atlas/constants";
import { isProposalActionResult, isRecord } from "../../shared/runtime/operations";



export function ProposalWorkspace({ onClose, review }: { onClose: () => void; review: ProposalReviewPayload }) {
  const initialProposalId = review.proposals.find((proposal) => proposal.apply_ready)?.proposal_id
    ?? review.proposals[0]?.proposal_id
    ?? "";
  const [selectedProposalId, setSelectedProposalId] = useState(initialProposalId);
  const [applyAcknowledged, setApplyAcknowledged] = useState(false);
  const [rollbackAcknowledged, setRollbackAcknowledged] = useState(false);
  const [pendingAction, setPendingAction] = useState<"approve_apply" | "rollback" | null>(null);
  const [actionResult, setActionResult] = useState<ProposalActionResult | null>(null);
  const [actionError, setActionError] = useState("");
  const selectedProposal = useMemo(
    () => review.proposals.find((proposal) => proposal.proposal_id === selectedProposalId) ?? review.proposals[0] ?? null,
    [review.proposals, selectedProposalId],
  );
  const selectedTransaction = useMemo(
    () => review.transactions.find((transaction) => transaction.proposal_id === selectedProposal?.proposal_id) ?? null,
    [review.transactions, selectedProposal?.proposal_id],
  );
  const rollbackCandidate = actionResult?.rollback_available && actionResult.rollback_token
    ? { transactionId: actionResult.transaction_id, rollbackToken: actionResult.rollback_token }
    : selectedTransaction
      ? { transactionId: selectedTransaction.transaction_id, rollbackToken: selectedTransaction.rollback_token }
      : null;

  useEffect(() => {
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape" && pendingAction === null) onClose();
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose, pendingAction]);

  const selectProposal = (proposalId: string) => {
    if (pendingAction) return;
    setSelectedProposalId(proposalId);
    setApplyAcknowledged(false);
    setRollbackAcknowledged(false);
    setActionResult(null);
    setActionError("");
  };

  const postProposalAction = async (body: Record<string, string>): Promise<ProposalActionResult> => {
    const response = await fetch("/__memory_atlas_proposal_action", {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const message = isRecord(payload) && typeof payload.message_zh === "string"
        ? payload.message_zh
        : `本地 proposal 请求失败（HTTP ${response.status}）。`;
      throw new Error(message);
    }
    if (!isProposalActionResult(payload)) {
      throw new Error("本地 proposal 返回格式未通过校验，已停止后续动作。");
    }
    return payload;
  };

  const approveAndApply = async () => {
    if (!selectedProposal?.apply_ready || !selectedProposal.review_token || !applyAcknowledged || pendingAction) return;
    setPendingAction("approve_apply");
    setActionError("");
    setActionResult(null);
    setRollbackAcknowledged(false);
    try {
      const result = await postProposalAction({
        action: "approve_apply",
        proposal_id: selectedProposal.proposal_id,
        review_token: selectedProposal.review_token,
        confirmation: `授权应用 ${selectedProposal.proposal_id}`,
      });
      setActionResult(result);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "本地 proposal apply 未完成。");
    } finally {
      setPendingAction(null);
    }
  };

  const rollback = async () => {
    if (
      !rollbackCandidate
      || !rollbackAcknowledged
      || pendingAction
    ) return;
    setPendingAction("rollback");
    setActionError("");
    try {
      const result = await postProposalAction({
        action: "rollback",
        transaction_id: rollbackCandidate.transactionId,
        rollback_token: rollbackCandidate.rollbackToken,
        confirmation: `确认回滚 ${rollbackCandidate.transactionId}`,
      });
      setActionResult(result);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "本地 proposal rollback 未完成。");
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <div className="proposal-workspace-backdrop" data-r4-proposal-workspace={PROPOSAL_WORKFLOW_VERSION}>
      <section aria-label="待授权提案复核" aria-modal="true" className="proposal-workspace-surface" role="dialog">
        <header className="proposal-workspace-heading">
          <div>
            <p className="eyebrow">授权与回滚</p>
            <h2>待授权提案</h2>
            <span>
              {review.summary.apply_ready_count} 条可应用 · {review.summary.review_only_count} 条仅复核
              {review.summary.interrupted_recovery_count > 0 ? ` · 已自动恢复 ${review.summary.interrupted_recovery_count} 个中断事务` : ""}
              {review.summary.manual_recovery_required_count > 0 ? ` · ${review.summary.manual_recovery_required_count} 个事务需人工回滚` : ""}
            </span>
          </div>
          <button aria-label="关闭提案复核" className="proposal-workspace-close" disabled={pendingAction !== null} onClick={onClose} title="关闭" type="button">
            <X aria-hidden="true" size={18} />
          </button>
        </header>
        <div className="proposal-workspace-body">
          <nav aria-label="提案列表" className="proposal-review-list">
            {review.proposals.map((proposal) => (
              <button
                className={proposal.proposal_id === selectedProposal?.proposal_id ? "proposal-review-list-item active" : "proposal-review-list-item"}
                data-r4-proposal-id={proposal.proposal_id}
                disabled={pendingAction !== null}
                key={proposal.proposal_id}
                onClick={() => selectProposal(proposal.proposal_id)}
                type="button"
              >
                <span className="proposal-review-list-title">
                  {proposal.apply_ready ? <FileCheck2 aria-hidden="true" size={15} /> : <ShieldCheck aria-hidden="true" size={15} />}
                  <strong>{proposal.proposal_id}</strong>
                </span>
                <small>{proposal.apply_ready ? "可授权应用" : "仅复核"} · {proposal.risk_level || "未知风险"}</small>
              </button>
            ))}
          </nav>
          <article className="proposal-review-detail" data-r4-selected-proposal={selectedProposal?.proposal_id ?? "none"}>
            {selectedProposal ? (
              <>
                <header className="proposal-review-detail-heading">
                  <div>
                    <span>{selectedProposal.target_type || "未分类"} · {selectedProposal.current_state}</span>
                    <h3>{selectedProposal.proposal_id}</h3>
                    <p>{selectedProposal.human_reason_zh}</p>
                  </div>
                  <strong className={selectedProposal.apply_ready ? "proposal-readiness ready" : "proposal-readiness review-only"}>
                    {selectedProposal.apply_ready ? "可应用" : "仅复核"}
                  </strong>
                </header>

                {selectedTransaction && !actionResult ? (
                  <section
                    className={`proposal-persisted-transaction proposal-persisted-transaction-${selectedTransaction.state}`}
                    data-r4-persisted-transaction={selectedTransaction.transaction_id}
                    data-r4-transaction-proposal={selectedTransaction.proposal_id}
                  >
                    <div>
                      <strong>{selectedTransaction.state === "manual_rollback_required" ? "中断事务需要人工回滚" : "已提交事务仍可回滚"}</strong>
                      <p>{selectedTransaction.transaction_id}</p>
                      <p>{selectedTransaction.target_files.join(" · ")}</p>
                    </div>
                    <div className="proposal-manual-rollback">
                      <label>
                        <input
                          checked={rollbackAcknowledged}
                          data-r4-rollback-ack
                          disabled={pendingAction !== null}
                          onChange={(event) => setRollbackAcknowledged(event.currentTarget.checked)}
                          type="checkbox"
                        />
                        <span>我确认将该事务恢复到应用前字节。</span>
                      </label>
                      <button data-r4-rollback disabled={!rollbackAcknowledged || pendingAction !== null} onClick={() => void rollback()} type="button">
                        <RotateCcw aria-hidden="true" size={16} />
                        <span>{pendingAction === "rollback" ? "正在回滚" : "回滚该事务"}</span>
                      </button>
                    </div>
                  </section>
                ) : null}

                {selectedProposal.apply_ready ? (
                  <div className="proposal-scope-strip">
                    <span>风险：{selectedProposal.risk_level}</span>
                    <span>有效期：{formatProposalExpiry(selectedProposal.expires_at)}</span>
                    <span>半衰期：{selectedProposal.action_half_life}</span>
                  </div>
                ) : (
                  <p className="proposal-review-only-reason" data-r4-review-only-reason>
                    {selectedProposal.blocked_reason_zh || "该提案缺少精确内容或固定验证，因此不能应用。"}
                  </p>
                )}

                <div className="proposal-diff-narrator">
                  {proposalNarratorRows(selectedProposal.narrator).map((row) => (
                    <section data-r4-diff-section={row.id} key={row.id}>
                      <strong>{row.label}</strong>
                      <p>{row.value || "当前提案尚未提供该项精确说明。"}</p>
                    </section>
                  ))}
                </div>

                <div className="proposal-scope-grid">
                  <section>
                    <h4>精确目标文件</h4>
                    {selectedProposal.target_files.length > 0 ? (
                      <ul>
                        {selectedProposal.target_files.map((target) => <li data-r4-target-file={target} key={target}><code>{target}</code></li>)}
                      </ul>
                    ) : <p>尚未形成可应用的精确文件目标。</p>}
                  </section>
                  <section>
                    <h4>固定验证</h4>
                    {selectedProposal.validation_ids.length > 0 ? (
                      <ul>
                        {selectedProposal.validation_ids.map((validationId) => <li data-r4-validation-id={validationId} key={validationId}><code>{validationId}</code></li>)}
                      </ul>
                    ) : <p>尚未形成固定 validation ID。</p>}
                  </section>
                </div>

                <section className="proposal-rollback-plan">
                  <h4>回滚范围</h4>
                  <p>{selectedProposal.rollback_plan_zh || "没有执行写入，因此当前无回滚动作。"}</p>
                </section>

                {selectedProposal.apply_ready ? (
                  <div className="proposal-approval-band">
                    <label>
                      <input
                        checked={applyAcknowledged}
                        data-r4-apply-ack
                        disabled={pendingAction !== null || actionResult !== null}
                        onChange={(event) => setApplyAcknowledged(event.currentTarget.checked)}
                        type="checkbox"
                      />
                      <span>我已核对中文 diff、精确目标、固定验证和回滚范围。</span>
                    </label>
                    <button
                      data-r4-apply={selectedProposal.proposal_id}
                      disabled={!applyAcknowledged || pendingAction !== null || actionResult !== null}
                      onClick={() => void approveAndApply()}
                      type="button"
                    >
                      {pendingAction === "approve_apply" ? <RefreshCw aria-hidden="true" className="command-running-icon" size={16} /> : <CheckCircle2 aria-hidden="true" size={16} />}
                      <span>{pendingAction === "approve_apply" ? "正在应用" : "授权并应用"}</span>
                    </button>
                  </div>
                ) : null}

                {actionError ? <p className="proposal-action-error" data-r4-action-error>{actionError}</p> : null}
                {actionResult ? (
                  <section
                    className={`proposal-action-result proposal-action-result-${actionResult.state}`}
                    data-r4-action-result={actionResult.proposal_id}
                    data-r4-action-state={actionResult.state}
                    role="status"
                  >
                    <strong>{proposalActionTitle(actionResult)}</strong>
                    <p>{actionResult.message_zh}</p>
                    {actionResult.state_history?.length ? <p>{actionResult.state_history.join(" → ")}</p> : null}
                    {actionResult.validation_results?.length ? (
                      <ul>
                        {actionResult.validation_results.map((item) => (
                          <li key={item.validation_id}>{item.validation_id}：{item.status}</li>
                        ))}
                      </ul>
                    ) : null}
                    {actionResult.rollback_available && actionResult.rollback_token ? (
                      <div className="proposal-manual-rollback">
                        <label>
                          <input
                            checked={rollbackAcknowledged}
                            data-r4-rollback-ack
                            disabled={pendingAction !== null}
                            onChange={(event) => setRollbackAcknowledged(event.currentTarget.checked)}
                            type="checkbox"
                          />
                          <span>我确认将本次事务恢复到应用前字节。</span>
                        </label>
                        <button data-r4-rollback disabled={!rollbackAcknowledged || pendingAction !== null} onClick={() => void rollback()} type="button">
                          <RotateCcw aria-hidden="true" size={16} />
                          <span>{pendingAction === "rollback" ? "正在回滚" : "回滚本次变更"}</span>
                        </button>
                      </div>
                    ) : null}
                  </section>
                ) : null}
              </>
            ) : (
              <EmptyState dataState="proposal-empty" description="当前没有可复核的提案。" title="没有待授权提案" />
            )}
          </article>
        </div>
      </section>
    </div>
  );
}



export function proposalNarratorRows(narrator: ProposalNarrator): Array<{ id: keyof ProposalNarrator; label: string; value: string }> {
  return [
    { id: "what_changed_zh", label: "改了什么", value: narrator.what_changed_zh },
    { id: "why_changed_zh", label: "为什么改", value: narrator.why_changed_zh },
    { id: "affected_surfaces_zh", label: "影响什么", value: narrator.affected_surfaces_zh },
    { id: "how_to_verify_zh", label: "如何验证", value: narrator.how_to_verify_zh },
    { id: "how_to_rollback_zh", label: "如何回滚", value: narrator.how_to_rollback_zh },
  ];
}



export function proposalActionTitle(result: ProposalActionResult): string {
  if (result.state === "committed") return "应用与验证已完成";
  if (result.state === "rolled_back_by_human") return "人工回滚已完成";
  return "验证失败，已自动回滚";
}



export function formatProposalExpiry(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "未提供";
  return date.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" });
}
