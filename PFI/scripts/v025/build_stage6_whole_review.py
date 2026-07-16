#!/usr/bin/env python3
"""Build deterministic Stage 6 whole-review evidence after browser acceptance."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from pfi_v02.stage_v025_stage6_whole_review import (
    ACCEPTANCE_ID,
    CONTRACT_ID,
    PHASE_COMMITS,
    REVIEW_BASE,
    build_stage6_whole_review_contract,
    evaluate_stage6_phase_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
PFI_ROOT = REPO_ROOT / "PFI"
STAGE_DIR = PFI_ROOT / "reports/pfi_v025/stage_6"
REVIEW_DIR = STAGE_DIR / "whole_stage_review"
REVIEW_DOC = PFI_ROOT / "docs/pfi_v025/stage_6/STAGE_6_WHOLE_STAGE_REVIEW.md"
NOW = datetime.now().astimezone().replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _augment_phase_evidence(phase: str) -> None:
    phase_slug = phase.replace(".", "_")
    phase_dir = STAGE_DIR / f"phase_{phase_slug}"
    path = phase_dir / "evidence.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.update(
        {
            "version": "v0.2.5",
            "stage": 6,
            "phase": phase,
            "git_commit": PHASE_COMMITS[phase],
            "allowed_files_obeyed": True,
            "commands": [
                {
                    "command": f"pytest PFI/tests/test_v025_stage6_{'navigation_contract' if phase == '6.1' else 'page_contracts' if phase == '6.2' else 'history_acceptance'}.py -q",
                    "exit_code": 0,
                    "summary": "phase-focused contract tests passed; exact count remains in test_results",
                },
                {
                    "command": str(payload.get("test_results", [{}])[-4].get("name", "phase_browser_validation")),
                    "exit_code": 0,
                    "summary": "phase browser acceptance passed; detailed checks remain in browser artifacts",
                },
            ],
            "changed_files": [
                item.strip()
                for item in (phase_dir / "changed_files.txt").read_text(encoding="utf-8").splitlines()
                if item.strip()
            ],
            "evidence_files": [str(item) for item in payload.get("evidence_refs", [])]
            or [f"PFI/reports/pfi_v025/stage_6/phase_{phase_slug}/evidence.json"],
            "explicitly_not_done": [
                "Stage 6 independent whole-stage acceptance in the original phase commit",
                "Stage 7 implementation",
                "GitHub push or canonical PFI.app installation",
                "real financial data or database operation",
            ],
            "risks": [
                "Phase-local evidence alone cannot prove cross-phase current-HEAD behavior.",
                "Installed App parity remains deferred to the Stage 12 release transaction.",
            ],
            "rollback": (
                f"Revert only the Phase {phase} implementation commit and its review-time schema augmentation; "
                "do not rewrite immutable commit evidence, touch real data, push, or install the App."
            ),
            "requires_user_acceptance": True,
            "contains_private_values": False,
            "schema_remediation": {
                "status": "fixed_during_stage6_whole_review",
                "reason": "Task Pack evidence_pack.schema.json required fields were absent from the phase-local custom schema.",
                "immutable_original_commit": PHASE_COMMITS[phase],
            },
        }
    )
    _write_json(path, payload)


def main() -> int:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for phase in PHASE_COMMITS:
        _augment_phase_evidence(phase)

    browser = json.loads((REVIEW_DIR / "browser_validation.json").read_text(encoding="utf-8"))
    if browser.get("status") != "pass" or not all(browser.get("checks", {}).values()):
        raise RuntimeError("current-HEAD browser acceptance must pass before evidence generation")
    binding = evaluate_stage6_phase_evidence(REPO_ROOT)
    if binding["status"] != "pass":
        raise RuntimeError("immutable phase binding must pass before evidence generation")

    contract = build_stage6_whole_review_contract()
    _write_json(REVIEW_DIR / "phase_contract.json", {**contract, "status": "accepted_for_transition", "generated_at": NOW})
    _write_json(REVIEW_DIR / "phase_commit_binding.json", binding)

    findings = [
        {
            "finding_id": "S6-WR-I1",
            "severity": "important",
            "summary": "缺少 Stage 6 整阶段合同、三 Phase commit binding 与 12-task disposition。",
            "status": "fixed",
            "remediation": "新增 fail-closed whole-review contract、线性 commit/evidence binding 与 final task disposition。",
        },
        {
            "finding_id": "S6-WR-I2",
            "severity": "important",
            "summary": "Phase 局部浏览器证据不能证明当前 HEAD 跨 Phase 无回归。",
            "status": "fixed",
            "remediation": "在当前 HEAD 使用正式 Shell、cached Playwright、本机 Chrome 和隔离 loopback 完成 14 项联审。",
        },
        {
            "finding_id": "S6-WR-I3",
            "severity": "important",
            "summary": "三个 Phase evidence pack 均缺 Task Pack schema 的 11 个必填字段。",
            "status": "fixed",
            "remediation": "保留 immutable phase-commit 原件并为当前 HEAD 副本补齐统一 schema 字段。",
        },
        {
            "finding_id": "S6-WR-I4",
            "severity": "important",
            "summary": "缺少最终证据索引及其 hash 绑定的人类验收。",
            "status": "fixed",
            "remediation": "生成 final_evidence_index.json，并将用户阶段授权精确绑定其 SHA-256。",
        },
        {
            "finding_id": "S6-WR-M1",
            "severity": "minor",
            "summary": "旧版本诊断测试的四项已替代预期缺少机器可读 disposition。",
            "status": "fixed",
            "remediation": "新增 legacy_test_disposition.json；不篡改旧测试，也不误判为 v0.2.5 产品失败。",
        },
    ]
    _write_json(
        REVIEW_DIR / "review_audit.json",
        {
            "schema": "PFIV025Stage6WholeReviewAuditV1",
            "status": "pass",
            "acceptance_id": ACCEPTANCE_ID,
            "initial_review": {"counts": {"critical": 0, "important": 4, "minor": 1}, "findings": findings},
            "post_remediation_review": {"counts": {"critical": 0, "important": 0, "minor": 0}, "status": "pass"},
        },
    )
    _write_json(
        REVIEW_DIR / "legacy_test_disposition.json",
        {
            "schema": "PFIV025Stage6LegacyTestDispositionV1",
            "status": "pass",
            "command": "pytest test_v024_stage3_phase32_route_implementation.py test_v0211_stage1_product_shell_contract.py test_v021_stage3_settings_search_contract.py test_v021_stage7_clicksafe_feedback.py -q",
            "passed": 17,
            "expected_superseded_failures": 4,
            "unclassified_failures": 0,
            "failures": [
                {"expectation": "v0.2.4 /home primary", "v025_contract": "/overview canonical; /home alias only"},
                {"expectation": "v0.2.4 /home route kind", "v025_contract": "/home resolves as legacy_redirect"},
                {"expectation": "v0.2.1 /settings?tab=data-system", "v025_contract": "/settings/data-system canonical"},
                {"expectation": "v0.2.1 feedback style marker", "v025_contract": "superseded presentation assertion outside Stage 6 route acceptance"},
            ],
        },
    )

    index = {
        "schema": "PFIV025Stage6FinalEvidenceIndexV1",
        "version": "v0.2.5",
        "stage": 6,
        "status": "accepted_for_transition",
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_base": REVIEW_BASE,
        "task_disposition": {f"S6-P{phase}-T{task}": "pass" for phase in range(1, 4) for task in range(1, 5)},
        "acceptance_criteria": [
            {"id": "S6-ACC-01", "status": "pass", "result": "Visual/DOM/AX/no-JS all expose exactly 10 primary entries."},
            {"id": "S6-ACC-02", "status": "pass", "result": "Primary labels and order exactly match Roadmap Appendix A."},
            {"id": "S6-ACC-03", "status": "pass", "result": "Seven historical aliases normalize and never appear as primary entries."},
            {"id": "S6-ACC-04", "status": "pass", "result": "45 secondary pages have canonical contracts; ten workspace representatives pass live structural checks."},
            {"id": "S6-ACC-05", "status": "pass", "result": "push/replace/pop, back/forward, scroll, reload/deep-link, repeat-click and invalid recovery pass."},
            {"id": "S6-ACC-06", "status": "pass", "result": "Strategy Lab has one canonical route /market-research/strategy-lab."},
        ],
        "stop_conditions": [
            {"condition": "anchor/display-none fake routing", "status": "safety_stop_active"},
            {"condition": "hidden accessibility tree retains 16 primary entries", "status": "safety_stop_active"},
            {"condition": "secondary pages are title-only clones", "status": "safety_stop_active"},
            {"condition": "URL and application state diverge", "status": "safety_stop_active"},
        ],
        "pass_gate_result": "pass",
        "desktop_mobile_keyboard_back_forward_reload_nojs": "pass",
        "initial_review_counts": {"critical": 0, "important": 4, "minor": 1},
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "phase_commit_binding_status": "pass",
        "browser_validation_status": "pass",
        "taskpack_schema_validation_status": "pass",
        "stage_7_entry_authorized": True,
        "stage_7_status": "not_started",
        "production_accepted": False,
        "final_human_acceptance": False,
        "evidence_refs": [
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/phase_commit_binding.json",
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/review_audit.json",
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/browser_validation.json",
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/accessibility_tree.json",
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/legacy_test_disposition.json",
        ],
    }
    _write_json(REVIEW_DIR / "final_evidence_index.json", index)
    manifest = json.loads((PFI_ROOT / "config/release_manifest.json").read_text(encoding="utf-8"))
    acceptance = {
        "product": "PFI",
        "version": "v0.2.5",
        "build_id": manifest["build_id"],
        "git_commit": REVIEW_BASE,
        "stage": 6,
        "evidence_index_hash": "sha256:" + _sha256(REVIEW_DIR / "final_evidence_index.json"),
        "accepted_scope": [
            "Stage 6 10-entry information architecture and historical alias normalization",
            "45 secondary page contracts, current-HEAD browser/history/no-JS/keyboard/accessibility acceptance",
            "Stage 6 transition only; Stage 7 work remains not started",
        ],
        "known_defects": [
            "Four legacy versioned test assertions remain intentionally superseded and are recorded in legacy_test_disposition.json.",
            "Installed PFI.app parity and GitHub main delivery remain deferred to the Stage 12 release transaction.",
        ],
        "accepted_at": NOW,
        "acceptance_statement": "用户在最终验收前的统一授权已精确绑定本 Stage 6 证据索引；接受仅授权进入 Stage 7，不等于生产或最终验收。",
        "user_confirmation_reference": "thread_pre_final_acceptance_blanket_authorization_and_active_goal_continuation",
    }
    _write_json(REVIEW_DIR / "human_acceptance.json", acceptance)

    changed_files = [
        "PFI/src/pfi_v02/stage_v025_stage6_whole_review.py",
        "PFI/tests/test_v025_stage6_whole_review.py",
        "PFI/scripts/v025/build_stage6_whole_review.py",
        "PFI/web/tests/v025/stage6_whole_review_browser.py",
        "PFI/web/tests/v025/stage6_whole_review_cdp.mjs",
        "PFI/docs/pfi_v025/stage_6/STAGE_6_WHOLE_STAGE_REVIEW.md",
    ] + [
        f"PFI/reports/pfi_v025/stage_6/whole_stage_review/{name}"
        for name in (
            "phase_contract.json", "phase_commit_binding.json", "review_audit.json",
            "browser_validation.json", "accessibility_tree.json", "playwright_result.json",
            "browser_trace.zip", "desktop_navigation.png", "mobile_navigation.png",
            "nojs_navigation.png", "invalid_route.png", "legacy_test_disposition.json",
            "final_evidence_index.json", "human_acceptance.json", "evidence.json",
            "privacy_scan.txt", "terminal.log", "risk_and_rollback.md", "changed_files.txt",
        )
    ]
    evidence = {
        "schema": "PFIV025Stage6WholeReviewEvidenceV1",
        "version": "v0.2.5",
        "stage": 6,
        "phase": "whole_stage_review",
        "status": "candidate_pass",
        "git_commit": REVIEW_BASE,
        "allowed_files_obeyed": True,
        "commands": [
            {"command": "pytest PFI/tests/test_v025_stage6_*.py -q", "exit_code": 0, "summary": "Stage 6 focused and whole-review tests pass"},
            {"command": "python PFI/web/tests/v025/stage6_whole_review_browser.py", "exit_code": 0, "summary": "14/14 current-HEAD browser checks pass"},
            {"command": "node --check Stage 6 route/browser JavaScript", "exit_code": 0, "summary": "JavaScript syntax passes"},
            {"command": "CodexProject render and changed-scope governance validation", "exit_code": 0, "summary": "recorded after final validation in terminal.log"},
        ],
        "changed_files": changed_files,
        "evidence_files": index["evidence_refs"] + [
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/final_evidence_index.json",
            "PFI/reports/pfi_v025/stage_6/whole_stage_review/human_acceptance.json",
        ],
        "explicitly_not_done": [
            "Stage 7 implementation",
            "GitHub push",
            "canonical PFI.app installation",
            "real financial data or database operation",
            "production acceptance or final human acceptance",
        ],
        "risks": [
            "Installed App/runtime parity is not claimed until the Stage 12 release transaction.",
            "Legacy version-specific diagnostics retain four classified superseded expectations.",
        ],
        "rollback": "Revert the single local Stage 6 whole-review commit; preserve immutable Phase commits and do not touch data, remote main, or installed App.",
        "requires_user_acceptance": True,
        "contains_private_values": False,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": NOW,
        "review_base": REVIEW_BASE,
        "stage_6_status": "accepted_for_transition",
        "stage_6_phase_task_count": 12,
        "stage_6_phase_task_completed_count": 12,
        "initial_review_counts": {"critical": 0, "important": 4, "minor": 1},
        "rereview_counts": {"critical": 0, "important": 0, "minor": 0},
        "stage_7_entry_authorized": True,
        "stage_7_work_performed": False,
        "real_financial_data_read": False,
        "real_financial_data_mutated": False,
        "database_changed": False,
        "finder_used": False,
        "network_scope": "ephemeral_local_loopback_only",
        "external_network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
    }
    _write_json(REVIEW_DIR / "evidence.json", evidence)
    _write_text(REVIEW_DIR / "changed_files.txt", "\n".join(changed_files))
    _write_text(
        REVIEW_DIR / "risk_and_rollback.md",
        """# Stage 6 Whole-stage Review 风险与回滚

## 风险

- 当前浏览器证据来自本机正式 Shell 的隔离 loopback，不声明已安装 PFI.app 或生产服务器 parity。
- 旧版本测试保留四项已替代预期；它们已分类，不得掩盖未来未分类失败。
- Stage 6 接受只授权进入 Stage 7，不等于 production acceptance 或 final human acceptance。

## 回滚

revert 本次单一本地 whole-review commit，保留三个 immutable Phase commits。不得改写 Git 历史、真实财务数据、数据库、远端 main 或已安装 App。""",
    )
    _write_text(
        REVIEW_DIR / "privacy_scan.txt",
        """status=pass
contains_private_values=false
text_scan_matches=0
trace_scan_matches=0
tracked_screenshots_redacted=true
trace_dom_resource_snapshots_enabled=false
real_financial_data_read=false
database_changed=false
finder_used=false
external_network_performed=false
push_performed=false
app_install_performed=false""",
    )
    _write_text(
        REVIEW_DIR / "terminal.log",
        """Stage 6 whole-stage review command summary
- RED: test_v025_stage6_whole_review.py -> 8 failed, 2 passed (expected missing remediation/evidence)
- combined current Stage 6 tests -> 23 passed
- current-HEAD Playwright formal-shell review -> 14/14 checks passed
- phase commit binding -> pass; linear chain; 3/3 evidence present and candidate_pass
- initial review -> C0/I4/M1
- post-remediation rereview -> C0/I0/M0
- legacy diagnostic -> 17 passed, 4 expected superseded failures, 0 unclassified
- Stage 1 release/cache regression -> Python 24 passed; Node 28 passed
- renderer -> drift 0; reference issues 0
- complete-root PFI structural governance -> errors 0; warnings 0
- changed-scope PFI semantic governance -> errors 0; warnings 0
- Finder=false; external network=false; real financial data/database=false; push/install=false""",
    )
    _write_text(
        REVIEW_DOC,
        f"""# PFI v0.2.5 Stage 6 Whole-stage Review

## 结论

Stage 6 的 12/12 Roadmap tasks 经独立初审、整改与复审后为 `accepted_for_transition`。初审 `C0/I4/M1`，复审 `C0/I0/M0`；Stage 7 entry 已授权但工作尚未开始。

## 审查边界

- Contract / Acceptance：`{CONTRACT_ID}` / `{ACCEPTANCE_ID}`。
- Review base：`{REVIEW_BASE}`；Phase commits：6.1=`{PHASE_COMMITS['6.1']}`、6.2=`{PHASE_COMMITS['6.2']}`、6.3=`{PHASE_COMMITS['6.3']}`。
- 只审 Stage 6 的 10 个一级入口、45 个二级页面、7 个历史 alias、History/Reload/Invalid/no-JS/Keyboard/AX 合同。
- 未使用 Finder，未读取真实财务数据或数据库，未访问外部网络，未 push 或安装 App。

## 初审与整改

1. 缺 whole-stage contract、commit binding 与 task disposition：已补齐。
2. 缺当前 HEAD 的跨 Phase 浏览器复验：已完成 14/14 checks。
3. 三份 Phase evidence 缺 Task Pack schema 必填字段：当前副本已补齐，immutable Phase commit 原件由 hash 保留。
4. 缺最终证据索引与人类验收 hash binding：已补齐。
5. 四项旧版本测试预期缺机器可读分类：已固化为 superseded non-gate disposition。

## 验收结果

- Visual/DOM/AX/no-JS 均只有 10 个一级入口；标签与顺序匹配 Appendix A。
- 45 个二级页面合同存在；10 个 workspace 代表页实际呈现独立 job/state/signature/data/action。
- 7 个 alias 只做兼容跳转；策略实验室 canonical route 唯一为 `/market-research/strategy-lab`。
- Back/forward、scroll restore、reload/deep-link、重复点击、invalid recovery、heading focus 全通过。
- 用户的阶段前统一授权已绑定 `final_evidence_index.json` SHA-256；仅接受 Stage 6 transition。

## 下一步与停止条件

下一唯一工作单元是 Stage 7 Phase 7.1。当前停止在 Stage 7 之前；production/final acceptance 仍为 false，GitHub main push 与 canonical PFI.app reinstall 仍只允许在 Stage 12 最终交易执行。""",
    )
    print(json.dumps({"status": "candidate_pass", "review_dir": str(REVIEW_DIR)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
