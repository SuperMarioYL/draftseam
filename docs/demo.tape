# demo.tape — drafts the 10-minute happy path for the README Demo section.
# Rendered to assets/demo.gif by `vhs docs/demo.tape` (local + .github/workflows/demo.yml).
# vhs runs from the repo root.

Output assets/demo.gif

Set Width 920
Set Height 400
Set FontSize 13
Set Padding 14
Set Theme "Dracula"

# --- install draftseam from source (editable; package not yet on PyPI at v0.1) ---
Type "# install draftseam"
Enter
Sleep 1
Type "pip install -e . -q"
Enter
Sleep 3

# --- inspect the bundled sample 剪映 .draft bundle ---
Type "# inspect the bundled sample 剪映 .draft bundle"
Enter
Sleep 1
Type "cp -r tests/fixtures/sample_project /tmp/ds_demo"
Enter
Sleep 1
Type "draftseam inspect /tmp/ds_demo"
Enter
Sleep 2

# --- an agent inserts a 字幕 into materials.texts ---
Type "# an agent inserts a 字幕 into materials.texts"
Enter
Sleep 1
Type "draftseam add-subtitle /tmp/ds_demo --text 'AI inserted this 字幕' --start 1.5 --dur 2.0"
Enter
Sleep 2

# --- re-inspect: 字幕 count 1 -> 2, reopens in 剪映 ---
Type "# re-inspect: 字幕 (materials.texts) 1 -> 2, reopens in 剪映 editable"
Enter
Sleep 1
Type "draftseam inspect /tmp/ds_demo | head -3"
Enter
Sleep 2

Type "rm -rf /tmp/ds_demo"
Enter
Sleep 1
