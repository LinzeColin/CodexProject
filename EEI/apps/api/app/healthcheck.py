from __future__ import annotations

import json

from .health import readiness_response


def main() -> int:
    payload = readiness_response().model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
