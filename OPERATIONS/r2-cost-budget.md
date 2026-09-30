# R2 周期任务预算与存储维度

> 2026-09-30 从根 `AGENTS.md` 移出（根 `AGENTS.md` 必须 <=4096 字节）。
> 云成本红线本身（禁 `InfrequentAccess`、禁高频整包校验、周期任务先算月操作量、存储优先级
> GitHub Release 资产 > R2 > OVH 本地）以工作区 `GithubProject/README.md` **铁律 7** 为唯一真源，本文件不复制；
> 这里只保存那份真源里没有的「R2 周期任务清单与预算」实测表与存储维度。数字是 2026-08 的实测，改任务前先现扫。
>
> 完整事故记录、账单逐行归因、免费额度速查表 → `Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7。
> 机器守卫 → OVH `/usr/local/bin/linze-r2-free-tier-guard.py`（本仓副本 `OPERATIONS/host-bin/linze-r2-free-tier-guard.py`，
> 每 6 小时跑，非 Standard 桶自动熔断改回；判定 `/srv/linze/apps/status/data/r2_free_tier_guard.json`）。

## R2 周期任务清单与预算（改动前必读）

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
