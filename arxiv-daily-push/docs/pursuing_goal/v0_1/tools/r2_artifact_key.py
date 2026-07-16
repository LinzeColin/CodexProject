#!/usr/bin/env python3
"""ADP V0.1 R2 RawArtifact key / hash / metadata / compression contract (ADP-S2-P01-T021).

Defines a stable, content-addressed object contract for immutable raw HTML/PDF/
attachments so that:
  - same bytes -> same sha256 -> same key (idempotent, no duplicate objects);
  - different source_id or content_version -> different key (no cross-overwrite);
  - the object key contains NO secret/PII (no raw URL, query string, or token) --
    only source_id, a content_version tag, and the content sha256.

This module is a spec + helper; it performs NO network or R2 I/O.

key layout:
  raw/{source_id}/{content_version}/{sha256[:2]}/{sha256[2:4]}/{sha256}{ext}

Usage (self-test):
  python3 r2_artifact_key.py --selftest
"""
import argparse, hashlib, json, re, sys

# compress text-like artifacts; never re-compress already-compressed binaries
COMPRESS_MIME_PREFIXES = ("text/", "application/xml", "application/json", "application/xhtml")
NO_COMPRESS_MIME = ("application/pdf", "image/", "application/zip", "application/gzip", "application/octet-stream")
EXT_BY_MIME = {"text/html": ".html", "application/xhtml+xml": ".html", "application/pdf": ".pdf",
               "application/xml": ".xml", "text/xml": ".xml", "application/json": ".json",
               "text/plain": ".txt"}
SECRET_PII_IN_KEY = re.compile(r"(?i)(token|apikey|api_key|password|secret|sessionid|[?&](q|key|token)=|@|%40)")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sniff_mime(content_bytes, declared_mime=None):
    if declared_mime:
        return declared_mime.split(";")[0].strip().lower()
    head = content_bytes[:512].lstrip()
    if head[:5].lower() == b"%pdf-":
        return "application/pdf"
    if head[:1] == b"<":
        return "text/html"
    if head[:1] in (b"{", b"["):
        return "application/json"
    return "application/octet-stream"


def should_compress(mime):
    if any(mime.startswith(p) for p in NO_COMPRESS_MIME):
        return False
    return any(mime.startswith(p) for p in COMPRESS_MIME_PREFIXES)


def ext_for(mime):
    return EXT_BY_MIME.get(mime, "")


def object_key(source_id, content_bytes, content_version="v1", declared_mime=None):
    if not re.match(r"^[a-z0-9][a-z0-9_-]*$", source_id or ""):
        raise ValueError(f"invalid source_id (must be slug): {source_id!r}")
    sha = sha256_bytes(content_bytes)
    mime = sniff_mime(content_bytes, declared_mime)
    ext = ext_for(mime)
    key = f"raw/{source_id}/{content_version}/{sha[:2]}/{sha[2:4]}/{sha}{ext}"
    if SECRET_PII_IN_KEY.search(key):
        raise ValueError("object key would contain secret/PII")
    return key, sha, mime


def artifact_metadata(source_id, url, content_bytes, content_version="v1", declared_mime=None, fetched_at=None):
    key, sha, mime = object_key(source_id, content_bytes, content_version, declared_mime)
    return {
        "object_key": key,
        "sha256": sha,
        "mime": mime,
        "content_length": len(content_bytes),
        "compressed": should_compress(mime),
        "compression": "gzip" if should_compress(mime) else "none",
        "source_id": source_id,
        "content_version": content_version,
        "url": url,               # stored as METADATA, never in the key
        "fetched_at": fetched_at, # caller-supplied ISO timestamp
        "immutable": True,
    }


def _selftest():
    ok = True
    a = b"<html>hello world</html>"
    b = b"<html>hello world</html>"
    c = b"<html>different</html>"
    ka, sa, _ = object_key("arxiv-all", a)
    kb, sb, _ = object_key("arxiv-all", b)
    kc, sc, _ = object_key("arxiv-all", c)
    print("same bytes -> same key/hash:", ka == kb and sa == sb); ok &= (ka == kb and sa == sb)
    print("different bytes -> different key:", ka != kc); ok &= (ka != kc)
    # different source -> different key even for same bytes
    ka2, _, _ = object_key("nature", a)
    print("different source -> different key (same bytes):", ka != ka2); ok &= (ka != ka2)
    # different content_version -> different key
    kav2, _, _ = object_key("arxiv-all", a, content_version="v2")
    print("different version -> different key:", ka != kav2); ok &= (ka != kav2)
    # no secret/PII in key: a URL with a token must not leak (url is metadata only)
    m = artifact_metadata("arxiv-all", "https://x.org/p?token=SECRET123", a, fetched_at="2026-07-16T00:00:00Z")
    leaked = bool(SECRET_PII_IN_KEY.search(m["object_key"]))
    print("object key has no secret/PII (token stays in metadata url only):", not leaked); ok &= (not leaked)
    # mime + compression policy
    pdf = b"%PDF-1.7\n..."
    mpdf = artifact_metadata("nature", "https://x", pdf)
    print("pdf -> mime application/pdf, not compressed:", mpdf["mime"] == "application/pdf" and not mpdf["compressed"])
    ok &= (mpdf["mime"] == "application/pdf" and not mpdf["compressed"])
    mhtml = artifact_metadata("arxiv-all", "https://x", a)
    print("html -> compressed gzip:", mhtml["mime"] == "text/html" and mhtml["compressed"])
    ok &= (mhtml["mime"] == "text/html" and mhtml["compressed"])
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(_selftest())
    ap.print_help()


if __name__ == "__main__":
    main()
