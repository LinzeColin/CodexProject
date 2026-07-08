# Taskpack: fund-weekly-analysis-skill

Deliverables:

1. Optimized Excel template: `templates/资金与税费管理母版_真实数据预览_v2.xlsx`
2. Skill instructions: `SKILL.md`
3. Automation prompt: `automation/daily_1130_sydney.prompt.md`
4. macOS launchd template: `automation/launchd/com.kmfa.fund-weekly-analysis.plist`
5. Deterministic runner, source readiness gate, source materializer, and validators under `tools/`
6. Governance references under `references/`
7. Owner review checklist: `references/excel_master_review_checklist.md`

Install:

```bash
export KMFA_REPO_ROOT=/path/to/CodexProject
bash tools/install_to_kmfa_main.sh
```

After install, replace `__REPO_ROOT__` in the launchd plist with the actual repo path, copy it to `~/Library/LaunchAgents/`, then run:

```bash
launchctl load ~/Library/LaunchAgents/com.kmfa.fund-weekly-analysis.plist
```

The installer does not commit raw financial evidence. It tracks only skill/governance/config files and a gitignored metadata private_runtime boundary.
