# CodexProject Agent Contract

默认中文优先；项目级 `AGENTS.md` 只能加严；细节见 `docs/governance/STANDARD.md`。

## P0：仓库拆分

本仓库正拆分为独立仓库，目录消失是有意迁移，不是数据丢失。

- 禁止从 Git 历史、revert 或备份恢复任何消失的目录/文件；禁止把迁出报告为事故。
- 已迁出：`whkmSalary -> LinzeColin/KMOS`；`Alpha/FIFA/QBVS/MetaDatabase/Serenity-Alipay/EEI -> LinzeColin/MetaDatabase`；治理框架 -> `LinzeColin/Governance`（本仓库暂保留副本）。不得“修复”这些项目。
- 有疑问立即停下询问 owner，禁止自行恢复。
- Agent 历史/会话只沿公开 `LinzeColin/AgentDatabase` 路线交付；只允许通过 credential/public-safety gate 的脱敏摘要或已授权 Release 附件，永久禁止 access-granting material。
- Clean Memory V3 不得改仓库可见性，不得路由到误建的 `AgentDatabase-Private`。

## 永久执行契约

- Active project 必须注册于 `governance/projects.yaml`，根目录直接维护完整中文
  `功能清单.md`、`开发记录.md`、`模型参数文件.md`，禁止 alias/link-only 页面。
- `开发记录.md` 直接含完整 Roadmap：Stage -> Phase -> Task、ID、hours/percentages、
  gates/stop conditions、Acceptance、evidence、rollback、current result。
- ID 格式：`TSK/ACC.<project>.<program>.<sequence>`。每个 run 默认仅处理一个
  project、一个 Roadmap task 与一个 Acceptance；不扫描无关目录。
- `V*_ROOT_LOCK.yaml` 是本文件之下最强项目契约；stage gate 不等于 production acceptance。
- Canonical facts 只写
  `docs/governance/{project.yaml,roadmap.yaml,events.jsonl}`、`VERSION`、`CHANGELOG.md`；
  dashboard、manifest、ledger、summary 是派生/只读证据，不得成为第二事实源。
- 按 `docs/governance/STANDARD.md` 路由 `T0`/`T1`/`T2`/`T3`。
  model/formula/parameter/schema/safety/release/legal/privacy/money/payroll/deletion/live/production
  必须升级到 `T2`/`T3`，fast path 不得绕过。
- 实施前声明读取/修改范围、测试、风险、rollback、stop conditions 与唯一 Acceptance。
  禁止伪造参数、版本、测试、owner decision、incident 或 evidence；`UNKNOWN` 绑定具体 Task。
- `arxiv-daily-push` source/board 的增删改、启停必须通过 user-center sync gate。
- GitHub source-of-truth：持久 product change 必须 commit 并 push 到
  `LinzeColin/CodexProject`；app/cache/WAL/SHM/recovery 不是 product root。
- Zero-Open：Done 需要 focused tests、changed-scope governance、无开放交付 PR；冲突、
  superseded、draft PR 必须关闭并从当前 `main` 重建。

## Run Modes

- `READ_ONLY`、`REVIEW`、`PLAN`、`CI`、Hook 必须 `zero tracked/source write`；
  仅命令契约明确时允许临时证据，禁止 event/version/generator/repair-loop 写入。
- `IMPLEMENT` 只改选定 Task 必需的项目或 root-governance 文件。
- SMTP、schedule、Release upload、paid API、source promotion、production side effect
  仍需独立 gate。

## Low-Token Contract

- 普通 T0/T1 初始上下文 <=12KB、<=5 files；根 `AGENTS.md` <=4KB。
- Shared durable context routes through OpenAIDatabase: use `codex_personalization` and
  load only its `read_order`; never scan raw/private memory paths without owner authorization.
- Agent memory discovery: `OpenAIDatabase/data/memory/agent-memory.json`。
- 只读能证明结论的最小证据；优先 compact deterministic output + `full_evidence_ref`。
- 不默认全文读取 `scripts/lean_governance.py` 或遍历
  `governance/run_manifests`；仅因失败、Task ID、evidence ref 或 root change 按需读取。
- 排除 dependency/cache/generated output/artifact/backup/binary/large data，除非 Task 明确需要。

## Model Definition

Model 包括 math/stat/ML、ranking/scoring、backtest、risk、salary/business formula、
rule engine、heuristic、LLM routing/fallback；stack 名不是 model。无模型项目仍需
evidence-backed `NOT_APPLICABLE` `MODEL_SPEC.md`。
