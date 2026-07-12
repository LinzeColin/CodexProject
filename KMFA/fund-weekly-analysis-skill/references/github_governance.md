# GitHub Governance

Target GitHub directory:

```text
KMFA/fund-weekly-analysis-skill/
```

Keep the package structure aligned with `kmfa-dingtalk-attendance-skill`: root README, root SKILL, references, templates, tools, automation, tests.

Rules:

* Use `main` only.
* Do not open PRs or branches.
* Pull with fast-forward only before changes.
* Validate before commit.
* Commit skill/automation/template changes and push to `origin main` in the same run.
* Mirror local automation prompts under `automation/` before updating local scheduler.
* Do not commit private runtime raw data.
