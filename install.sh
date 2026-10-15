#!/usr/bin/env bash
# macOS / Linux installer. Online install (PyPI ships arm64 + x86_64 wheels); no vendored binaries.
# Usage: ./install.sh [--python /path/to/python3] [--codex-home DIR] [--claude-skills]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
PYTHON_BIN=""
LINK_CLAUDE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PYTHON_BIN="$2"; shift 2 ;;
    --codex-home) CODEX_HOME_DIR="$2"; shift 2 ;;
    --claude-skills) LINK_CLAUDE=1; shift ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

# Homebrew is not on PATH for GUI-launched shells.
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in python3.12 python3.13 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON_BIN="$(command -v "$candidate")"; break; fi
  done
fi
[[ -n "$PYTHON_BIN" ]] || { echo "Python 3.10+ not found. Run: brew install python@3.12" >&2; exit 1; }
"$PYTHON_BIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "Python 3.10+ required: $("$PYTHON_BIN" --version)" >&2; exit 1; }

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffmpeg/ffprobe not found. Run: brew install ffmpeg" >&2
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$ROOT/.venv"
fi
"$ROOT/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/scripts/requirements-lock.txt"

link_skill() {
  local skills_dir="$1/skills" link="$1/skills/cinematic-edit-workflow"
  mkdir -p "$skills_dir"
  if [[ -L "$link" ]]; then
    [[ "$(readlink "$link")" == "$ROOT" ]] || { echo "Existing link points elsewhere: $link -> $(readlink "$link")" >&2; exit 1; }
  elif [[ -e "$link" ]]; then
    mv "$link" "$link.backup-$(date +%Y%m%d-%H%M%S)"
    ln -s "$ROOT" "$link"
  else
    ln -s "$ROOT" "$link"
  fi
  echo "Skill linked: $link"
}

link_skill "$CODEX_HOME_DIR"
if [[ "$LINK_CLAUDE" == "1" ]]; then link_skill "$HOME/.claude"; fi

"$ROOT/verify.sh" --codex-home "$CODEX_HOME_DIR"
echo "Install complete. Start a new Codex task so the skill list reloads."
