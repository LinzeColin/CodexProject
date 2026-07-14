import { CheckCircle2, Play, RefreshCw, RotateCcw, ShieldCheck, X } from "lucide-react";
import type { KeyboardEvent } from "react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { LOCAL_APP_HANDOFF_URL, OWNER_DAILY_UI_VERSION, OwnerDailyResult, OwnerDailyStepId } from "../../shared/atlas/constants";
import { RuntimeState } from "../../shared/atlas/contracts";
import { isOwnerDailyResult, isRecord, mergeOwnerDailyRetry } from "../../shared/runtime/operations";



export function OwnerDailyEntry({
  available,
  onOpen,
  serverMode,
}: {
  available: boolean;
  onOpen: () => void;
  serverMode: RuntimeState["serverMode"];
}) {
  return (
    <section
      className={available ? "owner-daily-entry available" : "owner-daily-entry local-required"}
      data-r5-owner-daily-entry={OWNER_DAILY_UI_VERSION}
      data-r5-owner-daily-runtime={available ? "available" : "local_required"}
    >
      <div className="owner-daily-entry-copy">
        <ShieldCheck aria-hidden="true" size={16} />
        <div>
          <strong>日常维护</strong>
          <span>8 项 no-write 检查</span>
        </div>
      </div>
      {available ? (
        <button data-r5-owner-daily-open onClick={onOpen} type="button">
          <Play aria-hidden="true" size={14} />
          <span>打开检查</span>
        </button>
      ) : (
        <a data-r5-owner-daily-handoff href={LOCAL_APP_HANDOFF_URL}>
          {serverMode === "本地自释放" ? "更新本地 app" : "在本地 app 打开"}
        </a>
      )}
    </section>
  );
}



export function OwnerDailyWorkspace({
  onClose,
  onResultChange,
  result,
}: {
  onClose: () => void;
  onResultChange: (result: OwnerDailyResult | null) => void;
  result: OwnerDailyResult | null;
}) {
  const dialogRef = useRef<HTMLElement | null>(null);
  const [pendingAction, setPendingAction] = useState<"run" | OwnerDailyStepId | null>(null);
  const [actionError, setActionError] = useState("");

  useLayoutEffect(() => {
    dialogRef.current?.querySelector<HTMLButtonElement>("[data-r5-owner-daily-start]")?.focus();
  }, []);

  useEffect(() => {
    const handleDialogKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape" && pendingAction === null) {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>("button:not([disabled]), a[href], summary, [tabindex]:not([tabindex='-1'])"),
      ).filter((element) => element.getClientRects().length > 0);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && (active === first || !dialogRef.current.contains(active))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || !dialogRef.current.contains(active))) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", handleDialogKey);
    return () => window.removeEventListener("keydown", handleDialogKey);
  }, [onClose, pendingAction]);

  const postOwnerDaily = async (body: { action: "run" } | { action: "retry"; step_id: OwnerDailyStepId }): Promise<OwnerDailyResult> => {
    const response = await fetch("/__memory_atlas_owner_daily", {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const message = isRecord(payload) && typeof payload.message_zh === "string"
        ? payload.message_zh
        : `Owner Daily 请求失败（HTTP ${response.status}）。`;
      throw new Error(message);
    }
    if (!isOwnerDailyResult(payload)) {
      throw new Error("Owner Daily 返回格式或 no-write 安全字段未通过校验，已停止显示结果。");
    }
    return payload;
  };

  const runProfile = async () => {
    if (pendingAction) return;
    setPendingAction("run");
    setActionError("");
    onResultChange(null);
    try {
      const nextResult = await postOwnerDaily({ action: "run" });
      if (nextResult.action !== "run") throw new Error("Owner Daily 返回了错误的 action，已停止显示结果。");
      onResultChange(nextResult);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Owner Daily 未完成，请查看本机日志后重试。");
    } finally {
      setPendingAction(null);
    }
  };

  const retryStep = async (stepId: OwnerDailyStepId) => {
    if (!result || pendingAction || !result.retryable_step_ids.includes(stepId)) return;
    setPendingAction(stepId);
    setActionError("");
    try {
      const retry = await postOwnerDaily({ action: "retry", step_id: stepId });
      if (retry.action !== "retry" || retry.requested_step_id !== stepId) {
        throw new Error("Owner Daily retry 返回了错误步骤，已停止合并结果。");
      }
      onResultChange(mergeOwnerDailyRetry(result, retry));
    } catch (error) {
      setActionError(error instanceof Error ? error.message : "Owner Daily 单步重试未完成。");
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <div
      className="proposal-workspace-backdrop owner-daily-workspace-backdrop"
      data-r5-owner-daily-workspace={OWNER_DAILY_UI_VERSION}
    >
      <section aria-label="Owner Daily 日常维护" aria-modal="true" className="proposal-workspace-surface owner-daily-workspace-surface" ref={dialogRef} role="dialog">
        <header className="proposal-workspace-heading owner-daily-workspace-heading">
          <div>
            <p className="eyebrow">日常维护</p>
            <h2>Owner Daily</h2>
            <span>八个固定步骤 · 只读 dry-run · 失败步骤可单独重试</span>
          </div>
          <button aria-label="关闭 Owner Daily" className="proposal-workspace-close" disabled={pendingAction !== null} onClick={onClose} title="关闭" type="button">
            <X aria-hidden="true" size={18} />
          </button>
        </header>
        <div className="owner-daily-workspace-body">
          <section className="owner-daily-start-band">
            <div>
              <strong>{result ? "重新检查当前维护状态" : "检查当前维护状态"}</strong>
              <p>不会写入 source、runtime 或 raw 数据，不会推送 GitHub、应用提案、发送到 ChatGPT 或打开浏览器。</p>
            </div>
            <button data-r5-owner-daily-start disabled={pendingAction !== null} onClick={() => void runProfile()} type="button">
              {pendingAction === "run" ? <RefreshCw aria-hidden="true" className="command-running-icon" size={16} /> : <Play aria-hidden="true" size={16} />}
              <span>{pendingAction === "run" ? "正在检查" : "开始 no-write 检查"}</span>
            </button>
          </section>

          {actionError ? <p className="owner-daily-action-error" data-r5-owner-daily-error role="alert">{actionError}</p> : null}

          {result ? (
            <>
              <section
                aria-live="polite"
                className={`owner-daily-summary owner-daily-summary-${result.status.toLowerCase()}`}
                data-r5-owner-daily-result-status={result.status}
                data-r5-owner-daily-summary
                role="status"
              >
                <div>
                  {result.status === "PASS" ? <CheckCircle2 aria-hidden="true" size={22} /> : <ShieldCheck aria-hidden="true" size={22} />}
                  <div>
                    <strong>{result.status === "PASS" ? "日常检查已通过" : "部分步骤需要处理"}</strong>
                    <p>{result.conclusion_zh}</p>
                  </div>
                </div>
                <dl>
                  <div data-r5-owner-daily-completed-count={result.completed_count}><dt>已完成</dt><dd>{result.completed_count}</dd></div>
                  <div data-r5-owner-daily-failed-count={result.failed_count}><dt>未通过</dt><dd>{result.failed_count}</dd></div>
                </dl>
              </section>

              <div className="owner-daily-step-list" data-r5-owner-daily-step-list>
                {result.steps.map((step) => (
                  <article
                    className={`owner-daily-step owner-daily-step-${step.status}`}
                    data-r5-owner-daily-step={step.step_id}
                    data-r5-owner-daily-step-status={step.status}
                    key={step.step_id}
                  >
                    <header>
                      <span>{String(step.order).padStart(2, "0")}</span>
                      <div>
                        <strong>{step.label_zh}</strong>
                        <small>{step.status === "pass" ? "通过" : "未通过"}</small>
                      </div>
                      {step.status === "pass" ? <CheckCircle2 aria-hidden="true" size={18} /> : <ShieldCheck aria-hidden="true" size={18} />}
                    </header>
                    {step.status === "pass" ? (
                      <p>{step.conclusion_zh}</p>
                    ) : (
                      <div className="owner-daily-step-failure">
                        <p data-r5-owner-daily-failure>{step.failure_zh}</p>
                        <button
                          data-r5-owner-daily-retry={step.step_id}
                          disabled={pendingAction !== null}
                          onClick={() => void retryStep(step.step_id)}
                          type="button"
                        >
                          <RotateCcw aria-hidden="true" className={pendingAction === step.step_id ? "command-running-icon" : undefined} size={14} />
                          <span>{pendingAction === step.step_id ? "正在重试" : "只重试此步骤"}</span>
                        </button>
                      </div>
                    )}
                    <details>
                      <summary>机读详情</summary>
                      <div className="owner-daily-machine-detail">
                        <code>{step.invocation.join(" ")}</code>
                        <small>耗时 {step.duration_ms} ms</small>
                        {Object.keys(step.metrics).length > 0 ? (
                          <dl>
                            {Object.entries(step.metrics).map(([key, value]) => (
                              <div key={key}><dt>{key}</dt><dd>{Array.isArray(value) ? value.join(" · ") : String(value)}</dd></div>
                            ))}
                          </dl>
                        ) : null}
                      </div>
                    </details>
                  </article>
                ))}
              </div>
            </>
          ) : pendingAction !== "run" ? (
            <section className="owner-daily-empty-state">
              <ShieldCheck aria-hidden="true" size={22} />
              <div>
                <strong>尚未运行本次检查</strong>
                <p>开始后会先给出整体结论，再列出八个步骤；只有失败步骤会出现重试入口。</p>
              </div>
            </section>
          ) : (
            <section className="owner-daily-empty-state owner-daily-running-state" aria-live="polite">
              <RefreshCw aria-hidden="true" className="command-running-icon" size={22} />
              <div><strong>正在顺序检查八个步骤</strong><p>失败不会中断后续步骤，完成后会给出完整结论。</p></div>
            </section>
          )}
        </div>
      </section>
    </div>
  );
}
