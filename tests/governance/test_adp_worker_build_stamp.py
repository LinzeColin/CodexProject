#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the ADP worker's BUILD stamp must reproduce via its own self-excluding hash.

`worker_cloud.js` carries `const BUILD = { build_id, source_sha256, ... }` and serves it at
`/build.json`. The contract, stated in the file itself, is: reset both values to their zero
placeholders ('0'*12 and '0'*64), sha256 the whole file, and you get `source_sha256` back, with
`build_id` its first 12 hex chars. That makes the stamp a cryptographic statement of *which source
is running in production*.

Why this guard exists: NOTHING enforced it. Before this test, `source_sha256` appeared nowhere in
tests/ or .github/workflows/ — the contract was upheld only by whoever remembered to re-stamp.
Edit one constant and forget, and `/build.json` reports a source that is not the source; measured:

    edit `META_SCAN = 200` -> `201`, do not re-stamp
      stamped source_sha256 : ac7cf4800e18a217...
      actual  source_sha256 : ffb5d5b5634a237e...
      -> /build.json lies, and nothing goes red

That matters beyond tidiness. Every adversarial review of this worker uses the stamp to prove the
implementer did not change code after the reviewer signed off — six times in the ADP-V02-P08 review
alone. A verification mechanism nobody verifies is exactly the failure mode this project keeps
hitting: *a false premise written down and trusted*. So: make the stamp falsifiable, in CI, by a
test that fails the moment the file and its stamp disagree.

Scope: the deployed Cloudflare worker only. It is the one file whose hash is published as a claim.
"""
import hashlib
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKER = ROOT / "arxiv-daily-push" / "deploy" / "cloudflare" / "worker_cloud.js"
STAMP_RE = re.compile(r"build_id: '([0-9a-f]{12})', source_sha256: '([0-9a-f]{64})'")
ZERO_ID, ZERO_SHA = "0" * 12, "0" * 64


def _recompute(src: str, build_id: str, source_sha256: str) -> str:
    """The contract, implemented exactly as worker_cloud.js documents it."""
    zeroed = src.replace("build_id: '{}'".format(build_id), "build_id: '{}'".format(ZERO_ID))
    zeroed = zeroed.replace("source_sha256: '{}'".format(source_sha256), "source_sha256: '{}'".format(ZERO_SHA))
    return hashlib.sha256(zeroed.encode("utf-8")).hexdigest()


class TestAdpWorkerBuildStamp(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKER.is_file(), "the deployed worker is missing: {}".format(WORKER))
        self.src = WORKER.read_text(encoding="utf-8")
        m = STAMP_RE.search(self.src)
        self.assertIsNotNone(
            m,
            "worker_cloud.js has no `build_id: '<12 hex>', source_sha256: '<64 hex>'` stamp. Either the "
            "stamp was removed (then /build.json can no longer identify the running source) or its shape "
            "changed (then this guard is checking nothing and must be updated deliberately).")
        self.build_id, self.source_sha256 = m.group(1), m.group(2)

    def test_stamp_is_not_a_placeholder(self):
        """A file left at the zero placeholders would trivially satisfy nothing useful."""
        self.assertNotEqual(self.build_id, ZERO_ID, "build_id is still the zero placeholder -- never stamped")
        self.assertNotEqual(self.source_sha256, ZERO_SHA, "source_sha256 is still the zero placeholder -- never stamped")

    def test_self_excluding_hash_reproduces(self):
        actual = _recompute(self.src, self.build_id, self.source_sha256)
        self.assertEqual(
            actual, self.source_sha256,
            "worker_cloud.js was edited without re-stamping BUILD.\n"
            "  stamped source_sha256 : {}\n"
            "  actual  source_sha256 : {}\n"
            "/build.json therefore reports a source that is NOT the source now running, and every review "
            "that uses the stamp to prove 'no code changed after sign-off' is reasoning from a false premise.\n"
            "Fix: reset build_id to '{}' and source_sha256 to 64 zeros, sha256 the whole file, and write "
            "back sha256 as source_sha256 and its first 12 chars as build_id.".format(
                self.source_sha256[:24], actual[:24], ZERO_ID))

    def test_build_id_is_the_hash_prefix(self):
        """build_id is what the footer and /build.json show; it must be derived, not decorative."""
        self.assertEqual(
            self.build_id, self.source_sha256[:12],
            "build_id {} is not the first 12 chars of source_sha256 {} -- the short id shown in the UI "
            "does not identify the hashed source.".format(self.build_id, self.source_sha256[:12]))

    def test_guard_would_catch_an_unstamped_edit(self):
        """Load-bearing check: prove this guard can actually fail.

        A guard that cannot fail is decoration -- the exact defect this repo keeps shipping. Tamper with
        an in-memory copy and assert the contract rejects it."""
        tampered = self.src.replace("const KEEP_PER_BOARD", "const KEEP_PER_BOARD_X", 1)
        self.assertNotEqual(tampered, self.src, "could not construct a tampered copy -- anchor missing")
        self.assertNotEqual(
            _recompute(tampered, self.build_id, self.source_sha256), self.source_sha256,
            "an edited worker still reproduces the stamp -- the hash is not covering the file content, "
            "so this guard proves nothing")


if __name__ == "__main__":
    unittest.main()
