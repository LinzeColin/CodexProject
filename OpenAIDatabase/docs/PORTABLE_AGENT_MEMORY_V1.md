# Portable Agent Memory V1 发布与运行手册

版本：`1.0.0`
Task / Acceptance：`TSK.OpenAIDatabase.PAM1.0019` / `ACC.OpenAIDatabase.PAM1.0019`

## 发布边界

- 源码只通过一个 `automation-c/memory-*` 非 draft PR 进入 `LinzeColin/CodexProject/main`，由 trusted Settlement squash merge 并删除事务分支。
- 禁止 direct/force push、绕过 required check、history rewrite、archive branch 或 whole-repository bundle。
- memory-only ZIP 只发布到 GitHub API 显示为 `public` 且 `private=false` 的 `LinzeColin/AgentDatabase` Release。它不是 private-origin 原始归档：每条 record 必须同时满足 `public_repository_allowed=true`、`credential_present=false`、`handling=redacted_summary`，否则停止发布。
- 公开资产必须以 `--release-candidate` 导出，使 ZIP 的 canonical、generated、policy、runbook 和 recovery tool 全部直接读取 accepted commit；任何工作树 runtime member 都不能进入 Release。
- SHA-256 只证明完整性，不证明作者身份。源码 tag `portable-agent-memory-v1.0.0` 必须解析到 accepted `main` commit。

## 候选验收

在 `OpenAIDatabase/` 执行：

```bash
python3 -B scripts/evaluate_memory_production_acceptance.py \
  --phase candidate --artifact-ref CANDIDATE_TREE --write
python3 -B scripts/evaluate_memory_production_acceptance.py \
  --phase candidate --artifact-ref CANDIDATE_TREE --check
python3 -B scripts/run_verification.py --tier full
```

候选报告只表示 `CANDIDATE_READY_NOT_PUBLISHED`，不能代替生产验收。还必须通过 root governance、credential scan、candidate-tree hygiene、remote overlap 和 GitHub `0/0/0`。

## Public-safe Snapshot 发布

trusted Settlement 完成后，以 accepted `main` SHA 作为 `<accepted-sha>`：

```bash
git fetch https://github.com/LinzeColin/CodexProject.git main
test "$(git rev-parse FETCH_HEAD)" = "<accepted-sha>"
python3 -B OpenAIDatabase/scripts/memory_snapshot.py export \
  --database-dir OpenAIDatabase \
  --source-commit "<accepted-sha>" \
  --release-candidate \
  --output-dir "<outside-repository-output-dir>"
```

发布前用 GitHub API 重新确认 `LinzeColin/AgentDatabase.visibility == public` 且 `private == false`。导出结果必须同时报告 `release_candidate=true`、`all_members_from_source_commit=true` 和全部 canonical records public-safe。创建非 draft、非 prerelease 的 `portable-agent-memory-v1.0.0` Release，并上传唯一：

`portable-agent-memory-v1-<accepted-sha>.zip`

若上传或后验验证失败，删除未完成 Release/asset；不要修改 canonical memory、不要创建补偿分支、不要改写历史。

## 发布后独立验收

```bash
python3 -B OpenAIDatabase/scripts/evaluate_memory_production_acceptance.py \
  --database-dir OpenAIDatabase \
  --phase published \
  --artifact-ref "<accepted-sha>" \
  --report "<outside-repository-output-dir>/portable-agent-memory-v1-<accepted-sha>-acceptance.json" \
  --write
```

published 模式会 fresh-fetch accepted commit，重跑所有 hard gates，要求 repository hygiene 零违规，核验 `governance`、`openai-database-verify`、`memory-atlas-verify` 三个合同级 required check 的最新结果均为 success，检查源码 tag、public Release、asset size/SHA-256、snapshot commit/hash、commit-only member provenance 和 record public-safety，并要求最终 PR/Issue/non-main branch=`0/0/0`。只有报告为 `PRODUCTION_ACCEPTED` 才能关闭 Roadmap。

## 日常读取与恢复

- 默认入口：`data/memory/agent-memory.json`；只沿其 compact/shard 索引读取。
- 统一 CLI：`python3 scripts/memory.py --database-dir . validate|query|doctor`。
- 恢复：按 `docs/MEMORY_SNAPSHOT_RECOVERY.md` 在断网环境先 `validate`，再恢复到不存在的新目录；禁止覆盖现有目标。
- 写入：只走 mutation envelope、`automation-c/memory-*` 和 trusted Settlement；模型推断、raw evidence 或未授权来源不得直接持久化。
