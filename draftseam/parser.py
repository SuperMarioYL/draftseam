"""``template.tmp`` JSON -> :class:`draftseam.schema.Draft` model.

There is no binary codec. The on-disk document is plain JSON; this module
lifts it into a tolerant pydantic model (``extra="allow"``) that preserves
every 剪映 key draftseam does not explicitly model.
"""

from __future__ import annotations

from typing import Any

from .bundle import DraftBundle
from .schema import Draft


def parse_dict(data: dict[str, Any]) -> Draft:
    """Build a :class:`Draft` model from a parsed ``template.tmp`` dict."""
    return Draft.model_validate(data)


def parse_bundle(bundle: DraftBundle) -> Draft:
    """Read ``template.tmp`` from ``bundle`` and return a :class:`Draft`."""
    return parse_dict(bundle.read_template())


def parse_path(path: str) -> Draft:
    """Convenience: parse a draft bundle directory path into a :class:`Draft`."""
    return parse_bundle(DraftBundle.resolve(path))
