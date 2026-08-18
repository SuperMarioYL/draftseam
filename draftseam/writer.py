""" :class:`draftseam.schema.Draft` model -> ``template.tmp`` JSON (round-trip safe).

``model_dump()`` on an ``extra="allow"`` pydantic model emits the extra keys
back, so a parse -> no-op write -> re-parse is semantically identical (same
tracks, same materials buckets and counts). ``ensure_ascii=False`` keeps CJK
字幕 text intact.
"""

from __future__ import annotations

from typing import Any

from .bundle import DraftBundle
from .schema import Draft


def draft_to_dict(draft: Draft) -> dict[str, Any]:
    """Lower a :class:`Draft` model to a ``template.tmp``-shaped dict.

    Uses ``model_dump()`` so both explicitly-modelled fields and preserved
    extras are emitted, round-tripping 剪映's own keys losslessly.
    """
    return draft.model_dump()


def write_bundle(draft: Draft, bundle: DraftBundle) -> None:
    """Write a :class:`Draft` back into a bundle's ``template.tmp``."""
    bundle.write_template(draft_to_dict(draft))


def round_trip(bundle: DraftBundle) -> Draft:
    """Parse -> no-op write -> re-parse a bundle; returns the re-parsed draft.

    Used by the round-trip test to prove semantic identity.
    """
    from .parser import parse_bundle

    draft = parse_bundle(bundle)
    write_bundle(draft, bundle)
    return parse_bundle(bundle)
