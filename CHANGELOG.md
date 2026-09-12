# Changelog

All notable changes to draftseam are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with semver tags.

## [0.2.0] - 2026-09-12

### Fixed

- **Clean CLI error contract** — a directory without `template.tmp`, a corrupt
  `template.tmp`, or a non-dict JSON root used to dump raw
  `DraftBundleError` / `JSONDecodeError` / pydantic `ValidationError`
  tracebacks (exit 1). Every bundle-taking command now prints a single
  `Error: <reason>` line and exits 2.
- **Bare project names resolve again** — `draftseam inspect 2月18日` was
  rejected by click's path check before `DraftBundle.resolve` could map the
  name under the default 剪映 projects root; the m1 name-resolution feature
  was unreachable from the CLI.
- **No-op writes no longer mutate `template.tmp`** — the writer used a plain
  `model_dump()` and injected every modelled-but-absent field (e.g.
  `"mix": null` on every track). It now uses `model_dump(exclude_unset=True)`:
  a no-op write leaves the JSON deep-equal to the source, source nulls survive
  verbatim, and agent-inserted entries serialize exactly their constructed
  fields.
- **Time-argument validation** — `insert_subtitle` / `add_voiceover` /
  `add_transition` rejected nothing in v0.1.0: negative start/dur silently
  wrote corrupt timeranges (exit 0), NaN/Inf crashed with raw
  `ValueError`/`OverflowError`. They now raise a precise `ValueError` before
  any mutation; the CLI surfaces it as a clean exit-2 error with the bundle
  untouched.

### Added

- **`draftseam check <bundle>`** — bundle-consistency validation (roadmap v0.2):
  material/track referential integrity, non-negative timeranges, duration
  coverage. Exit 0 = consistent, 1 = problems listed, 2 = unreadable. The
  encrypted `draft_info.json` stays opaque — only its presence is noted; a
  byte-level comparison with `template.tmp` is impossible without decryption.
- **Segment-level field documentation** — `docs/format_notes.md` now lists the
  segment field set observed in the bundled sample (built from the real
  JianyingPro 75.0.0 bundle shell), with the explicit caveat that populated
  real-draft semantics remain unverified.
- `CHANGELOG.md` and a version-consistency test pinning every live version
  surface to the same value.

### Changed

- Version surfaces bumped in lockstep: `VERSION`, `pyproject.toml`,
  `draftseam.__version__`, README badges, `web/site.json` `meta.content_version`
  and footer tag. Frozen recordings (`docs/demo-results.json`,
  `assets/demo.gif`) keep their recorded 0.1.0 content.

## [0.1.0] - 2026-08-18

Initial release.

- 剪映/CapCut `.draft` directory-bundle I/O (`bundle.py`): reads/writes only
  `template.tmp` (plain JSON); `draft_info.json` treated as opaque.
- Pydantic timeline model (`schema.py`, `parser.py`, `writer.py`): tolerant
  `extra="allow"` models; parse → write round-trip semantically identical.
- Agent primitives (`agent_api.py`): `insert_subtitle` (materials.texts),
  `add_voiceover`, `add_transition`.
- CLI (`cli.py`): `inspect` / `add-subtitle` / `add-voiceover` /
  `add-transition` / `write` / `list-projects`.
- Bundled sample project fixture, `docs/format_notes.md`, bilingual README,
  CI-rendered demo GIF.

[0.2.0]: https://github.com/SuperMarioYL/draftseam/releases/tag/v0.2.0
[0.1.0]: https://github.com/SuperMarioYL/draftseam/releases/tag/v0.1.0
