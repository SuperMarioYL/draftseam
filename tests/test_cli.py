"""CLI input-contract tests (v0.2).

Every bad-draft-input path must keep one contract: a single clean ``Error:``
line, exit code 2, no traceback. At v0.1 these paths dumped raw
DraftBundleError / JSONDecodeError / pydantic ValidationError / ValueError /
OverflowError tracebacks and exited 1, and the bare-project-name resolution
was unreachable because ``click.Path(exists=True)`` rejected the name before
``DraftBundle.resolve`` could remap it under the 剪映 root.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from draftseam.bundle import DraftBundle
from draftseam.cli import cli

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_project"


def _copy_fixture(tmp_path: Path, name: str = "sample_project") -> Path:
    dst = tmp_path / name
    shutil.copytree(FIXTURE, dst)
    return dst


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_inspect_missing_template_tmp_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    empty = tmp_path / "not_a_bundle"
    empty.mkdir()
    result = runner.invoke(cli, ["inspect", str(empty)])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "template.tmp" in result.output
    assert "Traceback" not in result.output


def test_inspect_corrupt_json_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    (bundle / "template.tmp").write_text('{"broken json', encoding="utf-8")
    result = runner.invoke(cli, ["inspect", str(bundle)])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_inspect_non_dict_root_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    (bundle / "template.tmp").write_text("[1, 2]", encoding="utf-8")
    result = runner.invoke(cli, ["inspect", str(bundle)])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_inspect_nonexistent_path_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(cli, ["inspect", str(tmp_path / "nope")])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_bare_project_name_resolves_under_jianying_root(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bare name must reach DraftBundle.resolve, not be rejected by click.

    v0.1's ``click.Path(exists=True)`` failed with ``Directory ... does not
    exist`` before resolve could map the name under the 剪映 projects root,
    making the m1 name-resolution feature unreachable from the CLI.
    """
    fake_root = tmp_path / "com.lveditor.draft"
    shutil.copytree(FIXTURE, fake_root / "fakeproj")
    monkeypatch.setattr("draftseam.bundle.DEFAULT_DRAFT_ROOT", fake_root)
    # CWD (tmp_path) has no "fakeproj" — only the 剪映 root does.
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(cli, ["inspect", "fakeproj"])
    assert result.exit_code == 0, result.output
    assert "剪映 draft" in result.output
    assert str(fake_root / "fakeproj") in str(DraftBundle.resolve("fakeproj").path)


def test_add_subtitle_negative_start_is_rejected_and_file_untouched(
    runner: CliRunner, tmp_path: Path
) -> None:
    bundle = _copy_fixture(tmp_path)
    before = (bundle / "template.tmp").read_bytes()
    result = runner.invoke(cli, ["add-subtitle", str(bundle), "--text", "x", "--start", "-5.0", "--dur", "2.0"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "start" in result.output
    assert "Traceback" not in result.output
    # rejected before any mutation: no rewrite, no .bak
    assert (bundle / "template.tmp").read_bytes() == before
    assert not (bundle / "template.tmp.bak").exists()


def test_add_subtitle_nan_start_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["add-subtitle", str(bundle), "--text", "x", "--start", "nan", "--dur", "2.0"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_add_subtitle_inf_dur_is_clean_exit_2(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["add-subtitle", str(bundle), "--text", "x", "--start", "1.0", "--dur", "inf"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_add_subtitle_zero_dur_is_rejected(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["add-subtitle", str(bundle), "--text", "x", "--start", "1.0", "--dur", "0"])
    assert result.exit_code == 2
    assert "dur" in result.output


def test_add_voiceover_negative_start_is_rejected(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["add-voiceover", str(bundle), "--path", "/tmp/a.mp3", "--start", "-1", "--dur", "2"])
    assert result.exit_code == 2
    assert "start" in result.output


def test_add_transition_negative_dur_is_rejected(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["add-transition", str(bundle), "--name", "叠化", "--dur", "-0.5"])
    assert result.exit_code == 2
    assert "duration" in result.output


def test_happy_paths_still_exit_0(runner: CliRunner, tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    result = runner.invoke(cli, ["inspect", str(bundle)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli, ["add-subtitle", str(bundle), "--text", "AI 生成字幕", "--start", "2.0", "--dur", "1.5"]
    )
    assert result.exit_code == 0, result.output
    raw = json.loads((bundle / "template.tmp").read_text(encoding="utf-8"))
    assert any(t.get("text") == "AI 生成字幕" for t in raw["materials"]["texts"])

    result = runner.invoke(cli, ["write", str(bundle)])
    assert result.exit_code == 0, result.output
