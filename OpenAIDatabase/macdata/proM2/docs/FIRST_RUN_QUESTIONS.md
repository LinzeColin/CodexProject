# proM2 首次运行确认问题

Codex 在首次运行、配置缺失、设备预检失败、或设备差异出现时，必须先问我以下问题，得到明确答复后才能运行脚本。

1. 当前这台机器是否确认是 `proM2`？当前 owner 覆盖后的预期硬件：MacBook Pro / Apple M2 Max / 32GB / 约 1TB。
2. CodexProject 仓库根目录是否就是当前项目根目录？如果不是，请提供路径。
3. 是否确认使用 GitHub 归档分支 `macdata-proM2` 保存 `proM2` 的完整历史？
4. 是否确认每次运行都 commit + push，且 push 后必须验证远程 commit hash？
5. 是否确认只有远程上传验证成功后，才删除本机 3 天以前的 `proM2` macdata 数据、报告、运行记录和 macdata 临时缓存？
6. 是否确认 Time Machine 暂不采集，iCloud 不使用？
7. 是否确认除 API key / token / password 及等价凭证外，其他设备明文指标都可以进入 GitHub？
8. 是否确认远程上传验证成功后，自动清理 Docker、Homebrew、系统缓存、项目缓存，并且 Docker 默认不使用 `-a`、不清理 volumes，项目缓存只按白名单目录删除？
9. 如果预检发现设备型号、芯片、内存、Git remote、归档分支和预期不同，是否需要继续？若继续，请明确差异和授权。

确认后，Codex 应创建：

```text
OpenAIDatabase/macdata/proM2/config/owner_confirmations.json
```

格式参考：

```json
{
  "confirmed_device_key": "proM2",
  "confirmed_at": "<ISO 时间>",
  "run_full_cycle_confirmed": true,
  "allow_plaintext_device_metrics_to_github": true,
  "allow_github_upload": true,
  "allow_delete_local_macdata_older_than_3_days_after_verified_upload": true,
  "allow_development_cache_cleanup_after_verified_upload": true,
  "understand_no_timemachine_no_icloud": true,
  "understand_scripts_do_not_auto_schedule": true,
  "repo_remote_name": "origin",
  "archive_branch": "macdata-proM2",
  "notes_cn": "不要在此文件写入 API key、token、password。"
}
```
