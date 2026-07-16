# Known gaps · ADP-S4-P03-T049（省级政府门户通用 Adapter Family, A1）

目标：**用少量模板族覆盖 A1**，而非为每省复制业务代码。以下是诚实边界。

1. **3 省级站点 / 2 模板族**：验证通过的是 3 个真实省级门户（江苏、山东、北京），跨 **2 个模板族**——`art-cms`（江苏+山东，同 CMS，URL `/art/Y/M/D/art_col_id.html`，标题钩子 `strip_leading_labels`）与 `beijing-zhengce`（北京，URL `./YYYYMM/tYYYYMMDD_id.html`，标题钩子 `before_underscore`）。**江苏与山东共用 art-cms 族正是本任务的要点**（少模板族覆盖多省）——若强行为每省一族则违背「用少量模板族覆盖」的目标。要求 3 个**独立族**会与目标矛盾；这里以「3 站点 + 2 族 + profile 承载全部差异 + 类体零省份字面量」证明 family 抽象成立而非 3 个一次性适配器。

2. **server-rendered 门户范围**：本 family 用 stdlib urllib（服务端抓取）。多数其他省级门户（广东/浙江/湖南等）从服务器环境**TLS 握手被拒或列表 JS 渲染**，stdlib 抓不到——需 headless-browser fetcher（另一能力，非 adapter family 职责）。已验证的 3 个是可靠 server-rendered 的。JS/TLS 门户随 headless fetcher 增强后接入（未来工作）。

3. **A1 身份证据来自 profile 的 curated 断言**：省级门户文章页无内联 主办单位/网站标识码（JS 加载页脚）。profile 声明 `gov_directory_listed=True`（curated：该域名确为官方省政府门户），`verify_identity` 据「官方 .gov.cn 域 + directory marker + 非中央」判 A1。诚实：这些确是官方省政府门户，域名可核。

4. **NOT_DEPLOYED**：adapter family + profiles + fixtures，**未接 worker/生产**。fixtures 从 dev-env 实抓（0 云成本）。live build 仍 b189d3cc0703（==T040），六主题/MVP 不变。省级分批回填是 T050（本 family 的下游执行）。

5. **正文抽取**：normalize 目前落 title/docnum/date/attachments/identity（结构化字段）；body_text 留空（省级正文正文抽取按 T034 模式后续按 profile 增，或复用 factsheet 管线）。本任务交付 adapter family 骨架 + profiles + override hooks + fixtures，符合 deliverables 定义。
