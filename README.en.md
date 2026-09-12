**English** | [简体中文](README.md)

<picture>
  <source media="(max-width: 640px) and (prefers-color-scheme: dark)" srcset="assets/presentation/hero-mobile-dark.svg">
  <source media="(max-width: 640px)" srcset="assets/presentation/hero-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/hero-dark.svg">
  <img src="assets/presentation/hero-light.svg" width="1000" alt="Parse supported Jianying draft bundles into a multitrack model and edit subtitle, audio and transition materials through Python or CLI.">
</picture>

**Parse supported Jianying draft bundles into a multitrack model and edit subtitle, audio and transition materials through Python or CLI.**

`v0.2.0` · `Python 3.12+` · [MIT](LICENSE)

[Website](https://draftseam.lei6393.com) · [Demo record](docs/demo-results.json)

## Why use it

An exported video does not expose the original subtitle and audio structure. draftseam provides structured access to template.tmp and focused helpers for common timeline edits. Opening the result in a particular Jianying version still requires validation with that project.

## Architecture

<picture>
  <source media="(max-width: 640px) and (prefers-color-scheme: dark)" srcset="assets/presentation/architecture-mobile-dark.svg">
  <source media="(max-width: 640px)" srcset="assets/presentation/architecture-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/architecture-dark.svg">
  <img src="assets/presentation/architecture-light.svg" width="1000" alt="bundle.py owns directory I/O; parser.py and schema.py create a Draft model that permits extra fields. agent_api.py mutates materials and segments, and writer.py writes JSON back. Sibling files such as draft_info.json are opaque and are not decrypted or synchronized.">
</picture>

bundle.py owns directory I/O; parser.py and schema.py create a Draft model that permits extra fields. agent_api.py mutates materials and segments, and writer.py writes JSON back. Sibling files such as draft_info.json are opaque and are not decrypted or synchronized.

See [format notes](docs/format_notes.md). A subtitle combines a materials.texts entry and a text-track segment. API time values are seconds, stored internally as microseconds.

## Install

Requires Python 3.12+. The demo parses JSON locally and writes only to a disposable copy.

```bash
git clone https://github.com/SuperMarioYL/draftseam.git
cd draftseam
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Quickstart

The supplied fixture validates model round-trip equality, a subtitle count change from one to two, and unchanged opaque-file bytes. It is not reopened in the Jianying/CapCut application in this demo.

```bash
python -m draftseam.cli inspect tests/fixtures/sample_project
python -m draftseam.cli check tests/fixtures/sample_project
python examples/presentation_demo.py
```

Inputs are in [tests/fixtures/sample_project](tests/fixtures/sample_project/). The [demo script](examples/presentation_demo.py) copies, edits, reads back and removes its temporary directory.

## Usage

inspect prints the track tree. add-subtitle accepts --text, --start and --dur, plus optional --size and --color. add-voiceover adds audio material and a segment; add-transition appends transition material. check validates a bundle's internal consistency (segment material references resolve, track references match, timeranges are non-negative, duration covers the content) with exit codes 0/1/2 for consistent / problems found / unreadable. Invalid time arguments (negative, zero-length, NaN/Inf) are rejected before any write with a clean error. CLI add-* commands write in place, while Python API edits require write_bundle.

## Recorded demo

<picture>
  <source media="(max-width: 640px) and (prefers-color-scheme: dark)" srcset="assets/presentation/process-mobile-dark.svg">
  <source media="(max-width: 640px)" srcset="assets/presentation/process-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/process-dark.svg">
  <img src="assets/presentation/process-light.svg" width="1000" alt="The supplied fixture validates model round-trip equality, a subtitle count change from one to two, and unchanged opaque-file bytes. It is not reopened in the Jianying/CapCut application in this demo.">
</picture>

### Inspect the fixture

Read the three tracks and material lists.

```text
$ python -m draftseam.cli inspect tests/fixtures/sample_project
剪映 draft: sample_project  version=360000 new_version=75.0.0  fps=30.0  duration=10.000s
materials: videos=2 audios=1 texts(字幕)=1 effects=0 video_effects=0 transitions(转场)=1
tracks: 3
  [0] 视频轨 (id=AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA) segments=2
      - seg material=11111111-1111-4111-8111-111111111111 start=0.000s dur=5.000s
      - seg material=22222222-2222-4222-8222-222222222222 start=5.000s dur=5.000s
  [1] 配音轨 (id=BBBBBBBB-BBBB-4BBB-8BBB-BBBBBBBBBBBB) segments=1
      - seg material=33333333-3333-4333-8333-333333333333 start=6.000s dur=4.000s
  [2] 字幕轨 (id=CCCCCCCC-CCCC-4CCC-8CCC-CCCCCCCCCCCC) segments=1
      - seg material=44444444-4444-4444-8444-444444444444 start=1.500s dur=2.000s
        字幕: '你好，剪映'
转场 materials.transitions: 1
  - 叠化 dur=0.500s id=55555555-5555-4555-8555-555555555555
```

### Edit and read back

Add a subtitle in a temporary copy and check the model and opaque file.

```text
$ python examples/presentation_demo.py
{
  "before": {
    "tracks": 3,
    "texts": 1
  },
  "after": {
    "tracks": 3,
    "texts": 2
  },
  "subtitle": "A new local subtitle",
  "roundtrip_equal": true,
  "draft_info_unchanged": true
}
```

## Capabilities and integration

<picture>
  <source media="(max-width: 640px) and (prefers-color-scheme: dark)" srcset="assets/presentation/integrations-mobile-dark.svg">
  <source media="(max-width: 640px)" srcset="assets/presentation/integrations-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/presentation/integrations-dark.svg">
  <img src="assets/presentation/integrations-light.svg" width="1000" alt="It handles project structure; rendering and application compatibility belong to the editor. Keep a project copy before real edits; a one-generation .bak is not full version control.">
</picture>

It handles project structure; rendering and application compatibility belong to the editor. Keep a project copy before real edits; a one-generation .bak is not full version control.



## Configuration

Writes preserve one previous template.tmp.bak. list-projects accepts --root. The schema allows extra fields but does not understand all unknown semantics. add-transition adds a material entry; it does not by itself attach a transition between adjacent clips.

## Roadmap and scope

Supported JSON-bundle access and editing helpers are implemented. v0.2 adds the `draftseam check` consistency validation (referential integrity and timerange checks on template.tmp; draft_info.json stays encrypted and opaque — no byte-level comparison) plus segment-level field documentation. Validation across more real project versions and batch workflows remain future work. There is no live Pro plan or MP4 renderer.

- The fixture does not establish lossless compatibility with every Jianying version or field.
- The tool neither decrypts draft_info nor renders video.
- A transition material does not prove it is attached to clips in the editor.

Version history is in [CHANGELOG.md](CHANGELOG.md).

[Terminal recording](assets/demo.gif) · [Recording script](docs/demo.tape)

## License

[MIT](LICENSE)
