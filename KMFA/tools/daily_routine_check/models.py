from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Any


@dataclass(frozen=True)
class SourceMessage:
    group_name: str
    message_id: str
    message_time: datetime
    sender_name: str
    content: str = ""
    resource_count: int = 0
    resource_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceFile:
    group_name: str
    message_id: str
    message_time: datetime
    sender_name: str
    resource_type: str
    output_path: str
    absolute_path: str
    sha256: str = ""
    status: str = ""


@dataclass(frozen=True)
class RoutineRule:
    rule_id: str
    group_name: str
    frequency: str
    due_time: str
    required_senders: tuple[str, ...]
    artifact_name: str
    document_family: str
    keywords_positive: tuple[str, ...] = ()
    keywords_negative: tuple[str, ...] = ()
    weekdays: tuple[str, ...] = ()
    independent_required_artifact: bool = True
    trigger_window: str = ""


@dataclass
class RoutineCheckResult:
    rule_id: str
    check_date: date
    status: str
    group_name: str
    artifact_name: str
    matched_message_id: str | None = None
    matched_sender_name: str | None = None
    matched_file_sha256: str | None = None
    confidence: float = 0.0
    abnormal_type: str = ""
    reminder_level: str = "P2"
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class CashRiskResult:
    report_date: date
    risk_level: str
    total_available_cash: float | None
    hard_threshold: float
    soft_threshold: float
    source_message_id: str | None = None
    source_file_sha256: str | None = None
    confidence: float = 0.0
    reason: str = ""
