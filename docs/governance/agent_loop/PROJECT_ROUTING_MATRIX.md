# Project Routing Matrix

Task Pack metadata 必须明确 `project`、`allowed_paths`、`forbidden_paths`、
`risk_tier`、`plan_required` 和 `validation_commands`。本矩阵给 ChatGPT 和
Owner 一个默认起点；最终以 Owner 批准的 Task Pack 为准。

## Machine-Readable Routing Matrix

`scripts/agent_loop/route_taskpack.py` 和
`scripts/agent_loop/autofill_taskpack_metadata.py` 只读取下面的 JSON block 作为
路由事实源。更新人工表格时必须同步更新这个 block。

<!-- AGENT_LOOP_ROUTING_MATRIX_JSON
{
  "version": "1.0",
  "routes": [
    {
      "project": "Alpha",
      "aliases": ["alpha"],
      "default_allowed_paths": ["Alpha/**"],
      "default_forbidden_paths": ["AGENTS.md", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "Alpha runnable checks must be chosen from the specific Alpha Task Pack and current runtime contract.",
      "t2_triggers": ["live/paper trading gates", "broker policy", "order/risk logic", "owner gate"],
      "split_when": ["Task also changes non-Alpha project code", "Task mixes trading/runtime work with governance automation"]
    },
    {
      "project": "EEI",
      "aliases": ["eei"],
      "default_allowed_paths": ["EEI/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "EEI validation depends on the active EEI Task Pack and release gate.",
      "t2_triggers": ["release gate", "A209 soak", "worker/runtime reliability", "schema/data contract"],
      "split_when": ["Task spans EEI and another business project", "Task mixes release evidence with generic governance automation"]
    },
    {
      "project": "FIFA",
      "aliases": ["fifa"],
      "default_allowed_paths": ["FIFA/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "No default FIFA command is known; Task Pack must define runnable checks.",
      "t2_triggers": ["model/formula/ranking logic", "release", "data schema"],
      "split_when": ["Task changes FIFA and another project"]
    },
    {
      "project": "KMFA",
      "aliases": ["kmfa"],
      "default_allowed_paths": ["KMFA/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "KMFA validation depends on the specific stage and Task Pack.",
      "t2_triggers": ["money/amount logic", "authority baseline", "schema mapping", "private data handling"],
      "split_when": ["Task changes KMFA and another business project"]
    },
    {
      "project": "MetaDatabase",
      "aliases": ["metadatabase", "meta database"],
      "default_allowed_paths": ["MetaDatabase/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "MetaDatabase checks must be declared by the Task Pack.",
      "t2_triggers": ["data trust", "schema", "ingestion", "privacy"],
      "split_when": ["Task changes MetaDatabase and another data system"]
    },
    {
      "project": "OpenAIDatabase",
      "aliases": ["openaidatabase", "openai database", "memory atlas"],
      "default_allowed_paths": ["OpenAIDatabase/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "OpenAIDatabase checks must match the active Memory Atlas Task Pack.",
      "t2_triggers": ["Codex data extraction", "privacy", "sync automation", "publication"],
      "split_when": ["Task changes OpenAIDatabase and another project"]
    },
    {
      "project": "OpMe_System",
      "aliases": ["opme_system", "opme system", "opme"],
      "default_allowed_paths": ["OpMe_System/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "OpMe_System validation must be task-specific because operational automation may touch runtime boundaries.",
      "t2_triggers": ["operational automation", "credentials boundary", "production"],
      "split_when": ["Task changes OpMe_System and another project"]
    },
    {
      "project": "PFI",
      "aliases": ["pfi"],
      "default_allowed_paths": ["PFI/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "PFI validation depends on the active stage and app/runtime contract.",
      "t2_triggers": ["financial data trust", "report formulas", "UI contract", "release gate"],
      "split_when": ["Task changes PFI and another project"]
    },
    {
      "project": "QBVS",
      "aliases": ["qbvs"],
      "default_allowed_paths": ["QBVS/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "QBVS checks must be declared by the Task Pack.",
      "t2_triggers": ["model/scoring/formula changes", "schema", "release"],
      "split_when": ["Task changes QBVS and another project"]
    },
    {
      "project": "Serenity-Alipay",
      "aliases": ["serenity-alipay", "serenity", "alipay"],
      "default_allowed_paths": ["Serenity-Alipay/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "Serenity validation depends on the active runtime, mail, and report contract.",
      "t2_triggers": ["mail/trading/runtime automation", "scheduler", "production continuity"],
      "split_when": ["Task changes Serenity-Alipay and another project"]
    },
    {
      "project": "arxiv-daily-push",
      "aliases": ["arxiv-daily-push", "adp", "arxiv daily push"],
      "default_allowed_paths": ["arxiv-daily-push/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "whkmSalary/**"],
      "validation_commands": [],
      "validation_na_reason": "arxiv-daily-push validation depends on the selected delivery/scheduler task.",
      "t2_triggers": ["source/board sync", "scheduler", "SMTP", "production delivery"],
      "split_when": ["Task changes arxiv-daily-push and another project"]
    },
    {
      "project": "whkmSalary",
      "aliases": ["whkmsalary", "whkm salary"],
      "default_allowed_paths": ["whkmSalary/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**"],
      "validation_commands": [],
      "validation_na_reason": "Salary validation must be task-specific because payroll and privacy rules are high impact.",
      "t2_triggers": ["payroll", "salary formulas", "privacy", "legal/tax"],
      "split_when": ["Task changes whkmSalary and another project"]
    },
    {
      "project": "governance",
      "aliases": ["governance", "governance docs"],
      "default_allowed_paths": ["docs/governance/**", "governance/**", "scripts/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": ["python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main"],
      "validation_na_reason": "",
      "t2_triggers": ["governance contract", "schema", "merge policy"],
      "split_when": ["Task changes governance and business project code in one Task Pack"]
    },
    {
      "project": "agent-loop",
      "aliases": ["agent-loop", "agent loop", "agent_loop"],
      "default_allowed_paths": [".github/workflows/agent-loop-*.yml", ".github/ISSUE_TEMPLATE/codex-task.yml", ".github/PULL_REQUEST_TEMPLATE/codex-task.md", ".github/codex/**", "docs/governance/agent_loop/**", "scripts/agent_loop/**"],
      "default_forbidden_paths": ["AGENTS.md", "Alpha/**", "EEI/**", "FIFA/**", "KMFA/**", "MetaDatabase/**", "OpenAIDatabase/**", "OpMe_System/**", "PFI/**", "QBVS/**", "Serenity-Alipay/**", "arxiv-daily-push/**", "whkmSalary/**"],
      "validation_commands": ["python3 -m py_compile scripts/agent_loop/*.py", "ruby -e 'require \"yaml\"; ARGV.each { |f| YAML.load_file(f); puts \"YAML_OK #{f}\" }' .github/workflows/agent-loop-run-approved-taskpack.yml .github/workflows/agent-loop-review-existing-pr.yml .github/workflows/agent-loop-retrospective.yml .github/ISSUE_TEMPLATE/codex-task.yml"],
      "validation_na_reason": "",
      "t2_triggers": ["workflow permissions", "auto-merge policy", "entrypoint routing"],
      "split_when": ["Task changes agent-loop and business project code"]
    }
  ]
}
END_AGENT_LOOP_ROUTING_MATRIX_JSON -->

默认禁止路径：

```json
[
  "AGENTS.md",
  "Alpha/**",
  "EEI/**",
  "FIFA/**",
  "KMFA/**",
  "MetaDatabase/**",
  "OpenAIDatabase/**",
  "OpMe_System/**",
  "PFI/**",
  "QBVS/**",
  "Serenity-Alipay/**",
  "arxiv-daily-push/**",
  "whkmSalary/**"
]
```

项目 Task Pack 应从默认禁止路径中移除自身项目路径，并只加入明确需要的
allowed path。

| Project value | Default allowed_paths | Default validation | Common T2 triggers |
|---|---|---|---|
| `Alpha` | `["Alpha/**"]` | Project-specific tests from `Alpha/` docs, plus changed-scope governance when available | live/paper trading gates, broker policy, order/risk logic, owner gate |
| `EEI` | `["EEI/**"]` | Project-specific EEI tests from Task Pack | release gate, A209 soak, worker/runtime reliability, schema/data contract |
| `FIFA` | `["FIFA/**"]` | N/A until Task Pack identifies runnable FIFA checks | model/formula/ranking logic, release, data schema |
| `KMFA` | `["KMFA/**"]` | Project-specific KMFA tests from Task Pack | money/amount logic, authority baseline, schema mapping, private data handling |
| `MetaDatabase` | `["MetaDatabase/**"]` | N/A until Task Pack identifies runnable MetaDatabase checks | data trust, schema, ingestion, privacy |
| `OpenAIDatabase` | `["OpenAIDatabase/**"]` | Project-specific Memory Atlas/OpenAIDatabase checks from Task Pack | Codex data extraction, privacy, sync automation, publication |
| `OpMe_System` | `["OpMe_System/**"]` | N/A until Task Pack identifies runnable OpMe checks | operational automation, credentials boundary, production |
| `PFI` | `["PFI/**"]` | Project-specific PFI tests from Task Pack | financial data trust, report formulas, UI contract, release gate |
| `QBVS` | `["QBVS/**"]` | N/A until Task Pack identifies runnable QBVS checks | model/scoring/formula changes, schema, release |
| `Serenity-Alipay` | `["Serenity-Alipay/**"]` | Project-specific Serenity tests from Task Pack | mail/trading/runtime automation, scheduler, production continuity |
| `arxiv-daily-push` | `["arxiv-daily-push/**"]` | Project-specific ADP checks from Task Pack | source/board sync, scheduler, SMTP, production delivery |
| `whkmSalary` | `["whkmSalary/**"]` | N/A until Task Pack identifies runnable salary checks | payroll, salary formulas, privacy, legal/tax |
| `governance` | `["docs/governance/**", "governance/**", "scripts/**"]` | `python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main` when environment supports it | governance contract, schema, merge policy |
| `agent-loop` | `[".github/workflows/agent-loop-*.yml", ".github/ISSUE_TEMPLATE/codex-task.yml", ".github/codex/**", "docs/governance/agent_loop/**", "scripts/agent_loop/**"]` | `python3 -m py_compile scripts/agent_loop/*.py` and workflow YAML parse | workflow permissions, auto-merge policy, entrypoint routing |
