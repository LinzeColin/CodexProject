from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable


_TOKEN_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SOURCE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PROFILE_STATUSES = {"active", "inactive", "blocked"}
_ASSIGNMENT_STATUSES = {"active", "ended", "pending_review"}


@dataclass(frozen=True)
class ParserProvenance:
    parser_id: str
    parser_version: str
    source_hash: str
    hash_algorithm: str = "sha256"
    hash_scheme: str = "sha256-file-bytes-v1"

    def __post_init__(self) -> None:
        _require_token(self.parser_id, "parser_id")
        _require_text(self.parser_version, "parser_version")
        if any(character.isspace() for character in self.parser_version):
            raise ValueError("parser_version must not contain whitespace")
        if not _SOURCE_HASH_RE.fullmatch(self.source_hash):
            raise ValueError("source_hash must be sha256:<64 lowercase hex>")
        if self.hash_algorithm != "sha256":
            raise ValueError("hash_algorithm must be sha256")
        _require_token(self.hash_scheme, "hash_scheme")

    def to_dict(self) -> dict[str, str]:
        return {
            "parser_id": self.parser_id,
            "parser_version": self.parser_version,
            "source_hash": self.source_hash,
            "hash_algorithm": self.hash_algorithm,
            "hash_scheme": self.hash_scheme,
        }


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    source_type: str
    capabilities: tuple[str, ...]
    parser_provenance: ParserProvenance
    profile_version: str = "1"
    status: str = "active"

    def __post_init__(self) -> None:
        _require_token(self.source_id, "source_id")
        _require_token(self.source_type, "source_type")
        _require_text(self.profile_version, "profile_version")
        if self.status not in _PROFILE_STATUSES:
            raise ValueError(f"unsupported source profile status: {self.status}")
        normalized = tuple(sorted(set(self.capabilities)))
        if not normalized:
            raise ValueError("capabilities must not be empty")
        for capability in normalized:
            _require_token(capability, "capability")
        object.__setattr__(self, "capabilities", normalized)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "capabilities": list(self.capabilities),
            "parser_provenance": self.parser_provenance.to_dict(),
            "profile_version": self.profile_version,
            "status": self.status,
        }


@dataclass(frozen=True)
class AccountRoleAssignment:
    assignment_id: str
    account_ref: str
    source_id: str
    role: str
    effective_from: date
    effective_to: date | None = None
    status: str = "active"

    def __post_init__(self) -> None:
        _require_token(self.assignment_id, "assignment_id")
        _require_token(self.account_ref, "account_ref")
        _require_token(self.source_id, "source_id")
        _require_token(self.role, "role")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        if self.status not in _ASSIGNMENT_STATUSES:
            raise ValueError(f"unsupported assignment status: {self.status}")

    def is_effective(self, at: date) -> bool:
        return self.effective_from <= at and (self.effective_to is None or at <= self.effective_to)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignment_id": self.assignment_id,
            "account_ref": self.account_ref,
            "source_id": self.source_id,
            "role": self.role,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "status": self.status,
        }


@dataclass(frozen=True)
class RoleReviewItem:
    review_id: str
    source_id: str
    account_ref: str
    proposed_role: str
    effective_from: date
    effective_to: date | None
    reason_code: str
    created_at: str
    status: str = "open"
    publish_allowed: bool = False

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.review_id, "review_id"),
            (self.source_id, "source_id"),
            (self.account_ref, "account_ref"),
            (self.proposed_role, "proposed_role"),
            (self.reason_code, "reason_code"),
        ):
            _require_token(value, field_name)
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        _require_rfc3339(self.created_at, "created_at")
        if self.status != "open":
            raise ValueError("new role review items must be open")
        if self.publish_allowed:
            raise ValueError("role review items must not permit publication")

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "source_id": self.source_id,
            "account_ref": self.account_ref,
            "proposed_role": self.proposed_role,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "reason_code": self.reason_code,
            "created_at": self.created_at,
            "status": self.status,
            "publish_allowed": self.publish_allowed,
        }


@dataclass(frozen=True)
class RoleRoutingDecision:
    status: str
    publish_allowed: bool
    assignment: AccountRoleAssignment | None
    review_item: RoleReviewItem | None

    def __post_init__(self) -> None:
        if self.status == "publishable":
            if not self.publish_allowed or self.assignment is None or self.review_item is not None:
                raise ValueError("publishable decisions require only an assignment")
        elif self.status == "review_required":
            if self.publish_allowed or self.assignment is not None or self.review_item is None:
                raise ValueError("review-required decisions require only a review item")
        else:
            raise ValueError(f"unsupported role routing status: {self.status}")


def roles_for_account(
    assignments: Iterable[AccountRoleAssignment],
    account_ref: str,
    at: date,
) -> tuple[str, ...]:
    _require_token(account_ref, "account_ref")
    return tuple(
        sorted(
            {
                assignment.role
                for assignment in assignments
                if assignment.account_ref == account_ref
                and assignment.status == "active"
                and assignment.is_effective(at)
            }
        )
    )


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_token(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase namespaced token")


def _require_rfc3339(value: str, field_name: str) -> None:
    _require_text(value, field_name)
    clean = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
