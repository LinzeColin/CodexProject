# KMFA v1.5 S02-P1 需求合并与范围锁回滚计划

## 回滚范围

只允许通过新的反向提交撤回本 Run 新增的 S02-P1 requirements ledger、business-line matrix、scope-lock、manifest、validator/tests 与同步治理记录。禁止改写或删除 source package、S01 P1/P2/P3、S01 Stage review、受控过渡修订及其历史证据。

## 回滚后的门禁

- 当前入口恢复为 `S02-P1`；`S02-P2` entry 必须关闭。
- `S01` 仍为 `BLOCKED / NOT_PASSED / NO_GO`。
- 受控过渡修订仍为 `PASSED / GO_TO_S02_P1_ONLY`，但不得解释为 Stage PASS 或产品实现授权。
- 24 Stage / 72 Phase / 216 Task 数量不得改变。

## 禁止动作

禁止 `git reset --hard`、`git checkout --`、`git clean -fd`、force push；禁止 raw 复制、移动、删除、改写或 App 替换；禁止用旧静态 IA、launcher 或 DOM 点击证据恢复 v1.5 产品验收。

## 回滚后验证

回滚提交后必须复跑受控过渡修订 strict validator、S01-P2 dependency validator、Roadmap 24/72/216 sync、governance、no-float、no-omission 与 structured public-safe checks；任一失败都必须 fail closed。
