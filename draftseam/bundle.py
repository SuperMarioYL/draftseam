"""Directory-bundle I/O for a 剪映/CapCut ``.draft``.

A 剪映 draft on macOS is a **directory bundle** at
``~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/<project-name>/``.
It contains, among other files:

* ``template.tmp`` — **plain JSON** holding ``version`` + ``tracks`` +
  ``materials`` (+ many other keys). This is the document draftseam parses and
  writes. There is no binary codec, no varint, no length-prefix.
* ``draft_info.json`` — a base64 / likely-AES-encrypted persisted form.
  Treated as **opaque**: copied byte-for-byte if present, never decrypted.
* assorted plain-JSON siblings (``draft_meta_info.json`` (encrypted),
  ``draft_agency_config.json``, ``key_value.json``, ``draft_settings`` (INI),
  ``timeline_layout.json``, ...). draftseam does not touch these.

The only file draftseam reads/writes is ``template.tmp``; the rest of the
bundle is left alone so the project still reopens in 剪映.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

# The single file inside a draft bundle that draftseam owns.
TEMPLATE_TMP = "template.tmp"
# Encrypted persisted form — opaque, never decoded.
DRAFT_INFO_JSON = "draft_info.json"

# Default macOS location for 剪映 draft projects.
DEFAULT_DRAFT_ROOT = Path.home() / "Movies" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft"


class DraftBundleError(Exception):
    """Raised when a draft bundle is missing or malformed on disk."""


class DraftBundle:
    """A handle to a 剪映 draft directory bundle.

    Usage::

        bundle = DraftBundle("/path/to/project/")
        raw = bundle.read_template()      # -> dict (parsed template.tmp JSON)
        bundle.write_template(raw)       # round-trips the dict back to disk

    ``draft_info.json`` (and the encrypted ``draft_meta_info.json``) are
    treated as opaque blobs — draftseam never interprets them.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path).expanduser().resolve()

    # ------------------------------------------------------------------ paths
    @property
    def template_path(self) -> Path:
        return self.path / TEMPLATE_TMP

    @property
    def draft_info_path(self) -> Path:
        return self.path / DRAFT_INFO_JSON

    @property
    def name(self) -> str:
        """The project name (the bundle directory's basename)."""
        return self.path.name

    # -------------------------------------------------------------- existence
    def exists(self) -> bool:
        """True if the directory and its ``template.tmp`` are present."""
        return self.path.is_dir() and self.template_path.is_file()

    def require(self) -> None:
        if not self.path.is_dir():
            raise DraftBundleError(f"not a draft bundle directory: {self.path}")
        if not self.template_path.is_file():
            raise DraftBundleError(
                f"missing {TEMPLATE_TMP} in bundle: {self.template_path}"
            )

    # ---------------------------------------------------------------- finders
    @staticmethod
    def resolve(path: str | os.PathLike[str]) -> "DraftBundle":
        """Resolve a bundle from a path that may be absolute or a project name.

        A bare project name like ``"2月18日"`` resolves under the default
        剪映 projects root on this machine; an absolute/relative path is used
        verbatim.
        """
        p = Path(path).expanduser()
        if not p.is_absolute() and "/" not in str(path) and not p.exists():
            candidate = DEFAULT_DRAFT_ROOT / str(path)
            if candidate.is_dir():
                p = candidate
        bundle = DraftBundle(p)
        bundle.require()
        return bundle

    @staticmethod
    def default_root() -> Path:
        """The default 剪映 projects directory for this user, if present."""
        return DEFAULT_DRAFT_ROOT

    @staticmethod
    def list_projects(root: Optional[Path] = None) -> list[str]:
        """List project bundle names under the (default) projects root."""
        root = root or DEFAULT_DRAFT_ROOT
        if not root.is_dir():
            return []
        names = []
        for entry in sorted(root.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir() and (entry / TEMPLATE_TMP).is_file():
                names.append(entry.name)
        return names

    # ----------------------------------------------------------- template.tmp
    def read_template(self) -> dict[str, Any]:
        """Read and parse ``template.tmp`` as a Python ``dict``.

        The file is plain JSON — no decryption, no binary decode.
        """
        self.require()
        with self.template_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def write_template(self, data: dict[str, Any]) -> None:
        """Write a dict back to ``template.tmp`` as compact JSON.

        A ``.bak`` of the previous file is kept for one generation. The JSON is
        written with ``ensure_ascii=False`` so CJK 字幕 text round-trips
        verbatim, and keys are preserved in insertion order (CPython dict
        order) so a no-op write stays diff-stable.
        """
        self.path.mkdir(parents=True, exist_ok=True)
        if self.template_path.is_file():
            bak = self.template_path.with_name(TEMPLATE_TMP + ".bak")
            bak.write_bytes(self.template_path.read_bytes())
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        self.template_path.write_text(text, encoding="utf-8")

    # ----------------------------------------------------- draft_info.json
    def read_draft_info_bytes(self) -> Optional[bytes]:
        """Return the raw encrypted bytes of ``draft_info.json`` if present.

        Opaque: never decoded, never re-encoded. Only present so callers can
        see the file exists; draftseam does not modify it.
        """
        if not self.draft_info_path.is_file():
            return None
        return self.draft_info_path.read_bytes()

    # ------------------------------------------------------------- siblings
    def sibling_files(self) -> list[Path]:
        """Other top-level files in the bundle (excluding template.tmp)."""
        if not self.path.is_dir():
            return []
        return [
            p
            for p in sorted(self.path.iterdir())
            if p.is_file() and p.name != TEMPLATE_TMP
        ]

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"DraftBundle({self.path!s})"
