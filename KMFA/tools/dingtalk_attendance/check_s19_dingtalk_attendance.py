#!/usr/bin/env python3
"""deprecated_compatibility: forward the legacy checker entry to the canonical checker."""

from __future__ import annotations

from KMFA.tools.dingtalk_attendance.check_dingtalk_attendance import (
    main,
    validate_dingtalk_attendance_files,
)


DEPRECATED_COMPATIBILITY = True
# deprecated_compatibility alias; no validation logic lives in this module.
validate_s19_files = validate_dingtalk_attendance_files


if __name__ == "__main__":
    raise SystemExit(main())
