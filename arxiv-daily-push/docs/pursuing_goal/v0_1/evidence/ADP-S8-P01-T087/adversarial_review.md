# 独立对抗复核 · ADP-S8-P01-T087｜最终 Value-Cost Gate

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **实现者不自签 PASS，也不自签 Owner gate**：交独立 Agent 复核（两轮）。
- **裁决**：初版 **HOLE_FOUND**（R2 部署状态失实），修复后**待聚焦复核 CONFIRMED_SOUND**。

## 第一轮复核（独立 skeptic，五向）
- **机器规则载重**：PASS——独立 flip:空 value_metric→rule(1) False;deployed 无证据→rule(2) False;off 标 keep/scale→rule(2) False;+$25 付费行→within_budget False。非空跑。
- **$0 免费档依据**：PASS——DIR-007 封顶免费档、FACT-013 VERIFIED(Owner 于 S0 Exit 确认 Free)。
- **parity 92/131**：PASS——独立从 committed parity_registry_131 重数(delivered 92)。
- **release_mode 分布 73+3+12+2=90**：PASS。
- **Owner gate 不自签**：PASS——owner_signoff.status=PENDING(工具+committed json+验证器断言);框定为「机器规则过、Owner 签署待」,未称门关。
- **★HOLE_FOUND（诚实/2b）★**：R2 行标 `deployed=false / RAW_DUALWRITE=false (off) / off by default`,但 committed `worker_cloud.js:28` 是 `const RAW_DUALWRITE=true`(T023 SHADOW 开启后从未回退)、`wrangler_cloud.jsonc` 绑 R2 `adp-raw-artifacts`、双写路径 `if(RAW_DUALWRITE&&env.RAW&&sourceId)` 在 live `b189d3cc0703` **活跃写入**;T023 cost_value 记 SHADOW 部署(build 9cd3d8a2fe68,~90 Class A/mo)、T086 DR 列 R2 为活跃 PERMANENT 库、T040 只改 A0 flag 未动 RAW_DUALWRITE。**这是给 Owner 签署文件里的部署状态失实**——正是诚实检查要抓的。

## 修复（诚实，根治）
- **R2 行的 `deployed` 现从 worker 实际 flag 派生**:新增 `raw_dualwrite_live()` 解析 `const RAW_DUALWRITE`(+R2 绑定),if active → R2 行 deployed=True/keep,如实标 **SHADOW-active(RAW_DUALWRITE=true, per-run cap 3)**,写永久 R2 桶(live b189,免费档内 ~90 Class A/mo·~4.7MB/mo),需 DIR-007 监控;else off/hold。手断的"关"状态不再可能——从生产实际派生。
- **验证器加诚实不变式**:`row.deployed == raw_dualwrite_live()['active']`——scorecard 的 R2 部署断言与 worker 实际不符即 FAIL,防再漂移。
- **核实其余行诚实**:S5/S6 深度层在 live worker **grep 0 出现**、A1/A2 子国家源不在 live worker→hold 属实;worker/d1/cron/domains/boards/six-theme 确为 live。
- 结果:**7 keep / 3 hold**,$0/mo(免费档),92/131 delivered,机器规则 PASS,Owner 签署 PENDING。

## 第二轮：聚焦复核（fixed 代码）——**CONFIRMED_SOUND**
独立 skeptic 四点全 PASS:①R2 行 deployed 从 `raw_dualwrite_live()` 派生,独立解析 worker `const RAW_DUALWRITE=true`+R2 绑定→row deployed=True/keep/"SHADOW-active"/"actively captured",原 hole 关闭;②诚实不变式载重——scratch 探测:强制 row deployed=False(worker=true)→CAUGHT、模拟 worker=false 而 row=True→CAUGHT、monkeypatch flag→false 则 row 翻 deployed=False/hold(**追随 flag,非手断**);③其余行诚实:S5/S6 grep worker=**0**、A1/A2 子国家=**0**、deployed=True 行确 live;④验证器 exit 0、7 keep/3 hold、$0/mo、92/131、owner PENDING、live GET=b189d3cc0703、T087 只增 tool+evidence。
- **复核者两个透明 caveat（不重开 hole）**:①三个 build_id(HEAD/working-tree/live)——工具读 working-tree worker,但 `RAW_DUALWRITE=true` 自 T023 起在 HEAD/工作树/全历史**不变**,故 live b189 必然 R2 active,build.json 证实 live=b189d3cc0703;②main worktree 的 `worker_cloud.js` 有未提交 UI 编辑(T079-T084,与 T087 无关)——**本任务治理用 fullwt(reset 到 origin/main 干净),只 copy T087 的 tool+evidence,不 `git add` main worktree 的 worker M,故此 caveat 不适用**;fullwt 的 worker 是 origin/main(RAW_DUALWRITE=true committed since T023),工具从 committed 状态跑仍 R2 active,一致。

## 结论
初版 R2 部署失实(HOLE_FOUND)已根治为从 worker flag 派生 + 诚实不变式,第二轮 **CONFIRMED_SOUND**。机器规则 PASS,**Owner 签署 PENDING——门未关,呈交 Owner**。满足「实现者不自签 PASS/不自签 Owner gate」门槛。

**★教训:给 Owner 签署的 value-cost/部署状态断言必须从生产实际(worker flag / registry / live build)派生,不能凭记忆手断——"开/关"这类状态手断极易失实,且会误导 Owner 决策。透视多样/独立复核对"给人签的文件"尤其关键。★**
