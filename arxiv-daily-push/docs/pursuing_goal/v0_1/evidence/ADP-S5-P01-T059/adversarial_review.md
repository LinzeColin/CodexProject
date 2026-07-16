# 对抗复核记录 · ADP-S5-P01-T059（跨板块 Evidence Relation）

用独立 skeptic 对关系层做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) 每 saved 边有证据**：6 种走私无源边(纯空白 fragment/缺 doc_id/None/空 dict/空串 doc_id/空串 fragment)全→inferred_unsaved 不入图;仅 saved 分支改 graph;verifier `set(graph)=={saved rel_ids}` 强制图恰等证据边集。
- **(b) 无证据推断标记不存**：无证据断言→status=inferred_unsaved/evidence=None/明确 note——既不存(不在图)也不静默丢(在 audit)。
- **(c) 有界**：RELATION_TYPES 真固定 8 谓词+允许对;任意谓词(frobnicate)/off-pair((paper)-implements->(policy))/未知 kind(tweet)全 refused 不入图。
- **(d) verifier 从 tool 现推**(R.build_graph(br.ASSERTIONS)),忽略 report JSON,防手改;负控制独立加合法词表但无证据边→不入图。
- **(e) fixture 诚实**:真 backfill 文号(苏政办函39/苏采7/鲁科字143/某试点)+现实片段引用;refused 案例合法测边界;NOT_DEPLOYED 零成本。

**加固（关闭 skeptic 指出的 latent 弱点）**：skeptic 指 `_has_evidence` strip fragment 但未 strip doc_id,理论上纯空白 doc_id 可过(fixture 无此例,不构成 hole)。已改 `_has_evidence` **doc_id 也 strip**,纯空白 doc_id 现→inferred_unsaved(实测确认)。证据规则密封。复跑 PASS(exit 0)。

实现者不自签 PASS —— 交独立复核。
