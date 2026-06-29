# PFI v0.2.3 Stage 1 App 入口与前端版本一致性

## 目标

Stage 1 只解决入口一致性：用户从 `~/Downloads/PFI.app` 打开 PFI 时，必须启动当前 checkout 的本机服务，并加载同一份 v0.2.3 前端 bundle。

## 本轮范围

- 更新 `PFI.app` bundle version 为 `0.2.3 / 20260629.1`。
- 启动 URL 固定携带 `pfi_app_version=0.2.3`、`pfi_build=20260629-stage1` 和 `pfi_ui_contract=PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY`。
- Streamlit 嵌入的 Web Shell 注入当前 checkout 的 `projectRoot`、`webBundleHash`、`webIndexSha256`、`shellJsSha256`、`buildId` 和 `uiContractVersion`。
- `scripts/installPFIEntryApps.sh --downloads-only` 可只安装 `~/Downloads/PFI.app`，并写入 `Contents/Resources/PFI_PROJECT_ROOT` 绑定当前 checkout。
- 验收必须使用真实 `~/Downloads/PFI.app` 和全新浏览器 profile 验证。

## 明确不做

- 不做 Stage 2 页面重建。
- 不修改一级入口数量或路由归属。
- 不改数据计算、read model、报告生成或财务结论。
- 不引入 mock、sample、synthetic、fixture、demo、fake 财务数据。

## 一致性字段

Stage 1 evidence pack 至少记录：

- repo path
- current HEAD
- app path
- app project binding
- served URL
- browser profile path
- build id
- app version
- UI contract version
- web bundle hash
- `PFI/web/index.html` sha256
- `PFI/web/app/shell.js` sha256

## 验证命令

```bash
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests/test_v023_stage0_contract.py PFI/tests/test_v023_stage1_app_entry_bundle_contract.py PFI/tests/test_pfi_app_entry_version_contract.py -q
PFI/scripts/installPFIEntryApps.sh --downloads-only
PFI/scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI.app --summary-json
```

浏览器验收使用独立临时 profile，并从真实页面 iframe 中读取 `window.PFI_STAGE1_ENTRY_METADATA` 与磁盘 bundle hash 对比。
