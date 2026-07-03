# WDA Stage 2 Sprint 2G Automated Acquisition Feasibility

Date: 2026-07-03

## Decision

Sprint 2G replaces the manual owner-prepared artifact route for WDA core
viability. WDA now requires an automated, owner-approved message-level
acquisition route that can produce a WDA Raw Import Pack.

Raw Gate remains `Conditional Investigation`. No `messages.jsonl` exists yet.
RAG, Web, and Matrix remain blocked.

## Scope

This sprint is a planning and feasibility package only.

- External hard drive required: no
- WeChat export tools executed: no
- Decryption or key extraction executed: no
- Protected stores opened: no
- Message content parsed: no
- RAG/Web/Matrix implemented: no

## Outputs

- `current_blocker_summary.md`
- `manual_artifact_route_deprecated.md`
- `automated_route_requirements.md`
- `candidate_tool_matrix.md`
- `candidate_tool_risk_matrix.md`
- `live_environment_requirement.md`
- `new_vs_old_computer_execution_plan.md`
- `controlled_trial_plan.md`
- `go_no_go_criteria.md`
- `recommended_next_sprint.md`
- `updated_handoff_note.md`

## Evidence Sources

Public documentation was used only for route feasibility. No tool was run.

- [r266-tech/wechat-local-mcp security notes](https://github.com/r266-tech/wechat-local-mcp/blob/main/SECURITY.md)
- [huohuoer/wechat-cli](https://github.com/huohuoer/wechat-cli)
- [wechat-export-macos](https://github.com/ydotdog/wechat-export-macos)
- [EchoTrace](https://github.com/ycccccccy/echotrace)
- [macos-wechat-cli](https://github.com/ginqi7/macos-wechat-cli)
- [PyWxDump PyPI](https://pypi.org/project/pywxdump/)
- [wechat-exporter / WeChatTweak route](https://github.com/JettChenT/wechat-exporter/blob/main/README.md)
- [HONOR WeChat backup note](https://www.honor.com/mea/support/content/en-us15833954/)
