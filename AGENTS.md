# CodexProject Agent Contract

默认中文优先；项目级 `AGENTS.md` 只能加严；细节见 `docs/governance/STANDARD.md`。

## P0：仓库拆分

本仓库正拆分为独立仓库，目录消失是有意迁移，不是数据丢失。

- 禁止从 Git 历史、revert 或备份恢复任何消失的目录/文件；禁止把迁出报告为事故。
- 已迁出：whkmSalary/KMFA/KM_IDSystem->KMOS；Alpha/FIFA/QBVS/MetaDatabase/Serenity-Alipay/EEI/PFI/arxiv-daily-push->MetaDatabase；OpenAIDatabase->AgentDatabase。禁“修复”。
- 数据存 Private-Database，禁 clone。
- 有疑问立即停下询问 owner，禁止自行恢复。
- Agent 历史/会话只沿公开 `LinzeColin/AgentDatabase` 路线交付；只允许通过 credential/public-safety gate 的脱敏摘要或已授权 Release 附件，永久禁止 access-granting material。
- Clean Memory V3 不得改仓库可见性，不得路由到误建的 `AgentDatabase-Private`。

## 永久执行契约

- Active project 必须注册于 `governance/projects.yaml`，并有完整中文
  `功能清单.md`、`开发记录.md`、`模型参数文件.md`；已拆分视图按 canonical facts 按需渲染。
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

---

## 云成本红线：对象存储必须零付费（Owner 硬指令 · 长期有效）

**云端账单必须恒为 $0.00。不允许任何 agent 触发收费行为。**

1. **禁止 `InfrequentAccess` 存储类** —— 建桶、写对象、生命周期转换，一律不许。
   R2 的免费额度（10GB 存储 / 100 万 Class A / 1000 万 Class B）**只覆盖 Standard**；
   IA 从第 1 次操作起计费，且**按整计费单位向上取整**。
   2026-08-07 实账单：**51 次 IA 操作 = $9.00**，同期 **301 万次 Standard 操作 = $0.00**。
   根因是建桶时默认存储类选了 IA，写入端不指定存储类就全部继承 —— 一次手滑，之后静默自动计费。
2. **禁止"整包下载来判断存在 / 做校验"的高频轮询。** 判断对象存在用 `HeadObject`
   （写入时把 sha256 放进对象 `Metadata`，Head 就读得到）；真要逐字节复核，
   **按天或按周跑，不许按分钟跑**。
   反例：memory-atlas reconcile 每 15 分钟把 2466 个对象整包拉一遍核 sha256，
   折合 71 万次 Class B/天、21.3M/月，直接打穿 10M/月免费额度。
3. **新增或改动任何周期性任务，先算月操作量**：
   `每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。**算不出来就不上线。**
4. **存储优先级**：**GitHub Release 资产 > R2 > OVH 本地**。
   Release 资产不计仓库体积、没有操作计费，永远优先。

完整事故记录、账单逐行归因、免费额度速查表 → **`Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7**。
机器守卫 → OVH `/usr/local/bin/linze-r2-free-tier-guard.py`（每 6 小时，非 Standard 桶自动熔断改回；
判定 `/srv/linze/apps/status/data/r2_free_tier_guard.json`）。

### R2 周期任务清单与预算（改动前必读）

云端账单恒为 $0.00，靠的是下面这份预算不被打破。**改这些任务的频率、范围或参数之前，先算月操作量。**
数字为 2026-08-07 实测（Cloudflare GraphQL `r2OperationsAdaptiveGroups`，7 个完整日日均外推）。

| 任务 | 频率 | 桶 | 作用 | 月 Class A | 月 Class B | **一碰就变收费的地方** |
|---|---|---|---|---|---|---|
| `weread-port-r2-oci-backup` | 每日 04:23 | weread-port-private | 加密用户对象镜像到 OCI 异地冷备 | 465 | 0 | **`rclone sync` 必须带 `--fast-list`**。删掉它 → 按前缀逐个列举，实测 15 次 → **9,300 次**（Class A 额度的 28.8%），且随对象数线性增长 |
| `memory-atlas-reconcile` | **每日** | weread-port-private | 核对 R2 是否仍持有 manifest 里的字节 | 434 | **229,338 (2.3%)** | **频率**。原为每 15 分钟 = 21.3M/月，直接打穿 10M 额度。因为 `exists_with_hash()` 对每个对象**整包下载**（2 Head + 1 Get × 2466 对象 = 7,398/轮） |
| `linze-status-r2-mirror.sh` | 每 5 分钟 | primary-objects | status 站数据镜像 | 31,872 (3.2%) | ~200 | **镜像的文件个数**。每多镜像 1 个文件 = +8,928 次/月 |
| weread-port 平台写入（常驻） | 持续 ~56 次/小时 | weread-port-private | 加密笔记 / 跨设备同步的对象写入 | 41,664 (4.2%) | 0 | 随用户活跃度增长。**写入方未逐一归因**，但已确认不是 reconcile（降频后仍在） |
| `social-archive-replication` | 每 15 分钟 | social-archive-e2n-v0004 | 对象复制到多存储 | 3,224 | 19,468 | **`--limit 200` 这个上限**，别放大 |
| `weread-port-private-database-backup` | 每日 04:01 | backups | Private-Database git bundle 冷备 | 190 | ~30 | 有 `UNCHANGED` 短路，**别去掉** |
| `linze-offsite-backup.sh` | 每日 03:40 | backups | 全量加密备份（单对象） | ~60 | ~30 | 别改成分片小块上传 |
| `cyberboss-backup` | 每日 03:35 | cyberboss-cold | CyberBoss 冷备 | 35 | ~150 | — |
| `memory-atlas-action-worker` | 每分钟 | weread-port-private | 有界 owner 动作队列 | ~0 | ~0 | 队列空时不发任何 R2 请求；**队列一旦长期非空，就会变成每分钟打 R2** |
| 其余（adp / sl-* / kmfa / status-evidence） | 每日 | 各自 | 各项目产物 | <900 | <100 | — |
| **合计** | | | | **≈ 8.0% 的 100 万/月** | **≈ 2.5% 的 1000 万/月** | |

**余量**：Class B 有 **40 倍**余量；Class A 有 **12 倍**余量。两者都健康，但 **Class A 历来是先见底的那个**
（修 `--fast-list` 之前它已经到 37%，而 Class B 只有 2.5%）—— 盯额度先盯 Class A。

**改动这些任务时的三条硬规则**

1. **别删这三类参数** —— 它们是额度的直接开关，不是性能调优：
   `--fast-list`（rclone 列举方式）、`--limit`（单轮上限）、`UNCHANGED` / `--skip-if-unchanged`（无变化短路）。
2. **别把日级任务改成分钟级。** 先算：`每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。**算不出来就不上线。**
3. **别用"整包下载"判断对象存在或做校验。** 判断存在用 `HeadObject` 读 `Metadata.sha256`；
   逐字节复核按天/周跑，不许按分钟跑。（`exists_with_hash()` 就是反例，它是这次事故的第二个根因。）

**改完自己核**（不要交给 owner 去发现）：

```bash
ssh ovh 'sudo /usr/local/bin/linze-r2-free-tier-guard.py'
```

它会打印本计费周期 Class A / Class B / 存储对免费额度的投影占比，≥70% 报 WARN、≥90% 报 CRIT，
并把判定写进每日复审清单。完整事故记录见 `Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7。

**存储维度（唯一跨月累积的）**：操作次数每计费周期清零，**存储不清零**。2026-08-10 实测 **4.55 GB / 10 GB = 44.4%**。

| 桶 | 当前 | 状态 |
|---|---|---|
| `weread-port-private` | 3.22 GB | 冻结（memory-atlas 迁出后不再增长） |
| `backups` | 0.96 GB | 冻结（`linze-offsite-backup.sh` 的 R2 写入已停用：`R2_CODE=disabled_zero_charge_policy`） |
| `social-archive-e2n-v0004` | 0.31 GB | **3 天保留封顶**（见下） |
| 其余 7 个桶 | 合计 <0.06 GB | 冻结 |

**social-archive 的 3 天保留（Owner 2026-08-10 定）**

`backups/runtime-db/` 每 15 分钟写一份 1.03 MB 加密快照，而 `prune_runtime_db_snapshots.py`
**只清本地**——它的文件头明确写着「不碰远端副本(R2/OCI/GitHub)，保留期是另一个决定」，
那个决定一直没给，于是 R2 上累积了 **512 份 / 521 MB、+99 MB/天**，是当时账号里唯一还在长的东西。

现由 `social-archive/scripts/prune_r2_backup_replicas.py --apply` 承接（挂在
`social-archive-backup.service`，每日 03:20），保留 **72 小时**，稳态约 290 MB。首次执行删了 258 个 / 234 MB。

> **改动禁区**：① 别删那条 `ExecStart`，② 别把 `--apply` 拿掉，③ 别放宽 `--hours`。
> 脚本的安全底线也别削：**删 R2 对象前先 `HeadObject` 核对 OCI 上同 key 同大小，核不上就跳过不删**；
> 最新一批永远保留；只碰 `backups/<组>/<时间戳>/`，**不碰 `primary-objects/`（那是制品字节，删了就是毁档）**。
> 每份快照有 `r2`/`oci`/`github` 三个 verified 副本，删掉 R2 那份仍剩两份 —— 这是「卸载」不是「删除」。
