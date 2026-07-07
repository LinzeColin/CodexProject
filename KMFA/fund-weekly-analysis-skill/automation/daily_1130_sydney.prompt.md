Use `$fund-weekly-analysis-skill`.

Run KMFA资金与税费管理日报/周报自动化 at local Sydney time 11:30.
Reference only: 11:30 Australia/Sydney equals 09:30 Asia/Shanghai during the current UTC+10 offset.

Read the latest files under:

/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群

Hard requirements:

1. Work on GitHub `main` only. No branch, no PR, no worktree.
2. Read `KMFA/fund-weekly-analysis-skill/SKILL.md` and all referenced files before acting.
3. Do not use simulated/test/fake/estimated financial data.
4. Build evidence index first, then fund ledger, then internal transfer netting, then balance continuity, then tax/loan risk, then company-bank matrix, then Excel.
5. Generate the Excel workbook with exact sheet order:
   - 01_首页总览
   - 02_资金趋势预测
   - 03_三层净流余额
   - 04_税费融资风险
   - 05_公司银行矩阵
   - 06_CodexSkill流程
   - hidden H01-H06 audit/review/config sheets
6. 首页 and trend charts must be native line charts and each chart must be <= 1728x864 px.
7. Perform cross-review checks: formula errors, hidden sheets, no simulation data, internal transfer netting, balance continuity tolerance 0.01, sensitive fields not visible, tax version conflict detection, company-bank mapping coverage.
8. Write all outputs to the private runtime run directory.
9. Mirror any prompt/skill/template/governance changes under `KMFA/fund-weekly-analysis-skill/automation/` or relevant tracked folders, validate, commit and push to GitHub main if and only if validation passes.
10. If a value cannot be confidently extracted from real evidence, leave it blank or mark `待识别/待复核` and create an exception task. Do not guess.
