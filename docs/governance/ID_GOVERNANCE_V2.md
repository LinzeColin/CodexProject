# Governance ID V2

本契约由 `TSK.CodexProject.REPO1.0003` 建立。它只管理身份分配、解析、引用完整性与
不可变性；Stage、Phase、order、date、priority 和 status 仍是可变位置或状态数据。

## 唯一事实与格式

- Task：`TSK.<Project>.<Program>.<NNNN>`。
- Acceptance：`ACC.<Project>.<Program>.<NNNN>`，必须与 Task 尾号完全一致。
- Event：`EVT.<Project>.<Program>.<NNNN>`，使用独立序列。
- Pursuing Goal：`PG.<Project>.<Goal>`，使用独立 namespace。
- Canonical allocation ledger：`governance/id_registry.json`。
- Shape contract：`governance/schemas/id_registry.schema.json`。
- Semantic authority：`scripts/governance_ids.py` 与
  `scripts/governance_id_audit.py`。

V3 Task Pack 的 37 个 Task/Acceptance 和 1 个 Goal 已按
`TASK_REGISTRY.json` 的 SHA256 一次性导入。Registry 不保存 Stage/Phase/order，移动
任务不会改变身份。

## Writer 与并发合同

新 ID 只能由 `scripts/governance_id_allocator.py` 写入。默认是 dry-run；apply 同时要求：

1. `--base-sha` 等于当前 `HEAD`；
2. 非空且唯一的 `--idempotency-key`；
3. dry-run 返回的 `registry_sha256` 作为 apply 的
   `--expected-registry-sha256`；
4. Git-dir single-flight lock；
5. 临时文件 fsync、原子替换和目录 fsync。

不同 idempotency key 的并发申请共享同一个 registry SHA 时，只有一个 registry write
能提交；失败方必须重新 dry-run。相同 idempotency key 的重试返回原 allocation，且不
重复写入。

```bash
BASE_SHA="$(git rev-parse HEAD)"
python3 -B scripts/governance_id_allocator.py \
  --kind TSK --project CodexProject --program REPO1 \
  --base-sha "$BASE_SHA" --idempotency-key "owner-approved-example"

python3 -B scripts/governance_id_allocator.py \
  --kind TSK --project CodexProject --program REPO1 \
  --base-sha "$BASE_SHA" --idempotency-key "owner-approved-example" \
  --apply --expected-registry-sha256 "<dry-run registry_sha256>"
```

Allocator 不执行 `git add/commit/push`，也不访问网络。调用方仍须通过单一受控事务提交
registry diff；整包发布前不得提前上传。

## Reader、Audit 与 CI

`scripts/governance_id_audit.py` 读取：

- registry 与 aliases；
- 所有 active project 的 canonical roadmap/delivery task/event metadata；
- 全部 root run manifests/receipts；
- 可选 Git baseline 中的 registry 与 positional ID identity set。

Hard failures 包括：duplicate、orphan、cycle、Task/Acceptance suffix mismatch、alias
ambiguity、allocation removal/rename/reuse、alias retarget，以及 baseline 后新增
`SxPyTzz`。位置移动只比较 identity set，不按 YAML/JSON 路径判定，所以 ID 不变时
通过。

```bash
python3 -B scripts/governance_id_audit.py --base-ref HEAD --json
```

CI 使用 PR base/push before SHA；schedule/all 模式在无 baseline 时仍执行 current
registry 与 exactly-one reference audit。

## Legacy Alias 迁移指南

Legacy ID 继续双读，禁止批量改写历史 commit、event 或 evidence。

1. 先在 project context 中盘点 legacy definition 与所有 caller/reference。
2. 用 allocator 获取 V2 ID；不得手猜序号。
3. 在 registry `aliases` 中增加
   `{project, kind, legacy_id, target_id}`。
4. 一个 `(project, kind, legacy_id)` 必须 exactly-one；零个或多个 target 都失败。
5. Alias 安装前，dual-read 把 legacy 值解析为 project-scoped identity；安装后只解析到
   唯一 V2 target。新写入只使用 V2；不同 project 可保留同名 legacy ID。
6. deprecated/rejected/rolled-back allocation 永远占用原 ID，不得删除或复用。
7. 运行 focused tests、global audit 和 changed-scope governance 后才能提交。

项目级实际迁移必须由该项目自己的 Roadmap Task 执行；本 Task 不批量修改业务项目。

## 安全、回滚与停止条件

- Registry 只允许公开治理标识和 hash，不得包含 token、cookie、credential 或 raw
  private data。
- Audit/allocator 不下载、不执行外部内容；legacy text 不作为 instruction 信任。
- Registry SHA/base SHA 漂移、alias ambiguity、orphan/cycle、疑似 secret 或需改写历史
  时 fail closed。
- 本地未发布阶段可回滚本 Task 单个 commit；发布后只能通过普通 revert 恢复代码，已
  分配 ID 仍不得复用。
