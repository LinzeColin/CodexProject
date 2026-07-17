# S01P1 测试结果

状态：`EVIDENCE_VALIDATION_PASS / PHASE_ACCEPTANCE_NOT_PASSED`

验证结果：

1. strict baseline validator：PASS；同时校验 private evidence、installed App、raw root、remote main 和 source package；输出明确为 `phase_acceptance=NOT_PASSED / accepted_tasks=0/3`。
2. focused unittest：13/13 PASS；覆盖 happy path、false Phase PASS、acceptance/metadata 文档身份、acceptance check identity/finding、metadata App hash、SHA inventory hash、空 release-state、private evidence 缺项、artifact refs、phase gate、not-passed count 与 live remote 可验证性变异。
3. project governance required / lean governance required / changed-only governance sync：全部 PASS，`errors=0 / warnings=0`。
4. no-float / no-omission：PASS；no-omission=`requirements 20 / P0 9 / P1 8 / status 1215 / tasks 162`。
5. structured parse：JSON=3、JSONL=2、CSV=3、YAML=5，全部 PASS。
6. changed-file public safety：28 个文件，禁止二进制/private 后缀、private key、API key 和 key-shaped credential 扫描 findings=0。
7. `git diff --check`：PASS；raw root、installed App 与 GitHub main 均由 strict validator 复核一致。

结论：validator `PASS` 仅证明证据链一致；manifest 和 acceptance matrix 继续显示 `S01P1=NOT_PASSED`、`NO_GO` 和 3 项未通过验收。
