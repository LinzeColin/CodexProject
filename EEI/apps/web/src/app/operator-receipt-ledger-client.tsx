"use client";

import { RefreshCw, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

const SHARED_API_BASE_STORAGE_KEY = "eei.apiBaseUrl.v1";

export type OperatorReceiptLedgerRecord = {
  schema_version: "eei-operator-input-submission-receipt-ledger-v1";
  artifact_id: string;
  task_id: string;
  acceptance_ids: string[];
  receipt_count: number;
  accepted_receipt_count: number;
  rejected_receipt_count: number;
  latest_receipt_id: string;
  receipt_ids: string[];
  release_gate_closed_by_receipt_ledger: boolean;
  release_manager_preflight_refresh_allowed: boolean;
  mvp_release_gate_refresh_allowed: boolean;
  conflict_policy: {
    expected_previous_receipt_id_required_when_supplied: boolean;
    identical_receipt_is_idempotent: boolean;
    ledger_never_modifies_operator_input_files: boolean;
    receipt_id_must_be_unique: boolean;
  };
  non_claims: string[];
  receipts: OperatorReceiptRecord[];
};

type OperatorReceiptRecord = {
  receipt_id: string;
  status: string;
  input_id: string;
  acceptance_id: string;
  generated_at: string;
  validator_id: string;
};

type LedgerSyncState =
  | {
      mode: "server";
      status: "hydrated";
      endpoint: string;
      ledger: OperatorReceiptLedgerRecord;
    }
  | {
      mode: "server";
      status: "error";
      endpoint: string;
      reason: string;
      ledger: OperatorReceiptLedgerRecord;
    }
  | {
      mode: "local_fallback";
      status: "artifact";
      reason: "api_base_missing";
      ledger: OperatorReceiptLedgerRecord;
    };

type Props = {
  initialLedger: OperatorReceiptLedgerRecord;
  evidenceHref: string;
};

export function OperatorReceiptLedgerPanel({ initialLedger, evidenceHref }: Props) {
  const [syncState, setSyncState] = useState<LedgerSyncState>({
    mode: "local_fallback",
    status: "artifact",
    reason: "api_base_missing",
    ledger: initialLedger
  });
  const [loading, setLoading] = useState(false);

  const hydrateLedger = useCallback(async () => {
    const apiBaseUrl = readReceiptLedgerApiBaseUrl();
    if (!apiBaseUrl) {
      setSyncState({
        mode: "local_fallback",
        status: "artifact",
        reason: "api_base_missing",
        ledger: initialLedger
      });
      return;
    }

    const endpoint = `${apiBaseUrl}/v1/release/operator-input-submission-receipts`;
    setLoading(true);
    try {
      const response = await window.fetch(endpoint);
      const payload = (await response.json().catch(() => null)) as unknown;
      if (!response.ok || !isOperatorReceiptLedgerRecord(payload)) {
        setSyncState({
          mode: "server",
          status: "error",
          endpoint,
          reason: `http_${response.status}`,
          ledger: initialLedger
        });
        return;
      }
      setSyncState({ mode: "server", status: "hydrated", endpoint, ledger: payload });
    } catch (error) {
      setSyncState({
        mode: "server",
        status: "error",
        endpoint,
        reason: error instanceof Error ? error.name : "fetch_failed",
        ledger: initialLedger
      });
    } finally {
      setLoading(false);
    }
  }, [initialLedger]);

  useEffect(() => {
    void hydrateLedger();
  }, [hydrateLedger]);

  const ledger = syncState.ledger;
  const syncLabel = useMemo(() => {
    if (syncState.mode === "server" && syncState.status === "hydrated") return "API hydrated";
    if (syncState.mode === "server" && syncState.status === "error") return `API ${syncState.reason}`;
    return "local artifact";
  }, [syncState]);

  return (
    <article data-testid="status-receipt-ledger-panel">
      <header>
        <ShieldCheck size={18} aria-hidden="true" />
        <h2>Operator Receipt Ledger</h2>
        <button
          aria-label="Refresh operator receipt ledger"
          className="iconButton"
          data-testid="status-receipt-ledger-refresh"
          disabled={loading}
          onClick={() => void hydrateLedger()}
          title="Refresh operator receipt ledger"
          type="button"
        >
          <RefreshCw size={16} aria-hidden="true" />
        </button>
      </header>
      <div className="statusTable" data-testid="status-receipt-ledger-table">
        <div data-testid="status-receipt-ledger-schema">
          <strong>schema</strong>
          <span>{ledger.schema_version}</span>
          <em>{syncLabel}</em>
          <small>{syncState.mode === "server" ? syncState.endpoint : evidenceHref}</small>
        </div>
        <div data-testid="status-receipt-ledger-counts">
          <strong>receipts</strong>
          <span>
            {ledger.accepted_receipt_count} accepted / {ledger.rejected_receipt_count} rejected
          </span>
          <em>{ledger.receipt_count}</em>
          <small>{ledger.latest_receipt_id || "no receipt head"}</small>
        </div>
        <div data-testid="status-receipt-ledger-conflict-policy">
          <strong>conflict</strong>
          <span>
            {ledger.conflict_policy.identical_receipt_is_idempotent
              ? "idempotent retry"
              : "retry appends"}
          </span>
          <em>
            {ledger.conflict_policy.expected_previous_receipt_id_required_when_supplied
              ? "head checked"
              : "head unchecked"}
          </em>
          <small>
            {ledger.conflict_policy.ledger_never_modifies_operator_input_files
              ? "never modifies operator files"
              : "operator file mutation risk"}
          </small>
        </div>
        <div data-testid="status-receipt-ledger-release-policy">
          <strong>release</strong>
          <span>
            {ledger.release_manager_preflight_refresh_allowed
              ? "release-manager refresh allowed"
              : "release-manager refresh blocked"}
          </span>
          <em>
            {ledger.release_gate_closed_by_receipt_ledger ? "release closed" : "release open"}
          </em>
          <small>
            {ledger.mvp_release_gate_refresh_allowed
              ? "MVP refresh allowed"
              : "MVP refresh blocked"}
          </small>
        </div>
      </div>
    </article>
  );
}

function readReceiptLedgerApiBaseUrl() {
  const override = window.localStorage.getItem(SHARED_API_BASE_STORAGE_KEY)?.trim();
  const configured = process.env.NEXT_PUBLIC_EEI_API_BASE_URL?.trim();
  return stripTrailingSlash(override || configured || "");
}

function isOperatorReceiptLedgerRecord(value: unknown): value is OperatorReceiptLedgerRecord {
  if (!isRecord(value) || !isRecord(value.conflict_policy)) return false;
  return (
    value.schema_version === "eei-operator-input-submission-receipt-ledger-v1" &&
    typeof value.artifact_id === "string" &&
    typeof value.task_id === "string" &&
    Array.isArray(value.acceptance_ids) &&
    typeof value.receipt_count === "number" &&
    typeof value.accepted_receipt_count === "number" &&
    typeof value.rejected_receipt_count === "number" &&
    typeof value.latest_receipt_id === "string" &&
    Array.isArray(value.receipt_ids) &&
    Array.isArray(value.receipts) &&
    typeof value.release_gate_closed_by_receipt_ledger === "boolean" &&
    typeof value.release_manager_preflight_refresh_allowed === "boolean" &&
    typeof value.mvp_release_gate_refresh_allowed === "boolean" &&
    typeof value.conflict_policy.expected_previous_receipt_id_required_when_supplied ===
      "boolean" &&
    typeof value.conflict_policy.identical_receipt_is_idempotent === "boolean" &&
    typeof value.conflict_policy.ledger_never_modifies_operator_input_files === "boolean" &&
    typeof value.conflict_policy.receipt_id_must_be_unique === "boolean" &&
    value.receipts.every(isOperatorReceiptRecord)
  );
}

function isOperatorReceiptRecord(value: unknown): value is OperatorReceiptRecord {
  return (
    isRecord(value) &&
    typeof value.receipt_id === "string" &&
    typeof value.status === "string" &&
    typeof value.input_id === "string" &&
    typeof value.acceptance_id === "string" &&
    typeof value.generated_at === "string" &&
    typeof value.validator_id === "string"
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function stripTrailingSlash(value: string) {
  return value.replace(/\/+$/, "");
}
