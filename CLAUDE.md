@AGENTS.md
@OpenAIDatabase/data/derived/personalization/claude_personalization.md

# Claude Code adapter

- Imported personalization is derived and read-only; regenerate it, never hand edit it.
- OpenAIDatabase is the durable user-memory and routing control plane.
- Project status remains canonical in the selected project's governance files.
- For deeper context, run `python3 OpenAIDatabase/scripts/route_agent_resources.py --database-dir OpenAIDatabase --intent claude_personalization` and read only its returned `read_order`.
- During a business-project run, do not modify OpenAIDatabase; memory sync is a separate run.
- Never read raw/private paths or credentials without explicit Owner authorization.
