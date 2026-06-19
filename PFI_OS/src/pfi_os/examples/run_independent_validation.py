from __future__ import annotations

import argparse
import json
from pathlib import Path

from pfi_os.integrations.independent_validation import (
    DEFAULT_ROWS_PER_SHARD,
    independent_validation_runs_frame,
    run_independent_validation,
    write_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or plan the independent validation system through the shared research bus.")
    sub = parser.add_subparsers(required=True)

    manifest = sub.add_parser("create-manifest")
    manifest.add_argument("--output", required=True)
    manifest.add_argument("--dataset-name", default="IndependentValidationDataset")
    manifest.add_argument("input_paths", nargs="+")

    run = sub.add_parser("run")
    run.add_argument("--manifest", default="")
    run.add_argument("--db", default="")
    run.add_argument("--synthetic-rows", type=int, default=0)
    run.add_argument("--rows-per-shard", type=int, default=DEFAULT_ROWS_PER_SHARD)
    run.add_argument("--mode", choices=["dry_run", "checksum"], default="dry_run")
    run.add_argument("--output-dir", default="")
    run.add_argument("--worker-count", type=int, default=1)
    run.add_argument("--json", action="store_true")

    status = sub.add_parser("status")
    status.add_argument("--db", default="")
    status.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if hasattr(args, "input_paths"):
        path = write_manifest([Path(item).expanduser() for item in args.input_paths], args.output, dataset_name=args.dataset_name)
        print(path)
        return

    if args.__dict__.get("manifest", None) is not None:
        result = run_independent_validation(
            Path(args.manifest).expanduser() if args.manifest else None,
            db_path=Path(args.db).expanduser() if args.db else None,
            synthetic_rows=args.synthetic_rows,
            rows_per_shard=args.rows_per_shard,
            mode=args.mode,
            output_dir=Path(args.output_dir).expanduser() if args.output_dir else None,
            worker_count=args.worker_count,
        )
        payload = result.to_dict()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        print(f"run_id: {result.run_id}")
        print(f"status: {result.status}")
        print(f"total_rows: {result.total_rows}")
        print(f"shard_count: {result.shard_count}")
        print(f"execution_tier: {result.execution_tier}")
        print(f"worker_count: {result.worker_count}")
        print(f"output_path: {result.output_path}")
        return

    frame = independent_validation_runs_frame(Path(args.db).expanduser() if args.db else None)
    if args.json:
        print(json.dumps(frame.to_dict("records"), ensure_ascii=False, indent=2))
        return
    if frame.empty:
        print("No independent validation runs.")
    else:
        print(frame.to_csv(index=False))


if __name__ == "__main__":
    main()
