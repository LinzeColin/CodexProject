from __future__ import annotations

import os
import unittest
import zipfile
from io import BytesIO

import source_registry.attachment_parser as attachment_parser
from source_registry.attachment_parser import AttachmentText, extract_attachment_text


class AttachmentParserTest(unittest.TestCase):
    def test_docx_text_is_extracted(self) -> None:
        body = _zip_bytes(
            {
                "word/document.xml": """
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:body>
                    <w:p><w:r><w:t>人工智能政策文件</w:t></w:r></w:p>
                    <w:p><w:r><w:t>推进算力和工业软件发展。</w:t></w:r></w:p>
                  </w:body>
                </w:document>
                """,
            }
        )
        parsed = extract_attachment_text("https://example.gov.cn/policy.docx", "", body)
        self.assertEqual(parsed.status, "parsed")
        self.assertIn("人工智能政策文件", parsed.text)
        self.assertIn("工业软件", parsed.text)

    def test_docx_headers_footers_and_comments_are_extracted(self) -> None:
        body = _zip_bytes(
            {
                "word/document.xml": """
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:body><w:p><w:r><w:t>正文条款</w:t></w:r></w:p></w:body>
                </w:document>
                """,
                "word/header1.xml": """
                <w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:p><w:r><w:t>广东省政策附件页眉</w:t></w:r></w:p>
                </w:hdr>
                """,
                "word/footer1.xml": """
                <w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:p><w:r><w:t>附件页脚说明</w:t></w:r></w:p>
                </w:ftr>
                """,
                "word/comments.xml": """
                <w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                  <w:comment><w:p><w:r><w:t>征求意见批注</w:t></w:r></w:p></w:comment>
                </w:comments>
                """,
            }
        )
        parsed = extract_attachment_text("https://example.gov.cn/policy.docx", "", body)
        self.assertEqual(parsed.status, "parsed")
        self.assertIn("正文条款", parsed.text)
        self.assertIn("政策附件页眉", parsed.text)
        self.assertIn("附件页脚说明", parsed.text)
        self.assertIn("征求意见批注", parsed.text)

    def test_xlsx_text_is_extracted(self) -> None:
        body = _zip_bytes(
            {
                "xl/workbook.xml": """
                <workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                  <sheets><sheet name="产业项目清单" sheetId="1"/></sheets>
                </workbook>
                """,
                "xl/sharedStrings.xml": """
                <sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                  <si><t>半导体</t></si>
                  <si><t>政策清单</t></si>
                </sst>
                """,
                "xl/worksheets/sheet1.xml": """
                <worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
                  <sheetData>
                    <row>
                      <c t="s"><v>0</v></c>
                      <c t="s"><v>1</v></c>
                    </row>
                  </sheetData>
                </worksheet>
                """,
            }
        )
        parsed = extract_attachment_text("https://example.gov.cn/list.xlsx", "", body)
        self.assertEqual(parsed.status, "parsed")
        self.assertIn("产业项目清单", parsed.text)
        self.assertIn("半导体", parsed.text)
        self.assertIn("政策清单", parsed.text)

    def test_pptx_text_is_extracted(self) -> None:
        body = _zip_bytes(
            {
                "ppt/slides/slide1.xml": """
                <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                  <p:cSld><p:spTree><p:sp><p:txBody>
                    <a:p><a:r><a:t>机器人产业政策解读</a:t></a:r></a:p>
                  </p:txBody></p:sp></p:spTree></p:cSld>
                </p:sld>
                """,
                "ppt/slides/slide2.xml": """
                <p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                  <p:cSld><p:spTree><p:sp><p:txBody>
                    <a:p><a:r><a:t>财政补贴和应用场景</a:t></a:r></a:p>
                  </p:txBody></p:sp></p:spTree></p:cSld>
                </p:sld>
                """,
            }
        )
        parsed = extract_attachment_text(
            "https://example.gov.cn/slides.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            body,
        )
        self.assertEqual(parsed.status, "parsed")
        self.assertEqual(parsed.parser, "pptx")
        self.assertIn("Slide 1", parsed.text)
        self.assertIn("机器人产业政策解读", parsed.text)
        self.assertIn("财政补贴", parsed.text)

    def test_image_attachment_uses_optional_ocr(self) -> None:
        old_ocr = attachment_parser._ocr_image_bytes
        try:
            attachment_parser._ocr_image_bytes = lambda body, limit: AttachmentText(
                "图片公告 OCR 文本", "image_ocr", "ocr_parsed"
            )
            parsed = extract_attachment_text("https://example.gov.cn/notice.png", "image/png", b"image")
        finally:
            attachment_parser._ocr_image_bytes = old_ocr

        self.assertEqual(parsed.status, "ocr_parsed")
        self.assertEqual(parsed.parser, "image_ocr")
        self.assertIn("OCR 文本", parsed.text)

    def test_pdf_falls_back_to_ocr_when_text_layer_fails(self) -> None:
        old_pdf_ocr = attachment_parser._extract_pdf_ocr
        try:
            attachment_parser._extract_pdf_ocr = lambda body, limit: AttachmentText(
                "扫描 PDF OCR 文本", "pdf_ocr", "ocr_parsed"
            )
            parsed = extract_attachment_text("https://example.gov.cn/scanned.pdf", "application/pdf", b"not-a-pdf")
        finally:
            attachment_parser._extract_pdf_ocr = old_pdf_ocr

        self.assertEqual(parsed.status, "ocr_parsed")
        self.assertEqual(parsed.parser, "pdf_ocr")
        self.assertIn("扫描 PDF", parsed.text)

    def test_legacy_office_uses_tika_when_configured(self) -> None:
        calls = []
        old_urlopen = attachment_parser.urlopen
        old_url = os.environ.get("TIKA_SERVER_URL")
        old_timeout = os.environ.get("TIKA_REQUEST_TIMEOUT")
        try:
            os.environ["TIKA_SERVER_URL"] = "http://127.0.0.1:9998"
            os.environ["TIKA_REQUEST_TIMEOUT"] = "7"

            def fake_urlopen(request, timeout):
                calls.append((request, timeout))
                return _FakeTikaResponse("旧版 Word 政策附件\n支持半导体和人工智能。")

            attachment_parser.urlopen = fake_urlopen
            parsed = extract_attachment_text(
                "https://example.gov.cn/policy.doc",
                "application/msword",
                b"legacy-doc-bytes",
            )
        finally:
            attachment_parser.urlopen = old_urlopen
            _restore_env("TIKA_SERVER_URL", old_url)
            _restore_env("TIKA_REQUEST_TIMEOUT", old_timeout)

        self.assertEqual(parsed.status, "parsed")
        self.assertEqual(parsed.parser, "tika")
        self.assertIn("半导体", parsed.text)
        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(timeout, 7)
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(request.full_url, "http://127.0.0.1:9998/tika")
        self.assertEqual(request.headers["Content-type"], "application/msword")

    def test_legacy_office_records_tika_dependency_when_missing(self) -> None:
        old_url = os.environ.get("TIKA_SERVER_URL")
        try:
            os.environ.pop("TIKA_SERVER_URL", None)
            parsed = extract_attachment_text(
                "https://example.gov.cn/report.rtf",
                "application/rtf",
                b"rtf-body",
            )
        finally:
            _restore_env("TIKA_SERVER_URL", old_url)

        self.assertEqual(parsed.parser, "tika")
        self.assertEqual(parsed.status, "needs_dependency:tika_server:rtf")
        self.assertEqual(parsed.text, "")

    def test_pdf_uses_grobid_when_configured(self) -> None:
        calls = []
        old_urlopen = attachment_parser.urlopen
        old_url = os.environ.get("GROBID_SERVER_URL")
        old_timeout = os.environ.get("GROBID_REQUEST_TIMEOUT")
        try:
            os.environ["GROBID_SERVER_URL"] = "http://127.0.0.1:8070"
            os.environ["GROBID_REQUEST_TIMEOUT"] = "9"

            def fake_urlopen(request, timeout):
                calls.append((request, timeout))
                return _FakeTikaResponse(
                    """
                    <TEI xmlns="http://www.tei-c.org/ns/1.0">
                      <teiHeader><fileDesc><titleStmt><title>AI Policy Research Report</title></titleStmt></fileDesc></teiHeader>
                      <text>
                        <body>
                          <div><head>产业影响</head><p>人工智能政策影响算力和机器人产业。</p></div>
                        </body>
                        <back>
                          <listBibl><biblStruct><analytic><title>参考研究一</title></analytic></biblStruct></listBibl>
                        </back>
                      </text>
                      <sourceDesc><biblStruct><analytic><author><persName>张三</persName></author></analytic></biblStruct></sourceDesc>
                    </TEI>
                    """
                )

            attachment_parser.urlopen = fake_urlopen
            parsed = extract_attachment_text("https://example.org/research.pdf", "application/pdf", b"%PDF")
        finally:
            attachment_parser.urlopen = old_urlopen
            _restore_env("GROBID_SERVER_URL", old_url)
            _restore_env("GROBID_REQUEST_TIMEOUT", old_timeout)

        self.assertEqual(parsed.status, "parsed")
        self.assertEqual(parsed.parser, "grobid")
        self.assertIn("Title: AI Policy Research Report", parsed.text)
        self.assertIn("Authors: 张三", parsed.text)
        self.assertIn("Section 1", parsed.text)
        self.assertIn("Reference 1", parsed.text)
        self.assertEqual(len(calls), 1)
        request, timeout = calls[0]
        self.assertEqual(timeout, 9)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.full_url, "http://127.0.0.1:8070/api/processFulltextDocument")
        self.assertIn("multipart/form-data", request.headers["Content-type"])

    def test_pdf_falls_back_when_grobid_fails(self) -> None:
        old_urlopen = attachment_parser.urlopen
        old_pdf_ocr = attachment_parser._extract_pdf_ocr
        old_url = os.environ.get("GROBID_SERVER_URL")
        try:
            os.environ["GROBID_SERVER_URL"] = "http://127.0.0.1:8070"

            def fake_urlopen(request, timeout):
                raise RuntimeError("grobid unavailable")

            attachment_parser.urlopen = fake_urlopen
            attachment_parser._extract_pdf_ocr = lambda body, limit: AttachmentText(
                "GROBID 失败后的扫描 PDF OCR 文本", "pdf_ocr", "ocr_parsed"
            )
            parsed = extract_attachment_text("https://example.org/research.pdf", "application/pdf", b"not-a-pdf")
        finally:
            attachment_parser.urlopen = old_urlopen
            attachment_parser._extract_pdf_ocr = old_pdf_ocr
            _restore_env("GROBID_SERVER_URL", old_url)

        self.assertEqual(parsed.status, "ocr_parsed_after_grobid_failure:RuntimeError")
        self.assertEqual(parsed.parser, "pdf_ocr")
        self.assertIn("GROBID 失败", parsed.text)


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buf.getvalue()


class _FakeHeaders:
    def get_content_charset(self):
        return "utf-8"


class _FakeTikaResponse:
    headers = _FakeHeaders()

    def __init__(self, text: str) -> None:
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._text.encode("utf-8")


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
