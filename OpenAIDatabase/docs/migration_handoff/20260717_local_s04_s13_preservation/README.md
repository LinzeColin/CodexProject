# OpenAIDatabase 本地 S04–S13 迁移保全包

状态：`PRESERVED_NOT_INTEGRATED`
生成时间：`2026-07-17T15:14:51+10:00`

## 目的

在 CodexProject 八仓迁移与双平面治理期间，保全唯一旧 checkout 中尚未进入迁移后
`main` 的 45 个本地 OpenAIDatabase 提交。该目录只保存可审查的 source、
governance、test 与 evidence patch；它不会把迁出的旧目录或大型数据重新写回活动树，
也不代表这些 patch 已与迁移后的架构完成语义整合。

## 精确来源

- 原始父提交：`3c7626008c25aeb6b71ddccc0eb9b999e5d3aedb`
- 首个保全提交：`05d2f91a6cfe7c734b175d04fb5d1491799ca579`
- 最后保全提交：`0bc1b83bd37cc93f7316b1abbfbdbc335822eeac`
- patch 数：`45`
- 存储文件数：`46`（第 8 个 gzip 为满足普通 blob 小于 1 MiB 门槛拆成两片）
- 存储字节（deterministic gzip）：`5614879`
- 存储 series SHA-256：`c79feb8be37c63546cb5f0118b5687bc8c9fc1b14bca76981f5fbadc69a4f0e2`
- 解压后 patch 总字节：`38172293`
- 解压后 series SHA-256：`4ee88eb7be9a889308344dcd8540bee13caaa3924e253594a4e36b18fc20e0b9`
- 生成时迁移后 `origin/main`：`12d10f63d15e41cec50026d5dfd2ea0fab5a0e69`
- 完整顺序与主题：[`COMMIT_LEDGER.tsv`](COMMIT_LEDGER.tsv)

存储 series hash 算法为：
`sha256(concat(sort(numeric prefix, then full filename)(filename UTF-8 + stored file bytes)))`。
解压后 hash 使用逻辑数字文件名和解压后的 patch bytes。

## 数据边界

patch 生成时明确排除：

- `OpenAIDatabase/data/**`
- `OpenAIDatabase/macdata/**`

这些路径没有被删除，也不应从旧 CodexProject 历史重新灌回迁移后的活动树。2026-07-17
只读核验确认公开 `LinzeColin/AgentDatabase` 的 `raw-archives-20260708` Release
包含 `chatgpt_raw_export_2026-07-07.zip`，大小 `1473421021`，SHA-256
`52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868`。

## 恢复规则

1. 不要把本目录视为已集成实现，也不要一次性盲目 `git am` 到 `main`。
2. 在迁移完成后的隔离、干净 checkout 中，按 `COMMIT_LEDGER.tsv` 顺序逐 Phase
   解压对应 `patches/<sequence>.gz`；第 8 个 patch 先按顺序连接
   `8.chunk00` 与 `8.chunk01` 再解压。之后使用 `git apply --check` 或
   `git am --3way` 预演。
3. 冲突时保留迁移后根 `AGENTS.md` 的 P0 仓库拆分规则、OpenAIDatabase lean
   governance 边界与双平面七文件架构；禁止恢复已迁出的项目或旧第二事实源。
4. 数据只绑定 AgentDatabase Release/manifest，不复制大型 raw、archive、credential、
   session state 或 private core。
5. 先恢复并重新验证至 S13 Whole-Stage Review，再从 `S14-P1` 继续；不要跳过阶段审查。

## 暂停点真值

- S13 Whole-Stage Review：本地完成，最终 Critical/Important=`0/0`
- TaskPack Phase：`36/50 (72%)`
- 下一 Phase：`S14-P1`，尚未开始
- S08：`FAILED_NEEDS_HUMAN_AUTH`，development-nonblocking
- delivery readiness：`FAILED`
- `TASK-OAI-B-001`：`blocked`
- App/live：未在本保全动作中验证，不得写为 PASS
