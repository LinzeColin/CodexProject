from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from pfi_os.config import DATA_DIR
from pfi_os.storage import locked_json_update, read_json_state


VALIDATION_QUEUE_DIR = DATA_DIR / "validationQueue"
VALIDATION_QUEUE_PATH = VALIDATION_QUEUE_DIR / "ValidationTasks.json"

VALIDATION_TASK_STATUSES = ("待验证", "验证中", "已完成", "暂停")


@dataclass(frozen=True)
class ValidationTask:
    task_id: str
    created_at: str
    source_report: str
    source_paragraph: str
    research_topic: str
    symbol: str
    market: str
    signal_to_validate: str
    sample_period: str
    cost_assumption: str
    benchmark: str
    status: str
    validation_report_path: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_validation_task(payload: dict[str, Any]) -> ValidationTask:
    return ValidationTask(
        task_id=str(payload.get("task_id") or f"task_{uuid4().hex[:12]}"),
        created_at=str(payload.get("created_at") or datetime.now().isoformat(timespec="seconds")),
        source_report=str(payload.get("source_report", "")).strip(),
        source_paragraph=str(payload.get("source_paragraph", "")).strip(),
        research_topic=str(payload.get("research_topic", "")).strip(),
        symbol=str(payload.get("symbol", "")).strip(),
        market=str(payload.get("market", "")).strip(),
        signal_to_validate=str(payload.get("signal_to_validate", "")).strip(),
        sample_period=str(payload.get("sample_period", "")).strip(),
        cost_assumption=str(payload.get("cost_assumption", "")).strip(),
        benchmark=str(payload.get("benchmark", "")).strip(),
        status=_status(payload.get("status", "待验证")),
        validation_report_path=str(payload.get("validation_report_path", "")).strip(),
        notes=str(payload.get("notes", "")).strip(),
    )


def load_validation_tasks(path: Path | str = VALIDATION_QUEUE_PATH) -> list[ValidationTask]:
    queue_path = Path(path)
    records = read_json_state(queue_path, [], expected_type=list)
    return [create_validation_task(item) for item in records if isinstance(item, dict)]


def save_validation_task(task: ValidationTask, path: Path | str = VALIDATION_QUEUE_PATH) -> Path:
    queue_path = Path(path)

    def append_task(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for item in records if isinstance(item, dict)] + [task.to_dict()]

    return locked_json_update(queue_path, [], append_task, expected_type=list)


def validation_task_frame(path: Path | str = VALIDATION_QUEUE_PATH) -> pd.DataFrame:
    tasks = load_validation_tasks(path)
    if not tasks:
        return pd.DataFrame(columns=_task_columns())
    frame = pd.DataFrame([task.to_dict() for task in tasks])
    return frame[_task_columns()]


def validation_queue_cards(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return [
            {"label": "验证任务", "value": 0, "help": "待验证研究问题数量"},
            {"label": "待验证", "value": 0, "help": "尚未完成验证的任务"},
            {"label": "已完成", "value": 0, "help": "已有验证报告路径的任务"},
            {"label": "暂停", "value": 0, "help": "暂不继续验证的任务"},
        ]
    statuses = frame["status"].astype(str)
    return [
        {"label": "验证任务", "value": int(len(frame)), "help": "待验证研究问题数量"},
        {"label": "待验证", "value": int((statuses == "待验证").sum()), "help": "尚未完成验证的任务"},
        {"label": "已完成", "value": int((statuses == "已完成").sum()), "help": "已有验证报告路径的任务"},
        {"label": "暂停", "value": int((statuses == "暂停").sum()), "help": "暂不继续验证的任务"},
    ]


def _task_columns() -> list[str]:
    return [
        "task_id",
        "created_at",
        "source_report",
        "source_paragraph",
        "research_topic",
        "symbol",
        "market",
        "signal_to_validate",
        "sample_period",
        "cost_assumption",
        "benchmark",
        "status",
        "validation_report_path",
        "notes",
    ]


def _status(value: object) -> str:
    text = str(value or "").strip()
    return text if text in VALIDATION_TASK_STATUSES else "待验证"
