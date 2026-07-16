# Known gaps · ADP-S5-P01-T057（Canonical Event 聚合）

目标：把同一政策/研究/事件的原文/解读/转载/反应聚成一个事件。20 同事件页只产生 1 提醒；所有证据仍可展开。诚实边界：

1. **事件身份=共享事件键（文号）**：原文以自身文号为键;解读/转载/反应以其**引用的文号**join。**无模糊纯标题合并**（防误并）。fixture 用真实文号 苏政办函〔2026〕39号(事件1原文,T050江苏回填)+19 引用它的成员=20 页;事件2 用不同真实文号 鲁科字〔2023〕143号(保持独立)。
2. **primary=最权威原文**：cluster 内 authority 最高且自身 id==事件键的成员(A0>A1>A2>media);事件1 primary=A1 江苏原文非 media 转载。member_links 保留每成员 role(original/interpretation/repost/reaction)可单独取。
3. **20→1 提醒 + 可展开**：28 页→3 事件(3 提醒);事件1 的 20 页→1 事件1 提醒;expand(事件1)=全 20 成员逐一可取(page_id 唯一,与源 20 页精确一致)。**负控制:事件2(不同文号)保持独立,事件1 不吸事件2 页(无过并)**;无关新闻 singleton 自成事件。
4. **成员 join 靠显式 references（文号引用）**：当前用 references 字段模拟转载/解读引用原文文号。真实抓取中,转载页确含原文文号/标题引用→抽取 references 填此字段(承 T038 媒体→官方 resolver)。无 references 且无匹配文号的页=singleton 事件(诚实,不强并)。
5. **NOT_DEPLOYED**：event identity+primary+member links 库,未接 worker/生产。live build 仍 b189d3cc0703(==T040)。跨来源实体解析是 T058,跨板块 Evidence Relation 是 T059。
