# OpenAIDatabase CLEAN Gate 独立验收

- Task：`TSK.OpenAIDatabase.CLEAN1.0010`
- Acceptance：`ACC.OpenAIDatabase.CLEAN1.0010`
- Execution base：`e1473638e75e1a6845a2956e390a066e4a67507a`
- 结论：`PASS_LOCAL_PROJECT_CLEAN_GATE`
- 边界：不新增产品功能、不执行 PAM1、不发布 business commit、不创建 PR/Issue/branch。

## Fresh-clone 方法

从 execution base 建立 `--depth 1 --no-tags --single-branch --no-local` clone；clone HEAD
精确等于 base，`is-shallow-repository=true`，无 object alternates，初始工作树 clean。
仅按既有 policy 定向 fetch 四个 baseline commit：

- directory lifecycle：`74dc2f7a52f1f1b7694c0433c5be87ce6da4cf73`
- generated retention：`0b66ae8192d2285f2972516e4fe080b9d2267bb7`
- raw material：`d05af208c0684a556831bfca04ec0c57b7747345`
- repository hygiene baseline tree owner：`57cb6bca623d2e01bde1a866140804c283340bd8`

未执行全历史 fetch。`git fsck --full --strict` exit `0`；上述定向 commit 在 shallow
clone 中显示为预期 dangling commit，不是对象损坏。

## 硬门禁结果

| Gate | 量化结果 |
|---|---|
| Directory / writer | `227/227` directories owned；unowned、duplicate owner/destination、dual-write、forbidden/missing writer=`0` |
| Scripts / CLI | 20 canonical capabilities；dead script、missing implementation、duplicate canonical owner、deleted active reference、implicit write mode=`0` |
| Generated / transient | 116 tracked targets；unclassified、multiply classified、no-consumer、missing binding、retained drift、tracked transient=`0` |
| Raw / security | 513 tracked public-raw files、`452,781,269 B`、1 destination；credential/private text、known credential context、instruction obedience、tracked private path、active bundle producer=`0` |
| Test ownership / CI | 52/52 test files 与 177/177 frontend validators 唯一 owned；duplicate/skip/flaky/live-unit/config/lock/workflow/action drift=`0` |
| Clean test repeat | 两轮各 `253/253 PASS`，总计 506 executions，runner elapsed `256.549s` |
| Data reproducibility | 两次 `SOURCE_DATE_EPOCH=1784155570` 构建均为 SHA-256 `4f71ebc731bbcbd7faaebade56a88e15854bdc17a8e1f81796ce0cc64e446e92` |
| Frontend reproducibility | fresh `npm ci` 154 packages；lint PASS；两次 Vite build tree SHA-256 均为 `863f33050aff1b8a8ea1e70a3b2f84c3ee42896ee9ad6018ec7f818057734985` |
| Governance | focused Lean `7/7 PASS`；human render drift/reference=`0/0`；OpenAIDatabase structural/semantic=`0/0`；ID references `11,825/11,825` |
| Repository hygiene | tracked runtime noise、forbidden backup producer、unregistered large object violation=`0`；policy PASS |
| Terminal invariant | execution start PR/Issue/non-main branch=`0/0/0`；business remote writes=`0` |

## Fresh CI 缺陷与最小修复

首次 clean clone 在 build 前运行 integration，`test_goal_completion_does_not_repeat_publish_release_in_preflight`
因 `apps/memory-atlas/dist` 尚不存在而失败。错误明确要求 build first；这证明旧 workflow
顺序无法通过全新 CI，而不是业务实现失败。

本 Task 只把 `Local integration tier` 移到 frontend build 后、aggregate audit 前，并把该顺序
写入 verification policy。`ci_step_order_drift_count=0`；build 后两轮 full tier 全过。

## Budgets 与解释边界

- Root `AGENTS.md`：`4,084 B <= 4 KiB`。
- Project `AGENTS.md`：`7,441 B → 5,852 B <= 6 KiB`；合并重复 raw/private/stable-layer 规则，
  credential、private archive、route、proposal-only 与 generated-candidate 边界均保留。
- Startup route：2 files、最多 `12,000 B <= 12 KiB`。
- Repo hygiene 保留规则解释 51 个 large objects；无未登记 large object。public raw 的任务专用
  上限为 40 MiB；`active_memory.jsonl` 的 GitHub-compatible sharding 明确属于
  `TSK.OpenAIDatabase.PAM1.0002`，本 CLEAN Gate 不越权提前实施。

## 非本 Gate 债务

- 全仓 semantic precheck 仍报告 62 条既有 KMFA machine-local / 旧 EEI/ADP manifest 问题；
  OpenAIDatabase 自身 structural/semantic 为 `0 errors / 0 warnings`，本 Task 不修改其他 project。
- `.0008` 的 GitHub internal `refs/pull` / cached-view purge 仍归 GitHub Support；owner-managed
  refs current target-path/credential-context residual=`0`，不宣称 full platform GC。
- Cloudflare live authorization 仍是 deployment 外部边界，不是 Project CLEAN Gate 失败。

## Integrity、交付与 rollback

最终 run manifest 以 candidate Git tree SHA-1 与 `git ls-tree -r` SHA-256 绑定本报告和全部
Task 文件；manifest 自身按 self-reference policy 排除。正常 build/test 后 tracked status 必须 clean。

Rollback：revert 本 Task 单一 local commit，恢复 CI step 顺序和原 project AGENTS；不改写历史、
不删除 data、不 push。若任何最终门禁或 `0/0/0` 失败，本报告结论必须撤销并继续阻断 PAM1。
