# 回滚方案

1. 删除本 phase 公开 artifacts 和 metadata 镜像。
2. 删除本 phase ignored private outputs，保留私有输入规范；不触碰原始数据目录。
3. 移除本 phase 治理记录并重跑上一 phase validator。
