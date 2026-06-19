#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from db_tools import ROOT, connect_database, read_sql

MIGRATIONS_DIR = ROOT / "infra/db/migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path

    @property
    def up_path(self) -> Path:
        return self.path / "up.sql"

    @property
    def down_path(self) -> Path:
        return self.path / "down.sql"

    @property
    def checksum(self) -> str:
        return hashlib.sha256(read_sql(self.up_path).encode("utf-8")).hexdigest()


def discover_migrations() -> list[Migration]:
    migrations: list[Migration] = []
    for path in sorted(MIGRATIONS_DIR.iterdir()):
        if not path.is_dir() or "_" not in path.name:
            continue
        version, name = path.name.split("_", 1)
        if not version.isdigit():
            continue
        if not path.joinpath("up.sql").exists() or not path.joinpath("down.sql").exists():
            raise RuntimeError(f"Migration {path.name} must contain up.sql and down.sql")
        migrations.append(Migration(version=version, name=name, path=path))
    return migrations


def ensure_migration_table(connection: object) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version text PRIMARY KEY,
          name text NOT NULL,
          checksum text NOT NULL,
          applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def applied_migrations(connection: object) -> dict[str, str]:
    rows = connection.execute("SELECT version, checksum FROM schema_migrations").fetchall()
    return {version: checksum for version, checksum in rows}


def upgrade() -> list[str]:
    migrations = discover_migrations()
    applied_versions: dict[str, str]
    applied_now: list[str] = []
    with connect_database() as connection:
        ensure_migration_table(connection)
        applied_versions = applied_migrations(connection)
        for migration in migrations:
            if migration.version in applied_versions:
                if applied_versions[migration.version] != migration.checksum:
                    raise RuntimeError(f"Applied migration checksum drift: {migration.version}")
                continue
            connection.execute(read_sql(migration.up_path))
            connection.execute(
                """
                INSERT INTO schema_migrations(version, name, checksum)
                VALUES (%s, %s, %s)
                """,
                (migration.version, migration.name, migration.checksum),
            )
            applied_now.append(migration.version)
    return applied_now


def downgrade(all_migrations: bool, steps: int) -> list[str]:
    if not all_migrations and steps < 1:
        raise RuntimeError("Use --all or --steps N for downgrade")
    migrations = {migration.version: migration for migration in discover_migrations()}
    reverted: list[str] = []
    with connect_database() as connection:
        ensure_migration_table(connection)
        rows = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version DESC"
        ).fetchall()
        versions = [row[0] for row in rows]
        if not all_migrations:
            versions = versions[:steps]
        for version in versions:
            migration = migrations.get(version)
            if migration is None:
                raise RuntimeError(f"Unknown applied migration: {version}")
            connection.execute(read_sql(migration.down_path))
            connection.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
            reverted.append(version)
    return reverted


def status() -> dict[str, object]:
    migrations = discover_migrations()
    with connect_database() as connection:
        ensure_migration_table(connection)
        applied = applied_migrations(connection)
    return {
        "migrations": [
            {
                "version": migration.version,
                "name": migration.name,
                "applied": migration.version in applied,
                "checksum": migration.checksum,
            }
            for migration in migrations
        ]
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EEI PostgreSQL migrations.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("upgrade")
    downgrade_parser = subcommands.add_parser("downgrade")
    downgrade_parser.add_argument("--all", action="store_true", help="Revert every migration.")
    downgrade_parser.add_argument(
        "--steps",
        type=int,
        default=0,
        help="Number of migrations to revert.",
    )
    status_parser = subcommands.add_parser("status")
    status_parser.add_argument("--json", action="store_true", help="Emit machine-readable status.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "upgrade":
        applied = upgrade()
        print(json.dumps({"applied": applied}, indent=2))
    elif args.command == "downgrade":
        reverted = downgrade(all_migrations=args.all, steps=args.steps)
        print(json.dumps({"reverted": reverted}, indent=2))
    elif args.command == "status":
        payload = status()
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for migration in payload["migrations"]:
                marker = "applied" if migration["applied"] else "pending"
                print(f"{migration['version']} {migration['name']} {marker}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Migration failed: {exc}")
        raise SystemExit(1) from exc
