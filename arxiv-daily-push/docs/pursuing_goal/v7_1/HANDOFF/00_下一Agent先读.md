# 下一 Agent 先读

## 当前结论

V7.1 三轨审查已完成，**生产合并被 P0/P1 阻塞**；Stage2 Shadow 来源开发可继续。

## 唯一下一任务

`S2PAT05_V7.1并行审查落库与治理修复`

## 读取顺序

1. `README_先读.md`
2. `09_并行审查/并行审查汇总与合并结论.md`
3. `09_并行审查/问题清单.csv`
4. `08_首批任务卡/S2PAT05_V7.1并行审查落库与治理修复.md`
5. `machine_readable/product_contract_v7.yaml`
6. `ROADMAP/ARXIV_DAILY_PUSH_ROADMAP_V7_1_CN.md`

## Side conversation 同步

- `HANDOFF/05_Stage1本机日更运行侧线程同步.md` 记录了 Stage1-only 本机 launchd、真实 SMTP 发送、readiness 验收、V7.1 M1-compatible 邮件模板修复、本机 arXiv HTTPS CA 修复和主线程合并建议。注意：上一轮真实 SMTP 发送使用旧模板；本轮当前代码已通过真实 arXiv no-send preview 和真实 `local-runner daily --allow-smtp-send` 发送证明新模板，且 readiness 重新通过。主线程应自行判断是否吸收 `codex/adp-stage1-daily-operation-hardening-20260624` 分支，不得把该记录误用为 Stage2 integrated production acceptance。

## 禁止

- 不得直接开始 S2PMT02–T07 而未先把 V7.1 合同落库。
- 不得在没有完整仓库测试证据时把 not_verified 改成 PASS。
- 不得启用真实 SMTP、restore、scheduler install 或 DAILY_OPERATION。
