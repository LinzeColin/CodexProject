# Adversarial review · ADP-S5-P03-T064｜Research Set / 结构化比较 / 筛选

独立对抗复核（general-purpose skeptic，两轮），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 可回原文（offset/length/quote 与 value 漂移、strip/CJK 多字节/句界/首末 marker/重复 marker）；(b) 缺失不猜（空值 marker、词内子串假配如 methodology、裸统计假阳、missing 是否真判别）；(c) 筛选可重复（跨输入序确定性、平凡全/空、大小写）；(d) comparison table（present 带证据/missing 带标记）；(e) 非空跑（每条款有判别负控制、verifier 从工具而非 report 现推、Golden Set 是否充分）；NOT_DEPLOYED（无网络/写/时钟/随机）。

## 第一轮：CONFIRMED_SOUND（三条款均稳固，列 2 项精度残留）
- **(a) 可回原文**：复核者自造 leading/trailing/全角/tab 空白、空值 marker、marker 在末尾、无句界结尾、句界字符在值内、重复/重叠 marker、CJK 多字节——**逐例 `text[off:off+len]==value==quote`**；offset 经 lstrip 计数收紧、length=len(strip)，构造上保证一致。幻觉负控制（值不在 offset 处）令 `traces_to_source` 返回 False → **判别有效**。
- **(b) 缺失不猜**：标签需 `[:：]` 冒号 → `methodology`（无冒号）不误配；空值 marker、marker 在末尾均正确报 missing；抽取器只吐原文逐字子串；guess-default（"N/A"@0）负控制被 traceability 拒。
- **(c) 筛选可重复**：全 3! 输入排列产出同一 sorted 结果；非平凡 + 精确期望 + 两 filter 不同控制齐备。
- **(d)**：present cell 恒带证据、missing cell value=None，无"present 无证据"。
- **(e)**：verifier `RS.make_set(brs.PAPERS)` 从**工具现推**（不读 report JSON）；Golden Set 充分（10 存在 + 5 缺失，中英混，标签 + 裸统计双路径）；三条款各有判别负控制；工具无网络/写/时钟/随机。
- **判定**：**三条款真成立、非空跑/作弊/错**。列 2 项**精度（非验收）残留**：裸 `n=..` 对 "function = 5" 假阳（"n" 为词尾）；ASCII `.` 边界截断小数（"92.5"→"92"）。二者仍为原文逐字节 span、满足验收，但语义欠精。

## 精度残留的主动闭合
1. **小数截断** → `_capture_after` 边界改为 `_is_boundary`：CJK 终止符（。；）+ 换行恒为边界；**ASCII `.` 仅句末（其后空白/文末）才作边界**——小数（92.5%、3.14）不再截断；英文句末 `.` 仍正确成界。
2. **裸统计假阳** → `_SAMPLE_STAT` 加负向前瞻 `(?<![A-Za-z])`——`functio[n]=5` 不再命中，真正独立 `n = 64`/`N = 5`/句首 `n = 5` 仍命中。
3. 文档措辞明确"标签需带冒号"。
- verifier 加 4 条 PRECISION 控制（92.5% 保全 / 88.7 percent 句末正确成界 / function=5 不配 / n=64 命中）。

## 第二轮（复核 DELTA）：CONFIRMED_SOUND（hole=null, severity=none）
- **边界改动安全**：`_is_boundary` 只改**在哪停**、不动 offset/length/strip/quote 数学，故 `text[off:off+len]==value` 证明仍成立；复核者攻 `.` 在文末/换行前/tab/全角空格前、连续 `..`、纯小数值、marker 紧跟 `.`、混排缩写（e.g./Fig. 3/3.14 vs. baseline）——逐例 `slice==value==quote`、`traces_to_source=True`、`.`-在文末短路不 IndexError；**8+ Golden 存在字段逐字节复现、filter 精确**。
- **前瞻安全**：挡词尾字母同时保住句首 `n = 5`、`re.I` 的 `N = 5`、空格前置 `n = 64`、Golden `n = 128`；无合法命中被破坏。
- **4 条精度控制均判别**（回退任一即失败）。纯正则/逻辑改动、仍仅 `import re`、NOT_DEPLOYED 完好。**无新空洞、无 traceability 漂移**。

## 残留（诚实披露，非空洞、非回归、恒可回原文）
- 英文缩写（e.g./Fig. 3/vs.）在 `. ` 处过切；裸 `n=` 守卫仅挡前置 ASCII 字母（`var_n=5`、`中n=5` 仍配）。**二者恒产出原文逐字节 span、绝不编造**，落在三验收条款之外、且 ≥ 修复前行为。语义级缩写/统计消歧留待后续（known_gaps 已披露）。

## 结论
两轮复核均 **CONFIRMED_SOUND**；三验收条款（字段可回原文 / 缺失不猜 / 筛选可重复）有 load-bearing 判别负控制、非空跑。2 项精度残留主动闭合（小数不截断、裸统计假阳消除）并加判别控制，边界改动经穷尽复核证明保持 byte-exact traceability、Golden Set 不变。确定性、零副作用。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
