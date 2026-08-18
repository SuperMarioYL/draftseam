"""Pydantic types for the 剪映/CapCut ``.draft`` timeline model.

All models use ``extra="allow"`` so that fields 剪映 writes which draftseam does
not explicitly model are preserved through a parse → write round-trip. This is
the format-asset moat: own parse/write of the undocumented ``template.tmp``
JSON without losing any of 剪映's own keys on the way back to disk.

The on-disk shape (verified against JianyingPro 75.0.0 on macOS) is a *plain
JSON* document at ``template.tmp`` with top-level ``version`` (int, e.g.
``360000``), ``fps`` (float, e.g. ``30.0``), ``duration`` (microseconds),
``tracks`` (list) and ``materials`` (a dict of typed lists). Segment-level
field names are *unverified* against populated drafts (local samples are
empty, ``duration == 0``) — hence the tolerant, extra-allowing models here.

字幕 (subtitles) are ``materials.texts`` entries referenced by segments on a
text track — there is no dedicated "Subtitle" track type. Effects are split
across ``materials.effects`` / ``materials.video_effects`` /
``materials.transitions``.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# Time values inside a 剪映 draft are microseconds (1_000_000 == 1.0s at any
# fps). The CLI surface accepts human-friendly seconds and converts.
MICROS_PER_SECOND: int = 1_000_000


class _TolerantModel(BaseModel):
    """Base model: tolerate every unknown key 剪映 may add.

    ``extra="allow"`` stores unknown fields in ``__pydantic_extra__`` and
    ``model_dump()`` emits them again, so a round-trip is lossless for keys
    draftseam does not explicitly model.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class TimeRange(_TolerantModel):
    """A ``{duration, offset}`` timerange (microseconds).

    Used as ``source_timerange`` (window into the source media) and
    ``target_timerange`` (window on the timeline) on segments.
    """

    duration: Optional[int] = None
    offset: Optional[int] = None


class Segment(_TolerantModel):
    """A single clip on a track.

    Field names below are the *commonly observed* ones; because segment-level
    fields are unverified against populated drafts, the model is tolerant of
    anything 剪映 actually writes. The two load-bearing refs for agent edits
    are ``material_id`` (points into ``materials.<kind>``) and
    ``target_timerange`` (places the clip on the timeline).
    """

    id: Optional[str] = None
    track_id: Optional[str] = None
    material_id: Optional[str] = None
    source_timerange: Optional[TimeRange] = None
    target_timerange: Optional[TimeRange] = None
    source: Optional[int] = None
    common_keyframe_refs: list[Any] = Field(default_factory=list)
    animation_entries: list[Any] = Field(default_factory=list)
    is_placeholder: Optional[bool] = None
    render_index: Optional[int] = None
    extra_transform: Optional[dict[str, Any]] = None
    clip: Optional[dict[str, Any]] = None
    responsive_layout: Optional[dict[str, Any]] = None


class Track(_TolerantModel):
    """A timeline track (video / audio / text / effect / sticker / ...).

    ``type`` is the 剪映 track type string (``"video"``, ``"audio"``,
    ``"text"``, ``"effect"``, ``"sticker"``, ``"filter"`` ...). 字幕 live on a
    text track whose segments reference ``materials.texts`` entries.
    """

    id: Optional[str] = None
    type: Optional[str] = None
    segments: list[Segment] = Field(default_factory=list)
    flag: Optional[int] = None
    render_index: Optional[int] = None
    attribute: Optional[int] = None
    mix: Optional[bool] = None


class VideoMaterial(_TolerantModel):
    id: Optional[str] = None
    type: Optional[str] = None
    path: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    is_tone_adjust: Optional[bool] = None


class AudioMaterial(_TolerantModel):
    id: Optional[str] = None
    type: Optional[str] = None
    path: Optional[str] = None
    duration: Optional[int] = None
    name: Optional[str] = None


class TextMaterial(_TolerantModel):
    """A 字幕 / text material entry in ``materials.texts``.

    The ``content`` blob carries the rich text payload 剪映 reads back; the
    convenience ``text`` field holds the plain subtitle string draftseam writes
    when inserting a 字幕.
    """

    id: Optional[str] = None
    type: Optional[str] = None
    text: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    text_size: Optional[float] = None
    text_color: Optional[str] = None
    font_path: Optional[str] = None
    font_size: Optional[float] = None
    font_id: Optional[str] = None
    font_resource_id: Optional[str] = None
    font_team_id: Optional[str] = None
    base_content: Optional[str] = None


class EffectMaterial(_TolerantModel):
    id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    duration: Optional[int] = None


class VideoEffectMaterial(_TolerantModel):
    id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    duration: Optional[int] = None


class TransitionMaterial(_TolerantModel):
    id: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    duration: Optional[int] = None
    path: Optional[str] = None


class Materials(_TolerantModel):
    """The ``materials`` dict on a draft.

    The six load-bearing buckets are typed; the *many* other buckets 剪映
    writes (``ai_translates``, ``audio_balances``, ``beats``, ``canvases``,
    ``masks``, ``stickers``, ``speeds``, ``shapes``, ... — 40+ in 75.0.0) are
    preserved as extras by ``extra="allow"`` and round-trip untouched.
    """

    videos: list[VideoMaterial] = Field(default_factory=list)
    audios: list[AudioMaterial] = Field(default_factory=list)
    texts: list[TextMaterial] = Field(default_factory=list)
    effects: list[EffectMaterial] = Field(default_factory=list)
    video_effects: list[VideoEffectMaterial] = Field(default_factory=list)
    transitions: list[TransitionMaterial] = Field(default_factory=list)


class CanvasConfig(_TolerantModel):
    background: Any = None
    height: Optional[int] = None
    ratio: Optional[str] = None
    width: Optional[int] = None


class Draft(_TolerantModel):
    """The top-level 剪映 draft timeline model.

    ``version`` is the 剪映 internal schema version int (e.g. ``360000``);
    ``new_version`` is the editor product version string (e.g. ``"75.0.0"``).
    ``duration`` and all segment timeranges are microseconds.
    """

    version: Optional[int] = None
    new_version: Optional[str] = None
    fps: Optional[float] = None
    duration: Optional[int] = None
    id: Optional[str] = None
    name: Optional[str] = None
    canvas_config: Optional[CanvasConfig] = None
    tracks: list[Track] = Field(default_factory=list)
    materials: Materials = Field(default_factory=Materials)
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    source: Optional[str] = None
    path: Optional[str] = None


__all__ = [
    "MICROS_PER_SECOND",
    "_TolerantModel",
    "TimeRange",
    "Segment",
    "Track",
    "VideoMaterial",
    "AudioMaterial",
    "TextMaterial",
    "EffectMaterial",
    "VideoEffectMaterial",
    "TransitionMaterial",
    "Materials",
    "CanvasConfig",
    "Draft",
]
