"""Version-lockstep tests (v0.2).

Every live version surface must agree; the two frozen recordings
(``docs/demo-results.json`` — a captured v0.1 run pinning fixture hashes —
and ``assets/demo.gif``) deliberately keep their recorded 0.1.0 content and
are the only allow-listed leftovers.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

import draftseam

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "0.2.0"
#: Recorded artifacts that legitimately still say the old version.
FROZEN = {"docs/demo-results.json"}
#: This test file itself — the sweep tool contains the literal it searches for.
SELF = "tests/test_version_consistency.py"


def test_version_file() -> None:
    assert (ROOT / "VERSION").read_text().strip() == EXPECTED


def test_pyproject_version() -> None:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        project = tomllib.load(fh)["project"]
    assert project["version"] == EXPECTED


def test_package_dunder_version() -> None:
    assert draftseam.__version__ == EXPECTED


def test_site_json_content_version() -> None:
    site = json.loads((ROOT / "web" / "site.json").read_text(encoding="utf-8"))
    assert site["meta"]["content_version"] == EXPECTED
    assert EXPECTED in site["footer"]["tag"]


def test_readme_badges_pinned_to_current() -> None:
    for name in ("README.md", "README.en.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert f"v{EXPECTED}" in text, f"{name} badge line missing v{EXPECTED}"


def test_changelog_has_both_sections() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [0.1.0]" in text
    assert f"## [{EXPECTED}]" in text


def test_no_stale_0_1_0_in_live_sources() -> None:
    """Repo-wide sweep: 0.1.0 may appear only in CHANGELOG history + frozen files."""
    pattern = re.compile(r"0\.1\.0")
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", ".venv/", "build/", "dist/")) or rel.endswith((".gif", ".pyc")):
            continue
        if "/__pycache__/" in rel or rel.startswith("draftseam_demo"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IsADirectoryError):
            continue  # binary (svg/png assets are one-line text but skip-safe)
        if pattern.search(text) and rel not in FROZEN and rel != "CHANGELOG.md" and rel != SELF:
            offenders.append(rel)
    assert not offenders, f"stale 0.1.0 surfaces: {offenders}"


def test_cli_version_reports_current() -> None:
    """Shells out to this environment's console script only when it exists.

    Resolved from the interpreter's bin dir (not PATH-scanned) so a stale
    draftseam elsewhere on the machine cannot make the test lie; GH runners
    without the entry point skip.
    """
    import sys
    import unittest

    exe = Path(sys.executable).parent / "draftseam"
    if not exe.is_file():  # pragma: no cover - environment without the entry point
        raise unittest.SkipTest("draftseam console script not installed")
    out = subprocess.run([str(exe), "--version"], capture_output=True, text=True)
    assert out.returncode == 0
    assert EXPECTED in out.stdout
