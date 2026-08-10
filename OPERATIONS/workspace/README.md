# GithubProject —— 本机唯一工作间

本目录是**本机所有 agent（Codex / Claude Code）的唯一工作间**，一比一对标 GitHub `LinzeColin` 的 8 个仓。
你在 GitHub 上看到几个仓，这里就是几个文件夹，一眼对得上。

> 旧结构（`main_worktree/`、散落的日期文件夹、14G 单体克隆、runtime_*、backups）**已于 2026-07-17 全部淘汰清除**，

## 8 仓结构（目标态）

| 仓 | 装什么 |
|---|---|
| `CodexProject/` | `WDA`(退休) + Golden Path 可复用工作流（`arxiv-daily-push` 已于 2026-07-20 迁去 `MetaDatabase/`） |
| `KMOS/` | KMFA、KM_IDSystem、whkmSalary、KMDatabase |
| `MetaDatabase/` | Alpha、EEI、FIFA、LinzeDatabase、QBVS、Serenity-Alipay、PFI、ADP |
| `AgentDatabase/` | MemoryAtlas、OpenAIDatabase |
| `Governance/` | 双平面治理标准与工具（共享） |
| `LinzeHomeHub/` | 前端门户 |
| `NotionStudyProject/` | 学习笔记（内容归档，不套软件治理） |
| `Archive/` | 冷归档（CodexTokenMonitor、EVA_OS 已双平面；COM1005/回归课程/nab 为内容归档） |

**目录按需出现** —— 你要动哪个仓才 clone 哪个仓。没 clone 的仓不是缺失，是铁律 1 生效。

## 七条铁律（所有 agent 必须遵守）

1. **按需 clone，非必要不全下**。只 clone 你要动的那个仓，只 checkout 你要动的那个子项目：
   ```bash
   cd ~/Documents/Codex/GithubProject
   git clone --filter=blob:none --sparse git@github.com:LinzeColin/<REPO>.git
   cd <REPO> && git sparse-checkout set <子项目目录>
   ```
   `--filter=blob:none` 只在需要时拉文件内容，`--sparse` 只落地你要的子项目。**不要 clone 整仓全内容。**

2. **主树只读，开发一律在 worktree**。这条既是「干净」的前提，也是「并行」的前提。

   **主工作树（`GithubProject/<REPO>/`）永远停在 `main`、永远干净、只 `git pull` 不写。**
   它是参考副本，也是所有 worktree 的 base。**不要在主树上切分支，不要在主树上留未提交改动。**

   **一个 session / agent 一个 worktree**：
   ```bash
   git worktree add ../_scratch/<repo>-<任务名> -b <分支名> origin/main
   ```
   > **为什么必须这样**：git worktree 是 Claude Code **唯一**的并行隔离机制，没有第二种。
   > 两个 session 挤同一个物理工作树会互相踩文件和 git index —— app 拒绝并行是对的，那种「并行」本来就会出事。
   > 主树被人占着（切了分支 / 留着脏改动），等于这个仓的并行被一个人锁死。

   > **project 怎么开**：一个仓开一个 project（8 个），根指到 `GithubProject/<REPO>`。
   > **不要在 `GithubProject` 父目录上开 project** —— 它不是 git repo，拿不到任何隔离。
   > 桌面版可在 Settings → Claude Code → Worktree location 指到 `~/Documents/Codex/GithubProject/_scratch/`。

3. **谁开的谁收：干完自己合并、关闭、清理，不留隐患和垃圾。**

   开发过程中 worktree / branch / PR 随便开，**但收尾是开的人自己的事**，不是留给别人扫。
   一个任务算完成 = 代码合了 + PR 关了 + worktree 收了 + 分支删了 + 缓存清了。**五件缺一件都不算完成。**
   ```bash
   gh pr merge <PR#> --delete-branch        # 合 PR，同时删远程分支
   git worktree remove ../_scratch/<path>   # 收工作树
   git worktree prune                       # 清 worktree 元数据
   git branch -d <已并入的分支>              # 删本地分支（-d 会拒绝未合并的，别改成 -D）
   git gc                                    # 回收松散对象、压缩存储
   ```
   > ⚠️ **`git gc` 不要加 `--prune=now`。** 它会**立刻**销毁不可达对象，没有后悔药。
   > 「仓库拆分」线程就是在这条上丢掉过 2467 个提交且不可恢复。不加参数的 `git gc` 有两周宽限期，够安全。

   > 旧结构就是死在这一条上：13 个 worktree 挂在一个 14G 的共享对象库上，谁也不敢删。**不要重蹈覆辙。**
   > 本机只有一块盘。每个人留一点垃圾，就是所有人一起卡死。**开得出，必须收得回。**

4. **不跨仓**。一个仓 = 一个 project 根。不要在 A 仓里放 B 仓的东西。

5. **`_protected/` 永不删、永不上传**。里面是 KMFA 技能与私有运行时、信息费更新、交付物、Alpha 工作产物、清理前的 stash 兜底。

6. **`_scratch/` 放临时产物**，随时可清。**不要再在根目录建日期文件夹**（旧结构的乱源）。

7. **云端零付费：不许任何 agent 触发收费行为，账单恒为 $0.00。**（2026-08-07 R2 被计费 $9.92 后加）

   - **禁止 `InfrequentAccess` 存储类** —— 建桶、写对象、生命周期转换，一律不许。
     R2 的免费额度（10GB 存储 / 100 万 Class A / 1000 万 Class B）**只覆盖 Standard**；
     IA 从第 1 次操作起计费，且**按整计费单位向上取整**。
     > 实账单：**51 次 IA 操作 = $9.00**；同一周期 **301 万次 Standard 操作 = $0.00**。
     > 根因是建桶时默认存储类选了 IA，而写入端不指定存储类就全部继承 ——
     > **一次手滑，之后每天静默自动计费，账面上完全看不出来。**

   - **禁止"整包下载来判断存在 / 做校验"的高频轮询。** 判断对象存在用 `HeadObject`
     （写入时把 sha256 放进对象 `Metadata`，Head 就读得到）；真要逐字节复核，
     **按天或按周跑，不许按分钟跑**。
     > 反例：memory-atlas reconcile 每 15 分钟把 2466 个对象整包拉一遍核 sha256，
     > 折合 71 万次 Class B/天、21.3M/月，直接打穿 10M/月的免费额度。

   - **新增或改动任何周期性任务，先算月操作量**：
     `每轮操作数 × 每天轮数 × 31 < 免费额度 × 50%`。**算不出来就不上线。**

   - **存储优先级：GitHub Release 资产 > R2 > OVH 本地。**
     Release 资产不计仓库体积、没有操作计费，永远优先。

   - **未来新增项目和周期任务默认禁止写 R2。** 只有 Owner 单独授权，并且机器守卫对同一计费周期
     直接证明全部桶为 `Standard`、无非 Standard 对象、最坏情况新增存储和月操作量都低于免费额度
     40%，才允许提出启用；证据缺失、过期或任一指标达到 40% 就 fail-closed 跳过 R2。
     Memory Atlas 每日完整备份固定走 GitHub 私有 Release，R2 必须是
     `SKIPPED_ZERO_CHARGE` / `billable_requests=0`。

   完整事故记录与免费额度速查表 → `Private-Database` 仓 `OPS/AGENT_ONBOARDING.md` §9.7。
   机器守卫 → OVH `/usr/local/bin/linze-r2-free-tier-guard.py`（每 6 小时跑，非 Standard 桶自动熔断改回）。

## 收工自检

**开工前和收工后都跑这一条**（2026-08-10 起，取代下面那段手抄循环）：

```bash
bash ~/Documents/Codex/GithubProject/tools/workspace-doctor.sh
```

它逐仓实测铁律 2 / 铁律 3，退出码 0 = 全绿。`--fix` 会顺手做安全的自动修复（干净主树补 pull）。
不安全的（收 worktree、删分支）只报不做 —— 那是开的人的事。

### 机器守卫（不是文档约定，是真的拦得住）

- `tools/install-guards.sh` 给 8 个仓装 `pre-commit` hook：**在主树的 main 上 commit 直接被拒**，在 worktree 里不受影响。
  逃生口 `LINZE_ALLOW_MAINTREE_COMMIT=1`，用之前先想清楚为什么不开 worktree。
- hook 不进 git（`.git/hooks/` 不受版本控制），**clone 新仓或重建 `.git` 之后要重跑安装脚本**；doctor 会检查它还在不在岗。

> **铁律 2 里的「不写」包括不写产物。** 2026-08-05 有线程直接在主树目录里跑了
> `Serenity-Alipay` 的 preflight，输出写进工作树 → 主树脏了 6 天 → `pull --ff-only`
> 一直失败 → 落后 45 个提交。破规的人未必是在主树上改代码，**在主树里跑任何会写文件的
> 程序（测试、preflight、采集脚本）都算**。产物一律写到 `_scratch/`。

<details><summary>旧的手抄自检循环（留档）</summary>

```bash
cd ~/Documents/Codex/GithubProject
for r in */; do
  [ -d "$r/.git" ] || continue
  echo "=== $r"
  echo "  主树分支: $(git -C "$r" branch --show-current)"       # 应为 main
  echo "  主树脏文件: $(git -C "$r" status --porcelain | wc -l)"  # 应为 0
  git -C "$r" worktree list | sed 's/^/  /'                     # 应只剩主树一行
done
du -sh ~/Documents/Codex/GithubProject   # 应保持在最小必要
```

</details>

收工后每个仓应是三条全中：**主树在 `main`、0 个脏文件、`worktree list` 只有主树一行**。

- 主树不在 `main` 或有脏文件 → **违反铁律 2**，这个仓的并行被你锁死了，先把改动挪进 worktree。
- 多出来的 worktree → 必须对得上一个**正在进行**的任务。对不上的就是垃圾，按铁律 3 收掉。
