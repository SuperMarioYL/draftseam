""" :class:`draftseam.schema.Draft` model -> ``template.tmp`` JSON (round-trip safe).

``model_dump(exclude_unset=True)`` on an ``extra="allow"`` pydantic model emits
the extra keys back plus exactly the fields present in the source, so a parse ->
no-op write -> re-read is JSON-identical: keys 剪映 wrote but draftseam does not
model survive verbatim (extras), and modelled fields absent from the source are
NOT injected. ``ensure_ascii=False`` keeps CJK 字幕 text intact.

``exclude_unset`` is safe for edits made through the model: validation marks
every source key as set, attribute assignment after parse (e.g.
``_bump_duration``) marks the assigned field as set, and agent-inserted
materials/segments carry exactly their constructed fields.
"""

from __future__ import annotations

from typing import Any

from .bundle import DraftBundle
from .schema import Draft


def draft_to_dict(draft: Draft) -> dict[str, Any]:
    """Lower a :class:`Draft` model to a ``template.tmp``-shaped dict.

    Uses ``model_dump(exclude_unset=True)`` so both explicitly-modelled fields
    and preserved extras are emitted, round-tripping 剪映's own keys losslessly
    without adding keys the source draft never had (a plain ``model_dump``
    would inject every modelled-but-absent field, e.g. ``"mix": null`` on
    every track).
    """
    return draft.model_dump(exclude_unset=True)


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
