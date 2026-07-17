# KMFA v1.5 Stage 01 review 回滚方案

## 可回滚范围

- `V015_S01_STAGE_REVIEW` public-safe evidence。
- Stage review validator 与 focused tests。
- review 发现后对 P1/P2/P3 validators/tests 的 fail-closed 加固。
- `KMFA/AGENTS.md` 与当前治理状态同步。

## 不可触碰范围

- `/Users/linzezhang/Downloads/KMFA_MetaData`。
- `/Users/linzezhang/Downloads/KMFA.app`。
- P1/P2/P3 历史 manifest 的负面/正面结论。
- 远端 main、GitHub push、App reinstall。

## 回滚方法

只允许对本 review commit 做非破坏性反向提交，或在独立临时 worktree 中检出 review base `5aba436c3e7f1a98bb1a3ad88735b8ad2b279d46` 做只读比较。禁止 `reset --hard`、`checkout --`、`clean -fd`、force push 或改写历史。

回滚后必须复跑 P1/P2/P3 frozen validators，并确认 Stage 01 仍为 `BLOCKED / NOT_PASSED / NO_GO`；回滚不得被解释为 S02 entry。
