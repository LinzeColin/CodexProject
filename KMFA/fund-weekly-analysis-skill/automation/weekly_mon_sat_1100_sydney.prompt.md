Use `$fund-weekly-analysis-skill`.

Run KMFA资金与税费管理周报自动化 every Monday and Saturday at local Sydney time 11:00.
Australia/Sydney local time is the scheduler source of truth. Do not use Beijing time as the scheduler timezone.

统一工作区规则：本 automation 只保留并只显示 KMFA/CodexProject 工作间：
- KMFA/CodexProject 工作间：`/Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject`
本 automation 的实际执行目录必须切到 `/Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject` 后再运行 KMFA git、skill、test 或脚本命令。
DWS 归档是独立上游 automation，不再作为本 KMFA automation 的 cwd/workspace；需要上游数据时只读取已生成的 OneDrive `DWS_Outputs.zip` 或 KMFA 私有输入副本，不得切入 DWS 归档工作间运行命令。
若发现本 KMFA automation 重新绑定了 DWS archive cwd/workspace，先修正 automation 配置并报告。

Upstream DWS source package priority:
1. `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`
2. `/Users/linzezhang/onedrive/DWS_Outputs.zip`
Legacy direct-folder source is compatibility fallback only and must not be assumed to exist:
`/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群`

Hard requirements:

1. Work on GitHub `main` only. No branch, no PR, no worktree.
2. Switch to `/Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject` or `/Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject` before repo commands, then read `KMFA/fund-weekly-analysis-skill/SKILL.md` and all referenced files before acting.
3. Run source readiness first:
   `python3 KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py --repo-root /Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject --timezone Australia/Sydney`
4. If readiness is `SOURCE_MISSING` only because the legacy direct folder is absent, inspect the readiness report source candidates. If a DWS_Outputs.zip candidate is `READY`, materialize the 付款请示群 source explicitly and then rerun readiness:
   `python3 KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py --source-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --zip-prefix 付款请示群 --target-dir /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群 --repo-root /Users/linzezhang/Documents/Codex/2026-07-05/1-airm2-2-codexproject-https-github/work/CodexProject --timezone Australia/Sydney --apply`
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
12. After the runner writes `screenshot_ocr_coverage.csv`, reuse any matching, non-empty private OCR sidecars already present in ignored private runtime; if coverage is still missing, generate private local Vision OCR sidecars with `tools/generate_screenshot_ocr_sidecars.py --engine vision --apply`. Existing successful generation-plan rows must be preserved, new rows append with the next generation id, empty OCR output must not be written, OCR text remains private runtime only, and generated OCR text must not be promoted into financial facts without review. If new private sidecars are generated, rerun `tools/run_fund_weekly_analysis.py` once with the same `run_id` so the workbook package includes pending-review OCR text/value/financial-fact candidates plus OCR fact cross-review summary, no-write OCR fact ledger staging preview, and validation-only OCR fact review gate/template/preview outputs.
13. Mirror any prompt/skill/template/governance changes under `KMFA/fund-weekly-analysis-skill/automation/` or relevant tracked folders, validate, commit and push to GitHub main if and only if validation passes.
14. If a value cannot be confidently extracted from real evidence, leave it blank or mark `待识别/待复核` and create an exception task. Do not guess.
15. Do not modify upstream DWS archive outputs; materialization is a downstream private compatibility copy from the current DWS zip into the configured KMFA input folder.
Final response must be Chinese and include source readiness, selected DWS input path, whether materialization was performed, workbook path if generated, validation status, blockers, and next action.
