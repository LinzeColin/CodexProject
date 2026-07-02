# v0.2.4 Overall Project Review Risk and Rollback

## Risks

- Stage 8.3 and Stage 9.3 phase evidence keeps historical waiting states. Mitigation: overall review uses whole-stage review and upload evidence as the acceptance source after user replied `1`.
- Remote `main` may advance before final push. Mitigation: fetch and inspect before push; if PFI paths changed, stop and rebase only after review.
- Final commit hash is self-referential to this evidence pack. Mitigation: record final proof in terminal output after push.

## Rollback

- If local validation fails, do not push; fix only within this overall review gate.
- If push fails, fetch and inspect `origin/main` before any rebase.
- If final remote verification fails, stop and report `HEAD`, `origin/main`, and `ls-remote` hashes.

## Non-Goals

- future version 未开始。
- No app bundle reinstall.
- No launcher C or Info.plist mutation.
- No real financial data mutation, deletion, cleanup, backfill, or synthesis.
- No mock/sample/demo/synthetic/fixture/fake financial data.
