# 独立对抗复核 — ADP V0.2 P01 Factsheet 集成

复核者：独立 general-purpose skeptic（非实施者；实施者不自签）。方法：读 diff + extract_factsheet.py + 全 worker 上下文，力图证伪其安全性。

## 第一轮：BLOCK（抓到真实缺陷）
- **ReDoS（确认）**：`FS_UNIT_RE` `\d[\d,.]*\s*(?:unit)/g` 二次回溯，实测 `"1,"×20000`(40KB)→2295ms，跑在请求路径（today 卡 / itemListHTML 每条 / 条目详情），输入无界，board4 金融内容天然触发；50 条 board 列表可累积到秒级，超 Cloudflare Worker CPU 限。
- 其余 CONFIRMED SOUND：XSS（`esc(k)/esc(v)` 全覆盖，DOI 正则结构排除 `<>"`）；忠实移植（DOI 仅 board1/2，文号仅 board3，单位 board3/4；trailing-strip 与 Python 一致）；null 安全（全字段 guard，全空→[]→''，不抛）；HTML 合法（`<p><span.badge>` 在 .card / .itemrow>.body 合法嵌套）；主题/动效未触（无 data-theme/data-fx/keyframes/heroSection/theme_js/token 改动，复用既有 .badge）；BUILD 自哈希一致。

## 修复
双重防御：(1) 有界量词 `\d[\d,.]{0,39}` → 线性；(2) `factsheet()` 输入 `slice(0,500)/slice(0,2000)` 兜底。

## 第二轮：CONFIRMED_SOUND
- ReDoS 已解（线性证明）：40KB→4.8ms、**400KB→48.8ms（正好 10× = 定义域线性）**、加 slice 后 0.24ms、全数字最坏 `"1"×40000`→7.2ms 仍线性。
- 抽取正确性不变：`3 个百分点 / 50亿元 / 25bps / 1,234.56亿元 / 12.5% / 2.3亿美元 / 50个基点 / 500美元` 全部照常捕获；`{0,39}` 上限远大于最大真实 token，无遗漏。
- BUILD `0864030f7dc8`，`sha[:12]==build_id`，自排除规则复算一致。
- 两处新编辑未扰动此前 CONFIRMED（XSS/忠实/null/HTML/主题动效）。

**终判：VERDICT: CONFIRMED_SOUND**
