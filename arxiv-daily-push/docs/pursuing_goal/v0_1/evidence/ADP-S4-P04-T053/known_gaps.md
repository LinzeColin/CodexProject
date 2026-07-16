# Known gaps · ADP-S4-P04-T053（首批高价值 A2 pilot, SHADOW）

目标：先验证重要区/新区/自贸片区/高新区的**增量价值**（中央/省级之外的第一线本地行动信号）；无价值源不晋级。诚实边界：

1. **增量价值=本地行动信号超出 A0/A1 基线**：baseline={policy,regulation,statistics}（A0 中央 + A1 省级已覆盖）。A2 增量信号={项目立项/招投标采购/试点先行先试/产业落地签约/招商引资/规划公示}。入选须 incremental_signal_types 非空（≥1 本地行动信号不在 baseline）。**policy-repost-zone（仅转政策）0 增量 → 拒**；zone-media（资讯号）非官方 → 拒。10 入选全真高价值功能区（雄安/浦东/中关村/临港/苏州工业园区/横琴/天府/西安高新/两江/前海）。
2. **选择非抓取（同 T045/T051）**：交付 A2 pilot profiles + 2016 cursors + local action signals（选择/配置产物）。实际信号抓取是后续批次（需 headless fetcher）。
3. **3 区 server-reachable 有实证信号**：recon 实测雄安/苏州工业园区/横琴 200 + 本地行动信号词 9/17/6（confirmed_signals）；其余 7 区 TLS 挡（tls_blocked，fetch pending，诚实非冒充已抓）。
4. **增量价值当前是信号类型层面**：incremental_value=本地行动信号 TYPE 计数；单条信号的真实增量（相对具体 A0/A1 文档）随实际抓取 + T054 边际价值报告 + T055 生产门量化。本任务先验证 TYPE 级增量存在。
5. **SHADOW/未部署**：profiles+cursors+signals，未接 worker/生产。live build 仍 b189d3cc0703（==T040）。A2 registry 扩展是 T054，生产门是 T055。
