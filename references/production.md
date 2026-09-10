# Rendering, finishing, and verification

Preserve source files. Put generated artifacts under `<project>/edit/`. The final EDL must reference original sources and source timecodes; automatically split clips are browsing proxies unless the project explicitly adopts them as intermediates.

Use per-segment extraction when shots need individual transforms, speed, or grade. Add short audio fades at hard segment boundaries to prevent clicks. Do not cut dialogue inside a word; use verified word boundaries and small handles when transcript timestamps may drift.

Apply subtitles after visual overlays so graphics cannot hide them. Shift timed overlays from their own frame zero to the intended output window. Avoid unnecessary repeated encoding; use intermediate codecs or a controlled single finishing encode appropriate to the project.

Before a full render, test global effects, framing, titles, transitions, and color treatments on representative short samples. Inspect skin, highlights, blacks, motion, safe areas, and existing branding.

Distinguish mixing from mastering. Independent dialogue/music/ambience/effects balance requires separate stems. With only a stereo master, report the work as mastering or enhancement.

Rendered-output QC must include:

- every cut and transition boundary;
- first and last two seconds;
- all overlays, titles, subtitles, reframes, speed changes, and global effects;
- representative dark, bright, high-motion, and skin-tone frames;
- audible clicks, unwanted gaps, clipping, intelligibility, loudness, and true peak after delivery encoding;
- full decode plus duration, dimensions, frame rate, video/audio stream, and aspect verification.

Cap blind automatic repair loops. If a defect remains after three evidence-driven render/review passes, document it for user judgment.
