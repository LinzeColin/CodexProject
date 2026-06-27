# PFI v0.2.2 来源资料 Manifest

生成时间：2026-06-28 Australia/Sydney

本 manifest 记录本轮 Stage 0 使用的 Downloads 来源资料。GitHub 中以后以本目录和合同测试作为可追溯入口；Downloads 原文件不作为长期产品根。

| 来源文件 | SHA-256 | 角色 | Stage 0 使用方式 |
| --- | --- | --- | --- |
| `PFI_v0.2.2_Roadmap_Acceptance_Stop_Validation_zh.md` | `6c3d54696095c28cfaeb134ba609d9ea240ee56732dab05621c61a3f36db4af7` | roadmap / acceptance / stop / validation | 提取 Milestone 0-8 和 Stage 0 验收标准。 |
| `PFI_v0.2.2_Codex_Task_Pack_zh.md` | `027ce56c62bdd66727d7457cec89f3883f3653ed99bc37a3421383624952c2de` | Codex Task Pack | 提取参数、Interconnection、标签、Runtime Diff、测试文件要求。 |
| `PFI_v0.2.2_Parameter_Draft_zh.md` | `861faa6c0ef458bd730a0e7da78d11b39e839177441689664922fdf36444cd93` | 中文参数草案 | 对照当前硬编码参数和后续 Stage 1 参数文件重构。 |
| `PFI_v0.2.2_6Agent_CrossReview_zh.md` | `7677a34add6b7a61b26f2a5d2262750cd232315f407e014a6a684e6d7a830ebd` | 交付前设计复审 | Stage 0 使用 Agent 1 / Agent 3 做 baseline 自检；完整 2 轮 x 6 Agent 留到 Milestone 8。 |
| `PFI_v0.2.2_UIUX_Logic_Review_Template.html` | `d8a19f901d2396582de5b2ab65f3ba945624b58e9a81636a0b5f9107404ab0f2` | 未来逻辑审查页参考 | 只作为理解数据逻辑与审查信息架构的参考；Stage 0 不修改前端显示。 |
| `PFI_v0.2.2_E2E_logic_optimization_package.zip` | `7ea03c89a7720dd8b5f498833c11a7d286e2e9d132fe48eb24eefef85ea78cfe` | 原始打包资料 | 作为来源包 hash 记录，不提交 binary zip 到 PFI。 |

## HTML 模板边界

用户已明确：`PFI_v0.2.2_UIUX_Logic_Review_Template.html` 只是帮助 Codex 理解，不代表本轮要修改 UIUX 前端显示。v0.2.2 Stage 0 到 Stage 6 的主线是数据库治理、参数治理、Interconnection、模型口径、标签持久化和 Runtime Diff。正式 UIUX 仍以 v0.2.1 为主。

