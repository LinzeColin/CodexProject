# CodexProject

Active Codex-related project hub for LinzeColin.

This repository is a parent index that keeps active project repositories together
as git submodules. The original repositories remain independent and keep their
own history, issues, settings, and release flow.

## Projects

| Path | Repository |
| --- | --- |
| `Alpha` | https://github.com/LinzeColin/Alpha |
| `EVA_OS` | https://github.com/LinzeColin/EVA_OS |
| `OpenAIDatabase` | https://github.com/LinzeColin/OpenAIDatabase |
| `FIFA` | https://github.com/LinzeColin/FIFA |
| `Serenity-Alipay` | https://github.com/LinzeColin/Serenity-Alipay |
| `OpMe_System` | https://github.com/LinzeColin/OpMe_System |
| `whkmSalary` | https://github.com/LinzeColin/whkmSalary |

## Clone

```bash
git clone --recurse-submodules git@github.com:LinzeColin/CodexProject.git
```

If already cloned:

```bash
git submodule update --init --recursive
```

## Update submodule pointers

```bash
git submodule update --remote --merge
git status
git add .gitmodules Alpha EVA_OS OpenAIDatabase FIFA Serenity-Alipay OpMe_System whkmSalary
git commit -m "Update project submodule pointers"
git push
```

## Rule

Do not move project source code into this parent repository unless a future
monorepo migration is explicitly approved. This parent repository should remain
a clean navigation and orchestration layer.
