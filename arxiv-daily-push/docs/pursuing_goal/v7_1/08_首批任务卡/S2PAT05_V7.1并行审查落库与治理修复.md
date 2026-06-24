# S2PAT05｜V7.1 并行审查落库与治理修复

- Pursuing Goal：把本包全部关键结论写入 GitHub 中文人类入口和机器事实源，修复依赖、Stop Code、追踪和交接门。
- 允许读取：产品合同、Roadmap、AGENTS、三基、当前 Task、机器 YAML。
- 允许修改：上述治理文件、`00_用户中心` 生成器、Task Pack validator。
- 禁止修改：来源解析器、运行副作用实现。
- 测试：`python tools/validate_task_pack.py --root <落库目录>`；对应治理 pytest。
- Stop Gate：所有机器文件可解析；任务依赖无环；Stop Code 100% 注册；需求追踪 100%；三基/用户中心同步。
- 回滚：单提交回滚，不覆盖历史 V5/V6/V7.0 证据。
