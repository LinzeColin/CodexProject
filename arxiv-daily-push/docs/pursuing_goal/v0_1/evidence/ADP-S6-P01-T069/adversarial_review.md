# Adversarial review · ADP-S6-P01-T069｜预测目标 / Outcome Rule / 事件标签

独立对抗复核（general-purpose skeptic，两轮），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) settleability 门（模糊/主观/空字段/未知类型/非法 horizon/n 能否混入回测）；(b) official-only（媒体/A2/None/大小写/带空格是否误结算）；(c) 泄漏/observed_at 窗口（边界、跨月跨年闰年、malformed/None、未来文档是否泄漏为 1）；(d) label definiteness（是否恒 0/1/pending、count>=n、status_transition、topic 匹配）；(e) 非空跑（每条款判别控制、verifier 从工具现推、fixture 是否充分）；NOT_DEPLOYED（无网络/写/时钟/随机）。

## 第一轮：CONFIRMED_SOUND（hole=null, severity=none）
- **(a)**：拒空白字段/未知类型/负零 horizon/count n≤0-float-string/缺 settlement。**门真实**。
- **(b)**：仅精确 A0/A1 结算；media/A2/None/'a0'/'A0 '（带空格）**全不结算 1**（保守朝安全方向）。
- **(c)**：obs==origin→1、obs==end→1、end+1→0、origin 前→排除→pending、future-only 匹配→0（不泄漏为 1）、in-window 匹配但 obs 在 end 后→排除→0；`_add_days_bound` 用 `datetime.date` 故跨月/年/闰年**日历精确**；malformed/None/缺 observed_at→排除→pending。**未来文档只能 pending→0（as-of 时钟），永不→1**。
- **(d)**：count 用 `>=n`（media 不计入 count）；status_transition 精确 canonical_id+status。恒 0/1/pending。
- **(e)**：verifier 直接调 `admit_targets/settle/is_settleable`（**不读 report JSON**）；判别负控制（媒体不结算/未来不泄漏/模糊拒绝且 settle raise/genuine pending）；fixture 覆盖三种结算类型 + 官方/媒体/未来。
- **NOT_DEPLOYED**：仅 import datetime（传入日期算术）+ re；无 today()/now()/网络/写。
- **判定**：两验收条款（每目标可官方结算 / 模糊不入回测）**真成立、非空跑/作弊/错**。列 4 项**非致命防御性类型** latent。

## latent 的主动闭合（3 项防御性类型硬化 + 1 项披露）
1. **topics 为字符串会子串误配**（`s[topic] in (d.topics or [])` 对 string 做子串）→ 新增 `_topic_match` 要求 **topics 为 list 且精确成员**；`_match` 改用之。string 超集「数据共享政策」、tuple、空 list、缺键、None **全不匹配**（无 spurious 1）。
2. **bool horizon/n 通过 isinstance(_,int)**→ 新增 `_pos_int`（`isinstance(int) and not isinstance(bool) and >0`）用于 horizon_days 与 count n；bool/float/str/0/负 **全拒**。
3. **非-dict settlement 抛 AttributeError**→ `is_settleable` 加 `isinstance(s, dict)` 守卫，string/None/list/int/tuple/空 dict/bool **返回 False 不崩溃**，admit_targets 干净拒绝。
- **(#4 披露，未改)**：pending-vs-0「窗口已过」时钟用 max(observed_at) over 全部证据（含 media）——复核确认为 as-of 代理、**永不产生错误 1，仅 pending→0 时序**，defensible，known_gaps 已述精神。
- verifier 加 TYPE-SAFETY 控制（string-topics 不误配 / bool horizon-n 不 settleable / 非 dict settlement 拒不崩）。

## 第二轮（复核 DELTA）：CONFIRMED_SOUND（hole=null, severity=none）
复核者重跑 verifier（PASS，golden G1/G2/G3 值**逐一不变**），逐项攻击三部分 delta：`_topic_match` 保留全部先前结果（list present 单/多元=1、absent=0；string 超集/精确/tuple/空/缺键/None **全 0** 无子串泄漏；status_transition 路径未受影响）；`_pos_int` 接受 180/1/2 拒 0/负/True/False/180.0/'180'；非 dict 守卫对 string/None/list/int/tuple/空 dict/bool **全 False 无崩溃**。**纯加性硬化、零回归、无新空洞**。唯一有意收窄：tuple-topics 不再匹配，与声明的 list schema 一致。

## 结论
两轮复核均 **CONFIRMED_SOUND**；两验收条款有 load-bearing 判别负控制（媒体不结算/未来不泄漏/模糊 raise/边界精确）、非空跑，verifier 从工具现推。3 项防御性类型 latent 主动闭合（string-topics 精确成员/bool horizon-n 拒/非 dict settlement 拒不崩），复核证明零回归。确定性、零副作用、不读时钟；结算规则为确定性 Outcome Rule（非训练模型，MODEL_SPEC 未动）。实时无回归（live build_id b189d3cc0703 == T040）。**开启 Stage S6**。判定：**可交独立验证 / SHIP**。
