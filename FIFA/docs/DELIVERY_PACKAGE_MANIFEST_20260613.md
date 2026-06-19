# Delivery Package Manifest 2026-06-13

交付包目标：让其他 agent 拿到 ZIP 后可以继续开发、审查、运行和验证 TAB FIFA 盘口研究系统。

最新交付包命名：`/Users/linzezhang/Downloads/FIFA Report/FIFA_agent_review_package_14062026_<git-short-sha>.zip`
对应 Git commit：在仓库根目录运行 `git rev-parse HEAD`。

## 包含内容

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | 项目级开发规则 |
| `tab-research-pipeline/` | 当前主系统完整源码、测试、脚本、配置、README/RUNBOOK、app icon assets |
| `docs/HANDOFF.md` | 当前状态和下一步 |
| `docs/DEVELOPMENT_STATUS.md` | 当前交付状态和验证结果 |
| `docs/PARALLEL_REVIEW_SUMMARY_20260613.md` | 本轮并行审查结论、严重程度、修复状态 |
| `docs/FEATURE_LIST.md` | 功能清单 |
| `docs/DELIVERY_STANDARDS.md` | 交付标准、运行方式、合并 gate |
| `docs/FILE_RETENTION_POLICY.md` | 本地保留/清理策略 |
| `artifacts/latest/` | public-safe latest 状态产物 |
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
- TAB 密码、OTP、session secret、私有持仓明细原始文本

## 必须先读

1. `AGENTS.md`
2. `docs/HANDOFF.md`
3. `docs/DEVELOPMENT_STATUS.md`
4. `docs/PARALLEL_REVIEW_SUMMARY_20260613.md`
5. `docs/DELIVERY_STANDARDS.md`

## 当前验收快照

- App URL: `http://127.0.0.1:8767/`
- Runtime cwd: `github_sync/FIFA/tab-research-pipeline`
- Python tests: `176 tests OK`
- Node security tests: passed
- Downloads HTML/App rebuilt: yes
- Current raw state: blocked by `ai_controlled_access_rejected`
- Provider raw state: staged The Odds API Matches research-ready for Result/Handicap; Total O/U reached usable threshold; formal publish still blocked.
- Provider latest refresh: `20260613T135338Z-provider-50380e82`
- Provider coverage: Result `68/68`, Handicap `47/68`, Total O/U `55/68`, Team Total O/U `0/68`
- Alternate plan: The Odds API Total O/U queue `0`; Team Total fallback queue `68`; next batch `0`; estimated credits `0-0`; status `fallback_required`
- Fallback verification: queue `68`; high priority `55`; status `provider_blocked_manual_verification_required`; artifact `artifacts/latest/provider_fallback_verification_latest.*`
- Manual verification import: template `artifacts/latest/provider_manual_verification_template_latest.csv`; status `import_missing`; complete `0/68`; high priority complete `0/55`; invalid rows `0`; artifact `artifacts/latest/provider_manual_verification_status_latest.*`
- Manual hash gate: status `waiting_for_import`; ready_for_manual_signature `false`; approved_by_user `false`; publish-compatible with provider raw `false`; artifact `artifacts/latest/provider_manual_hash_gate_latest.*`
- OpticOdds status: blocked by `opticodds_access_denied_1010`; last-good coverage preserved in `odds_provider_coverage_latest.json`; blocker stored in `odds_provider_blocked_latest.json`
- Recommended provider action: stop The Odds API team_totals/Total O/U probes; use OpticOdds official access or TAB manual final verification for Team Total and shortlisted missing candidates.
- Current executable new stake: AUD 0

## 安全边界

- ZIP 和 GitHub 不包含真实 API key；本机真实 key 只允许放在 ignored `tab-research-pipeline/config/odds_providers.local.env`。
- The Odds API key 曾出现在早期远端历史；即使 HEAD 和交付包已清理，仍建议在 provider 后台 rotate。
- 当前系统只生成研究报告、候选建议、KPI、人工校验队列和人工导入状态；不自动下注，不点击 TAB odds，不修改 Bet Slip。
