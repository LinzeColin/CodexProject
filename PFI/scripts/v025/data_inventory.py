#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import sys
import tempfile
from pathlib import Path


sys.dont_write_bytecode = True

PFI_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PFI_ROOT.parent
sys.path.insert(0, str(PFI_ROOT / "src"))

from pfi_v02.stage_v025_data_inventory import (  # noqa: E402
    assert_public_safe_payload,
    build_source_manifest,
    collect_data_root_inventory,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="data_inventory.py", add_help=True)
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--redact", action="store_true")
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args(argv)
    if not args.read_only or not args.redact:
        parser.error("--read-only and --redact are required")

    output = _lexical_absolute(args.json_out)
    _validate_output_path(parser, output)

    parent_fd: int | None = None
    temporary_name: str | None = None
    try:
        inventory = collect_data_root_inventory(REPO_ROOT)
        if inventory.get("acceptance_gate_status") != "pass":
            raise RuntimeError("inventory_not_publishable")
        manifest = build_source_manifest(inventory)
        assert_public_safe_payload(manifest)
        rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        parent_fd = _open_output_parent_fd(output)
        temporary_name, descriptor = _create_private_temp(parent_fd)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(
            temporary_name,
            output.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        # The no-overwrite hard link is the publication commit point: the
        # destination now names a complete, file-fsynced 0600 inode. Cleanup
        # and directory fsync are best-effort post-commit work so the CLI can
        # never report FAIL while leaving a valid published destination.
        if _best_effort_unlink(temporary_name, parent_fd):
            temporary_name = None
        try:
            os.fsync(parent_fd)
        except OSError:
            pass
    except Exception:
        if parent_fd is not None and temporary_name is not None:
            _best_effort_unlink(temporary_name, parent_fd)
        print("source_manifest=FAIL|reason=redacted", file=sys.stderr)
        return 1
    finally:
        if parent_fd is not None:
            try:
                os.close(parent_fd)
            except OSError:
                pass
    print("source_manifest=PASS|read_only=true|redacted=true")
    return 0


def _validate_output_path(parser: argparse.ArgumentParser, output: Path) -> None:
    try:
        temp_root = _trusted_temp_root(output)
    except ValueError:
        parser.error("output must be inside the operating-system temp root")
    if output.exists() or output.is_symlink():
        parser.error("output must be a new non-symlink file")
    if not output.parent.is_dir() or _path_chain_has_symlink(output.parent, temp_root):
        parser.error("output parent must be an existing non-symlink temp directory")

    data_home = _lexical_absolute(os.environ.get("PFI_DATA_HOME", "~/.pfi"))
    candidates = (
        REPO_ROOT / "MetaDatabase" / "PFI",
        PFI_ROOT / "MetaDatabase",
        data_home,
        _lexical_absolute(Path.home() / ".pfi"),
        REPO_ROOT,
    )
    if any(_is_relative_to(output.resolve(strict=False), root.resolve(strict=False)) for root in candidates):
        parser.error("output must not be inside source, repository, or private roots")


def _trusted_temp_root(output: Path) -> Path:
    lexical = _lexical_absolute(tempfile.gettempdir())
    canonical = lexical.resolve()
    for root in dict.fromkeys((lexical, canonical)):
        if _is_relative_to(output, root):
            return root
    raise ValueError("output_outside_trusted_temp_root")


def _open_output_parent_fd(output: Path) -> int:
    root = _trusted_temp_root(output)
    relative_parent = output.parent.relative_to(root)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(root, directory_flags)
    try:
        for part in relative_parent.parts:
            child = os.open(
                part,
                directory_flags | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        try:
            os.stat(output.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            return descriptor
        raise FileExistsError("output_exists")
    except Exception:
        os.close(descriptor)
        raise


def _create_private_temp(parent_fd: int) -> tuple[str, int]:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    for _ in range(8):
        name = f".pfi-v025-source-manifest-{secrets.token_hex(16)}.tmp"
        try:
            return name, os.open(name, flags, 0o600, dir_fd=parent_fd)
        except FileExistsError:
            continue
    raise FileExistsError("temporary_name_exhausted")


def _best_effort_unlink(name: str, parent_fd: int) -> bool:
    for _ in range(2):
        try:
            os.unlink(name, dir_fd=parent_fd)
            return True
        except OSError:
            continue
    return False


def _path_chain_has_symlink(path: Path, trusted_root: Path) -> bool:
    try:
        relative = path.relative_to(trusted_root)
    except ValueError:
        return True
    current = trusted_root
    for part in relative.parts:
        current = current / part
        try:
            info = current.lstat()
        except (FileNotFoundError, PermissionError):
            return True
        if stat.S_ISLNK(info.st_mode):
            return True
    return False


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _lexical_absolute(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(os.fspath(value))))


if __name__ == "__main__":
    raise SystemExit(main())
