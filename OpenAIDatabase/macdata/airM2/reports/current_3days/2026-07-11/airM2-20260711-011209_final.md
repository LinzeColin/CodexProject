# airM2 每日明文健康报告

报告日期：2026-07-11
采集时间：2026-07-11T01:12:11+10:00
设备角色：工作前台 / 移动终端 / 云端入口
运行来源：Codex Automation 调用受控脚本
Codex 模型：gpt-5.3-codex-spark
推理强度：xhigh
报告语言：全中文
Time Machine：本任务不采集
iCloud：本任务不使用
本机保留策略：仅保留最近 3 天数据、报告、运行记录和 macdata 临时缓存

一、运行状态

| 项目 | 明文值 |
|---|---|
| 采集编号 | airM2-20260711-011209 |
| 本机任务目录 | OpenAIDatabase/macdata/airM2 |
| 运行状态 | 上传成功并已验证 |
| 上传说明 | 远程分支提交哈希与本地提交哈希一致。 |
| 归档分支 | macdata-airM2 |
| 数据提交哈希 | cf1e03f1291dce16010c90b0c30a6f29ed7c7f89 |
| 报告提交哈希 | 未采集 |
| 远程验证 | True |
| 清理状态 | 已在 raw 数据上传验证成功后清理本机旧数据和 macdata 临时缓存 |

二、设备基础信息

| 指标 | 明文值 |
|---|---|
| 设备名称 | Linzes-MacBook-Air.local |
| 设备型号 | MacBook Air |
| 型号标识 | Mac14,2 |
| 芯片 | Apple M2 |
| 统一内存 | 8 GB |
| 序列号 | XHJ635M9MD |
| 本机用户名 | linzezhang |
| macOS 版本 | macOS 26.5.1 (25F80) |
| 当前电源状态 | 电池 |

三、电池健康

| 指标 | 明文值 |
|---|---|
| 当前电量 | 53% |
| 是否正在充电 | 正在充电 |
| 电源来源 | 电池 |
| 电池循环次数 | 260 |
| 最大容量 | 85% |
| 电池状态 | Good |
| 电池风险等级 | 绿色 |
| pmset 原文摘要 | Now drawing from 'Battery Power'
 -InternalBattery-0 (id=22216803)	53%; discharging; 10:32 remaining present: true |

电池明文判断：若最大容量低于 80% 或系统显示建议维修，优先评估换电池；若长期插电且系统支持充电上限，建议使用 80% 或 85%；如果系统没有显示充电上限，则报告只写“未采集/系统未显示”，不猜测。

四、存储健康

| 指标 | 明文值 |
|---|---|
| 根目录总容量 | 228.27 GB |
| 根目录已用容量 | 185.47 GB |
| 根目录剩余容量 | 42.81 GB |
| 根目录使用率 | 81.2% |
| 黄色预警线 | 剩余空间 < 70 GB |
| 红色预警线 | 剩余空间 < 40 GB |
| 当前存储风险等级 | 黄色 |
| macdata 本机目录体积 | 0.0 GB |
| 下载目录体积 | 0.81 GB |
| 桌面目录体积 | 0.02 GB |
| 文档目录体积 | 23.32 GB |

五、内存与 swap

| 指标 | 明文值 |
|---|---|
| 物理内存 | 8.0 GB |
| 当前 swap 使用量 | 0.84 GB |
| 黄色预警线 | swap ≥ 1 GB |
| 红色预警线 | swap ≥ 4 GB |
| 当前内存风险等级 | 绿色 |
| vm_stat 摘要 | Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                     4833.
Pages active:                                 136808.
Pages inactive:                               133894.
Pages speculative:                              5995.
Pages throttled:                                   0.
Pages wired down:                              84081.
Pages purgeable:                                1774.
"Translation faults":                     4020311563.
Pages copy-on-write:                       183574112.
Pages zero filled:                        1773813230.
Pages reactivated:                         925420563.
Pages purged:                               68048588.
File-backed pages:                            110352.
Anonymous pages:                              166345.
Pages stored in compressor:                   356028.
Pages occupied by compressor:                 121696.
Decompressions:                            797782576. |

六、进程负载摘要

Top CPU 进程原文摘要，尽量只包含进程名称，不采集命令行参数：

```text
Processes: 473 total, 5 running, 468 sleeping, 2677 threads
2026/07/11 01:12:10
Load Avg: 2.35, 2.52, 2.47
CPU usage: 41.44% user, 21.62% sys, 36.93% idle
SharedLibs: 354M resident, 79M data, 77M linkedit.
MemRegions: 130016 total, 2177M resident, 152M private, 597M shared.
PhysMem: 7448M used (1314M wired, 1901M compressor), 167M unused.
VM: 196T vsize, 6144M framework vsize, 7545024(0) swapins, 9326004(0) swapouts.
Networks: packets: 97495018/84G in, 64816624/25G out.
Disks: 125286176/3353G read, 46300389/1499G written.

PID    COMMAND          %CPU MEM
99659  spindump         0.0  20M
99653  deleted_helper   0.0  1936K
99652  FeatureAccessAge 0.0  5216K
99577  neagent          0.0  3456K
```

Top 内存进程原文摘要，尽量只包含进程名称，不采集命令行参数：

```text
Processes: 473 total, 5 running, 468 sleeping, 2688 threads
2026/07/11 01:12:10
Load Avg: 2.35, 2.52, 2.47
CPU usage: 22.11% user, 16.8% sys, 61.80% idle
SharedLibs: 354M resident, 79M data, 77M linkedit.
MemRegions: 130039 total, 2179M resident, 152M private, 597M shared.
PhysMem: 7448M used (1314M wired, 1901M compressor), 166M unused.
VM: 196T vsize, 6144M framework vsize, 7545024(0) swapins, 9326004(0) swapouts.
Networks: packets: 97495239/84G in, 64816785/25G out.
Disks: 125286191/3353G read, 46300389/1499G written.

PID    COMMAND          %CPU MEM
99072  Codex (Renderer) 0.0  734M
99044  codex            0.0  603M
398    WindowServer     0.0  485M
99071  Codex (Renderer) 0.0  310M
```

七、Air 逐级使用与远程入口状态

| 指标 | 明文值 |
|---|---|
| SSH 配置文件是否存在 | True |
| VS Code code 命令是否可用 | False |
| VS Code 版本摘要 | 未发现 code 命令 |
| GitHub CLI 是否可用 | False |
| GitHub CLI 版本摘要 | 未发现 gh 命令 |
| Codespaces 检查说明 | 仅检查 gh 是否存在；不自动访问 Codespaces，避免额外网络/权限动作。 |

Air 明文使用边界：Air 作为工作前台、移动终端和云端入口；不建议承担 Docker、本地大构建、本地大模型、多服务开发。若 swap 持续升高或剩余空间低于黄色线，应优先转到 Pro 或 Codespaces。

八、Git 与仓库状态

| 指标 | 明文值 |
|---|---|
| 仓库根目录 | /Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject |
| 当前分支 | main |
| 最新提交 | 3d7952b47c6b9f1f31f47ee0d5f7bbe5fbcff3ac test(memory-atlas): harden R6 content matrix |
| 仓库已跟踪 dirty 数量 | 9 |
| 本设备 macdata dirty 数量 | 0 |
| 本设备 macdata 未跟踪数量 | 0 |

九、收益与 ROI 明文分析

| 判断项 | 结论 | 明文依据 |
|---|---|---|
| 是否继续做工作前台 | 是 | 存储风险：黄色；内存风险：绿色；电池风险：绿色 |
| 是否适合本地开发 | 否，仅轻量任务 | Air M2 8GB/256GB 应定位为工作前台、移动终端和云端入口 |
| 是否需要马上换 Air | 否，除非连续红色风险或工作体验明显受损 | 优先降负载、清理、远程 Pro 或 Codespaces |
| 是否需要换电池 | 暂不需要，继续观察 | 电池最大容量风险等级：绿色 |
| 是否需要清理存储 | 是 | Air 黄色线 70GB，红色线 40GB |
| 是否需要更多使用 Pro/Codespaces | 是 | Air 的 ROI 来自移动入口，不来自本地重负载 |
| 本日 ROI 状态 | 中/需处理 | 轻量化越彻底，Air 使用寿命和移动收益越高 |

十、优势、劣势、机会、威胁

| 类型 | 内容 | 对收益的影响 | 风险 |
|---|---|---|---|
| 优势 | Air M2 轻便、低功耗、适合移动办公和远程入口。 | 提升会议、资料整理、Notion、远程连接效率。 | 如果误用为主开发机会迅速降低体验。 |
| 劣势 | 8GB 内存和 256GB 存储限制明显。 | 多任务、浏览器和会议软件容易导致 swap。 | 存储低于黄色线后体验会明显下降。 |
| 机会 | 把 Air 固定为 Pro/Codespaces 入口。 | 延长 Air 寿命，减少换机支出。 | 需要先建立远程工作流。 |
| 威胁 | 本地缓存、下载目录、浏览器标签和会议软件膨胀。 | 可能让 Air 提前进入低体验状态。 | 需要每日监控和三天保留约束。 |

十一、本机三天保留与清理结果

| 项目 | 明文值 |
|---|---|
| 保留天数 | 3 |
| 保留起始日期 | 2026-07-09 |
| 删除旧目录数量 | 0 |
| 删除旧文件数量 | 0 |
| 释放空间 | 0.0 MB |
| 清理说明 | 已在 raw 数据上传验证成功后清理本机旧数据和 macdata 临时缓存 |

十二、缺失项与失败项

| 字段 | 状态 | 原因 |
|---|---|---|
| Time Machine | 未采集 | 用户明确要求暂不采集 |
| iCloud | 未采集 | 用户明确不要 iCloud |
| API key / token / password | 未采集 | 凭证类数据禁止进入 GitHub |
| Docker 清理 | 未执行 | 本任务只观察，不自动清理开发环境 |
| 系统缓存清理 | 未执行 | 本任务只清理 macdata 自身临时缓存 |

十三、下一次检查重点

- 观察存储剩余空间是否越过黄色或红色预警线。
- 观察 swap 是否持续升高。
- 观察电池最大容量和循环次数变化。
- 观察 GitHub 上传验证是否连续成功。
- 观察本机是否严格只保留最近三天 macdata 数据和记录。
