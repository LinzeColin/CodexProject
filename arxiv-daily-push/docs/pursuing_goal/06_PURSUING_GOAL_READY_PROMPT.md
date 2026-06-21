# Pursuing Goal Ready Prompt

```text
/goal 构建并验证 arXiv 日报推送（arXiv Daily Push）：一套私有、自用、非商业、证据可追溯、可长期稳定运行的每日 arXiv 学习推送系统。系统必须在 Australia/Sydney 每日 05:00 从 arXiv 最新可用来源中增量抓取、去重、评分、选择一项最值得学习的内容，生成专业中文文本讲解、自然中文旁白和高质量二维动画视频；每周生成前沿雷达，每月生成社会技术成熟度地图。Phase 1-11 以 arXiv 为第一和唯一初始数据源对象，但架构必须保留 SourceAdapter、SourceItem、EvidenceClaim、Lesson、Storyboard、Publication、RunRecord 等通用边界，未来可接入 RSS、GitHub、标准、产业报告、网页、书籍、课程、播客和用户文档，不得把核心系统写死成 arXiv-only。

使用 A+C 架构：本地 Codex 负责开发、证据约束的内容理解与复核；GitHub Actions + private self-hosted runner 负责定时、串行编排、日志、人工补跑和 GitHub Release。GitHub 仓库为 LinzeColin/CodexProject，项目路径为 arxiv-daily-push。仓库只保存源码、schema、配置示例、小 fixture、文本报告、Claim Ledger、RunRecord、日志索引和 SHA256；MP4、音频、模型权重、声音样本、渲染缓存、Codex auth、GitHub token、SMTP 密钥不得进入 Git。正式二进制产物通过 private GitHub Release 发布或等效的私有发布通道发布。

本系统通知方式为邮件，收件人为 linzezhang35@gmail.com。所有正式 daily/weekly/monthly 成功、降级、失败、证据门禁阻断、Release 上传失败和 04:45 health check 失败都必须生成邮件通知或通知恢复任务。邮件发送器必须支持 dry-run；SMTP 密钥和 OAuth token 不得写入仓库或日志。

本地资源必须低占用运行：Phase 1-6 不下载 TTS 模型，不生成视频，不保留大媒体。任何正式运行前必须检查磁盘、内存、缓存、staging、Git untracked 大文件和 secrets。若磁盘不足、内存压力过高、模型缓存不可控或 Git 中出现大媒体/权重/声音样本，必须 fail closed，并邮件通知，不得继续生成。当前机器 Phase 0 审计显示 Node/npm/gh/ffmpeg/docker 不可用、磁盘约 25 GiB、8 GiB RAM，因此在后续明确授权前不得假设视频/TTS/GitHub automation 已可用。

不得使用 OpenAI Platform API，不得创建或请求付费 API key，不得静默切换到收费服务。Codex CLI 可使用本机 ChatGPT 登录态，但必须验证 codex exec 非交互执行、登录续期和失败关闭；若身份失效，停止发布并报告。不得读取、打印或提交 ~/.codex/auth.json。

严格按 Phase 1-11 顺序推进。任何时刻只执行一个 Phase、一个 Issue、一个目录范围、一个主要验收标准。每个阶段先只读分析和计划，列出将读取/修改的文件、测试命令、风险和回滚方案。未通过阶段门禁不得进入下一阶段。每个阶段结束必须输出：进度百分比、已完成、未完成、预计剩余迭代次数/时间/置信度、状态表、diff summary、测试结果、证据、剩余风险、回滚方法、下一阶段是否解锁和推荐下一步。

真实性是最高门禁：所有关键事实和数字必须进入 Claim Ledger，并定位到原始来源的页码、章节、表格、图或稳定 URL；必须区分论文直接结果、作者主张、系统推断、教学类比和不确定性。任何关键事实无法支持、元数据冲突、PDF 解析失败、许可证不清楚或视频新增未经核验结论时，必须失败关闭，不得发布。不得把 arXiv 预印本描述成已经同行评审，除非存在独立可核验证据。

完成条件不是“代码存在”，而是 Phase 11 的 30 天试运行标准全部通过：无重复发布、关键数字 100% 可追溯、失败不会生成误导内容、05:00 任务可补跑、文本失败/视频失败有清晰降级、私有 Release 正常、邮件通知稳定、周报/月报可重放、所有秘密未进入仓库、缓存和本地存储压力可控、恢复演练通过。达到条件后停止目标并输出最终移交包；若任何阶段被阻塞，停在该阶段并给出最小可执行修复路径，不得自行扩大范围。
```

