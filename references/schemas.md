# Persistent project artifacts

Use the following layout as project memory. Omit artifacts that genuinely do not apply, but do not replace persistent records with chat-only conclusions.

```text
<project>/edit/
├── footage_index/
│   ├── CODEX_INDEX.md
│   ├── manifest.json
│   ├── source_registry.json   # fingerprint -> SRC id, append-only; never edit by hand
│   ├── shots.csv
│   └── sources/
├── material_review.md
├── usable_ranges.json
├── similarity_notes.md
├── script_breakdown.md       # narrative mode
├── continuity_map.md         # narrative mode
├── selection_matrix.md       # narrative mode with alternate takes or continuity tradeoffs
├── music_map.md              # montage mode
├── edl.json
├── davinci/                  # when DaVinci Resolve is the requested editor
│   ├── <edl>.fcpxml
│   ├── <edl>.edl
│   └── import_check.md
├── jianying/                 # when Jianying is the requested editor
│   ├── material_map.json
│   ├── patches/
│   ├── validation/
│   ├── operation_log.json
│   ├── export_settings.md
│   ├── app-version.txt
│   └── project-archive/
├── verify/                   # includes *.qc.json from scripts/qc.py
├── preview.mp4
├── final.mp4
└── project.md
```

Minimum EDL structure:

```json
{
  "version": 1,
  "mode": "montage-or-narrative",
  "sources": {"SRC0001": "absolute/original/source.mp4"},
  "ranges": [
    {
      "source": "SRC0001",
      "start": 0.0,
      "end": 2.4,
      "role": "project-specific role",
      "reason": "selection and cut rationale",
      "audio": "source|music|mute|custom",
      "transition": "cut"
    }
  ],
  "total_duration_seconds": 2.4
}
```

For Jianying projects, use EDL version 2 while retaining the original second-based fields for readability. Add exact microsecond and record-position fields where known:

```json
{
  "version": 2,
  "timeline": {"frame_rate": 25, "width": 1920, "height": 1080},
  "sources": {"SRC0001": "absolute/original/source.mp4"},
  "ranges": [
    {
      "id": "shot-0001",
      "source": "SRC0001",
      "start": 5.1,
      "end": 7.5,
      "source_in_us": 5100000,
      "source_out_us": 7500000,
      "record_in_us": 0,
      "video_track": "V1",
      "role": "project-specific role",
      "selection_reason": "specific dramatic or informational gain",
      "transform": "native",
      "transition": "cut",
      "handles_frames": 8
    }
  ]
}
```

`material_map.json` must map stable source ids to real Jianying material ids obtained from the authorized target project. Include original path, size and fingerprint when available. Never infer a material id from display name or media order.

`material_review.md` must record review coverage, literal event, subjects/environment, shot language, information, emotional effect, strong moments, candidate ranges, defects, possible uses, functional similarity, and uncertainty for every source/detected shot.

When narrative selection has meaningful alternatives, `selection_matrix.md` should record one row per beat/candidate with source range, coverage function, performance or dramatic value, defect class and salience, repairability, minimum useful duration, decision, and reason. Keep value and risk in separate fields so a clean but weak take does not silently outrank a stronger repairable moment.

Optional EDL fields may record evidence behind a transformation or compromise:

```json
{
  "transform": "native|hflip|reframe|custom",
  "selection_reason": "specific dramatic or informational gain",
  "continuity_compromise": "none or documented visible risk",
  "repair": "insert, reaction, action cut, mirror, crop, or custom"
}
```

Append each work session to `project.md` with strategy, decisions and reasons, verification performed, outstanding questions, and package version.

`SRC` identifiers are stable: `source_registry.json` maps a content fingerprint (size + head + tail bytes) to its id and only ever appends. Adding, removing or moving footage never renumbers existing sources, so an EDL written earlier keeps pointing at the same media. EDL `sources` paths are authoring-machine paths; on another machine remap them at export time with `edl_export.py --path-map` rather than editing the EDL.

Without an explicit `record_in*`, a range is appended after the previous range **on the same track**.
