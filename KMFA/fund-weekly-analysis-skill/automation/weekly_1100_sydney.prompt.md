Use `$fund-weekly-analysis-skill`.

Run KMFA资金与税费管理周报自动化 at local Sydney time 11:00 every Monday and Saturday.
Reference only: 11:00 Australia/Sydney equals 09:00 Asia/Shanghai during the current UTC+10 offset.

统一工作区规则：本 automation 与上游每日钉钉DWS归档、考勤检查、钉钉工作检查使用同一组 Codex cwds（干净显示入口）：
- DWS 归档 alias：`/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/dws-archive` -> 真实目录 `/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p`
- KMFA/CodexProject alias：`/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/kmfa-codexproject` -> 真实目录 `/Users/linzezhang/CodexProject`
本 automation 的实际执行目录必须切到 KMFA alias 或 `/Users/linzezhang/CodexProject` 后再运行 KMFA git、skill、test 或脚本命令；DWS 归档 alias 只作为上游输出和诊断可见工作区。若发现这些上游/下游 automation 的 cwds 不一致，先修正 automation 配置并报告。

Upstream DWS source package priority:
1. `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`
2. `/Users/linzezhang/onedrive/DWS_Outputs.zip`
Legacy direct-folder source is compatibility fallback only and must not be assumed to exist:
`/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群`

Hard requirements:

1. Work on GitHub `main` only. No branch, no PR, no worktree.
2. Switch to `/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/kmfa-codexproject` or `/Users/linzezhang/CodexProject` before repo commands, then read `KMFA/fund-weekly-analysis-skill/SKILL.md` and all referenced files before acting.
3. Run source readiness first:
   `python3 KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py --repo-root /Users/linzezhang/CodexProject --timezone Australia/Sydney`
4. If readiness is `SOURCE_MISSING` only because the legacy direct folder is absent, inspect the readiness report source candidates. If a DWS_Outputs.zip candidate is `READY`, materialize the 付款请示群 source explicitly and then rerun readiness:
   `python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py --source-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --zip-prefix 付款请示群 --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群 --repo-root /Users/linzezhang/CodexProject --timezone Australia/Sydney --apply`
   If the CloudStorage zip is unavailable but `/Users/linzezhang/onedrive/DWS_Outputs.zip` is readable, use that path with the same `--zip-prefix` and `--target-dir`. Do not materialize from stale, unreadable, or non-DWS zip sources.
5. Continue to extraction only if readiness is `READY` after the initial check or after explicit materialization; otherwise fail closed with the readiness report and include which upstream DWS zip/fallback path was checked.
6. Do not use simulated/test/fake/estimated financial data.
7. Build evidence index first, then fund ledger, then internal transfer netting, then balance continuity, then tax/loan risk, then company-bank matrix, then Excel.
8. Generate the Excel workbook with exact sheet order:
   - 01_首页总览
   - 02_资金趋势预测
   - 03_三层净流余额
   - 04_税费融资风险
   - 05_公司银行矩阵
   - 06_CodexSkill流程
   - hidden H01-H06 audit/review/config sheets
9. 首页 and trend charts must be native line charts and each chart must be <= 1728x864 px.
10. Perform cross-review checks: formula errors, hidden sheets, no simulation data, internal transfer netting, balance continuity tolerance 0.01, sensitive fields not visible, tax version conflict detection, company-bank mapping coverage.
11. Write all outputs to the private runtime run directory.
12. After the runner writes `screenshot_ocr_coverage.csv`, generate the private OCR sidecar plan with `tools/generate_screenshot_ocr_sidecars.py`; dry-run is default, empty OCR output must not be written, and OCR text remains private runtime only.
13. Mirror any prompt/skill/template/governance changes under `KMFA/fund-weekly-analysis-skill/automation/` or relevant tracked folders, validate, commit and push to GitHub main if and only if validation passes.
14. If a value cannot be confidently extracted from real evidence, leave it blank or mark `待识别/待复核` and create an exception task. Do not guess.
15. Do not modify upstream DWS archive outputs; materialization is a downstream private compatibility copy from the current DWS zip into the configured KMFA input folder.
16. Sidebar 收尾：最终报告准备好后，作为最后一个 tool action，使用 Codex app 的 `set_thread_archived`（如需先用 `tool_search` 发现该工具）将当前 automation-run 线程归档；调用时不要传 `threadId`，只归档当前运行线程，避免它重复显示在 sidebar chat。不要归档普通用户交接线程。

Final response must be Chinese and include source readiness, selected DWS input path, whether materialization was performed, workbook path if generated, validation status, blockers, and next action.
