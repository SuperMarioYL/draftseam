"""``draftseam check`` consistency tests (v0.2).

The check command owns one contract: a consistent bundle exits 0 with an OK
summary, an internally-broken template.tmp exits 1 with numbered problems,
and an unreadable bundle exits 2 via the shared CLI bad-input contract. The
rules are structural (refs / timeranges / duration coverage) — an OK result
never claims 剪映 will reopen the bundle, and the encrypted draft_info.json is
never compared byte-wise.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from click.testing import CliRunner

from draftseam import agent_api
from draftseam.bundle import DraftBundle
from draftseam.checks import check_bundle, check_draft
from draftseam.cli import cli
from draftseam.parser import parse_bundle

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_project"


def _copy_fixture(tmp_path: Path) -> Path:
    dst = tmp_path / "sample_project"
    shutil.copytree(FIXTURE, dst)
    return dst


def _mutate(bundle_dir: Path, fn) -> None:
    path = bundle_dir / "template.tmp"
    data = json.loads(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_fixture_is_consistent(tmp_path: Path) -> None:
    bundle = DraftBundle(_copy_fixture(tmp_path))
    assert check_bundle(bundle) == []


def test_check_command_ok_exit_0(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    result = CliRunner().invoke(cli, ["check", str(bundle_dir)])
    assert result.exit_code == 0, result.output
    assert "OK" in result.output
    assert "internally consistent" in result.output


def test_check_after_agent_edit_still_ok(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    bundle = DraftBundle(bundle_dir)
    draft = parse_bundle(bundle)
    agent_api.insert_subtitle(draft, text="check me", start=3.0, dur=1.0)
    from draftseam.writer import write_bundle

    write_bundle(draft, bundle)
    assert check_bundle(bundle) == []
    result = CliRunner().invoke(cli, ["check", str(bundle_dir)])
    assert result.exit_code == 0, result.output


def test_broken_material_ref_is_a_problem(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)

    def break_ref(data: dict) -> None:
        data["tracks"][0]["segments"][0]["material_id"] = "DEADBEEF-0000-4000-8000-00000000BAD0"

    _mutate(bundle_dir, break_ref)
    problems = check_bundle(DraftBundle(bundle_dir))
    assert any("material_id" in p and "not found" in p for p in problems)

    result = CliRunner().invoke(cli, ["check", str(bundle_dir)])
    assert result.exit_code == 1
    assert "problem" in result.output
    assert "DEADBEEF-0000-4000-8000-00000000BAD0" in result.output


def test_negative_timerange_is_a_problem(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)

    def break_duration(data: dict) -> None:
        data["tracks"][1]["segments"][0]["target_timerange"]["duration"] = -100

    _mutate(bundle_dir, break_duration)
    problems = check_bundle(DraftBundle(bundle_dir))
    assert any("negative" in p for p in problems)


def test_track_id_mismatch_is_a_problem(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)

    def break_track_ref(data: dict) -> None:
        data["tracks"][0]["segments"][0]["track_id"] = "NOT-THE-TRACK-ID"

    _mutate(bundle_dir, break_track_ref)
    problems = check_bundle(DraftBundle(bundle_dir))
    assert any("track_id" in p and "does not match" in p for p in problems)


def test_duration_shorter_than_content_is_a_problem(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)

    def shorten(data: dict) -> None:
        data["duration"] = 1000  # 1ms; the fixture's content runs to 10s

    _mutate(bundle_dir, shorten)
    problems = check_bundle(DraftBundle(bundle_dir))
    assert any("duration" in p and "shorter" in p for p in problems)


def test_unreadable_bundle_exits_2(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = CliRunner().invoke(cli, ["check", str(empty)])
    assert result.exit_code == 2
    assert "Error:" in result.output

    bundle_dir = _copy_fixture(tmp_path)
    (bundle_dir / "template.tmp").write_text("{broken", encoding="utf-8")
    result = CliRunner().invoke(cli, ["check", str(bundle_dir)])
    assert result.exit_code == 2
    assert "Error:" in result.output


def test_missing_draft_info_json_is_a_note_not_a_problem(tmp_path: Path) -> None:
    bundle_dir = _copy_fixture(tmp_path)
    (bundle_dir / "draft_info.json").unlink()
    result = CliRunner().invoke(cli, ["check", str(bundle_dir)])
    assert result.exit_code == 0, result.output
    assert "draft_info.json absent" in result.output


def test_extra_bucket_material_refs_do_not_false_positive(tmp_path: Path) -> None:
    """A segment referencing materials.stickers (an unmodelled bucket) is valid."""
    bundle_dir = _copy_fixture(tmp_path)

    def add_sticker_segment(data: dict) -> None:
        data["materials"]["stickers"] = [{"id": "STICKER-1", "type": "sticker"}]
        seg = json.loads(json.dumps(data["tracks"][0]["segments"][0]))
        seg["id"] = "SEG-STICKER-1"
        seg["material_id"] = "STICKER-1"
        data["tracks"][0]["segments"].append(seg)

    _mutate(bundle_dir, add_sticker_segment)
    draft = parse_bundle(DraftBundle(bundle_dir))
    assert check_draft(draft) == []
