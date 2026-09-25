#!/usr/bin/env bash
# FF-02C target-machine validation entry point.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec python3 scripts/ff02c_validate.py "$@"
