# S3 DAILY_OPERATION 下一 Agent 先读

更新时间：2026-07-02 23:48:12 Australia/Sydney

## 当前结论

当前 GitHub main 已记录 Stage 2 integrated production acceptance 和 final bundle 完成证据，但 S3/DAILY_OPERATION 仍未完成。

| 项目 | 当前状态 | 证据 |
|---|---|---|
| 交接内容生成基线 | `bccc600959e6bf478c8fc71f8c2e90c13c455d1f` | 上一轮生成本页内容时的 `origin/main` |
| 交接页首次落库提交 | `91f22b876b05f373229ef4bf5de2e67bdb927c0b` | 首次添加本页的 GitHub `main` 提交 |
| final bundle | `status=pass`，`missing_items=[]` | `FINAL_ACCEPTANCE_BUNDLE/manifest.json` |
| Stage 2 integrated acceptance | `stage2_integrated_production_accepted=true`，`production_acceptance_claimed=true` | `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` |
| owner A 决策 | `keep_daily_operation_disabled_no_persistent_authorization` | `governance/run_manifests/ADP-S2PMT07-DAILY-OPERATION-OWNER-DECISION-AFTER-REQUEST-MAINLINE-ATTESTATION-20260701.json` |
| DAILY_OPERATION | `daily_operation_enabled=false` | `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml` |
| 持久授权 artifact | 缺失 | `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` |
| 持久授权模板 | 存在，但默认无效、不能替代授权 | `FINAL_ACCEPTANCE_BUNDLE/templates/daily_operation_persistent_enablement_authorization.template.json` |
| root verifier S3 阻断输出 | `daily_operation_authorization_ready=false`，`daily_operation_blocking_reasons=["persistent_daily_operation_authorization_missing"]` | `python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1` |
| DAILY_OPERATION 专用 root gate | 当前必须 `status=FAIL` / exit 2 | `tools/verify_daily_operation_readiness.py` |
| DAILY_OPERATION enablement preflight root gate | 当前必须 `status=FAIL / exit 2`，`enablement_preflight_ready=false`，阻断原因为 `persistent_daily_operation_authorization_missing` | `tools/verify_daily_operation_enablement_preflight.py` |
| Root 执行根校验 | 正确 CodexProject 仓库根必须输出 `repo_root_valid=true`、`root_validation_errors=[]`、`required_paths_missing=[]`；误传项目子目录时必须 fail-closed 为 `codexproject_repo_root_invalid` | `tools/verify_daily_operation_readiness.py` / `tools/verify_daily_operation_enablement_preflight.py` |

## 不要误读

- `HANDOFF/00_下一Agent先读.md` 是 final bundle 的 no-production 输入 artifact，按 validator 必须保持 `integrated_production_accepted=false`。不要把它当成当前 S3/DAILY_OPERATION 状态页。
- `FINAL_ACCEPTANCE_BUNDLE/manifest.json`、`no_production_side_effects.json`、`owner_production_boundary_decision.json`、`p0_p1_zero_proof.json` 中的 `closure_state` / `no_production_side_effects` false 字段，只说明该 artifact 写入时的 no-production / closure-state 语境；不得回退当前 Stage 2 accepted 事实，也不得诱导修改这些历史 final bundle artifact。
- 当前 Stage 2 accepted 事实以 `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml` 和 `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` 为准。
- 当前最新状态以 `CURRENT.yaml`、`OWNER_STATUS.md`、`关键结论与用户决策.md` 和本文件为准。
- 一次受控真实运行验收、final bundle pass、Stage 2 integrated acceptance 都不等于持久 DAILY_OPERATION 授权。
- `python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1` 的 `status=PASS` 只证明 final bundle / zero-proof / no-production root gate 通过；必须同时读取 `daily_operation_authorization_ready=false` 和 `daily_operation_blocking_reasons`，不得把 root PASS 当作 S3/DAILY_OPERATION 可启用。
- `tools/verify_daily_operation_readiness.py` 是 S3/DAILY_OPERATION 专用 fail-closed root gate；缺持久授权 artifact 时必须返回 `status=FAIL` 和 exit 2。该非零退出是正确阻断，不是验证故障。
- `tools/verify_daily_operation_enablement_preflight.py` 是 `S2PMT07-DAILY-OPERATION-ENABLEMENT-PREFLIGHT` 的只读组合门；它只汇总 readiness + open PR + SMTP flag + LaunchAgent + background process，不创建授权、不启用运行。默认命令会自动观察 GitHub open PR count、真实 `ADP_ALLOW_SMTP_SEND` 环境值、LaunchAgent 和后台 ADP 进程，输出 `open_pr_observation_mode=auto_observed`、`adp_allow_smtp_send_environment_raw` 和 `runtime_observation_mode=auto_observed`；当前缺持久授权时同样必须返回 `status=FAIL / exit 2`。
- 两个 DAILY_OPERATION root gate 的 exit 2 还不够；后续 agent 必须同时核对 JSON 字段 `repo_root_valid=true`、`root_validation_errors=[]`、`required_paths_missing=[]`。若误传 `--root arxiv-daily-push` 等非 CodexProject 仓库根，工具应返回 `repo_root_valid=false` 和 `codexproject_repo_root_invalid`，这代表命令执行根错误，不是 S3 授权缺失。
- `FINAL_ACCEPTANCE_BUNDLE/templates/daily_operation_persistent_enablement_authorization.template.json` 只是 owner-editable 模板，默认 `template_only=true` 且 `explicit_persistent_daily_operation_authorization=false`；复制不改必须无效，不得当作持久授权 artifact。半改模板也不能通过：保留占位 `generated_at` 或 `authorization_text` 仍必须无效，必须替换为当前 owner 明确授权证据。
- 当前 S3 安全边界必须检查真实 LaunchAgent 标签：`com.linzezhang.adp.daily`、`com.linzezhang.adp.health`、`com.linzezhang.adp.watchdog`。旧 `com.linze.adp.local.*` 只属于历史记录，不得作为当前 S3 safety check。
- 当前 `daily-operation-authorization-preflight` 与 `integrated-production-acceptance-preflight` 机器 gate 输出同样使用真实 LaunchAgent 标签；历史 artifact 只读兼容旧 label，不得反推当前命令继续使用旧 label。
- 不要为了追逐当前提交号重复改写本页；只有 S3/DAILY_OPERATION 事实、授权状态或证据路径变化时才更新。

## 唯一当前阻断

`FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json` 不存在。

在该显式 owner 持久授权 artifact 缺失时，必须保持：

- `persistent_daily_operation_authorized=false`
- `daily_operation_enabled=false`
- `ADP_ALLOW_SMTP_SEND` 原始值只能是 `UNSET` 或 false-like；truthy 必须停止
- `real_smtp_send_enabled=false`
- `scheduler_install_enabled=false`
- `release_packaging_enabled=false`
- `production_restore_enabled=false`

## 禁止动作

- 不要启用 SMTP。
- 不要启用、安装或 kickstart scheduler/LaunchAgents。
- 不要上传 Release。
- 不要执行 production restore。
- 不要创建或伪造 `daily_operation_persistent_enablement_authorization.json`。
- 不要把 `daily_operation_persistent_enablement_authorization.request.json` 当成授权。
- 不要重新发送同日 M1-M4 邮件来制造进度。

## 若 owner 未来明确授权

只有在 owner 明确要求持久 DAILY_OPERATION 时，下一 agent 才能进入以下顺序：

1. 创建显式授权 artifact：`FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`。
2. 运行 `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION` gate。
3. 运行单独 enablement preflight：`S2PMT07-DAILY-OPERATION-ENABLEMENT-PREFLIGHT` / `tools/verify_daily_operation_enablement_preflight.py`。
4. 继续验证 `ADP_ALLOW_SMTP_SEND`、LaunchAgents、open PR count、后台进程和 no duplicate-send guard。

没有第 1 步时，后续只能做只读复核、证据同步或 owner-facing handoff，不得推进 DAILY_OPERATION。

## 最小复核命令

以下命令必须从 CodexProject 仓库根目录运行；`tools/`、`scripts/` 和 `FINAL_ACCEPTANCE_BUNDLE/` 均为仓库根路径。不要给这些 root tools 追加 `--json`；它们默认输出 JSON。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_governance_current_state.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B scripts/validate_project_governance.py --project arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B scripts/validate_governance_sync.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2
```

预期：`verify_acceptance_bundle.py` 输出 `status=PASS`，同时显示 `daily_operation_authorization_ready=false`；`verify_daily_operation_readiness.py` 和 `verify_daily_operation_enablement_preflight.py` 的命令本体都输出 `status=FAIL` / exit 2；随后 shell 断言分别输出 `EXPECTED_READINESS_EXIT=2` 和 `EXPECTED_PREFLIGHT_EXIT=2` 并通过。若任一 DAILY_OPERATION 命令返回 0 或其他非 2 exit code，停止并回报，不得为了让命令变绿而放宽 DAILY_OPERATION 门。

最小复核命令还必须读取 JSON 字段：正确仓库根下 `repo_root_valid=true`、`root_validation_errors=[]`、`required_paths_missing=[]`；缺持久授权时仍应同时显示 `authorization_artifact_exists=false` 和 `persistent_daily_operation_authorization_missing`。若看到 `codexproject_repo_root_invalid`，先修正执行目录或 `--root`，不要把它解释为 DAILY_OPERATION 授权阻断。

## 安全边界复核

安全边界复核主路径：先运行上方最小复核命令中的 copy-safe enablement preflight，确认 `EXPECTED_PREFLIGHT_EXIT=2` 后，再读取自动观察到的 `open_pr_observation_mode=auto_observed`、`open_pr_count`、`adp_allow_smtp_send_environment_raw`、LaunchAgent 和后台进程结果。下方 shell 只作为人工补充复核；open PR 人工 HTML fallback 只允许作为降级审计补充，不得替代 enablement preflight root gate。

```bash
test ! -e FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json
ADP_ALLOW_SMTP_SEND_VALUE="${ADP_ALLOW_SMTP_SEND-UNSET}"
printf 'ADP_ALLOW_SMTP_SEND=%s\n' "$ADP_ALLOW_SMTP_SEND_VALUE"
case "$ADP_ALLOW_SMTP_SEND_VALUE" in
  1|true|TRUE|yes|YES|on|ON)
    printf 'blocked: ADP_ALLOW_SMTP_SEND is truthy\n' >&2
    exit 1
    ;;
esac
for label in com.linzezhang.adp.daily com.linzezhang.adp.health com.linzezhang.adp.watchdog; do
  if launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
    printf 'blocked: %s is loaded\n' "$label" >&2
    exit 1
  fi
  printf '%s not_loaded\n' "$label"
done
ps aux | rg -i 'arxiv_daily_push|arxiv-daily-push|local_runner|CodexProject.*arxiv-daily-push' | rg -v 'rg -i|pytest|unittest|validate|zsh -lc|exec_command' || true
FALLBACK_PR_COUNT=$(
  curl -fsSL -H 'User-Agent: codex-adp-open-pr-check' 'https://github.com/LinzeColin/CodexProject/pulls?q=is%3Apr+is%3Aopen' |
  python3 -c 'import re,sys; html=sys.stdin.read(); m=re.search(r">\s*([0-9,]+)\s+Open\s*<", html); print(m.group(1).replace(",","") if m else "UNKNOWN")'
)
printf 'fallback_open_pr_count=%s\n' "$FALLBACK_PR_COUNT"
test "$FALLBACK_PR_COUNT" = "0"
```

预期：授权 artifact 不存在；真实环境 `ADP_ALLOW_SMTP_SEND` 为 `UNSET` 或 false-like；enablement preflight 输出 `open_pr_observation_mode=auto_observed`、`adp_allow_smtp_send_environment_raw` 和 `runtime_observation_mode=auto_observed`；`com.linzezhang.adp.daily`、`com.linzezhang.adp.health`、`com.linzezhang.adp.watchdog` 三个真实 ADP LaunchAgent 标签均未加载或保持 disabled；旧 `com.linze.adp.local.*` 仅为历史标签口径，不得作为当前复核通过依据；无 ADP 后台进程；root gate 自动观察 `open_pr_count=0`，人工补充 fallback 输出 `fallback_open_pr_count=0`。后台进程扫描只匹配 ADP runner/module/path 信号，不使用裸 `adp` 子串，避免把普通工作树路径或 shell 命令误判为运行中。若 `ADP_ALLOW_SMTP_SEND` 为 truthy（按真实环境值判断）、任一真实 LaunchAgent 标签已加载，或 open PR 结果为 `UNKNOWN` / 非 0，停止并回报，不得当作通过。
