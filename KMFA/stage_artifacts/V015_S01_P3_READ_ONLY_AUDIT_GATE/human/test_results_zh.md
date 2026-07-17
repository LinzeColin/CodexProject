# KMFA v1.5 S01-P3 验证结果

## 最终结果

- strict validator（source package + App/raw/process + P1/P2 dependencies）：PASS；输出仍为 `EXECUTION_COMPLETE / NOT_PASSED / 2 of 3 accepted`。
- focused mutation tests：46/46 PASS；ResourceWarning 作为错误执行仍通过。
- project governance：0 errors / 0 warnings。
- lean governance：0 errors / 0 warnings。
- changed-only governance sync：0 errors / 0 warnings。
- no-float：PASS。
- no-omission：PASS；requirements=20、P0=9、P1=8、status records=1218、tasks=162。
- structured parse：JSON=4、JSONL=2、CSV=3、YAML=5，全部 PASS。
- changed public-safety scan：29 files / 0 findings。
- git diff --check：PASS。
- independent final review：blocker=0 / high=0；可本地提交，仍禁止 push。
- App：13 files / 830331 bytes / aggregate hash exact / codesign PASS。
- raw root shallow sentinel：exact；未读取 raw 名称、内容或 hash。
- 当前 App persistent process/listener：0/0。

## 负向覆盖

46 项测试拒绝：REFACTORABLE/AUDIT_BLOCKED 假结论、静态按钮作为证据、风险遗漏/重复/已关闭/无 owner/无 Stage/无 stop、推荐解决 Stage 语义链断裂、P0 覆盖缺口、未知 capability、缺证据路径、零代码/零 metadata 假声明、零 private writes、raw recursive 伪证明、process history 伪完整、否认 one-shot launch、App hash/raw sentinel 漂移、隐藏 local tracking/remote main drift、虚假 fetch 归因、共享 Git ref 变化计数归零、过期最新 stage status、伪称当前任务 push、空 phase boundaries、重复 acceptance/manifest task outcome、空 artifact refs、T03/Phase 假 PASS、S02 越界、acceptance identity 漂移、manifest/metadata/release-state 假状态、虚假 no-unexpected-change 和 `NO_SIDE_EFFECTS_PROVEN`。

## 真实终态

- T01：PASSED / RUNTIME_OBJECT_MISSING。
- T02：PASSED / 24 OPEN_WITH_PLAN risks。
- T03：NOT_PASSED / UNEXPECTED_LOCAL_GIT_STATE_CHANGE_AND_INSUFFICIENT_PREAUDIT_TELEMETRY。
- Phase：EXECUTION_COMPLETE / NOT_PASSED。
- Stage 01：NOT_PASSED；下一 Run 仅允许 Stage 01 整体复审。
