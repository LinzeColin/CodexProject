# 机器治理

这里放 Memory Atlas v1.2 的机器可读参数、公式、数据契约、同步配置、验收门禁和运行证据。

本目录不替代 apps/scripts/tests/config/data/docs/governance。现有运行代码、测试、配置、
数据和旧治理目录继续留在原位置。

## 子目录

- `参数与公式/`：公式、权重、阈值和参数解释。
- `数据契约/`：source、raw、derived、reports、visualization 的 schema 或契约。
- `同步与备份/`：ChatGPT、Codex、后续其他 agent 的 source registry 和同步策略。
- `可视化配置/`：图表、human question map、visual ROI gate 的机器配置。
- `行为智能模型/`：facets、clusters、latent signals、collaboration quality 的模型配置。
- `运行门禁/`：stage gates、stop conditions、rollback 和需求冻结。
- `测试与验收/`：validator、acceptance matrix 和测试说明。
- `证据与日志/`：run evidence、audit logs、manifest/hash 和 stage evidence。

## 当前阶段

当前为 S03 P2。S01 整体复审已通过，S02 整体复审已通过，公开 raw 路径、
manifest/hash 文件合同、append-only 规则、hash drift fail 规则和 credential is not memory
门禁已定义。

当前机器产物：

- `数据契约/source_data_model.v1_2_s02_p1.json`
- `同步与备份/sync_source_registry.json`
- `同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json`
- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `../人类可读/05_ChatGPT与Codex及其他Agent自动同步说明.md`
- `../人类可读/06_Raw明文公开与只读归档说明.md`
- `../人类可读/07_凭证排除说明.md`
- `../data/public_raw/README.md`
- `人类可读/06_Raw明文公开与只读归档说明.md`
- `data/public_raw/README.md`
- `../docs/reviews/memory_atlas_v1_2_s02_review.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p1_public_raw_path.md`
- `../docs/reviews/memory_atlas_v1_2_s03_p2_credential_exclusion.md`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`

`运行门禁/v1.2需求冻结清单.json` 继续固定：

- 四线范围。
- 14 Stage 与每次 run 最多一个 phase 的执行规则。
- raw 公开授权。
- 凭证排除。
- 后续其他 agent 数据源扩展规则。

下一步是 S03 P3；本目录仍不替代 apps/scripts/tests/config/data/docs/governance。
