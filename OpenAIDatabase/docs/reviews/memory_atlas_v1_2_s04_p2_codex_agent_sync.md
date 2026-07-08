# Memory Atlas v1.2 S04 P2 Codex/Future Agent Sync

任务 ID：`MA-V12-S04P2`。

验收 ID：`ACC-MA-V12-S04P2`。

状态：`phase_s04_p2_codex_agent_sync_completed_pending_s04_p3`。

## 结论

S04 P2 完成 Codex local sync 和 future-agent minimal adapter 的最小可运行同步面。
本 phase 使 `atlasctl.py sync --source codex --dry-run` 和
`atlasctl.py sync --source future-agent --dry-run` 返回 no-write 合同，并让 apply 路径
按 raw + derived + run log 输出。

## 文件

- `scripts/sync_codex_memory_data.py`
- `scripts/sync_future_agent_data.py`
- `scripts/atlasctl.py`
- `机器治理/同步与备份/codex_agent_sync_policy.v1_2_s04_p2.json`
- `人类可读/10_Codex与FutureAgent同步.md`
- `tests/test_s04p2_codex_agent_sync.py`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p2.cjs`

## 验收点

- Codex local sync 支持 dry-run，不写文件。
- Codex apply 输出 append-only public raw snapshot、derived summary 和 sync run log。
- future-agent minimal adapter 支持 dry-run，不写文件。
- future-agent apply 必须提供本地输入，输出 public raw、derived summary 和 sync run log。
- atlasctl 覆盖 ChatGPT、Codex、future-agent 和 build-atlas 的可运行入口。
- credential is not memory；凭证样式内容被 fail closed。

## 边界

- No GitHub main upload in this phase。
- 不实现 GitHub backup dry-run/apply；那是 S04 P3。
- 不读取或保存密码/验证码。
- 不修改 ChatGPT 会话状态。
- 不生成伪数据；缺少 future-agent 输入时必须停止。

## 验证命令

- `python -B -m unittest OpenAIDatabase.tests.test_s04p2_codex_agent_sync -q`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.2-s04-p2`
- `python3 OpenAIDatabase/scripts/privacy_guard.py --database-dir OpenAIDatabase --scan-only`
- `python3 OpenAIDatabase/scripts/raw_archive_manifest.py audit --database-dir OpenAIDatabase`
- `pnpm --dir OpenAIDatabase/apps/memory-atlas run lint`

下一步是 S04 P3。
