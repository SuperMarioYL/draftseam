"""Bundle-consistency checks for a 剪映/CapCut ``.draft``.

The v0.2 roadmap line asks for a consistency check between ``draft_info.json``
(the encrypted persisted form) and ``template.tmp``. ``draft_info.json`` is
base64/AES-encrypted and opacity is a hard product boundary — it is never
decoded — so a byte-level comparison is impossible without decryption. What
*is* checkable without decrypting is the surface draftseam owns:
``template.tmp``'s internal consistency, i.e. the referential and temporal
relations an agent's edits must preserve:

* every segment's ``material_id`` resolves into some materials bucket,
* every segment's ``track_id`` back-references the track it sits on,
* ``source_timerange`` / ``target_timerange`` carry non-negative values,
* ``draft.duration`` (when set) covers the last segment end.

The rules are deliberately structural — they validate relations, not 剪映-app
semantics, so an ``OK`` result means "internally consistent", never "guaranteed
to reopen in 剪映".
"""

from __future__ import annotations

from typing import Any, Optional

from .bundle import DraftBundle
from .parser import parse_bundle
from .schema import Draft, Materials, Track


def _material_ids(materials: Materials) -> set[str]:
    """All material ids across every bucket — typed and extra.

    Extras matter: 剪映 keeps many buckets draftseam does not model
    (``stickers``, ``shapes``, ...), and their entries are referenced by
    segments exactly like the typed ones; restricting the check to the typed
    buckets would false-positive on a perfectly valid draft.
    """
    ids: set[str] = set()
    for name in ("videos", "audios", "texts", "effects", "video_effects", "transitions"):
        for mat in getattr(materials, name):
            if mat.id:
                ids.add(mat.id)
    extras: dict[str, Any] = materials.model_extra or {}
    for value in extras.values():
        if not isinstance(value, list):
            continue
        for entry in value:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                ids.add(entry["id"])
    return ids


def _timerange_problems(track_i: int, seg_i: int, seg, range_name: str) -> list[str]:
    tr = getattr(seg, range_name, None)
    if tr is None:
        return []
    path = f"tracks[{track_i}].segments[{seg_i}].{range_name}"
    problems = []
    if tr.duration is not None and tr.duration < 0:
        problems.append(f"{path}.duration is negative ({tr.duration})")
    if tr.offset is not None and tr.offset < 0:
        problems.append(f"{path}.offset is negative ({tr.offset})")
    return problems


def _track_problems(track: Track, track_i: int, material_ids: set[str]) -> list[str]:
    problems = []
    for seg_i, seg in enumerate(track.segments):
        path = f"tracks[{track_i}].segments[{seg_i}]"
        if seg.material_id and seg.material_id not in material_ids:
            problems.append(
                f"{path}.material_id {seg.material_id} not found in any materials bucket"
            )
        if seg.track_id is not None and track.id is not None and seg.track_id != track.id:
            problems.append(
                f"{path}.track_id {seg.track_id} does not match its track id {track.id}"
            )
        problems.extend(_timerange_problems(track_i, seg_i, seg, "source_timerange"))
        problems.extend(_timerange_problems(track_i, seg_i, seg, "target_timerange"))
    return problems


def _duration_problem(draft: Draft) -> Optional[str]:
    """draft.duration, when set, must cover the last segment end."""
    if not draft.duration or draft.duration <= 0:
        return None
    last_end = 0
    for track in draft.tracks:
        for seg in track.segments:
            tr = seg.target_timerange
            if tr is None or tr.duration is None or tr.offset is None:
                continue
            last_end = max(last_end, tr.offset + tr.duration)
    if last_end > draft.duration:
        return (
            f"duration ({draft.duration}) is shorter than the last segment end "
            f"({last_end})"
        )
    return None


def check_draft(draft: Draft) -> list[str]:
    """Return a list of consistency problems in a parsed :class:`Draft`.

    An empty list means the draft is internally consistent (referential
    integrity, timerange sanity, duration coverage) — not that 剪映 is
    guaranteed to reopen it.
    """
    material_ids = _material_ids(draft.materials)
    problems: list[str] = []
    for track_i, track in enumerate(draft.tracks):
        problems.extend(_track_problems(track, track_i, material_ids))
    duration_problem = _duration_problem(draft)
    if duration_problem:
        problems.append(duration_problem)
    return problems


def check_bundle(bundle: DraftBundle) -> list[str]:
    """Read + parse a bundle's ``template.tmp`` and check its consistency.

    Raises DraftBundleError / ValueError (via parse) for an unreadable bundle
    — the CLI maps those to its clean exit-2 error contract.
    """
    return check_draft(parse_bundle(bundle))


__all__ = ["check_bundle", "check_draft"]
