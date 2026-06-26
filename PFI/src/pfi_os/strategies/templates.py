from __future__ import annotations

import re
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

from pfi_os.config import PROJECT_ROOT
from pfi_os.strategies.custom_builder import CUSTOM_STRATEGY_SPEC_PATH, custom_strategy_spec_from_payload, save_custom_strategy_spec


CUSTOM_STRATEGY_DIR = PROJECT_ROOT / "src" / "pfi_os" / "strategies" / "custom"
STRATEGY_PROFILE_DOC_DIR = PROJECT_ROOT / "docs" / "strategyProfiles"


@dataclass(frozen=True)
class StrategyTemplateArtifact:
    strategy_id: str
    class_name: str
    strategy_file: str
    profile_file: str
    approval_id: str
    status: str


@dataclass(frozen=True)
class StrategyCodeQualityReport:
    strategy_id: str
    status: str
    score: int
    findings: tuple[str, ...]
    path: str

    def to_row(self) -> dict[str, object]:
        return {
            "策略编号 Strategy Id": self.strategy_id,
            "代码状态 Code Status": self.status,
            "代码分数 Code Score": self.score,
            "发现项 Findings": ", ".join(self.findings),
            "代码路径 Code Path": self.path,
        }


@dataclass(frozen=True)
class StrategyReadinessGate:
    strategy_id: str
    status: str
    reasons: tuple[str, ...]
    actions: tuple[str, ...]

    def to_row(self) -> dict[str, object]:
        return {
            "策略编号 Strategy Id": self.strategy_id,
            "综合状态 Readiness Status": self.status,
            "原因 Reasons": ", ".join(self.reasons),
            "建议动作 Actions": ", ".join(self.actions),
        }


@dataclass(frozen=True)
class StrategySmokeTestReport:
    strategy_id: str
    status: str
    rows: int
    findings: tuple[str, ...]
    path: str

    def to_row(self) -> dict[str, object]:
        return {
            "策略编号 Strategy Id": self.strategy_id,
            "烟雾测试 Smoke Test": self.status,
            "信号行数 Signal Rows": self.rows,
            "发现项 Findings": ", ".join(self.findings),
            "代码路径 Code Path": self.path,
        }


def create_strategy_template(
    strategy_id: str,
    display_name: str,
    display_name_en: str,
    category: str,
    return_source: str,
    thesis: str,
    failure: str,
    parameter_notes: str = "",
    return_source_en: str = "",
    thesis_en: str = "",
    failure_en: str = "",
    parameter_notes_en: str = "",
    custom_spec: dict | None = None,
    custom_spec_path: Path | str = CUSTOM_STRATEGY_SPEC_PATH,
    version: str = "0.1.0",
    strategy_dir: Path | str = CUSTOM_STRATEGY_DIR,
    profile_dir: Path | str = STRATEGY_PROFILE_DOC_DIR,
    approval_registry=None,
    overwrite: bool = False,
) -> StrategyTemplateArtifact:
    normalized_id = normalize_strategy_id(strategy_id)
    class_name = strategy_class_name(normalized_id)
    strategy_root = Path(strategy_dir)
    profile_root = Path(profile_dir)
    strategy_root.mkdir(parents=True, exist_ok=True)
    profile_root.mkdir(parents=True, exist_ok=True)
    init_path = strategy_root / "__init__.py"
    if not init_path.exists():
        init_path.write_text('"""Custom strategy drafts. Drafts are not auto-imported or auto-approved."""\n', encoding="utf-8")
    strategy_path = strategy_root / f"{normalized_id}.py"
    profile_path = profile_root / f"{normalized_id}.md"
    clean_custom_spec = _prepare_custom_spec(
        custom_spec,
        strategy_id=normalized_id,
        version=version,
        display_name=display_name,
        display_name_en=display_name_en,
        category=category,
        return_source=return_source,
        return_source_en=return_source_en,
        thesis=thesis,
        thesis_en=thesis_en,
        failure=failure,
        failure_en=failure_en,
        parameter_notes=parameter_notes,
        parameter_notes_en=parameter_notes_en,
    )
    strategy_code = (
        _no_code_strategy_template_code(normalized_id, class_name, display_name_en, version, clean_custom_spec)
        if clean_custom_spec
        else _strategy_template_code(normalized_id, class_name, display_name_en, version)
    )
    _write_new_file(strategy_path, strategy_code, overwrite)
    _write_new_file(
        profile_path,
        _profile_template_markdown(
            normalized_id,
            display_name,
            display_name_en,
            category,
            return_source,
            thesis,
            failure,
            parameter_notes,
            return_source_en,
            thesis_en,
            failure_en,
            parameter_notes_en,
            version,
        ),
        overwrite,
    )
    if clean_custom_spec:
        save_custom_strategy_spec(clean_custom_spec, path=custom_spec_path)
    if approval_registry is None:
        from pfi_os.approvals import StrategyApprovalRegistry

        registry = StrategyApprovalRegistry()
    else:
        registry = approval_registry
    approval = registry.request_approval(
        normalized_id,
        version,
        f"Draft custom strategy template created for {display_name_en}.",
        f"Return source: {return_source}. Thesis: {thesis}. Failure regime: {failure}.",
    )
    return StrategyTemplateArtifact(
        strategy_id=normalized_id,
        class_name=class_name,
        strategy_file=strategy_path.as_posix(),
        profile_file=profile_path.as_posix(),
        approval_id=approval.approval_id,
        status=approval.status,
    )


def write_custom_strategy_code_for_spec(spec, strategy_dir: Path | str = CUSTOM_STRATEGY_DIR) -> Path:
    clean_spec = custom_strategy_spec_from_payload(spec)
    normalized_id = normalize_strategy_id(clean_spec.strategy_id)
    strategy_root = Path(strategy_dir)
    strategy_root.mkdir(parents=True, exist_ok=True)
    init_path = strategy_root / "__init__.py"
    if not init_path.exists():
        init_path.write_text('"""Custom strategy drafts. Drafts are not auto-imported or auto-approved."""\n', encoding="utf-8")
    strategy_path = strategy_root / f"{normalized_id}.py"
    strategy_path.write_text(
        _no_code_strategy_template_code(
            normalized_id,
            strategy_class_name(normalized_id),
            clean_spec.display_name_en,
            clean_spec.version,
            clean_spec.to_dict(),
        ),
        encoding="utf-8",
    )
    return strategy_path


def normalize_strategy_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        raise ValueError("Strategy id cannot be empty.")
    if not re.match(r"^[a-z][a-z0-9_]*$", cleaned):
        raise ValueError("Strategy id must start with a letter and contain only lowercase letters, numbers, and underscores.")
    return cleaned


def strategy_class_name(strategy_id: str) -> str:
    base = strategy_id[:-9] if strategy_id.endswith("_strategy") else strategy_id
    return "".join(part.capitalize() for part in base.split("_")) + "Strategy"


def evaluate_strategy_code_quality(path: Path | str) -> StrategyCodeQualityReport:
    strategy_path = Path(path)
    text = strategy_path.read_text(encoding="utf-8")
    strategy_id = _strategy_id_from_code(text) or strategy_path.stem
    checks = [
        ("缺少 Strategy 子类 Missing Strategy subclass", "class " in text and ("(Strategy)" in text or "(CustomNoCodeStrategy)" in text)),
        ("缺少 strategy_id Missing strategy_id", "strategy_id" in text),
        ("缺少 version Missing version", "version" in text),
        ("缺少 generate_signals Missing generate_signals", "def generate_signals" in text),
        ("缺少 StrategyResult Missing StrategyResult", "StrategyResult" in text),
        ("缺少 finalize_signal_frame 或权重裁剪 Missing finalize_signal_frame or weight clipping", "finalize_signal_frame" in text or ".clip(" in text or "CustomNoCodeStrategy" in text),
        ("仍是空仓模板 Still flat draft template", not _looks_like_flat_template(text)),
        ("缺少参数校验提示 Missing parameter validation hint", _has_parameter_validation_hint(text)),
    ]
    findings = tuple(label for label, passed in checks if not passed)
    score = int(round((len(checks) - len(findings)) / len(checks) * 100))
    status = "CodeReadyForReview" if not findings else "CodeDraft"
    return StrategyCodeQualityReport(strategy_id=strategy_id, status=status, score=score, findings=findings, path=strategy_path.as_posix())


def collect_strategy_code_quality_reports(strategy_dir: Path | str = CUSTOM_STRATEGY_DIR) -> list[StrategyCodeQualityReport]:
    root = Path(strategy_dir)
    if not root.exists():
        return []
    return [evaluate_strategy_code_quality(path) for path in sorted(root.glob("*.py")) if path.name != "__init__.py"]


def strategy_code_quality_rows(strategy_dir: Path | str = CUSTOM_STRATEGY_DIR) -> list[dict[str, object]]:
    return [report.to_row() for report in collect_strategy_code_quality_reports(strategy_dir)]


def run_strategy_smoke_test(path: Path | str) -> StrategySmokeTestReport:
    strategy_path = Path(path)
    strategy_id = strategy_path.stem
    try:
        strategy_cls = _load_strategy_class(strategy_path)
        strategy = strategy_cls()
        strategy_id = getattr(strategy, "strategy_id", strategy_id)
        data = _sample_smoke_data()
        result = strategy.generate_signals(data)
        signals = result.signals
        findings = _signal_findings(signals)
        status = "SmokePass" if not findings else "SmokeFail"
        return StrategySmokeTestReport(strategy_id=strategy_id, status=status, rows=int(len(signals)) if signals is not None else 0, findings=tuple(findings), path=strategy_path.as_posix())
    except Exception as exc:
        return StrategySmokeTestReport(strategy_id=strategy_id, status="SmokeFail", rows=0, findings=(f"{type(exc).__name__}: {exc}",), path=strategy_path.as_posix())


def collect_strategy_smoke_tests(strategy_dir: Path | str = CUSTOM_STRATEGY_DIR) -> list[StrategySmokeTestReport]:
    root = Path(strategy_dir)
    if not root.exists():
        return []
    return [run_strategy_smoke_test(path) for path in sorted(root.glob("*.py")) if path.name != "__init__.py"]


def strategy_smoke_test_rows(strategy_dir: Path | str = CUSTOM_STRATEGY_DIR) -> list[dict[str, object]]:
    return [report.to_row() for report in collect_strategy_smoke_tests(strategy_dir)]


def evaluate_strategy_readiness_gate(candidate, code_report: StrategyCodeQualityReport | None, approval_records=None, smoke_report: StrategySmokeTestReport | None = None) -> StrategyReadinessGate:
    approval_records = approval_records or []
    reasons: list[str] = []
    actions: list[str] = []
    strategy_id = getattr(candidate, "strategy_id", "")
    version = getattr(candidate, "version", "")
    profile_status = getattr(candidate, "quality_status", "")
    code_status = code_report.status if code_report else "MissingCode"
    smoke_status = smoke_report.status if smoke_report else "MissingSmoke"
    approval_status = _latest_approval_status(strategy_id, version, approval_records) or getattr(candidate, "approval_status", "")

    if profile_status != "ReadyForReview":
        reasons.append(f"Profile quality is {profile_status}.")
        missing = getattr(candidate, "missing_items", ())
        actions.append("Complete missing profile items: " + (", ".join(missing) if missing else "review profile fields."))
    if code_status != "CodeReadyForReview":
        reasons.append(f"Code quality is {code_status}.")
        if code_report and code_report.findings:
            actions.append("Fix code findings: " + ", ".join(code_report.findings))
        else:
            actions.append("Add or repair the matching custom strategy code file.")
    if approval_status != "Approved":
        reasons.append(f"Approval status is {approval_status or 'Missing'}.")
        actions.append("Submit or confirm strategy approval after profile and code review.")
    if smoke_status != "SmokePass":
        reasons.append(f"Smoke test status is {smoke_status}.")
        if smoke_report and smoke_report.findings:
            actions.append("Fix smoke test findings: " + ", ".join(smoke_report.findings))
        else:
            actions.append("Run or repair the candidate strategy smoke test.")

    if approval_status == "Approved" and profile_status == "ReadyForReview" and code_status == "CodeReadyForReview" and smoke_status == "SmokePass":
        return StrategyReadinessGate(strategy_id=strategy_id, status="ApprovedForResearch", reasons=("All pre-research gates passed.",), actions=("Continue with controlled research validation.",))
    if profile_status == "ReadyForReview" and code_status == "CodeReadyForReview" and smoke_status == "SmokePass":
        return StrategyReadinessGate(strategy_id=strategy_id, status="ReadyForReview", reasons=tuple(reasons), actions=tuple(actions))
    return StrategyReadinessGate(strategy_id=strategy_id, status="NotReady", reasons=tuple(reasons), actions=tuple(actions))


def _latest_approval_status(strategy_id: str, version: str, records) -> str:
    matches = [record for record in records if getattr(record, "strategy_id", "") == strategy_id and getattr(record, "version", "") == version]
    if not matches:
        return ""
    return getattr(matches[-1], "status", "")


def _load_strategy_class(path: Path):
    from pfi_os.strategies.base import Strategy

    module_name = f"pfi_os_custom_smoke_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load strategy module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidates = [
        value
        for value in module.__dict__.values()
        if isinstance(value, type) and issubclass(value, Strategy) and value is not Strategy and value.__module__ == module_name
    ]
    if not candidates:
        raise ValueError("No Strategy subclass found.")
    return candidates[0]


def _sample_smoke_data():
    from pfi_os.data.models import BarDataRequest
    from pfi_os.data.providers import SampleDataProvider

    return SampleDataProvider(seed=101).get_bars(
        BarDataRequest(symbol="SMOKE", market="US", interval="1d", start="2021-01-01", end="2021-03-31")
    )


def _signal_findings(signals) -> list[str]:
    if signals is None:
        return ["generate_signals returned no signal frame."]
    required = {"datetime", "symbol", "market", "close", "target_weight"}
    missing = sorted(required - set(signals.columns))
    findings = [f"Missing required signal columns: {', '.join(missing)}."] if missing else []
    if len(signals) == 0:
        findings.append("Signal frame is empty.")
    if "target_weight" in signals.columns:
        weights = signals["target_weight"]
        if weights.isna().any():
            findings.append("target_weight contains missing values.")
        if ((weights < -1.0) | (weights > 1.0)).any():
            findings.append("target_weight is outside [-1.00, 1.00].")
    return findings


def _write_new_file(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists.")
    path.write_text(content, encoding="utf-8")


def _strategy_id_from_code(text: str) -> str:
    match = re.search(r"strategy_id\s*=\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else ""


def _looks_like_flat_template(text: str) -> bool:
    if "Draft example: flat target weights" in text or "Replace this method with your actual signal rules" in text:
        return True
    has_flat_initialization = "target = pd.Series(0.0, index=data.index)" in text
    has_non_zero_assignment = any(_is_non_zero_target_assignment(line) for line in text.splitlines())
    return has_flat_initialization and not has_non_zero_assignment


def _is_non_zero_target_assignment(line: str) -> bool:
    stripped = line.strip().replace(" ", "")
    if not stripped.startswith("target[") or "=" not in stripped:
        return False
    assigned = stripped.rsplit("=", 1)[-1]
    return assigned.startswith(("1", "-1", "0.")) and not assigned.startswith("0.0")


def _has_parameter_validation_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ["raise valueerror", "assert ", "if lookback", "if self.", "min(", "max("])


def _prepare_custom_spec(
    custom_spec: dict | None,
    *,
    strategy_id: str,
    version: str,
    display_name: str,
    display_name_en: str,
    category: str,
    return_source: str,
    return_source_en: str,
    thesis: str,
    thesis_en: str,
    failure: str,
    failure_en: str,
    parameter_notes: str,
    parameter_notes_en: str,
) -> dict | None:
    if custom_spec is None:
        return None
    payload = dict(custom_spec)
    payload.update(
        {
            "strategy_id": strategy_id,
            "version": version,
            "display_name": display_name,
            "display_name_en": display_name_en,
            "category": category,
            "return_source": return_source,
            "return_source_en": return_source_en or return_source,
            "thesis": thesis,
            "thesis_en": thesis_en or thesis,
            "failure": failure,
            "failure_en": failure_en or failure,
            "parameter_notes": parameter_notes,
            "parameter_notes_en": parameter_notes_en or parameter_notes,
        }
    )
    payload.setdefault("logic_key", "mean_reversion")
    payload.setdefault("indicator_keys", [])
    payload.setdefault("settings", {})
    return payload


def _no_code_strategy_template_code(strategy_id: str, class_name: str, display_name_en: str, version: str, custom_spec: dict) -> str:
    embedded_spec = json.dumps(custom_spec, ensure_ascii=False, indent=2, sort_keys=True)
    return f'''from __future__ import annotations

import json

import pandas as pd

from pfi_os.strategies.base import StrategyResult
from pfi_os.strategies.custom_builder import CustomNoCodeStrategy, get_custom_strategy_spec


_EMBEDDED_SPEC = json.loads(r"""{embedded_spec}""")


class {class_name}(CustomNoCodeStrategy):
    strategy_id = "{strategy_id}"
    version = "{version}"
    description = "No-code custom strategy: {display_name_en}. Research only, not approved by default."

    def __init__(self, weight: float = 1.0):
        spec = get_custom_strategy_spec(self.strategy_id, default=_EMBEDDED_SPEC)
        if spec.strategy_id != self.strategy_id:
            raise ValueError("strategy spec mismatch")
        if spec.version != self.version:
            raise ValueError("strategy spec version mismatch")
        super().__init__(spec=spec, weight=weight)

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        return super().generate_signals(data)
'''


def _strategy_template_code(strategy_id: str, class_name: str, display_name_en: str, version: str) -> str:
    return f'''from __future__ import annotations

import pandas as pd

from pfi_os.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class {class_name}(Strategy):
    strategy_id = "{strategy_id}"
    version = "{version}"
    description = "Draft custom strategy: {display_name_en}. Research only, not approved by default."

    def __init__(self, lookback: int = 20):
        super().__init__(lookback=lookback)
        self.lookback = lookback

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        """Draft example: flat target weights until you replace this logic.

        Replace this method with your actual signal rules, then complete strategy
        profile review and approval before running formal research.
        """
        target = pd.Series(0.0, index=data.index)
        signals = finalize_signal_frame(data, target)
        return StrategyResult(signals=signals, metadata=self.metadata())
'''


def _profile_template_markdown(
    strategy_id: str,
    display_name: str,
    display_name_en: str,
    category: str,
    return_source: str,
    thesis: str,
    failure: str,
    parameter_notes: str,
    return_source_en: str,
    thesis_en: str,
    failure_en: str,
    parameter_notes_en: str,
    version: str,
) -> str:
    return_source_en = return_source_en or return_source
    thesis_en = thesis_en or thesis
    failure_en = failure_en or failure
    parameter_notes = parameter_notes or "请补充参数含义、默认值、允许范围和禁止组合。"
    parameter_notes_en = parameter_notes_en or parameter_notes
    return f"""# {display_name} {display_name_en}

策略编号：`{strategy_id}`

Strategy Id: `{strategy_id}`

版本：`{version}`

Version: `{version}`

类别：{category}

Category: {category}

## 研究假设

{thesis}

## Research Thesis

{thesis_en}

## 收益来源

{return_source}

## Return Source

{return_source_en}

## 失效环境

{failure}

## Failure Regime

{failure_en}

## 参数设置

{parameter_notes}

## Parameter Settings

{parameter_notes_en}

## 审批状态

默认状态为 `Pending`。完成研究假设、代码审查、数据验证和风险说明后，再在 PFIOS 中确认审批。

## Approval Status

Default status is `Pending`. Confirm approval in PFIOS only after thesis, code review, data validation, and risk notes are complete.
"""
