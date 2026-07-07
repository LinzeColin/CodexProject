from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if yaml is None:
        return _load_simple_yaml(p)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {p}")
    return data


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    lines: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    def parse_value(value: str) -> Any:
        value = value.strip()
        if value in {"true", "false"}:
            return value == "true"
        if value in {"null", "None", "~"}:
            return None
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []
            return [parse_value(part.strip()) for part in inner.split(",")]
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines) or lines[index][0] < indent:
            return {}, index
        is_list = lines[index][0] == indent and lines[index][1].startswith("- ")
        if is_list:
            out: list[Any] = []
            while index < len(lines):
                line_indent, content = lines[index]
                if line_indent < indent:
                    break
                if line_indent > indent:
                    break
                if not content.startswith("- "):
                    break
                rest = content[2:].strip()
                index += 1
                if not rest:
                    child, index = parse_block(index, lines[index][0] if index < len(lines) else indent + 2)
                    out.append(child)
                    continue
                if ":" in rest:
                    key, value = rest.split(":", 1)
                    item: dict[str, Any] = {}
                    if value.strip():
                        item[key.strip()] = parse_value(value)
                    else:
                        child, index = parse_block(index, lines[index][0] if index < len(lines) else indent + 2)
                        item[key.strip()] = child
                    if index < len(lines) and lines[index][0] > indent:
                        continuation, index = parse_block(index, lines[index][0])
                        if isinstance(continuation, dict):
                            item.update(continuation)
                    out.append(item)
                else:
                    out.append(parse_value(rest))
            return out, index

        out_dict: dict[str, Any] = {}
        while index < len(lines):
            line_indent, content = lines[index]
            if line_indent < indent:
                break
            if line_indent > indent:
                break
            if content.startswith("- "):
                break
            if ":" not in content:
                raise ValueError(f"Unsupported YAML line in {path}: {content}")
            key, value = content.split(":", 1)
            key = key.strip()
            index += 1
            if value.strip():
                out_dict[key] = parse_value(value)
            else:
                child_indent = lines[index][0] if index < len(lines) else indent + 2
                child, index = parse_block(index, child_indent)
                out_dict[key] = child
        return out_dict, index

    parsed, final_index = parse_block(0, lines[0][0] if lines else 0)
    if final_index != len(lines):
        raise ValueError(f"Unsupported YAML structure near line {final_index + 1}: {path}")
    if not isinstance(parsed, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return parsed
