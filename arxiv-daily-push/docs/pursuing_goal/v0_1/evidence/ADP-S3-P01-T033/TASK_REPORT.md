# TASK_REPORT · ADP-S3-P01-T033｜实现官方身份验证与 A0 标记

## 唯一目标（达成）
用**官方域、主办单位、政府网站目录、网站标识码**验证源并标 A0；交付 identity verifier、evidence fields、manual review state。**未验证 source 不能 enabled；搜索/媒体只能作为 discovery，不得获得 A0。**

## 六个开始前问题（已回答）
1. **唯一目标**：官方身份验证器 + A0 标记；未验证不 enable；搜索/媒体 discovery-only 不得 A0。
2. **允许修改文件**：`docs/pursuing_goal/v0_1/{tools/official_identity.py, OFFICIAL_IDENTITY_SPEC.md}` + 本证据包（source_specs/identity_report/real_identity_smoke/test-results/报告）+ 治理同步。
3. **绝不能改变**：抓取行为（生产）、六主题、worker、生产 D1/R2、cron；不接生产 enable 流程。NOT_DEPLOYED。
4. **基线**：main `07cc3a29`（T032 契约测试已合入）；落实 T012 registry 的 authority 约束。
5. **验收**：未验证 source 不能 enabled；搜索/媒体只能 discovery，不得 A0。
6. **回滚**：`git revert <sha>`（纯验证器，生产未变更）。

## 交付物
- `tools/official_identity.py` —— `is_official_domain`/`is_central_domain`（央域清单）+ `extract_evidence`（页脚抽 主办单位/网站标识码/ICP）+ `verify_identity`（四证据 → authority + can_enable + discovery_only + manual_review + evidence + reasons）。
- `OFFICIAL_IDENTITY_SPEC.md` —— 四类证据、两条硬规则、分级表。
- `evidence/.../identity_report.json`（6 源分类）+ `real_identity_smoke.json`（实测 gov.cn/stats 页脚证据）。

## 验收结果（实测，见 test-results/identity_tests.txt，ACCEPTANCE = PASS，exit 0）
- **A0 标记**：中央 .gov.cn + ≥1 强证据（主办单位/网站标识码/目录）→ **A0，can_enable=True**（gov.cn 含 markers、stats.gov.cn 仅 id_code 均 A0）。
- **A1**：非中央 .gov.cn + 强证据 → A1（官方但非中央）。
- **搜索/媒体/聚合 → discovery-only，永不 A0**：media（**即使在 gov 域**）、search、aggregator → authority=该类、`discovery_only=True`、`can_enable=False`。
- **未验证不能 enabled**：official 域但零证据 → `manual_review=pending`、`can_enable=False`；声称 official 但非 gov 域 → `unofficial`、`can_enable=False`。
- **两条硬规则显式断言**：**RULE 1**（未验证不 enabled）OK；**RULE 2**（搜索/媒体永不 A0）OK。
- **真实证据**：实测 **gov.cn 页脚 = 主办单位 国务院办公厅 / 网站标识码 bm01000001 / 京ICP备05070218号 → A0**；stats.gov.cn = bm36000002 → A0（live 时点）。

## Data / Performance / Visual
Data = 6 源分类报告 + 2 站 live 页脚证据。无 UI 改动、无性能路径；六主题动效与线上 MVP 未触碰（NOT_DEPLOYED）。

## Value / Cost（S3 China A0 Official Pilot）
- **Value**：**只有被官方域 + 主办单位/标识码证明的中央源才得 A0**，未验证源拒绝 enable，搜索/媒体硬性挡在 A0 之外——保证 A0 试点权威、防止新闻噪声冒充官方；落实 T012 registry authority 约束。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 读 0 / 写 0；R2 字节 0 / 操作 0；模型 0；人工维护 = manual_review 源需人工裁决；未接生产 enable 流程。经常性云成本 delta = $0/月（live 抽取走开发环境）。

## Known gaps
见 `known_gaps.md`：NOT_DEPLOYED（未接生产 enable 闸门）；政府网站目录核验为传入标志；央域清单随适配器扩充；页脚正则抽取个别站可能抽不到（→ manual_review 偏安全）；live 抽取不逐字复现；同域不同栏目细分属 T037。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A。`data-samples` = identity_report.json + source_specs.json + real_identity_smoke.json。

## 完成声明
```text
Task: ADP-S3-P01-T033
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/official_identity.py + OFFICIAL_IDENTITY_SPEC.md + T033 证据包（source_specs/identity_report/real_identity_smoke/test-results/报告）+ 治理同步（见 changed_files.txt）
Tests: identity_tests.txt —— 8 用例(A0/A1/media·search·aggregator discovery-only/manual_review/unofficial)+RULE1 未验证不enable+RULE2 搜索媒体永不A0，ACCEPTANCE=PASS(exit 0)；real_identity_smoke.json 实测 gov.cn=A0(国务院办公厅/bm01000001)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: 官方身份验证器 + A0 标记（未验证不enable；搜索/媒体不得A0）
Data/Performance/Visual: Data=分类报告+live页脚证据；无性能/UI
Value: 只有证明的中央官方源得A0，防新闻噪声冒充官方
Cost: 请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（未接生产 enable 流程）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
