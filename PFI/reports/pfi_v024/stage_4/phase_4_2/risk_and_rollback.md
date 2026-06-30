# Stage 4 Phase 4.2 Risk And Rollback

- 风险：`/api/read-model-status` 或嵌入 JSON 失败时，页面可能回到旧空态。
- 控制：shell 同时支持 API 与 `#pfi-read-model-status` 嵌入兜底；非 ready 状态不显示财务 0。
- 回滚：回滚 `PFI/src/pfi_os/application/read_model_status.py`、runtime endpoint、`data_state.js`、`shell.js`、`index.html` 和 Streamlit embed 改动；保留 Phase 4.1 状态机合同。
- 数据安全：本轮只读 `MetaDatabase/PFI` 摘要，不写入、清理、删除或补造用户数据。
