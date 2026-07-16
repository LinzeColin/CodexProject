# 独立对抗复核 · ADP-S8-P01-T085｜全链路迁移与数据一致性彩排

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **实现者不自签 PASS**：交独立 Agent（general-purpose skeptic，agent `ad5cdfe2b49d2b38c`）复核。
- **裁决**：**CONFIRMED_SOUND**（六向攻击全部证伪失败；复核者在 `/private/tmp` scratch dir 独立重算，绝不写仓库）。

## 复核者独立重算的六向

- **(a) 复现真实、非同义反复**：复核者**直接 import canonicalize + snapshot_writer**（绕过 harness），对已提交 `items_500`/`fs_500` 独立跑，得 canon summary `{items_in:500, canonical_documents:498, duplicate_items_collapsed:2}` 与 snapshot_id `sha256:61de7073ca96fd7d733bd5e46b425b7bfb501ce962df123e968f7d6be5ece644`——**与已提交锚点逐字节相同**，92 个分区 logical_hash 全等；`extract_factsheet(items_500)` 复现已提交 `fs_500`（sha16 相等）。是从 fixture 的真实再导出，非拿锚点自比。
- **(b) 负控制载重**：drop-last/drop-mid/mutate-title/mutate-date 各使 snapshot_id 离开 `61de7073`（非常量）；`assess_row_ledger` 拒绝 poisoned ledger（未解释 −100 + preserved 却掉行）。
- **(c) 不碰生产/证据不可变**：5 个锚点文件 + 3 个链工具彩排前后 shasum 逐字节相同；git status 计数不变(142)；`rehearse()` 只写 tmp work_dir；restore 用 `:memory:` SQLite；无 network/D1/R2。manifest/diff_report 是**新 untracked 交付物**非覆盖。（树里 worker_cloud.js/schema_cloud.sql 的改动**早于 T085**，是 pre-existing 分支状态，T085 证据已明确不认领；source_registry.json git-clean。）
- **(d) 诚实无过度声称**：stage 8 如实标 `decoupled=True`（读内嵌 G0/G1/G2，不消费快照）；500→498 是**真去重**（3 条相同 "Nominations Sent to the Senate"，同源 whitehouse-actions，`ttl:a008b842…` 合 1 doc，3 条全作 3 版本保留）；fixture 无 PII/密钥（SECRET/Authorization 命中是内容词 "SECRETARY"/"…Duty Free"，非 email/key/token）；"preserved" 成立（复核者自求和分区行=498 docs/500 versions==totals）。
- **(e) 完整性**：链真跨 registry(33 源/d63cf6bd)→factsheet(500)→render(500)→canonical(500→498)→version(500)→snapshot(61de7073/92 分区)→restore(counts_consistent/0 孤儿)→prediction(G1/G2)；无空阶段；ledger 覆盖每个 delta；restore out=329 是 3 月子集核验，正确地不计为丢失。
- **(f) NOT_DEPLOYED**：git 显示 T085 只新增 untracked `tools/full_chain_rehearsal.py` + `evidence/ADP-S8-P01-T085/**`，无 worker/schema/source_registry 改动；复核者自行只读 GET `https://adp.linzezhang.com/build.json` = `b189d3cc0703`/`cn_v0_3`，live 未变。

## 复核者提出的唯一次要 note（非载重，已如实披露）

> `assess_row_ledger` 只要求 reason 非空字符串——一条真丢失但配「垃圾理由」的条目会通过。

**评估与处置**：复核者明确「**不影响本任务**」——本任务 ledger 的每条 reason 都正确且**与独立复现的计数绑定**（items→docs −2、docs→versions +2、snapshot 行守恒，均由复核者独立重算证实）。ledger 的 reason-string 检查是**次级 sanity 层**；**主保护是逐阶段 `matches_committed`（从已提交输入真实再导出并比对锚点）**，这一层是载重且已被复核者独立复现。故**不改代码**（gold-plating reason 语义校验主观且无益），仅在 known_gaps 如实披露此边界。

## 结论

复核者对**彩排复现、数据一致性、无未解释丢失、不碰生产、NOT_DEPLOYED** 全部返回 **CONFIRMED_SOUND**。满足「实现者不自签 PASS」的独立复核门槛，可进入治理登记与合入。
