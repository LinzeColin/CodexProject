# Adversarial review · ADP-S5-P04-T067｜Library / 笔记 / Provenance 导出

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) provenance 完整性（present-but-empty/空白/None/[]/0/False、是否有绕过 _assert_exportable 的路径、save 路径是否校验）；(b) 格式完整性（MD/CSV/JSON 是否无损、逗号/引号/换行/CRLF/CJK 是否破坏字段、CSV round-trip、verifier MD 子串检查是否证明逐条）；(c) 拒绝控制（是否真判别、save+export 双测）；(d) 许可提示（是否逐条必含）；(e) 非空跑（verifier 从工具而非样本文件现推、fixture 是否充分）；NOT_DEPLOYED（无网络/写/时钟/随机）。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
（复核者注：Read 工具一度返回**过期 102 行弱版**，其结论均对**真实在盘 107 行稳健版**得出。）
- **(a) 完整性**：`provenance_complete` 正确拒 None/[]/空白串（`isinstance(v,str) and not v.strip()`），正确**接受真值 0**；空白绕过（" "/"\t"/"\n"）save+export 均拒；三导出全经 `_assert_exportable`，add_to_library 亦校验，**无绕过路径**。
- **(b) 格式完整**：CSV 经 DictWriter/DictReader 对**逗号/双引号/\n/\r\n/CJK 无损 round-trip**；JSON round-trip；MD 即便含换行仍保留值为子串。committed CSV 样本与工具逐字节一致（初始 diff 仅 `\r\n→\n` 读回译码假象）。
- **(c) 拒绝控制**：**真判别负控制**——save（BAD_ITEM）与 export（空 license 混入条目，三格式）双测；移除校验即失败。
- **(d) 许可**：`PROVENANCE_FIELDS` 含 license，逐条在三格式必含且被检。
- **(e) 非空跑**：verifier 从**工具现推**（import library_export 调其函数，不读样本文件）；fixture 充分（中英 + 笔记 + collection + format-hostile）。
- **NOT_DEPLOYED**：工具仅 import csv/io/json——无网络/时钟/随机/写；生成脚本仅写声明证据；verifier 无副作用；两次运行输出一致。
- **判定**：验收（三格式每条含 URL/版本/抓取时间/证据/许可）**真成立、有判别负控制、非空跑/作弊/错**。列 3 项**非致命** latent。

## latent 的主动闭合（3 项）
1. **verifier MD 标签检查曾为全串子串**（复核者读到的是并发编辑前版本）：**当前 verifier 已改为逐条 block 重导校验**（`block = export_markdown({entries:[e]})`，每条 block 须含全 5 标签+值），非全文档子串——已闭合。
2. **verifier 空判用 falsy（`if not ...`）会误拒真值 0**：**已改为复用工具的 `LX._is_blank`**（None/[]/空白=缺，0 算有），与工具语义一致；自检 `0 accepted=True / blank rejected=True`。
3. **add_to_library 错误消息 `missing` 列表用 falsy**（会把 0 误列为 missing，仅错误文案）：**已改用 `_is_blank`**；并抽出模块级 `_is_blank` 供 `provenance_complete`/错误消息/verifier 三处共用，语义单一。

## 结论
复核 **CONFIRMED_SOUND**；验收（三格式逐条含 5 项 provenance + 许可提示）有 load-bearing 判别负控制（缺 provenance save+export 双拒）、非空跑，verifier 从工具现推。3 项非致命 latent 主动闭合（MD 逐条 block 校验、空判统一 `_is_blank` 接受 0 拒空白、错误消息一致）。确定性、零副作用、不读时钟。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
