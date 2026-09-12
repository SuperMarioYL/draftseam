"""Agent-seam test: ``insert_subtitle`` round-trips and reopens correctly.

An agent inserts a 字幕 into ``materials.texts`` (+ a referencing segment on a
text track), writes the bundle, re-parses it, and the new 字幕 entry is
present and editable — the core "wow" of the format-asset moat.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from draftseam import agent_api
from draftseam.bundle import DraftBundle
from draftseam.parser import parse_bundle
from draftseam.writer import write_bundle

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_project"


def _copy_fixture(tmp_path: Path) -> Path:
    dst = tmp_path / "sample_project"
    shutil.copytree(FIXTURE, dst)
    return dst


def test_insert_subtitle_round_trips(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)

    draft = parse_bundle(bundle)
    n_before = len(draft.materials.texts)

    mat_id = agent_api.insert_subtitle(
        draft, text="AI inserted this 字幕", start=1.5, dur=2.0
    )
    assert mat_id  # a fresh GUID was minted
    assert len(draft.materials.texts) == n_before + 1

    # the new material sits in materials.texts with the right text
    new_mat = next(tm for tm in draft.materials.texts if tm.id == mat_id)
    assert new_mat.text == "AI inserted this 字幕"
    assert new_mat.type == "text"

    # a text track now has a segment referencing the new material
    text_trks = [t for t in draft.tracks if t.type == "text"]
    assert text_trks, "insert_subtitle should ensure a text track exists"
    segs = [s for s in text_trks[0].segments if s.material_id == mat_id]
    assert len(segs) == 1
    seg = segs[0]
    assert seg.target_timerange.offset == 1_500_000  # 1.5s in micros
    assert seg.target_timerange.duration == 2_000_000  # 2.0s in micros

    # write -> re-parse -> the 字幕 survived on disk
    write_bundle(draft, bundle)
    redraft = parse_bundle(bundle)
    again = [tm for tm in redraft.materials.texts if tm.id == mat_id]
    assert len(again) == 1, "inserted 字幕 must persist across write/re-parse"
    assert again[0].text == "AI inserted this 字幕"

    # and its referencing segment survived too
    rtext_trks = [t for t in redraft.tracks if t.type == "text"]
    assert rtext_trks
    rsegs = [s for s in rtext_trks[0].segments if s.material_id == mat_id]
    assert len(rsegs) == 1
    assert rsegs[0].target_timerange.offset == 1_500_000


def test_insert_subtitle_two_entries_distinct_ids(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft = parse_bundle(bundle)

    id1 = agent_api.insert_subtitle(draft, text="第一条", start=0.0, dur=1.0)
    id2 = agent_api.insert_subtitle(draft, text="第二条", start=1.5, dur=1.0)
    assert id1 != id2
    write_bundle(draft, bundle)
    redraft = parse_bundle(bundle)
    ids = {tm.id for tm in redraft.materials.texts}
    assert {id1, id2}.issubset(ids)


def test_add_voiceover_round_trips(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft = parse_bundle(bundle)
    n_before = len(draft.materials.audios)

    aid = agent_api.add_voiceover(
        draft, path="/tmp/vo.mp3", start=2.0, dur=3.0, name="配音1"
    )
    assert len(draft.materials.audios) == n_before + 1
    write_bundle(draft, bundle)
    redraft = parse_bundle(bundle)
    assert any(a.id == aid for a in redraft.materials.audios)


def test_add_transition_round_trips(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft = parse_bundle(bundle)
    n_before = len(draft.materials.transitions)

    tid = agent_api.add_transition(draft, name="叠化", duration=0.5)
    assert len(draft.materials.transitions) == n_before + 1
    write_bundle(draft, bundle)
    redraft = parse_bundle(bundle)
    assert any(t.id == tid for t in redraft.materials.transitions)


# --- v0.2: time-argument validation (library contract) ----------------------
#
# v0.1 silently wrote negative timeranges for negative values and crashed
# with ValueError/OverflowError for NaN/Inf inside _seconds_to_micros. The
# primitives now reject bad values BEFORE any mutation.


def test_insert_subtitle_rejects_negative_start(tmp_path: Path) -> None:
    draft = parse_bundle(DraftBundle(_copy_fixture(tmp_path)))
    n_texts = len(draft.materials.texts)
    with pytest.raises(ValueError, match="start"):
        agent_api.insert_subtitle(draft, text="x", start=-1.0, dur=1.0)
    assert len(draft.materials.texts) == n_texts  # not mutated


def test_insert_subtitle_rejects_nonpositive_dur(tmp_path: Path) -> None:
    draft = parse_bundle(DraftBundle(_copy_fixture(tmp_path)))
    with pytest.raises(ValueError, match="dur"):
        agent_api.insert_subtitle(draft, text="x", start=0.0, dur=0.0)
    with pytest.raises(ValueError, match="dur"):
        agent_api.insert_subtitle(draft, text="x", start=0.0, dur=-2.0)


def test_insert_subtitle_rejects_nan_and_inf(tmp_path: Path) -> None:
    draft = parse_bundle(DraftBundle(_copy_fixture(tmp_path)))
    with pytest.raises(ValueError, match="finite"):
        agent_api.insert_subtitle(draft, text="x", start=float("nan"), dur=1.0)
    with pytest.raises(ValueError, match="finite"):
        agent_api.insert_subtitle(draft, text="x", start=0.0, dur=float("inf"))


def test_add_voiceover_and_transition_reject_bad_times(tmp_path: Path) -> None:
    draft = parse_bundle(DraftBundle(_copy_fixture(tmp_path)))
    with pytest.raises(ValueError, match="start"):
        agent_api.add_voiceover(draft, path="/tmp/a.mp3", start=-0.1, dur=1.0)
    with pytest.raises(ValueError, match="dur"):
        agent_api.add_voiceover(draft, path="/tmp/a.mp3", start=0.0, dur=0.0)
    with pytest.raises(ValueError, match="duration"):
        agent_api.add_transition(draft, name="叠化", duration=-0.5)
