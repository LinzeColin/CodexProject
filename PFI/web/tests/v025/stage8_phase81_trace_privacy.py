#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

from stage7_trace_privacy import sanitize_playwright_trace


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: stage8_phase81_trace_privacy.py RAW_TRACE OUTPUT_TRACE")
    result = sanitize_playwright_trace(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
