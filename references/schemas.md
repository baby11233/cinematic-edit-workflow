# Persistent project artifacts

Use the following layout as project memory. Omit artifacts that genuinely do not apply, but do not replace persistent records with chat-only conclusions.

```text
<project>/edit/
├── footage_index/
│   ├── CODEX_INDEX.md
│   ├── manifest.json
│   ├── shots.csv
│   └── sources/
├── material_review.md
├── usable_ranges.json
├── similarity_notes.md
├── script_breakdown.md       # narrative mode
├── continuity_map.md         # narrative mode
├── music_map.md              # montage mode
├── edl.json
├── verify/
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

`material_review.md` must record review coverage, literal event, subjects/environment, shot language, information, emotional effect, strong moments, candidate ranges, defects, possible uses, functional similarity, and uncertainty for every source/detected shot.

Append each work session to `project.md` with strategy, decisions and reasons, verification performed, outstanding questions, and package version.
