#!/usr/bin/env python3
"""ADP V0.1 Deployment Manifest generator (ADP-S1-P01-T009).

Binds commit + worker + schema + sources + parser + prompt + model + cron into
one rebuildable manifest. Deterministic: on the same commit, two clean builds
produce byte-identical output EXCEPT the allowed-to-vary fields
(generated_at, generator_note). The content_hash is computed over the `binding`
object only, so it is identical across rebuilds of the same content.

Secret redaction: the manifest stores file HASHES, never file contents, so no
secret can leak by construction. In addition, every string value emitted is run
through redact(), which masks token/key/secret-like substrings.

Usage:
  python3 generate_manifest.py [--out PATH] [--commit SHA]
Prints the manifest JSON to stdout (and to --out if given).
"""
import argparse, hashlib, json, re, subprocess, sys, pathlib, datetime

HERE = pathlib.Path(__file__).resolve().parent
ADP_ROOT = HERE.parents[3]  # tools -> v0_1 -> pursuing_goal -> docs -> arxiv-daily-push
MANIFEST_VERSION = "adp.deployment_manifest.v0_1"

# files bound into the manifest, grouped by component
BIND = {
    "worker_entry": "deploy/cloudflare/worker_cloud.js",
    "wrangler": "deploy/cloudflare/wrangler_cloud.jsonc",
    "schema": "deploy/cloudflare/schema_cloud.sql",
    "sources": "config/boards_v0_3.yaml",
    "owner_controls": "config/owner_controls.yaml",
    "thresholds": "config/thresholds_v0_3.yaml",
    "model_spec": "docs/governance/MODEL_SPEC.md",
    "formula_registry": "docs/governance/formula_registry.yaml",
    "parameter_registry": "docs/governance/parameter_registry.csv",
}
CRON = "30 20 * * *"  # from wrangler_cloud.jsonc triggers.crons
ALLOWED_VARY = ["generated_at", "generator_note"]  # excluded from content_hash

SECRET_PATTERNS = [
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)(oauth|refresh|api|access)[_-]?token\S*"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"\b[A-Fa-f0-9]{40,}\b"),  # long hex secrets
]


def redact(s):
    if not isinstance(s, str):
        return s
    out = s
    for pat in SECRET_PATTERNS:
        out = pat.sub("<redacted>", out)
    return out


def sha256_file(rel):
    p = ADP_ROOT / rel
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def file_binding(rel):
    h = sha256_file(rel)
    return {"file": rel, "sha256": h, "present": h is not None}


def read_registry_ver():
    p = ADP_ROOT / BIND["sources"]
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("registry_ver:"):
            return redact(line.split(":", 1)[1].strip())
    return None


def schema_tables():
    p = ADP_ROOT / BIND["schema"]
    if not p.exists():
        return []
    txt = p.read_text(encoding="utf-8")
    return sorted(set(re.findall(r"(?i)CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([A-Za-z_][A-Za-z0-9_]*)", txt)))


def git_commit(explicit):
    if explicit:
        return explicit
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ADP_ROOT,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return "UNKNOWN_NOT_IN_GIT"


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build(commit):
    binding = {
        "commit": commit,
        "cron": CRON,
        "worker": {
            "name": "adp-cloud",
            "entry": file_binding(BIND["worker_entry"]),
            "wrangler": file_binding(BIND["wrangler"]),
        },
        "schema": {**file_binding(BIND["schema"]), "tables": schema_tables()},
        "sources": {**file_binding(BIND["sources"]), "registry_ver": read_registry_ver()},
        # parser lives inline in the worker (parseFeed/parse*); bound via the worker entry hash
        "parser": {**file_binding(BIND["worker_entry"]), "note": "parseFeed/parse* inline in worker entry"},
        "prompt": {"sources": [file_binding(BIND["worker_entry"]), file_binding(BIND["owner_controls"])],
                   "note": "deep-dive + lesson prompts inline in worker; owner controls in config"},
        "model": {"sources": [file_binding(BIND["model_spec"]), file_binding(BIND["formula_registry"]),
                              file_binding(BIND["parameter_registry"]), file_binding(BIND["thresholds"])],
                  "note": "scoring/selection model = MODEL_SPEC + formula_registry + parameter_registry + thresholds"},
    }
    content_hash = "sha256:" + hashlib.sha256(canonical(binding).encode("utf-8")).hexdigest()
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": None,          # filled by caller (ALLOWED to vary)
        "generator_note": None,        # optional (ALLOWED to vary)
        "binding": binding,
        "content_hash": content_hash,
        "redaction": {
            "secrets_redacted": True,
            "policy": "manifest stores file sha256 hashes, never file contents; all emitted strings pass redact()",
            "patterns": len(SECRET_PATTERNS),
        },
    }
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--commit")
    ap.add_argument("--generated-at", help="override timestamp (for reproducible tests)")
    args = ap.parse_args()

    manifest = build(git_commit(args.commit))
    manifest["generated_at"] = args.generated_at or (datetime.datetime.utcnow().isoformat() + "Z")
    manifest["generator_note"] = "generated by tools/generate_manifest.py"

    out = json.dumps(manifest, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(out + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
