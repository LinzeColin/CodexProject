# ADP-V02-P14 — /system 来源健康与维护看板（T044 可操作半部）

状态: **CONFIRMED_SOUND**（独立对抗复核 2 轮：R1 BLOCK 属实，R2 CONFIRMED_SOUND；实施者未自签）
release_mode: **PRODUCTION** — `9df554e13297` → `24ffba0cdecf`（Version 0078911e-f5d1-4993-a657-bf1bc324c2bd）

## 为什么
`cn_sources` 里 `healthStmt` 一直在写 `health / consecutive_failures / last_fetch`，但 /system 只把它做成
一个汇总徽章，**从不逐源细列**。P09 查出的 6 个被数据中心 IP 挡住的官方源，在页面上看不清是哪几个、坏到什么程度。

## 做了什么
/system 加**只读**「来源健康与维护」卡片：每源 健康（正常/降级/自动停用）、连续失败数、上次抓取（尝试）距今、
陈旧★。需要关注的（自动停用 › 降级 › 陈旧）排前面。`maintenanceGrid` 一次只读 `SELECT cn_sources`，
`maintenanceHTML` 排序渲染，`try/catch` 兜底不带 /system 下线。

## 诚实边界
这是 T044 的**健康/维护**半部，**不是「单位成本」**——每源子请求成本没被采集，不臆造成本数字。
`last_fetch` 是**上次抓取尝试**（healthStmt 成功/失败都写），不是上次成功；文案已如实标注。

## 复核（2 轮）
- **R1 BLOCK（属实）**：`s.fails` 是这张表**唯一**没过 `esc` 的 DB 值，违反本文件「每个 DB 值都转义
  （连 health 枚举都 esc）」的铁律，且我的测试没喂非数字值、漏了这条 sink。潜伏/纵深防御型注入
  （现网写路径只有 healthStmt 写整数、外部触发不了），但确是客观缺陷。
- **R2 修**：`${s.fails ? esc(s.fails) : '—'}`（保留 0 显示「—」）；验证器补 3 条 sink 覆盖断言
  （承重：退回裸拼→污染泄漏）；`age_days` 加 `Math.max(0,…)` clamp 未来时钟。复核**穷尽扫**了
  maintenanceHTML 全部 12 处插值，确认再无裸拼 DB 值。R2 CONFIRMED_SOUND，未自签。

## 上线验证
`/build.json=24ffba0cdecf`；6 路由 200；/system 渲染出维护卡片（登记 37 源、异常 6 排前，6 个被墙源一目了然）；
验证器 13 断言全绿（含污染 fails 转义）。

## 非阻断处置（复核已接受）
- 重复扫 cn_sources：保留独立查询不合并（coverageGrid 是 P09 复核过、带承重注释的；约 74 行/次对 5M/天可忽略）。
- 验证器硬编码 SELECT + 重实现 grid()：真 sink 抽取实测；已披露的保真度限制。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：CONFIRMED_SOUND；已部署）
