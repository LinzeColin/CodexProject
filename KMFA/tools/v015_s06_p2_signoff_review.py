#!/usr/bin/env python3
"""Local-only private review UI for KMFA v1.5 S06-P2 owner sign-off.

The server is deliberately dependency-free and binds only to 127.0.0.1.  It
never places private candidate content in the tracked tree, never pre-approves
a candidate, and never appends a golden version.  A final sign-off file is
created only after the existing S06-P2 kernel accepts every decision and all
project arithmetic.
"""

from __future__ import annotations

import argparse
import copy
import hmac
import html
import json
import os
import secrets
import stat
import tempfile
import threading
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

from KMFA.tools import v015_s06_p2_golden_baseline_lock as kernel


PRIVATE_DRAFT_PATH = kernel.PRIVATE_OUTPUT_DIR / "private_human_signoff_draft.json"
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_TEXT_LENGTH = 4096
HOST = "127.0.0.1"

TOP_LEVEL_KEYS = frozenset({
    "schema_version", "project_id", "target_release", "phase_id", "packet_digest",
    "baseline_version", "previous_record_hash", "correction_reason", "confirmer",
    "authorization_statement", "decision_rows",
})
CONFIRMER_KEYS = frozenset({"identity", "role", "confirmed_at", "basis"})
DECISION_KEYS = frozenset({
    "candidate_id", "decision", "project_ref", "canonical_value", "unit", "tax_status",
    "business_meaning", "confirmed_source_locator", "category_key", "rejection_reason",
})


class ReviewError(RuntimeError):
    """Stable fail-closed review transport error."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReviewError(f"private JSON unavailable or invalid: {path.name}") from error
    _require(isinstance(value, dict), f"private JSON object required: {path.name}")
    return value


def _optional_text(value: Any, field: str) -> None:
    _require(value is None or isinstance(value, str), f"{field} must be text or null")
    if isinstance(value, str):
        _require(len(value) <= MAX_TEXT_LENGTH, f"{field} is too long")


def validate_draft(draft: dict[str, Any], packet: dict[str, Any]) -> None:
    """Validate an incomplete UI draft without treating it as a sign-off."""

    kernel.validate_candidate_packet(packet)
    _require(set(draft) == TOP_LEVEL_KEYS, "draft top-level scope mismatch")
    for key, expected in (
        ("schema_version", kernel.PRIVATE_SIGNOFF_SCHEMA),
        ("project_id", "KMFA"),
        ("target_release", "v1.5"),
        ("phase_id", kernel.RUN_PHASE_ID),
        ("packet_digest", packet["packet_digest"]),
    ):
        _require(draft.get(key) == expected, f"draft {key} binding mismatch")
    _require(draft.get("baseline_version") == "S06P2-GOLDEN-0001", "draft baseline version mismatch")
    _require(draft.get("previous_record_hash") is None, "initial draft previous hash must be null")
    _optional_text(draft.get("correction_reason"), "correction_reason")
    _require(
        draft.get("authorization_statement") in {None, kernel.AUTHORIZATION_STATEMENT},
        "authorization statement is invalid",
    )

    confirmer = draft.get("confirmer")
    _require(isinstance(confirmer, dict) and set(confirmer) == CONFIRMER_KEYS, "confirmer scope mismatch")
    for key in CONFIRMER_KEYS:
        _optional_text(confirmer.get(key), f"confirmer.{key}")

    candidates = {row["candidate_id"]: row for row in packet["candidate_records"]}
    decisions = draft.get("decision_rows")
    _require(isinstance(decisions, list), "decision_rows must be a list")
    _require(len(decisions) == len(candidates), "draft must preserve every candidate row")
    _require(all(isinstance(row, dict) for row in decisions), "decision row must be an object")
    _require(all(set(row) == DECISION_KEYS for row in decisions), "decision row scope mismatch")
    identifiers = [row.get("candidate_id") for row in decisions]
    _require(len(set(identifiers)) == len(identifiers), "draft decision IDs are not unique")
    _require(set(identifiers) == set(candidates), "draft decision scope differs from packet")

    for decision in decisions:
        candidate = candidates[decision["candidate_id"]]
        status = decision.get("decision")
        _require(status in {"PENDING", "ACCEPT", "REJECT"}, "unknown draft decision")
        for field in (
            "project_ref", "canonical_value", "unit", "tax_status", "business_meaning",
            "confirmed_source_locator", "category_key", "rejection_reason",
        ):
            _optional_text(decision.get(field), field)
        unit = decision.get("unit")
        _require(unit in {None, kernel.EXPECTED_UNITS[candidate["field_family"]]}, "draft unit mismatch")
        _require(decision.get("tax_status") in {None, *kernel.ALLOWED_TAX_STATUS}, "draft tax status invalid")
        locator = decision.get("confirmed_source_locator")
        _require(locator in {None, candidate["source_locator"]}, "draft source locator mismatch")
        canonical = decision.get("canonical_value")
        if canonical is not None and candidate["field_family"] != "PROJECT_IDENTITY":
            _require(canonical and canonical.lstrip("-").isdigit(), "numeric canonical value must be integer text")
            _require(len(canonical.lstrip("-")) <= 30, "numeric canonical value is too long")


def _materialize_signoff(draft: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    """Convert exact integer text to Python integers only for final validation."""

    validate_draft(draft, packet)
    signoff = copy.deepcopy(draft)
    candidates = {row["candidate_id"]: row for row in packet["candidate_records"]}
    for decision in signoff["decision_rows"]:
        family = candidates[decision["candidate_id"]]["field_family"]
        if decision.get("canonical_value") is not None and family != "PROJECT_IDENTITY":
            decision["canonical_value"] = int(decision["canonical_value"])
    return signoff


def _private_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _require(not path.parent.is_symlink(), "private output directory cannot be a symlink")
    os.chmod(path.parent, 0o700)
    _require(stat.S_IMODE(path.parent.stat().st_mode) == 0o700, "private output directory must be 0700")


def _atomic_private_json(path: Path, value: dict[str, Any]) -> None:
    """Atomically replace a private draft with a mode-0600 regular file."""

    _private_parent(path)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    _require(path.is_file() and not path.is_symlink(), "private draft must be a regular file")
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "private draft must be 0600")


def _create_private_json(path: Path, value: dict[str, Any]) -> None:
    """Create a final sign-off exactly once; never overwrite an existing record."""

    _private_parent(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as error:
        raise ReviewError("final sign-off already exists and cannot be overwritten") from error
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as error:
        if descriptor >= 0:
            os.close(descriptor)
        path.unlink(missing_ok=True)
        raise ReviewError("final sign-off could not be written") from error
    os.chmod(path, 0o600)
    _require(path.is_file() and not path.is_symlink(), "final sign-off must be a regular file")
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "final sign-off must be 0600")


def _decision_counts(draft: dict[str, Any]) -> dict[str, int]:
    counts = Counter(row["decision"] for row in draft["decision_rows"])
    return {key: counts.get(key, 0) for key in ("PENDING", "ACCEPT", "REJECT")}


class ReviewState:
    def __init__(self, packet_path: Path, template_path: Path, draft_path: Path, signoff_path: Path) -> None:
        self.packet_path = packet_path
        self.template_path = template_path
        self.draft_path = draft_path
        self.signoff_path = signoff_path
        self.packet = _read_json(packet_path)
        kernel.validate_candidate_packet(self.packet)
        template = _read_json(template_path)
        validate_draft(template, self.packet)
        self.draft = _read_json(draft_path) if draft_path.exists() else template
        validate_draft(self.draft, self.packet)
        self._lock = threading.RLock()

    def public_to_local_state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "packet": self.packet,
                "draft": self.draft,
                "decision_counts": _decision_counts(self.draft),
                "authorization_statement": kernel.AUTHORIZATION_STATEMENT,
                "final_signoff_exists": self.signoff_path.exists(),
                "golden_version_appended": kernel.PRIVATE_VERSION_LEDGER_PATH.exists(),
            }

    def save_draft(self, draft: dict[str, Any]) -> dict[str, int]:
        with self._lock:
            validate_draft(draft, self.packet)
            try:
                _atomic_private_json(self.draft_path, draft)
            except OSError as error:
                raise ReviewError("private draft could not be written") from error
            self.draft = copy.deepcopy(draft)
            return _decision_counts(self.draft)

    def finalize(self, draft: dict[str, Any], confirmation: Any) -> dict[str, int]:
        with self._lock:
            _require(
                confirmation == kernel.AUTHORIZATION_STATEMENT,
                "typed final authorization statement does not match",
            )
            signoff = _materialize_signoff(draft, self.packet)
            _require(
                signoff.get("authorization_statement") == kernel.AUTHORIZATION_STATEMENT,
                "draft authorization statement is missing",
            )
            try:
                accepted = kernel.validate_signoff(signoff, self.packet)
                summaries = kernel.build_project_summaries(accepted)
            except kernel.GoldenBaselineError as error:
                raise ReviewError(str(error)) from error
            _require(not self.signoff_path.exists(), "final sign-off already exists and cannot be overwritten")
            try:
                _atomic_private_json(self.draft_path, draft)
            except OSError as error:
                raise ReviewError("private draft could not be written") from error
            _create_private_json(self.signoff_path, signoff)
            self.draft = copy.deepcopy(draft)
            return {
                "accepted_field_count": len(accepted),
                "resolved_candidate_count": len(signoff["decision_rows"]),
                "project_summary_count": len(summaries),
            }


def _review_html(token: str, nonce: str) -> str:
    token_json = json.dumps(token)
    authorization_json = json.dumps(kernel.AUTHORIZATION_STATEMENT)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>KMFA v1.5 S06-P2 私有签署复核</title>
  <style nonce="{html.escape(nonce)}">
    :root {{ color-scheme: light; --ink:#15211b; --muted:#62706a; --line:#d8e0dc; --bg:#eef3f0; --panel:#fff; --green:#176b45; --amber:#aa6400; --red:#a12b2b; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    header {{ position:sticky; top:0; z-index:4; background:#102b20; color:#fff; padding:18px 24px; box-shadow:0 2px 14px #0002; }}
    header h1 {{ margin:0 0 4px; font-size:20px; }} header p {{ margin:0; color:#cbe0d5; }}
    main {{ max-width:1500px; margin:20px auto 60px; padding:0 20px; }}
    .warning {{ background:#fff5df; border:1px solid #e9c46b; border-radius:10px; padding:12px 14px; margin-bottom:16px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-bottom:16px; }}
    .stat,.panel,.candidate {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; }}
    .stat {{ padding:14px; }} .stat strong {{ display:block; font-size:24px; }} .stat span {{ color:var(--muted); }}
    .panel {{ padding:16px; margin-bottom:16px; }} .panel h2 {{ margin:0 0 12px; font-size:17px; }}
    .formgrid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }}
    label {{ display:block; color:var(--muted); font-size:12px; }} input,select,textarea,button {{ font:inherit; }}
    input,select,textarea {{ width:100%; margin-top:5px; padding:9px 10px; color:var(--ink); background:#fff; border:1px solid #bcc9c2; border-radius:8px; }}
    textarea {{ min-height:76px; resize:vertical; }} button {{ border:0; border-radius:8px; padding:9px 14px; cursor:pointer; background:#dfe8e3; color:var(--ink); font-weight:600; }}
    button.primary {{ background:var(--green); color:#fff; }} button.danger {{ background:var(--red); color:#fff; }} button:disabled {{ cursor:not-allowed; opacity:.5; }}
    .toolbar {{ display:grid; grid-template-columns:2fr 1.35fr 1fr 1fr auto; gap:10px; align-items:end; }}
    .source-info {{ margin:12px 0 4px; color:var(--muted); }}
    .candidate {{ padding:14px; margin:10px 0; }} .candidate-head {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px; }}
    .tag {{ border-radius:999px; padding:3px 8px; background:#e5ece8; font-size:12px; }} .candidate-id {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; color:var(--muted); }}
    .private-value {{ white-space:pre-wrap; overflow-wrap:anywhere; background:#f3f6f4; border-radius:8px; padding:9px; margin:7px 0; }}
    .rowgrid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:10px; }}
    .wide {{ grid-column:1/-1; }} .inline {{ display:flex; gap:8px; align-items:center; }} .inline input[type=checkbox] {{ width:auto; margin:0; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:9px; align-items:center; }} #message {{ color:var(--muted); }} .error {{ color:var(--red)!important; }} .success {{ color:var(--green)!important; }}
    .pager {{ display:flex; justify-content:space-between; align-items:center; margin-top:12px; }} code {{ overflow-wrap:anywhere; }}
    @media (max-width:900px) {{ .grid,.formgrid,.rowgrid,.toolbar {{ grid-template-columns:1fr; }} .wide {{ grid-column:auto; }} }}
  </style>
</head>
<body>
<header><h1>KMFA v1.5 · S06-P2 私有签署复核</h1><p>localhost-only · 保存草稿不等于签署 · 签署不等于黄金版本锁定</p></header>
<main>
  <div class="warning"><strong>复核方式：</strong>先按来源逐组处理，再按“待决定”检查遗漏。页面只应在本机打开，不得截图外传或复制到 Git。工具不会预选 ACCEPT，也不会自动推断项目、金额、税口径或业务含义。</div>
  <section class="grid">
    <div class="stat"><strong id="total">—</strong><span>候选总数</span></div>
    <div class="stat"><strong id="pending">—</strong><span>待决定</span></div>
    <div class="stat"><strong id="accepted">—</strong><span>接受</span></div>
    <div class="stat"><strong id="rejected">—</strong><span>拒绝</span></div>
  </section>
  <section class="panel">
    <h2>确认人信息</h2>
    <div class="formgrid">
      <label>确认人身份<input id="identity" autocomplete="off"></label>
      <label>角色<input id="role" autocomplete="off"></label>
      <label>确认时间（必须含时区）<div class="inline"><input id="confirmedAt" placeholder="2026-07-15T10:00:00+10:00"><button id="now" type="button">使用当前时间</button></div></label>
      <label>确认依据<textarea id="basis" placeholder="说明逐源复核依据"></textarea></label>
    </div>
  </section>
  <section class="panel">
    <h2>候选复核</h2>
    <div class="toolbar">
      <label>搜索<input id="search" placeholder="ID、字段族、来源、定位或候选文本"></label>
      <label>来源分组<select id="source"><option value="">全部来源</option></select></label>
      <label>字段族<select id="family"><option value="">全部</option></select></label>
      <label>决定<select id="decision"><option value="">全部</option><option>PENDING</option><option>ACCEPT</option><option>REJECT</option></select></label>
      <button id="resetFilters" type="button">清除筛选</button>
    </div>
    <p id="sourceInfo" class="source-info"></p>
    <div id="list"></div>
    <div class="pager"><button id="prev" type="button">上一页</button><span id="pageInfo"></span><button id="next" type="button">下一页</button></div>
  </section>
  <section class="panel">
    <h2>保存与最终签署</h2>
    <p>最终签署要求全部候选均为 ACCEPT/REJECT，并通过项目汇总与 0 分差异校验。成功后仅创建不可覆盖的 <code>private_human_signoff.json</code>，仍不会追加黄金版本。</p>
    <label>输入精确授权语句以完成最终签署<input id="authorization" autocomplete="off" spellcheck="false"></label>
    <p><code id="authorizationHint"></code></p>
    <div class="actions"><button class="primary" id="save" type="button">保存私有草稿</button><button class="danger" id="finalize" type="button">校验并创建最终签署</button><span id="message"></span></div>
  </section>
</main>
<script nonce="{html.escape(nonce)}">
(() => {{
  'use strict';
  const TOKEN = {token_json};
  const AUTH = {authorization_json};
  const PAGE_SIZE = 15;
  const FAMILY_LABELS = {{PROJECT_IDENTITY:'项目身份',CONTRACT_AMOUNT:'合同额',TOTAL_EXPENDITURE:'总支出',GROSS_PROFIT:'毛利润',GROSS_MARGIN:'毛利率',COST_CATEGORY:'成本分类'}};
  const ROLE_LABELS = {{PRIMARY_FIELD:'主字段',CROSS_SOURCE_PRIMARY_FIELD:'跨来源主字段',TOP_LEVEL_CATEGORY:'一级成本',INTERMEDIATE_TOTAL:'中间汇总',IDENTITY_COMPONENT:'身份组成'}};
  const SOURCE_ROLE_LABELS = {{AUTHORITATIVE_PROJECT_COST_PDF:'项目成本 PDF',AUTHORITATIVE_PROJECT_COST_WORKBOOK:'项目成本工作簿'}};
  const UNIT_LABELS = {{TEXT:'文本',CNY_CENT:'人民币分',BASIS_POINT:'基点'}};
  let packet, draft, candidates, rowsById, page = 1;
  const $ = id => document.getElementById(id);
  const text = (node, value) => {{ node.textContent = value == null ? '' : String(value); }};
  const api = async (path, options={{}}) => {{
    const response = await fetch(path, {{...options, headers:{{'X-KMFA-Review-Token':TOKEN, ...(options.headers||{{}})}}}});
    const body = await response.json().catch(() => ({{error:'响应格式错误'}}));
    if (!response.ok) throw new Error(body.error || `HTTP ${{response.status}}`);
    return body;
  }};
  const field = (labelText, value, onChange, kind='input') => {{
    const label=document.createElement('label'); text(label,labelText);
    const input=document.createElement(kind); input.value=value ?? '';
    input.addEventListener('change', () => onChange(input.value)); label.appendChild(input); return label;
  }};
  const selectField = (labelText, value, choices, onChange) => {{
    const label=document.createElement('label'); text(label,labelText); const select=document.createElement('select');
    for (const [optionValue, optionText] of choices) {{ const option=document.createElement('option'); option.value=optionValue; text(option,optionText); select.appendChild(option); }}
    select.value=value ?? ''; select.addEventListener('change',()=>onChange(select.value)); label.appendChild(select); return label;
  }};
  const updateCounts = () => {{
    const counts={{PENDING:0,ACCEPT:0,REJECT:0}}; for (const row of draft.decision_rows) counts[row.decision]++;
    text($('total'), draft.decision_rows.length); text($('pending'),counts.PENDING); text($('accepted'),counts.ACCEPT); text($('rejected'),counts.REJECT);
  }};
  const filtered = () => {{
    const query=$('search').value.trim().toLocaleLowerCase(); const source=$('source').value; const family=$('family').value; const decision=$('decision').value;
    return candidates.filter(candidate => {{ const row=rowsById.get(candidate.candidate_id);
      const hay=[candidate.candidate_id,candidate.field_family,FAMILY_LABELS[candidate.field_family],candidate.source_ref,candidate.source_role,candidate.candidate_role,candidate.source_locator,candidate.raw_text,candidate.cached_display_value].join(' ').toLocaleLowerCase();
      return (!query || hay.includes(query)) && (!source || candidate.source_ref===source) && (!family || candidate.field_family===family) && (!decision || row.decision===decision);
    }});
  }};
  const render = () => {{
    updateCounts(); const matches=filtered(); const pages=Math.max(1,Math.ceil(matches.length/PAGE_SIZE)); page=Math.min(page,pages);
    const activeSource=$('source').value; const sourceRows=activeSource?candidates.filter(candidate=>candidate.source_ref===activeSource):candidates;
    const sourcePending=sourceRows.filter(candidate=>rowsById.get(candidate.candidate_id).decision==='PENDING').length;
    const sourceCount=new Set(candidates.map(candidate=>candidate.source_ref)).size;
    text($('sourceInfo'),activeSource?`${{activeSource}} · ${{SOURCE_ROLE_LABELS[sourceRows[0]?.source_role]||sourceRows[0]?.source_role||'来源'}} · ${{sourceRows.length}} 条 · 待决定 ${{sourcePending}} 条`:`共 ${{sourceCount}} 个来源；建议逐个来源完成，再筛选 PENDING 检查遗漏。`);
    const list=$('list'); list.replaceChildren(); const slice=matches.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE);
    for (const candidate of slice) {{ const row=rowsById.get(candidate.candidate_id); const card=document.createElement('article'); card.className='candidate';
      const head=document.createElement('div'); head.className='candidate-head';
      const tags=[`${{FAMILY_LABELS[candidate.field_family]||candidate.field_family}} · ${{candidate.field_family}}`,`${{UNIT_LABELS[candidate.expected_canonical_unit]||candidate.expected_canonical_unit}}`,SOURCE_ROLE_LABELS[candidate.source_role]||candidate.source_role,ROLE_LABELS[candidate.candidate_role]||candidate.candidate_role,candidate.candidate_id].filter(Boolean);
      for (const value of tags) {{ const span=document.createElement('span'); span.className=value===candidate.candidate_id?'candidate-id':'tag'; text(span,value); head.appendChild(span); }} card.appendChild(head);
      for (const [labelText,value] of [['来源',candidate.source_ref],['定位',candidate.source_locator],['候选文本',candidate.raw_text ?? candidate.cached_display_value ?? '']]) {{ const label=document.createElement('strong'); text(label,labelText); card.appendChild(label); const block=document.createElement('div'); block.className='private-value'; text(block,value); card.appendChild(block); }}
      const grid=document.createElement('div'); grid.className='rowgrid';
      grid.appendChild(selectField('决定',row.decision,[['PENDING','PENDING'],['ACCEPT','ACCEPT'],['REJECT','REJECT']],value=>{{row.decision=value; render();}}));
      if (row.decision==='ACCEPT') {{
        grid.appendChild(field('项目引用',row.project_ref,value=>row.project_ref=value||null));
        grid.appendChild(field(candidate.field_family==='PROJECT_IDENTITY'?'规范文本':'规范整数值',row.canonical_value,value=>row.canonical_value=value||null));
        grid.appendChild(selectField('单位',row.unit,[['','请选择'],[candidate.expected_canonical_unit,candidate.expected_canonical_unit]],value=>row.unit=value||null));
        grid.appendChild(selectField('税口径',row.tax_status,[['','请选择'],['TAX_INCLUDED','TAX_INCLUDED'],['TAX_EXCLUDED','TAX_EXCLUDED'],['SOURCE_NOT_STATED','原资料未说明'],['NOT_APPLICABLE','不适用']],value=>row.tax_status=value||null));
        grid.appendChild(field('业务含义',row.business_meaning,value=>row.business_meaning=value||null,'textarea'));
        if (candidate.field_family==='COST_CATEGORY') grid.appendChild(field('成本类别 key',row.category_key,value=>row.category_key=value||null));
        const locatorLabel=document.createElement('label'); locatorLabel.className='inline wide'; const checkbox=document.createElement('input'); checkbox.type='checkbox'; checkbox.checked=row.confirmed_source_locator===candidate.source_locator; checkbox.addEventListener('change',()=>{{row.confirmed_source_locator=checkbox.checked?candidate.source_locator:null;}}); locatorLabel.appendChild(checkbox); locatorLabel.appendChild(document.createTextNode(' 我已核对并确认使用上述来源定位')); grid.appendChild(locatorLabel);
      }} else if (row.decision==='REJECT') {{ const reason=field('拒绝原因',row.rejection_reason,value=>row.rejection_reason=value||null,'textarea'); reason.className='wide'; grid.appendChild(reason); }}
      card.appendChild(grid); list.appendChild(card);
    }}
    text($('pageInfo'),`第 ${{page}} / ${{pages}} 页 · 筛选后 ${{matches.length}} 条`); $('prev').disabled=page<=1; $('next').disabled=page>=pages;
  }};
  const applyGlobals = () => {{
    draft.confirmer.identity=$('identity').value.trim()||null; draft.confirmer.role=$('role').value.trim()||null;
    draft.confirmer.confirmed_at=$('confirmedAt').value.trim()||null; draft.confirmer.basis=$('basis').value.trim()||null;
    draft.authorization_statement=$('authorization').value.trim()||null;
  }};
  const message = (value, kind='') => {{ text($('message'),value); $('message').className=kind; }};
  const init = async () => {{
    const state=await api('/api/state'); packet=state.packet; draft=state.draft;
    candidates=[...packet.candidate_records].sort((left,right)=>[left.source_ref,left.field_family,left.candidate_role||'',left.source_locator].join('\u0000').localeCompare([right.source_ref,right.field_family,right.candidate_role||'',right.source_locator].join('\u0000'),'zh-CN'));
    rowsById=new Map(draft.decision_rows.map(row=>[row.candidate_id,row]));
    $('identity').value=draft.confirmer.identity??''; $('role').value=draft.confirmer.role??''; $('confirmedAt').value=draft.confirmer.confirmed_at??''; $('basis').value=draft.confirmer.basis??''; $('authorization').value=draft.authorization_statement??''; text($('authorizationHint'),AUTH);
    const bySource=new Map(); for (const candidate of candidates) {{ if (!bySource.has(candidate.source_ref)) bySource.set(candidate.source_ref,{{count:0,role:candidate.source_role}}); bySource.get(candidate.source_ref).count++; }}
    for (const [sourceRef,summary] of bySource) {{ const option=document.createElement('option'); option.value=sourceRef; text(option,`${{sourceRef}} · ${{SOURCE_ROLE_LABELS[summary.role]||summary.role||'来源'}} · ${{summary.count}} 条`); $('source').appendChild(option); }}
    for (const family of Object.keys(packet.field_family_counts).sort()) {{ const option=document.createElement('option'); option.value=family; text(option,family); $('family').appendChild(option); }}
    if (state.final_signoff_exists) {{ $('finalize').disabled=true; message('最终签署已存在；此界面不会覆盖。','success'); }}
    render(); window.__KMFA_REVIEW_READY__=true;
  }};
  for (const id of ['search','source','family','decision']) $(id).addEventListener(id==='search'?'input':'change',()=>{{page=1;render();}});
  $('resetFilters').addEventListener('click',()=>{{$('search').value='';$('source').value='';$('family').value='';$('decision').value='';page=1;render();}});
  $('prev').addEventListener('click',()=>{{page--;render();window.scrollTo(0,300);}}); $('next').addEventListener('click',()=>{{page++;render();window.scrollTo(0,300);}});
  $('now').addEventListener('click',()=>{{$('confirmedAt').value=new Date().toISOString();}});
  $('save').addEventListener('click',async()=>{{ try {{ applyGlobals(); const result=await api('/api/draft',{{method:'PUT',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{draft}})}}); message(`草稿已保存：PENDING ${{result.decision_counts.PENDING}} / ACCEPT ${{result.decision_counts.ACCEPT}} / REJECT ${{result.decision_counts.REJECT}}`,'success'); }} catch(error) {{ message(error.message,'error'); }} }});
  $('finalize').addEventListener('click',async()=>{{ try {{ applyGlobals(); const result=await api('/api/finalize',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{signoff:draft,confirmation:$('authorization').value.trim()}})}}); $('finalize').disabled=true; message(`最终签署已创建：${{result.resolved_candidate_count}} 项已解决，${{result.accepted_field_count}} 项接受；黄金版本仍未锁定。`,'success'); }} catch(error) {{ message(error.message,'error'); }} }});
  init().catch(error=>message(error.message,'error'));
}})();
</script>
</body>
</html>
"""


class ReviewHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], state: ReviewState, token: str) -> None:
        _require(address[0] == HOST, "review server may bind only to 127.0.0.1")
        self.state = state
        self.review_token = token
        self.csp_nonce = secrets.token_urlsafe(24)
        super().__init__(address, ReviewHandler)
        port = self.server_address[1]
        self.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        self.allowed_origin = f"http://127.0.0.1:{port}"

    @property
    def review_url(self) -> str:
        return f"{self.allowed_origin}/review/{self.review_token}"


class ReviewHandler(BaseHTTPRequestHandler):
    server: ReviewHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return

    def _base_allowed(self) -> bool:
        return self.client_address[0] == HOST and self.headers.get("Host") in self.server.allowed_hosts

    def _token_allowed(self) -> bool:
        provided = self.headers.get("X-KMFA-Review-Token", "")
        return hmac.compare_digest(provided, self.server.review_token)

    def _security_headers(self, content_type: str, length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", f"default-src 'none'; script-src 'nonce-{self.server.csp_nonce}'; style-src 'nonce-{self.server.csp_nonce}'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")

    def _send(self, status: HTTPStatus, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self._security_headers(content_type, len(payload))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send(status, payload, "application/json; charset=utf-8")

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"error": message})

    def _request_json(self) -> dict[str, Any]:
        _require(self.headers.get("Content-Type", "").split(";", 1)[0] == "application/json", "application/json required")
        length_text = self.headers.get("Content-Length")
        _require(length_text is not None and length_text.isdigit(), "valid Content-Length required")
        length = int(length_text)
        _require(0 < length <= MAX_BODY_BYTES, "request body size is invalid")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ReviewError("request JSON is invalid") from error
        _require(isinstance(value, dict), "request JSON object required")
        return value

    def _write_allowed(self) -> bool:
        return self._base_allowed() and self._token_allowed() and self.headers.get("Origin") == self.server.allowed_origin

    def do_GET(self) -> None:  # noqa: N802
        if not self._base_allowed():
            self._error(HTTPStatus.NOT_FOUND, "not found")
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "private_data": False})
            return
        if path == f"/review/{self.server.review_token}":
            payload = _review_html(self.server.review_token, self.server.csp_nonce).encode("utf-8")
            self._send(HTTPStatus.OK, payload, "text/html; charset=utf-8")
            return
        if path == "/api/state" and self._token_allowed():
            self._json(HTTPStatus.OK, self.server.state.public_to_local_state())
            return
        self._error(HTTPStatus.NOT_FOUND, "not found")

    def do_PUT(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/draft" or not self._write_allowed():
            self._error(HTTPStatus.FORBIDDEN, "write request rejected")
            return
        try:
            request = self._request_json()
            _require(set(request) == {"draft"} and isinstance(request["draft"], dict), "draft request scope mismatch")
            counts = self.server.state.save_draft(request["draft"])
        except ReviewError as error:
            self._error(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._json(HTTPStatus.OK, {"saved": True, "decision_counts": counts, "finalized": False})

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/api/finalize" or not self._write_allowed():
            self._error(HTTPStatus.FORBIDDEN, "write request rejected")
            return
        try:
            request = self._request_json()
            _require(set(request) == {"signoff", "confirmation"}, "finalize request scope mismatch")
            _require(isinstance(request["signoff"], dict), "signoff object required")
            result = self.server.state.finalize(request["signoff"], request["confirmation"])
        except ReviewError as error:
            status = HTTPStatus.CONFLICT if "already exists" in str(error) else HTTPStatus.BAD_REQUEST
            self._error(status, str(error))
            return
        self._json(HTTPStatus.CREATED, {"finalized": True, "golden_version_appended": False, **result})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._error(HTTPStatus.METHOD_NOT_ALLOWED, "cross-origin preflight is not supported")


def build_server(
    packet_path: Path = kernel.PRIVATE_PACKET_PATH,
    template_path: Path = kernel.PRIVATE_SIGNOFF_TEMPLATE_PATH,
    draft_path: Path = PRIVATE_DRAFT_PATH,
    signoff_path: Path = kernel.PRIVATE_SIGNOFF_PATH,
    *,
    host: str = HOST,
    port: int = 0,
    token: str | None = None,
) -> ReviewHTTPServer:
    _require(host == HOST, "review server may bind only to 127.0.0.1")
    review_token = token or secrets.token_urlsafe(32)
    _require(len(review_token) >= 32, "review token is too short")
    state = ReviewState(packet_path, template_path, draft_path, signoff_path)
    return ReviewHTTPServer((host, port), state, review_token)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KMFA v1.5 S06-P2 localhost-only private sign-off review UI")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--packet-path", type=Path, default=kernel.PRIVATE_PACKET_PATH)
    parser.add_argument("--template-path", type=Path, default=kernel.PRIVATE_SIGNOFF_TEMPLATE_PATH)
    parser.add_argument("--draft-path", type=Path, default=PRIVATE_DRAFT_PATH)
    parser.add_argument("--signoff-path", type=Path, default=kernel.PRIVATE_SIGNOFF_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)
    token = None
    if os.environ.get("KMFA_V015_S06_P2_TEST_MODE") == "1":
        token = os.environ.get("KMFA_V015_S06_P2_REVIEW_TOKEN")
    server = build_server(
        args.packet_path, args.template_path, args.draft_path, args.signoff_path,
        host=args.host, port=args.port, token=token,
    )
    print(f"PRIVATE REVIEW URL (do not share): {server.review_url}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
