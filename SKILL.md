---
name: cinematic-edit-workflow
description: Locally index, deeply review, edit, finish, and verify pre-curated visual footage for montage, portfolio, promotional, or narrative films. Use when dense 0.3/0.2-second visual understanding and persistent project memory must drive the edit. Independent of video-use; do not use for ordinary transcript-first talking-head editing.
---

# Cinematic Edit Workflow

Use this package as the authoritative workflow. It is self-contained and must not import instructions, scripts, defaults, or assumptions from `video-use`. Treat future `video-use` releases as external candidates that require explicit comparison before anything is adopted.

## Intake and routing

Confirm that the user has already performed first-pass removal of unwanted, erroneous, and functionally repetitive source material. Preserve all supplied originals and write only beneath `<project>/edit/`.

Determine the editorial mode from the actual project:

- For music-driven montage, showreel, portfolio, or promotional work, read [references/montage.md](references/montage.md). A soundtrack is required before timing design or cutting.
- For scripted or dramatic continuity editing, read [references/narrative.md](references/narrative.md). A screenplay, outline, or explicit scene intent is normally required; music is not required for the assembly cut. When alternate takes, generated coverage, eyeline conflicts, or continuity defects affect selection, also read [references/performance-first-selection.md](references/performance-first-selection.md).
- For every project, read [references/review-and-index.md](references/review-and-index.md) before inspecting footage and [references/production.md](references/production.md) before rendering.
- Read [references/schemas.md](references/schemas.md) when creating cached review records or the EDL.

## Required gates

1. Inventory and locally index the final footage set using `scripts/footage_indexer.py`. Reuse its file-fingerprint cache when sources and settings are unchanged.
2. Review every filmstrip sequentially at no wider than 0.3 seconds. Recheck fast action, expressions, hands, effects, transformations, suspected defects, transitions, and candidate cut points at 0.2 seconds or denser. Frame extraction alone is not review.
3. Persist what each shot literally contains, communicates, and can safely contribute. Keep technical usability separate from artistic suitability.
4. Build the project-specific editorial strategy from the material, script or soundtrack, and requested outcome. In narrative work, keep dramatic value separate from defect risk and select beat-level moments before rejecting an entire take. Do not reuse the arc, shot order, pacing, grade, titles, or packaging of a previous project.
5. Present the strategy in plain language and obtain approval before creating an EDL or changing a timeline.
6. Create a source-timecode EDL, render a lightweight preview, inspect the rendered output, iterate, then finish and verify the delivery.

## Independence boundary

The package version is recorded in `VERSION`. Do not automatically merge changes from another skill. An update may be adopted only after documenting the candidate behavior, benefit, compatibility impact, regression risk, and a representative test result in `references/upstream-evaluation.md`.

## Completion

Do not claim completion from successful commands alone. Delivery requires visual inspection, audio checks appropriate to available stems, full decode verification, confirmed dimensions/frame rate/duration, and a persisted project log.
