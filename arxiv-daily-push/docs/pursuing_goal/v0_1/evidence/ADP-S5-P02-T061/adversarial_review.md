# 对抗复核记录 · ADP-S5-P02-T061（全文/语义重排基准 + ADR）

用独立 skeptic 对基准+ADR 做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) AND 非 OR 真测**：decide_adopt `adopt=bool(improved and respects_filters)`;verifier 测全 4 象限:提升+守过滤→采用;不提升+守过滤→拒;守过滤但不提升→拒;**关键 improving-but-bypassing(m_syn 真提升+respects=False)→拒**(区分 AND/OR),承重。
- **(b) 提升真实可测**:FTS baseline recall@5=0.875<1.0(perfect 则 verifier FAIL);逐查询 低温雨雪=0.75/医疗=0.5/余 1.0→avg 0.875;FTS 真漏 doc-004「冰冻灾害恢复重建实施意见」(同义词,无与低温雨雪词法重叠);synonym rerank 找回→该查询 0.75→1.0,总 recall→0.9167。mrr/recall_at_k 数学正确。
- **(c) respects_filters 真计算非纯 flag**:good 候选经 respects_filters() 真子集检查得 True;skeptic 构造真 bypasser 忽略过滤集全局检索→返 False,证机制真检出越界。bypass 函数带 bypass=True flag 是 fixture 建模便利(与 identity 同码),不证伪 scoped claim(检测机制真+good True 真算+improver-bypass 拒隔离测)。
- **(d) verifier 从源现推**:import tool+generator 重建语料重算 metrics/决策,不读 report JSON,防手改;负控制(identity/bypass/improver-bypass/non-improver 拒)全真 fails.append 断言。
- **(e) fixture 诚实**:真形态中文政策标题;真同义词漏文档;严格 >min_improvement(0.0) 等值非「提升」;无 pass-while-false。NOT_DEPLOYED 0 生产请求。

本轮无需修复（CONFIRMED_SOUND）。实现者不自签 PASS —— 交独立复核。
