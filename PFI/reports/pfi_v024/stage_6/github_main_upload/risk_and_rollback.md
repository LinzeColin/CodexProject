# Stage 6 GitHub Main Upload Risk and Rollback

## Risk

- 本轮只执行 Stage 6 GitHub main upload gate。
- 上传前已确认当前 `origin/main` 的漂移只触碰 `OpenAIDatabase/`，未触碰 `PFI/`。
- 本轮不修改真实财务数据源，不写入 `MetaDatabase/PFI`，不重装 app bundle。

## Upload Safety

- 先 `git fetch origin main`。
- 再将 Stage 6 commits rebase 到当前 `origin/main`。
- 上传前重新运行 Stage 6 upload、whole-review、phase regression、Stage 5 adjacent regression、browser validation、syntax、JSON 和 diff checks。
- 上传后用 `git ls-remote origin refs/heads/main` 和 fresh fetch 验证 `HEAD == origin/main == remote main`。

## Rollback

如上传后需要回退，应新建 revert commit 回退 Stage 6 upload commit 和 Stage 6 package commits；不要 `git reset --hard` 或强推 main。回退不会影响用户真实数据，因为本轮没有数据写入或 app bundle 重装。
