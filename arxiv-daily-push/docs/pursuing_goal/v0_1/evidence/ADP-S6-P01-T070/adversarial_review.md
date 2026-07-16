# Adversarial review · ADP-S6-P01-T070｜Dataset Snapshot + observed_at 泄漏防线

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 泄漏 guard（是否真 observed_at 驱动、对未来/边界/malformed/缺失是否 FAIL、是否被 snapshot 静默过滤而空跑）；(b) 可重建（rebuild 确定性、snapshot_id 序无关、是否区分不同数据集、碰撞）；(c) 快照正确（<= 含当日、malformed 排除、malformed as_of raise）；(d) 验收控制非空跑（是否**外部注入**未来文档验 guard RAISE、verifier 从工具现推）；(e) observed_at-vs-doc_date 判别（backfill doc_date 是否真 < as_of）；NOT_DEPLOYED。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
- **(a) 泄漏 guard**：obs 恰 == as_of 保留且过；as_of+1、远未来 2030、malformed、**缺失 observed_at** 全被快照排除 **且外部注入时 raise LeakageError**。
- **(b) backfill**：doc_date 2016-05-01（< as_of）但 observed 2026-07-01 → 2018 快照排除、注入触发 guard——**证明按 observed_at 非 doc_date**；fixture backfill doc_date 确 < as_of。
- **(c)**：malformed as_of 在 snapshot 与 guard **均 raise ValueError**（非静默空）。
- **(d)**：verifier **外部注入**未来文档进 `snap['docs']` 并断言 `assert_no_leakage` RAISE，且从工具现推（非 report JSON）——guard 非空跑，即便 snapshot 忘过滤仍会抓。
- **(e)**：rebuild 复现 snapshot_id；**200 次打乱序无关**（单一 id）；不同 as_of、变更 content_hash 均改 id。
- **NOT_DEPLOYED**：无 today()/now()/网络/随机/写（used paths）。
- **判定**：两验收条款（注入未来文档使测试失败 / 任何预测可重建其当时数据集）**真成立、非空跑/作弊/错**。列 2 项**非致命** latent。

## latent 的主动闭合（1 项硬化 + 1 项披露）
1. **snapshot_id 碰撞**（复核指出）：原 id 键 = [canonical_id, observed_at, content_hash|version]——若两文档仅在键外字段不同、或 content_hash+version 均缺则同 id+observed_at 不同正文碰撞。**已硬化**：新增 `_doc_fingerprint`（优先 content_hash/version，否则**全文档稳定哈希**），故不同正文**永不碰撞**；fixture 均带 content_hash 故 id 不变（snap:a2b9b696de61d77f）。verifier 加控制（同 id+observed_at 不同 body / 不同 content_hash → 不同 snapshot_id）。
2. **`_parse_date` 接受非法日（如 2017-02-31）**（cosmetic，**继承 T056** coverage_asof，不分叉）：因 snapshot 与 snapshot_id 用**同一** lexical observed_at 排序键，确定性/序无关仍成立；well-formed YYYY-MM-DD 字典序==时序。known_gaps 述其精神。

## 结论
复核 **CONFIRMED_SOUND**；两验收条款有 load-bearing 判别负控制（外部注入未来文档 RAISE、backfill 排除证 observed_at 键控、rebuild 复现 + 序无关）、非空跑，verifier 从工具现推。snapshot_id 碰撞 latent 主动硬化为内容指纹（不同正文不碰撞）；_parse_date cosmetic 属 T056 继承不分叉。复用 T056 as-of 解析。确定性、零副作用、不读时钟。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
