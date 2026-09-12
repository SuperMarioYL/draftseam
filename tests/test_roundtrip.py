"""Round-trip test: parse ``template.tmp`` -> no-op write -> re-parse == identical.

Proves draftseam owns the format seam: a no-op write is semantically identical
(same tracks, same materials buckets and counts, same version/fps/duration),
so a draft written back reopens in 剪映 with nothing lost.
"""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

from draftseam.bundle import DraftBundle
from draftseam.parser import parse_bundle
from draftseam.writer import draft_to_dict, write_bundle

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_project"


def _copy_fixture(tmp_path: Path) -> Path:
    """Copy the read-only fixture into tmp_path so writes don't mutate the repo."""
    dst = tmp_path / "sample_project"
    shutil.copytree(FIXTURE, dst)
    return dst


def test_roundtrip_semantically_identical(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)

    original_raw = bundle.read_template()
    draft1 = parse_bundle(bundle)

    # no-op write: model -> template.tmp
    write_bundle(draft1, bundle)

    # re-parse the written file
    written_raw = bundle.read_template()
    draft2 = parse_bundle(bundle)

    # --- top-level scalars identical ---
    assert draft2.version == draft1.version == 360000
    assert draft2.fps == draft1.fps == 30.0
    assert draft2.duration == draft1.duration

    # --- tracks: same count, same types, same segment counts ---
    assert len(draft2.tracks) == len(draft1.tracks)
    for t1, t2 in zip(draft1.tracks, draft2.tracks):
        assert t2.type == t1.type
        assert len(t2.segments) == len(t1.segments)
        for s1, s2 in zip(t1.segments, t2.segments):
            assert s2.material_id == s1.material_id
            assert s2.target_timerange == s1.target_timerange

    # --- materials: every original bucket still present, same counts ---
    m1, m2 = draft1.materials, draft2.materials
    assert len(m2.videos) == len(m1.videos)
    assert len(m2.audios) == len(m1.audios)
    assert len(m2.texts) == len(m1.texts)
    assert len(m2.effects) == len(m1.effects)
    assert len(m2.video_effects) == len(m1.video_effects)
    assert len(m2.transitions) == len(m1.transitions)

    # every materials key in the original JSON survived the round-trip
    assert set(written_raw["materials"].keys()) == set(original_raw["materials"].keys())

    # --- the dump of the re-parsed model deep-equals the dump of the first ---
    assert draft_to_dict(draft2) == draft_to_dict(draft1)


def test_roundtrip_preserves_unknown_segment_extras(tmp_path: Path) -> None:
    """extra="allow" must keep unmodelled fields (e.g. segment.cartoon_name)."""
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft1 = parse_bundle(bundle)
    seg = draft1.tracks[0].segments[0]
    # the fixture writes a `cartoon_name` extra on every segment; extra="allow"
    # must preserve it through parse, and through write -> re-parse
    assert seg.model_dump().get("cartoon_name") == ""

    write_bundle(draft1, bundle)
    draft2 = parse_bundle(bundle)
    seg2 = draft2.tracks[0].segments[0]
    assert seg2.model_dump().get("cartoon_name") == seg.model_dump().get("cartoon_name")


def test_write_does_not_touch_draft_info(tmp_path: Path) -> None:
    """draft_info.json is opaque — a write must not change it."""
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    before = bundle.draft_info_path.read_bytes()
    draft = parse_bundle(bundle)
    write_bundle(draft, bundle)
    after = bundle.draft_info_path.read_bytes()
    assert before == after


def test_noop_write_is_raw_json_identical(tmp_path: Path) -> None:
    """v0.2 fidelity contract: a no-op write leaves template.tmp JSON deep-equal.

    v0.1 used a plain model_dump() and injected every modelled-but-absent
    field — e.g. ``"mix": null`` appeared on every track that never had one.
    """
    import json

    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    original_raw = bundle.read_template()

    draft = parse_bundle(bundle)
    write_bundle(draft, bundle)

    written_raw = bundle.read_template()
    assert written_raw == original_raw
    # the v0.1 regression, pinned explicitly: no injected "mix" keys
    for i, (orig_track, written_track) in enumerate(
        zip(original_raw["tracks"], written_raw["tracks"])
    ):
        if "mix" not in orig_track:
            assert "mix" not in written_track, f"tracks[{i}] gained an injected mix key"


def test_write_preserves_explicit_nulls(tmp_path: Path) -> None:
    """Source nulls (canvas_config.background, cover, ...) must survive verbatim."""
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    original_raw = bundle.read_template()
    assert original_raw["canvas_config"]["background"] is None

    draft = parse_bundle(bundle)
    write_bundle(draft, bundle)

    written_raw = bundle.read_template()
    assert written_raw["canvas_config"]["background"] is None
    assert written_raw["cover"] is None


def test_assigned_duration_survives_write(tmp_path: Path) -> None:
    """exclude_unset must not drop fields assigned after parse (the
    _bump_duration path mutates draft.duration through attribute assignment)."""
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft = parse_bundle(bundle)
    draft.duration = 12_000_000
    write_bundle(draft, bundle)
    redraft = parse_bundle(bundle)
    assert redraft.duration == 12_000_000
