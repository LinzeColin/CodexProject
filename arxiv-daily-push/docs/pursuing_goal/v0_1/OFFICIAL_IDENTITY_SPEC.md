# Official Identity & A0 Marking Spec · ADP-S3-P01-T033

用**官方域、主办单位、政府网站目录、网站标识码**四类证据验证源并分级；工具：`tools/official_identity.py`。
**NOT_DEPLOYED**（验证器 + 规则；未接生产 enable 流程）。落实 T012 registry 的 authority 约束
（china_official 限 A0/A1/A2；media/search/aggregator 不得 official_evidence）。

## 四类证据

1. **官方域** —— 中央国家级 `.gov.cn`（`CENTRAL_GOV_HOSTS`：gov.cn / stats / ndrc / cac / nda / npc / court / spp / miit / pbc / mof …）；一般 `.gov.cn` 为官方但非中央。
2. **主办单位** —— 页脚 `主办[单位]：X`（如 国务院办公厅）。
3. **政府网站目录** —— 是否在政府网站目录登记（`gov_directory_listed` 标志）。
4. **网站标识码** —— 页脚 `网站标识码 bmXXXXXXXX`（辅以 ICP 备案）。

`extract_evidence(html)` 从**真实页脚**抽 `host_org / id_code / icp`（实测 gov.cn=国务院办公厅 / bm01000001 / 京ICP备05070218号；stats.gov.cn=bm36000002）。

## 硬规则（强制，非建议）

- **未验证 source 不能 enabled**：official 域但**无任何强证据**（host_org / id_code / directory 全无）→ `manual_review=pending`、`can_enable=False`；声称 official 但**非 .gov.cn 域** → `unofficial`、`can_enable=False`。
- **搜索/媒体/聚合只能 discovery，不得 A0**：category ∈ {media, search, aggregator} → authority=该类、`discovery_only=True`、`can_enable=False`，**即使在 gov 域也不给 A0**。原文须回溯到官方原件（T038）。

## 分级

| 条件 | authority | can_enable |
|---|---|---|
| 中央 .gov.cn + ≥1 强证据 | **A0** | True |
| 非中央 .gov.cn + ≥1 强证据 | A1 | True |
| media / search / aggregator | 该类 | **False（discovery only）** |
| official 域但零证据 | pending | **False（manual_review）** |
| 声称 official 但非 gov 域 | unofficial | **False** |

## 验收（`test-results/identity_tests.txt`，PASS）

8 用例覆盖上表；两条硬规则显式断言：**RULE 1** 未验证(pending/unofficial)不 enabled；**RULE 2** 搜索/媒体/聚合永不 A0/enabled。`real_identity_smoke.json` = 实测 gov.cn/stats.gov.cn 页脚证据 → A0（live 时点，不逐字复现）。

## 边界

`gov_directory_listed` 目前为传入标志（真实目录核验接入属后续）；央域清单随 T034+ 适配器扩充；`manual_review` 是状态标记，接生产 enable 闸门属后续接线。
