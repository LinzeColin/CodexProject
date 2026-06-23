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

## 5. 6月30迁移步骤

1. 当前 Mac 停止本地 launchd（如已安装）。
2. 复制仓库、Stage 1 migration package、`$HOME/.adp/arxiv-daily-push` state 目录到新电脑。
3. 在新电脑运行 `migration verify`、`restore`、`runtime-audit`、`local-runner preflight`。
4. 运行一次 `local-runner daily` smoke test，确认 queue、ledger、email preview 都生成。
5. 只有 smoke test 通过后，再安装新电脑 launchd。
6. GitHub 继续只记录代码、PR/CI、证据和状态，不作为每日生产 runner。
