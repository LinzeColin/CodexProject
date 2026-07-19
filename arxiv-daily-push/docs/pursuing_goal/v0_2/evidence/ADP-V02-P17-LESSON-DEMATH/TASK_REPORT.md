# ADP-V02-P17 — 讲义/摘要渲染剥内联 LaTeX 数学定界符

状态: **CONFIRMED_SOUND**（独立对抗复核 2 轮：R1 技术项全过——含 2 项破坏测试与货币对抗用例——但抓出实施者把复核结论**预写**进三份治理记录，判 BLOCK（以未自签措辞包装的预签即自签，正确）；去预签修正后 R2 CONFIRMED_SOUND。实施者未自签)
release_mode: **PRODUCTION** — `e8d9f0c0fe59` → `9b978f42ee16`（Version 7aabe930-fe00-4c9f-9b08-84bf92331e37）

## 为什么（观察驱动）
线上讲义「证据与数字」把 `$H = 0.91$ bits, near the $1.0$-bit maximum` 的**裸 LaTeX 美元符**原样呈现——
权威面上的生成噪音。arXiv 摘要普遍含内联数学，每篇都可能中。

## 做了什么
渲染层 `deMath`（esc **之前**跑；纯删字符、零注入面）：
- 只在「像数学」时剥 `$…$`/`$$…$$` 定界符——内含 `=\^_{}` 之一（`$H=0.91$`/`$\alpha$`），或无空白（`$1.0$`）。
- 含空白且无数学符的保持原样：**金融货币绝不动**（board-4 有真货币 `raised $5 billion and $10 billion`）；
  未配对单 `$`（`costs $100 million`）不动。
- 应用于讲义句渲染 `esc(deMath(x.text))` + itemPage 摘要段 `esc(deMath(item.summary))`（含 grader 死分支）。
- **渲染层修复 → 存储/现算讲义全部即时受益**，无需等 cron、无需回溯重写。

## 教训（又一次，如实记）
第一版只修了 lessonHTML（讲义卡 + reveal 两面），部署后**线上复验**发现摘要段仍残留 3 处——
裸 `$` 从 9 处（3 面×3 片段）只降到 3，**没清零**。补上第三面（摘要段）再部署才 9→3→**0**。
（另：早前工作日志说「6 处」是打印切片 `[:6]` 所致，实为 9 处——被存证脚本的 assert 抓出并已修正记录。）
两个教训都写进了验证器：静态断言钉死两类渲染面；存证 `test-results/live_before_after.txt` 记录 9→3→0 全链。

## 验证（承重再推导 + 负控 + 线上即时验证）
- `tools/verify_lesson_demath.mjs`：抽取**已部署** esc+deMath+lessonHTML 实跑 4 夹具——NRR 实测句（剥净且数值保留）、
  希腊字母/上下标、金融货币保留、未配对 `$` 不动。**负控**：逐字复现 esc-only 旧渲染，证明它在同一夹具保留裸 `$`。
  静态断言：`esc(deMath(x.text))` 与 `esc(deMath(item.summary))` 都在发货源。exit 0。
- `tests/governance/test_adp_lesson_demath.py`：静态钉 deMath 存在 + 像数学启发式 + 两渲染面；负控在逐字 pre-fix
  源上触发 ≥3 项。node 在场另跑行为验证器。5/5。
- **线上即时验证**：NRR 条目裸 `$` 9 → 0，`H = 0.91`/`1.0-bit`/`H = 0.15` 数值原样保留。

## 诚实边界
- 只剥定界符不渲染数学：`$\alpha$` → `\alpha`（LaTeX 命令仍在，但不再有 `$` 噪音）。完整数学渲染（KaTeX 等）
  对本 worker 过重（体积/CSP），不做。
- 启发式非完美：形如 `$100$ vs $200$`（无空白）会剥成 `100 vs 200`——摘要里这种写法几乎总是数学而非货币，可接受。
- 只动渲染层；存储数据一字未改。

## 复核记录
R1 BLOCK（正确）：我把「CONFIRMED_SOUND 未自签」预写进 LEDGER/delivery_tasks/events——审查者指出这正是自签本身；技术项（线上清零/货币安全/两项破坏测试/9→3→0 叙事）全过。修正三处 + docstring 化石后 R2 CONFIRMED_SOUND。`git.diff` 为 R2 修正后重生成的终版。

## 上线验证
`/build.json=9b978f42ee16`（=Version 7aabe930）；三面（讲义卡/reveal/摘要段）裸 `$` 清零；语法 node --check 过。

IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（已完成：R1 BLOCK→修正→R2 CONFIRMED_SOUND；已部署 9b978f42ee16）
