#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
while [[ $# -gt 0 ]]; do
  case "$1" in --codex-home) CODEX_HOME_DIR="$2"; shift 2 ;; *) shift ;; esac
done
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PY="$ROOT/.venv/bin/python"

for f in SKILL.md VERSION scripts/footage_indexer.py scripts/jianying_patch_compiler.py scripts/edl_export.py scripts/qc.py; do
  [[ -f "$ROOT/$f" ]] || { echo "Missing: $f" >&2; exit 1; }
done
[[ -x "$PY" ]] || { echo "Missing .venv; run ./install.sh" >&2; exit 1; }
"$PY" -c "import cv2, PIL, scenedetect; print('Python dependencies: OK')"
ffmpeg -hide_banner -version | head -1
ffprobe -hide_banner -version | head -1
for s in footage_indexer jianying_patch_compiler edl_export qc; do "$PY" "$ROOT/scripts/$s.py" --help >/dev/null; done
"$PY" -m unittest discover -s "$ROOT/tests" -p "test_*.py"
[[ -e "$CODEX_HOME_DIR/skills/cinematic-edit-workflow" ]] || { echo "Skill not registered in $CODEX_HOME_DIR/skills" >&2; exit 1; }
echo "Cinematic Edit Workflow $(cat "$ROOT/VERSION") verified (macOS/Linux)."
