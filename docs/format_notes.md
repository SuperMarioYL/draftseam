# 剪映 / CapCut `.draft` 格式笔记

> Verified on JianyingPro 75.0.0 (macOS). These notes document the on-disk
> shape of a 剪映 draft so future maintainers don't have to re-derive it.

## 1. The draft is a *directory bundle*, not a file

A 剪映 project on macOS lives at:

```
~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/<project-name>/
```

The "project" is the **directory itself**. It contains many files; only one
of them matters to draftseam.

Typical contents (a real 75.0.0 bundle):

```
<project-name>/
├── template.tmp            ← PLAIN JSON: version + tracks + materials (+ more). draftseam owns this.
├── template-2.tmp          ← encrypted (base64/AES) backup of the live template
├── draft_info.json         ← encrypted persisted form (opaque — never decoded)
├── draft_info.json.bak     ← backup
├── draft_meta_info.json    ← encrypted metadata (opaque)
├── draft_agency_config.json ← plain JSON (agency/agent config)
├── draft_settings          ← INI-ish key=value text
├── draft_virtual_store.json
├── key_value.json
├── attachment_editing.json
├── timeline_layout.json
├── performance_opt_info.json
├── draft_cover.jpg         ← cover thumbnail
├── Resources/              ← imported media / generated assets
├── common_attachment/
├── .backup/                ← timestamped .bak files (encrypted)
├── adjust_mask/ matting/ qr_upload/ smart_crop/ subdraft/
└── root_meta_info.json     ← (one level up, at the projects root)
```

draftseam reads/writes **only** `template.tmp`. Everything else is left
untouched so the bundle still reopens in 剪映.

## 2. `template.tmp` is plain JSON — no binary codec

The whole timeline is a single JSON document. There is **no** varint,
length-prefix, or `construct`-parsed binary framing. `json.load` is all you
need. This was the key reverse-engineering finding: the format-asset moat is
owning parse/write of an *undocumented but plain-JSON* schema.

### Top-level shape

```jsonc
{
  "version": 360000,            // internal schema version int
  "new_version": "75.0.0",      // editor product version string
  "fps": 30.0,
  "duration": 0,                // microseconds (1_000_000 == 1.0s)
  "id": "F2DAE6E6-9AA1-40F8-B87E-2AC5CB52D371",
  "name": "",
  "canvas_config": {"background": null, "height": 0, "ratio": "original", "width": 0},
  "tracks": [],                 // list of Track
  "materials": { ... },         // dict of typed lists (see below)
  "config": { ... },
  "keyframes": {"adjusts":[],"audios":[],"effects":[],"filters":[],"handwrites":[],"stickers":[],"texts":[],"videos":[]},
  "platform": {...},
  "last_modified_platform": {...},
  "create_time": 0,
  "update_time": 0,
  "source": "default",
  "path": "",
  ... many more keys (extra="allow" preserves them)
}
```

Newer 75.0.0 bundles add `draft_type`, `function_assistant_info`,
`smart_ads_info`, `uneven_animation_template_info`, `use_float_render`, etc.
draftseam's `extra="allow"` models carry these through untouched.

### `tracks` and `segments`

```jsonc
{
  "id": "GUID",
  "type": "video",              // video | audio | text | effect | sticker | filter | ...
  "flag": 0,
  "render_index": 0,
  "attribute": 0,
  "segments": [
    {
      "id": "GUID",
      "track_id": "GUID",        // back-ref to the track
      "material_id": "GUID",    // ref into materials.<bucket>
      "source_timerange": {"duration": N, "offset": N},  // window into source media
      "target_timerange": {"duration": N, "offset": N},  // window on the timeline
      "source": 0,
      "common_keyframe_refs": [],
      "animation_entries": [],
      "is_placeholder": false,
      "render_index": 0,
      ... more (UNVERIFIED — see below)
    }
  ]
}
```

### `materials` — the typed material buckets

`materials` is a dict of **~40+ lists** in 75.0.0. The six draftseam models
explicitly:

| bucket | models | meaning |
|---|---|---|
| `materials.videos` | `VideoMaterial` | video clips |
| `materials.audios` | `AudioMaterial` | audio clips / 配音 |
| `materials.texts` | `TextMaterial` | **字幕 / text overlays** (subtitles live here, NOT in a track type) |
| `materials.effects` | `EffectMaterial` | timeline effects |
| `materials.video_effects` | `VideoEffectMaterial` | per-segment video effects |
| `materials.transitions` | `TransitionMaterial` | transitions |

The other ~34 buckets (`ai_translates`, `audio_balances`, `audio_effects`,
`audio_fades`, `beats`, `canvases`, `chromas`, `color_curves`,
`digital_humans`, `flowers`, `green_screens`, `handwrites`, `hsl`,
`images`, `loudnesses`, `masks`, `material_animations`, `placeholders`,
`plugin_effects`, `shapes`, `smart_crops`, `sound_channel_mappings`,
`speeds`, `stickers`, `tail_leaders`, `text_templates`, `time_marks`,
`video_radius`, `video_shadows`, `video_strokes`, `video_trackings`,
`vocal_beautifys`, `vocal_separations`, ...) are **preserved as extras**
(`extra="allow"`) and round-trip untouched.

## 3. The "字幕" rule (load-bearing)

字幕 (subtitles) are **`materials.texts` entries referenced by segments on a
`text` track**. There is no dedicated `"subtitle"` track type. To insert a
字幕 you must:

1. append a `materials.texts` entry (the subtitle string + styling);
2. add a segment on a `type=="text"` track whose `material_id` points at the
   new text entry, with a `target_timerange` placing it on the timeline.

This is exactly what `draftseam.agent_api.insert_subtitle` does.

## 4. Effects are split across three buckets

Do not look for "all effects" in one place:

* `materials.effects` — timeline-level effects.
* `materials.video_effects` — per-segment video effects.
* `materials.transitions` — transitions between adjacent segments.

## 5. `draft_info.json` is opaque (encrypted)

`draft_info.json` is **base64 of (likely AES-encrypted) bytes**. It is the
persisted form 剪映 re-reads on open. draftseam treats it as an opaque blob:

* it is **never decoded** — no key derivation, no decryption;
* it is copied byte-for-byte if a bundle is copied;
* a draftseam `write` does **not** touch it (only `template.tmp` is rewritten).

The same applies to `draft_meta_info.json` and the `.backup/*.bak` files.

> ⚠️ The `template.tmp` you write must stay consistent with whatever
> `draft_info.json` encodes, or 剪映 may complain on reopen. For v0.1, the
> round-trip contract is: parse `template.tmp` → mutate → write
> `template.tmp`. Reopening in 剪映 reads the bundle; if `draft_info.json`
> disagrees, 剪映 typically regenerates it from `template.tmp`. This is the
> m1/m2 boundary; reconciling the encrypted form is a future milestone.
>
> v0.2 adds `draftseam check`: it validates the consistency that can be
> checked **without decrypting anything** — referential integrity
> (`segment.material_id` resolves into a materials bucket, `segment.track_id`
> matches its track), non-negative timeranges, and `duration` covering the
> last segment end. A byte-level comparison against the encrypted
> `draft_info.json` remains out of scope by the opacity boundary above.

## 6. Field-name uncertainty (why the models are tolerant)

Local draft samples on this Mac are **empty** (`duration: 0`, `tracks: []`,
all material buckets `[]`). That means **segment-level field names beyond the
commonly-observed ones are unverified against an externally populated real
draft**. draftseam does not hardcode every field; the pydantic models use
`extra="allow"` so:

* the documented fields (`id`, `track_id`, `material_id`,
  `source_timerange`, `target_timerange`, ...) are typed for ergonomics;
* every other field 剪映 actually writes is preserved through a parse → write
  round-trip and shows up in `model_dump()`.

### Segment-level fields observed in the bundled sample (v0.2)

The fixture `tests/fixtures/sample_project` was populated during m1 from the
real JianyingPro 75.0.0 bundle shell (both real local drafts are empty), so
its field set — not its values — is the current evidence. Every segment in
the sample carries exactly these fields:

| field | observed shape | meaning |
|---|---|---|
| `id` | GUID string | segment identity |
| `track_id` | GUID string | back-reference to the owning track |
| `material_id` | GUID string | reference into `materials.<bucket>` |
| `source_timerange` | `{duration, offset}` µs | window into the source media |
| `target_timerange` | `{duration, offset}` µs | window on the timeline |
| `source` | int (`0`) | source selector |
| `common_keyframe_refs` | list (empty) | keyframe back-refs |
| `animation_entries` | list (empty) | animation entries |
| `is_placeholder` | bool | placeholder flag |
| `render_index` | int | render order |
| `extra_transform` | object | transform payload |
| `clip` | object | clip payload |
| `responsive_layout` | object | responsive layout payload |
| `cartoon_name` | string (empty) | cartoon/animation name (unmodelled extra) |
| `is_tone_adjust` | bool | tone-adjust flag (unmodelled extra) |

`draftseam check` enforces the structural relations of the first rows
(material/track references, timerange sanity); the payload fields
(`clip`, `extra_transform`, ...) are preserved but their inner semantics are
not interpreted. When a real, populated creator draft becomes available,
re-verify this table against it and promote load-bearing fields to explicit
model attributes.

## 7. Time units

All timerange `duration`/`offset` values and the top-level `duration` are
**microseconds** (`1_000_000 == 1.0s` at any fps). The CLI and agent API
accept human-friendly **seconds** (floats) and convert with
`draftseam.schema.MICROS_PER_SECOND`.
