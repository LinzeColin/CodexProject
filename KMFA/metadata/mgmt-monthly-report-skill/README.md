# 经营管理月报 Metadata

该目录保存 `mgmt-monthly-report-skill` 的数据治理资产。经 owner 明确授权、secret
扫描和 upload manifest 登记后，原始敏感明文文件也可以放入 `KMFA/metadata/`。

允许提交：

- hash index
- run manifest
- backup registry
- validation summary
- cleanup report
- SQL schema/export
- 脱敏日志摘要
- owner 授权明文上传登记
- owner 授权且 secret 扫描通过的原始敏感明文文件

不允许提交：

- token、API key、webhook secret、signing key、账号密码、私钥
- 未登记 owner 授权和 secret 扫描结果的敏感明文文件
