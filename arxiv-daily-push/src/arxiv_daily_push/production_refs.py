"""Fail-closed production readiness refs collection gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from typing import Any


PRODUCTION_REFS_VALIDATOR_ID = "adp-production-refs-v1"
DEFAULT_GITHUB_REPO = "LinzeColin/CodexProject"
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
PRODUCTION_REFS_TEMPLATE_REQUIRED_SECTIONS = (
    "runner",
    "smtp_secrets",
    "release_target",
    "workflow_vars",
)
PROVISIONING_AUDIT_REVIEW_ID = "adp-provisioning-audit-review-v1"
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


class ProductionRefsDiscoveryError(RuntimeError):
    """Raised when no-secret GitHub metadata discovery cannot complete."""


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


def build_production_refs_input_template(
    *,
    runner_label: str = "arxiv-daily-push",
    release_target: str = "",
) -> dict[str, Any]:
    """Build a no-secret owner-fillable input template for production refs."""

    return {
        "runner": {
            "ready": False,
            "label": str(runner_label or "").strip() or "arxiv-daily-push",
            "evidence_ref": "",
        },
        "smtp_secrets": {
            "ready": False,
            "secret_names": list(REQUIRED_SMTP_SECRET_NAMES),
            "evidence_ref": "",
        },
        "release_target": {
            "ready": False,
            "var_name": "ADP_RELEASE_TARGET",
            "target": str(release_target or "").strip(),
            "evidence_ref": "",
        },
        "workflow_vars": {
            "ready": False,
            "var_names": list(REQUIRED_WORKFLOW_VAR_NAMES),
            "evidence_ref": "",
        },
    }


def build_production_refs_input_from_github_metadata(
    *,
    repo: str = DEFAULT_GITHUB_REPO,
    runner_label: str = "arxiv-daily-push",
    secrets_metadata: Mapping[str, Any] | list[Any] | tuple[Any, ...],
    variables_metadata: Mapping[str, Any] | list[Any] | tuple[Any, ...],
    runners_metadata: Mapping[str, Any] | list[Any] | tuple[Any, ...],
) -> dict[str, Any]:
    """Build no-secret production refs input from GitHub Actions metadata."""

    repo_name = str(repo or DEFAULT_GITHUB_REPO).strip() or DEFAULT_GITHUB_REPO
    label = str(runner_label or "arxiv-daily-push").strip() or "arxiv-daily-push"
    secret_items = _metadata_items(secrets_metadata, "secrets")
    variable_items = _metadata_items(variables_metadata, "variables")
    runner_items = _metadata_items(runners_metadata, "runners")
    secret_names = _metadata_names(secret_items)
    variable_by_name = _metadata_by_name(variable_items)
    runner_matches = [runner for runner in runner_items if _runner_has_label(runner, label)]
    online_runner_matches = [runner for runner in runner_matches if str(runner.get("status") or "").lower() == "online"]
    release_target_item = variable_by_name.get("ADP_RELEASE_TARGET", {})
    release_target = str(release_target_item.get("value") or "").strip() if isinstance(release_target_item, Mapping) else ""
    configured_workflow_vars = sorted(name for name in REQUIRED_WORKFLOW_VAR_NAMES if name in variable_by_name)
    configured_smtp_secrets = sorted(name for name in REQUIRED_SMTP_SECRET_NAMES if name in secret_names)
    runner_ready = bool(online_runner_matches)
    smtp_ready = all(name in secret_names for name in REQUIRED_SMTP_SECRET_NAMES)
    release_target_ready = "ADP_RELEASE_TARGET" in variable_by_name and bool(release_target)
    workflow_vars_ready = all(name in variable_by_name for name in REQUIRED_WORKFLOW_VAR_NAMES)
    return {
        "runner": {
            "ready": runner_ready,
            "label": label,
            "evidence_ref": _metadata_ref(
                "github-runners",
                repo_name,
                label,
                _runner_fingerprint_payload(online_runner_matches),
            )
            if runner_ready
            else "",
        },
        "smtp_secrets": {
            "ready": smtp_ready,
            "secret_names": configured_smtp_secrets,
            "evidence_ref": _metadata_ref(
                "github-secrets",
                repo_name,
                "actions/smtp",
                _named_item_fingerprint_payload(secret_items, REQUIRED_SMTP_SECRET_NAMES),
            )
            if smtp_ready
            else "",
        },
        "release_target": {
            "ready": release_target_ready,
            "var_name": "ADP_RELEASE_TARGET",
            "target": release_target,
            "evidence_ref": _metadata_ref(
                "github-vars",
                repo_name,
                "actions/ADP_RELEASE_TARGET",
                {"name": "ADP_RELEASE_TARGET", "target": release_target},
            )
            if release_target_ready
            else "",
        },
        "workflow_vars": {
            "ready": workflow_vars_ready,
            "var_names": configured_workflow_vars,
            "evidence_ref": _metadata_ref(
                "github-vars",
                repo_name,
                "actions/workflow-vars",
                {"names": configured_workflow_vars},
            )
            if workflow_vars_ready
            else "",
        },
    }


def discover_production_refs_input_with_gh(
    *,
    repo: str = DEFAULT_GITHUB_REPO,
    runner_label: str = "arxiv-daily-push",
    gh_command: str = "gh",
    runner: Any = None,
) -> dict[str, Any]:
    """Collect GitHub Actions metadata with gh and return no-secret refs input."""

    repo_name = str(repo or DEFAULT_GITHUB_REPO).strip() or DEFAULT_GITHUB_REPO
    secrets_metadata = _gh_api_json(f"/repos/{repo_name}/actions/secrets", gh_command=gh_command, runner=runner)
    variables_metadata = _gh_api_json(f"/repos/{repo_name}/actions/variables", gh_command=gh_command, runner=runner)
    runners_metadata = _gh_api_json(f"/repos/{repo_name}/actions/runners", gh_command=gh_command, runner=runner)
    return build_production_refs_input_from_github_metadata(
        repo=repo_name,
        runner_label=runner_label,
        secrets_metadata=secrets_metadata,
        variables_metadata=variables_metadata,
        runners_metadata=runners_metadata,
    )


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


def build_provisioning_audit_review(
    refs_report: Mapping[str, Any],
    *,
    generated_at: str,
    workflow_run_ref: str = "",
    artifact_ref: str = "",
) -> dict[str, Any]:
    """Register a downloaded provisioning audit artifact without side effects."""

    refs_errors = validate_production_refs_report(refs_report)
    refs_ready = not refs_errors and refs_report.get("production_refs_ready") is True
    gates = [
        _gate("production_refs_report_valid", not refs_errors, refs_errors),
        _simple_gate(
            "production_refs_ready",
            refs_ready,
            "production refs report must pass before trial-start dispatch",
        ),
        _durable_value_gate("workflow_run_ref", workflow_run_ref),
        _durable_value_gate("artifact_ref", artifact_ref),
        _simple_gate(
            "no_side_effects_confirmed",
            all(
                refs_report.get(key) is False
                for key in (
                    "side_effects_performed",
                    "secret_values_logged",
                    "codex_auth_read",
                    "workflow_dispatched",
                    "production_acceptance_claimed",
                )
            ),
            "production refs report must record no side effects, no secret logging, no Codex auth read, no workflow dispatch, and no acceptance claim",
        ),
    ]
    blocking_reasons = [
        reason
        for gate in gates
        for reason in gate["blocking_reasons"]
        if gate.get("passed") is not True
    ]
    ready = not blocking_reasons
    return _with_audit_validation(
        {
            "audit_review_id": f"provisioning-audit:arxiv-daily-push:{generated_at}",
            "validator_id": PROVISIONING_AUDIT_REVIEW_ID,
            "project_id": "arxiv-daily-push",
            "generated_at": generated_at,
            "status": "pass" if ready else "blocked",
            "provisioning_audit_ready": ready,
            "refs_report_id": str(refs_report.get("refs_report_id") or ""),
            "refs_validator_id": str(refs_report.get("validator_id") or ""),
            "workflow_run_ref": _ref(workflow_run_ref),
            "artifact_ref": _ref(artifact_ref),
            "readiness_refs": dict(refs_report.get("readiness_refs") or {}) if isinstance(refs_report.get("readiness_refs"), Mapping) else {},
            "review_gates": gates,
            "side_effects_performed": False,
            "secret_values_logged": False,
            "codex_auth_read": False,
            "workflow_dispatched": False,
            "smtp_sent": False,
            "release_uploaded": False,
            "production_acceptance_claimed": False,
            "blocking_reasons": blocking_reasons,
            "next_external_actions": [] if ready else _next_audit_actions(gates),
        }
    )


def validate_provisioning_audit_review(review: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("validator_id") != PROVISIONING_AUDIT_REVIEW_ID:
        errors.append("provisioning audit review validator_id must be adp-provisioning-audit-review-v1")
    if review.get("status") not in {"pass", "blocked"}:
        errors.append("provisioning audit review status must be pass or blocked")
    if review.get("provisioning_audit_ready") not in {True, False}:
        errors.append("provisioning audit review requires provisioning_audit_ready boolean")
    for key in (
        "side_effects_performed",
        "secret_values_logged",
        "codex_auth_read",
        "workflow_dispatched",
        "smtp_sent",
        "release_uploaded",
        "production_acceptance_claimed",
    ):
        if review.get(key) is not False:
            errors.append(f"provisioning audit review {key} must be false")
    if not isinstance(review.get("review_gates"), list) or not review.get("review_gates"):
        errors.append("provisioning audit review requires review_gates list")
        return errors
    failed = [
        str(gate.get("gate_id"))
        for gate in review.get("review_gates", [])
        if isinstance(gate, Mapping) and gate.get("passed") is not True
    ]
    if review.get("status") == "pass":
        if review.get("provisioning_audit_ready") is not True:
            errors.append("passing provisioning audit review requires provisioning_audit_ready true")
        if failed:
            errors.append("passing provisioning audit review cannot include failed gates: " + ", ".join(failed))
        if review.get("blocking_reasons"):
            errors.append("passing provisioning audit review cannot include blocking_reasons")
        if not _ref(review.get("workflow_run_ref")):
            errors.append("passing provisioning audit review requires durable workflow_run_ref")
        if not _ref(review.get("artifact_ref")):
            errors.append("passing provisioning audit review requires durable artifact_ref")
        refs = review.get("readiness_refs")
        if not isinstance(refs, Mapping):
            errors.append("passing provisioning audit review requires readiness_refs object")
        else:
            for key in REQUIRED_REF_KEYS:
                if not _ref(refs.get(key)):
                    errors.append(f"passing provisioning audit review requires durable {key}")
    if review.get("status") == "blocked" and not review.get("blocking_reasons"):
        errors.append("blocked provisioning audit review requires blocking_reasons")
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


def _durable_value_gate(gate_id: str, value: Any) -> dict[str, Any]:
    return _simple_gate(gate_id, bool(_ref(value)), f"{gate_id} must be a durable ref containing ://")


def _simple_gate(gate_id: str, passed: bool, reason: str) -> dict[str, Any]:
    return _gate(gate_id, passed, [] if passed else [reason])


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


def _next_audit_actions(gates: list[Mapping[str, Any]]) -> list[str]:
    action_map = {
        "production_refs_report_valid": "rerun the provisioning audit workflow and download a valid adp-production-refs-v1 artifact",
        "production_refs_ready": "resolve blocked runner, SMTP secret-name, Release target, or workflow variable readiness in the provisioning audit",
        "workflow_run_ref": "provide a durable GitHub Actions workflow run ref for the provisioning audit",
        "artifact_ref": "provide a durable artifact ref for adp-production-provisioning-audit",
        "no_side_effects_confirmed": "use a no-secret provisioning refs report that records no side effects",
    }
    actions = []
    for gate in gates:
        if gate.get("passed") is True:
            continue
        actions.append(action_map.get(str(gate.get("gate_id")), f"resolve {gate.get('gate_id')}"))
    return actions


def _metadata_items(metadata: Mapping[str, Any] | list[Any] | tuple[Any, ...], key: str) -> list[Mapping[str, Any]]:
    raw_items: Any
    if isinstance(metadata, Mapping):
        raw_items = metadata.get(key)
    else:
        raw_items = metadata
    if not isinstance(raw_items, list | tuple):
        return []
    return [item for item in raw_items if isinstance(item, Mapping)]


def _metadata_names(items: list[Mapping[str, Any]]) -> set[str]:
    return {str(item.get("name") or "").strip() for item in items if str(item.get("name") or "").strip()}


def _metadata_by_name(items: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(item.get("name") or "").strip(): item for item in items if str(item.get("name") or "").strip()}


def _runner_has_label(runner: Mapping[str, Any], label: str) -> bool:
    labels = runner.get("labels")
    if not isinstance(labels, list | tuple):
        return False
    names = {str(item.get("name") or "").strip() for item in labels if isinstance(item, Mapping)}
    return label in names


def _runner_fingerprint_payload(runners: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    payload = []
    for runner in runners:
        labels = runner.get("labels") if isinstance(runner.get("labels"), list | tuple) else []
        payload.append(
            {
                "name": str(runner.get("name") or ""),
                "status": str(runner.get("status") or ""),
                "busy": bool(runner.get("busy")),
                "labels": sorted(str(item.get("name") or "") for item in labels if isinstance(item, Mapping)),
            }
        )
    return payload


def _named_item_fingerprint_payload(items: list[Mapping[str, Any]], names: tuple[str, ...]) -> list[dict[str, Any]]:
    by_name = _metadata_by_name(items)
    return [
        {
            "name": name,
            "updated_at": str(by_name.get(name, {}).get("updated_at") or ""),
        }
        for name in names
        if name in by_name
    ]


def _metadata_ref(scheme: str, repo: str, path: str, payload: Any) -> str:
    return f"{scheme}://{repo}/{path}#sha256:{_fingerprint(payload)}"


def _fingerprint(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _gh_api_json(endpoint: str, *, gh_command: str, runner: Any = None) -> Any:
    command = [gh_command, "api", endpoint]
    run = runner or _run_command
    try:
        result = run(command)
    except FileNotFoundError as exc:
        raise ProductionRefsDiscoveryError("gh command is required for GitHub metadata discovery") from exc
    if int(getattr(result, "returncode", 1)) != 0:
        raise ProductionRefsDiscoveryError(f"gh api {endpoint} failed with exit code {getattr(result, 'returncode', '<unknown>')}")
    try:
        return json.loads(str(getattr(result, "stdout", "") or ""))
    except json.JSONDecodeError as exc:
        raise ProductionRefsDiscoveryError(f"gh api {endpoint} returned invalid JSON") from exc


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)


def _with_validation(report: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(report)
    normalized["validation_errors"] = validate_production_refs_report(normalized)
    return normalized


def _with_audit_validation(review: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(review)
    normalized["validation_errors"] = validate_provisioning_audit_review(normalized)
    return normalized


def _ref(value: Any) -> str:
    text = str(value or "").strip()
    return text if "://" in text else ""
