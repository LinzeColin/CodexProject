# archive —— R0-6 冻结登记（只读，不删除）

冻结日期：2026-07-14 · 依据：docs/v03/03_执行计划/ROADMAP.md R0-6 + docs/v03/DECISIONS.md E 节

## 冻结方式

仓库级治理校验器（`scripts/validate_project_governance.py`、`scripts/lean_governance.py` 的 HUMAN_ENTRY_FILES 契约）把下列文件的路径与 V7 锁引用钉死为全仓 CI 必需项，物理移动会破坏 13 个项目共用的治理门。因此冻结**在原地执行**：文件不移动、不删除、不再追加；三大人读入口顶部已加冻结横幅。本目录是冻结事实的唯一登记处。

## 冻结清单（此后任何任务不得以它们为阅读输入或追加目标）

| 文件 | 体积 | 角色（历史） |
|---|---|---|
| ../功能清单.md | ≈364 KB | 旧人读功能账（由 docs/v03 取代） |
| ../开发记录.md | ≈428 KB | 旧开发总账（由 docs/v03/04_开发记录/CHANGELOG.md 一行制取代） |
| ../模型参数文件.md | ≈528 KB | 旧参数人读文件（由 config/thresholds_v0_3.yaml 取代） |
| ../docs/governance/formula_registry.yaml | ≈524 KB | 旧公式登记（machine 锁保留，不再扩展） |
| ../docs/governance/model_registry.yaml | ≈252 KB | 旧模型登记（同上） |
| ../docs/governance/parameter_registry.csv | ≈1.1 MB | 旧参数登记（同上） |
| ../docs/governance/DEVELOPMENT_LEDGER.md | ≈960 KB | 旧开发台账（同上） |
| ../docs/governance/development_events.jsonl | ≈2.0 MB | 旧事件流（同上） |
| ../docs/governance/delivery_tasks.yaml | ≈1.1 MB | 旧任务登记（同上） |
| ../用户中心/ | ≈864 KB | 旧证据页集（由 run manifest 自动生成的用户中心取代，R1 起） |

## 会话成本对照（R0-6 验收）

- 旧阅读契约面（上表合计）：≈8.1 MB
- 新阅读契约面（docs/v03 + config/thresholds_v0_3.yaml + CONTRACT/DECISIONS/STATUS）：≈115 KB
- 压缩比：≈70:1，满足「治理上下文 ≤100 KB」量级目标（任务包本体 <110 KB）。

## 例外

docs/governance 下的小型状态文件（STATUS.md、OWNER_STATUS.md、ASSURANCE_STATUS.yaml、VERSION_MATRIX.yaml、TRACEABILITY_MATRIX.csv、MODEL_SPEC.md）仍由治理 dashboard 生成器维护，属机器平面，不在冻结清单内。
