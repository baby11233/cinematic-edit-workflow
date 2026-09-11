# Local indexing and deep review

Run `scripts/footage_indexer.py <footage-folder>` before editorial analysis. It uses PySceneDetect for candidate boundaries and FFmpeg for accurate split previews and time-based filmstrips. Runtime processing is local and does not call a model or upload footage.

Read generated artifacts in this order:

1. `<project>/edit/footage_index/CODEX_INDEX.md`
2. `manifest.json` or `shots.csv`
3. Only the filmstrip pages for the shot currently being reviewed
4. Original source or denser extraction only for unresolved ranges

Automatic scene boundaries are advisory. AI footage can change scene through morphing, occlusion, camera movement, flash, or subject replacement without a conventional cut. Merge false splits and add missed boundaries in the review record without modifying the original file.

Review is complete only when every supplied source is covered from beginning to end and every detected shot records:

- literal beginning, middle, and ending event;
- subjects, environment, framing, camera and subject movement, screen direction;
- information and emotional effect;
- strongest performance, reaction, action, and information moments with source timecodes, even when the full take is unsuitable;
- safe candidate ranges and minimum useful duration;
- anatomy, physics, deformation, identity, flicker, exposure, compression, continuity, or transition concerns;
- defect salience, duration, story importance, and plausible repair or coverage;
- candidate function as speaker, listener, relationship shot, action/information insert, or neutral bridge;
- plausible editorial functions and functionally similar alternatives;
- review interval and any unresolved uncertainty.

Use 0.3 seconds as the maximum baseline interval. Use 0.2 seconds or denser around fast motion, combat, impacts, flashes, transformations, hands, weapons, brief expressions, transition frames, suspected defects, and exact sync points. Decode only narrow ambiguous windows frame by frame.

Cache source identity using absolute path, size, modification time, and fingerprint. Re-index only changed sources or changed extraction settings.
