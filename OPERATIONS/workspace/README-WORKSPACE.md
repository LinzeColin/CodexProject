# workspace/ —— 本机工作间的契约与工具

## 为什么在这里

`~/Documents/Codex/GithubProject/` 是本机所有 agent 的唯一工作间,里面并排放着 8 个仓。
但工作间**自己**的三样东西,到 2026-08-11 为止**只存在于那一台 Mac 上**:

| 文件 | 是什么 | 风险 |
|---|---|---|
| `README.md` | 七条铁律。全局 `CLAUDE.md` 明写「该 README 是唯一真源」 | 机器一坏,所有 agent 的行为契约就没了 |
| `tools/workspace-doctor.sh` | 铁律 2/3 的体检脚本 | 同上 |
| `tools/install-guards.sh` | 装 pre-commit / pre-push 守卫 | 同上 |

**守着铁律的工具,自己没有版本控制。** 现在收进来。

## 同步方向:仓是源,本机是部署副本

改动先改仓、再同步到本机:

```bash
R=~/Documents/Codex/GithubProject
cp $R/CodexProject/OPERATIONS/workspace/README.md            $R/README.md
cp $R/CodexProject/OPERATIONS/workspace/tools/*.sh           $R/tools/
```

**是否已分叉**由 `workspace-doctor.sh` 自己检查(【工作间契约】那一节,按 sha256 比)。
它只报不改 —— 方向猜错就会把本机的紧急修改覆盖掉。

## 为什么放 CodexProject

这三样东西横跨 8 个仓,不属于任何单个项目;铁律 4 是「不跨仓」,而 CodexProject
已经是运维/治理的落点(`OPERATIONS/schedule_registry.yaml`、`OPERATIONS/host-bin/`)。
放这里是延续既有归属,不是新开一处。
