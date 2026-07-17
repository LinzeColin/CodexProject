# KMFA v1.5 S01 受控过渡修订回滚

只允许反向提交本 bridge Run 的 transition artifacts、validator/tests 与治理同步。回滚后下一入口恢复为 `S01_CONTROLLED_TRANSITION_AMENDMENT`，`S02-P1` planning edge 关闭。

禁止修改或删除 S01 P1/P2/P3、Stage review 历史证据；禁止 `reset --hard`、`checkout --`、`clean -fd`、force push、raw 复制/备份/修改或 App 替换。

回滚前后都必须保留 S01 `BLOCKED / NOT_PASSED / NO_GO`、IB-001 至 IB-004 `CARRIED_OPEN`，并复跑 Stage review strict validator。
