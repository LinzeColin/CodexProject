# PFI v0.2.2 来源资料 Manifest

生成时间：2026-06-28 Australia/Sydney

本 manifest 记录本轮 Stage 0 使用的 Downloads 来源资料。GitHub 中以后以本目录和合同测试作为可追溯入口；Downloads 原文件不作为长期产品根。

| 来源文件 | SHA-256 | 角色 | Stage 0 使用方式 |
| --- | --- | --- | --- |
| `PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md` | `94950e0cc4a46cfd19dfa2ed5ff2ebcab10909775e20d8bae1a4a2fe6f8b879c` | Stage -> Phase -> Task roadmap | 补做 Stage 0 的权威任务粒度，锁定 `S0-P1-T1..S0-P2-T2`。 |
| `PFI_v0.2.2_E2E_logic_optimization_package (1).zip` | `57143e8bf96fb148f72d4b8a086adbb75334de6a1d4389fb940038e5effff925` | 含 Stage -> Phase -> Task roadmap 的更新来源包 | 作为第二版来源包 hash 记录，不提交 binary zip 到 PFI。 |
| `PFI_v0.2.2_Roadmap_Acceptance_Stop_Validation_zh.md` | `6c3d54696095c28cfaeb134ba609d9ea240ee56732dab05621c61a3f36db4af7` | roadmap / acceptance / stop / validation | 作为第一版验收资料保留，最终执行粒度以 Stage -> Phase -> Task roadmap 为准。 |
| `PFI_v0.2.2_Codex_Task_Pack_zh.md` | `027ce56c62bdd66727d7457cec89f3883f3653ed99bc37a3421383624952c2de` | Codex Task Pack | 提取参数、Interconnection、标签、Runtime Diff、测试文件要求。 |
| `PFI_v0.2.2_Parameter_Draft_zh.md` | `861faa6c0ef458bd730a0e7da78d11b39e839177441689664922fdf36444cd93` | 中文参数草案 | 对照当前硬编码参数和后续 Stage 1 参数文件重构。 |
| `PFI_v0.2.2_6Agent_CrossReview_zh.md` | `7677a34add6b7a61b26f2a5d2262750cd232315f407e014a6a684e6d7a830ebd` | 交付前设计复审 | Stage 0 使用 Agent 1 / Agent 3 做 baseline 自检；完整触发型复核按 Stage 13 规则执行。 |
| `PFI_v0.2.2_UIUX_Logic_Review_Template.html` | `d8a19f901d2396582de5b2ab65f3ba945624b58e9a81636a0b5f9107404ab0f2` | 未来逻辑审查页参考 | 只作为理解数据逻辑与审查信息架构的参考；Stage 0 不修改前端显示。 |
| `PFI_v0.2.2_E2E_logic_optimization_package.zip` | `7ea03c89a7720dd8b5f498833c11a7d286e2e9d132fe48eb24eefef85ea78cfe` | 原始打包资料 | 作为来源包 hash 记录，不提交 binary zip 到 PFI。 |

## HTML 模板边界

用户已明确：`PFI_v0.2.2_UIUX_Logic_Review_Template.html` 只是帮助 Codex 理解，不代表本轮要修改 UIUX 前端显示。v0.2.2 Stage 0 到 Stage 6 的主线是数据库治理、参数治理、Interconnection、模型口径、标签持久化和 Runtime Diff。正式 UIUX 仍以 v0.2.1 为主。

## 第二版补做说明

`PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md` 明确指出该 roadmap 不是 milestone 列表，而是 Codex 可以逐项执行的 Stage -> Phase -> Task 路线。因此 Stage 0 补做后，以 `S0-P1-T1`、`S0-P1-T2`、`S0-P1-T3`、`S0-P2-T1`、`S0-P2-T2` 为本轮验收任务 ID；后续开发也按该 roadmap 的 Stage 1-13 顺序推进。
