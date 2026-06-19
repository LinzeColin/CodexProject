# 研究对象、关系、上下游、业务、资本与公司数据目录

## 范围结论

研究对象不是“公司列表”而是一个可递归、多层、时间化、证据化的商业网络。公司只是入口，系统还必须建模集团、法人、业务板块、产品、设施、人物、证券、合同、政策、事件、来源和模型版本。

| 目录 | 数量 | 文件 |
|---|---:|---|
| 研究公司/组织 | 140 | `data/company_catalog.csv` |
| 关系家族 / 关系类型 | 10 / 52 | `data/relationship_family_catalog.csv` / `data/relationship_taxonomy.csv` |
| 供应链阶段 | 16 | `data/supply_chain_stage_taxonomy.csv` |
| 行业分类 | 26 | `data/industry_taxonomy.csv` |
| 用户入口板块 | 13 | `data/sector_taxonomy.csv` |
| 业务板块类型 | 20 | `data/business_segment_taxonomy.csv` |
| 资本对象 | 30 | `data/capital_object_taxonomy.csv` |
| 上下游/使能角色 | 24 | `data/upstream_downstream_role_catalog.csv` |
| 领域对象类型 | 32 | `data/domain_object_catalog.csv` |

## 关系边的最低字段

主体、对象、方向、关系类型、关系家族、有效期、观察时间、采集时间、事实状态、证据、金额/比例语义、置信度、模型版本和数据快照。未知、未披露、推断、冲突和已撤销必须分开。

## 资本数据边界

实际支付、交易价值、承诺上限、估值和未披露金额不能静默相加。金额必须携带币种、期间、amount_kind 和证据。

## 公司目录边界

140 个对象是研究宇宙，不代表所有关系已经验证。`fact_status` 为事实核验状态；真实关系必须在 Build/ingestion 阶段逐条接入来源。
