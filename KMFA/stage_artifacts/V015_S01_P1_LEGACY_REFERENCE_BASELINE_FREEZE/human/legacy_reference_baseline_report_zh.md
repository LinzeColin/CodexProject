# KMFA v1.5 S01P1 legacy 参考基线报告

## 结论

本 Phase 的事实收集和基线冻结执行完成，但验收状态必须保持 `NOT_PASSED`，决策保持 `NO_GO`。

当前 `/Users/linzezhang/Downloads/KMFA.app` 是 v0.1.4 静态 HTML 启动器，不是 TaskPack v2.0 要求的真实应用。仓库中没有 KMFA 产品的可启动源码、构建清单、服务端 API、数据库绑定或 App builder/installer 源码。

## 已冻结内容

- Git legacy 基线：`d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05`。
- `KMFA/metadata`：Git tree、文件数、字节数和公开安全聚合 SHA-256。
- 当前静态目标：Git blob 与 SHA-256，可从 baseline commit 重建。
- 当前已安装 App：版本、build、bundle id、签名、全树聚合指纹和关键文件 SHA-256。
- 桌面与移动截图：仅在 ignored private runtime 保存，公开层只登记 viewport、字节数和 SHA-256。
- raw 根目录：只登记目录元信息与顶层计数，不登记文件名、内容或文件哈希。

## 三个 Task 的真实状态

| Task | 执行状态 | 验收状态 | 结论 |
|---|---|---|---|
| S01P1T01 | COMPLETE | NOT_PASSED | RUNTIME_NOT_FOUND |
| S01P1T02 | STOPPED_BY_CONTRACT | NOT_PASSED | STATIC_SAMPLE_ONLY |
| S01P1T03 | COMPLETE_WITH_LIMITATIONS | NOT_PASSED | PARTIAL_REPO_REBUILDABLE_APP_RESTORE_ONLY |

T03 可以证明 repo、metadata 和静态目标可重建，也可以比较或从现有副本恢复 App；但无法从 tracked source 重新构建完整 App。因此不能把 legacy 参考基线包装成 v1.5 实际运行基线。

## Phase 边界

- S01P1 acceptance：`NOT_PASSED`。
- 已验收 Task：0 / 3。
- 未执行 S01P2、Stage 01 复审、GitHub 上传或 App 重装。
- 未修改业务代码、模型公式或金额路径。
- 当前证据仅支持后续 S01P2/P3 收敛差距和正式登记“运行对象缺失”，不支持进入实现 Stage。
