"""共享 Jinja2 环境 —— 网页与邮件同一模板环境（复审修复：消除双环境漂移）."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES = Path(__file__).parent / "templates"

env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
env.filters["fromjson"] = json.loads
