# KMFA v1.5 S01-P2 分支、回滚与最终合并方案

## 当前选择

复用 canonical 独立 sparse worktree：

- 路径：/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa
- 分支：codex/kmfa
- S01-P1 checkpoint：0e309502f21f12e2deba0931acd3fe1bafd0614c
- v0.1.4 public-safe 基线：d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05

该目录不是主仓库 main worktree，因此已满足“不在主工作区直接重写”。本轮不创建额外 branch、worktree 或 tag，避免重复状态面；固定 commit、blob 和 SHA-256 已足以无歧义恢复。

## 一键代码恢复

前置门禁：

```sh
test -z "$(git status --porcelain=v1)"
git cat-file -e d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05^{commit}
git merge-base --is-ancestor d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05 HEAD
```

切到 v0.1.4 public-safe tracked 视图：

```sh
git switch --detach d6f379ad11d486d8a7ebde9e61b2fc7b3aaf9d05
```

恢复开发分支：

```sh
git switch codex/kmfa
```

不使用 reset --hard、checkout --、clean 或强制删除。以上命令只切换 tracked 代码，不触碰 raw root。

## 已执行 dry-run

- 基线 commit 可解析且是当前 HEAD 祖先：PASS。
- 旧静态 target blob OID：5410e829d842f2349c2a6b02042184534bb3b1bf，PASS。
- 从 git archive 流式读取的 target SHA-256：8b3618a6ba01977ead18e03b07afc4296183ebcf02aa4b2a5e3fd4af29b816b2，PASS。
- 首次 archive 仅因本机 C.UTF-8 locale 不可用失败；设置 LANG=C、LC_ALL=C 后通过，无仓库或 raw 写入。
- raw root device/inode/size/mtime 与 S01-P1 相同：PASS。

## App 回滚边界

当前 v0.1.4 App 无 tracked builder，因此本轮禁止替换。最终替换前必须先在 ignored private runtime 建立逐文件备份，以 S01-P1 aggregate fingerprint 和 codesign 复核。新 App 只能从最终 GitHub main exact commit 构建；替换失败时先恢复旧 bundle，再复核版本、签名和指纹。

## 最终一次性合并与上传

仅在 24 Stage 全部 Phase、逐 Stage 复审及 finding 修复、最终整体复审全部通过后执行：

1. fetch origin/main，先用 merge-tree 做只读冲突预检。
2. 以 --no-ff --no-commit 合并最新 origin/main；冲突或范围异常立即 merge --abort。
3. 复跑全量、治理、public-safe 与 final validators，提交 integration commit。
4. 锁定远端 main OID，并用 ls-remote 确认未漂移。
5. 唯一一次非 force 执行 git push origin HEAD:refs/heads/main。
6. fetch 后证明 local HEAD = origin/main = GitHub main。
7. 从同一 commit 构建、重装并验证 App/GitHub/本地治理 parity。

每个 Stage 禁止上传；本轮也未上传。
