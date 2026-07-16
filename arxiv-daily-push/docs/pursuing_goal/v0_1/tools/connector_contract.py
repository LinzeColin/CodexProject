#!/usr/bin/env python3
"""ADP V0.1 connector fixture + contract-test harness (ADP-S3-P01-T032).

Freezes official-page snapshots as fixtures and compares a connector's parse against golden
expected JSON, so a government-site template change is caught in CI -- not silently mis-fetched
after go-live. Any field drift, lost attachment, or broken pagination fails the matching contract.

Includes a stdlib-only ReferenceOfficialConnector that parses a defined official-doc template
(class-anchored fields), so the same fixtures that exercise the real A0 adapters (T034+) already
have a working reference parser. Deterministic; no network. The harness reads local fixture bytes.
"""
from __future__ import annotations
import dataclasses, hashlib, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import official_connector as OC


def _find(pattern, text, group=1):
    m = re.search(pattern, text, re.S)
    return m.group(group).strip() if m else None


def _strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


class ReferenceOfficialConnector(OC.OfficialConnector):
    """Parses the defined official-doc template. Real A0 adapters (T034+) subclass/replace the
    selectors per site but keep this contract shape."""
    source_id = "reference-a0"
    authority_level = "A0"

    def __init__(self, fixtures_dir: pathlib.Path):
        self.dir = pathlib.Path(fixtures_dir)

    # -- capabilities --------------------------------------------------------------------
    def health(self):
        return OC.HealthResult(True, "reference fixtures", str(self.dir))

    def _read(self, name):
        return (self.dir / name).read_bytes()

    def fetch(self, url, fetched_at):
        body = self._read(url)               # url == fixture filename in the harness
        return OC.FetchResult(url, 200, "text/html", body, hashlib.sha256(body).hexdigest(), fetched_at, True)

    def discover(self, cursor):
        """Parse a paginated listing across all its pages into DiscoverItems."""
        items, page = [], "pagination.html"
        seen = set()
        while page and page not in seen:
            seen.add(page)
            html = self._read(page).decode("utf-8", "ignore")
            for m in re.finditer(r'<a class="doc-link" href="([^"]+)">(.*?)</a>\s*<span class="date">([^<]+)</span>', html, re.S):
                items.append(OC.DiscoverItem(m.group(1), _strip_tags(m.group(2)), m.group(3).strip()))
            nxt = _find(r'<a class="next" href="([^"]+)">', html)
            page = (nxt.replace("?", "").replace("page=", "pagination_p") + ".html") if nxt else None
        return items

    def verify(self, item, fetched):
        official = True  # fixtures are official by construction; real verify is T033
        return OC.VerifyResult(official, "A0", official, ("fixture official",))

    def normalize(self, item, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        title = _strip_tags(_find(r'<h1 class="doc-title">(.*?)</h1>', html))
        return OC.NormalizedDoc(
            self.source_id, item.url if isinstance(item, OC.DiscoverItem) else item, title or "",
            _find(r'<span class="doc-number">([^<]+)</span>', html),
            _find(r'<span class="doc-date">([^<]+)</span>', html),
            _find(r'<span class="doc-status">([^<]+)</span>', html),
            "A0", _strip_tags(_find(r'<div class="doc-body">(.*?)</div>', html)) or "",
            attachments=tuple(self.attachments(fetched)),
            canonical_hint="ttl:" + hashlib.sha256((title or "").encode()).hexdigest()[:16])

    def attachments(self, fetched):
        html = fetched.body.decode("utf-8", "ignore")
        return [OC.Attachment(m.group(1), (m.group(1).rsplit(".", 1)[-1].lower() if "." in m.group(1) else "other"))
                for m in re.finditer(r'<a class="doc-att" href="([^"]+)">', html)]

    def cursor(self, docs):
        dates = [d.doc_date for d in docs if d.doc_date]
        return OC.Cursor(last_id=docs[-1].doc_id if docs else None, last_date=max(dates) if dates else None)


# --- contract harness ---------------------------------------------------------------------
def _doc_to_json(nd: OC.NormalizedDoc):
    return {"title": nd.title, "doc_number": nd.doc_number, "doc_date": nd.doc_date,
            "status": nd.status, "authority_level": nd.authority_level, "body_text": nd.body_text,
            "attachments": [{"url": a.url, "kind": a.kind} for a in nd.attachments]}


def check_doc(connector, fixture, expected, fetched_at="2026-07-17T00:00:00+10:00"):
    fr = connector.fetch(fixture, fetched_at)
    got = _doc_to_json(connector.normalize(OC.DiscoverItem(fixture, "", None), fr))
    diffs = [f"{k}: expected {expected.get(k)!r} got {got.get(k)!r}" for k in expected if got.get(k) != expected.get(k)]
    return {"fixture": fixture, "passed": not diffs, "diffs": diffs, "got": got}


def check_pagination(connector, expected_items):
    items = [{"url": i.url, "title": i.title, "hint_date": i.hint_date} for i in connector.discover(OC.Cursor())]
    passed = items == expected_items
    return {"fixture": "pagination.html", "passed": passed,
            "diffs": [] if passed else [f"discovered {len(items)} items != expected {len(expected_items)}"],
            "got": items}


def run_contract(fixtures_dir, expected_dir):
    fdir, edir = pathlib.Path(fixtures_dir), pathlib.Path(expected_dir)
    conn = ReferenceOfficialConnector(fdir)
    results = []
    for fx in ("normal.html", "attachment.html"):
        exp = json.loads((edir / fx.replace(".html", ".json")).read_text(encoding="utf-8"))
        results.append(check_doc(conn, fx, exp))
    exp_pg = json.loads((edir / "pagination.json").read_text(encoding="utf-8"))
    results.append(check_pagination(conn, exp_pg))
    return {"health": dataclasses.asdict(conn.health()), "results": results,
            "all_passed": all(r["passed"] for r in results)}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", required=True)
    ap.add_argument("--expected", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    rep = run_contract(args.fixtures, args.expected)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": rep["all_passed"],
                      "results": [{"fixture": r["fixture"], "passed": r["passed"], "diffs": r["diffs"]} for r in rep["results"]]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
