# Known gaps · ADP-S8-P03-T090｜最终追溯 + 运行包

## 90/90 终态（诚实）
- **89 COMPLETE + 1 PARTIAL**：T089 的 clause 2（停线演练）已交付，clause 1（14 次连续真实日运行无 Sev-1/2）**日历约束**——Owner 已 **waive 放行**（「先推上线不要因为 soak 阻碍部署上线」）；这是**运营开项**，非开发缺口。故 90/90 **有终态**（含 1 个 Owner-waived 的 partial），但严格「14 日 soak 满足」需操作方跑 14 天 cron。
- **T090 acceptance「90/90 有终态」满足**（每任务 COMPLETE 或 honest PARTIAL）；「P0 有 PASS/waiver」满足（10 PASS + soak waiver）。

## 部署（诚实）
- **已执行生产部署**（Owner 授权）：live 从 b189d3cc0703 → 452f7c5de919，上线 S7 accumulated 改进 + D1 索引。**这是一次累积部署（6 任务）**，非逐项 canary——Owner 指令「先推上线不要因 soak 阻碍」优先于 canary 逐项；每项已单独验证 + 六主题合同逐字节保持 + 回滚目标 d5890974 就绪。
- **行为变化提示**：T080 评分流改为**乐观撤销**（4s 窗口后才写 D1；4s 内离开可能不落一次评分——当天可重评，见 T080 known_gaps）；T081 RUM 采集写 cn_rum（免费档内）。

## 运营开项（next version）
- 14 日 soak 完成（T089 clause 1）→ 关 T090 到严格 90/90。
- held 能力（A1/A2/S5/S6）逐能力 Owner 门晋级（经 T088 canary 框架）。
- CWV 质量错误预算自动停止的部署侧监控接线。

## 依赖披露
- 本 session 装了 pyarrow==17.0.0 + duckdb==1.1.3 到用户 Python3.9 user-site（离线证据依赖，runtime/worker 不用）。
