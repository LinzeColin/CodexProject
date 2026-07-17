---
name: hongquan-main-contract-dws
description: 从红圈 cloud.hecom.cn 导出、下载并归档主合同 DWS/Excel 原始数据。Use when the user asks for 红圈主合同DWS、红圈主合同导出、下载红圈主合同、更新红圈主合同原始数据，或需要把红圈主合同 Excel 按日期命名并移动到固定原始数据目录。
---

# 红圈主合同DWS

## Scope

Use Chrome with the user's existing 红圈 session. If UI control is needed, use Computer Use and target stable labels, buttons, and Finder paths rather than screen coordinates.

Do not store, reveal, or replay credentials. If 红圈 is not logged in, ask the user to complete login in Chrome, then continue after the main 红圈 page is visible.

## Batch Date Rule

Use the local date in `Australia/Sydney` unless the user specifies another date.

Treat each business week as Monday through Sunday. For any run date, compute the Saturday in that Monday-Sunday week and use that Saturday as the batch date folder name under OneDrive:

`/Users/linzezhang/Onedrive/WPS钉钉红圈原始数据/YYYY-MM-DD/`

Example: for the week starting Monday `2026-06-29` and ending Sunday `2026-07-05`, the batch date folder is `2026-07-04`.

## Workflow

1. Open Chrome and go to 红圈:
   - Prefer an existing authenticated tab, bookmark, or shortcut.
   - Fallback URL: `https://cloud.hecom.cn/login`.

2. If prompted, let the user log in. Continue only after the 红圈 workspace is visible.

3. Use the left black navigation area:
   - Click the page navigation icon/menu in the left black sidebar.
   - Select `标准工作台`.
   - Verify the upper page area shows the expected workspace state: top tabs include `项目经营分析`, `审批`, `招标信息`, `投标记录`, `主合同`, and the visible card/filter area includes `全部合同状态` and `全部主合同`.

4. If the expected workspace state is not visible, use the same left black page navigation to route manually:
   - `项目管理` -> `主合同` for the project-management main contract.
   - `投标管理` -> `招标信息`, `投标记录`, and `主合同` for the three tender-management exports.

5. Open the project-management `主合同` list and verify the table is for 主合同. Expected visible fields include `合同名称`, `合同编号`, `创建时间`, `施工状态`, and `甲方`.

6. Click `导出`.

7. In the export dialog, keep the default export fields, click `开始导出`, wait for export completion, and click `下载数据` exactly once. The downloaded file is usually named like `主合同_导出文件_<id>.xlsx`.

8. Return to 红圈 and open `投标管理` -> `招标信息`.

9. Click `导出`, keep the default export fields, click `开始导出`, wait for export completion, and click `下载数据` exactly once. The downloaded file is usually named like `招标信息_导出文件_<id>.xlsx`.

10. Open `投标管理` -> `投标记录`.

11. Click `导出`, keep the default export fields, click `开始导出`, wait for export completion, and click `下载数据` exactly once. The downloaded file is usually named like `投标记录_导出文件_<id>.xlsx`.

12. Open `投标管理` -> `主合同`.

13. Click `导出`, keep the default export fields, click `开始导出`, wait for export completion, and click `下载数据` exactly once. The downloaded file is usually named like `主合同_导出文件_<id>.xlsx`.

14. In Finder, go to `~/Downloads` and identify the four newly downloaded Excel files from this run:
    - project-management `主合同_导出文件_<id>.xlsx`
    - `招标信息_导出文件_<id>.xlsx`
    - `投标记录_导出文件_<id>.xlsx`
    - tender-management `主合同_导出文件_<id>.xlsx`

15. Rename the four Excel files using today's local date unless the user specifies another date:
    - project-management `主合同_导出文件_<id>.xlsx` -> `红圈主合同 YYYY-MM-DD.xlsx`
    - `招标信息_导出文件_<id>.xlsx` -> `红圈招标信息 YYYY-MM-DD.xlsx`
    - `投标记录_导出文件_<id>.xlsx` -> `红圈投标记录 YYYY-MM-DD.xlsx`
    - tender-management `主合同_导出文件_<id>.xlsx` -> `红圈投标主合同 YYYY-MM-DD.xlsx`

16. Move all four renamed Excel files to the batch folder:
    `/Users/linzezhang/Onedrive/WPS钉钉红圈原始数据/<batch-date>/`

17. Verify the batch folder contains:
    - `红圈主合同 YYYY-MM-DD.xlsx`
    - `红圈招标信息 YYYY-MM-DD.xlsx`
    - `红圈投标记录 YYYY-MM-DD.xlsx`
    - `红圈投标主合同 YYYY-MM-DD.xlsx`

## Verification

Before reporting completion:

- Confirm exactly one of each renamed file exists in `/Users/linzezhang/Onedrive/WPS钉钉红圈原始数据/<batch-date>/`:
  - `红圈主合同 YYYY-MM-DD.xlsx`
  - `红圈招标信息 YYYY-MM-DD.xlsx`
  - `红圈投标记录 YYYY-MM-DD.xlsx`
  - `红圈投标主合同 YYYY-MM-DD.xlsx`
- Confirm no `.crdownload` or incomplete download remains for the selected file.
- If duplicate raw downloads exist because `下载数据` was clicked more than once, preserve files and report the duplicate instead of deleting anything automatically.
- Report the final absolute paths for all batch files.

## Failure Handling

- If `下载数据` is not visible, wait briefly for export completion and re-check the export/download notification area.
- If the file already exists in the target folder, do not overwrite silently. Ask whether to replace, keep both, or stop.
- If the target batch folder does not exist, create `/Users/linzezhang/Onedrive/WPS钉钉红圈原始数据/<batch-date>/` before moving files.
- Do not use `DWS_Outputs.zip`; that previous zip-copy step is no longer part of this skill.
- If 红圈 changes labels or layout, rely on the verified table fields and export/download semantics, then document the observed label difference in the final response.
