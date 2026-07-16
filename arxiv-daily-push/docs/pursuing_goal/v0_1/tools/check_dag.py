#!/usr/bin/env python3
"""ADP V0.1 dependency DAG checker.

Validates TASK_INDEX.csv:
  1. every task_id is unique;
  2. expected task count (default 90);
  3. every dependency references an existing task_id;
  4. the dependency graph is acyclic (topological sort succeeds).

Exit 0 only when all checks pass. Never mutates anything.

Usage:
  python3 check_dag.py [--index PATH] [--expect N]
"""
import argparse, csv, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_INDEX = HERE.parent / "TASK_INDEX.csv"


def load(index_path):
    with open(index_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    tasks = {}
    order = []
    for r in rows:
        tid = (r.get("task_id") or "").strip()
        deps_raw = (r.get("dependencies") or "").strip()
        deps = [d.strip() for d in deps_raw.replace(",", ";").split(";") if d.strip()]
        tasks.setdefault(tid, []) if tid not in tasks else None
        if tid in tasks and order.count(tid):
            pass
        tasks[tid] = deps
        order.append(tid)
    return rows, tasks, order


def find_cycle(tasks):
    """Return a cycle path if one exists, else None. Iterative DFS with colors."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {t: WHITE for t in tasks}
    parent = {}
    for start in tasks:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(tasks.get(start, [])))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            advanced = False
            for dep in it:
                if dep not in tasks:
                    continue  # dangling dep handled separately
                if color[dep] == GRAY:
                    # back edge -> cycle; reconstruct
                    cycle = [dep, node]
                    p = parent.get(node)
                    while p is not None and p != dep:
                        cycle.append(p); p = parent.get(p)
                    cycle.append(dep)
                    return list(reversed(cycle))
                if color[dep] == WHITE:
                    color[dep] = GRAY
                    parent[dep] = node
                    stack.append((dep, iter(tasks.get(dep, []))))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    ap.add_argument("--expect", type=int, default=90)
    args = ap.parse_args()

    rows, tasks, order = load(args.index)
    problems = []

    # 1. duplicate ids
    dupes = sorted({t for t in order if order.count(t) > 1})
    if dupes:
        problems.append(f"duplicate task_id(s): {dupes}")

    # 2. count
    unique_ids = list(tasks.keys())
    if len(unique_ids) != args.expect:
        problems.append(f"expected {args.expect} unique task_ids, found {len(unique_ids)}")

    # 3. dangling deps
    dangling = sorted({d for deps in tasks.values() for d in deps if d not in tasks})
    if dangling:
        problems.append(f"dependencies referencing unknown task_id(s): {dangling}")

    # 4. cycle
    cycle = find_cycle(tasks)
    if cycle:
        problems.append("dependency cycle: " + " -> ".join(cycle))

    print(f"TASK_INDEX: {args.index}")
    print(f"unique task_ids: {len(unique_ids)}")
    print(f"total dependency edges: {sum(len(v) for v in tasks.values())}")
    if problems:
        print("RESULT: FAIL")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("RESULT: PASS (unique ids, count matches, no dangling deps, acyclic)")
    sys.exit(0)


if __name__ == "__main__":
    main()
