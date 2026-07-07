from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from .models import RoutineCheckResult, RoutineRule, SourceMessage
from .schedule_rules import has_due_time_passed, is_rule_due_on, parse_time_hhmm


def keyword_score(text: str, positives: tuple[str, ...], negatives: tuple[str, ...]) -> float:
    if not text:
        return 0.0
    score = 0.0
    for k in positives:
        if k and k in text:
            score += 1.0
    return max(score, 0.0)


def contains_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    return any(k for k in keywords if k and k in text)


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


def message_matches_wrong_family(msg: SourceMessage, rule: RoutineRule) -> bool:
    if msg.group_name != rule.group_name:
        return False
    if msg.sender_name not in rule.required_senders:
        return False
    if contains_any_keyword(msg.content, rule.keywords_positive):
        return False
    return contains_any_keyword(msg.content, rule.keywords_negative)


def result_from_message(
    *,
    rule: RoutineRule,
    check_date: date,
    status: str,
    msg: SourceMessage,
    confidence: float,
    reason: str,
    abnormal_type: str = "",
    reminder_level: str = "P2",
) -> RoutineCheckResult:
    return RoutineCheckResult(
        rule_id=rule.rule_id,
        check_date=check_date,
        status=status,
        group_name=rule.group_name,
        artifact_name=rule.artifact_name,
        matched_message_id=msg.message_id,
        matched_sender_name=msg.sender_name,
        confidence=confidence,
        abnormal_type=abnormal_type,
        reminder_level=reminder_level,
        reason=reason,
    )


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
        return RoutineCheckResult(
            rule.rule_id,
            check_date,
            "NOT_DUE",
            rule.group_name,
            rule.artifact_name,
            reason="due time not passed",
        )

    candidates = [m for m in messages if m.message_time.date() == check_date]
    best: tuple[SourceMessage, float, str] | None = None
    for msg in candidates:
        matched, confidence, reason = message_matches_rule(msg, rule)
        if matched and (best is None or confidence > best[1]):
            best = (msg, confidence, reason)
    if best:
        msg, confidence, reason = best
        if confidence < 0.70:
            return result_from_message(
                rule=rule,
                check_date=check_date,
                status="NEEDS_OCR_REVIEW",
                msg=msg,
                confidence=confidence,
                reason=reason,
                abnormal_type="review",
                reminder_level="P1",
            )
        if msg.message_time.time() > parse_time_hhmm(rule.due_time):
            return result_from_message(
                rule=rule,
                check_date=check_date,
                status="LATE",
                msg=msg,
                confidence=confidence,
                reason=f"matched after due_time {rule.due_time}",
                abnormal_type="late",
                reminder_level="P1",
            )
        return result_from_message(
            rule=rule,
            check_date=check_date,
            status="OK",
            msg=msg,
            confidence=confidence,
            reason=reason,
        )
    wrong_candidates = [m for m in candidates if message_matches_wrong_family(m, rule)]
    if wrong_candidates:
        msg = sorted(wrong_candidates, key=lambda item: item.message_time)[0]
        return result_from_message(
            rule=rule,
            check_date=check_date,
            status="WRONG",
            msg=msg,
            confidence=0.65,
            reason="negative keyword matched a different document family",
            abnormal_type="wrong",
            reminder_level="P1",
        )
    return RoutineCheckResult(
        rule.rule_id,
        check_date,
        "MISSING",
        rule.group_name,
        rule.artifact_name,
        abnormal_type="missing",
        reminder_level="P0",
        reason="no matching message by trigger window",
    )
