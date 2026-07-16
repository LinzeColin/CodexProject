# R2 RawArtifact 对象合同（ADP-S2-P01-T021）

> 为不可变原始 HTML/PDF/附件建立稳定对象合同。**本任务 NOT_DEPLOYED**：只定义合同（key/hash/mime/元数据/压缩），不写 R2、不需开 R2。
> 机器实现见 `tools/r2_artifact_key.py`；元数据 schema 见 `schemas/r2_raw_artifact.schema.json`。

## 1. 对象键（content-addressed，确定性）
```
raw/{source_id}/{content_version}/{sha256[:2]}/{sha256[2:4]}/{sha256}{ext}
```
- `source_id`：Registry 中的来源 slug（`^[a-z0-9][a-z0-9_-]*$`）。
- `content_version`：内容版本标签（默认 `v1`）。
- `sha256`：原始字节的 sha256（前 2/2 位做分片目录，控制单目录对象数）。
- `ext`：按 mime 推断（.html/.pdf/.xml/.json/.txt/空）。

## 2. 不可变与去重
- **同字节 → 同 sha256 → 同键**：幂等写入，不产生重复对象（T022 重试安全）。
- **不同 source_id 或 content_version → 不同键**：不同来源/版本不互相覆盖。
- 对象一经写入视为 immutable（不覆盖、不删改）。

## 3. Hash / mime / 元数据
- `sha256`：唯一内容指纹。
- `mime`：优先用响应声明，否则按字节头嗅探（%PDF→application/pdf、`<`→text/html、`{`/`[`→json）。
- 元数据（存 D1 artifact 行 + R2 对象元数据，见 schema）：object_key/sha256/mime/content_length/compression/source_id/content_version/url/fetched_at/immutable。

## 4. 压缩策略
- **压缩（gzip）**：text/*、application/xml、application/json、xhtml。
- **不压缩**：application/pdf、image/*、zip、gzip、octet-stream（已压缩或二进制）。

## 5. 安全（无 secret/PII 于路径）
- 键**只含** source_id + content_version + sha256（+ext）；**绝不含** URL、query string、token、邮箱等。
- 原始 URL 仅作**元数据** `url` 字段保存；键生成时若检出 secret/PII 模式则抛错拒绝。

## 6. 验收（tools/r2_artifact_key.py --selftest 全 PASS）
- 同字节同 hash/键；不同字节不同键；不同 source/version 不同键（不覆盖）；键无 secret/PII（token 留在元数据 url）；PDF 不压缩 / HTML gzip。
