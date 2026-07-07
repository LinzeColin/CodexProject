# KMFA Fund Weekly Analysis Skill Package

This folder packages a public-safe, deterministic skill for KMFA资金与税费管理：钉钉财务截图证据库、资金净流、余额连续性、税费融资风险、公司银行矩阵、管理层周报/月报Excel。

Canonical target path:

    KMFA/fund-weekly-analysis-skill/

Start with `SKILL.md`, then read `references/runbook.md`, `references/configuration.md`, `references/operating_contract.md`, `references/source_of_truth_contract.md`, and `references/validation_checks.md`.

This package intentionally excludes raw bank screenshots, raw bank exports, full account numbers, passwords, access tokens, employee/private plaintext, and non-redacted report bodies. Public GitHub should hold skill code, config schemas, redacted manifests, validators, and templates only. Raw private financial evidence stays local/private runtime unless the repo is explicitly made private and the user authorizes upload in the current run.
