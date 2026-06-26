from __future__ import annotations

import os
import re
import secrets
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree


@dataclass(frozen=True)
class AttachmentText:
    text: str
    parser: str
    status: str


def extract_attachment_text(url: str, content_type: str, body: bytes, limit: int = 6000) -> AttachmentText:
    kind = _attachment_kind(url, content_type)
    if kind == "pdf":
        return _extract_pdf(body, limit)
    if kind == "docx":
        return _extract_docx(body, limit)
    if kind == "xlsx":
        return _extract_xlsx(body, limit)
    if kind == "pptx":
        return _extract_pptx(body, limit)
    if kind == "image":
        return _extract_image_ocr(body, limit)
    if kind in {"doc", "xls", "ppt", "rtf", "odt", "ods", "epub"}:
        return _extract_tika(body, content_type, limit, kind)
    return AttachmentText("", "none", f"unsupported_attachment:{kind or 'unknown'}")


def _attachment_kind(url: str, content_type: str) -> str:
    path = urlsplit(url).path.lower()
    lowered_type = (content_type or "").lower()
    if path.endswith(".pdf") or "pdf" in lowered_type:
        return "pdf"
    if path.endswith(".docx") or "wordprocessingml" in lowered_type:
        return "docx"
    if path.endswith(".xlsx") or "spreadsheetml" in lowered_type:
        return "xlsx"
    if path.endswith(".pptx") or "presentationml" in lowered_type:
        return "pptx"
    if path.endswith(".doc") or "application/msword" in lowered_type:
        return "doc"
    if path.endswith(".xls") or "application/vnd.ms-excel" in lowered_type:
        return "xls"
    if path.endswith(".ppt") or "application/vnd.ms-powerpoint" in lowered_type:
        return "ppt"
    if path.endswith(".rtf") or "application/rtf" in lowered_type or "text/rtf" in lowered_type:
        return "rtf"
    if path.endswith(".odt") or "opendocument.text" in lowered_type:
        return "odt"
    if path.endswith(".ods") or "opendocument.spreadsheet" in lowered_type:
        return "ods"
    if path.endswith(".epub") or "application/epub+zip" in lowered_type:
        return "epub"
    if path.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")):
        return "image"
    if any(token in lowered_type for token in ("image/png", "image/jpeg", "image/tiff", "image/bmp", "image/webp")):
        return "image"
    return ""


def _extract_pdf(body: bytes, limit: int) -> AttachmentText:
    grobid_status = ""
    if _grobid_enabled():
        grobid = _extract_grobid_pdf(body, limit)
        if grobid.text:
            return grobid
        grobid_status = grobid.status
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(body))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        cleaned = _compact(text)[:limit]
        if not cleaned:
            ocr = _extract_pdf_ocr(body, limit)
            if ocr.text or ocr.status.startswith("ocr_"):
                return _with_grobid_fallback_status(ocr, grobid_status)
        return _with_grobid_fallback_status(
            AttachmentText(cleaned, "pypdf", "parsed" if cleaned else "empty_pdf_text"),
            grobid_status,
        )
    except Exception:
        pass
    try:
        import fitz

        with fitz.open(stream=body, filetype="pdf") as doc:
            text = "\n".join(page.get_text("text") for page in doc)
        cleaned = _compact(text)[:limit]
        if not cleaned:
            ocr = _extract_pdf_ocr(body, limit)
            if ocr.text or ocr.status.startswith("ocr_"):
                return _with_grobid_fallback_status(ocr, grobid_status)
        return _with_grobid_fallback_status(
            AttachmentText(cleaned, "pymupdf", "parsed" if cleaned else "empty_pdf_text"),
            grobid_status,
        )
    except Exception as exc:
        ocr = _extract_pdf_ocr(body, limit)
        if ocr.text or ocr.status.startswith("ocr_"):
            return _with_grobid_fallback_status(ocr, grobid_status)
        return AttachmentText("", "pdf", f"parse_failed:pdf:{type(exc).__name__}")


def _extract_pdf_ocr(body: bytes, limit: int) -> AttachmentText:
    try:
        import fitz
    except Exception:
        return AttachmentText("", "pdf_ocr", "ocr_unavailable:missing_dependency:pymupdf")
    try:
        parts: list[str] = []
        with fitz.open(stream=body, filetype="pdf") as doc:
            for index in range(min(3, doc.page_count)):
                page = doc.load_page(index)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image_bytes = pixmap.tobytes("png")
                parsed = _ocr_image_bytes(image_bytes, limit)
                if parsed.text:
                    parts.append(parsed.text)
                if len(" ".join(parts)) >= limit:
                    break
        cleaned = _compact(" ".join(parts))[:limit]
        return AttachmentText(cleaned, "pdf_ocr", "ocr_parsed" if cleaned else "ocr_empty")
    except Exception as exc:
        return AttachmentText("", "pdf_ocr", f"ocr_failed:pdf:{type(exc).__name__}")


def _extract_image_ocr(body: bytes, limit: int) -> AttachmentText:
    return _ocr_image_bytes(body, limit)


def _extract_tika(body: bytes, content_type: str, limit: int, kind: str) -> AttachmentText:
    base_url = (os.environ.get("TIKA_SERVER_URL") or "").strip()
    if not base_url:
        return AttachmentText("", "tika", f"needs_dependency:tika_server:{kind}")
    endpoint = base_url.rstrip("/") + "/tika"
    timeout = _env_int("TIKA_REQUEST_TIMEOUT", default=20, minimum=1, maximum=120)
    request = Request(
        endpoint,
        data=body,
        headers={
            "Accept": "text/plain",
            "Content-Type": content_type or "application/octet-stream",
        },
        method="PUT",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            response_type = response.headers.get_content_charset() if response.headers else None
        text = raw.decode(response_type or "utf-8", errors="replace")
        cleaned = _compact(text)[:limit]
        return AttachmentText(cleaned, "tika", "parsed" if cleaned else "empty_tika_text")
    except Exception as exc:
        return AttachmentText("", "tika", f"parse_failed:tika:{type(exc).__name__}")


def _extract_grobid_pdf(body: bytes, limit: int) -> AttachmentText:
    base_url = (os.environ.get("GROBID_SERVER_URL") or "").strip()
    if not base_url:
        return AttachmentText("", "grobid", "needs_dependency:grobid_server")
    endpoint = base_url.rstrip("/") + "/api/processFulltextDocument"
    timeout = _env_int("GROBID_REQUEST_TIMEOUT", default=45, minimum=1, maximum=180)
    boundary = f"codex-grobid-{secrets.token_hex(8)}"
    payload = _multipart_file_body(boundary, "input.pdf", "application/pdf", body)
    request = Request(
        endpoint,
        data=payload,
        headers={
            "Accept": "application/xml",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
        text = _grobid_tei_text(raw, limit)
        return AttachmentText(text, "grobid", "parsed" if text else "empty_grobid_text")
    except Exception as exc:
        return AttachmentText("", "grobid", f"parse_failed:grobid:{type(exc).__name__}")


def _with_grobid_fallback_status(result: AttachmentText, grobid_status: str) -> AttachmentText:
    if result.text and grobid_status.startswith("parse_failed:grobid:"):
        reason = grobid_status.rsplit(":", 1)[-1]
        return AttachmentText(result.text, result.parser, f"{result.status}_after_grobid_failure:{reason}")
    return result


def _grobid_enabled() -> bool:
    if not (os.environ.get("GROBID_SERVER_URL") or "").strip():
        return False
    value = (os.environ.get("GROBID_AUTO_PDF") or "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _multipart_file_body(boundary: str, filename: str, content_type: str, body: bytes) -> bytes:
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="input"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return header + body + footer


def _grobid_tei_text(xml: bytes, limit: int) -> str:
    root = ElementTree.fromstring(xml)
    title = _first_tei_text(root, "title")
    authors = _tei_authors(root)[:8]
    sections = _tei_sections(root)[:12]
    references = _tei_references(root)[:12]
    parts: list[str] = []
    if title:
        parts.append(f"Title: {title}")
    if authors:
        parts.append(f"Authors: {', '.join(authors)}")
    for index, section in enumerate(sections, start=1):
        parts.append(f"Section {index}: {section}")
    for index, reference in enumerate(references, start=1):
        parts.append(f"Reference {index}: {reference}")
    return _compact(" ".join(parts))[:limit]


def _first_tei_text(root: ElementTree.Element, tag: str) -> str:
    for node in root.iter():
        if _local_name(node.tag) == tag:
            text = _compact(" ".join(_iter_text(node)))
            if text:
                return text
    return ""


def _tei_authors(root: ElementTree.Element) -> list[str]:
    authors: list[str] = []
    for node in root.iter():
        if _local_name(node.tag) != "author":
            continue
        text = _compact(" ".join(_iter_text(node)))
        if text:
            authors.append(text)
    return authors


def _tei_sections(root: ElementTree.Element) -> list[str]:
    sections: list[str] = []
    for node in root.iter():
        if _local_name(node.tag) != "div":
            continue
        parts: list[str] = []
        for child in node:
            name = _local_name(child.tag)
            if name in {"head", "p"}:
                text = _compact(" ".join(_iter_text(child)))
                if text:
                    parts.append(text)
            if len(" ".join(parts)) > 900:
                break
        text = _compact(" ".join(parts))
        if text:
            sections.append(text[:900])
    return sections


def _tei_references(root: ElementTree.Element) -> list[str]:
    references: list[str] = []
    for node in root.iter():
        if _local_name(node.tag) not in {"biblStruct", "bibl", "listBibl"}:
            continue
        text = _compact(" ".join(_iter_text(node)))
        if text:
            references.append(text[:700])
    return references


def _env_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def _ocr_image_bytes(body: bytes, limit: int) -> AttachmentText:
    try:
        from PIL import Image
    except Exception:
        return AttachmentText("", "image_ocr", "ocr_unavailable:missing_dependency:pillow")
    try:
        import pytesseract
    except Exception:
        return AttachmentText("", "image_ocr", "ocr_unavailable:missing_dependency:pytesseract")
    try:
        with Image.open(BytesIO(body)) as image:
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        cleaned = _compact(text)[:limit]
        return AttachmentText(cleaned, "image_ocr", "ocr_parsed" if cleaned else "ocr_empty")
    except Exception as exc:
        return AttachmentText("", "image_ocr", f"ocr_failed:image:{type(exc).__name__}")


def _extract_docx(body: bytes, limit: int) -> AttachmentText:
    try:
        with zipfile.ZipFile(BytesIO(body)) as archive:
            parts = []
            for name in _docx_part_names(archive):
                try:
                    parts.append(_xml_text(archive.read(name), tags={"t", "tab", "br", "p"}))
                except KeyError:
                    continue
        text = " ".join(parts)
        cleaned = _compact(text)[:limit]
        return AttachmentText(cleaned, "docx", "parsed" if cleaned else "empty_docx_text")
    except Exception as exc:
        return AttachmentText("", "docx", f"parse_failed:docx:{type(exc).__name__}")


def _extract_xlsx(body: bytes, limit: int) -> AttachmentText:
    try:
        with zipfile.ZipFile(BytesIO(body)) as archive:
            shared = _shared_strings(archive)
            workbook_names = _workbook_sheet_names(archive)
            sheet_names = sorted(
                name
                for name in archive.namelist()
                if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
            )
            parts: list[str] = []
            for index, name in enumerate(sheet_names[:8]):
                if index < len(workbook_names):
                    parts.append(workbook_names[index])
                parts.extend(_sheet_text(archive.read(name), shared))
        cleaned = _compact(" ".join(parts))[:limit]
        return AttachmentText(cleaned, "xlsx", "parsed" if cleaned else "empty_xlsx_text")
    except Exception as exc:
        return AttachmentText("", "xlsx", f"parse_failed:xlsx:{type(exc).__name__}")


def _extract_pptx(body: bytes, limit: int) -> AttachmentText:
    try:
        with zipfile.ZipFile(BytesIO(body)) as archive:
            slide_names = sorted(
                name
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            parts = []
            for index, name in enumerate(slide_names[:80], start=1):
                text = _xml_text(archive.read(name), tags={"t", "br", "p"})
                if text:
                    parts.append(f"Slide {index}: {text}")
        cleaned = _compact(" ".join(parts))[:limit]
        return AttachmentText(cleaned, "pptx", "parsed" if cleaned else "empty_pptx_text")
    except Exception as exc:
        return AttachmentText("", "pptx", f"parse_failed:pptx:{type(exc).__name__}")


def _docx_part_names(archive: zipfile.ZipFile) -> list[str]:
    names = ["word/document.xml"]
    extras = sorted(
        name
        for name in archive.namelist()
        if (
            name.startswith("word/header")
            or name.startswith("word/footer")
            or name in {"word/footnotes.xml", "word/endnotes.xml", "word/comments.xml"}
        )
        and name.endswith(".xml")
    )
    return names + extras


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        xml = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(xml)
    return [_compact(" ".join(_iter_text(node))) for node in root]


def _workbook_sheet_names(archive: zipfile.ZipFile) -> list[str]:
    try:
        xml = archive.read("xl/workbook.xml")
    except KeyError:
        return []
    root = ElementTree.fromstring(xml)
    names = []
    for node in root.iter():
        if _local_name(node.tag) == "sheet" and node.attrib.get("name"):
            names.append(str(node.attrib["name"]))
    return names


def _sheet_text(xml: bytes, shared: list[str]) -> list[str]:
    root = ElementTree.fromstring(xml)
    values: list[str] = []
    for cell in root.iter():
        if _local_name(cell.tag) != "c":
            continue
        cell_type = cell.attrib.get("t")
        value = ""
        for child in cell:
            if _local_name(child.tag) == "v" and child.text:
                value = child.text
                break
            if _local_name(child.tag) == "is":
                value = " ".join(_iter_text(child))
                break
        if cell_type == "s" and value.isdigit():
            index = int(value)
            value = shared[index] if index < len(shared) else ""
        if value:
            values.append(value)
    return values


def _xml_text(xml: bytes, tags: set[str]) -> str:
    root = ElementTree.fromstring(xml)
    parts: list[str] = []
    for node in root.iter():
        name = _local_name(node.tag)
        if name == "tab":
            parts.append(" ")
        elif name in {"br", "p"}:
            parts.append("\n")
        elif name in tags and node.text:
            parts.append(node.text)
    return " ".join(parts)


def _iter_text(node) -> Iterable[str]:
    if node.text:
        yield node.text
    for child in node:
        yield from _iter_text(child)
        if child.tail:
            yield child.tail


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
