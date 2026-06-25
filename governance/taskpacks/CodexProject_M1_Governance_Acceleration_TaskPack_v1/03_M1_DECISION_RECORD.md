# M1-S 决策记录：最小改动，不改总体架构

## 采用

- 现有双平面保持不动。
- 现有 `scripts/lean_governance.py` 保持唯一外部治理入口。
- T0-T3 保持不动。
- legacy changed-scope 在影子等价性完成前保持唯一权威结果。
- 优化对象仅限：重复调用、误触发、过长 stdout、错误零写入判定和不可测性能。
- 先 shadow，再 parity，再有限激活。

## 不采用

- 不新增 `CURRENT.md` 或 `SHIP.md`。
- 不新增 `projectctl.py` 或另一套 CLI。
- 不把项目 Roadmap 换成交付卡。
- 不删除三个中文人类文件。
- 不删除 Acceptance/Evidence/Stop Gate。
- 不在普通任务中全仓物理改写。
- 不把 Task Pack 变成仓库长期事实源。

## 从《优化治理V0.1》吸收的原则

吸收：

- Build / Review / Release / Governance 的职责分离；
- 一次一个用户结果和一个可验收目标；
- 单一验证入口；
- 实际 diff、测试、运行证据和明确 SHIP/FIX-ONE/STOP；
- 独立审查者不能由实现者自证。

不直接复制：

- `CURRENT.md`、`SHIP.md`、`CLAUDE.md` 等新增平行入口；
- 用短交付卡取代既有 Roadmap；
- 在尚未证明等价时删减完整治理门禁。

原因：当前仓库已经有完整 Roadmap、双平面与单一 `lean_governance.py` 入口。继续增加文件会重新制造“多个当前真相”。

## 激活策略

```text
legacy-authoritative
    + candidate-shadow
    -> fixture parity
    -> fault injection
    -> real change shadow
    -> owner gate
    -> limited activation
    -> two-run monitor
```

任何阶段出现 false negative、tracked 写入、范围越界或 Required Check 身份变化，立即回滚 legacy-authoritative。
