#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: nothing may read TASK_INDEX.csv's `status` column, because it is dead config that lies.

`arxiv-daily-push/docs/pursuing_goal/v0_1/TASK_INDEX.csv` is the V0.1 plan of record: 90 tasks,
written once (commit f24456f95, "S0-P03-T008: task/evidence/independent-review framework") and
NEVER modified since -- one commit in the file's entire history. Its last column, `status`, says
`NOT_STARTED` for all 90 rows.

All 90 are delivered. The CHANGELOG says so, the evidence bundles under v0_1/evidence/ say so, and
the deployed worker serves the result. The column was never wired to anything: no code writes it,
and -- as this test pins -- no code reads it either. It is not a stale value that drifted. It was
inert from the day it was typed.

Why this is worth a test rather than a shrug: it already cost real work. An agent (me) trusted the
column while shipping the V0.2 integration, concluded T041 had never been built, and rebuilt it.
T041 already existed. The duplicate was deleted before it reached a commit, but the hours were gone.
The column is a trap that fires on readers, not on code -- which is exactly why no test caught it and
why CI is green while it lies.

What this test asserts, and why only this:
  * No Python under the repo reads the `status` field of a TASK_INDEX row.

That invariant is TRUE today, so this test is green on arrival and stays that way until someone wires
the column up. If someone does, this goes red and forces the real question first: the column has no
maintained value, so before reading it you must either populate it truthfully or delete it.

What this test deliberately does NOT do:
  * It does not rewrite the column to say `DELIVERED`. Nobody living wrote those 90 statuses, and
    inventing them -- 90 rows of authoritative-looking state derived from my own reading of a
    CHANGELOG -- is precisely the fabrication this project keeps getting burned by. A record that
    says nothing is safer than a record that confidently says something nobody verified.
  * It does not edit TASK_INDEX.csv at all. That file is the original plan as written. It is history,
    not a dashboard; back-dating history to match the outcome destroys its only value.
  * It does not assert the column contradicts the CHANGELOG. Such a test would be red on arrival and
    would simply be deleted, which is how guards die.

The disposition of the column -- populate it, or drop it -- is the Owner's call, because it is the
Owner's plan document. This test makes sure that until that call is made, the lie cannot spread from
a document nobody reads into code that acts on it.

KNOWN GAPS, stated so nobody mistakes this for airtight (all found by independent review, not by me):
  * INTERPROCEDURAL READS ARE NOT CAUGHT. `def is_done(rec): return rec["status"]`, called with an
    index row, passes. This is the realistic bypass -- it is how someone would naturally write the
    exact T041 trap -- and it is the most serious known hole. Name-based taint cannot follow a value
    into a callee's parameter without real interprocedural analysis.
  * Also uncaught: `row.items()` / `row.values()` loops, positional `csv.reader` access (`row[17]`),
    computed keys (`"sta"+"tus"`), pandas. These are contrived rather than natural, but they are
    holes.
  * SCOPE IS *.py ONLY. Independently confirmed there are no non-Python readers today (no .sh/.yml/
    .js/.ts reads it), so this is honest scoping rather than a hidden gap -- but it is scoping.
  * `value_cost_scorecard.py` has a NEAR-MISS false positive at the `card['owner_signoff']['status']`
    site: `card` IS in the taint set, and that read escapes only because its receiver is a Subscript
    rather than a Name. A cosmetic refactor (`sec = card['owner_signoff']` then `sec['status']`)
    would turn this guard red on innocent code. If that happens, the guard is wrong, not the code.
  * THIS FILE'S OWN BASENAME IS A BLIND SPOT. test_the_set_of_files_that_parse_the_index_has_not_grown
    skips any file named `test_adp_task_index_status_is_dead_config.py` wherever it lives -- the skip
    is by name, not path (see the comment on that line for why it must be). So a file adopting this
    exact basename could parse the index and read `status` invisibly. Verified real by review: a
    same-named file doing `if row["status"] == "NOT_STARTED": print("rebuilding", row["task_id"])`
    still leaves the suite at `4 passed`. Judged acceptable, and the reasoning is the point: the
    threat model is an agent INNOCENTLY trusting the column, and nobody names their status-reader
    after this guard by accident. It is a hole against an adversary, not against the failure this
    exists to prevent.
This catches the natural, direct forms. It does not make the column safe to read.
"""
import ast
import csv
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX = ROOT / "arxiv-daily-push" / "docs" / "pursuing_goal" / "v0_1" / "TASK_INDEX.csv"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Every Python file naming TASK_INDEX.csv, hand-reviewed 2026-07-19. Pinned by
# test_the_set_of_files_that_parse_the_index_has_not_grown so the reader check cannot lose coverage
# to a new parser nobody looked at.
_TOOLS = "arxiv-daily-push/docs/pursuing_goal/v0_1/tools/"
KNOWN_PARSERS = (
    _TOOLS + "task_runner.py",           # 'status' appears only in a docstring line
    _TOOLS + "value_cost_scorecard.py",  # reads status off PARITY + its own card dict, not the index
    _TOOLS + "check_dag.py",             # never mentions status
    _TOOLS + "final_handoff.py",         # status is its own hardcoded literals
)


def _rows():
    with INDEX.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _python_files():
    for p in ROOT.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in p.parts):
            yield p


class TestTaskIndexStatusIsDeadConfig(unittest.TestCase):
    def test_the_index_and_its_status_column_still_exist(self):
        """If the file or column is gone, this guard is checking nothing -- fail loudly instead."""
        self.assertTrue(INDEX.is_file(), "TASK_INDEX.csv is missing: {}".format(INDEX))
        rows = _rows()
        self.assertEqual(len(rows), 90, "expected the 90-task V0.1 plan of record; found {}".format(len(rows)))
        self.assertIn("status", rows[0],
                      "TASK_INDEX.csv no longer has a `status` column. If it was deliberately dropped, "
                      "delete this guard in the same commit and say so. Do not leave it passing "
                      "vacuously over a column that no longer exists.")

    def test_the_status_column_is_still_uniformly_inert(self):
        """Pin the premise this guard rests on: every row says the same never-updated thing.

        If some rows now carry real statuses, the column is being maintained after all and the
        docstring above is out of date -- which changes what the right fix is. Go read it, then
        decide deliberately; do not let this test keep asserting a story that stopped being true."""
        values = {r.get("status", "") for r in _rows()}
        self.assertEqual(
            values, {"NOT_STARTED"},
            "TASK_INDEX.csv's status column is no longer uniformly NOT_STARTED: {}.\nThis guard exists "
            "because the column was inert and misleading. If it is now being maintained, that is good "
            "news -- update this test's premise deliberately rather than deleting it.".format(sorted(values)))

    def test_the_set_of_files_that_parse_the_index_has_not_grown(self):
        """Pin WHO parses TASK_INDEX.csv, so a new parser cannot slip past the reader check below.

        The reader check only inspects files that parse the index. If that set silently grows, the
        check's coverage silently shrinks. Reviewed by hand on 2026-07-19: of these four, task_runner
        says 'status' only in a docstring, value_cost_scorecard reads it off PARITY and its own card
        dict, check_dag never mentions it, and final_handoff uses its own hardcoded literals. None
        touches a TASK_INDEX row's status."""
        found = set()
        for path in _python_files():
            # Skip THIS guard by filename, not by resolved path: the V0.2 evidence bundle keeps a
            # byte-identical copy of it under test-results/, and that copy also contains the literal
            # "TASK_INDEX.csv". A resolved-path check matches only the original, so the copy counted
            # as a new parser and this assertion fired on the guard's own evidence -- red on arrival,
            # which the docstring above correctly says is a death sentence for a guard.
            # The copy is DELIBERATE, NOT REQUIRED: an evidence bundle should contain the artifact that
            # was reviewed. test_adp_v02_evidence_bundles only requires the test-results DIRECTORY to
            # be non-empty, which nc_results.txt satisfies alone -- deleting this copy would be a
            # perfectly valid alternative. Do not read the two facts as "the copy cannot be deleted":
            # a negative control asserting exactly that was fabricated in review round 2, and it does
            # not fire. This skip makes keeping the copy safe; it does not make keeping it mandatory.
            if path.name == pathlib.Path(__file__).name:
                continue
            try:
                if "TASK_INDEX.csv" in path.read_text(encoding="utf-8"):
                    found.add(str(path.relative_to(ROOT)))
            except (UnicodeDecodeError, OSError):
                continue
        self.assertEqual(
            found, set(KNOWN_PARSERS),
            "The set of Python files naming TASK_INDEX.csv changed.\n  added:   {}\n  removed: {}\n"
            "Each new one must be hand-checked for whether it reads the (inert, misleading) status "
            "column, then added here deliberately.".format(
                sorted(found - set(KNOWN_PARSERS)) or "-", sorted(set(KNOWN_PARSERS) - found) or "-"))

    def test_no_code_reads_the_status_column(self):
        """The invariant that actually protects anyone: the lie must not reach code.

        The column claims all 90 tasks are NOT_STARTED. Any code that believes it will skip, rebuild,
        or re-plan delivered work -- which already happened once, to an agent, at the cost of a
        rebuilt T041. Until the column is populated truthfully or removed, nothing may read it.

        This tracks DATAFLOW, not filenames: it finds the names bound to a parse of TASK_INDEX.csv
        (and the loop variables iterating them), then flags `status` reads on THOSE names only. The
        first cut of this test flagged any ['status'] in any file that merely mentioned TASK_INDEX in
        a docstring -- 33 false positives, every one a read of an unrelated dict. A guard that cries
        wolf on arrival gets deleted, and deleting it would be the correct response."""
        offenders = []
        for rel in KNOWN_PARSERS:
            path = ROOT / rel
            if not path.is_file():
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            # Seed: names bound to an expression naming the CSV. Then propagate to a fixpoint through
            # the chain the real code actually uses:
            #     INDEX = ... / "TASK_INDEX.csv"      -> INDEX
            #     open(INDEX) as f                    -> f
            #     reader = csv.DictReader(f)          -> reader
            #     for r in reader                     -> r
            #     by_id[key] = r                      -> by_id
            #     row = by_id[task_id]                -> row       <-- where the T041 trap lives
            # Coarse on purpose: anything derived from the index is a suspect. NC3 pins that this does
            # not bleed onto unrelated dicts (PARITY et al) in the same file.
            tainted = set()

            def mentions(node_):
                """Does this expression reference a tainted name?"""
                return any(isinstance(n, ast.Name) and n.id in tainted for n in ast.walk(node_))

            def bind(target):
                if isinstance(target, ast.Name):
                    tainted.add(target.id)
                elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                    tainted.add(target.value.id)          # by_id[key] = <tainted row>
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for e in target.elts:
                        bind(e)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and "TASK_INDEX.csv" in ast.dump(node.value):
                    for t in node.targets:
                        bind(t)

            for _ in range(8):                             # settle; the real chains are <=6 hops
                before = len(tainted)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign) and mentions(node.value):
                        for t in node.targets:
                            bind(t)
                    elif isinstance(node, (ast.For, ast.comprehension)) and mentions(node.iter):
                        bind(node.target)
                    elif isinstance(node, ast.withitem) and node.optional_vars is not None \
                            and mentions(node.context_expr):
                        bind(node.optional_vars)
                    elif isinstance(node, ast.Return) and node.value is not None and mentions(node.value):
                        tainted.add("__returns_index__")
                # a function returning index data taints its callers' assignments
                if "__returns_index__" in tainted:
                    fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                           and any(isinstance(x, ast.Return) and x.value is not None and mentions(x.value)
                                   for x in ast.walk(n))}
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                                and isinstance(node.value.func, ast.Name) and node.value.func.id in fns:
                            for t in node.targets:
                                bind(t)
                if len(tainted) == before:
                    break
            for node in ast.walk(tree):
                recv, how = None, None
                if (isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant)
                        and node.slice.value == "status" and isinstance(node.value, ast.Name)):
                    recv, how = node.value.id, "['status']"
                elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                      and node.func.attr == "get" and node.args
                      and isinstance(node.args[0], ast.Constant) and node.args[0].value == "status"
                      and isinstance(node.func.value, ast.Name)):
                    recv, how = node.func.value.id, ".get('status')"
                if recv in tainted:
                    offenders.append("{}:{}: {}{}".format(rel, node.lineno, recv, how))
        self.assertEqual(
            offenders, [],
            "Code now reads `status` off a TASK_INDEX.csv row:\n  " + "\n  ".join(offenders)
            + "\n\nThat column says NOT_STARTED for all 90 tasks. All 90 are delivered. It has never "
              "been updated since the commit that created the file, and nothing has ever read it. "
              "Acting on it means skipping or rebuilding finished work -- an agent already rebuilt "
              "T041 by trusting it.\n"
              "Before reading this column: populate it truthfully, or delete it. Do not read it as-is, "
              "and do not populate it by inferring 90 statuses from a CHANGELOG.")


if __name__ == "__main__":
    unittest.main()
