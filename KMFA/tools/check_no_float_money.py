#!/usr/bin/env python3
"""Check that KMFA Python code does not use float for business money."""

from __future__ import annotations

import argparse
import ast
import re
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
MONEY_CONTEXT_TOKENS = {
    "amount",
    "balance",
    "cash",
    "cents",
    "cost",
    "expense",
    "fee",
    "fund",
    "loan",
    "money",
    "payable",
    "price",
    "receivable",
    "revenue",
    "salary",
    "tax",
    "wage",
    "yuan",
}
NON_MONEY_CONTEXT_TOKENS = {
    "confidence",
    "duration",
    "height",
    "interval",
    "mtime",
    "opacity",
    "percent",
    "probability",
    "ratio",
    "score",
    "seconds",
    "timestamp",
    "timeout",
    "weight",
    "width",
}


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
    def __init__(self, path: Path, tree: ast.AST) -> None:
        self.path = path
        self.findings: list[FloatFinding] = []
        self.non_money_nodes: set[int] = set()
        self.parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                self.parents[id(child)] = parent

    @staticmethod
    def _tokens(value: str) -> set[str]:
        expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
        return {part.lower() for part in re.findall(r"[A-Za-z]+", expanded)}

    @classmethod
    def _binding_tokens(cls, node: ast.AST) -> set[str]:
        tokens: set[str] = set()
        if isinstance(node, ast.Name):
            tokens.update(cls._tokens(node.id))
        elif isinstance(node, ast.Attribute):
            tokens.update(cls._tokens(node.attr))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tokens.update(cls._tokens(node.name))
        elif isinstance(node, ast.arg):
            tokens.update(cls._tokens(node.arg))
        elif isinstance(node, ast.keyword) and node.arg:
            tokens.update(cls._tokens(node.arg))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            tokens.update(cls._tokens(node.value))
        return tokens

    def _context_tokens(self, node: ast.AST) -> tuple[set[str], set[str]]:
        local: set[str] = self._binding_tokens(node)
        if isinstance(node, ast.AnnAssign):
            for child in ast.walk(node.target):
                local.update(self._binding_tokens(child))
        outer: set[str] = set()
        current: ast.AST | None = node
        while current is not None:
            parent = self.parents.get(id(current))
            if parent is None:
                break
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                outer.update(self._binding_tokens(parent))
            elif isinstance(parent, ast.Assign):
                for target in parent.targets:
                    for child in ast.walk(target):
                        local.update(self._binding_tokens(child))
            elif isinstance(parent, ast.AnnAssign):
                for child in ast.walk(parent.target):
                    local.update(self._binding_tokens(child))
            elif isinstance(parent, ast.keyword):
                local.update(self._binding_tokens(parent))
            elif isinstance(parent, ast.Call):
                for child in ast.walk(parent):
                    if isinstance(child, (ast.Name, ast.Attribute, ast.keyword)):
                        local.update(self._binding_tokens(child))
            elif isinstance(parent, ast.Dict):
                for key, value in zip(parent.keys, parent.values):
                    if value is current and key is not None:
                        local.update(self._binding_tokens(key))
                        break
            current = parent
        return local, outer

    def _is_money_context(self, node: ast.AST) -> bool:
        local, outer = self._context_tokens(node)
        if local & NON_MONEY_CONTEXT_TOKENS:
            return False
        return bool((local | outer) & MONEY_CONTEXT_TOKENS)

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
        if (
            isinstance(node.value, float)
            and id(node) not in self.non_money_nodes
            and self._is_money_context(node)
        ):
            self.add(node, "float literal is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and key.value in NON_MONEY_FLOAT_DICT_KEYS:
                self.non_money_nodes.update(id(child) for child in ast.walk(value))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _call_name(node) == "float" and self._is_money_context(node):
            self.add(node, "float() conversion is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        if _is_float_annotation(node.annotation) and self._is_money_context(node):
            self.add(node, "float annotation is forbidden for KMFA business money")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if _is_float_annotation(node.annotation) and self._is_money_context(node):
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
    visitor = FloatMoneyVisitor(path, tree)
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
