# PFI v0.2.5 原始输入包与恢复说明

本目录保存 v0.2.5 开发与验收所使用的两个原始输入文件，供迁移后的 agent 从 GitHub `main` 精确恢复，不再依赖本机 Downloads。

| 文件 | SHA-256 | 说明 |
|---|---|---|
| `PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md` | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` | 13 Stage / 156 Task 的原始 Roadmap |
| `PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip` | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` | 原始 46-entry ZIP；`unzip -t` 通过 |

## 产品与验收锚点

- Final delivery commit：`d488b1f47d5ef8dd5f95fc7d6f9a5382d1486a8a`。
- 已验收 PFI product tree：`a6aae2ae9e89f601b9a1833a45947ed625aa100c`。
- Product candidate A：`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`。
- Reviewed closure B：`559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`。
- Rereview evidence C：`123f5a6f7e7af22c283e49e55c2ba581310238d5`。
- Evidence index：`sha256:ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344`。
- Acceptance request time：`2026-07-15T21:45:47Z`。

本目录是不可变 source package，不是第二套可编辑产品事实源；当前产品事实仍以 `PFI/docs/governance/`、`PFI/VERSION`、`PFI/CHANGELOG.md` 与版本化 evidence 为准。

## 数据恢复边界

`$HOME/.pfi`、SQLite、上传文件、imports、日志、缓存、App 备份和任何真实财务值都不得写入公开 CodexProject。四个已验收 raw source blobs 已随仓库拆分迁移到 `LinzeColin/MetaDatabase@main`，验证锚点为 commit `8fad21d7e578c8ec56a1997d3a0e2f4a34a2fd6f`；其 blob OID、字节数与 SHA-256 均与 `PFI/config/sources/v025_immutable_real_source_lock.json` 一致。不得恢复已迁出的顶层 `MetaDatabase` 目录。

## CLI-only 恢复

```bash
git clone git@github.com:LinzeColin/CodexProject.git
cd CodexProject
git switch main
test "$(git rev-parse HEAD:PFI/docs/source_packages/pfi_v025)" != ""
shasum -a 256 \
  PFI/docs/source_packages/pfi_v025/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md \
  PFI/docs/source_packages/pfi_v025/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
unzip -t PFI/docs/source_packages/pfi_v025/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
```

如需真实 raw source，只从迁移后的 MetaDatabase 仓库按其自身权限与治理恢复；不要把 raw/private 数据复制回公开 PFI 产品树。全流程禁止 Finder、`open`、LaunchServices、AppleScript 与 GUI 文件操作。
