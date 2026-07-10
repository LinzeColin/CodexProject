#!/usr/bin/env python3
"""Check that KMFA Python code does not use float for business money."""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDES = {
    ".codex_private_runtime",
    "taskpack",
    "stage_artifacts",
    "tests",
    "__pycache__",
}
NON_MONEY_FLOAT_DICT_KEYS = {"derived_percent"}


@dataclass(frozen=True)
class FloatFinding:
    path: Path
    line: int
    column: int
    message: str


def _is_float_annotation(annotation: ast.AST | None) -> bool:
    if isinstance(annotation, ast.Name) and annotation.id == "float":
        return True
    if isinstance(annotation, ast.Attribute) and annotation.attr == "float":
        return True
    if isinstance(annotation, ast.Subscript):
        return _is_float_annotation(annotation.slice)
    if isinstance(annotation, ast.Tuple):
        return any(_is_float_annotation(item) for item in annotation.elts)
    if isinstance(annotation, ast.BinOp):
        return _is_float_annotation(annotation.left) or _is_float_annotation(annotation.right)
    return False


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


class FloatMoneyVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[FloatFinding] = []
        self.non_money_nodes: set[int] = set()

    def add(self, node: ast.AST, message: str) -> None:
        self.findings.append(
            FloatFinding(
                path=self.path,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                message=message,
            )
        )

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, float) and id(node) not in self.non_money_nodes:
            self.add(node, "float literal is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value in NON_MONEY_FLOAT_DICT_KEYS:
                self.non_money_nodes.update(id(child) for child in ast.walk(value))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _call_name(node) == "float":
            self.add(node, "float() conversion is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        if _is_float_annotation(node.annotation):
            self.add(node, "float annotation is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if _is_float_annotation(node.annotation):
            self.add(node, "float annotation is forbidden for KMFA business money")
        self.generic_visit(node)


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue
        if not path.is_dir():
            continue
        for candidate in path.rglob("*.py"):
            rel_parts = candidate.relative_to(path).parts
            if any(part in DEFAULT_EXCLUDES for part in rel_parts):
                continue
            files.append(candidate)
    return sorted(set(files))


def scan_file(path: Path) -> list[FloatFinding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [FloatFinding(path, exc.lineno or 0, exc.offset or 0, f"syntax error blocks float scan: {exc.msg}")]
    visitor = FloatMoneyVisitor(path)
    visitor.visit(tree)
    return visitor.findings


def scan_paths(paths: list[Path]) -> list[FloatFinding]:
    findings: list[FloatFinding] = []
    for path in iter_python_files(paths):
        findings.extend(scan_file(path))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check KMFA Python files for forbidden float money usage.")
    parser.add_argument("paths", nargs="*", default=[str(ROOT)])
    args = parser.parse_args(argv)
    paths = [Path(item) for item in args.paths]
    findings = scan_paths(paths)
    if findings:
        for finding in findings:
            rel = finding.path if finding.path.is_absolute() else finding.path
            print(f"FAIL: {rel}:{finding.line}:{finding.column}: {finding.message}")
        return 1
    print("PASS: no KMFA Python float money usage found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
