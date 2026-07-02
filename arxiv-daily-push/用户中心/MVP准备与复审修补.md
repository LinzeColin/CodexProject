# MVP 准备与复审修补

更新时间：2026-07-03 06:34:13 Australia/Sydney

本页是 ADP 在 Stage 2 integrated acceptance 已记录、但不进入 S3/DAILY_OPERATION 的前提下，为后续 MVP 复审和修补准备的 GitHub 浅层入口。

## 当前结论

| 项目 | 当前口径 | 证据 |
|---|---|---|
| Stage 2 状态 | 已记录 `stage2_integrated_production_accepted=true` 和 `production_acceptance_claimed=true` | [integrated acceptance](../../FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json) / [最终验收包与 S3 阻断](./最终验收包与S3阻断.md) |
| S3/DAILY_OPERATION | 不进入；继续保持 `daily_operation_enabled=false` | [最终验收包与 S3 阻断](./最终验收包与S3阻断.md) / [S3 handoff](../../HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md) |
| 持久授权 | 缺 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`，不得伪造或由请求包替代 | [CURRENT.yaml](../docs/pursuing_goal/CURRENT.yaml) |
| Enablement preflight | 已有只读组合 root gate：`S2PMT07-DAILY-OPERATION-ENABLEMENT-PREFLIGHT`；当前因 `persistent_daily_operation_authorization_missing` 必须 `enablement_preflight_ready=false` | `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` |
| 一次受控真实运行窗口 | 一次受控真实运行窗口只允许临时切换 `ADP_ALLOW_SMTP_SEND`；窗口结束后必须恢复为 `UNSET` 或 false-like，重新运行 enablement preflight 并确认仍 `status=FAIL / exit 2`；不得把一次受控真实运行当作持久 DAILY_OPERATION 授权 | [S3 handoff](../../HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md) |
| Root 执行根 | 正确 root 必须显示 `repo_root_valid=true`；误传 `--root arxiv-daily-push` 等子目录必须 JSON fail-closed、exit 2，并给出 `codexproject_repo_root_invalid` | `python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2` / `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` |
| MVP 准备 | 只做复审、修补、用户向可读性、证据同步、测试补强和低风险局部修复 | 本页 |
| 开发基线 | 每轮从 GitHub `origin/main` 的干净隔离工作树开始；本机脏工作树、detached HEAD 或临时 worktree 结果不能单独当作交付基线 | `git status` / GitHub `main` |

## 01 目标与用户结果

MVP 目标不是开启后台日常运行，而是让 owner 和后续 agent 能稳定完成以下工作：

- 快速理解当前 ADP 状态：Stage 2 已验收，S3/DAILY_OPERATION 未授权。
- 找到下一轮复审修补入口，不翻本机 `.adp` 或深层历史文档。
- 对用户中心、候选池、邮件模板、证据链、P0/P1 zero-proof、最终验收包和治理同步做小步修补。
- 每次修补都能通过最小回归验证，并保持 SMTP/scheduler/Release/restore 禁用。

## 02 用户与主流程

| 用户 | 主流程 | 成功标准 |
|---|---|---|
| owner | 打开 GitHub `arxiv-daily-push/用户中心/`，先看本页和关键结论 | 能判断当前是否进入 DAILY_OPERATION，以及下一轮修补该看什么 |
| 复审 agent | 读取本页、S3 handoff、CURRENT 和相关用户中心页面 | 能选一个小范围问题修补，不误开生产开关 |
| 实现 agent | 根据复审发现做单点修复 | 同一提交更新用户向入口、三基、测试和验证证据 |

## 03 MVP 范围

| 范围 | 本轮允许 | 本轮禁止 |
|---|---|---|
| 用户中心 | 修复浅层页面、链接、中文口径、证据表、阻断项默认动作 | 只把本机路径当 owner 主入口 |
| 证据链 | 修复 handoff、run manifest 引用、CURRENT 读取说明、测试断言 | 改写 V7.1/V7.2 合同基线或伪造验收 |
| 邮件与队列 | 只读复审 Email V1、M1-M4、队列状态和去重证据 | 发送 SMTP、安装或 kickstart scheduler |
| 数据源与板块 | 只做无生产副作用的文档/测试同步；任何来源变更必须同步用户中心和 source gate | 绕过 `source/board user-center sync gate` |
| 评分与 ROI | 公开现有公式、因子、权重、空值处理和证据字段 | 伪造历史评分或用未公开模型声明高价值 |

## 04 核心页面、模块与服务

| 模块 | MVP 读入口 | 修补原则 |
|---|---|---|
| 当前状态 | [关键结论与用户决策](./关键结论与用户决策.md) | 阻断项必须写默认动作和验收证据 |
| S3 边界 | [S3 DAILY_OPERATION 下一 Agent 先读](../../HANDOFF/01_S3_DAILY_OPERATION_下一Agent先读.md) | 不把 final bundle no-production handoff 当当前 S3 状态页 |
| 总候选池 | [截至今日总候选池](./截至今日候选池.md) | 总候选池、前20精选、评分明细必须可复核 |
| 邮件与队列 | [邮件发送与队列状态](./邮件发送与队列状态.md) | 已发送、未发送/阻断、排队必须 GitHub 可读 |
| 数据源与板块 | [数据源与板块健康](./数据源与板块健康.md) | 来源/板块变更必须同步用户中心和测试 |
| 最终验收包 | [最终验收包与 S3 阻断](./最终验收包与S3阻断.md) / [manifest](../../FINAL_ACCEPTANCE_BUNDLE/manifest.json) | 只能作为 Stage 2 acceptance 证据，不等于 DAILY_OPERATION 授权 |

## 05 数据输入与存储

| 数据 | 用途 | MVP 约束 |
|---|---|---|
| `docs/owner/CONTENT_LEDGER.csv` | 总候选池、报告/邮件预览索引、候选状态 | 用户中心必须展示总量和可追踪链接 |
| `governance/run_manifests/*.json` | 运行证据和阶段收口 | 只能引用真实存在文件 |
| `FINAL_ACCEPTANCE_BUNDLE/*.json` | final bundle、zero-proof、acceptance 和授权门证据 | `.request.json` 不能替代真正授权 artifact |
| `docs/pursuing_goal/CURRENT.yaml` | 当前合同、门和生产边界 | 不因 MVP 准备改变 CURRENT 或启用 DAILY_OPERATION |

## 06 风险与约束

| 风险 | 控制 |
|---|---|
| 把 Stage 2 accepted 误读为 S3 已进入 | 所有 MVP 页面必须同时写 `daily_operation_enabled=false` |
| 把 request-only artifact 当授权 | 页面和测试必须点名真正授权 artifact 仍缺失 |
| 用户中心再次变成深层或本机路径依赖 | owner-facing 信息必须在 `arxiv-daily-push/用户中心/` 可读 |
| 本机脏工作树或 detached HEAD 被误当主线 | 后续 agent 必须先核对 `origin/main`、open PR count、生产禁用状态和目标文件 diff；需要保留的本地成果只能从当前 `origin/main` 重切干净分支或隔离 worktree 后重新落库 |
| 旧 LaunchAgent 标签被误当当前停止门 | 当前 S3/MVP 复核只接受 `com.linzezhang.adp.daily`、`com.linzezhang.adp.health`、`com.linzezhang.adp.watchdog`；旧 `com.linze.adp.local.*` 只属于历史记录 |
| 机器预检输出回退短 key | 当前 `daily-operation-authorization-preflight` 和 `integrated-production-acceptance-preflight` 必须输出真实标签；短 key 只允许验证历史 artifact |
| root verifier PASS 被误读为 S3 可启用 | `verify_acceptance_bundle.py` 必须同时显示 `daily_operation_authorization_ready=false` 和 `persistent_daily_operation_authorization_missing`，root PASS 只代表 no-production/final-bundle 证明 |
| 一次受控真实运行被误读为持久授权 | 一次受控真实运行窗口只允许临时切换 `ADP_ALLOW_SMTP_SEND`；窗口结束后必须恢复为 `UNSET` 或 false-like，并重新运行 enablement preflight 确认仍 `status=FAIL / exit 2` |
| DAILY_OPERATION 专用 gate 被改成宽松通过 | `verify_daily_operation_readiness.py` 在缺持久授权时必须 exit 2；当前非零退出是正确阻断 |
| Enablement preflight 被误读为生产入口 | `tools/verify_daily_operation_enablement_preflight.py` 只汇总 readiness + open PR + SMTP flag + LaunchAgent + background process；默认自动观察 open PR count、ADP_ALLOW_SMTP_SEND 环境值、LaunchAgent 和后台进程，输出 `open_pr_observation_mode=auto_observed`、`adp_allow_smtp_send_environment_raw` 与 `runtime_observation_mode=auto_observed`；当前缺持久授权时必须 `status=FAIL / exit 2`，不得启用 runtime |
| 错误 `--root` 造成 traceback 或误读 | readiness 和 enablement preflight 都必须先做 CodexProject 仓库根校验；错误 root 必须输出 JSON `status=FAIL`、`repo_root_valid=false`、`root_validation_errors=["codexproject_repo_root_invalid"]`，不得抛 Python traceback |
| 自动观察失败被误读成普通授权阻断 | enablement preflight 必须把 `open_pr_observation_errors` 和 `runtime_observation_errors` 中的具体错误同步提升到 `blocking_reasons`，例如 `open_pr_count_observation_failed` 或 `background_process_observation_failed`，方便 owner/agent 直接定位 GitHub API、LaunchAgent 或后台进程观察失败 |
| 持久授权模板被误当 live artifact | 模板默认无效；半改模板仍无效；真正授权路径仍是 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`，并且必须替换真实时间和当前 owner 授权文本 |
| 复审修补扩大到生产运行 | 每轮只修一个明确问题；不启用 SMTP/scheduler/Release/restore |
| 数据源/板块变更漏同步 | 遵守根规则和 `arxiv-daily-push/AGENTS.md` 的 source/board user-center sync gate |

## 07 MVP 验收标准

| 验收项 | 通过标准 | 验证入口 |
|---|---|---|
| 用户可读入口 | 本页、README、关键结论互相可跳转 | `test_governance_current_state.py` |
| 生产边界 | 授权 artifact 不存在，`ADP_ALLOW_SMTP_SEND` 为 `UNSET` 或 false-like，真实 LaunchAgent 标签 `com.linzezhang.adp.daily` / `com.linzezhang.adp.health` / `com.linzezhang.adp.watchdog` 未加载或 disabled，无 ADP 后台进程；后台进程扫描只匹配 ADP runner/module/path，不使用裸 `adp` 子串；旧 `com.linze.adp.local.*` 不得作为当前通过依据 | `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` |
| Stage 2 证据 | final bundle pass，P0/P1 zero-proof pass，Stage2 accepted true；同时显示 DAILY_OPERATION 仍被 `persistent_daily_operation_authorization_missing` 阻断 | `python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1` |
| S3 readiness | 缺持久授权 artifact 时必须 fail-closed，返回 `status=FAIL` / exit 2；正确 root 输出必须包含 `repo_root`、`required_cwd=CodexProject repository root`、`repo_root_valid=true`、`root_validation_errors=[]`、`required_paths_missing=[]` 和 `authorization_artifact_exists=false`；错误 root 必须 JSON fail-closed 并给出 `codexproject_repo_root_invalid` | `python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2` |
| S3 enablement preflight | 缺持久授权 artifact 时必须 fail-closed，返回 `status=FAIL / exit 2`、`enablement_preflight_ready=false`，并同时报告 `repo_root`、`required_cwd=CodexProject repository root`、`repo_root_valid=true`、`root_validation_errors=[]`、`required_paths_missing=[]`、`authorization_artifact_exists=false`、open PR、SMTP flag、LaunchAgent 和后台进程边界；错误 root 必须 JSON fail-closed 并给出 `codexproject_repo_root_invalid`；默认命令必须自动观察 open PR count、`ADP_ALLOW_SMTP_SEND` 环境值、LaunchAgent 和后台进程，不要求后续 agent 手填这些安全事实；若自动观察失败，具体 `open_pr_observation_errors` / `runtime_observation_errors` 必须进入 `blocking_reasons` | `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` |
| 授权模板 | 模板存在但默认无效；复制不改、保留占位时间或占位授权文本的半改模板不能通过 validator | `FINAL_ACCEPTANCE_BUNDLE/templates/daily_operation_persistent_enablement_authorization.template.json` / `test_stage2_final_gate.py` |
| 治理同步 | 项目治理和治理同步 0 error / 0 warning | `validate_project_governance.py` / `validate_governance_sync.py` |
| open PR | GitHub open PR count 为 0；若结果为 `UNKNOWN` 或非 0，不得当作通过 | 默认通过 `python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2` 自动观察 GitHub open PR count，输出 `open_pr_observation_mode=auto_observed`；HTML fallback 只允许作为降级审计补充 |

## 08 停止条件

遇到以下任一情况，停止 MVP 修补并回报：

- 需要创建 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`。
- 需要启用 SMTP、scheduler、Release、restore 或后台 DAILY_OPERATION。
- 需要修改 V7.1/V7.2 根合同、CURRENT 指针或公共 schema。
- 发现证据文件不存在、hash 不匹配或测试失败且无法在当前小范围内修复。
- GitHub `main` 直推被保护拒绝；不得改为开 PR。

## 09 推荐下一轮 Run Contract 模板

| 项 | 内容 |
|---|---|
| 目标 | 复审一个 owner-facing 页面或一个证据链断点，并做最小修补 |
| 最小范围 | 只改相关用户中心页、对应三基记录和一个目标测试 |
| 验证 | 目标测试、project governance、governance sync、`python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1`、`python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2`；open PR 由 enablement preflight 自动观察为 0，降级人工复核只能作为补充证据 |
| 禁止 | SMTP/scheduler/Release/restore/DAILY_OPERATION、CURRENT/V7 合同、公共 schema、DB、数据源运行、副作用队列 |
| 收口 | 直接 commit/push `main`；open PR count 保持 0；最终报告列已完成/未完成/剩余迭代 |

## 10 下一轮最小验证命令

以下命令必须从 CodexProject 仓库根目录运行；`tools/`、`scripts/` 和 `FINAL_ACCEPTANCE_BUNDLE/` 均为仓库根路径。不要给这些 root tools 追加 `--json`；它们默认输出 JSON。readiness 和 enablement preflight 当前必须返回 exit 2，才表示缺持久授权时仍 fail-closed。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B -m unittest arxiv-daily-push/tests/test_governance_current_state.py -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B scripts/validate_project_governance.py --project arxiv-daily-push
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B scripts/validate_governance_sync.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_acceptance_bundle.py --root . --require-zero P0 P1
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_daily_operation_readiness.py --root .; ec=$?; echo "EXPECTED_READINESS_EXIT=$ec"; test "$ec" -eq 2
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_mvp_pyc PYTHONPATH=arxiv-daily-push/src python3 -B tools/verify_daily_operation_enablement_preflight.py --root .; ec=$?; echo "EXPECTED_PREFLIGHT_EXIT=$ec"; test "$ec" -eq 2
```

这些命令只证明 MVP/S3 前置复审仍可安全继续：`verify_acceptance_bundle.py` 可以 PASS Stage 2/final bundle 证据；readiness 与 enablement preflight 仍必须因 `persistent_daily_operation_authorization_missing` 阻断。若任一命令要求创建持久授权 artifact、启用 SMTP、启用 LaunchAgent 或改成 exit 0 来“通过”，应立即停止。
