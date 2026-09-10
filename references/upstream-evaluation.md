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
