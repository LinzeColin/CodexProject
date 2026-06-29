# S03-P1 文件型导入完成记录

更新时间: 2026-06-29

## 范围

- Stage: `S03｜原始文件导入与数据源检查矩阵`
- Phase: `S03-P1｜文件型导入`
- 任务:
  - `S3PAT01`: 支持 `zip/xlsx/xls/csv/pdf` 登记和安全解包。
  - `S3PAT02`: 为每个文件生成 hash、大小、上传批次、来源包记录。
  - `S3PAT03`: 识别 WPS/OLE 特殊格式并给出可操作提示。

## 已完成

- 新增 `KMFA/tools/file_import_register.py`，提供文件登记、格式识别、hash 计算、私有 storage ref 生成和 zip 安全解包。
- 新增 `KMFA/tests/test_file_import_register.py`，覆盖登记结果、隐私边界、OLE/WPS 提示和 zip traversal 防护。
- 扩展 `KMFA/metadata/imports/raw_manifest_schema.json` 与 `raw_manifest_policy.yaml`，把 S03-P1 文件格式、容器类型和来源包登记字段纳入 raw manifest 协议。
- 新增 `KMFA/metadata/imports/file_import_policy.yaml`，固化 S03-P1 支持格式、zip 安全规则、WPS/OLE 操作提示和公开仓库禁止项。
- 更新 `KMFA/metadata/imports/import_runs.jsonl`、`raw_file_manifest.jsonl`、`KMFA/metadata/sources/source_registry.yaml` 与 `KMFA/metadata/protocol/directory_manifest.json`，登记 S03-P1 能力头记录和机器可读入口。

## 非范围

- 不导入真实私有源文件。
- 不提交 `.zip/.xlsx/.xls/.pdf/.db/.sqlite/.mov` 等原始或敏感文件到公开仓库。
- 不实现 S03-P2 数据源检查矩阵。
- 不实现 S03-P3 源优先级、冲突队列或自动选边。
- 不解析业务字段、不生成项目成本事实、不处理金额、不生成报告。
- 不接外部接口或自动同步 WPS/ERP/银行/税务系统。

## TDD 证据

- RED: 先写 `KMFA/tests/test_file_import_register.py`，运行 `python3 -m unittest KMFA.tests.test_file_import_register -q` 得到 `ModuleNotFoundError: No module named 'KMFA.tools.file_import_register'`。
- GREEN: 实现 `KMFA/tools/file_import_register.py` 后，同一测试通过：`Ran 3 tests ... OK`。

## 验收映射

| Roadmap 任务 | 验收点 | 证据 |
|---|---|---|
| `S3PAT01` | 支持 `zip/xlsx/xls/csv/pdf` 登记；zip 解包拒绝 traversal 和 symlink | `KMFA/tools/file_import_register.py`, `KMFA/tests/test_file_import_register.py` |
| `S3PAT02` | 输出 `file_hash`, `file_size_bytes`, `import_run_id`, `source_package_ref`, `storage_ref` | `KMFA/tools/file_import_register.py`, `KMFA/metadata/imports/raw_manifest_schema.json` |
| `S3PAT03` | OLE `.xls` 和 WPS native 格式返回可操作转换提示 | `KMFA/tools/file_import_register.py`, `KMFA/metadata/imports/file_import_policy.yaml` |

## 风险与控制

| 风险 | 控制 |
|---|---|
| 原始私有文件进入公开仓库 | 工具只生成 metadata bundle；`.gitignore`、no_omission、metadata/immutability gate 和敏感后缀扫描共同约束 |
| zip path traversal 覆盖本地文件 | `safe_extract_zip` 拒绝绝对路径、`..`、空路径段和 symlink entry |
| 旧 `.xls` / WPS native 误认为可直接高质量解析 | 登记为特殊容器并给出转换为 `.xlsx` 或 `.csv` 的人工提示 |
| 文件登记被误解为业务导入完成 | 本 Phase 只登记 hash/manifest/source package，不解析业务字段、不生成事实层 |

## 下一步

继续 Stage 3 时只进入 `S03-P2｜数据源检查矩阵`。Stage 3 的 P2/P3 完成并复审修复前，不上传 GitHub。
