from __future__ import annotations

import json

from .health import ready


def main() -> int:
    print(json.dumps(ready().model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

