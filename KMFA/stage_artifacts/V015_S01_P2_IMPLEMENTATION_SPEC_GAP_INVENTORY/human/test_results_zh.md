# KMFA v1.5 S01-P2 验证结果

## 最终结果

- strict validator（source package + raw root）：PASS；requirements=55、migration capabilities=37、next=S01-P3、Stage 01 passed=false。
- focused mutation tests：18/18 PASS；ResourceWarning 作为错误执行仍通过。
- project governance：0 errors / 0 warnings。
- lean governance：0 errors / 0 warnings。
- changed-only governance sync：0 errors / 0 warnings。
- no-float：PASS。
- no-omission：PASS；requirements=20、P0=9、P1=8、status records=1216、tasks=162。
- structured parse：JSON=4、JSONL=2、CSV=4、YAML=5，全部 PASS。
- changed public-safety scan：31 files / 0 findings。
- git diff --check：PASS。
- 基线 commit/ancestor/blob：PASS；git archive 流式 SHA-256 在 LANG=C、LC_ALL=C 下 PASS。首次仅因本机 C.UTF-8 locale 不可用失败，无写入和副作用。
- raw root stat 与 S01-P1 一致：PASS。
- 产品修复、S01-P3、Stage 复审、push、App 重装：均未执行。

## 负向覆盖

测试明确拒绝：缺失/重复 R001-R055、空 impact/evidence、无效 Stage、TaskPack name 漂移、KEEP 未 VERIFIED、废弃精度不变量、保留静态 launcher、acceptance check identity 漂移、manifest 计数漂移、恢复命令未固定 v0.1.4、final merge 任意位置 `--force`、破坏性 reset-hard、基线 commit 漂移、提前进入 P3，以及把 Stage 01 错标为通过。
