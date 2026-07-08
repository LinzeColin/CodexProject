#!/usr/bin/env bash
set -euo pipefail

# Install this skill into LinzeColin/CodexProject/KMFA/fund-weekly-analysis-skill,
# validate, commit, and push to main. No branch, no PR.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="${KMFA_REPO_ROOT:-}"
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(git -C "$SKILL_SRC" rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
TARGET_DIR="$REPO_ROOT/KMFA/fund-weekly-analysis-skill"
METADATA_DIR="$REPO_ROOT/KMFA/metadata/fund_weekly_analysis"

cd "$REPO_ROOT"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: REPO_ROOT is not a git repository: $REPO_ROOT" >&2
  exit 2
fi
BRANCH="$(git branch --show-current)"
if [[ "$BRANCH" != "main" ]]; then
  echo "ERROR: must be on main, current branch is $BRANCH" >&2
  exit 3
fi

git fetch origin main
git merge --ff-only origin/main

mkdir -p "$TARGET_DIR" "$METADATA_DIR"
rsync -a --delete --exclude='.git' "$SKILL_SRC/" "$TARGET_DIR/"
cat > "$METADATA_DIR/.gitignore" <<'GITIGNORE'
private_runtime/
*.sqlite
*.db
*.zip
*.png
*.jpg
*.jpeg
*.webp
*.xlsx
*.xls
*.csv
*.pdf
*.doc
*.docx
!README.md
!.gitignore
GITIGNORE
if [[ ! -f "$METADATA_DIR/README.md" ]]; then
  cp "$TARGET_DIR/metadata/README.md" "$METADATA_DIR/README.md"
fi

python3 "$TARGET_DIR/tools/validate_taskpack.py"

git add KMFA/fund-weekly-analysis-skill KMFA/metadata/fund_weekly_analysis/.gitignore KMFA/metadata/fund_weekly_analysis/README.md
git add -f KMFA/fund-weekly-analysis-skill/templates/资金与税费管理母版_真实数据预览_v2.xlsx
if git diff --cached --quiet; then
  echo "No tracked changes to commit."
else
  git commit -m "Add KMFA fund weekly analysis skill"
  git push origin main
fi

echo "PASS: installed, validated, and pushed to main when changes existed."
