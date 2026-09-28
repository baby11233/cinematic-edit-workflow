# External workflow evaluation log

This package is independent of `video-use` and other editing skills. Never synchronize automatically.

When the user asks to evaluate an upstream update, record:

- upstream name and exact version or commit;
- changed behavior, not merely changed files;
- concrete benefit to this workflow;
- overlap with current rules/scripts;
- incompatible assumptions or regressions;
- licensing or dependency changes;
- representative local test input and observable result;
- decision: reject, defer, adapt manually, or adopt;
- package version increment and migration notes if adopted.

Adopt only the smallest proven change. Copying a whole updated skill would erase the independence boundary.

## Jianying Professional 11.5 backend evaluation — 2026-09-28

- Candidate: local Jianying Professional `11.5.0.14471`; bundled `jianying-agent-cli 0.1.0`.
- Observed behavior: CLI exposes draft query, plan, validate and apply stages. Binary-declared operation vocabulary includes track/clip add, remove and update; clip move, trim and split; effects; transitions; and timeline properties. Timing fields use microseconds.
- Representative test: a synthetic patch containing `add_track` and `add_clip` with material, source and record timing passed the bundled non-mutating validator with `ok: true` and `valid: true`.
- Security/compatibility boundary: apply requires an authorized Jianying host, runtime token, real draft/project/material identifiers and PC confirmation. Direct `lyra-cli` launch returned `unauthorized host process`. The interface is internal and undocumented, so version drift is a material regression risk.
- Decision: adopt a version-gated Jianying editing mode and a conservative assembly patch compiler. Do not adopt direct draft JSON mutation, host bypass, automatic confirmation, guessed effect/resource ids, or unattended apply.
- Package impact: version `1.3.0`; EDL v2 adds optional microsecond, record-position and track fields while retaining v1 compatibility.
