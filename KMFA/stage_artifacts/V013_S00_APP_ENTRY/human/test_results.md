# KMFA v0.1.3 S00-P1 Test Results

生成时间: 2026-07-02T14:21:39+10:00

## RED Proof

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s00_app_entry.py`
  - 预期失败：`/Users/linzezhang/Downloads/KMFA.app`、`Info.plist`、launcher、icon、bindings 和 manifest 缺失。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s00_app_entry -q`
  - 预期失败：`ValidationError` 指向 app bundle 和 manifest 缺失。

## Implementation Notes

- Swift/AppKit 图标生成路径因本机 CommandLineTools SDK/toolchain mismatch 失败，未使用该路径。
- 改用 Codex bundled Python + Pillow 生成 1024px PNG，再用 `sips` 和 `iconutil` 生成 `.icns`。
- launcher 只打开 canonical KMFA public-safe 首页 HTML，不接外部系统，不写 raw/source 数据。

## GREEN Proof

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s00_app_entry.py`
  - PASS: app `/Users/linzezhang/Downloads/KMFA.app` installed，target HTML 为 canonical worktree 中 `kmfa_home_navigation.html`，icon sha `sha256:8e7d17d088e32ae59a1275d28ec573a9d3c8c6abed34a24ff43a77270d0df27c`。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s00_app_entry -q`
  - PASS: Ran 1 test OK。
- `plutil -lint /Users/linzezhang/Downloads/KMFA.app/Contents/Info.plist`
  - PASS: OK。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: Ran 279 tests OK。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0 / warnings 0。
- `changed-file raw/private/secret/parse scan`
  - PASS: changed_files=15，parse_checked=4，未发现 raw/private 路径、禁入扩展或 high-signal secret。
- `git diff --check -- KMFA scripts`
  - PASS: no whitespace errors。

## NO_GO Boundary

- `delivery_allowed=false`
- `formal_report_allowed=false`
- `official_report_release_allowed=false`
- `business_decision_basis_allowed=false`
- `business_execution_allowed=false`
- `github_upload_this_phase=false`
