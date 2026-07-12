# 回滚方案

1. 删除本 phase public-safe artifacts 与 metadata 镜像。
2. 删除本 phase ignored private outputs；不触碰 raw 根目录和源 private inputs。
3. 移除本 phase 三条治理记录并重跑上一 phase validator。
