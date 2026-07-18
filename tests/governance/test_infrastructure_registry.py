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
  * dormant_resources (retired-but-still-existing cloud objects: the adp-origin DNS record, the `adp`
    Cloudflare Tunnel, the old adp-mirror worker) are tracked with a required shape AND an actionable
    disposition, and -- the load-bearing control -- a LIVE serving host may never be mislabeled dormant.
    _dormant_violations() is proven non-vacuous by three negative controls that must each fire.
"""
import copy
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "governance" / "infrastructure_registry.json"

# The three dormant cloud resources discovered on 2026-07-18 (verified: adp-origin resolves + HTTP 530,
# adp-mirror.workers.dev HTTP 200). If a future edit drops one, tracking silently regresses -- pin them.
EXPECTED_DORMANT_IDS = {"adp-origin-dns", "adp-tunnel", "adp-mirror-worker"}
DORMANT_REQUIRED_FIELDS = ("resource_id", "kind", "surface", "name", "verified_state", "disposition")
_HOST_RE = re.compile(r"[a-z0-9-]+\.linzezhang\.com|[a-z0-9-]+\.workers\.dev")


def _live_serving_hosts(reg):
    """Hosts of workloads marked live in workload_placement -- these must never appear as dormant."""
    hosts = set()
    for p in reg.get("workload_placement", []):
        if p.get("status") == "live" and p.get("url"):
            hosts.add(p["url"].split("//")[-1].split("/")[0])
    return hosts


def _dormant_violations(reg):
    """Return a list of invariant violations in dormant_resources ([] == clean). Factored out so the
    negative controls can prove it actually bites, not just that the real file happens to pass."""
    violations = []
    surface_ids = {s.get("surface_id") for s in reg.get("surfaces", [])}
    live_hosts = _live_serving_hosts(reg)
    for r in reg.get("dormant_resources", []):
        rid = r.get("resource_id", "<no-id>")
        for f in DORMANT_REQUIRED_FIELDS:
            if not r.get(f):
                violations.append("dormant '{}' missing required field '{}'".format(rid, f))
        if r.get("surface") and r["surface"] not in surface_ids:
            violations.append("dormant '{}' names unknown surface '{}'".format(rid, r.get("surface")))
        # LOAD-BEARING: a dormant record must not name a currently-live serving host (would mean the
        # live workload was mislabeled retired -- the exact confusion the registry exists to prevent).
        for host in _HOST_RE.findall(r.get("name", "")):
            if host in live_hosts:
                violations.append("dormant '{}' names LIVE serving host '{}'".format(rid, host))
    return violations

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

    def test_dormant_resources_tracked_and_well_formed(self):
        """The retired cloud objects are recorded, each with the required shape + an actionable
        disposition, and the real registry has zero dormant-invariant violations."""
        dormant = self.reg.get("dormant_resources", [])
        self.assertGreaterEqual(len(dormant), 1, "dormant_resources is empty -- known retired resources untracked")
        ids = {r.get("resource_id") for r in dormant}
        missing = EXPECTED_DORMANT_IDS - ids
        self.assertEqual(missing, set(),
                         "dormant_resources dropped known retired resource(s): {} -- tracking regressed".format(missing))
        self.assertEqual(_dormant_violations(self.reg), [],
                         "real registry has dormant-invariant violations: {}".format(_dormant_violations(self.reg)))

    def test_dormant_violation_check_is_not_vacuous(self):
        """Prove _dormant_violations() bites: a checker that passes everything is worthless. Three
        negative controls, each a realistic corruption, must each produce a violation."""
        # NC1 -- a dormant record with no disposition (recorded but not actionable = not really tracked).
        nc1 = copy.deepcopy(self.reg)
        nc1["dormant_resources"][0].pop("disposition", None)
        self.assertTrue(any("disposition" in v for v in _dormant_violations(nc1)),
                        "NC1 vacuous: dropping a dormant resource's disposition was not caught")
        # NC2 -- the LOAD-BEARING control: mislabel the live serving host adp.linzezhang.com as dormant.
        nc2 = copy.deepcopy(self.reg)
        nc2["dormant_resources"][0]["name"] = "adp.linzezhang.com"
        self.assertTrue(any("LIVE serving host" in v for v in _dormant_violations(nc2)),
                        "NC2 vacuous: a live serving host mislabeled dormant was not caught -- the guard is "
                        "not protecting against live/retired confusion, its whole purpose")
        # NC3 -- a dormant record pointing at a surface that does not exist (dangling, like the placement check).
        nc3 = copy.deepcopy(self.reg)
        nc3["dormant_resources"][0]["surface"] = "surface-that-does-not-exist"
        self.assertTrue(any("unknown surface" in v for v in _dormant_violations(nc3)),
                        "NC3 vacuous: a dormant resource on a nonexistent surface was not caught")


if __name__ == "__main__":
    unittest.main()
