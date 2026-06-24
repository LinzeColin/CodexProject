# arXiv Daily Push 本机 Codex Runner Runbook

适用范围：Stage 1 / B1 arXiv。  
部署口径：本机电脑 + Codex/local runner；GitHub 只做代码、证据、状态记录、备份、PR/CI。

## 1. 不做什么

- 不启用 GitHub cloud scheduled production。
- 不把 Gmail SMTP 密码写入仓库、Runbook、plist、日志或迁移包。
- 不生成视频、不上传 GitHub Release、不把视频作为 Stage 1 要求。
- 不安装 launchd，除非用户单独确认启用本机每日自动运行。

## 2. 本地 smoke test

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner daily \
  --project-root . \
  --state-dir "$HOME/.adp/arxiv-daily-push" \
  --date "$(TZ=Australia/Sydney date +%F)" \
  --generated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --max-results-per-category 1 \
  --json
```

通过后检查：

- `$HOME/.adp/arxiv-daily-push/latest_local_run.json`
- `$HOME/.adp/arxiv-daily-push/candidate_queue.json`
- `$HOME/.adp/arxiv-daily-push/local_content_ledger.jsonl`
- `$HOME/.adp/arxiv-daily-push/runs/YYYYMMDD/email_preview.txt`
- `$HOME/.adp/arxiv-daily-push/runs/YYYYMMDD/adp-local-runner-report.json`

## 3. 真实 Gmail SMTP 边界

真实发送只允许在本机环境变量或 Keychain-backed shell 中配置：

- `ADP_SMTP_HOST`
- `ADP_SMTP_PORT`
- `ADP_SMTP_USERNAME`
- `ADP_SMTP_PASSWORD`

命令必须显式加 `--allow-smtp-send`；否则只生成本地邮件预览和哈希证据。

## 4. launchd 生成包

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner launchd-package \
  --project-root . \
  --state-dir "$HOME/.adp/arxiv-daily-push" \
  --artifact-dir "$HOME/.adp/arxiv-daily-push/launchd-package" \
  --generated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --json
```

该命令只生成 `.plist`、安装脚本、卸载脚本和 README；不会自动安装。

生成包包含三类本机任务：

- `04:45` health preflight：检查本机命令、资源和 SMTP env 名称。
- `05:00` daily run：生成 Stage 1 arXiv 日报、queue、ledger、邮件预览；只有本地 env 文件中 `ADP_ALLOW_SMTP_SEND=true` 且 SMTP 四个 key 都存在时才附加 `--allow-smtp-send`。
- `05:10` readiness watchdog：检查最新真实发送证据、调度安装证据和 SMTP 门禁。

本地 env 文件默认路径：

```bash
$HOME/.config/arxiv-daily-push/local-runner.env
```

只允许在该本机文件或 Keychain-backed shell 中保存真实值；仓库、plist、日志、README、migration package 都不得包含真实 SMTP 密码。

## 5. 长期运行 readiness 验收

不要用“生成了 launchd 包”或“dry-run 通过”替代“可以每天等邮件”。启用前后都运行：

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push local-runner readiness \
  --project-root . \
  --state-dir "$HOME/.adp/arxiv-daily-push" \
  --launchd-dir "$HOME/.adp/arxiv-daily-push/launchd-package" \
  --generated-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --require-smtp \
  --require-scheduler \
  --json
```

只有输出同时满足以下条件，才可以说“可以等每天邮件”：

- `status: pass`
- `stable_daily_email_ready: true`
- `local_smtp_send_enablement` gate pass
- `local_scheduler_install_evidence` gate pass
- `latest_local_daily_evidence` gate pass，且最新 run 含 `real_smtp_sent: true`

如果输出 blocked，按 `next_owner_actions` 一次性处理，不要反复猜测。

## 6. 6月30迁移步骤

1. 当前 Mac 停止本地 launchd（如已安装）。
2. 复制仓库、Stage 1 migration package、`$HOME/.adp/arxiv-daily-push` state 目录到新电脑。
3. 在新电脑运行 `migration verify`、`restore`、`runtime-audit`、`local-runner preflight`。
4. 运行一次 `local-runner daily --allow-smtp-send` smoke test，确认 queue、ledger、email preview 和真实 SMTP 发送证据都生成。
5. 生成并安装新电脑 launchd 包。
6. 运行 `local-runner readiness --require-smtp --require-scheduler`，确认 pass。
7. GitHub 继续只记录代码、PR/CI、证据和状态，不作为每日生产 runner。
