#!/usr/bin/env bash

set -euo pipefail

if command -v quill &>/dev/null; then
  quill validate "$@"
else
  # Fallback: run from source tree (for development without uv tool install)
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  SOURCE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  PYTHONPATH="$SOURCE_ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m quill validate "$@"
fi
