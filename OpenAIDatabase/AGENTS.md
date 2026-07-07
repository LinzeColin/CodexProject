# OpenAIDatabase Agent Rules

Default user-facing language: Chinese. Keep code identifiers, API names, model
names, errors, and source titles in English when that is clearer.

## Startup

1. Read this `AGENTS.md`.
2. Route the task with `scripts/route_agent_resources.py --intent <intent>`.
3. For default startup, read only the route's required `read_order`.
4. Load `data/derived/profile/CORE_PROFILE.md`, full agent context packs, or
   architecture docs only when the route lists them as conditional resources
   and the current task gives a concrete reason.
5. For ChatGPT/Project personalization tasks, read
   `data/derived/personalization/chatgpt_personalization.md`.

Use route-specific files before broad repository search.

## Canonical Contracts

- Three-layer context source: `config/context_sources/three_layer_context.json`
- Resource routing: `config/context_sources/resource_routes.json`
- Codex runtime config: `.codex/config.toml`
- Personalization manifests, not runtime config:
  `config/codex/config.template.toml` and `config/codex/project.config.toml`
- Evaluation harness: `config/evaluation/personalization_harness.json`
- Task-run evidence schema: `config/evaluation/task_run.schema.json`
- Detailed user requirements: `docs/USER_REQUIREMENTS.md`
- Model and parameter documentation: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Delivery record: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`

## Sync Requirement

Any future agent that updates or syncs profile, preference, taste, history, or
pattern information must:

1. Update the mapped source files in the three-layer context.
2. Regenerate `data/derived/agent_context/*`.
3. Regenerate `data/derived/personalization/*`.
4. Run `scripts/evaluate_personalization_context.py`.
5. Append a redacted task-run evidence row under one of:
   - `data/run_logs/sync_runs/`
   - `data/run_logs/export_runs/`
   - `data/run_logs/evaluation_runs/`
   - `data/run_logs/agent_runs/`
   Each row must include `context_used`, `tools_used`, `tests_run`, and
   `failure_recovery`.
6. Commit and push the redacted derived updates to GitHub.

If the update target is unclear, log it as `UNKNOWN` with a follow-up task.
Do not silently drop memory-affecting changes.

## v1.2 S01 P3 Bridge

不要把 taskpack 大段写入 AGENTS.md；这里只保留可执行边界。用户授权后 raw/transcript 可公开进入 GitHub，但必须走 public raw、append-only、manifest/hash gate。

raw 只读、只追加、不覆盖、不增删改。cookies、session tokens、passwords、API keys、private keys、OAuth tokens 和浏览器凭证库不是 transcript，永远不能提交。

每次 run 最多只完成一个 phase。S01 P3 完成后下一步是 S01 复审，不自动进入 S02，不上传 GitHub main，不重装 app 入口。

## Hard Boundaries

- Do not commit cookies, browser state, `.local_keys/`, `.env`, plaintext
  secrets, private keys, or local absolute paths. User-authorized raw data /
  transcript may enter GitHub only through the v1.2 public raw, append-only,
  manifest/hash gate.
- Do not automate ChatGPT login, UI scraping, export download, or saved-memory
  writes.
- Generated memory candidates remain pending until reviewed.
- Memory Atlas may consume only redacted derived visualization data from
  `data/derived/visualization/memory_atlas.json`.
- Frontend writeback must remain proposal-only; do not directly mutate
  `data/memory/active/active_memory.jsonl` from the UI.
- Local `node_modules`, `dist`, app bundles, temporary work, and caches are not
  delivery artifacts and must not be committed.

## S5PBT02 Structure Boundary

- `apps/memory-atlas/` is the app layer. It reads redacted derived snapshots
  and must not read raw OpenAI exports, private imports, or plaintext secrets.
- `skills/openai-memory-analysis/` is the reusable skill/tooling layer.
- `context/` and `config/context_sources/` hold routing and source-context
  contracts; default startup must use route-specific reads instead of broad
  data scans.
- Raw and private exports are external-first until v1.2 public raw gates are
  implemented. User-authorized raw data / transcript may be committed only as
  append-only public raw with manifest/hash. Credentials, cookies, browser
  state and plaintext secrets stay outside git, encrypted, or under ignored
  local paths such as `data/raw_encrypted/`, `data/private_imports/`,
  `private_exports/`, `exports/private/`, and `data/private/`.
- Default entries must be repository-relative (`AGENTS.md`, route scripts, and
  redacted derived context packs). Local absolute paths are examples only and
  are never default entry points.

## Minimum Validation

Run the narrowest useful checks for the change. For personalization/context
changes, use:

```bash
python3 scripts/build_personalization_exports.py --database-dir .
python3 scripts/route_agent_resources.py --database-dir . --intent startup
python3 scripts/evaluate_personalization_context.py --database-dir .
python3 -m unittest tests.test_personalization_architecture -q
```

For broader OpenAIDatabase changes, add:

```bash
python3 -m py_compile scripts/build_agent_context_pack.py scripts/sync_codex_memory_data.py
python3 -m unittest discover -s tests -p "test_*.py" -q
```

## S4 精简执行胶囊

- 普通 T0/T1 任务先读本文件，并使用 `scripts/route_agent_resources.py` 返回的读取路线；
  避免大范围数据扫描。
- 不得读取完整 `模型参数文件.md`，除非变更涉及 profile scoring、路由、个性化规则、
  评估指标、memory sync、隐私门禁或派生上下文生成。
- 治理验证：`python -B scripts/lean_governance.py validate --project OpenAIDatabase --semantic`。
- owner 预览：`python -B scripts/lean_governance.py check-render --project OpenAIDatabase`。
