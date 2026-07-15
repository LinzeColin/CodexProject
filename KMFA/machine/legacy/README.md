<!-- 机器平面 · 遗留归档指针。此文件不是给 Owner 看的人类平面。 -->

# legacy —— v0.1.4 遗留记录指针（就地引用，未搬动）

交接契约 `交接给ClaudeCode.md` 阶段一第 2 步原定把下列大文件搬进本目录。
**本次未搬动。** 因为这三个文件被本仓库正在开发的 v015 治理套件硬引用
（166 个工具 + 13 个测试，含 `build_v015_s06_p2_golden_baseline_lock.py`
里的 `FEATURES_PATH = Path("KMFA/功能清单.md")`）。搬动会让 Codex 正在开发的
套件整体失败并造成在制数据错位。

因此以"就地引用"代替"物理搬动"，满足双平面对遗留归档位的要求，同时不干涉
Codex 正常开发。真正的封版/搬动是 Owner 的架构决定，须与 v015 引用改写协调，
不在阶段一骨架范围内。

## 被引用为 v0.1.4 遗留记录的文件（仍在 KMFA/ 根，原位只读）

| 文件 | 大小 | 性质 |
|---|---|---|
| `../../功能清单.md` | ~762KB | append-only 功能日志（人类平面退化样本） |
| `../../开发记录.md` | ~868KB | append-only 开发流水 |
| `../../模型参数文件.md` | ~895KB | 模型参数流水 |

> 契约只点名了前两个；第三个体量相当、性质相同，一并登记为遗留，供 Owner 决策。

## 版本号

契约阶段一第 1 步要求把根 `VERSION` 从 `0.1.4-one-time-github-main-upload`
改为 `0.1.4`。**本次未改。** 该字符串被 18 个文件引用（含
`docs/governance/VERSION_MATRIX.yaml`、`project.yaml`、
`tools/check_v014_one_time_github_main_upload.py`）。注意：`project.yaml` 里
`installed_version` 已是 `0.1.4`，即"干净版本号"其实已存在于机器平面。
根 `VERSION` 的清洗须与 v015 引用协调，属 Owner 决策。
