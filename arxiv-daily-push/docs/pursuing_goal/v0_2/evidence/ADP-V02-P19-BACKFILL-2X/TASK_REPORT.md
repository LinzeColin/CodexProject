# ADP-V02-P19 — 回填吞吐 2x：第二个回填 cron 槽

状态: **CONFIRMED_SOUND**（独立对抗复核：线上自哈希亲算、两项破坏测试重放双杀、两槽幂等全交错对抗推演通过、零预签；审查者如实声明验证边界——CF 触发器挂载以旁证链核实，首夜双跑为时间门。实施者未自签）
release_mode: **PRODUCTION** — `d0ebaee1f43c` → `983af33c8352`（脚本先行部署；三调度 2026-07-20 挂载成功）

## 为什么（P12 自己的门开了）
P12 的 stop_condition：「读到 backfill_last.ms 之前不要加大 PAGES」。首跑已实测 **ms=11736**（1 页 1300 行、零降级）
——提速门正式打开。现状 1 页/夜 ≈ 5 天 arXiv，补完 2016+ 约 **2 年**，对「全面」太慢。

## 做了什么（选保守路线）
- **不提 PAGES**：单 invocation 双倍 XML 解析 CPU 未实测（免费档 CPU 上限含糊）——不赌。
- **加第二个回填 cron 槽 `30 2 * * *`**：每 invocation **独立** 50 子请求预算，运行剖面与已验证首跑
  **完全同型**（11.7s / 1300 行 / ≈19/50 子请求）；游标单调 + OAI-busy 不推进，两槽天然幂等。
  吞吐 2 倍：补完周期 2 年 → **约 1 年**。
- 顺带修 127 行**陈旧预算注释**（旧「33/50」；实测账：1 fetch + ceil(1300/80)=17 个 D1 batch + 游标写 ≈ **19/50**）。
- `/api/backfill` 增 `pages_per_run` / `runs_per_day`，`pages_per_night` 语义改为每夜总页数=2（grep 证实无外部读者）。

## 过程发现（如实）：CF 10072 与废弃 worker 的空转 cron
首次挂载第三触发器撞 **CF 10072「账号 cron 触发器上限 5 已满」**（基建注册表 23 行本就记着这条约束——先查自己的注册表）。
证据链闭合：`/system` 运行日志**每日两条「幂等跳过」** = 废弃 adp-mirror worker 的旧 cron 仍每晚空转打生产 D1
（被幂等守卫挡住），并占满槽位。**Owner 2026-07-20 授权后只摘其触发器**（`wrangler triggers deploy` 空 crons，
worker 本体未动、摘后仍 200）；随后 adp-cloud 三调度挂载成功。基建注册表 dormant 条目已如实更新。
副产品：消除了「死 worker 每晚打生产库」的运维异味，/system 的幂等跳过行自明日起应消失。

## 验证（守卫 + 负控 + 部署证据；首夜时间门如实声明）
- **路由守卫**（P12 的 config↔handler 一致性设计）对新槽**自动成立**（不硬编码时间的好设计）；
  另加**吞吐政策 pin**：≥2 个显式路由的回填槽（防止有人把第二槽连根拔掉时守卫仍绿的静默减半）。
- **负控（实跑）**：去掉 `'30 2'` 路由分支 → 守卫真 FAIL（吞吐 pin + else 分支检查双杀），还原后 OK。
- 部署证据：triggers deploy 输出三调度；`/build.json=983af33c8352`；`/api/backfill` 新字段 live；
  adp-mirror 摘触发器后 200。存证 `test-results/deploy_and_slots_evidence.txt`（含 10072 原始错误）。
- **首夜双跑证据是时间门**：02:30/08:30 UTC 两跑后，明晨读 `/api/backfill`——游标应前进**两个窗口**
  （对比今晨单跑前进一窗）。liveness watchdog（22:00 UTC）继续自动兜底。

## 复核修正一处小账
审查者复算子请求账：≈**20**/50（我 127 行注释写 ≈19，漏计 last_run 写入）——近似成立、余量巨大，复核记为非问题；如实记录于此，不为一行注释重新 stamp+部署。

## 诚实边界
- 每 invocation 剖面与已验证首跑同型是**设计等价**（同代码同 PAGES 同预算），非双跑实测——首夜证据补上。
- 摘 adp-mirror 触发器属 Owner 授权的**最小操作**（只动调度）；worker 本体删除仍属 Owner 控制台决策（注册表 disposition 不变）。
- 账号 cron 槽现占 3/5（全部 adp-cloud）；留 2 空槽。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：CONFIRMED_SOUND；三调度已挂载，首夜双跑证据明晨读取）
