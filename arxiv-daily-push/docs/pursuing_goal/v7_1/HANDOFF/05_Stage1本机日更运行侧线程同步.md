# Stage1 本机日更运行侧线程同步

更新时间：2026-06-24T15:40:00+10:00

## 目的

把 side conversation 中完成的 Stage1-only 本机日更启用、真实 SMTP 发送、readiness 验收、邮件模板核验和 GitHub 同步状态整理成主线程可判断的交接记录。

本文件是同步面，不是主线程合并决定；主线程需要自行判断是否吸收 `codex/adp-stage1-daily-operation-hardening-20260624` 分支中的 runner/readiness/launchd 改动。

## 结论

- Stage1 arXiv 本机日更路径已经在本 Mac 上跑通过一次真实 `local-runner daily --allow-smtp-send`。
- `local-runner readiness --require-smtp --require-scheduler` 已通过，证明本机 SMTP、launchd 安装证据、最近真实发送证据和 launchd package 文件齐备。
- 当前本机日更 runner 是 macOS `launchd` + repo 内 `local-runner`，不是 Codex Automation，也不是 GitHub cloud schedule。
- GitHub cloud scheduled production 仍保持 disabled；Stage2 `INTEGRATED_PRODUCTION_ACCEPTED` 未声明。
- 更正：上一轮真实 SMTP 发送证据使用的仍是旧中文教学/反馈模板；这解释了用户实际收到旧模板。
- 本轮已把当前分支代码实际修正为 V7.1 M1-compatible 邮件模板，并通过真实 arXiv 抓取的 no-send `local-runner daily` 和真实 `local-runner daily --allow-smtp-send` 生成/发送新 preview；旧 `【今天讲透一个问题】` 模板标记不再出现。
- 本轮同时修复本机 Python `urllib` 抓 arXiv 时 OpenSSL 默认 CA 路径为空导致的 `CERTIFICATE_VERIFY_FAILED` 阻断；不关闭 TLS 校验。

## 当前运行边界

| 项 | 状态 |
|---|---|
| Stage1 accepted artifact | maintained |
| Stage1 local daily email | ready on this Mac |
| Runner | `local_macos_launchd_with_codex_local_python` |
| Codex Automation runner | `false` |
| GitHub cloud schedule | disabled |
| Stage2 integrated production | not accepted |
| Secrets in repo | none |
| SMTP password storage | local Keychain/env only; value must never be written to repo |

## 本机 launchd 状态

已安装的 labels：

- `com.linze.adp.local.health`
- `com.linze.adp.local.daily`
- `com.linze.adp.local.watchdog`

当前日更命令指向 side runner 工作树：

`/Users/linzezhang/Documents/Codex/2026-06-21/readme-first-md-01-execution-contract/work/CodexProject_adp_stage1_daily_operation`

原因：该分支包含 `local-runner readiness` 与 health/daily/watchdog launchd package；截至本记录，主线程工作树的 `local-runner` 只有 `preflight/daily/launchd-package`，尚无 `readiness` 子命令。

## 真实运行证据

### 真实发送

证据文件：

- `/tmp/adp_stage1_daily_real_success_attempt3.json`
- `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260624/email_preview.txt`
- `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260624/email_preview.html`

关键结果：

```text
status: pass
real_smtp_sent: true
candidate_queue_persisted: true
selected_source_id: arxiv:2606.24212
selected_title: Path Space Robust Bayesian Portfolio Selection
date: 2026-06-24
generated_at: 2026-06-24T03:54:34Z
```

### Readiness 验收

证据文件：

- `/tmp/adp_stage1_readiness_final.json`

关键结果：

```text
status: pass
stable_daily_email_ready: true
runner: local_macos_launchd_with_codex_local_python
codex_automation_runner: false
gates: local_preflight pass; local_smtp_send_enablement pass; local_scheduler_install_evidence pass; latest_local_daily_evidence pass; launchd_package_files pass
```

## 邮件模板核验

### 本轮真实 SMTP resend（新模板，已通过）

证据文件：

- `/tmp/adp_v71_m1_real_send.json`
- `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260624/email_preview.txt`
- `/Users/linzezhang/.adp/arxiv-daily-push/runs/20260624/email_preview.html`
- `/tmp/adp_v71_m1_readiness.json`

关键结果：

```text
local-runner daily status: pass
daily_run_status: succeeded
notification_report.status: sent
real_smtp_sent: true
selected_source_id: arxiv:2606.24817
secret_values_logged: false
readiness status: pass
stable_daily_email_ready: true
```

真实发送 preview plain text 包含所有 V7.1 M1 marker，且不包含旧模板 marker。

### 本轮当前代码 no-send preview（新模板，已通过）

证据文件：

- `/private/tmp/adp_v71_email_preview_state_ssl/runs/20260624/email_preview.txt`
- `/private/tmp/adp_v71_email_preview_state_ssl/runs/20260624/email_preview.html`

关键结果：

```text
local-runner daily status: pass
notification_report.status: dry_run
selected_source_id: arxiv:2606.24309
old_template_present: false
html_brand: M1 科学与理论前沿 · B1+B4/B5/B6
```

当前 plain text 包含：

- `【M1 科学与理论前沿】`
- `【1. 今日真正变化】`
- `【2. 一分钟决策卡】`
- `【3. 主讲深度解释】`
- `【4. 前沿 Delta】`
- `【5. 证据级别与不确定性】`
- `【6. B4 社会与时代影响】`
- `【7. B5 风险、反证与失败条件】`
- `【8. B6 个人影响、ROI 和行动】`
- `【9. 复习问题】`
- `【10. 反馈】`
- `预计 ROI`
- `时间成本`
- `置信度`
- `行动路径`

当前 plain/html 均不应出现：

- `【今天讲透一个问题】`
- `为什么值得你看`
- `ROI score`
- `Release 资料包`
- `后台`
- `日报`
- `视频入口`

### 上一轮真实 SMTP preview（旧模板，已被本轮修复取代）

真实发送预览 plain text 包含：

- `【今天讲透一个问题】`
- `【为什么值得你看】`
- `【候选队列摘要】`
- `【反馈】`
- `值得深入 / 相关性低 / 太浅 / 太长 / 需要实验`

真实发送预览 plain/html 均未出现以下旧前台标记：

- `ROI score`
- `Release 资料包`
- `后台`
- `日报`
- `视频入口`

注意：上一轮真实 SMTP 发送发生在本轮 V7.1 M1 template fix 之前，不能再作为“新模板已发送”的证明；它只能证明 SMTP transport 能发。本轮已经用同一类本机 SMTP env 重新执行 `local-runner daily --allow-smtp-send` 并发送新模板。

## 为什么用户可能看到“旧模板”

已确认的事实：

- side runner 分支此前与 `origin/main` 在 `global_scan.py` 的旧邮件前台模板标记上一致，因此真实发送仍是旧模板。
- 本轮分支已不再与旧模板一致：`global_scan.py` 的 plain/html renderer 现在按 V7.1 M1-compatible 结构生成邮件。
- 主线程工作树包含新模板标记，但缺少 side runner 分支新增的 `readiness` 子命令。
- 本机 launchd 指向 side runner 工作树，是为了保留 readiness/watchdog 能力。

可能原因：

- 用户看到的是本轮修复前发出的真实 SMTP 邮件；本轮修复后又发送了一封新模板邮件。
- 主线程有尚未进入当前 checkout/origin 的更晚 UI/UX 模板改动。
- 本机 launchd 当前指向 side runner 工作树；本轮已在该工作树内验证新模板真实发送和 readiness。合并到主线程后仍建议重新生成/安装 launchd package，避免未来切换工作树后回退。

主线程如有更晚模板改动，应以主线程当前文件为准，把本轮 V7.1 M1 renderer、`local-runner readiness`、health/daily/watchdog launchd、本机 HTTPS CA 修复和本机验收记录合并过去，再重新生成并安装 launchd package。

## 已完成的代码/治理改动

side runner 分支：

`codex/adp-stage1-daily-operation-hardening-20260624`

本地 commits：

- `51fefa6 Harden ADP stage1 daily operation readiness`
- `72a8f78 Install ADP stage1 local launchd runner`
- `f7db00b Record ADP stage1 SMTP auth blocker`
- `ad4b683 Mark ADP stage1 local daily ready`

主要改动范围：

- `arxiv-daily-push/src/arxiv_daily_push/local_runner.py`
- `arxiv-daily-push/src/arxiv_daily_push/cli.py`
- `arxiv-daily-push/tests/test_local_runner.py`
- `arxiv-daily-push/docs/runbooks/LOCAL_CODEX_RUNNER_RUNBOOK.md`
- `arxiv-daily-push/docs/governance/*`

## 主线程建议判断

默认推荐：把 side runner 分支中的 Stage1 local readiness/launchd/watchdog 能力 cherry-pick 或合并到主线程最新 Stage2 工作树，然后由主线程重新运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_stage1_runner_tests \
PYTHONPATH=arxiv-daily-push/src \
python3 -m unittest arxiv-daily-push/tests/test_local_runner.py arxiv-daily-push/tests/test_stage1_runtime.py arxiv-daily-push/tests/test_scheduled_execution.py -q

PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_stage1_governance \
python3 scripts/validate_project_governance.py --project arxiv-daily-push

PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/adp_stage1_sync \
python3 scripts/validate_governance_sync.py --changed-only --enforce-sync --semantic --base-ref origin/main

git diff --check
```

合并后主线程再重新生成 launchd package、安装并运行：

```bash
python3 -m arxiv_daily_push local-runner daily --allow-smtp-send
python3 -m arxiv_daily_push local-runner readiness --require-smtp --require-scheduler
```

## 禁止与风险

- 不要把 SMTP password 写入 GitHub repo、handoff、logs 或 governance jsonl。
- 不要把 GitHub secret 等同于本机 Keychain；当前真实本机 runner 读取本机 env/Keychain。
- 不要启用 GitHub cloud scheduled production。
- 不要把 Stage1 local daily ready 误写为 Stage2 integrated production accepted。
- 如果主线程模板比当前 origin/main 更新，必须先合并模板，再重装 launchd。

## 回滚

如需停止本机日更：

```bash
$HOME/.adp/arxiv-daily-push/launchd-package/uninstall-local-launchd.sh
```

然后把 `stage1_stable_daily_email_ready` 相关治理状态恢复为 blocked/pending，并保留 Stage1 accepted artifact 状态不变。
