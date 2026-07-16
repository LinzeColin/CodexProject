# 对抗复核记录 · ADP-S5-P01-T057（Canonical Event 聚合）

用独立 skeptic 对事件聚合做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) 真聚合非丢弃**：20 事件1 页共键 ("docnum","苏政办函〔2026〕39号")(原文以自身 doc_number join,19 成员以 references==该文号精确匹配);Σmember_counts(28)==pages_in(28),成员 page_id 并集==输入集(零丢零幻)。「1 提醒」来自聚类非删减。
- **(b) 全证据可展开**：expand(事件1)=20 member_links,page_id 唯一,与 20 源页精确一致,无丢无并。
- **(c) primary=官方原文**：primary=orig-jiangsu(A1,doc_number==键);originals 过滤要求 not references AND doc_number/canonical_id==键,故 A1 解读(doc_number null)不可选。**证 false-primary 路径**:移除原文→primary 落 A1 interp(doc_number None)→verifier 的 `prim.doc_number!=EVENT1` 会 FAIL——该检查真强制「primary 是原文」非仅「是 A1」。
- **(d) 无过并**：纯精确键聚类(无模糊标题并);事件2(鲁科字...,7 页)独立 event_id;solo 页自成 cid singleton;无跨事件页重叠,事件1 不吸事件2/solo。
- **(e) verifier 非空洞 + fixture 诚实对抗**：缺事件1 经 test1 FAIL 不能空过;输入乱序确定性(sha256 id + page_id tiebreaker);fixture=1 真文号原文+19 真引用成员(6 解读/8 转载/5 反应)+不同真文号无过并控制+无关 singleton,非凑;NOT_DEPLOYED 零生产副作用。

本轮无需修复（CONFIRMED_SOUND）。实现者不自签 PASS —— 交独立复核。
