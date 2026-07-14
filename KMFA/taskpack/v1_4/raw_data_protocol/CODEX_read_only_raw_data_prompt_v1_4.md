# KMFA Codex 本机原始数据读取只读启动提示词 v1.4

Project: KMFA
Mode: PLAN / READ_ONLY first
Risk: T3 because company financial raw data is involved

本轮目标：
在不修改任何原始数据的前提下，读取并登记用户本机原始数据目录，建立 raw manifest、hash、数据源检查矩阵和字段合同候选。

原始数据只读目录：

```text
/Users/linzezhang/Downloads/KMFA_MetaData
```

绝对禁止：

```text
不得在原始数据目录写入任何文件。
不得删除、移动、重命名、覆盖、转换原始文件。
不得在原始数据目录生成临时文件、缓存、日志或报告。
不得把原始敏感数据提交 GitHub。
不得把账号密码、银行明细、客户合同全文、工资明细提交 GitHub。
```

允许：

```text
只读遍历目录。
读取文件元数据。
计算 hash。
复制到 KMFA/local_runtime/raw_ingest/ 后处理。
把不含敏感值的 manifest / hash / 状态写入 KMFA/metadata。
```

第一轮只输出计划，不实现。必须输出：

```text
1. 拟读取目录和文件类型
2. 拟写入 KMFA 的文件清单
3. 不会写入原始目录的证明方式
4. raw manifest schema
5. hash 计算命令
6. metadata 输出路径
7. 测试命令
8. 回滚方案
9. stop conditions
```

Stop conditions：

```text
发现脚本试图写入 /Users/linzezhang/Downloads/KMFA_MetaData 立即停止。
发现任何金额使用 float 立即停止。
发现同源引用不一致但未触发重跑立即停止。
发现 raw 文件被修改、mtime 改变、hash 改变但无人工授权立即停止。
```
