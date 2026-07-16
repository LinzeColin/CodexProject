# 对抗复核记录 · ADP-S5-P01-T058（跨来源实体解析）

用独立 skeptic 对实体解析做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) 可撤销=精确**：merge 不改原对象(merged=deepcopy(a),在 shallow dict(entities) 上重赋键);audit.before 为 a/b 真 deepcopy(改快照不动 live)。split 经 deepcopy(snap) 还原,与 merge 前 ground-truth 快照 deep-equal(==),count 正确,返回对象独立。无路径丢失 split 不可恢复的信息。
- **(b) provenance**：每 alias 建时同建 provenance(make_entity 与 resolve else 分支逐 form append);set(provenance_of)==set(aliases),每源集非空,无 unsourced。
- **(c) 置信边界**：conf<0.80 返回同一 entities 对象/pending_review/len 不变(无 mutation);0.80/0.95 applied;0.7999 pends。两分支真门。
- **(d) 跨源/无过并**：纯精确 alias 成员聚类(无模糊/子串/token);独立 NBS(media-x)真并入国家统计局(stats-gov)带多源 provenance;仅共享子串「国家」的两机关保持独立(2 实体)。
- **(e) verifier 从 tool 现推**(ER.resolve(be.MENTIONS))断言,报告 JSON 仅打印不用于 pass/fail。

本轮无需修复（CONFIRMED_SOUND）。实现者不自签 PASS —— 交独立复核。
