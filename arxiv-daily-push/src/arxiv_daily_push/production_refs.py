"""Fail-closed production readiness refs collection gate."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PRODUCTION_REFS_VALIDATOR_ID = "adp-production-refs-v1"
REQUIRED_SMTP_SECRET_NAMES = (
    "ADP_SMTP_HOST",
    "ADP_SMTP_PORT",
    "ADP_SMTP_USERNAME",
    "ADP_SMTP_PASSWORD",
)
REQUIRED_WORKFLOW_VAR_NAMES = (
    "ADP_RELEASE_TARGET",
    "ADP_ALLOW_SMTP_SEND",
    "ADP_ALLOW_RELEASE_UPLOAD",
)
REQUIRED_REF_KEYS = (
    "runner_ref",
    "smtp_secret_ref",
    "release_target_ref",
    "workflow_vars_ref",
)
SENSITIVE_INPUT_KEYWORDS = (
    "api_key",
    "auth_json",
    "credential",
    "credentials",
    "host",
    "oauth",
    "password",
    "port",
    "private_key",
    "secret_value",
    "secret_values",
    "token",
    "username",
    "value",
    "values",
)
SECRET_LIKE_VALUE_MARKERS = (
    "sk-",
    "ghp_",
    "github_pat_",
    "-----BEGIN",
    "password=",
    "token=",
)


def build_production_refs_report(readiness_input: Mapping[str, Any], *, generated_at: str) -> dict[str, Any]:
    """Build a no-secret readiness report for external production refs."""

    data: Mapping[str, Any] = readiness_input if isinstance(readiness_input, Mapping) else {}
    runner = _section(data, "runner")
    smtp_secrets = _section(data, "smtp_secrets")
    release_target = _section(data, "release_target")
    workflow_vars = _section(data, "workflow_vars")
    readiness_refs = {
        "runner_ref": _ref(runner.get("evidence_ref")),
        "smtp_secret_ref": _ref(smtp_secrets.get("evidence_ref")),
        "release_target_ref": _ref(release_target.get("evidence_ref")),
        "workflow_vars_ref": _ref(workflow_vars.get("evidence_ref")),
    }
    gates = [
        _gate("no_secret_values_in_input", not _secret_hygiene_errors(data), _secret_hygiene_errors(data)),
        _runner_gate(runner),
        _smtp_secret_gate(smtp_secrets),
        _release_target_gate(release_target),
        _workflow_vars_gate(workflow_vars),
        _durable_refs_gate(readiness_refs),
    ]
    blocking_reasons = [
        reason
        for gate in gates
        for reason in gate["blocking_reasons"]
        if gate.get("passed") is not True
    ]
    ready = not blocking_reasons
    report = {
        "refs_report_id": f"production-refs:arxiv-daily-push:{generated_at}",
        "validator_id": PRODUCTION_REFS_VALIDATOR_ID,
        "project_id": "arxiv-daily-push",
        "generated_at": generated_at,
        "status": "pass" if ready else "blocked",
        "production_refs_ready": ready,
        "readiness_refs": readiness_refs,
        "readiness_gates": gates,
        "side_effects_performed": False,
        "secret_values_logged": False,
        "codex_auth_read": False,
        "workflow_dispatched": False,
        "production_acceptance_claimed": False,
        "blocking_reasons": blocking_reasons,
        "next_external_actions": [] if ready else _next_external_actions(gates),
    }
    return _with_validation(report)


def validate_production_refs_report(report: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("validator_id") != PRODUCTION_REFS_VALIDATOR_ID:
        errors.append("production refs validator_id must be adp-production-refs-v1")
    if report.get("status") not in {"pass", "blocked"}:
        errors.append("production refs status must be pass or blocked")
    if report.get("production_refs_ready") not in {True, False}:
        errors.append("production refs report requires production_refs_ready boolean")
    for key in (
        "side_effects_performed",
        "secret_values_logged",
        "codex_auth_read",
        "workflow_dispatched",
        "production_acceptance_claimed",
    ):
        if report.get(key) is not False:
            errors.append(f"production refs {key} must be false")
    refs = report.get("readiness_refs")
    if not isinstance(refs, Mapping):
        errors.append("production refs report requires readiness_refs object")
    else:
        for key in REQUIRED_REF_KEYS:
            if key not in refs:
                errors.append(f"production refs readiness_refs missing {key}")
    gates = report.get("readiness_gates")
    if not isinstance(gates, list) or not gates:
        errors.append("production refs report requires readiness_gates list")
        return errors
    failed = [
        str(gate.get("gate_id"))
        for gate in gates
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if report.get("status") == "pass":
        if report.get("production_refs_ready") is not True:
            errors.append("passing production refs report requires production_refs_ready true")
        if failed:
            errors.append("passing production refs report cannot include failed gates: " + ", ".join(failed))
        if report.get("blocking_reasons"):
            errors.append("passing production refs report cannot include blocking_reasons")
        if isinstance(refs, Mapping):
            for key in REQUIRED_REF_KEYS:
                if not _ref(refs.get(key)):
                    errors.append(f"passing production refs report requires durable {key}")
    if report.get("status") == "blocked" and not report.get("blocking_reasons"):
        errors.append("blocked production refs report requires blocking_reasons")
    return errors


def _section(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    return value if isinstance(value, Mapping) else {}


def _runner_gate(section: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if section.get("ready") is not True:
        reasons.append("runner.ready must be true")
    if not str(section.get("label") or "").strip():
        reasons.append("runner.label is required")
    if not _ref(section.get("evidence_ref")):
        reasons.append("runner.evidence_ref must be a durable ref containing ://")
    return _gate("runner_ready", not reasons, reasons)


def _smtp_secret_gate(section: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if section.get("ready") is not True:
        reasons.append("smtp_secrets.ready must be true")
    names = _string_set(section.get("secret_names"))
    missing = [name for name in REQUIRED_SMTP_SECRET_NAMES if name not in names]
    if missing:
        reasons.append("smtp_secrets.secret_names missing required names: " + ", ".join(missing))
    if not _ref(section.get("evidence_ref")):
        reasons.append("smtp_secrets.evidence_ref must be a durable ref containing ://")
    return _gate("smtp_secrets_ready", not reasons, reasons)


def _release_target_gate(section: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if section.get("ready") is not True:
        reasons.append("release_target.ready must be true")
    if str(section.get("var_name") or "").strip() != "ADP_RELEASE_TARGET":
        reasons.append("release_target.var_name must be ADP_RELEASE_TARGET")
    if not str(section.get("target") or "").strip():
        reasons.append("release_target.target is required")
    if not _ref(section.get("evidence_ref")):
        reasons.append("release_target.evidence_ref must be a durable ref containing ://")
    return _gate("release_target_ready", not reasons, reasons)


def _workflow_vars_gate(section: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if section.get("ready") is not True:
        reasons.append("workflow_vars.ready must be true")
    names = _string_set(section.get("var_names"))
    missing = [name for name in REQUIRED_WORKFLOW_VAR_NAMES if name not in names]
    if missing:
        reasons.append("workflow_vars.var_names missing required names: " + ", ".join(missing))
    if not _ref(section.get("evidence_ref")):
        reasons.append("workflow_vars.evidence_ref must be a durable ref containing ://")
    return _gate("workflow_vars_ready", not reasons, reasons)


def _durable_refs_gate(readiness_refs: Mapping[str, str]) -> dict[str, Any]:
    missing = [key for key in REQUIRED_REF_KEYS if not _ref(readiness_refs.get(key))]
    return _gate(
        "readiness_refs_durable",
        not missing,
        [f"readiness_refs missing durable refs: {', '.join(missing)}"] if missing else [],
    )


def _secret_hygiene_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            key_path = f"{path}.{key_text}"
            key_lower = key_text.lower()
            if key_lower not in {"smtp_secrets", "secret_names"}:
                for marker in SENSITIVE_INPUT_KEYWORDS:
                    if marker in key_lower:
                        errors.append(f"{key_path} must not contain secret or credential values")
                        break
            errors.extend(_secret_hygiene_errors(item, key_path))
        return errors
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            errors.extend(_secret_hygiene_errors(item, f"{path}[{index}]"))
        return errors
    if isinstance(value, str):
        lowered = value.lower()
        for marker in SECRET_LIKE_VALUE_MARKERS:
            if marker.lower() in lowered:
                errors.append(f"{path} contains a secret-like value marker")
                break
    return errors


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        parts = value.replace(",", ";").split(";")
        return {part.strip() for part in parts if part.strip()}
    if isinstance(value, list | tuple | set):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()


def _gate(gate_id: str, passed: bool, reasons: list[str]) -> dict[str, Any]:
    return {"gate_id": gate_id, "passed": bool(passed), "blocking_reasons": [] if passed else reasons}


def _next_external_actions(gates: list[Mapping[str, Any]]) -> list[str]:
    action_map = {
        "no_secret_values_in_input": "remove secret values and provide only secret names plus durable evidence refs",
        "runner_ready": "provide ready runner label and durable runner readiness ref",
        "smtp_secrets_ready": "provide required SMTP secret names and durable GitHub secrets readiness ref without values",
        "release_target_ready": "provide ADP_RELEASE_TARGET readiness and durable GitHub variables ref",
        "workflow_vars_ready": "provide required workflow variable names and durable GitHub variables readiness ref",
        "readiness_refs_durable": "provide all production readiness refs with a durable scheme",
    }
    actions = []
    for gate in gates:
        if gate.get("passed") is True:
            continue
        actions.append(action_map.get(str(gate.get("gate_id")), f"resolve {gate.get('gate_id')}"))
    return actions


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_production_refs_report(normalized)
    return normalized


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
