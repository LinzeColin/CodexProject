# Owner 控制台

主入口已迁移到 GitHub 浅层目录：

- `arxiv-daily-push/用户中心/README.md`
- `arxiv-daily-push/用户中心/邮件发送与队列状态.md`

本文件保留为兼容旧路径的指针，不再作为 owner 主阅读入口。

## 当前摘要

| 信息 | 当前值 |
|---|---|
| 今天最新补发 | `sent` |
| 最新模板 | `EMAIL_LEARNING_V1` |
| 今天最新未发送/阻断 | 0 |
| 当前排队候选 | 11 |

## 当前边界

- GitHub `用户中心` 是 owner 人类可读入口。
- 本机运行文件是底层证据来源，不是 owner 阅读入口。
- Stage 1 本机日常邮件已可真实发送；Stage 2 integrated production 仍不能因为本文件自动宣称通过。
- Owner 文档不能直接触发补发、改队列、改 SMTP 密钥、改 scheduler、改 public schema 或改数据库。
