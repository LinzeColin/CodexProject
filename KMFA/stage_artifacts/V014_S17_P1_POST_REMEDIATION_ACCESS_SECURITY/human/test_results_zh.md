# S17-P1 权限与安全测试结果

- focused test / strict validator：最终复验记录见 manifest。
- 角色/授权：4 角色 / 14 授权分配 / 16 探针 / 8 ALLOW / 8 DENY / 0 mismatch。
- 敏感策略：15 类全部 fail-closed；tracked 禁止后缀/private runtime=`0/0`。
- 审计契约：5 类 / 5 probe PASS / 0 mismatch / 0 persistent event。
- raw phase 前后 / 跨 Stage 16 review / current：exact match。
- quality：Q4 / D / NO_GO / 3-9-2-1。
