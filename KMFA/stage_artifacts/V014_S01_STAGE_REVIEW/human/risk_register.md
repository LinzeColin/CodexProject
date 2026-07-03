# KMFA v0.1.4 Stage 1 Review 风险登记

| 风险 | 当前状态 | 控制 |
|---|---|---|
| 将 Stage 1 review 误解释为 GitHub upload gate | open_controlled | manifest 和治理记录明确 `github_upload_performed=false`，upload 延期到 v1.4 Stage 1-18 complete overall review |
| 在非 raw phase 读取或列出 raw inbox | closed_by_scope | 本 review 不需要 raw evidence，未访问 `/Users/linzezhang/Downloads/KMFA_MetaData` |
| public repo 泄露敏感材料 | closed_by_scan | changed/untracked path scan、secret scan、diff check 纳入验收 |
| 跳过 S02-P1 进入后续业务实现 | open_controlled | next phase 只标记为 `S02-P1`，且必须另起 run work |
| 把 D/NO_GO 状态误报为 delivery ready | open_controlled | release_state 保持 `delivery_allowed=false`、`current_go_no_go=NO_GO`、`current_report_grade=D` |
