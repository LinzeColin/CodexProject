# KMFA S01-P1 Test Commands

更新时间: 2026-06-29

## 1. 本轮已运行

```bash
git status --short
git remote -v
git branch --show-current
git rev-parse --show-toplevel
```

结果摘要:

- 当前分支: `main`
- 当前仓库根: `/Users/linzezhang/Documents/KMFA v0.1`
- 未配置 remote
- 初始状态仅有 `.git`

```bash
shasum -a 256 \
  "/Users/linzezhang/Downloads/KMFA v0.1/01_KMFA_Codex_TaskPack_v1_1_完整防遗漏.md" \
  "/Users/linzezhang/Downloads/KMFA v0.1/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_1.md" \
  "/Users/linzezhang/Downloads/KMFA v0.1/KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_1_18Stages.zip"
```

结果摘要:

- TaskPack SHA256: `6446d5bcaab11be2b2e7cb4b1db673782d785062d8e9071152cabdb74b9dfcd5`
- Roadmap SHA256: `de08602f659b2618883e686f88d3427a76c5358ec4f1491062d0b5df8b304cc5`
- Delivery zip SHA256: `647adacf89f9dd0f15ac61ac703193e20c9d13c7762008487f5cd026fb4f9a69`

```bash
rm -rf /tmp/kmfa_s01p1_pack
mkdir -p /tmp/kmfa_s01p1_pack
unzip -q "/Users/linzezhang/Downloads/KMFA v0.1/KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_1_18Stages.zip" -d /tmp/kmfa_s01p1_pack
find /tmp/kmfa_s01p1_pack -maxdepth 3 -type f -print | sort
```

结果摘要:

- zip 可正常解包到 `/tmp/kmfa_s01p1_pack`
- 中文文件名解包后可读
- 共识别 23 个文件

```bash
python3 -m py_compile \
  /tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/tools/no_omission_check.py \
  /tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/tools/zero_delta_validator_reference.py
python3 /tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/tools/no_omission_check.py
python3 /tmp/kmfa_s01p1_pack/KMFA_ChatGPT_Stage3_Codex_Delivery_v1_1/tools/zero_delta_validator_reference.py
```

结果摘要:

```text
PASS: no omission check passed
PASS: zero delta reference checks passed
```

## 2. 本轮未运行的正式项目命令

以下命令来自 TaskPack，但正式 `KMFA/` 目录、工具脚本、fixtures 尚未创建，所以本轮不能声称通过:

```bash
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
python3 scripts/lean_governance.py validate --project KMFA
python3 KMFA/tools/no_omission_check.py
python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/metadata/fixtures/a0_project_cost_fixture.json
python3 KMFA/tools/check_no_float_money.py
python3 KMFA/tools/check_lineage_completeness.py
python3 KMFA/tools/check_report_grade_gate.py
```

处理方式:

- `lean_governance.py` 所属根治理工具需在正确 `CodexProject` checkout 中确认。
- `KMFA/tools/*` 属于 S01-P3 或后续 Stage，当前不存在属于预期状态。
- S01-P2 不应伪造这些命令通过；S01-P3 后再纳入正式验证。
