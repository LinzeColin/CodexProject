# 回滚方案

1. 删除本 phase 的公开 artifacts 和 metadata 镜像。
2. 删除本 phase 的忽略私有运行目录；不触碰 operator 原始数据目录。
3. 从治理 JSONL 中移除本 phase 对应记录。
