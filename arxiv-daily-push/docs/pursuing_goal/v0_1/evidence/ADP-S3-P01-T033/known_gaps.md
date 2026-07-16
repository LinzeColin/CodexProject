# Known gaps · ADP-S3-P01-T033

- **NOT_DEPLOYED（任务边界，非缺陷）**：验证器 + 规则未接生产 enable 流程。把 `can_enable=False` / `manual_review` 接成 registry/worker 的硬闸门（拒绝 enable 未验证源）属后续接线；本任务只交付 verifier + evidence fields + manual_review 状态。
- **政府网站目录核验为传入标志**：`gov_directory_listed` 目前由调用方提供，尚未真正查政府网站目录 API/页面核验；真实目录核验属后续（可作第 4 类强证据）。
- **央域清单需随适配器扩充**：`CENTRAL_GOV_HOSTS` 覆盖 gov.cn/stats/ndrc/cac/nda/npc/court/spp/miit/pbc/mof 等；T034+ 接新央源时补充。非中央 .gov.cn 判 A1（本任务不细分 A1/A2 省市级，留待需要时）。
- **主办单位/标识码为页脚正则抽取**：`extract_evidence` 用页脚正则抽 `主办/网站标识码/ICP`；个别站页脚结构异常可能抽不到（→ manual_review，偏安全不误判 A0）。真实各站页脚差异由 T034+ fixtures 覆盖。
- **live 页脚抽取不逐字复现**：`real_identity_smoke.json` 是实测 gov.cn/stats.gov.cn 的 live 时点证据（站点会变）；确定性验收跑在 fixture 页脚上。live 抽取走开发环境（非 worker）→ 0 云成本。
- **media on gov domain**：若某官方站同时含媒体栏目，本任务按 source 的 category 判定（category=media → discovery only）；细粒度「同域不同栏目」区分属 T037 Board3 准入范围。
