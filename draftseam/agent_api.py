"""Agent-callable timeline primitives.

These verbs let a coding agent (e.g. Claude Code) manipulate a 剪映 draft
model without touching JSON directly. Each operates **in place** on a
:class:`draftseam.schema.Draft` (mutating ``tracks`` / ``materials``); call
:func:`draftseam.writer.write_bundle` afterwards to persist.

Time arguments are **seconds** (human-friendly); they are converted to the
microsecond integers 剪映 stores internally. 字幕 (subtitles) are
``materials.texts`` entries referenced by segments on a text track — there is
no "Subtitle" track type, so :func:`insert_subtitle` both appends a text
material *and* adds a referencing segment on a text track (creating one if the
draft has none).
"""

from __future__ import annotations

import uuid
from typing import Optional

from .schema import (
    MICROS_PER_SECOND,
    AudioMaterial,
    Draft,
    Segment,
    TextMaterial,
    TimeRange,
    Track,
    TransitionMaterial,
)

# 剪映 track type strings.
TRACK_TEXT = "text"
TRACK_AUDIO = "audio"
TRACK_VIDEO = "video"


def new_id() -> str:
    """A 剪映-style uppercase GUID (e.g. ``F2DAE6E6-9AA1-40F8-B87E-2AC5CB52D371``)."""
    return str(uuid.uuid4()).upper()


def _seconds_to_micros(seconds: float) -> int:
    return int(round(seconds * MICROS_PER_SECOND))


def _bump_duration(draft: Draft, end_micros: int) -> None:
    """Ensure ``draft.duration`` covers ``end_micros`` if it is set."""
    if end_micros <= 0:
        return
    cur = draft.duration or 0
    if end_micros > cur:
        draft.duration = end_micros


def _ensure_track(draft: Draft, track_type: str) -> Track:
    """Return the first track of ``track_type``, creating one if absent."""
    for tr in draft.tracks:
        if tr.type == track_type:
            return tr
    track = Track(id=new_id(), type=track_type, segments=[])
    draft.tracks.append(track)
    return track


def insert_subtitle(
    draft: Draft,
    text: str,
    start: float,
    dur: float,
    *,
    text_size: Optional[float] = None,
    text_color: Optional[str] = None,
    material_id: Optional[str] = None,
) -> str:
    """Append a 字幕 (subtitle) to ``materials.texts`` + a referencing segment.

    Args:
        draft: the draft model to mutate in place.
        text: the subtitle string (CJK or plain).
        start: timeline start in seconds.
        dur: on-screen duration in seconds.
        text_size / text_color: optional styling stored on the text material.
        material_id: explicit material id (else a fresh GUID is generated).

    Returns:
        The text material id (useful for the agent to reference later).
    """
    mat_id = material_id or new_id()
    material = TextMaterial(
        id=mat_id,
        type="text",
        text=text,
        text_size=text_size,
        text_color=text_color,
    )
    draft.materials.texts.append(material)

    offset = _seconds_to_micros(start)
    duration = _seconds_to_micros(dur)
    track = _ensure_track(draft, TRACK_TEXT)
    seg = Segment(
        id=new_id(),
        track_id=track.id,
        material_id=mat_id,
        source_timerange=TimeRange(duration=duration, offset=0),
        target_timerange=TimeRange(duration=duration, offset=offset),
        source=0,
        is_placeholder=False,
    )
    track.segments.append(seg)

    _bump_duration(draft, offset + duration)
    return mat_id


def add_voiceover(
    draft: Draft,
    path: str,
    start: float,
    dur: float,
    *,
    name: Optional[str] = None,
    material_id: Optional[str] = None,
) -> str:
    """Append a 配音 (voiceover) audio material + segment at ``start`` seconds."""
    mat_id = material_id or new_id()
    material = AudioMaterial(
        id=mat_id,
        type="audio",
        path=path,
        duration=_seconds_to_micros(dur),
        name=name or path,
    )
    draft.materials.audios.append(material)

    offset = _seconds_to_micros(start)
    duration = _seconds_to_micros(dur)
    track = _ensure_track(draft, TRACK_AUDIO)
    seg = Segment(
        id=new_id(),
        track_id=track.id,
        material_id=mat_id,
        source_timerange=TimeRange(duration=duration, offset=0),
        target_timerange=TimeRange(duration=duration, offset=offset),
        source=0,
        is_placeholder=False,
    )
    track.segments.append(seg)
    _bump_duration(draft, offset + duration)
    return mat_id


def add_transition(
    draft: Draft,
    name: str,
    duration: float,
    *,
    material_id: Optional[str] = None,
    path: Optional[str] = None,
) -> str:
    """Append a transition material entry to ``materials.transitions``.

    Transitions in 剪映 live in ``materials.transitions`` and are referenced
    between adjacent segments on the timeline. This primitive owns the material
    entry (the format-asset seam); linking it to a specific segment boundary is
    left to the agent once segment ids are known.
    """
    mat_id = material_id or new_id()
    material = TransitionMaterial(
        id=mat_id,
        type="transition",
        name=name,
        duration=_seconds_to_micros(duration),
        path=path,
    )
    draft.materials.transitions.append(material)
    return mat_id


__all__ = [
    "new_id",
    "insert_subtitle",
    "add_voiceover",
    "add_transition",
]
