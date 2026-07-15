<!-- 机器平面根说明。英文随意，Owner 不看这里。 -->

# machine/ —— 机器平面（事实源）

v1.5 双平面架构的机器平面。人类平面 `../文档/` 的每个字段都必须能在这里找到出处。

## 目录

| 目录 | 装什么 | 现状 |
|---|---|---|
| `facts/` | 事实源 JSON（status/features/flows/plan/acceptance/ops/blockers/changelog...） | **空**（阶段二只读扫描真实数据后落盘） |
| `runs/` | 每次运行的清单：读了什么、产出了什么、对哪个阻塞做了什么动作 | **空** |
| `tools/` | 三道门 + 渲染器 | 已装 |
| `legacy/` | v0.1.4 遗留记录指针（就地引用，未搬动，见其 README） | 指针 |

## 三道门（`tools/`）

```bash
cd KMFA
python3 machine/tools/render_human.py        # 血缘前置门（先跑）：facts 空 -> 当前红
python3 machine/tools/check_doc_budget.py    # 体积门 + 中文门 + 纯净门
python3 machine/tools/check_blocker_stop.py  # 阻塞重审门
```

`render_human.py` 现在必然 FAIL —— 这是**故意的**。`facts/` 为空，源优先级链第 1 环
未接通，人类平面还没有被真实事实渲染。绿的门是假门。只有阶段二接通真实数据、
且渲染逻辑落地后，本门才允许变绿。

## 阶段边界（本次只做骨架）

本次仅安装双平面骨架，**未做**契约阶段一的两个破坏性步骤（改根 `VERSION`、
搬动遗留大文件），因为它们会破坏 Codex 正在开发的 v015 套件。见 `legacy/README.md`。
阶段二（只读扫描 `KMFA_MetaData`、抽取 8 份 PDF、生成 A0 候选）是业务开发，不在本次范围。
