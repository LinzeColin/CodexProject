# AGENTS.md

Default language: Chinese for user-facing replies.

## Memory Vault Rules

- Default to Chinese for user-facing output. Keep professional terms, APIs, model names, code identifiers, and source titles in English when needed for precision.
- Treat this repo as a local-first, review-gated memory database.
- Treat this repo as the durable memory source for future AI agents. A new agent should be able to continue the user's work from this database without relying only on chat history.
- Start from `docs/PERSONAL_CONTEXT_ARCHITECTURE.md`, `config/context_sources/three_layer_context.json`, and `config/context_sources/resource_routes.json` before broad search.
- Use `scripts/route_agent_resources.py --intent <intent>` to select the smallest sufficient context route.
- The three required context layers are L1 core profile, L2 project/decision memory, and L3 behavior history/patterns.
- Future agents that update or sync profile, preference, taste, history, or pattern information must update the mapped source files, regenerate `data/derived/agent_context/*` and `data/derived/personalization/*`, run the evaluation harness, and append a redacted run log.
- For fast personalization, read `data/derived/profile/CORE_PROFILE.md` before broad search. It reflects manually reviewed core profile overrides from `data/memory/curation/core_profile_review.json`.
- Never commit raw unencrypted OpenAI export ZIPs or unredacted full messages.
- Never commit `.local_keys/`, cookies, sessions, browser profiles, tokens, passwords, private keys, or `.env`.
- Never upload plaintext high-risk secrets to GitHub. For finance/trading agents, store only `secret_ref` metadata, purpose, approval boundary, and local resolver hints.
- Default user-facing delivery is chat output plus GitHub-backed repository updates. Do not create local delivery ZIPs, copied report packages, or extra local deliverables unless the user explicitly asks.
- After every processing run, paste the analysis report, weekly review, and monthly review into the chat. Repository files are backup/audit/RAG surfaces, not a substitute for the chat answer.
- Also write the same chat-facing report to `data/derived/chat_reports/*.chat_report.md` for GitHub backup.
- Generated ChatGPT/Codex personalization exports live in `data/derived/personalization/` and are rebuilt with `scripts/build_personalization_exports.py`.
- Run logs use four GitHub-backed categories: `data/run_logs/sync_runs`, `data/run_logs/export_runs`, `data/run_logs/evaluation_runs`, and `data/run_logs/agent_runs`.
- Keep the local machine lean: clean transient delivery packages, copied report folders, `.DS_Store`, and Python cache after use. Do not delete source exports or encrypted raw archives without explicit authorization.
- Do not automate ChatGPT login, UI scraping, export download, or saved-memory writes.
- Keep generated memory candidates `review_status = pending` until the user accepts or edits them.
- Prefer deterministic local scripts over ad hoc model summarization for raw export ingest.
- For user-facing replies, translate memory records into human-useful topics, decisions, actions, risks, opportunities, ROI recommendations, and capability-growth advice.
- Do not present only record IDs, hashes, schemas, or agent-internal fields unless the user asks for audit detail.
- In every memory processing output, lead with conclusions from the memory content itself: topics, what to do, what to remember, recommendations, opportunities, ROI implications, and personal-growth signals. Put processing status and database mechanics after that.
- Immediately after the content conclusions, compare with the previous processed snapshot: new themes, stronger/weaker themes, changed decisions, new/changed rules, obsolete conclusions, risks, opportunities, and implications for next actions and personalization.
- After each processing run, output a chat-ready review covering: topics, what changed, what to do, what to remember, three-tier memory classification, old memory updates, new decisions, general short-term backup, memory updates for Codex/ChatGPT, future answer rules, ROI recommendations, personal growth recommendations, and potential development/investment opportunities.
- After each processing run, run at least two independent review passes: one strategic/opportunity/ROI reviewer and one execution/quality/omission reviewer. If real subagents are unavailable, the script must still generate two separate reviewer sections.
- Do not delete, discard, or fail to back up historical memory. Classify every item as `核心画像`, `一般`, or `临时`.
- Full-flow memory processing must maintain `active_memory`, Project Index, Decision Log, Timeline, chat report backups, weekly/monthly reports, candidates, secret refs, and the SQLite search/fetch index.
- Core profile curation must separate high-weight durable personalization from project-specific workflows. Do not promote learning dashboards, Nitrosend project details, code snippets, logs, or one-off instructions into `核心画像` unless a review override explicitly says so.
- If a week/month boundary is reached, produce the weekly/monthly review formats defined in `skills/openai-memory-analysis/references/human-review.md`. These reviews must be for the user: self-improvement, ROI, decisions, project progress, capability growth, opportunity discovery, and next actions; not only agent maintenance.
- Before changing schema, read `skills/openai-memory-analysis/references/schema.md`.
- Before changing security behavior, read `skills/openai-memory-analysis/references/security-policy.md`.
- Before changing search/fetch behavior, read `skills/openai-memory-analysis/references/retrieval.md`.
- Before writing chat-facing memory reviews, read `skills/openai-memory-analysis/references/human-review.md`.
- Memory Atlas is an independent local-first visualization app, not a third-party plugin. Keep it under `apps/memory-atlas`.
- Memory Atlas is one merged platform with selectable source slices, not separate apps. The homepage selector must show exactly `总数据源`, `ChatGPT`, and `Codex`, backed internally by `all`, `memory_atlas`, and `codex`, while sharing Galaxy, Notion Map, ROI, Obsidian Graph, Timeline, Contribution Grid, Search, and recommendation views.
- Future data sources such as `wechat`, `xiaohongshu`, and `douyin` must be registered in `config/data_sources/source_registry.json` before implementation. Add ingestors that emit canonical redacted derived events; do not hardcode new sources only in the UI and do not create fake nodes/activity for planned sources.
- Memory Atlas may consume only redacted derived visualization data from `data/derived/visualization/memory_atlas.json`. It must not read raw exports, `.local_keys`, raw encrypted archives, cookies, sessions, or plaintext secrets.
- Real Codex local data sync is allowed only through `scripts/sync_codex_memory_data.py` redacted summaries. Do not commit raw Codex transcripts, session files, local absolute paths, cookies, browser profiles, plaintext secrets, broker credentials, or `.env` values.
- Memory Atlas serves `memory_atlas.json` through runtime fetch (`/memory_atlas.json`) using the Vite public dir mapped to `data/derived/visualization`; do not reintroduce build-time JSON imports into the main JS bundle.
- The Memory Atlas Search/Review view must keep the two recommendation buckets: `Memory（给 ChatGPT / Codex Personalization）` and `Meta Data（给 ChatGPT / Codex Agents.md）`, with added/modified/deleted-or-demoted/current sections.
- The committed visualization snapshot must stay `public_redacted_read_only_visualization`: no private raw statements, source refs, record hashes, record indexes, local absolute paths, conversation refs, or client-side writeback conflict tokens.
- Memory Atlas frontend can request memory writeback in future, but it must create versioned change proposals first. It must not directly mutate `data/memory/active/active_memory.jsonl`.
- Writeback conflict detection belongs in a controlled backend/CLI layer that reloads current memory state and creates git/history rollback state before applying changes. Do not trust client-supplied source pointers or conflict tokens.
- Galaxy mode uses Three.js as the primary visual layer. Do not overlay visible HTML star dots during normal WebGL rendering; keep the clickable star overlay only for WebGL fallback.
- After local Vite + React + Three.js stabilizes, next deployment target is Cloudflare Pages + Access. Revisit Tauri only after data contracts, writeback proposals, and performance are stable.
- Memory Atlas production builds should not enable sourcemaps by default. Local `node_modules`, `dist`, and `*.tsbuildinfo` are transient generated files and must not be committed.
- Local macOS launchers are generated by `scripts/install_memory_atlas_app.py` into `~/Downloads/Memory Atlas.app` and `/Applications/Memory Atlas.app`. They are thin launchers with a generated `.icns` icon and a prebuilt static runtime under `~/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime`, not committed app bundles, not Tauri, and not a bypass around the redacted data contract.

## Validation

```bash
python3 -m py_compile skills/openai-memory-analysis/scripts/openai_memory_analysis.py
python3 -m py_compile scripts/build_memory_atlas_data.py
python3 -m py_compile scripts/sync_codex_memory_data.py
python3 -m py_compile scripts/install_codex_weekly_sync.py
python3 skills/openai-memory-analysis/scripts/openai_memory_analysis.py self-test --out-dir /tmp/openai-memory-analysis-self-test
python3 skills/openai-memory-analysis/scripts/openai_memory_analysis.py search --database-dir . --query Codex --limit 5
python3 scripts/build_memory_atlas_data.py --database-dir . --output data/derived/visualization/memory_atlas.json
python3 scripts/sync_codex_memory_data.py --database-dir . --build-atlas
python3 scripts/build_personalization_exports.py --database-dir .
python3 scripts/route_agent_resources.py --database-dir . --intent startup
python3 scripts/evaluate_personalization_context.py --database-dir .
python3 -m unittest discover -s tests -p "test_*.py"
npm ci --prefix apps/memory-atlas
npm run build --prefix apps/memory-atlas
python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_visual_acceptance.py
python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_goal_completion.py --publish-dir apps/memory-atlas/dist
python3 scripts/preflight_cloudflare_pages_access.py --publish-dir apps/memory-atlas/dist
python3 scripts/deploy_memory_atlas_cloudflare.py
python3 scripts/install_memory_atlas_app.py
python3 scripts/audit_memory_atlas_acceptance.py --require-local-apps
python3 scripts/audit_memory_atlas_goal_completion.py --require-local-apps
```
