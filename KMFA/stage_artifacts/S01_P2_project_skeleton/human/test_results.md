# KMFA S01-P2 Test Results

更新时间: 2026-06-29

```text
PASS_REQUIRED_FILES
PASS: git diff --check -- README.md governance/projects.yaml KMFA
PASS: python3 scripts/lean_governance.py validate --project KMFA
  root: checked
  projects checked: KMFA
  errors: 0
  warnings: 0
PASS: python3 scripts/validate_project_governance.py --project KMFA
  root: checked
  projects checked: KMFA
  errors: 0
  warnings: 0
PASS: rg -n "质量门禁|中间 Phase 不上传|Stage 完成复审" KMFA
```

Note: ad-hoc standalone YAML parsing was not used as acceptance evidence because the current `python3` environment lacks the third-party `yaml` module. The repository governance validators parsed the YAML successfully and are the authoritative checks for this project.
