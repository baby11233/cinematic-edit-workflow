# Jianying 11.5 editing backend

Read this reference when the user explicitly chooses Jianying Professional as the editor or asks for an editable Jianying project. The repository remains authoritative for review and editorial decisions; Jianying is the only timeline and delivery application in this mode. FFmpeg remains available for indexing and independent output verification, not for assembling the final edit.

## Proven local boundary

The workflow was evaluated against Jianying Professional `11.5.0.14471` and `jianying-agent-cli 0.1.0` on Windows. The installed agent accepts `query-content`, `plan-patch`, `validate-patch`, and `apply-patch`. Its validated operation vocabulary includes tracks, clips, trim, split, move, effects, transitions, and timeline properties.

Treat this as a version-gated internal interface, not a public stable SDK:

- never edit encrypted draft JSON directly;
- never bypass `JIANYING_AGENT_RUNTIME_TOKEN`, the authorized host requirement, or PC confirmation;
- never call `apply-patch` against a guessed project, material id, draft ref, or revision;
- do not store runtime tokens in project files, logs, Git, or chat;
- if the installed version or validation behavior changes, stop before applying and re-run a representative non-mutating probe.

`scripts/jianying_patch_compiler.py` compiles and optionally validates an assembly plan. It deliberately does not apply the plan. Application must occur through Jianying's authorized host after the user approves the concrete change.

## Workflow

1. Complete the normal footage inventory, filmstrip review, script or music analysis, material review, continuity map, selection matrix, and editorial strategy.
2. Create EDL v2 with original-source identifiers, source in/out, record in, track, selection reason, transform intent, transition intent, and handles. Browse proxies are never timeline sources.
3. Open or create the target Jianying project, set canvas and frame rate, import original media, and obtain the real project id, draft ref, base revision, and material ids from the authorized project context.
4. Persist those ids in `edit/jianying/material_map.json`. Match each id to an original source fingerprint; never map by display name or list order alone.
5. Compile the assembly plan and validate it with the exact installed `jianying-agent-cli` before any mutation.
6. Apply one scene, sequence, or editorial phase at a time. Re-read the project and revision after each accepted patch. If the revision changed, regenerate; do not force a stale patch.
7. Export a lightweight preview from Jianying, inspect it, revise the EDL and project memory, and then generate the next patch. Treat manual Jianying changes as project state that must be reconciled back into the EDL or operation log.
8. Lock picture before subtitles, complex transitions, paid effects, color styling, or final mix. Use Jianying for all timeline edits and delivery in this mode.
9. Verify the exported files independently according to `production.md` and archive the editable project.

## Staged editing

Do not apply a single monolithic patch. Use narrow, reviewable stages:

1. **structure** — project settings, stable media mapping, track plan;
2. **assembly** — source ranges, record positions, basic audio inclusion;
3. **fine cut** — trim, move, split, J/L cuts, reactions and inserts;
4. **continuity** — only evidence-backed reframes, mirrors, action repairs and bridges;
5. **sound** — dialogue, ambience, effects and music on separate tracks where sources permit;
6. **finish** — subtitles, titles, transitions, color and platform packaging after picture lock.

The compiler currently emits the proven assembly vocabulary (`add_track` and `add_clip`) plus editorial metadata. Treat transform, transition and repair fields as intent until their exact Jianying resource/property mapping has been tested in a disposable project. Do not silently convert intent into an unverified effect id.

## Timeline versions

Keep recoverable milestones in Jianying rather than repeatedly overwriting one timeline. Use project-appropriate names such as:

```text
10_SELECTS
20_ASSEMBLY
30_FINE_CUT
40_CONTINUITY
50_SOUND
60_PICTURE_LOCK
70_FINAL
```

For an ambiguous beat, create short performance-first and continuity-first alternatives and compare them without music before choosing. Persist the result in `selection_matrix.md`.

## Apply gate

Before an authorized apply, confirm all of the following:

- exact Jianying app and agent CLI version recorded;
- target project and active timeline visible in Jianying;
- material ids verified against paths and fingerprints;
- patch target project id, draft ref, run id, and base revision match current state;
- `validate-patch` returned `ok: true` and `valid: true`;
- patch scope and expected clip/track counts reviewed;
- a recoverable pre-apply project milestone exists;
- the user has approved the concrete PC confirmation.

After apply, compare actual tracks, clip count, source ranges, record positions and duration to the EDL. A successful process exit is not evidence that the edit is correct.

## Failure and fallback

- Validation failure: do not apply; save diagnostics and correct the EDL, material map, or version assumptions.
- Revision conflict: query current state and regenerate from the new revision.
- Unknown resource/effect id: omit the effect and leave a documented manual finishing instruction.
- Authorized host unavailable: deliver the validated patch plan, timeline map, SRT, stems and reference preview for controlled in-app reconstruction.
- Export mismatch: return to the Jianying project; do not repair the final master by replacing the native timeline with an FFmpeg assembly.

## Archive

After each picture lock and final delivery, close the draft editor and preserve the complete Jianying project through the application's supported local/cloud mechanism plus a local archive when accessible. Record app version, project id, timeline name, material manifest, patch history, export settings, validation results and final media checks. Cloud sync alone is not the project record.
