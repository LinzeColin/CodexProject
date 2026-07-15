#!/usr/bin/env python3
"""Owner-controlled delivery policy for the KMFA attendance skill."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DELIVERY_ENABLED = True
DELIVERY_DISABLED_STATUS = "NOT_SENT_OWNER_DISABLED"


def write_delivery_disabled_receipt(output_status: Mapping[str, Any]) -> dict[str, Any]:
    """Persist a receipt without resolving targets or invoking any sender."""
    receipt = {
        "notification_status": DELIVERY_DISABLED_STATUS,
        "delivery_enabled": False,
        "messages": [],
        "target_results": [],
        "run_id": str(output_status.get("run_id") or ""),
        "run_type": str(output_status.get("run_type") or ""),
        "work_date": str(output_status.get("work_date") or ""),
        "failure_reason": "owner policy keeps attendance delivery disabled",
    }
    receipt_path = output_status.get("dispatch_receipt")
    if receipt_path:
        path = Path(str(receipt_path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return receipt
