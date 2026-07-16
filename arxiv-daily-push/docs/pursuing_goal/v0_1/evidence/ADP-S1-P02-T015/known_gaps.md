# Known gaps · ADP-S1-P02-T015

- **scanner 未挂进 GitHub workflow**：check_source_drift.py 可本地/CI 运行且已验证，但尚未加入 .github/workflows（接入属后续部署纪律任务）；一旦接入，任何来源漂移的 PR 会被红灯。
- **runtime/D1 比对以 worker REGISTRY 为线上代理**：本任务用 worker_cloud.js 的 REGISTRY 作为「线上来源」的代理（它就是当前真身），未直连 D1 cn_sources 逐行比对（0 D1 读）；worker 改为消费 compiled/runtime.json 后可加 D1 直连比对。
- **第二数组检测基于 const <NAME> = [ 含 source 条目**：手写来源若用非 const 数组或异形结构可能规避；当前覆盖 worker 现有写法 + 常见注入。
- **例外文件需人工审批**：新增合法来源应改 Registry 重编译；确需线上有而 registry 无的，须显式写入 SOURCE_DRIFT_EXCEPTIONS.yaml 并附理由。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
