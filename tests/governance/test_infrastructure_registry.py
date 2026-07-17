#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the unified infrastructure registry is well-formed, self-consistent, and secret-free.

`governance/infrastructure_registry.json` is the single 统一治理 entry point over every deployment
surface (Cloudflare, the OVH VPS, Coolify-on-that-VPS). Its whole value is being the one place that is
trustworthy: if a workload_placement points at a surface that doesn't exist, or -- far worse -- if
someone pastes an SSH private key or an API token into it, the registry becomes a liability instead of
a source of truth.

What it asserts, and why only these:
  * The file parses and carries its required shape (schema_version, surfaces, workload_placement,
    governance_rule, secrets_boundary). Non-vacuity: surfaces and placements are non-empty.
  * Every workload_placement.surface names a real surface_id -- no dangling placement.
  * NO SECRET MATERIAL is present. This is the load-bearing safety guard: the registry's own
    secrets_boundary says only non-secret facts (provider/region/specs/public IP/reference names) go
    in; this test makes that promise enforceable. It scans for PEM private-key blocks, ssh key
    material, inline credential values, and long token/hex runs -- while deliberately NOT tripping on
    the registry's PROSE about tokens/keys (it talks *about* the secrets boundary; that must stay).
  * The scanner itself is proven non-vacuous: it must catch a synthetic key. A safety scanner that
    can't catch a planted secret is the NC0 failure mode this project keeps hitting.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "governance" / "infrastructure_registry.json"

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "PEM private key block"),
    (re.compile(r"\bssh-(rsa|ed25519|dss)\s+AAAA[0-9A-Za-z+/]{20,}"), "ssh key material"),
    (re.compile(r"(?i)(password|passwd|api[_-]?key|secret[_-]?key)\s*[:=]\s*\S{8,}"), "inline credential value"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"), "bearer token"),
    (re.compile(r"[A-Za-z0-9+/=]{44,}"), "base64 token-like run (>=44 chars)"),
    (re.compile(r"\b[0-9a-fA-F]{64,}\b"), "hex key-like run (>=64 chars)"),
]


def _scan(text):
    return [label for pat, label in SECRET_PATTERNS if pat.search(text)]


class TestInfrastructureRegistry(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REGISTRY.is_file(), "unified infra registry missing: {}".format(REGISTRY))
        self.raw = REGISTRY.read_text(encoding="utf-8")
        self.reg = json.loads(self.raw)

    def test_registry_has_required_shape(self):
        for key in ("schema_version", "surfaces", "workload_placement", "governance_rule", "secrets_boundary"):
            self.assertIn(key, self.reg, "registry missing required top-level key: {}".format(key))
        self.assertGreaterEqual(len(self.reg["surfaces"]), 1, "no surfaces -- registry would be vacuous")
        self.assertGreaterEqual(len(self.reg["workload_placement"]), 1, "no placements -- registry would be vacuous")
        for s in self.reg["surfaces"]:
            for f in ("surface_id", "kind", "status"):
                self.assertIn(f, s, "surface missing '{}': {}".format(f, s.get("surface_id", s)))

    def test_workload_placements_reference_real_surfaces(self):
        surface_ids = {s["surface_id"] for s in self.reg["surfaces"]}
        dangling = [p for p in self.reg["workload_placement"] if p.get("surface") not in surface_ids]
        self.assertEqual(
            dangling, [],
            "workload_placement entries point at unknown surface(s): {}\nknown surfaces: {}".format(
                [p.get("workload") + "->" + str(p.get("surface")) for p in dangling], sorted(surface_ids)))

    def test_no_secret_material_in_registry(self):
        hits = _scan(self.raw)
        self.assertEqual(
            hits, [],
            "the infra registry appears to contain SECRET material ({}). The registry records only "
            "non-secret facts and reference names -- private keys, passwords, tokens, and secret VALUES "
            "must never enter it (see its own secrets_boundary).".format(hits))

    def test_the_secret_scanner_is_not_vacuous(self):
        """A safety scanner that cannot catch a planted secret is worthless. Prove it catches one.

        The synthetic secrets are assembled from fragments at runtime ON PURPOSE, so the trigger
        literals never appear in this source file -- otherwise the repo's own push-protection /
        secret-scanning would flag the test's fixtures (which is exactly what this scanner defends
        against, one layer down)."""
        header = "-----BEGIN " + "OPENSSH PRIVATE KEY" + "-----"
        planted_pem = header + "\n" + ("b3Blbn" + "A" * 44) + "\n-----END " + "OPENSSH PRIVATE KEY" + "-----"
        self.assertTrue(_scan(planted_pem), "secret scanner failed to flag a synthetic private key -- it is vacuous")
        inline = "api" + "_key" + "=" + ("z" * 40)
        self.assertTrue(_scan(inline), "secret scanner missed an inline api_key value")


if __name__ == "__main__":
    unittest.main()
