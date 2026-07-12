from pathlib import Path
from typing import Iterable, Optional


class ArtifactSnapshot:
    """Restore fixed-path public artifacts after generator-backed tests."""

    def __init__(self, paths: Iterable[str]) -> None:
        self._contents: dict[Path, Optional[bytes]] = {}
        for path_text in paths:
            path = Path(path_text)
            self._contents[path] = path.read_bytes() if path.is_file() else None

    def restore(self) -> None:
        for path, content in self._contents.items():
            if content is None:
                if path.is_file():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
