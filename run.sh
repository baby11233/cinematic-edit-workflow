#!/usr/bin/env bash
# Build the footage index. Usage: ./run.sh <footage-dir> [indexer options...]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
[[ -x "$ROOT/.venv/bin/python" ]] || { echo "Run ./install.sh first." >&2; exit 1; }
[[ $# -ge 1 ]] || { echo "Usage: ./run.sh <footage-dir> [options]" >&2; exit 2; }
exec "$ROOT/.venv/bin/python" "$ROOT/scripts/footage_indexer.py" "$@"
