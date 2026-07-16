# Known gaps · ADP-S2-P02-T024

- **附件多文件挂载待 R2 键接入**：同 document 的多附件（不同 sha256 R2 对象）在 spec 中定义（artifact 集），实际挂载在 T022 R2 键 + 版本链任务里落地；本任务 artifact_keys 以 item_id 为锚，接 R2 后换成 object_key。
- **ttl 身份对超短/泛标题较弱**：无 DOI 时用归一化标题哈希；极短或高度模板化标题可能误合，故 DOI 优先，碰撞检测 + 回退内容 hash 兜底；真实 500 = 0 碰撞。
- **转载判据以 DOI/标题为准**：跨语言转载（中文报道英文论文）若无共享 DOI 且标题翻译不同，可能不自动归并——需后续跨语言链接规则（S2-P02 后续或 S3）。
- **只定规则不改运行时**：worker/D1 尚未按 canonical_id 去重存储；接入属后续版本链任务。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
