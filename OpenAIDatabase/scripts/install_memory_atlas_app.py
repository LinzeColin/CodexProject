#!/usr/bin/env python3
"""Install macOS .app launchers for the Memory Atlas local app."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


APP_NAME = "Memory Atlas.app"
EXECUTABLE_NAME = "memory-atlas-launcher"
BUNDLE_ID = "com.linze.openai-database.memory-atlas"
ICON_NAME = "MemoryAtlas"
DEFAULT_PORT = "4177"


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def default_targets() -> list[Path]:
    return [Path.home() / "Downloads" / APP_NAME, Path("/Applications") / APP_NAME]


def runtime_root() -> Path:
    override = os.environ.get("MEMORY_ATLAS_APP_SUPPORT_ROOT")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "OpenAIDatabase" / "MemoryAtlas"


def source_workspace_root() -> Path:
    return runtime_root() / "source"


def run_command(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True)


def run_npm_ci(repo_root: Path, app_dir: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="memory-atlas-npm-cache-") as cache_dir:
        subprocess.run(
            ["npm", "ci", "--prefix", str(app_dir), "--cache", cache_dir],
            cwd=str(repo_root),
            check=True,
        )


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path)
    except OSError:
        pass
    if path.exists():
        subprocess.run(["chmod", "-R", "u+w", str(path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["rm", "-rf", str(path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if path.exists():
        raise RuntimeError(f"failed to remove directory: {path}")


def frontend_dependencies_ready(app_dir: Path) -> bool:
    return (
        (app_dir / "node_modules" / ".bin" / "vite").exists()
        and (app_dir / "node_modules" / ".bin" / "tsc").exists()
        and (app_dir / "node_modules" / "vite" / "dist" / "client" / "client.mjs").exists()
        and (app_dir / "node_modules" / "lightningcss" / "package.json").exists()
        and (app_dir / "node_modules" / "typescript" / "package.json").exists()
    )


def git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def git_commit_count(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "1"
    return result.stdout.strip() or "1"


def write_runtime_build_info(repo_root: Path, runtime_dir: Path) -> None:
    snapshot_path = runtime_dir / "memory_atlas.json"
    snapshot_generated_at = ""
    if snapshot_path.exists():
        try:
            snapshot_generated_at = json.loads(snapshot_path.read_text(encoding="utf-8")).get("overview", {}).get("generated_at") or ""
        except json.JSONDecodeError:
            snapshot_generated_at = ""
    payload = {
        "schema_version": "memory_atlas_build.v1",
        "git_commit": git_commit(repo_root),
        "built_at_epoch": int(time.time()),
        "snapshot_generated_at": snapshot_generated_at,
        "snapshot_mtime_epoch": int(snapshot_path.stat().st_mtime) if snapshot_path.exists() else None,
    }
    (runtime_dir / "memory_atlas_build.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stop_existing_runtime_server() -> None:
    support_dir = runtime_root()
    pid_file = support_dir / "server.pid"
    watchdog_file = support_dir / "server_watchdog.pid"
    for file_path in (watchdog_file, pid_file):
        if not file_path.exists():
            continue
        try:
            pid = int(file_path.read_text(encoding="utf-8").strip())
        except ValueError:
            file_path.unlink(missing_ok=True)
            continue
        if pid <= 0:
            file_path.unlink(missing_ok=True)
            continue
        try:
            command = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                check=False,
                capture_output=True,
                text=True,
            ).stdout
        except OSError:
            command = ""
        if (
            ("python3 -m http.server" in command and "OpenAIDatabase/MemoryAtlas" in command)
            or ("memory_atlas_server.py" in command and "OpenAIDatabase/MemoryAtlas" in command)
        ):
            subprocess.run(["kill", str(pid)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        file_path.unlink(missing_ok=True)


def clean_frontend_build_cache(app_dir: Path) -> None:
    node_modules = app_dir / "node_modules"
    dist = app_dir / "dist"
    if node_modules.exists():
        remove_tree(node_modules)
    if dist.exists():
        remove_tree(dist)
    tsbuildinfo = app_dir / "tsconfig.tsbuildinfo"
    if tsbuildinfo.exists():
        tsbuildinfo.unlink()
    leftovers = [path for path in [node_modules, dist, tsbuildinfo] if path.exists()]
    if leftovers:
        raise RuntimeError(f"Memory Atlas build cache cleanup failed: {leftovers}")


def clean_frontend_dependencies(app_dir: Path) -> None:
    node_modules = app_dir / "node_modules"
    if node_modules.exists():
        remove_tree(node_modules)
    if node_modules.exists():
        raise RuntimeError(f"Memory Atlas dependency cleanup failed: {node_modules}")


def source_workspace_ignore(_directory: str, names: list[str]) -> set[str]:
    excluded_names = {
        ".DS_Store",
        ".git",
        ".local_keys",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "dist",
        "node_modules",
        "raw",
        "raw_encrypted",
        "tsconfig.tsbuildinfo",
    }
    excluded_suffixes = (".pyc", ".pyo")
    return {name for name in names if name in excluded_names or name.endswith(excluded_suffixes)}


def sync_source_workspace(repo_root: Path) -> Path:
    source_dir = source_workspace_root()
    staging_dir = source_dir.with_name("source.next")
    if staging_dir.exists():
        remove_tree(staging_dir)
    source_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(repo_root, staging_dir, ignore=source_workspace_ignore)

    manifest = {
        "schema_version": "memory_atlas_source_workspace.v1",
        "original_repo_root": str(repo_root),
        "installed_git_commit": git_commit(repo_root),
        "installed_at_epoch": int(time.time()),
        "purpose": "Runs Memory Atlas snapshot refresh outside Documents so every app launch can use the latest local data.",
    }
    (staging_dir / "memory_atlas_source_workspace.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if source_dir.exists():
        remove_tree(source_dir)
    staging_dir.rename(source_dir)
    return source_dir


def refresh_memory_atlas_snapshot(repo_root: Path) -> None:
    run_command(
        [
            sys.executable,
            "scripts/sync_codex_memory_data.py",
            "--database-dir",
            str(repo_root),
            "--build-atlas",
        ],
        cwd=repo_root,
    )


def create_icon_image():
    from PIL import Image, ImageDraw, ImageFilter

    canvas_size = 1024
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    mask = Image.new("L", (canvas_size, canvas_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, canvas_size, canvas_size), radius=224, fill=255)

    radial = Image.radial_gradient("L").resize((canvas_size, canvas_size), Image.Resampling.BICUBIC)
    inner = Image.new("RGBA", (canvas_size, canvas_size), (33, 55, 120, 255))
    outer = Image.new("RGBA", (canvas_size, canvas_size), (7, 9, 18, 255))
    base = Image.composite(outer, inner, radial)
    base.putalpha(mask)
    image.alpha_composite(base)

    glow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((166, 204, 858, 804), outline=(103, 232, 249, 110), width=42)
    glow_draw.ellipse((242, 240, 786, 782), outline=(167, 139, 250, 95), width=26)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    image.alpha_composite(glow)

    draw = ImageDraw.Draw(image)
    draw.arc((178, 220, 846, 802), 18, 336, fill=(103, 232, 249, 230), width=34)
    draw.arc((222, 252, 810, 784), 196, 20, fill=(244, 114, 182, 190), width=22)
    draw.arc((260, 214, 782, 786), 210, 33, fill=(167, 139, 250, 160), width=13)

    points = [(300, 606, 42), (438, 442, 34), (566, 578, 38), (716, 378, 46)]
    constellation_path = [(300, 606), (438, 442), (566, 578), (716, 378)]
    line_glow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    lg = ImageDraw.Draw(line_glow)
    lg.line(constellation_path, fill=(224, 242, 254, 170), width=42, joint="curve")
    line_glow = line_glow.filter(ImageFilter.GaussianBlur(12))
    image.alpha_composite(line_glow)
    draw.line(constellation_path, fill=(224, 242, 254, 235), width=28, joint="curve")
    for x, y, radius in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(248, 250, 252, 255))
        draw.ellipse(
            (x - radius - 15, y - radius - 15, x + radius + 15, y + radius + 15),
            outline=(125, 211, 252, 96),
            width=7,
        )

    for x, y, radius in [
        (194, 280, 8),
        (834, 280, 11),
        (804, 744, 8),
        (306, 802, 10),
        (512, 208, 7),
        (664, 820, 6),
        (248, 468, 5),
        (744, 596, 6),
    ]:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(125, 211, 252, 235))

    draw.ellipse((408, 408, 616, 616), outline=(255, 255, 255, 45), width=10)
    draw.ellipse((360, 360, 664, 664), outline=(103, 232, 249, 36), width=7)
    return image


def write_icon_png(source_image, path: Path, size: int) -> None:
    from PIL import Image

    canvas_size = 1024
    image = source_image
    if size != canvas_size:
        image = source_image.resize((size, size), Image.Resampling.LANCZOS)
    image.save(path, "PNG")


def create_app_icon(resources_dir: Path) -> bool:
    iconutil = shutil.which("iconutil")
    if not iconutil:
        if platform.system() == "Darwin":
            raise RuntimeError("iconutil is required to create the Memory Atlas macOS app icon")
        return False
    try:
        import PIL  # noqa: F401
    except Exception:
        if platform.system() == "Darwin":
            raise RuntimeError("Pillow is required to create the Memory Atlas macOS app icon")
        return False

    with tempfile.TemporaryDirectory() as temp_dir:
        iconset = Path(temp_dir) / f"{ICON_NAME}.iconset"
        iconset.mkdir()
        source_image = create_icon_image()
        for basename, size in [
            ("icon_16x16.png", 16),
            ("icon_16x16@2x.png", 32),
            ("icon_32x32.png", 32),
            ("icon_32x32@2x.png", 64),
            ("icon_128x128.png", 128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png", 256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png", 512),
            ("icon_512x512@2x.png", 1024),
        ]:
            write_icon_png(source_image, iconset / basename, size)
        subprocess.run(
            [iconutil, "-c", "icns", str(iconset), "-o", str(resources_dir / f"{ICON_NAME}.icns")],
            check=True,
        )
    return True


def prepare_static_runtime(repo_root: Path, keep_build_cache: bool = False, build_info_repo_root: Path | None = None) -> Path:
    app_dir = repo_root / "apps" / "memory-atlas"
    runtime_dir = runtime_root() / "runtime"
    staging_dir = runtime_root() / "runtime.next"
    build_info_repo_root = build_info_repo_root or repo_root
    try:
        refresh_memory_atlas_snapshot(repo_root)
        if not frontend_dependencies_ready(app_dir):
            clean_frontend_dependencies(app_dir)
            run_npm_ci(repo_root, app_dir)
        if not frontend_dependencies_ready(app_dir):
            raise RuntimeError(f"Memory Atlas frontend dependencies are incomplete after npm ci: {app_dir / 'node_modules'}")
        run_command(["npm", "run", "build", "--", "--emptyOutDir"], cwd=app_dir)
        dist_dir = app_dir / "dist"
        if not (dist_dir / "index.html").exists():
            raise RuntimeError(f"Memory Atlas build did not create expected index.html: {dist_dir}")

        if staging_dir.exists():
            remove_tree(staging_dir)
        runtime_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(dist_dir, staging_dir)

        atlas_data = repo_root / "data" / "derived" / "visualization" / "memory_atlas.json"
        if atlas_data.exists():
            shutil.copy2(atlas_data, staging_dir / "memory_atlas.json")
        write_runtime_build_info(build_info_repo_root, staging_dir)

        run_command(
            [
                "python3",
                "scripts/audit_memory_atlas_release.py",
                "--repo-root",
                str(repo_root),
                "--publish-dir",
                str(staging_dir),
            ],
            cwd=repo_root,
        )

        stop_existing_runtime_server()
        if runtime_dir.exists():
            remove_tree(runtime_dir)
        staging_dir.rename(runtime_dir)

        run_command(
            [
                "python3",
                "scripts/audit_memory_atlas_acceptance.py",
                "--repo-root",
                str(repo_root),
                "--publish-dir",
                str(runtime_dir),
            ],
            cwd=repo_root,
        )
        return runtime_dir
    finally:
        if staging_dir.exists():
            remove_tree(staging_dir)
        if not keep_build_cache:
            clean_frontend_build_cache(app_dir)


def build_launcher_script(repo_root: Path, original_repo_root: Path) -> str:
    quoted_repo = shell_quote(str(repo_root))
    quoted_original_repo = shell_quote(str(original_repo_root))
    installed_commit = shell_quote(git_commit(original_repo_root))
    return f"""#!/bin/zsh
set -euo pipefail

REPO_ROOT={quoted_repo}
ORIGINAL_REPO_ROOT={quoted_original_repo}
INSTALLED_GIT_COMMIT={installed_commit}
APP_DIR="$REPO_ROOT/apps/memory-atlas"
APP_SUPPORT="$HOME/Library/Application Support/OpenAIDatabase/MemoryAtlas"
RUNTIME_DIR="$APP_SUPPORT/runtime"
BUILD_INFO="$RUNTIME_DIR/memory_atlas_build.json"
STATUS_FILE="$APP_SUPPORT/launching.html"
PID_FILE="$APP_SUPPORT/server.pid"
WATCHDOG_PID_FILE="$APP_SUPPORT/server_watchdog.pid"
SERVER_SCRIPT="$APP_SUPPORT/memory_atlas_server.py"
SNAPSHOT="$REPO_ROOT/data/derived/visualization/memory_atlas.json"
LOG_DIR="$HOME/Library/Logs/OpenAIDatabase"
LOG_FILE="$LOG_DIR/memory-atlas-launcher.log"
PORT="${{MEMORY_ATLAS_PORT:-{DEFAULT_PORT}}}"
TTL_SECONDS="${{MEMORY_ATLAS_TTL_SECONDS:-7200}}"
IDLE_SECONDS="${{MEMORY_ATLAS_IDLE_SECONDS:-45}}"
REFRESH_TIMEOUT_SECONDS="${{MEMORY_ATLAS_REFRESH_TIMEOUT_SECONDS:-90}}"
URL="http://127.0.0.1:$PORT"

mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

notify_status() {{
  local message="$1"
  /usr/bin/osascript \\
    -e 'on run argv' \\
    -e 'display notification (item 1 of argv) with title "Memory Atlas"' \\
    -e 'end run' \\
    -- "$message" >/dev/null 2>&1 &!
}}

notify_error() {{
  local message="$1"
  /usr/bin/osascript \\
    -e 'on run argv' \\
    -e 'display dialog (item 1 of argv) buttons {{"OK"}} default button "OK" with icon caution' \\
    -e 'end run' \\
    -- "$message" >/dev/null 2>&1 || true
}}

write_status_page() {{
  mkdir -p "$APP_SUPPORT"
  cat > "$STATUS_FILE" <<EOF
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>记忆星图启动中</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #070912; color: #e5f6ff; font: 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ width: min(520px, calc(100vw - 48px)); }}
    .mark {{ width: 72px; height: 72px; border-radius: 22px; background: radial-gradient(circle at 50% 42%, #213778, #070912 72%); box-shadow: 0 0 42px rgba(103, 232, 249, .24); position: relative; margin-bottom: 22px; }}
    .mark::before {{ content: ""; position: absolute; inset: 17px 10px; border: 6px solid #67e8f9; border-right-color: #f472b6; border-radius: 50%; transform: rotate(-18deg); }}
    h1 {{ font-size: 28px; margin: 0 0 10px; letter-spacing: 0; }}
    p {{ margin: 0 0 18px; color: #9fb4c8; line-height: 1.6; }}
    a {{ color: #67e8f9; }}
  </style>
</head>
<body>
  <main>
    <div class="mark" aria-hidden="true"></div>
    <h1>记忆星图启动中</h1>
    <p>正在刷新最新脱敏数据快照并打开本地运行环境。服务准备好后，此页面会自动跳转到记忆星图。</p>
    <p><a href="$URL">打开记忆星图</a></p>
  </main>
  <script>
    const target = "$URL";
    async function ping() {{
      try {{
        await fetch(target + "/memory_atlas.json?snapshot=" + Date.now(), {{ mode: "no-cors", cache: "no-store" }});
        window.location.href = target;
      }} catch (error) {{
        window.setTimeout(ping, 800);
      }}
    }}
    window.setTimeout(ping, 300);
  </script>
</body>
</html>
EOF
}}

open_status_page() {{
  if [[ "${{MEMORY_ATLAS_NO_OPEN:-0}}" != "1" ]]; then
    write_status_page
    open "$STATUS_FILE"
  fi
}}

stop_watchdog() {{
  if [[ -f "$WATCHDOG_PID_FILE" ]]; then
    local watchdog_pid
    watchdog_pid="$(cat "$WATCHDOG_PID_FILE")"
    kill "$watchdog_pid" >/dev/null 2>&1 || true
    rm -f "$WATCHDOG_PID_FILE"
  fi
}}

is_managed_server() {{
  local pid="$1"
  local command_line
  command_line="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  [[ ( "$command_line" == *"memory_atlas_server.py"* && "$command_line" == *"$RUNTIME_DIR"* ) || ( "$command_line" == *"-m http.server"* && "$command_line" == *"$RUNTIME_DIR"* ) ]]
}}

write_runtime_server() {{
  mkdir -p "$APP_SUPPORT"
  cat > "$SERVER_SCRIPT" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


runtime_dir = Path(sys.argv[1]).resolve()
port = int(sys.argv[2])
ttl_seconds = int(sys.argv[3])
idle_seconds = int(sys.argv[4])
started_at = time.time()
last_seen_at = started_at
had_client = False
release_requested = False
released_at: float | None = None
shutdown_timer: threading.Timer | None = None
state_lock = threading.Lock()
httpd: ThreadingHTTPServer | None = None


def touch(client: bool = True) -> None:
    global had_client, last_seen_at
    with state_lock:
        last_seen_at = time.time()
        if client:
            had_client = True


def snapshot_mtime() -> int | None:
    snapshot = runtime_dir / "memory_atlas.json"
    if not snapshot.exists():
        return None
    return int(snapshot.stat().st_mtime)


def request_shutdown(reason: str) -> None:
    global had_client, last_seen_at, release_requested, released_at, shutdown_timer
    start_timer = False
    with state_lock:
        had_client = True
        last_seen_at = time.time()
        release_requested = True
        released_at = last_seen_at
        if shutdown_timer is None:
            start_timer = True
    if not start_timer:
        return
    sys.stderr.write("Memory Atlas server release requested (%s); shutting down.\\n" % reason)

    def shutdown_later() -> None:
        if httpd is not None:
            httpd.shutdown()

    timer = threading.Timer(0.2, shutdown_later)
    timer.daemon = True
    with state_lock:
        shutdown_timer = timer
    timer.start()


class MemoryAtlasHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request: object, client_address: object) -> None:
        exc_type, exc, _traceback = sys.exc_info()
        if exc_type in {{BrokenPipeError, ConnectionResetError}} or isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        if self.path.startswith("/memory_atlas.json") or self.path.startswith("/__memory_atlas"):
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("%s - - [%s] %s\\n" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_empty(self, status: int = 204) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/__memory_atlas_runtime_state":
            with state_lock:
                last_seen = int(last_seen_at)
                active = had_client
                released = release_requested
                release_epoch = int(released_at) if released_at else None
            self.send_json({{
                "status": "running",
                "pid": os.getpid(),
                "started_at_epoch": int(started_at),
                "last_seen_epoch": last_seen,
                "had_client": active,
                "release_requested": released,
                "released_at_epoch": release_epoch,
                "active_thread_count": threading.active_count(),
                "idle_seconds": idle_seconds,
                "ttl_seconds": ttl_seconds,
                "snapshot_mtime_epoch": snapshot_mtime(),
            }})
            return
        if path == "/memory_atlas.json":
            touch(True)
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/__memory_atlas_heartbeat":
            touch(True)
            self.send_empty()
            return
        if path == "/__memory_atlas_release":
            request_shutdown("page_release")
            self.send_empty()
            return
        self.send_error(404, "Not found")


def monitor_idle() -> None:
    while True:
        time.sleep(2)
        now = time.time()
        with state_lock:
            idle_for = now - last_seen_at
            client_seen = had_client
            release_seen = release_requested
        if release_seen:
            sys.stderr.write("Memory Atlas server release flag observed; shutting down.\\n")
            if httpd is not None:
                httpd.shutdown()
            return
        if ttl_seconds > 0 and now - started_at >= ttl_seconds:
            sys.stderr.write("Memory Atlas server reached TTL; shutting down.\\n")
            if httpd is not None:
                httpd.shutdown()
            return
        if client_seen and idle_seconds > 0 and idle_for >= idle_seconds:
            sys.stderr.write("Memory Atlas server idle after page close; shutting down.\\n")
            if httpd is not None:
                httpd.shutdown()
            return


def main() -> int:
    global httpd
    if not runtime_dir.exists():
        sys.stderr.write("runtime directory missing: %s\\n" % runtime_dir)
        return 1
    handler = partial(Handler, directory=str(runtime_dir))
    httpd = MemoryAtlasHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=monitor_idle, daemon=True).start()
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
  chmod 700 "$SERVER_SCRIPT"
}}

remember_existing_server() {{
  local pid
  pid="$(managed_server_pid_on_port)"
  if [[ -z "$pid" ]]; then
    return
  fi
  echo "$pid" > "$PID_FILE"
}}

managed_server_pid_on_port() {{
  if ! command -v lsof >/dev/null 2>&1; then
    return
  fi
  local pid
  pid="$(lsof -tiTCP:$PORT -sTCP:LISTEN | head -n 1 || true)"
  if [[ -n "$pid" ]] && is_managed_server "$pid"; then
    echo "$pid"
  fi
}}

stop_port_managed_server() {{
  local pid
  pid="$(managed_server_pid_on_port)"
  if [[ -z "$pid" ]]; then
    return
  fi
  echo "Stopping legacy Memory Atlas server PID $pid before starting heartbeat runtime."
  kill "$pid" >/dev/null 2>&1 || true
  sleep 1
  if kill -0 "$pid" >/dev/null 2>&1 && is_managed_server "$pid"; then
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi
}}

ensure_repo_access() {{
  if [[ ! -d "$REPO_ROOT" ]]; then
    notify_error "未找到 Memory Atlas 运行副本：$REPO_ROOT。请从终端重新安装：cd $ORIGINAL_REPO_ROOT && python3 scripts/install_memory_atlas_app.py"
    exit 1
  fi
  cd "$REPO_ROOT"
}}

current_git_commit() {{
  echo "$INSTALLED_GIT_COMMIT"
}}

runtime_git_commit() {{
  if [[ ! -f "$BUILD_INFO" ]]; then
    echo missing
    return
  fi
  python3 - "$BUILD_INFO" <<'PY'
import json
import sys
from pathlib import Path
try:
    print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("git_commit") or "missing")
except Exception:
    print("missing")
PY
}}

runtime_is_stale() {{
  if [[ ! -f "$RUNTIME_DIR/index.html" || ! -f "$RUNTIME_DIR/memory_atlas.json" || ! -f "$BUILD_INFO" ]]; then
    return 0
  fi
  local current_commit
  local runtime_commit
  current_commit="$(current_git_commit)"
  runtime_commit="$(runtime_git_commit)"
  [[ "$current_commit" != "unknown" && "$runtime_commit" != "$current_commit" ]]
}}

stop_managed_server() {{
  stop_watchdog
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    if [[ -n "$pid" && "$pid" != "$$" ]] && kill -0 "$pid" >/dev/null 2>&1 && is_managed_server "$pid"; then
      echo "Stopping stale Memory Atlas server PID $pid before runtime update."
      kill "$pid" >/dev/null 2>&1 || true
      sleep 1
      if kill -0 "$pid" >/dev/null 2>&1 && is_managed_server "$pid"; then
        kill -9 "$pid" >/dev/null 2>&1 || true
      fi
    fi
    rm -f "$PID_FILE"
  fi
}}

refresh_latest_snapshot() {{
  ensure_repo_access
  notify_status "正在刷新最新 Memory Atlas 数据快照..."
  echo "Refreshing latest Memory Atlas source data and redacted snapshot..."
  python3 - "$REFRESH_TIMEOUT_SECONDS" <<'PY'
import os
import signal
import subprocess
import sys
import time

timeout = int(sys.argv[1])
command = [
    "python3",
    "scripts/sync_codex_memory_data.py",
    "--database-dir",
    ".",
    "--build-atlas",
]
started_at = time.time()
process = subprocess.Popen(command, start_new_session=True)
try:
    return_code = process.wait(timeout=timeout if timeout > 0 else None)
except subprocess.TimeoutExpired:
    elapsed = int(time.time() - started_at)
    sys.stderr.write(f"Memory Atlas snapshot refresh exceeded {{timeout}}s after {{elapsed}}s; terminating refresh process group.\\n")
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    sys.exit(124)
sys.exit(return_code)
PY
  local refresh_status=$?
  if [[ "$refresh_status" -ne 0 ]]; then
    echo "Memory Atlas snapshot refresh failed or timed out with status $refresh_status."
    return "$refresh_status"
  fi
  if [[ ! -f "$SNAPSHOT" ]]; then
    echo "Memory Atlas snapshot file is still missing after refresh: $SNAPSHOT"
    return 1
  fi
}}

write_runtime_build_info() {{
  local target_build_info="${{1:-$BUILD_INFO}}"
  local target_snapshot="${{2:-$RUNTIME_DIR/memory_atlas.json}}"
  local snapshot_generated_at
  snapshot_generated_at="$(python3 - "$target_snapshot" <<'PY'
import json
import sys
from pathlib import Path
try:
    print(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")).get("overview", {{}}).get("generated_at") or "")
except Exception:
    print("")
PY
)"
  local current_commit
  current_commit="$INSTALLED_GIT_COMMIT"
  python3 - "$target_build_info" "$current_commit" "$snapshot_generated_at" "$target_snapshot" <<'PY'
import json
import sys
import time
from pathlib import Path
snapshot = Path(sys.argv[4])
Path(sys.argv[1]).write_text(json.dumps({{
    "schema_version": "memory_atlas_build.v1",
    "git_commit": sys.argv[2],
    "built_at_epoch": int(time.time()),
    "snapshot_generated_at": sys.argv[3],
    "snapshot_mtime_epoch": int(snapshot.stat().st_mtime) if snapshot.exists() else None,
}}, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
PY
}}

copy_latest_snapshot_to_runtime() {{
  if [[ ! -f "$RUNTIME_DIR/index.html" ]]; then
    return 1
  fi
  if ! refresh_latest_snapshot; then
    echo "Memory Atlas will keep serving the existing runtime snapshot because refresh did not complete."
    return 1
  fi
  cp "$SNAPSHOT" "$RUNTIME_DIR/memory_atlas.json"
  write_runtime_build_info
  if ! python3 scripts/audit_memory_atlas_release.py \\
    --repo-root . \\
    --publish-dir "$RUNTIME_DIR"; then
    notify_error "Memory Atlas 最新快照发布审计失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
  if ! python3 scripts/audit_memory_atlas_acceptance.py \\
    --repo-root . \\
    --publish-dir "$RUNTIME_DIR"; then
    notify_error "Memory Atlas 最新快照验收审计失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
}}

prepare_runtime() {{
  notify_status "正在准备本地运行环境，首次启动可能需要几分钟。"
  ensure_repo_access
  if ! refresh_latest_snapshot; then
    notify_error "Memory Atlas 无法刷新最新数据快照。请从终端重新安装运行副本：cd $ORIGINAL_REPO_ROOT && python3 scripts/install_memory_atlas_app.py"
    exit 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    notify_error "需要 npm 才能准备 Memory Atlas 本地运行环境。"
    exit 1
  fi
  if [[ ! -x "$APP_DIR/node_modules/.bin/vite" || ! -x "$APP_DIR/node_modules/.bin/tsc" || ! -f "$APP_DIR/node_modules/vite/dist/client/client.mjs" || ! -f "$APP_DIR/node_modules/lightningcss/package.json" || ! -f "$APP_DIR/node_modules/typescript/package.json" ]]; then
    rm -rf "$APP_DIR/node_modules"
    if [[ -d "$APP_DIR/node_modules" ]]; then
      notify_error "Memory Atlas 旧依赖清理失败，请查看日志：$LOG_FILE。"
      exit 1
    fi
    echo "Installing Memory Atlas frontend dependencies with npm ci..."
    local npm_cache="$APP_SUPPORT/npm-cache"
    rm -rf "$npm_cache"
    mkdir -p "$npm_cache"
    if ! npm ci --prefix "$APP_DIR" --cache "$npm_cache"; then
      rm -rf "$npm_cache"
      notify_error "Memory Atlas 依赖安装失败，请查看日志：$LOG_FILE。"
      exit 1
    fi
    rm -rf "$npm_cache"
  fi
  if [[ ! -x "$APP_DIR/node_modules/.bin/vite" || ! -x "$APP_DIR/node_modules/.bin/tsc" || ! -f "$APP_DIR/node_modules/vite/dist/client/client.mjs" || ! -f "$APP_DIR/node_modules/lightningcss/package.json" || ! -f "$APP_DIR/node_modules/typescript/package.json" ]]; then
    notify_error "Memory Atlas 依赖安装不完整，请查看日志：$LOG_FILE。"
    exit 1
  fi
  if ! (cd "$APP_DIR" && npm run build -- --emptyOutDir); then
    notify_error "Memory Atlas 本地运行环境构建失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
  local staged_runtime="$APP_SUPPORT/runtime.next"
  if [[ ! -f "$APP_DIR/dist/index.html" ]]; then
    notify_error "Memory Atlas 构建产物缺少 index.html，请查看日志：$LOG_FILE。"
    exit 1
  fi
  rm -rf "$staged_runtime"
  mkdir -p "$APP_SUPPORT"
  cp -R "$APP_DIR/dist" "$staged_runtime"
  cp "$SNAPSHOT" "$staged_runtime/memory_atlas.json"
  write_runtime_build_info "$staged_runtime/memory_atlas_build.json" "$staged_runtime/memory_atlas.json"
  if ! python3 scripts/audit_memory_atlas_release.py \\
    --repo-root . \\
    --publish-dir "$staged_runtime"; then
    notify_error "Memory Atlas 发布审计失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
  stop_managed_server
  rm -rf "$RUNTIME_DIR"
  mv "$staged_runtime" "$RUNTIME_DIR"
  if ! python3 scripts/audit_memory_atlas_acceptance.py \\
    --repo-root . \\
    --publish-dir "$RUNTIME_DIR"; then
    notify_error "Memory Atlas 验收审计失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
  rm -rf "$APP_DIR/node_modules" "$APP_DIR/dist" "$APP_DIR/tsconfig.tsbuildinfo"
  if [[ -d "$APP_DIR/node_modules" || -d "$APP_DIR/dist" || -f "$APP_DIR/tsconfig.tsbuildinfo" ]]; then
    notify_error "Memory Atlas 构建缓存清理失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
}}

echo "=== $(date -u '+%Y-%m-%dT%H:%M:%SZ') Memory Atlas launch ==="
notify_status "正在启动 Memory Atlas..."
open_status_page

if ! command -v python3 >/dev/null 2>&1; then
  notify_error "需要 python3 才能在本地运行 Memory Atlas。"
  exit 1
fi

if runtime_is_stale || [[ "${{MEMORY_ATLAS_REFRESH:-0}}" == "1" ]]; then
  prepare_runtime
else
  if ! copy_latest_snapshot_to_runtime; then
    echo "Using existing Memory Atlas runtime snapshot after refresh fallback."
    notify_status "Memory Atlas 将先使用现有快照打开；最新快照刷新未完成。"
  fi
fi

if [[ ! -f "$RUNTIME_DIR/memory_atlas.json" ]]; then
  notify_error "Memory Atlas 本地运行快照缺失。请从终端重新运行 scripts/install_memory_atlas_app.py 重建本地运行环境。"
  exit 1
fi

if curl -fsS "$URL/memory_atlas.json?snapshot=$(date +%s)" >/dev/null 2>&1; then
  if curl -fsS "$URL/__memory_atlas_runtime_state" >/dev/null 2>&1; then
    echo "Memory Atlas is already running at $URL"
    remember_existing_server
    echo "Status page will redirect to the running app."
    exit 0
  fi
  stop_port_managed_server
fi

echo "Starting Memory Atlas on $URL"
write_runtime_server
nohup python3 "$SERVER_SCRIPT" "$RUNTIME_DIR" "$PORT" "$TTL_SECONDS" "$IDLE_SECONDS" >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

for _ in {{1..80}}; do
  if curl -fsS "$URL/memory_atlas.json?snapshot=$(date +%s)" >/dev/null 2>&1; then
    echo "Memory Atlas ready at $URL"
    echo "Status page will redirect to the ready app."
    notify_status "Memory Atlas 已准备好。"
    exit 0
  fi
  if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    notify_error "Memory Atlas 启动失败，请查看日志：$LOG_FILE。"
    exit 1
  fi
  sleep 0.5
done

notify_error "Memory Atlas 在 40 秒内未准备好，请查看日志：$LOG_FILE。"
exit 1
"""


def install_app(target: Path, repo_root: Path, original_repo_root: Path) -> Path:
    target = target.expanduser().resolve()
    repo_root = repo_root.expanduser().resolve()
    original_repo_root = original_repo_root.expanduser().resolve()

    if target.exists():
        if target.name != APP_NAME or not target.is_dir():
            raise ValueError(f"Refusing to replace unexpected path: {target}")
        remove_tree(target)

    contents_dir = target / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    icon_created = create_app_icon(resources_dir)
    if platform.system() == "Darwin" and not icon_created:
        raise RuntimeError("Memory Atlas macOS app icon was not created")

    plist = {
        "CFBundleDisplayName": "Memory Atlas",
        "CFBundleExecutable": EXECUTABLE_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Memory Atlas",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": git_commit_count(original_repo_root),
        "LSMinimumSystemVersion": "13.0",
        "NSDocumentsFolderUsageDescription": "Memory Atlas 默认使用 Application Support 中的运行副本刷新脱敏快照，不需要每次打开访问 Documents 主仓库。",
        "NSHighResolutionCapable": True,
    }
    if icon_created:
        plist["CFBundleIconFile"] = ICON_NAME
    with (contents_dir / "Info.plist").open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=True)

    executable = macos_dir / EXECUTABLE_NAME
    executable.write_text(build_launcher_script(repo_root, original_repo_root), encoding="utf-8")
    executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    (contents_dir / "PkgInfo").write_text("APPL????", encoding="utf-8")
    clear_macos_metadata(target)
    ad_hoc_sign_app(target)
    refresh_launch_services(target)
    return target


def clear_macos_metadata(app_path: Path) -> None:
    xattr = shutil.which("xattr")
    if not xattr:
        return
    for attr in ("com.apple.quarantine", "com.apple.provenance"):
        subprocess.run([xattr, "-dr", attr, str(app_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ad_hoc_sign_app(app_path: Path) -> None:
    codesign = shutil.which("codesign")
    if not codesign:
        return
    subprocess.run(
        [codesign, "--force", "--deep", "--sign", "-", str(app_path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def refresh_launch_services(app_path: Path) -> None:
    app_path.touch()
    lsregister = Path("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister")
    if lsregister.exists():
        subprocess.run([str(lsregister), "-f", str(app_path)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Memory Atlas macOS app launchers.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="OpenAIDatabase repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        action="append",
        help="Target .app bundle path. Can be provided more than once. Defaults to Downloads and /Applications.",
    )
    parser.add_argument(
        "--skip-runtime",
        action="store_true",
        help="Only install app bundles; do not build the static runtime.",
    )
    parser.add_argument(
        "--keep-build-cache",
        action="store_true",
        help="Keep node_modules, dist, and tsbuildinfo after preparing the static runtime.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    if not (repo_root / "apps" / "memory-atlas" / "package.json").exists():
        raise SystemExit(f"Memory Atlas package not found under repo root: {repo_root}")

    source_repo_root = sync_source_workspace(repo_root)
    targets = args.target or default_targets()
    installed = [install_app(target, source_repo_root, repo_root) for target in targets]
    if not args.skip_runtime:
        runtime_dir = prepare_static_runtime(source_repo_root, keep_build_cache=args.keep_build_cache, build_info_repo_root=repo_root)
        print(runtime_dir)
    for path in installed:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
