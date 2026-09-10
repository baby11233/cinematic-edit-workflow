from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".mts", ".m2ts"}


def configure_console() -> None:
    """Keep status output usable in Windows hosts with a legacy code page."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Shot:
    source_id: str
    shot_id: str
    source_path: str
    source_name: str
    start: float
    end: float
    duration: float
    start_timecode: str
    end_timecode: str
    clip_path: str | None
    sheets: list[str]
    frame_count: int


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local batch footage scene indexer and filmstrip generator.")
    p.add_argument("input_dir", type=Path)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--interval", type=float, default=0.3)
    p.add_argument("--fine-interval", type=float, default=0.2)
    p.add_argument("--columns", type=int, default=5)
    p.add_argument("--rows", type=int, default=4)
    p.add_argument("--thumb-width", type=int, default=384)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--detector", choices=("adaptive", "content", "none"), default="adaptive")
    p.add_argument("--threshold", type=float)
    p.add_argument("--min-scene-len", type=float, default=0.5)
    p.add_argument("--split-mode", choices=("encode", "copy", "none"), default="encode")
    p.add_argument("--ffmpeg", default="ffmpeg")
    p.add_argument("--ffprobe", default="ffprobe")
    p.add_argument("--force", action="store_true")
    return p


def resolve_binary(value: str, names: tuple[str, ...], root: Path) -> str | None:
    candidate = Path(value)
    if candidate.is_file():
        return str(candidate.resolve())
    found = shutil.which(value)
    if found:
        return found
    app_dir = Path(__file__).resolve().parent
    for name in names:
        for path in (app_dir / "bin" / name, root / name, root / "bin" / name):
            if path.is_file():
                return str(path.resolve())
    return None


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, encoding="utf-8", errors="replace",
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None)


def discover(root: Path, output: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS and output not in path.parents:
            result.append(path.resolve())
    return sorted(result, key=lambda p: str(p).casefold())


def fingerprint(path: Path) -> str:
    stat = path.stat()
    digest = hashlib.sha256()
    digest.update(str(path.resolve()).encode("utf-8"))
    digest.update(f"|{stat.st_size}|{stat.st_mtime_ns}".encode())
    with path.open("rb") as handle:
        digest.update(handle.read(1024 * 1024))
    return digest.hexdigest()


def seconds_to_tc(value: float, filename: bool = False) -> str:
    value = max(0.0, value)
    ms = int(round(value * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    seconds, ms = divmod(ms, 1_000)
    sep = "-" if filename else ":"
    return f"{hours:02d}{sep}{minutes:02d}{sep}{seconds:02d}{sep}{ms:03d}"


def probe(path: Path, ffprobe: str | None, ffmpeg: str) -> dict[str, Any]:
    if ffprobe:
        result = run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                      "stream=width,height,r_frame_rate,avg_frame_rate,codec_name:format=duration",
                      "-of", "json", str(path)], capture=True)
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        return {
            "duration": float(data.get("format", {}).get("duration", 0)),
            "width": stream.get("width"), "height": stream.get("height"),
            "fps": stream.get("avg_frame_rate") or stream.get("r_frame_rate"),
            "codec": stream.get("codec_name"),
        }
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], text=True,
                            encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError(f"无法读取时长：{path}")
    duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    size = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", result.stderr)
    fps = re.search(r"([\d.]+)\s*fps", result.stderr)
    return {"duration": duration, "width": int(size[1]) if size else None,
            "height": int(size[2]) if size else None, "fps": fps[1] if fps else None, "codec": None}


def detect_scenes(path: Path, duration: float, detector: str, threshold: float | None,
                  min_scene_len: float) -> list[tuple[float, float]]:
    if detector == "none":
        return [(0.0, duration)]
    try:
        from scenedetect import AdaptiveDetector, ContentDetector, SceneManager, open_video
    except ImportError as exc:
        raise RuntimeError("缺少 PySceneDetect。请运行：python -m pip install -r requirements.txt") from exc
    video = open_video(str(path))
    manager = SceneManager()
    fps = float(video.frame_rate)
    min_frames = max(1, round(min_scene_len * fps))
    if detector == "adaptive":
        kwargs: dict[str, Any] = {"min_scene_len": min_frames}
        if threshold is not None:
            kwargs["adaptive_threshold"] = threshold
        manager.add_detector(AdaptiveDetector(**kwargs))
    else:
        kwargs = {"min_scene_len": min_frames}
        if threshold is not None:
            kwargs["threshold"] = threshold
        manager.add_detector(ContentDetector(**kwargs))
    manager.detect_scenes(video, show_progress=False)
    scenes = manager.get_scene_list(start_in_scene=True)
    result = [(max(0.0, a.seconds), min(duration, b.seconds)) for a, b in scenes]
    result = [(a, b) for a, b in result if b - a > 0.02] or [(0.0, duration)]
    # Detectors can still emit a very short tail or dense false cuts. Merge those
    # ranges so the requested minimum is also enforced on the final shot list.
    merged: list[tuple[float, float]] = []
    for start, end in result:
        if merged and end - start < min_scene_len:
            previous_start, _ = merged[-1]
            merged[-1] = (previous_start, end)
        else:
            merged.append((start, end))
    if len(merged) > 1 and merged[0][1] - merged[0][0] < min_scene_len:
        merged[1] = (merged[0][0], merged[1][1])
        merged.pop(0)
    return merged


def split_clip(ffmpeg: str, source: Path, destination: Path, start: float, duration: float, mode: str) -> None:
    if mode == "none":
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    base = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.6f}",
            "-i", str(source), "-t", f"{duration:.6f}", "-map", "0:v:0", "-map", "0:a?"]
    if mode == "copy":
        command = base + ["-c", "copy", "-avoid_negative_ts", "make_zero", str(destination)]
    else:
        command = base + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destination)]
    run(command)


def extract_frames(ffmpeg: str, source: Path, frame_dir: Path, start: float, duration: float,
                   interval: float, width: int) -> list[Path]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = frame_dir / "frame_%06d.jpg"
    if duration <= interval:
        fallback = frame_dir / "frame_000001.jpg"
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start + duration / 2:.6f}",
             "-i", str(source), "-frames:v", "1", "-vf", f"scale={width}:-2:flags=lanczos", str(fallback)])
        return [fallback]
    run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.6f}",
         "-i", str(source), "-t", f"{duration:.6f}", "-an", "-vf",
         f"fps=1/{interval},scale={width}:-2:flags=lanczos", "-q:v", "3", str(pattern)])
    frames = sorted(frame_dir.glob("frame_*.jpg"))
    if not frames:
        fallback = frame_dir / "frame_000001.jpg"
        run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{start:.6f}",
             "-i", str(source), "-frames:v", "1", "-vf", f"scale={width}:-2:flags=lanczos", str(fallback)])
        frames = [fallback]
    return frames


def font(size: int) -> ImageFont.ImageFont:
    candidates = [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc",
                  Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf"]
    for item in candidates:
        if item.is_file():
            return ImageFont.truetype(str(item), size)
    return ImageFont.load_default()


def make_sheets(frames: list[Path], output_dir: Path, source_name: str, shot_id: str,
                source_start: float, interval: float, columns: int, rows: int, width: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    per_page = columns * rows
    label_h, header_h, gap = 34, 58, 6
    first = Image.open(frames[0])
    thumb_h = round(width * first.height / first.width)
    first.close()
    page_w = columns * width + (columns + 1) * gap
    page_h = header_h + rows * (thumb_h + label_h) + (rows + 1) * gap
    title_font, label_font = font(22), font(17)
    outputs = []
    for page_index in range(math.ceil(len(frames) / per_page)):
        canvas = Image.new("RGB", (page_w, page_h), "#101217")
        draw = ImageDraw.Draw(canvas)
        draw.text((gap, 12), f"{shot_id}  |  {source_name}  |  page {page_index + 1}", fill="white", font=title_font)
        subset = frames[page_index * per_page:(page_index + 1) * per_page]
        for local_index, frame_path in enumerate(subset):
            global_index = page_index * per_page + local_index
            col, row = local_index % columns, local_index // columns
            x = gap + col * width
            y = header_h + gap + row * (thumb_h + label_h + gap)
            with Image.open(frame_path) as image:
                image = ImageOps.fit(image.convert("RGB"), (width, thumb_h), method=Image.Resampling.LANCZOS)
                canvas.paste(image, (x, y))
            timestamp = source_start + global_index * interval
            draw.rectangle((x, y + thumb_h, x + width, y + thumb_h + label_h), fill="#050608")
            draw.text((x + 7, y + thumb_h + 5), f"#{global_index + 1:04d}   {seconds_to_tc(timestamp)}",
                      fill="#f3c24f", font=label_font)
        target = output_dir / f"{shot_id}_sheet_{page_index + 1:03d}.jpg"
        canvas.save(target, quality=88, optimize=True)
        outputs.append(target)
    return outputs


def process_source(index: int, source: Path, output: Path, args: argparse.Namespace,
                   ffmpeg: str, ffprobe: str | None) -> dict[str, Any]:
    source_id = f"SRC{index:04d}"
    source_dir = output / "sources" / source_id
    clips_dir, sheets_dir = source_dir / "clips", source_dir / "sheets"
    metadata = probe(source, ffprobe, ffmpeg)
    boundaries = detect_scenes(source, metadata["duration"], args.detector, args.threshold, args.min_scene_len)
    shots: list[Shot] = []
    for shot_number, (start, end) in enumerate(boundaries, 1):
        shot_id = f"{source_id}_SH{shot_number:04d}"
        clip_name = f"{shot_id}_{seconds_to_tc(start, True)}_{seconds_to_tc(end, True)}.mp4"
        clip_path = clips_dir / clip_name
        split_clip(ffmpeg, source, clip_path, start, end - start, args.split_mode)
        temp_frames = source_dir / ".frames" / shot_id
        frames = extract_frames(ffmpeg, source, temp_frames, start, end - start, args.interval, args.thumb_width)
        sheets = make_sheets(frames, sheets_dir / shot_id, source.name, shot_id, start,
                             args.interval, args.columns, args.rows, args.thumb_width)
        shutil.rmtree(temp_frames, ignore_errors=True)
        shots.append(Shot(source_id, shot_id, str(source), source.name, start, end, end - start,
                          seconds_to_tc(start), seconds_to_tc(end),
                          str(clip_path) if args.split_mode != "none" else None,
                          [str(p) for p in sheets], len(frames)))
    payload = {"source_id": source_id, "source_path": str(source), "source_name": source.name,
               "fingerprint": fingerprint(source), "metadata": metadata,
               "detector": args.detector, "shots": [asdict(s) for s in shots]}
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "shots.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def relative(path: str | Path, root: Path) -> str:
    return Path(path).resolve().relative_to(root.resolve()).as_posix()


def write_outputs(output: Path, root: Path, sources: list[dict[str, Any]], args: argparse.Namespace) -> None:
    all_shots = [shot for source in sources for shot in source["shots"]]
    manifest = {"version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
                "input_dir": str(root), "output_dir": str(output),
                "settings": {"interval_seconds": args.interval, "fine_interval_seconds": args.fine_interval,
                             "detector": args.detector, "threshold": args.threshold,
                             "min_scene_len_seconds": args.min_scene_len, "split_mode": args.split_mode,
                             "sheet_grid": [args.columns, args.rows], "thumb_width": args.thumb_width},
                "source_count": len(sources), "shot_count": len(all_shots), "sources": sources}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "shots.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["source_id", "shot_id", "source_path", "source_name", "start", "end", "duration",
                  "start_timecode", "end_timecode", "clip_path", "sheets", "frame_count"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for shot in all_shots:
            row = dict(shot); row["sheets"] = " | ".join(row["sheets"]); writer.writerow(row)
    md = ["# Codex Footage Index", "", f"- 素材目录：`{root}`", f"- 素材数：{len(sources)}",
          f"- 自动镜头数：{len(all_shots)}", f"- 胶片条间隔：{args.interval:.3f} 秒",
          f"- 精查建议间隔：{args.fine_interval:.3f} 秒", "", "## 读取说明", "",
          "先读取本文件与 `manifest.json`。随后按需查看镜头对应胶片条，不要一次加载全部图片。",
          "自动分镜需要复核；最终 EDL 使用原始素材路径和源时间码。", "", "## 素材", ""]
    for source in sources:
        md.append(f"- **{source['source_id']}** `{source['source_name']}` — {len(source['shots'])} shots, {source['metadata']['duration']:.3f}s")
    (output / "CODEX_INDEX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    cards = []
    for shot in all_shots:
        sheet_links = "".join(f'<a href="{html.escape(relative(p, output))}"><img loading="lazy" src="{html.escape(relative(p, output))}"></a>' for p in shot["sheets"])
        clip = f'<video controls preload="none" src="{html.escape(relative(shot["clip_path"], output))}"></video>' if shot["clip_path"] else ""
        cards.append(f'<article><h2>{shot["shot_id"]}</h2><p>{html.escape(shot["source_name"])} · {shot["start_timecode"]} → {shot["end_timecode"]} · {shot["duration"]:.3f}s</p>{clip}<div class="sheets">{sheet_links}</div></article>')
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Footage Index</title><style>
body{{margin:0;background:#0b0d12;color:#e9edf5;font:15px system-ui,"Microsoft YaHei";padding:24px}}header{{position:sticky;top:0;background:#0b0d12ee;padding:8px 0 18px;z-index:2}}article{{border-top:1px solid #293040;padding:20px 0}}h1,h2{{margin:0 0 8px}}p{{color:#aeb8ca}}video{{width:min(720px,100%);display:block;margin:12px 0}}.sheets{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:12px}}img{{width:100%;display:block;border:1px solid #30384a}}
</style></head><body><header><h1>Footage Index</h1><p>{len(sources)} sources · {len(all_shots)} detected shots · interval {args.interval}s</p></header>{''.join(cards)}</body></html>'''
    (output / "index.html").write_text(page, encoding="utf-8")


def main() -> int:
    configure_console()
    args = build_parser().parse_args()
    if not (0.02 <= args.interval <= 5):
        raise SystemExit("--interval 必须在 0.02 到 5 秒之间")
    root = args.input_dir.resolve()
    if not root.is_dir():
        raise SystemExit(f"素材目录不存在：{root}")
    output = (args.output_dir or root / "edit" / "footage_index").resolve()
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = resolve_binary(args.ffmpeg, ("ffmpeg.exe", "ffmpeg"), root)
    ffprobe = resolve_binary(args.ffprobe, ("ffprobe.exe", "ffprobe"), root)
    if not ffmpeg:
        raise SystemExit("找不到 FFmpeg。请安装 FFmpeg 或使用 --ffmpeg 指定绝对路径。")
    videos = discover(root, output)
    if not videos:
        raise SystemExit("指定目录中没有发现视频素材。")
    cache_path = output / "cache.json"
    old_cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    settings_key = json.dumps({k: getattr(args, k) for k in ("interval", "columns", "rows", "thumb_width", "detector", "threshold", "min_scene_len", "split_mode")}, sort_keys=True)
    completed: dict[int, dict[str, Any]] = {}
    pending = []
    for index, source in enumerate(videos, 1):
        key = str(source)
        sig = fingerprint(source)
        cached = old_cache.get(key)
        source_json = output / "sources" / f"SRC{index:04d}" / "shots.json"
        if not args.force and cached == {"fingerprint": sig, "settings": settings_key} and source_json.is_file():
            completed[index] = json.loads(source_json.read_text(encoding="utf-8"))
            print(f"[缓存] {source.name}")
        else:
            pending.append((index, source))
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(process_source, i, p, output, args, ffmpeg, ffprobe): (i, p) for i, p in pending}
        for future in as_completed(futures):
            index, source = futures[future]
            completed[index] = future.result()
            print(f"[完成] {source.name} -> {len(completed[index]['shots'])} shots")
    sources = [completed[i] for i in sorted(completed)]
    write_outputs(output, root, sources, args)
    new_cache = {str(v): {"fingerprint": completed[i]["fingerprint"], "settings": settings_key}
                 for i, v in enumerate(videos, 1)}
    cache_path.write_text(json.dumps(new_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成：{output / 'index.html'}")
    print(f"Codex入口：{output / 'CODEX_INDEX.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
