@AGENTS.md

> ⚠️ **仓库拆分迁移进行中。禁止恢复任何消失的目录。** 详见 AGENTS.md 顶部的迁移指令。

# Claude Code adapter

## 📍 数据存哪、去哪找（全仓统一，2026-07-19）

**所有原始/业务数据的唯一落地处 = 私有仓 `LinzeColin/Private-Database`**，不再散落各仓。三大数据区：

| 数据区 | 谁的数据 |
|---|---|
| `Private-KMDatabase/` | KMOS / KMFA 经营数据（财务、红圈、绩效） |
| `Private-AgentDatabase/` | AgentDatabase / OpenAIDatabase 会话与派生数据 |
| `Private-MetaDatabase/` | MetaDatabase 各项目数据（含 `arxiv-daily-push` 迁入后） |

铁律：

- **禁止 `git clone` Private-Database**（预计膨胀到 500GB+，clone 会损伤本地机器）；只按需下载单文件。
- **不要把数据留在本地或提交进代码仓**——一律用 SDK 写进 Private-Database。
- Private-Database **只存数据、不存代码**；SDK 放各源仓。
- 读写 SDK `private_db_client.py`（见 `LinzeColin/KMOS` 的 `KMDatabase/machine/tools/`
  或 `LinzeColin/AgentDatabase` 的 `OpenAIDatabase/scripts/`）：`ingest / get / put / list / delete / verify`。
  语言无关协议见 `Private-Database/PROTOCOL.md`；天花板与对象存储逃生口见其根 `README.md`。

## OpenAIDatabase 已迁出本仓

`OpenAIDatabase` 已于 2026-07-17 迁往 `LinzeColin/AgentDatabase`（完整历史保留），本仓不再包含它。
原先此处的 personalization 导入与 `route_agent_resources.py` 均在该仓，**不要在本仓寻找或恢复**。
用户记忆与路由控制平面现由 `LinzeColin/AgentDatabase` 的 `OpenAIDatabase/` 承载。

## 其余

- Project status remains canonical in the selected project's governance files.
- Never read raw/private paths or credentials without explicit Owner authorization.
