<div align="right"><sub><b>English</b>&nbsp;&nbsp;⇄&nbsp;&nbsp;<a href="./README.md">简体中文</a></sub></div>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/hero-light.svg">
  <img src="./assets/hero-light.svg" width="880" alt="draftseam — read/write 剪映 .draft timelines">
</picture>

<p align="center"><sub>Let a coding agent read and write 剪映's native <code>.draft</code> timeline — no MP4 round-trip.</sub></p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-0071E3" alt="license"></a>
  <a href="https://github.com/SuperMarioYL/draftseam/releases"><img src="https://img.shields.io/github/v/release/SuperMarioYL/draftseam?label=release&color=0071E3" alt="release"></a>
  <a href="https://github.com/SuperMarioYL/draftseam/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/SuperMarioYL/draftseam/ci.yml?label=CI&color=10A37F" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.12+-5E5CE6?logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/Coding%20Agent-ready-5E5CE6" alt="Coding Agent">
  <img src="https://img.shields.io/badge/Claude%20Code-ready-8985FF" alt="Claude Code">
</p>

**Stop exporting MP4 and re-cutting by hand — let Claude Code edit your 剪映 project file directly.** draftseam parses 剪映's native `.draft` timeline into a structured multi-track model, lets a coding agent insert 字幕 / voiceover / transition tracks, and writes it back as a fully editable native timeline that reopens in 剪映 — no layer structure lost.

## Why now

剪映 (CapCut) is the de-facto editor for Chinese creators, but its `.draft` project format is an undocumented directory bundle that no coding agent can touch — so the only "AI edits video" path today is export-to-MP4 and re-cut by hand, losing every track, subtitle and transition. draftseam closes that seam by owning parse/write of 剪映's `.draft` format asset. It lands on the agent-video demand wave: [OpenMontage](https://github.com/OpenMontage/OpenMontage) (48k★) and [hyperframes](https://github.com/hyperframes/hyperframes) (41k★) have made "agents produce editable timelines" the consensus, but neither touches 剪映's native format — draftseam is the missing format adapter on that chain. Claude Code is the dominant coding agent CN creators already use to generate timeline edits, and draftseam lets it read and write 剪映 projects directly for the first time.

## Table of contents

- [Architecture](#architecture)
- [Install & Quickstart](#install--quickstart)
- [Usage](#usage)
- [Demo](#demo)
- [Roadmap](#roadmap)
- [Pricing](#pricing)
- [License](#license)

## <img src="https://api.iconify.design/tabler:topology-star-3.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Architecture

A 剪映 draft is a **directory bundle**: `template.tmp` (plain JSON: `version` + `tracks` + `materials`) + `draft_info.json` (base64/AES-encrypted, opaque — draftseam never decrypts it). draftseam reads/writes only `template.tmp` — no binary codec, no varint, no `construct` dependency; the whole timeline is plain JSON.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/atlas-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/atlas-light.svg">
  <img src="./assets/atlas-light.svg" width="880" alt="Architecture: 剪映 .draft → bundle.py parse → Draft model → writer.py write back to 剪映">
</picture>

Core flow: `bundle.py` owns directory-bundle I/O → `parser.py` lifts `template.tmp` JSON into a pydantic `Draft` model (`extra="allow"` tolerates 剪映's undocumented fields) → `writer.py` lowers the model back to `template.tmp` JSON with semantically-identical round-trip → `agent_api.py` exposes `insert_subtitle` (writes `materials.texts`) / `add_voiceover` / `add_transition` so the agent never touches JSON. 字幕 (subtitles) are `materials.texts` entries referenced by segments on a text track — there is no "Subtitle" track type.

## <img src="https://api.iconify.design/tabler:rocket.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Install & Quickstart

```bash
pip install draftseam                              # 1. install (<30s)
draftseam inspect tests/fixtures/sample_project/  # 2. print the multi-track timeline tree
draftseam add-subtitle tests/fixtures/sample_project/ \
  --text "AI subtitle" --start 2.0 --dur 1.5       # 3. agent inserts a subtitle and writes back
```

<details><summary>Sample output</summary>

```
剪映 draft: sample_project  version=360000 new_version=75.0.0  fps=30.0  duration=10.000s
materials: videos=2 audios=1 texts(字幕)=1 effects=0 video_effects=0 transitions(转场)=1
tracks: 3
  [0] 视频轨 segments=2
      - seg material=1111... start=0.000s dur=5.000s
  [1] 配音轨 segments=1
      - seg material=3333... start=6.000s dur=4.000s
  [2] 字幕轨 segments=1
      - seg material=4444... start=1.500s dur=2.000s
        字幕: '你好，剪映'
inserted 字幕 material C879... at 1.5s (+2.0s) and wrote .../template.tmp
```

</details>

After the write, reopen the bundle directory in 剪映 — the new subtitle appears on the 字幕 track as a `materials.texts` entry, fully editable.

## <img src="https://api.iconify.design/tabler:terminal-2.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Usage

```bash
# print the full multi-track tree (video/audio/text tracks, transitions, effects + timestamps)
draftseam inspect ~/Movies/JianyingPro/User\ Data/Projects/com.lveditor.draft/myproject/

# list every 剪映 draft project on this machine
draftseam list-projects

# agent inserts a subtitle (materials.texts entry + a referencing segment on a text track)
draftseam add-subtitle myproject/ --text "AI subtitle" --start 2.0 --dur 1.5

# agent inserts a voiceover (materials.audios + an audio-track segment)
draftseam add-voiceover myproject/ --path /path/vo.mp3 --start 0.0 --dur 4.0

# append a transition entry to materials.transitions
draftseam add-transition myproject/ --name 叠化 --dur 0.5

# canonicalise-rewrite template.tmp (proves parse → write round-trip safety)
draftseam write myproject/
```

Programmatic API (import directly from a coding agent, no shell needed):

```python
from draftseam import DraftBundle, parse_bundle, write_bundle, insert_subtitle

bundle = DraftBundle.resolve("tests/fixtures/sample_project/")
draft = parse_bundle(bundle)                          # template.tmp JSON -> Draft model
insert_subtitle(draft, text="AI subtitle", start=2.0, dur=1.5)  # edits materials.texts + text track
write_bundle(draft, bundle)                           # writes template.tmp, reopens in 剪映
```

More in [`examples/agent_insert_subtitle.py`](./examples/agent_insert_subtitle.py).

## <img src="https://api.iconify.design/tabler:photo.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Demo

![demo](assets/demo.gif)

A coding agent uses `draftseam add-subtitle` to insert a subtitle into the sample project; after the write, `materials.texts` grows from 1 to 2 and 剪映 reopens the bundle with the new subtitle editable. Full script in [`docs/demo.tape`](./docs/demo.tape); CI renders it via vhs in [`demo.yml`](./.github/workflows/demo.yml).

## <img src="https://api.iconify.design/tabler:map-2.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Roadmap

- [x] **m1 parse draft**: a real 剪映 `.draft` bundle parses into a `Draft` model and `draftseam inspect` prints a multi-track timeline tree; `bundle.py` / `schema.py` / `parser.py` + sample fixture + [`docs/format_notes.md`](./docs/format_notes.md)
- [x] **m2 write draft**: `writer.py` lowers the `Draft` model back to `template.tmp` JSON with semantically-identical round-trip (`tests/test_roundtrip.py` green)
- [x] **m3 agent seam**: `agent_api.py` (`insert_subtitle` / `add_voiceover` / `add_transition`) + `cli.py` + agent demo + bilingual README + CI-rendered demo gif
- [ ] **v0.2**: consistency check between the encrypted `draft_info.json` form and `template.tmp`; document segment-level field names against a populated real draft
- [ ] **v0.3**: draftseam pro batch tier (N scripts → N editable 剪映 timelines)

### draftseam vs manual MP4 re-cut

| Axis | draftseam | manual MP4 re-cut |
|---|:---:|:---:|
| agent edits timeline programmatically | ✓ | — |
| subtitle / voiceover / transition structure preserved | ✓ | ✗ (lost after re-cut) |
| reopens editable in 剪映 | ✓ | partial (must re-arrange) |
| no dependency on undocumented format stability | partial (depends on `.draft` schema) | ✓ |
| renders an MP4 | — (produces an editable timeline) | ✓ |

draftseam produces an editable timeline, not an MP4; if your goal is final-cut rendering, draftseam is not a replacement.

## <img src="https://api.iconify.design/tabler:cash-banknote.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> Pricing

The draftseam OSS core (parse / write / agent subtitle·voiceover·transition primitives + CLI) is **free forever** under MIT. The commercial revenue path is a **draftseam pro** batch tier: turn N scripts into N editable 剪映 timelines for MCN / creator studios, ¥99–299/mo per seat — the OSS core proves ownership of the format asset, and the pro tier monetises it. The pro tier is deferred to v0.3.

## <img src="https://api.iconify.design/tabler:license.svg?color=%230071E3&width=24" height="22" align="absmiddle" alt=""> License

[MIT](./LICENSE) © 2026 SuperMarioYL. File an issue or PR at [issues](https://github.com/SuperMarioYL/draftseam/issues).

## Share this

```
draftseam — let Claude Code read/write 剪映's native .draft timeline directly. No MP4 re-cut, no layer structure lost; write back and re-edit in 剪映. https://github.com/SuperMarioYL/draftseam
```

<p align="center"><sub><a href="./LICENSE">MIT</a> © 2026 SuperMarioYL</sub></p>
