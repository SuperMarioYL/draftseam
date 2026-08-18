"""``draftseam`` command-line interface.

Commands::

    draftseam inspect <bundle>                       # print the timeline tree
    draftseam add-subtitle <bundle> --text ... --start ... --dur ...
    draftseam add-voiceover <bundle> --path ... --start ... --dur ...
    draftseam add-transition <bundle> --name ... --dur ...
    draftseam write <bundle>                          # persist pending edits

``inspect`` parses ``template.tmp`` and prints a readable multi-track tree
(视频轨 / 字幕轨 / 配音轨 / 转场 / 特效) with timestamps in seconds.
The ``add-*`` commands mutate the bundle in place (parse -> mutate -> write)
so the result reopens in 剪映 with the new entry present.
"""

from __future__ import annotations

from typing import Optional

import click

from . import agent_api
from .bundle import DEFAULT_DRAFT_ROOT, DraftBundle
from .parser import parse_bundle
from .schema import MICROS_PER_SECOND
from .writer import draft_to_dict, write_bundle


def _micros_to_seconds(micros: Optional[int]) -> float:
    if micros is None:
        return 0.0
    return micros / MICROS_PER_SECOND


def _fmt_ts(micros: Optional[int]) -> str:
    return f"{_micros_to_seconds(micros):.3f}s"


def _render_tree(draft) -> str:
    """Render a Draft model as a readable multi-track tree string."""
    lines: list[str] = []
    lines.append(
        f"剪映 draft: {draft.name or '(unnamed)'}  "
        f"version={draft.version} new_version={draft.new_version}  "
        f"fps={draft.fps}  duration={_fmt_ts(draft.duration)}"
    )

    mats = draft.materials
    summary = (
        f"materials: videos={len(mats.videos)} audios={len(mats.audios)} "
        f"texts(字幕)={len(mats.texts)} effects={len(mats.effects)} "
        f"video_effects={len(mats.video_effects)} "
        f"transitions(转场)={len(mats.transitions)}"
    )
    lines.append(summary)

    if not draft.tracks:
        lines.append("tracks: (empty)")
        return "\n".join(lines)

    lines.append(f"tracks: {len(draft.tracks)}")
    track_kinds = {
        "video": "视频轨",
        "audio": "配音轨",
        "text": "字幕轨",
        "effect": "特效轨",
        "sticker": "贴纸轨",
        "filter": "滤镜轨",
    }
    for i, tr in enumerate(draft.tracks):
        kind = track_kinds.get(tr.type or "", tr.type or "track")
        lines.append(f"  [{i}] {kind} (id={tr.id}) segments={len(tr.segments)}")
        for seg in tr.segments:
            ttr = seg.target_timerange
            offset = ttr.offset if ttr else None
            dur = ttr.duration if ttr else None
            lines.append(
                f"      - seg material={seg.material_id} "
                f"start={_fmt_ts(offset)} dur={_fmt_ts(dur)}"
            )
            # If this is a text segment, show the 字幕 string.
            if tr.type == "text" and seg.material_id:
                for tm in mats.texts:
                    if tm.id == seg.material_id and tm.text:
                        lines.append(f"        字幕: {tm.text!r}")
                        break

    # Free-floating material entries not referenced by any track segment.
    if mats.transitions:
        lines.append(f"转场 materials.transitions: {len(mats.transitions)}")
        for tm in mats.transitions:
            lines.append(
                f"  - {tm.name} dur={_fmt_ts(tm.duration)} id={tm.id}"
            )
    if mats.effects:
        lines.append(f"特效 materials.effects: {len(mats.effects)}")
        for em in mats.effects:
            lines.append(f"  - {em.name or em.id}")
    if mats.video_effects:
        lines.append(f"视频特效 materials.video_effects: {len(mats.video_effects)}")
        for em in mats.video_effects:
            lines.append(f"  - {em.name or em.id}")
    return "\n".join(lines)


@click.group()
@click.version_option(package_name="draftseam")
def cli() -> None:
    """draftseam — read/write 剪映/CapCut .draft timelines for coding agents."""


@cli.command("inspect")
@click.argument("bundle", type=click.Path(exists=True, file_okay=False))
def inspect_cmd(bundle: str) -> None:
    """Print the multi-track timeline tree of a draft bundle."""
    b = DraftBundle.resolve(bundle)
    draft = parse_bundle(b)
    click.echo(_render_tree(draft))


@cli.command("add-subtitle")
@click.argument("bundle", type=click.Path(exists=True, file_okay=False))
@click.option("--text", "text", required=True, help="字幕 string (CJK OK).")
@click.option("--start", "start", required=True, type=float, help="timeline start, seconds")
@click.option("--dur", "dur", required=True, type=float, help="on-screen duration, seconds")
@click.option("--size", "size", type=float, default=None, help="optional text size")
@click.option("--color", "color", default=None, help="optional text color e.g. #FFFFFF")
def add_subtitle_cmd(bundle: str, text: str, start: float, dur: float,
                     size: Optional[float], color: Optional[str]) -> None:
    """Insert a 字幕 (materials.texts entry) into a draft bundle and write it back."""
    b = DraftBundle.resolve(bundle)
    draft = parse_bundle(b)
    mat_id = agent_api.insert_subtitle(
        draft, text=text, start=start, dur=dur, text_size=size, text_color=color
    )
    write_bundle(draft, b)
    click.echo(f"inserted 字幕 material {mat_id} at {start}s (+{dur}s) and wrote {b.template_path}")


@cli.command("add-voiceover")
@click.argument("bundle", type=click.Path(exists=True, file_okay=False))
@click.option("--path", "path", required=True, help="audio file path for the 配音 material")
@click.option("--start", "start", required=True, type=float, help="timeline start, seconds")
@click.option("--dur", "dur", required=True, type=float, help="duration, seconds")
@click.option("--name", "name", default=None, help="optional material display name")
def add_voiceover_cmd(bundle: str, path: str, start: float, dur: float,
                      name: Optional[str]) -> None:
    """Insert a 配音 (audio material + segment) into a draft bundle and write it back."""
    b = DraftBundle.resolve(bundle)
    draft = parse_bundle(b)
    mat_id = agent_api.add_voiceover(draft, path=path, start=start, dur=dur, name=name)
    write_bundle(draft, b)
    click.echo(f"inserted 配音 material {mat_id} at {start}s (+{dur}s) and wrote {b.template_path}")


@cli.command("add-transition")
@click.argument("bundle", type=click.Path(exists=True, file_okay=False))
@click.option("--name", "name", required=True, help="transition name")
@click.option("--dur", "dur", required=True, type=float, help="duration, seconds")
@click.option("--path", "path", default=None, help="optional transition asset path")
def add_transition_cmd(bundle: str, name: str, dur: float, path: Optional[str]) -> None:
    """Append a transition entry to materials.transitions and write it back."""
    b = DraftBundle.resolve(bundle)
    draft = parse_bundle(b)
    mat_id = agent_api.add_transition(draft, name=name, duration=dur, path=path)
    write_bundle(draft, b)
    click.echo(f"inserted 转场 material {mat_id} ({name}, +{dur}s) and wrote {b.template_path}")


@cli.command("write")
@click.argument("bundle", type=click.Path(exists=True, file_okay=False))
def write_cmd(bundle: str) -> None:
    """Re-serialize a bundle's template.tmp from its current on-disk JSON (no-op round-trip).

    Useful to canonicalise a draft's template.tmp after manual edits, or to
    prove parse -> write round-trip safety.
    """
    b = DraftBundle.resolve(bundle)
    draft = parse_bundle(b)
    write_bundle(draft, b)
    click.echo(f"round-trip wrote {b.template_path} ({len(draft_to_dict(draft))} top-level keys)")


@cli.command("list-projects")
@click.option("--root", "root", default=None, type=click.Path(exists=True, file_okay=False),
              help="projects root (default: 剪映 default root)")
def list_projects_cmd(root: Optional[str]) -> None:
    """List draft bundles under the (default) 剪映 projects root."""
    from pathlib import Path

    root_path = Path(root) if root else DEFAULT_DRAFT_ROOT
    names = DraftBundle.list_projects(root_path)
    if not names:
        click.echo(f"(no drafts under {root_path})")
        return
    for n in names:
        click.echo(n)


def main() -> None:  # pragma: no cover - entry point
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
