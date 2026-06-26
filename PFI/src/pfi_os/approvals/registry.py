from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from pfi_os.config import APPROVALS_DIR
from pfi_os.storage import atomic_write_json, locked_json_update, read_json_state
from pfi_os.strategies.base import Strategy


APPROVED_BUILT_IN_STRATEGIES = {
    ("ma_crossover", "0.1.0"),
    ("rsi_reversion", "0.1.0"),
    ("bollinger_reversion", "0.1.0"),
    ("breakout", "0.1.0"),
    ("momentum_rotation", "0.1.0"),
    ("alipay", "0.1.0"),
    ("alipay_enhanced", "0.1.0"),
}


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    strategy_id: str
    version: str
    status: str
    change_summary: str
    requested_at: str
    approved_at: str | None = None
    approver: str = "linzezhang"
    risk_notes: str = ""


class StrategyApprovalRegistry:
    def __init__(self, path: Path | str = APPROVALS_DIR / "StrategyApprovals.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def is_approved(self, strategy: Strategy) -> bool:
        strategy_key = (strategy.strategy_id, strategy.version)
        if strategy_key in APPROVED_BUILT_IN_STRATEGIES:
            return True
        return any(
            record.strategy_id == strategy.strategy_id and record.version == strategy.version and record.status == "Approved"
            for record in self.records()
        )

    def require_approved(self, strategy: Strategy) -> None:
        if not self.is_approved(strategy):
            raise PermissionError(
                f"Strategy {strategy.strategy_id} version {strategy.version} is not approved. "
                "策略未审批，不能运行回测。"
            )

    def request_approval(self, strategy_id: str, version: str, change_summary: str, risk_notes: str = "") -> ApprovalRecord:
        now = _now()
        record = ApprovalRecord(
            approval_id=f"{strategy_id}_{version}_{now.replace(':', '').replace('-', '')}",
            strategy_id=strategy_id,
            version=version,
            status="Pending",
            change_summary=change_summary,
            requested_at=now,
            risk_notes=risk_notes,
        )
        def append_record(payload: list[dict]) -> list[dict]:
            return [_record_payload(item) for item in payload if isinstance(item, dict)] + [asdict(record)]

        locked_json_update(self.path, [], append_record, expected_type=list)
        return record

    def approve(self, strategy_id: str, version: str, approver: str = "linzezhang") -> ApprovalRecord:
        approved_record: ApprovalRecord | None = None

        def approve_record(payload: list[dict]) -> list[dict]:
            nonlocal approved_record
            records = _records_from_payload(payload)
            for index in range(len(records) - 1, -1, -1):
                record = records[index]
                if record.strategy_id == strategy_id and record.version == version:
                    if record.status == "Approved":
                        approved_record = record
                        return [asdict(item) for item in records]
                    approved = ApprovalRecord(
                        approval_id=record.approval_id,
                        strategy_id=record.strategy_id,
                        version=record.version,
                        status="Approved",
                        change_summary=record.change_summary,
                        requested_at=record.requested_at,
                        approved_at=_now(),
                        approver=approver,
                        risk_notes=record.risk_notes,
                    )
                    records[index] = approved
                    approved_record = approved
                    return [asdict(item) for item in records]
            raise ValueError(f"No pending approval found for {strategy_id} {version}")

        locked_json_update(self.path, [], approve_record, expected_type=list)
        if approved_record is None:
            raise ValueError(f"No pending approval found for {strategy_id} {version}")
        return approved_record

    def latest_record(self, strategy_id: str, version: str | None = None) -> ApprovalRecord | None:
        matches = [
            record
            for record in self.records()
            if record.strategy_id == strategy_id and (version is None or record.version == version)
        ]
        return matches[-1] if matches else None

    def latest_status(self, strategy_id: str, version: str | None = None) -> str:
        record = self.latest_record(strategy_id, version)
        return record.status if record else ""

    def approve_or_request(
        self,
        strategy_id: str,
        version: str,
        change_summary: str,
        risk_notes: str = "",
        approver: str = "linzezhang",
    ) -> ApprovalRecord:
        record = self.latest_record(strategy_id, version)
        if record is None:
            self.request_approval(strategy_id, version, change_summary, risk_notes)
        return self.approve(strategy_id, version, approver=approver)

    def records(self) -> list[ApprovalRecord]:
        return _records_from_payload(read_json_state(self.path, [], expected_type=list))

    def _write_records(self, records: list[ApprovalRecord]) -> None:
        atomic_write_json(self.path, [asdict(record) for record in records])


def _records_from_payload(payload: list[dict]) -> list[ApprovalRecord]:
    records: list[ApprovalRecord] = []
    for item in payload:
        if isinstance(item, dict):
            records.append(ApprovalRecord(**_record_payload(item)))
    return records


def _record_payload(item: dict) -> dict:
    return {
        "approval_id": str(item.get("approval_id", "")),
        "strategy_id": str(item.get("strategy_id", "")),
        "version": str(item.get("version", "")),
        "status": str(item.get("status", "")),
        "change_summary": str(item.get("change_summary", "")),
        "requested_at": str(item.get("requested_at", "")),
        "approved_at": item.get("approved_at"),
        "approver": str(item.get("approver", "linzezhang")),
        "risk_notes": str(item.get("risk_notes", "")),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
