# Delivery Package Manifest 2026-06-14

交付包目标：让任何 agent 在没有本线程上下文和本机历史记录的情况下，能继续开发、审查、运行和验证 TAB FIFA 盘口研究系统。

最新交付包命名：`/Users/linzezhang/Downloads/FIFA Report/FIFA_agent_review_package_14062026_<git-short-sha>.zip`
对应 Git commit：以 ZIP 文件名中的 short sha 为准，或在解压后的仓库根目录运行 `git rev-parse HEAD`。

## 包含内容

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 项目级开发规则 |
| `README.md` | 仓库入口说明 |
| `tab-research-pipeline/` | 当前主系统完整源码、测试、脚本、配置模板、README/RUNBOOK、app icon assets |
| `docs/HANDOFF.md` | 当前状态、关键决策、验证结果、下一步 |
| `tab-research-pipeline/HANDOFF.md` | pipeline 内部交接摘要 |
| `docs/DEVELOPMENT_STATUS.md` | 当前交付状态和历史验证摘要 |
| `docs/PARALLEL_REVIEW_SUMMARY_20260613.md` | 并行审查结论、严重程度、修复状态 |
| `docs/FEATURE_LIST.md` | 功能清单 |
| `docs/DELIVERY_STANDARDS.md` | 交付标准、运行方式、合并 gate |
| `docs/DELIVERY_PACKAGE_MANIFEST_20260614.md` | 本交付包清单 |
| `docs/FILE_RETENTION_POLICY.md` | 本地保留/清理策略 |
| `artifacts/latest/` | public-safe latest 状态产物，包含 provider KPI、coverage、raw manifest、manual verification 状态 |
| `artifacts/backups/` | 已压缩备份，不含私有凭据 |
| `ops/local_cleanup_*` | 本地瘦身审计 |
| `legacy/` | 旧版系统源码，供兼容参考 |

## 不包含

- `.git/`
- `__pycache__/`
- `*.pyc`
- `.venv/`
- `node_modules/`
- `work/private/`
- `tab-research-pipeline/config/odds_providers.local.env`
- TAB 密码、OTP、session secret、私有持仓明细原始文本

## 必须先读

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `tab-research-pipeline/HANDOFF.md`
4. `docs/DEVELOPMENT_STATUS.md`
5. `docs/FEATURE_LIST.md`
6. `docs/DELIVERY_STANDARDS.md`

## 当前验收快照

- App URL: `http://127.0.0.1:8767/`
- Runtime cwd: `github_sync/FIFA/tab-research-pipeline`
- Python tests: full suite `196 tests OK`；本轮新增 provider KPI same-refresh rebuild、stale blocked-attempt labeling、persistent low-yield Team Total evidence across primary refresh 与 provider alternate-plan status API regression tests OK
- Downloads HTML/App rebuilt: yes
- In-app browser smoke: desktop `1280px` and mobile `390px` no horizontal overflow; Provider 配置医生 visible; Team Total pair-template buttons visible; console error `0`
- API smoke: `/api/status.provider_config_doctor` returns `ready`, no legacy sport, recommended sport `soccer_fifa_world_cup`, event probe limit `0`, stake `AUD 0`
- API smoke: `/api/status.provider_manual_overlay_publish` returns blocked publish-preflight state with stake `AUD 0`
- API smoke: `/api/status.provider_manual_workbench` returns `waiting_for_first_batch`, batch `TT-001`, remaining `68`, high priority remaining `55`, pair rows `136/16`, stake `AUD 0`
- Current raw state: blocked by `ai_controlled_access_rejected`
- Provider config doctor: status `ready`; local env exists; keys present but redacted; sports discovery enabled; no legacy sport; recommended sport `soccer_fifa_world_cup`; event probe limit `0`; artifact `artifacts/latest/provider_config_doctor_latest.*`
- Provider latest refresh: `20260613T173737Z-provider-e531900e`
- Provider coverage: Result `68/68`, Handicap `47/68`, Total O/U `55/68`, Team Total O/U `0/68`
- Provider request usage: payload `1`; request kinds `odds=1`; reported used `204`; remaining `296`; last cost `3`
- Provider raw manifest: `artifacts/latest/odds_provider_raw_latest.json`
- Alternate plan: Team Total default probe queue `0`; fallback queue `68`; next batch `0`; estimated credits `0-0`; status `fallback_required`; operational decision `manual_or_official_provider_priority`; persistent evidence artifact `artifacts/latest/provider_alternate_probe_evidence_latest.json`
- Alternate event-market evidence: sampled events `3`; Team Total available sample `0`; Total O/U available sample `3`; this evidence persists across primary-only refreshes and prevents blind The Odds API Team Total probing.
- Fallback verification: queue `68`; high priority `55`; status `provider_blocked_manual_verification_required`; artifact `artifacts/latest/provider_fallback_verification_latest.*`
- Manual verification import: template `artifacts/latest/provider_manual_verification_template_latest.csv`; template rows `68`; pair template `artifacts/latest/provider_manual_pair_template_latest.csv`; pair rows `136`; next-batch pair template `artifacts/latest/provider_manual_next_batch_pair_template_latest.csv`; next-batch pair rows `16`; status `import_missing`; complete `0/68`; high priority complete `0/55`; invalid rows `0`; artifact `artifacts/latest/provider_manual_verification_status_latest.*`
- Manual verification workbench: status `waiting_for_first_batch`; batch count `9`; next batch `TT-001`; remaining `68`; high priority remaining `55`; pair templates `136/16`; artifact `artifacts/latest/provider_manual_workbench_latest.*`
- Manual hash gate: status `waiting_for_import`; ready_for_manual_signature `false`; approved_by_user `false`; publish-compatible with provider raw `false`; artifact `artifacts/latest/provider_manual_hash_gate_latest.*`
- Manual Team Total overlay preview: status `waiting_for_import`; overlay `0/68`; ready_for_publish_preflight `false`; approved_by_user `false`; formal_publish_allowed `false`; artifact `artifacts/latest/provider_manual_overlay_preview_latest.*` and `artifacts/latest/provider_manual_team_total_overlay_raw_latest.json`
- Manual Team Total overlay publish preflight: status `waiting_for_import`; approval file `manual_verification/provider_team_total_overlay_approval.json`; overlay_publish_preflight_passed `false`; approved_by_user `false`; publish_compatible_with_provider_raw `false`; formal_publish_allowed `false`; artifact `artifacts/latest/provider_manual_overlay_approval_template_latest.json` and `artifacts/latest/provider_manual_overlay_publish_preflight_latest.*`
- Manual Team Total overlay publish: command `python3 publish_provider_manual_overlay.py`; status `blocked_overlay_publish_preflight`; ok `false`; overlay `0/68`; formal_raw_publish_performed `false`; raw_batch_manifest_written `false`; artifact `artifacts/latest/provider_manual_overlay_publish_latest.*`
- Public snapshot import: status `waiting_for_snapshot_import`; import dir `manual_verification/public_raw_snapshots`; preview ready `false`; formal_publish_allowed `false`; artifact `artifacts/latest/public_snapshot_import_status_latest.*`, `artifacts/latest/public_snapshot_import_manifest_template_latest.json`, and `artifacts/latest/public_snapshot_import_preview_raw_latest.json`
- Public snapshot publish preflight: status `waiting_for_snapshot_import`; approval file `manual_verification/public_snapshot_import_approval.json`; snapshot_publish_preflight_passed `false`; formal_publish_allowed `false`; artifact `artifacts/latest/public_snapshot_import_approval_template_latest.json` and `artifacts/latest/public_snapshot_import_publish_preflight_latest.*`
- Public snapshot raw publish: command `python3 publish_public_snapshot_raw.py`; status `blocked_publish_preflight`; ok `false`; formal_raw_publish_performed `false`; raw_batch_manifest_written `false`; artifact `artifacts/latest/public_snapshot_raw_publish_latest.*`
- OpticOdds status: earlier live access was blocked by `opticodds_access_denied_1010`; historical blockers are stored in `odds_provider_blocked_latest.json`. Current KPI marks stale blocked attempts as history-only when the active refresh succeeded.
- Current executable new stake: AUD 0

## 安全边界

- ZIP 和 GitHub 不包含真实 API key；本机真实 key 只允许放在 ignored `tab-research-pipeline/config/odds_providers.local.env`。
- Provider 配置医生只输出 key presence，不输出真实 key；用于防止 `Unknown sport` 和 event-probe credit 误用。
- The Odds API key 曾出现在早期远端历史；即使 HEAD 和交付包已清理，仍建议在 provider 后台 rotate。
- 当前系统只生成研究报告、候选建议、KPI、人工校验队列、人工导入状态、人工 hash gate、overlay 预览和 overlay 发布预检；不自动下注，不点击 TAB odds，不修改 Bet Slip。
- Overlay preview / publish preflight 不等于正式 raw publish：它只合并通过结构校验的人工 CSV 并校验人工签名文件，不证明 TAB 真实性，不自动设置 `approved_by_user=true`，不生成新增下注金额。
- Overlay publish 命令即使成功也只写 Matches raw slot，不写 5-board batch manifest，不解锁 full automation，不生成新增下注金额。
- Public snapshot import 不等于正式 raw publish：它只把外部导出的 Matches JSON 转成 research-only preview raw 与 hash，不证明 TAB 页面真实性，不写正式 raw batch manifest。
- Public snapshot publish preflight 只校验人工签名文件与 preview hash 是否匹配；通过后仍需显式 publish 命令和 safety gate，不能自动下注。
- Public snapshot raw publish 命令即使成功也只写 Matches raw slot，不写 5-board batch manifest，不解锁 full automation，不生成新增下注金额。
- Team Total 成对模板只预留人工录入行，不是 TAB 盘口真实性证据；未填写并通过 hash/signature gate 前不能发布正式 raw。
