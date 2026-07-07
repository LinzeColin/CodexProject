from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from .models import RoutineCheckResult, RoutineRule, SourceMessage
from .schedule_rules import has_due_time_passed, is_rule_due_on


def keyword_score(text: str, positives: tuple[str, ...], negatives: tuple[str, ...]) -> float:
    if not text:
        return 0.0
    score = 0.0
    for k in positives:
        if k and k in text:
            score += 1.0
    for k in negatives:
        if k and k in text:
            score -= 1.0
    return max(score, 0.0)


def message_matches_rule(msg: SourceMessage, rule: RoutineRule) -> tuple[bool, float, str]:
    if msg.group_name != rule.group_name:
        return False, 0.0, "group mismatch"
    if msg.sender_name not in rule.required_senders:
        return False, 0.0, "sender mismatch"
    score = keyword_score(msg.content, rule.keywords_positive, rule.keywords_negative)
    if score > 0:
        return True, min(1.0, score / max(1, len(rule.keywords_positive))), "keyword match"
    if msg.resource_count > 0:
        return True, 0.35, "image/file candidate needs OCR"
    return False, 0.0, "no keyword or resource"


def evaluate_rule(
    rule: RoutineRule,
    messages: Iterable[SourceMessage],
    check_date: date,
    now: datetime,
    respect_due_time: bool = False,
) -> RoutineCheckResult | None:
    if not is_rule_due_on(rule.frequency, check_date, rule.weekdays):
        return None
    if respect_due_time and not has_due_time_passed(now, rule.due_time):
        return RoutineCheckResult(rule.rule_id, check_date, "NOT_DUE", rule.group_name, rule.artifact_name, reason="due time not passed")

    candidates = [m for m in messages if m.message_time.date() == check_date]
    best: tuple[SourceMessage, float, str] | None = None
    for msg in candidates:
        matched, confidence, reason = message_matches_rule(msg, rule)
        if matched and (best is None or confidence > best[1]):
            best = (msg, confidence, reason)
    if best:
        msg, confidence, reason = best
        status = "OK" if confidence >= 0.70 else "NEEDS_OCR_REVIEW"
        return RoutineCheckResult(
            rule_id=rule.rule_id,
            check_date=check_date,
            status=status,
            group_name=rule.group_name,
            artifact_name=rule.artifact_name,
            matched_message_id=msg.message_id,
            matched_sender_name=msg.sender_name,
            confidence=confidence,
            reason=reason,
        )
    return RoutineCheckResult(rule.rule_id, check_date, "MISSING", rule.group_name, rule.artifact_name, reason="no matching message by trigger window")
