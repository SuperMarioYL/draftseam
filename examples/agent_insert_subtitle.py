"""Example: an agent inserts a 字幕 (字幕 = materials.texts entry) into a draft.

Run::

    python examples/agent_insert_subtitle.py tests/fixtures/sample_project/

This parses the sample draft bundle, inserts a 字幕 via the agent API,
writes it back, and re-parses to prove the entry is present and editable —
the core "wow" of draftseam's format-asset moat: an agent-generated edit
lands in the native editor as structured, editable data, not a baked MP4.
"""

from __future__ import annotations

import sys

from draftseam import agent_api
from draftseam.bundle import DraftBundle
from draftseam.parser import parse_bundle
from draftseam.writer import write_bundle


def main(bundle_path: str = "tests/fixtures/sample_project/",
         text: str = "AI inserted this 字幕",
         start: float = 1.5,
         dur: float = 2.0) -> None:
    bundle = DraftBundle.resolve(bundle_path)
    draft = parse_bundle(bundle)
    before = len(draft.materials.texts)

    mat_id = agent_api.insert_subtitle(draft, text=text, start=start, dur=dur)
    write_bundle(draft, bundle)

    redraft = parse_bundle(bundle)
    after = len(redraft.materials.texts)
    present = any(tm.id == mat_id for tm in redraft.materials.texts)
    print(f"字幕 materials.texts: {before} -> {after}")
    print(f"inserted 字幕 id={mat_id} text={text!r} reopened-in-bundle={present}")
    assert present, "inserted 字幕 did not survive write -> re-parse"
    print("reopen in 剪映 → editable 字幕 (materials.texts) present")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/fixtures/sample_project/"
    main(path)
