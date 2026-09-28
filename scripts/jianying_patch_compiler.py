#!/usr/bin/env python3
"""Compile a cinematic-edit-workflow EDL into a Jianying 11.5 draft patch plan.

The output intentionally stops at Jianying's validated planning boundary. Applying a
patch requires an authorized Jianying host, the real project/material identifiers,
and the application's PC confirmation. This script never edits draft files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


MICROSECONDS = 1_000_000


class CompileError(ValueError):
    pass


def configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompileError(f"无法读取JSON：{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CompileError(f"JSON根节点必须是对象：{path}")
    return value


def to_us(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CompileError(f"{field}必须是数字")
    result = round(float(value) * MICROSECONDS)
    if result < 0:
        raise CompileError(f"{field}不能为负数")
    return result


def read_us(item: dict[str, Any], us_key: str, seconds_keys: tuple[str, ...]) -> int | None:
    if us_key in item:
        value = item[us_key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise CompileError(f"{us_key}必须是非负整数微秒")
        return value
    for key in seconds_keys:
        if key in item:
            return to_us(item[key], key)
    return None


def material_entries(material_map: dict[str, Any]) -> dict[str, Any]:
    entries = material_map.get("materials", material_map)
    if not isinstance(entries, dict):
        raise CompileError("material_map的materials必须是对象")
    return entries


def resolve_material_id(source_id: str, entries: dict[str, Any]) -> str:
    entry = entries.get(source_id)
    if isinstance(entry, str) and entry:
        return entry
    if isinstance(entry, dict):
        value = entry.get("material_id") or entry.get("materialId")
        if isinstance(value, str) and value:
            return value
    raise CompileError(f"素材 {source_id} 缺少真实的剪映material_id")


def compile_patch(
    edl: dict[str, Any],
    material_map: dict[str, Any],
    project_id: str,
    draft_ref: str,
    run_id: str,
    base_revision: int,
) -> dict[str, Any]:
    ranges = edl.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise CompileError("EDL ranges必须是非空数组")
    if not project_id:
        raise CompileError("project_id不能为空")
    if not draft_ref:
        raise CompileError("draft_ref不能为空")
    if base_revision < 0:
        raise CompileError("base_revision不能为负数")

    entries = material_entries(material_map)
    tracks: list[str] = []
    for index, item in enumerate(ranges):
        if not isinstance(item, dict):
            raise CompileError(f"ranges[{index}]必须是对象")
        track_id = item.get("video_track") or item.get("track") or "V1"
        if not isinstance(track_id, str) or not track_id:
            raise CompileError(f"ranges[{index}]的视频轨道无效")
        if track_id not in tracks:
            tracks.append(track_id)

    operations: list[dict[str, Any]] = [
        {"op": "add_track", "type": "video", "trackId": track_id, "index": index}
        for index, track_id in enumerate(tracks)
    ]

    sequence_cursor_us = 0
    for index, item in enumerate(ranges):
        source_id = item.get("source")
        if not isinstance(source_id, str) or not source_id:
            raise CompileError(f"ranges[{index}].source不能为空")
        material_id = resolve_material_id(source_id, entries)

        source_in_us = read_us(item, "source_in_us", ("source_in_seconds", "start"))
        source_out_us = read_us(item, "source_out_us", ("source_out_seconds", "end"))
        if source_in_us is None or source_out_us is None:
            raise CompileError(f"ranges[{index}]缺少源入点或出点")
        if source_out_us <= source_in_us:
            raise CompileError(f"ranges[{index}]源出点必须晚于入点")
        duration_us = source_out_us - source_in_us

        record_in_us = read_us(
            item,
            "record_in_us",
            ("record_in_seconds", "record_start", "output_start"),
        )
        if record_in_us is None:
            record_in_us = sequence_cursor_us
        sequence_cursor_us = max(sequence_cursor_us, record_in_us + duration_us)

        clip_id = item.get("id") or f"shot-{index + 1:04d}"
        if not isinstance(clip_id, str) or not clip_id:
            raise CompileError(f"ranges[{index}].id必须是非空字符串")

        metadata = {
            "sourceId": source_id,
            "role": str(item.get("role", "")),
            "selectionReason": str(item.get("selection_reason", item.get("reason", ""))),
            "transformIntent": str(item.get("transform", "native")),
            "transitionIntent": str(item.get("transition", "cut")),
        }
        operations.append(
            {
                "op": "add_clip",
                "type": "video",
                "trackId": item.get("video_track") or item.get("track") or "V1",
                "clipId": clip_id,
                "materialId": material_id,
                "startUs": record_in_us,
                "durationUs": duration_us,
                "inUs": source_in_us,
                "outUs": source_out_us,
                "metadata": metadata,
            }
        )

    return {
        "schemaVersion": 1,
        "type": "draft_patch",
        "targetProjectId": project_id,
        "runId": run_id,
        "baseRevision": base_revision,
        "summary": (
            f"assembly plan: {len(ranges)} clips on {len(tracks)} video track(s); "
            "application requires Jianying host compilation and PC confirmation"
        ),
        "lyraDraftRef": draft_ref,
        "lyraCommands": [
            {"subcommand": "extract", "args": ["--params", "scope=summary"]}
        ],
        "operations": operations,
    }


def validate_with_cli(cli: Path, patch_path: Path) -> dict[str, Any]:
    if not cli.is_file():
        raise CompileError(f"找不到剪映Agent CLI：{cli}")
    env = os.environ.copy()
    env.setdefault("JIANYING_AGENT_RUNTIME_TOKEN", "local-validation")
    result = subprocess.run(
        [str(cli), "draft", "validate-patch", "--input", str(patch_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    output = (result.stdout or result.stderr).strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as exc:
        raise CompileError(f"剪映验证器返回了非JSON结果：{output}") from exc
    if result.returncode != 0 or not payload.get("ok") or not payload.get("result", {}).get("valid"):
        raise CompileError(f"剪映补丁验证失败：{output}")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将源时间码EDL编译为剪映11.5可验证的装配补丁计划；不会修改草稿。"
    )
    parser.add_argument("edl", type=Path)
    parser.add_argument("material_map", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--draft-ref", required=True)
    parser.add_argument("--run-id", default="cinematic-edit-workflow")
    parser.add_argument("--base-revision", type=int, default=0)
    parser.add_argument("--validate-cli", type=Path)
    parser.add_argument("--validation-output", type=Path)
    return parser


def main() -> int:
    configure_console_encoding()
    args = build_parser().parse_args()
    try:
        patch = compile_patch(
            load_json(args.edl),
            load_json(args.material_map),
            args.project_id,
            args.draft_ref,
            args.run_id,
            args.base_revision,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.validate_cli:
            validation = validate_with_cli(args.validate_cli, args.output)
            validation_path = args.validation_output or args.output.with_suffix(".validation.json")
            validation_path.write_text(
                json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        print(f"已生成剪映装配补丁计划：{args.output}")
        return 0
    except CompileError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
