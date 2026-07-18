# ADP-V02-P13 — /api/runhealth + watchdog 抓 P08 的真实病

状态: **CONFIRMED_SOUND**（独立对抗复核 2 轮：R1 BLOCK 属实且致命，R2 CONFIRMED_SOUND；实施者未自签）
release_mode: **PRODUCTION** — `e8491f75970f` → `9df554e13297`（Version 96afed49-d7eb-48e9-9485-34bec48c87ae）

## 为什么
长期稳定 watchdog(上一阶段)能抓摄入/选择的静默零，但**抓不到 P08 的真实病**：元数据补全被 429 限流
打成 0(补 0 条元数据)，而摄入/选择正常——绿着补 0。原因：公共端点不暴露每轮 meta 计数。

## 做了什么
- worker 加**只读**端点 `/api/runhealth`：暴露最近一次【真正跑过】的运行的解析后 counts(含
  `meta{requested,matched}` 与 `degraded`)。一次 D1 SELECT，`writes_nothing:true`。
- watchdog 据此判 P08。

## ★关键：为什么读 degraded 而不是只看 matched★
真 P08 是 **429 风暴** → `enrichMeta` 在 `errs===dois.length` 时**早退**(`worker:775`)，在设
`counts.meta`(`worker:812`)**之前**就 return，故那晚 `meta` **根本未设**、不是 `matched:0`。唯一幸存
的信号是 worker **特意**留在 `degraded` 里的 `meta:http429` 标记(worker 注释：「429 正是让 P08 隐形
整整一轮的那个信号」)。所以 watchdog **必须读 degraded**。判据：degraded 有 `meta:` 错误标记 且
(meta 未设 或 matched=0) → 红。

## 不误报
全 404(matched=0 但**无** meta 错误标记)= DOI 确实不在 OpenAlex，是**知识**不是故障 → 不报警。

## 复核(2 轮)
- **R1 BLOCK(致命)**：watchdog 号称防 P08 却**看不到 P08**——只看 `meta.matched`，而 429 风暴那晚
  `meta` 未设，端点返回 `meta:null`，检查判良性→绿。复核**逐字复现**。附带查出：端点 5xx 被当 404
  **静默跳过**(watchdog 对自己的盲区盲)、`_get` 丢了 5xx 重试(瞬时 5xx 误红整条路由)。
- **R1 修**：改读 `degraded` 标记(429 风暴现在红)；5xx→`health_fail`；`_get` 恢复 5xx 重试 + 持久 5xx
  才上报。worker **未动**(检测逻辑全在 watchdog；worker 早已在 degraded 里留好信号)。
- **R2 CONFIRMED_SOUND**，未自签。

## 已知残余(如实记，不阻塞)
- 全 404 无法与 **P10 式 DOI 编码回归**区分(两者都表现成全缺席)——本探针不抓，属 P10 单测的活。已在
  docstring 标注，不假装抓得到。
- `matched=0` 且恰有一条无关 meta 错会红——罕见，可接受的灵敏度。

## 上线验证
`/build.json=9df554e13297`；6 路由 200；`/api/runhealth` 200(部署前 404)；watchdog 线上 exit=0 且 meta
检查已激活；18 断言全绿(含 `test_the_429_storm_meta_unset_but_degraded_marked_is_caught`)。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：CONFIRMED_SOUND；已部署）
