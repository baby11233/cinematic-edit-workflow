#!/usr/bin/env python3
"""Automated delivery QC for a rendered file (Windows / macOS / Linux, FFmpeg only).

Checks: stream/dimension/fps/duration facts, full decode errors, black frames, frozen frames,
silence gaps, integrated loudness and true peak. Writes <name>.qc.json next to --out-dir and
prints a short verdict. It supports, but never replaces, visual inspection of every cut.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def find_tool(name: str, hint: str | None, required: bool = True) -> str | None:
    if hint and Path(hint).is_file():
        return str(Path(hint).resolve())
    found = shutil.which(name)
    if found:
        return found
    here = Path(__file__).resolve().parent / "bin"
    for candidate in (here / name, here / f"{name}.exe", Path("/opt/homebrew/bin") / name, Path("/usr/local/bin") / name):
        if candidate.is_file():
            return str(candidate)
    if required:
        raise SystemExit(f"{name} not found; install FFmpeg or pass --{name}")
    return None


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, encoding="utf-8", errors="replace",
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def probe_with_ffmpeg(ffmpeg: str, path: Path) -> dict:
    """The bundled Windows package ships ffmpeg without ffprobe; parse `ffmpeg -i` instead."""
    log = run([ffmpeg, "-hide_banner", "-i", str(path)]).stderr
    streams = []
    duration = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", log)
    video = re.search(r"Stream #\S+: Video: (\w+).*?, (\d{2,5})x(\d{2,5})[^,]*, .*?([\d.]+) fps", log)
    audio = re.search(r"Stream #\S+: Audio: (\w+)[^\n]*?, (\d+) Hz", log)
    if video:
        streams.append({"codec_type": "video", "codec_name": video[1], "width": int(video[2]),
                        "height": int(video[3]), "avg_frame_rate": f"{float(video[4])}/1"})
    if audio:
        streams.append({"codec_type": "audio", "codec_name": audio[1], "sample_rate": audio[2]})
    seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3]) if duration else 0
    return {"streams": streams, "format": {"duration": seconds}}


def probe(ffprobe: str | None, ffmpeg: str, path: Path) -> dict:
    if not ffprobe:
        return probe_with_ffmpeg(ffmpeg, path)
    result = run([ffprobe, "-v", "error", "-show_entries",
                  "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,sample_rate,channels:format=duration,bit_rate",
                  "-of", "json", str(path)])
    return json.loads(result.stdout or "{}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        getattr(stream, "reconfigure", lambda **_: None)(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("media", type=Path)
    p.add_argument("--out-dir", type=Path)
    p.add_argument("--ffmpeg")
    p.add_argument("--ffprobe")
    p.add_argument("--expect-width", type=int)
    p.add_argument("--expect-height", type=int)
    p.add_argument("--expect-fps", type=float)
    p.add_argument("--target-lufs", type=float, help="e.g. -14 (web) or -23 (broadcast)")
    p.add_argument("--black-min", type=float, default=0.1, help="minimum black duration to report (s)")
    p.add_argument("--silence-db", type=float, default=-50.0)
    p.add_argument("--silence-min", type=float, default=0.5)
    p.add_argument("--freeze-min", type=float, default=1.0)
    args = p.parse_args()

    ffmpeg = find_tool("ffmpeg", args.ffmpeg)
    ffprobe = find_tool("ffprobe", args.ffprobe, required=False)
    media = args.media.resolve()
    if not media.is_file():
        raise SystemExit(f"not a file: {media}")

    info = probe(ffprobe, ffmpeg, media)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    findings: list[dict] = []

    def flag(level: str, code: str, detail: str) -> None:
        findings.append({"level": level, "code": code, "detail": detail})

    if not video:
        flag("fail", "no_video", "no video stream")
    else:
        num, _, den = (video.get("avg_frame_rate") or "0/1").partition("/")
        fps = float(num) / float(den or 1) if float(den or 1) else 0.0
        if args.expect_width and video.get("width") != args.expect_width or args.expect_height and video.get("height") != args.expect_height:
            flag("fail", "dimensions", f"{video.get('width')}x{video.get('height')}")
        if args.expect_fps and abs(fps - args.expect_fps) > 0.01:
            flag("fail", "fps", f"{fps:.3f} != {args.expect_fps}")
    if not audio:
        flag("warn", "no_audio", "no audio stream")

    # Full decode: any stderr output at -v error means corruption or a muxing problem.
    decode = run([ffmpeg, "-v", "error", "-i", str(media), "-f", "null", "-"])
    decode_errors = [line for line in decode.stderr.splitlines() if line.strip()]
    if decode.returncode != 0 or decode_errors:
        flag("fail", "decode", "; ".join(decode_errors[:5]) or f"exit {decode.returncode}")

    filters = []
    if video:
        filters += ["-vf", f"blackdetect=d={args.black_min}:pix_th=0.10,freezedetect=n=-60dB:d={args.freeze_min}"]
    if audio:
        filters += ["-af", f"silencedetect=n={args.silence_db}dB:d={args.silence_min},ebur128=peak=true"]
    analysis = run([ffmpeg, "-hide_banner", "-nostats", "-i", str(media)] + filters + ["-f", "null", "-"])
    log = analysis.stderr

    for start, end, dur in re.findall(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)", log):
        flag("warn", "black", f"{float(start):.2f}-{float(end):.2f}s ({float(dur):.2f}s)")
    freeze_starts = re.findall(r"freeze_start: ([\d.]+)", log)
    freeze_durs = re.findall(r"freeze_duration: ([\d.]+)", log)
    for start, dur in zip(freeze_starts, freeze_durs):
        flag("warn", "freeze", f"from {float(start):.2f}s for {float(dur):.2f}s")
    for start, end in re.findall(r"silence_start: ([\d.-]+)[\s\S]*?silence_end: ([\d.]+)", log):
        flag("warn", "silence", f"{float(start):.2f}-{float(end):.2f}s")

    loudness = None
    summary = log.rsplit("Summary:", 1)[-1] if "Summary:" in log else ""
    lufs = re.search(r"I:\s+(-?[\d.]+) LUFS", summary)
    peak = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary)
    if lufs:
        loudness = {"integrated_lufs": float(lufs[1]), "true_peak_dbtp": float(peak[1]) if peak else None}
        if loudness["true_peak_dbtp"] is not None and loudness["true_peak_dbtp"] > -1.0:
            flag("fail", "true_peak", f"{loudness['true_peak_dbtp']} dBTP exceeds -1.0")
        if args.target_lufs is not None and abs(loudness["integrated_lufs"] - args.target_lufs) > 1.5:
            flag("warn", "loudness", f"{loudness['integrated_lufs']} LUFS vs target {args.target_lufs}")

    # Edge frames: first/last two seconds are mandatory visual-review windows.
    edge = {"first_window_s": [0, min(2.0, duration)], "last_window_s": [max(0.0, duration - 2.0), duration]}

    report = {"file": str(media), "duration_s": duration, "video": video, "audio": audio,
              "loudness": loudness, "review_windows": edge, "findings": findings,
              "verdict": "FAIL" if any(f["level"] == "fail" for f in findings)
              else ("REVIEW" if findings else "PASS")}
    out_dir = args.out_dir or media.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{media.stem}.qc.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{report['verdict']}  {media.name}  {duration:.2f}s")
    for item in findings:
        print(f"  [{item['level']}] {item['code']}: {item['detail']}")
    if loudness:
        print(f"  loudness: {loudness['integrated_lufs']} LUFS, true peak {loudness['true_peak_dbtp']} dBTP")
    print(f"report: {target}")
    return 1 if report["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
