# Known gaps · ADP-S2-P01-T021

- **只定合同不写 R2**：本任务是 content-addressed 键/hash/元数据/压缩的**合同 + 计算工具**，NOT_DEPLOYED，未写任何 R2 对象、未开 R2。
- **R2 NOT_ENABLED（FACT-012）**：R2 未启用是 Owner 后台/计费动作（Owner 已表示不碰后台）。**T022（feature-flagged dual-write，SHADOW）需要真写 R2**——到 T022 必须由 Owner 决定：开启 R2，或将 S2 剩余（T022/T023）延后。本任务不代开 R2。
- **mime 嗅探为轻量启发式**：覆盖 PDF/HTML/JSON/XML 常见头；异形内容可能需扩展。
- **content_version 语义**：默认 v1；真正的版本链在 S2-P02（Canonical Document 与版本链）细化。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
