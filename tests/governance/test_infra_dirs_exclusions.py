#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: documentation/skeleton top-level dirs are excluded from project discovery.

PR #285 added top-level `GOLDEN_PATH/` (a reusable-workflow template + caller example) and `INVENTORY/`
(domain/service/repo inventory .md files). Both carry a `README.md`, which is a PROJECT_MARKER, so
`discover_project_dirs()` classified them as project directories and the project-governance validator
errored ("Project registry does not cover actual project directories: GOLDEN_PATH, INVENTORY") -- which
is what turned main red after #285 merged. They are documentation/skeleton dirs, not code projects (no
VERSION / pyproject / model registries), so they belong in INFRA_DIRS.

This guard pins that exclusion so a future edit that drops it re-breaks visibly here, not silently in
the whole project-governance gate. It also asserts non-vacuity: the real project (arxiv-daily-push) is
still discovered, so the exclusion did not accidentally hide a genuine project.
"""
import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate_project_governance.py"


def _load():
    spec = importlib.util.spec_from_file_location("validate_project_governance", VALIDATOR)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m  # the module defines @dataclass classes that resolve types via sys.modules
    spec.loader.exec_module(m)
    return m


class TestInfraDirsExclusions(unittest.TestCase):
    def setUp(self):
        self.assertTrue(VALIDATOR.is_file(), "project-governance validator missing: {}".format(VALIDATOR))
        self.m = _load()

    def test_doc_skeleton_dirs_are_in_infra_dirs(self):
        for name in ("GOLDEN_PATH", "INVENTORY"):
            self.assertIn(name, self.m.INFRA_DIRS,
                          "{} is a documentation/skeleton dir (has only README + templates/inventory md); "
                          "it must stay in INFRA_DIRS or it gets misclassified as a project and reddens the "
                          "project-governance gate.".format(name))

    def test_discovery_does_not_return_the_doc_dirs(self):
        discovered = set(self.m.discover_project_dirs())
        for name in ("GOLDEN_PATH", "INVENTORY"):
            if (ROOT / name).is_dir():
                self.assertNotIn(name, discovered,
                                 "{} was discovered as a project directory despite being infra/docs".format(name))

    def test_the_real_project_is_still_discovered(self):
        """Non-vacuity: the exclusion must not have hidden the genuine project."""
        if (ROOT / "arxiv-daily-push").is_dir():
            self.assertIn("arxiv-daily-push", set(self.m.discover_project_dirs()),
                          "arxiv-daily-push must still be discovered -- the exclusion over-reached")


if __name__ == "__main__":
    unittest.main()
