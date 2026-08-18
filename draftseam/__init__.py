"""draftseam — read/write 剪映/CapCut ``.draft`` timelines for coding agents.

draftseam lets a coding agent (Claude Code) read a 剪映 native ``.draft``
timeline as structured data, insert 字幕/配音/转场 tracks, and write it back
as a fully editable native timeline that reopens in 剪映 — no MP4 round-trip,
no layer structure lost.

The format-asset moat is owning parse/write of 剪映's undocumented ``.draft``
format: a directory bundle whose ``template.tmp`` is plain JSON.
"""

from __future__ import annotations

from .agent_api import add_transition, add_voiceover, insert_subtitle, new_id
from .bundle import DraftBundle, DraftBundleError
from .parser import parse_bundle, parse_dict, parse_path
from .schema import Draft, Materials, Segment, Track
from .writer import draft_to_dict, write_bundle

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "DraftBundle",
    "DraftBundleError",
    "Draft",
    "Materials",
    "Track",
    "Segment",
    "parse_bundle",
    "parse_dict",
    "parse_path",
    "write_bundle",
    "draft_to_dict",
    "insert_subtitle",
    "add_voiceover",
    "add_transition",
    "new_id",
]
