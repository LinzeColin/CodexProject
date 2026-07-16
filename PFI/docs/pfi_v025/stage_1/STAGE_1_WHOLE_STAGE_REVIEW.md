# PFI v0.2.5 Stage 1 Whole-Stage Review

## 唯一验收目标

- Contract：`PFI-V025-STAGE1-WHOLE-REVIEW`
- Acceptance：`ACC-PFI-V025-STAGE1-WHOLE-REVIEW`
- Stage base：`9380fdf4a500f48a2b15859044ab7926b4924391`
- Whole-review base：`96305405dcf7eb56246d2cede2f5b50b2b1be101`
- Final remediation content：`04390bcf17c18de107eb2f1b4ce051c83638f98c`
- Tracked lifecycle：`candidate_pass_pending_postcommit_attestation`
- Remediation scope override：`PFI-V025-STAGE1-WHOLE-REVIEW-REMEDIATION-SCOPE-20260713`
- Launch method override：`PFI-V025-S1-NO-FINDER-20260713`（用户明确要求停止所有 Finder 操作）

## 范围与非范围

本 review 只复核 Stage 1 的 `S1-P1-T1..T4`、`S1-P2-T1..T4`、`S1-P3-T1..T4`，以及三组 Phase evidence/attestation chain。它不进入 Stage 2，不执行 canonical App install、dependency install、GitHub push、真实数据或数据库读取，也不替代 Stage 12 final human acceptance。

Roadmap 原始 allowlist 对 `runtime_api.py` 仅允许 release-manifest API，且未列出 production `streamlit_app.py` 与 `shell.js`。用户在 2026-07-13 明确授权最终验收前全部阶段内动作并要求不重复阻断；本 review 将该决定记录为独立 remediation scope override，只扩展到 verifier 固定的五个内容路径，并且不把它解释为 release acceptance、canonical install、push、数据访问或 future-stage 授权。

## 整改后的生产事实

- 唯一官方候选入口是 production `PFI/src/pfi_os/app/streamlit_app.py`；旧的简化候选入口已删除。
- release identity 绑定 14 个真实 frontend sources 与 12 个 release-critical backend/startup sources；Python 与 Node 使用相同 bytewise path order 并交叉测试。
- disposable candidate 使用 isolated empty data home，不读取 canonical finance data 或 SQLite；所有写 API返回 `403`。
- `/usr/bin/open -n -a ${ISOLATED_ROOT}/PFI.app` 经 LaunchServices 启动的隔离候选使用一个三成员进程组与三个 loopback listeners，未执行 Finder UI 操作；live `8501/8502/8766` 不在请求或监听集合中。
- fresh browser profile 验证 ordinary reload、cache-cleared reload、back/forward、pageshow、manifest/cache/read-model API、source bytes、console/network、无障碍与 cleanup。
- privacy gate 扫描 runtime payload、visible DOM、full HTML、trace ZIP 解压成员及无 metadata PNG；中文金额、账号、样本量和金融表单值均 fail closed。
- live form-control gate 直接读取可见 `input/textarea/select.value`，只持久化 count 与结构 hash；生产“数量/成本/价格”的 property-only 当前值不会被 `outerHTML` 漏掉。
- 隔离空数据 UI 显示“隔离候选未加载真实数据”，不再声称“本机数据可用”。

## Review findings

| Review | Critical | Important | Minor | 结果 |
|---|---:|---:|---:|---|
| 初始 whole-stage product review | 1 | 3 | 0 | 已整改 |
| verifier independent review | 2 | 4 | 2 | 已整改 |
| content re-review | 1 | 2 | 0 | 已整改 |
| C4 live-control re-review | 1 | 0 | 0 | 已整改 |
| C12 targeted source re-reviews | 0 | 0 | 0 | legacy/shell/browser source 定向复核通过 |
| C20 LaunchServices/runtime evidence recheck | 0 | 0 | 0 | 36/36 browser checks、10/10 routes、3-member process group、3 endpoints 与 cleanup 全通过 |
| final prebinding rereviews | 0 | 0 | 0 | 三个独立 lane 的 exact-hash reports 由 `review_audit.json` 绑定 |

## 验收与激活语义

Tracked evidence 只能声明 `PASS_PENDING_POSTCOMMIT_ATTESTATION`，因为 binding commit 不能把自身 SHA 写进自身内容。唯一 direct binding successor 提交后，三路独立 postbinding reviews 必须全部为 `C0/I0/M0`，external attestation 必须同时绑定 content commit、binding commit、evidence SHA、manifest SHA 与 exact binding path set。只有该 attestation 通过时，Stage 1 才解释为 `accepted_for_transition`，Stage 2 entry 才被授权；Stage 2 本身仍为 `not_started`。

## 回滚与停止条件

- 回滚：先以 path-limited compensating commit 撤销唯一 binding successor，再撤销 final remediation content commit；保留历史 Phase commits/events/attestations，不改写 append-only history。
- 停止条件：identity/source mismatch、非隔离数据访问、visible DOM/trace/privacy finding、canonical entry delta、进程/端口/LaunchServices 未清理、独立 review 非 `C0/I0/M0`、治理 validator 非零，均禁止 attestation。
- 本轮不 push、不安装、不进入 Stage 2；canonical install gate 仍为 `S12-P2-T1`。
