# Stage 7 GitHub Main Upload Risk and Rollback

## Risk

- 本轮只执行 Stage 7 GitHub main upload gate。
- 上传前已确认当前 `origin/main` 漂移未触碰 `PFI/`。
- 本轮不修改真实财务数据源，不写入 `MetaDatabase/PFI`，不重装 app bundle。
- 本轮不进入 Stage 8。

## Upload Safety

- 先 `git fetch origin main`。
- 再确认 Stage 7 commits 已在当前 `origin/main` 之上，ahead/behind 为 `4/0`。
- 上传前重新运行 Stage 7 upload、whole-review、phase regression、Stage 6 adjacent regression、browser validation、syntax、JSON 和 diff checks。
- 上传后用 `git ls-remote origin refs/heads/main` 和 fresh fetch 验证 `HEAD == origin/main == remote main`。

## Rollback

如上传后需要回退，应新建 revert commit 回退 Stage 7 upload commit 和 Stage 7 package commits；不要 `git reset --hard` 或强推 main。回退不会影响用户真实数据，因为本轮没有数据写入或 app bundle 重装。
