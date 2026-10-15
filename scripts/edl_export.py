#!/usr/bin/env python3
"""Export a cinematic-edit-workflow EDL (v1/v2) to NLE interchange files.

Targets DaVinci Resolve (Windows and macOS, Free and Studio) through File > Import > Timeline:

* FCPXML 1.9  - multi-track, preferred (``*.fcpxml``)
* CMX3600 EDL - V1 only, last-resort fallback (``*.edl``)

Pure standard library. It never edits media or project files and never talks to an NLE.
Relative-link note: Resolve relinks by file path/name, so remap paths with --path-map when
the EDL was authored on another OS (for example ``E:\\footage=/Volumes/SSD/footage``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from fractions import Fraction
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from xml.sax.saxutils import quoteattr

NTSC = {23.976: Fraction(24000, 1001), 29.97: Fraction(30000, 1001), 59.94: Fraction(60000, 1001)}
STANDARD_RES = {(1920, 1080), (3840, 2160), (1280, 720), (2560, 1440), (1080, 1920), (1080, 1080)}


class ExportError(ValueError):
    pass


def parse_fps(value: Any) -> Fraction:
    if isinstance(value, str) and "/" in value:
        num, den = value.split("/", 1)
        return Fraction(int(num), int(den))
    number = float(value)
    for key, fraction in NTSC.items():
        if abs(number - key) < 0.01:
            return fraction
    return Fraction(number).limit_denominator(1000)


def to_fraction(value: Any, field: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExportError(f"{field} must be a number")
    return Fraction(value).limit_denominator(1_000_000)


def read_time(item: dict[str, Any], us_key: str, seconds_keys: tuple[str, ...]) -> Fraction | None:
    if us_key in item:
        return Fraction(int(item[us_key]), 1_000_000)
    for key in seconds_keys:
        if key in item:
            return to_fraction(item[key], key)
    return None


def snap(value: Fraction, frame: Fraction) -> int:
    """Seconds -> whole frames on the timeline grid."""
    return int(round(value / frame))


def rational(frames: int, frame: Fraction) -> str:
    total = frames * frame
    if total == 0:
        return "0s"
    return f"{total.numerator}/{total.denominator}s"


def file_uri(raw: str, path_map: list[tuple[str, str]]) -> str:
    for old, new in path_map:
        if raw.replace("\\", "/").lower().startswith(old.replace("\\", "/").lower()):
            raw = new + raw[len(old):]
            break
    if re.match(r"^[A-Za-z]:[\\/]", raw):
        return PureWindowsPath(raw).as_uri()
    if not raw.startswith("/"):
        raise ExportError(f"source path must be absolute (use --path-map): {raw}")
    return PurePosixPath(raw).as_uri()


def display_name(raw: str) -> str:
    return re.split(r"[\\/]", raw)[-1]


class Clip:
    def __init__(self, item: dict[str, Any], index: int, frame: Fraction, cursor: int):
        self.id = str(item.get("id") or f"shot-{index + 1:04d}")
        self.source = item.get("source")
        if not isinstance(self.source, str) or not self.source:
            raise ExportError(f"ranges[{index}].source is required")
        src_in = read_time(item, "source_in_us", ("source_in_seconds", "start"))
        src_out = read_time(item, "source_out_us", ("source_out_seconds", "end"))
        if src_in is None or src_out is None or src_in < 0 or src_out <= src_in:
            raise ExportError(f"ranges[{index}] has an invalid source in/out")
        self.src_in = snap(src_in, frame)
        self.duration = max(1, snap(src_out - src_in, frame))
        rec = read_time(item, "record_in_us", ("record_in_seconds", "record_start", "output_start"))
        self.rec_in = snap(rec, frame) if rec is not None else cursor
        self.track = str(item.get("video_track") or item.get("track") or "V1")
        self.role = str(item.get("role", ""))
        self.reason = str(item.get("selection_reason", item.get("reason", "")))
        self.transform = str(item.get("transform", "native"))
        self.compromise = str(item.get("continuity_compromise", "none"))
        self.audio = str(item.get("audio", "source"))

    @property
    def rec_out(self) -> int:
        return self.rec_in + self.duration


def load_clips(edl: dict[str, Any], frame: Fraction) -> list[Clip]:
    ranges = edl.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise ExportError("EDL ranges must be a non-empty array")
    clips: list[Clip] = []
    cursors: dict[str, int] = {}  # omitted record_in => append after the previous clip on the same track
    for index, item in enumerate(ranges):
        if not isinstance(item, dict):
            raise ExportError(f"ranges[{index}] must be an object")
        track = str(item.get("video_track") or item.get("track") or "V1")
        clip = Clip(item, index, frame, cursors.get(track, 0))
        cursors[track] = max(cursors.get(track, 0), clip.rec_out)
        clips.append(clip)
    for track in {c.track for c in clips}:
        lane = sorted((c for c in clips if c.track == track), key=lambda c: c.rec_in)
        for a, b in zip(lane, lane[1:]):
            if b.rec_in < a.rec_out:
                raise ExportError(f"overlap on {track}: {a.id} and {b.id}; move one to another track")
    return clips


def track_number(name: str) -> int:
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else 1


def build_fcpxml(edl: dict[str, Any], clips: list[Clip], frame: Fraction, args: argparse.Namespace,
                 manifest: dict[str, Any] | None) -> str:
    timeline = edl.get("timeline", {})
    width = int(args.width or timeline.get("width") or 1920)
    height = int(args.height or timeline.get("height") or 1080)
    sources = edl.get("sources", {})
    path_map = [tuple(item.split("=", 1)) for item in args.path_map]
    durations: dict[str, Fraction] = {}
    for source in (manifest or {}).get("sources", []):
        durations[source["source_id"]] = Fraction(source["metadata"]["duration"]).limit_denominator(100000)

    used = sorted({c.source for c in clips})
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<!DOCTYPE fcpxml>', '<fcpxml version="1.9">', "  <resources>",
             f'    <format id="r0" name="CEW_{width}x{height}" frameDuration="{rational(1, frame)}" '
             f'width="{width}" height="{height}"/>']
    asset_ids = {}
    for number, source in enumerate(used, 1):
        if source not in sources:
            raise ExportError(f"source {source} missing from EDL sources")
        raw = sources[source]
        need = max(c.src_in + c.duration for c in clips if c.source == source) * frame
        total = max(durations.get(source, need), need)
        asset_ids[source] = f"a{number}"
        lines.append(f'    <asset id="a{number}" name={quoteattr(display_name(raw))} start="0s" '
                     f'duration="{total.numerator}/{total.denominator}s" hasVideo="1" hasAudio="1" format="r0" '
                     f'src={quoteattr(file_uri(raw, path_map))}/>')
    lines.append("  </resources>")

    base = sorted((c for c in clips if track_number(c.track) == 1), key=lambda c: c.rec_in)
    overlay = [c for c in clips if track_number(c.track) != 1]
    end = max(c.rec_out for c in clips)

    def clip_xml(c: Clip, lane: int | None, offset: int, indent: str, children: str = "") -> str:
        attrs = (f'ref="{asset_ids[c.source]}" name={quoteattr(c.id + (" " + c.role if c.role else ""))} '
                 f'offset="{rational(offset, frame)}" start="{rational(c.src_in, frame)}" '
                 f'duration="{rational(c.duration, frame)}" format="r0" tcFormat="NDF"')
        if lane:
            attrs += f' lane="{lane}"'
        inner = []
        if c.audio == "mute":
            inner.append('<adjust-volume amount="-96dB"/>')
        if c.transform not in ("native", "") or (c.compromise not in ("none", "")):
            text = f"{c.transform} | {c.compromise} | {c.reason}".strip()
            inner.append(f'<marker start="{rational(c.src_in, frame)}" duration="{rational(1, frame)}" '
                         f'value={quoteattr(text[:300])}/>')
        body = "".join(f"\n{indent}  {x}" for x in inner) + children
        return f"{indent}<asset-clip {attrs}>{body}\n{indent}</asset-clip>" if body else f"{indent}<asset-clip {attrs}/>"

    def attach(parent_offset: int, parent_start: int, parent_end: int, indent: str) -> str:
        out = ""
        for c in sorted(overlay, key=lambda c: (track_number(c.track), c.rec_in)):
            if parent_offset <= c.rec_in < parent_end:
                child_offset = parent_start + (c.rec_in - parent_offset)
                out += "\n" + clip_xml(c, track_number(c.track) - 1, child_offset, indent)
        return out

    spine: list[str] = []
    cursor = 0
    covered_overlay: set[str] = set()
    for c in base:
        if c.rec_in > cursor:
            gap = c.rec_in - cursor
            kids = attach(cursor, 0, c.rec_in, "            ")
            spine.append(f'          <gap name="Gap" offset="{rational(cursor, frame)}" start="0s" '
                         f'duration="{rational(gap, frame)}">{kids}\n          </gap>' if kids else
                         f'          <gap name="Gap" offset="{rational(cursor, frame)}" start="0s" '
                         f'duration="{rational(gap, frame)}"/>')
        kids = attach(c.rec_in, c.src_in, c.rec_out, "            ")
        spine.append(clip_xml(c, None, c.rec_in, "          ", kids))
        cursor = c.rec_out
    if cursor < end:  # overlays past the last V1 clip hang from a trailing gap
        kids = attach(cursor, 0, end, "            ")
        spine.append(f'          <gap name="Gap" offset="{rational(cursor, frame)}" start="0s" '
                     f'duration="{rational(end - cursor, frame)}">{kids}\n          </gap>')
    if not base:
        kids = attach(0, 0, end, "            ")
        spine.append(f'          <gap name="Base" offset="0s" start="0s" duration="{rational(end, frame)}">{kids}\n          </gap>')

    name = args.name or edl.get("name") or "CEW Assembly"
    lines += ["  <library>", '    <event name="Cinematic Edit Workflow">',
              f'      <project name={quoteattr(name)}>',
              f'        <sequence format="r0" duration="{rational(end, frame)}" tcStart="0s" tcFormat="NDF">',
              "          <spine>"]
    lines += spine
    lines += ["          </spine>", "        </sequence>", "      </project>", "    </event>", "  </library>", "</fcpxml>"]
    return "\n".join(lines) + "\n"


def timecode(frames: int, fps_nominal: int) -> str:
    seconds, frame = divmod(frames, fps_nominal)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"


def build_cmx3600(edl: dict[str, Any], clips: list[Clip], frame: Fraction, args: argparse.Namespace) -> str:
    nominal = round(1 / frame)
    base = sorted((c for c in clips if track_number(c.track) == 1), key=lambda c: c.rec_in)
    if not base:
        raise ExportError("CMX3600 needs V1 clips")
    skipped = len(clips) - len(base)
    sources = edl.get("sources", {})
    lines = [f"TITLE: {args.name or edl.get('name') or 'CEW Assembly'}", "FCM: NON-DROP FRAME", ""]
    for number, c in enumerate(base, 1):
        reel = re.sub(r"[^A-Z0-9]", "", c.source.upper())[:8] or "AX"
        lines.append(f"{number:03d}  {reel:<8} V     C        "
                     f"{timecode(c.src_in, nominal)} {timecode(c.src_in + c.duration, nominal)} "
                     f"{timecode(c.rec_in, nominal)} {timecode(c.rec_out, nominal)}")
        lines.append(f"* FROM CLIP NAME: {display_name(sources.get(c.source, c.source))}")
        lines.append(f"* COMMENT: {c.id} {c.role}".rstrip())
        lines.append("")
    if skipped:
        print(f"warning: CMX3600 carries V1 only; {skipped} clip(s) on other tracks were skipped.", file=sys.stderr)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Export a cinematic-edit-workflow EDL to FCPXML 1.9 / CMX3600 for DaVinci Resolve.")
    p.add_argument("edl", type=Path)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--format", choices=("fcpxml", "cmx3600", "both"), default="both")
    p.add_argument("--fps", help="Timeline frame rate, e.g. 25, 23.976, 24000/1001. Default: EDL timeline.frame_rate or 25.")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--manifest", type=Path, help="footage_index/manifest.json, used for true source durations.")
    p.add_argument("--path-map", action="append", default=[], metavar="FROM=TO",
                   help="Rewrite source path prefixes (repeatable), e.g. E:/footage=/Volumes/SSD/footage.")
    p.add_argument("--name")
    return p


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        getattr(stream, "reconfigure", lambda **_: None)(encoding="utf-8", errors="replace")
    args = build_parser().parse_args()
    try:
        edl = json.loads(args.edl.read_text(encoding="utf-8-sig"))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest else None
        frame = 1 / parse_fps(args.fps or edl.get("timeline", {}).get("frame_rate") or 25)
        clips = load_clips(edl, frame)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^\w.-]+", "_", args.edl.stem)
        if args.format in ("fcpxml", "both"):
            target = args.out_dir / f"{stem}.fcpxml"
            target.write_text(build_fcpxml(edl, clips, frame, args, manifest), encoding="utf-8")
            print(f"FCPXML: {target}")
        if args.format in ("cmx3600", "both"):
            target = args.out_dir / f"{stem}.edl"
            target.write_text(build_cmx3600(edl, clips, frame, args), encoding="utf-8")
            print(f"CMX3600: {target}")
        total = max(c.rec_out for c in clips)
        print(f"{len(clips)} clips, {total} frames ({float(total * frame):.3f}s) at {float(1 / frame):.3f} fps")
        return 0
    except (ExportError, OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
