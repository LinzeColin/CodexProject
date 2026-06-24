from __future__ import annotations


MAINTAIN_ACTIONS = {"Maintain", "维持"}


def has_material_holding_change(recommendations: list[dict[str, object]], *, limit: int = 5) -> bool:
    for row in recommendations[:limit]:
        action = str(row.get("action_label") or "")
        if action and action not in MAINTAIN_ACTIONS:
            return True
    return False


def should_send_mail_for_run(
    severity: str,
    recommendations: list[dict[str, object]],
    *,
    data_quality_status: str = "pass",
    execution_locked: bool | None = None,
) -> bool:
    locked = data_quality_status != "pass" if execution_locked is None else execution_locked
    if severity == "Urgent":
        return True
    if locked:
        return False
    return has_material_holding_change(recommendations)


def suppressed_no_material_change_message() -> str:
    return "Non-essential email suppressed by policy; data-quality locks stay in app/report unless urgent"
