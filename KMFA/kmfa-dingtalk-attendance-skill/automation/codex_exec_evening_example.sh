#!/usr/bin/env bash
set -euo pipefail
cd /Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa
export KMFA_RUN_SLOT=evening
codex exec --sandbox workspace-write --json \
  "$(cat KMFA/kmfa-dingtalk-attendance-skill/automation/evening_prompt.md)" \
  > KMFA/metadata/dingtalk_attendance/private_runtime/automation_runs/evening_$(date +%Y%m%dT%H%M%S).jsonl
