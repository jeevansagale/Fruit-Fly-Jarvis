#!/usr/bin/env bash
# Fruit-Fly launcher: spikes, validation, and dev vertical slice.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage: ./Run.sh [MODE]

Modes:
  (none)      smoke test + status summary (default)
  --smoke     python3 scripts/smoke_test.py
  --tests     run unit tests (unittest discover -s tests)
  --check     offline verification: unit tests + brain smoke
  --dev       one-command slice demo: brain + mock events + headless avatar
  --dev-visible like --dev, but avatar opens a real window (needs display)
  --overlay   build/run existing FF-01 overlay (foreground, Ctrl+C to stop)
  --probe     serve Three.js FF-02 probe on http://127.0.0.1:8765/
  --vision    live hand-gesture camera check (needs camera + terminal)
            ./Run.sh --vision --control to actually switch/scroll/toggle
  --validate  run FF-02C target-machine validation harness
  --help      this message

Notes:
  - No auto-installs. Missing deps print a message and exit non-zero.
  - --dev needs no display, no network, no API keys; visuals stay manual.
  - --vision needs mediapipe/opencv (`pip install mediapipe opencv-python`)
    and a camera; show palm/fist/pinch/swipes when prompted.
EOF
}

smoke() { python3 scripts/smoke_test.py; }

tests() { python3 -m unittest discover -s tests -v; }

overlay() {
  if ! command -v cargo >/dev/null 2>&1; then
    echo "Run.sh: cargo not found; install rust toolchain first." >&2; exit 1
  fi
  echo "Run.sh: launching FF-01 overlay in foreground (Ctrl+C = SIGINT to stop)."
  cargo run --release --manifest-path "$ROOT/apps/overlay-linux/Cargo.toml"
}

probe() {
  echo "Run.sh: serving static probe only (models stay local, picked via browser file picker)."
  echo "Open http://127.0.0.1:8765/ on this machine. Ctrl+C to stop."
  python3 -m http.server 8765 --bind 127.0.0.1 --directory "$ROOT/apps/avatar-renderer/probes/ff02"
}

validate() { exec "$ROOT/scripts/ff02c-validate.sh"; }

vision() { exec python3 "$ROOT/scripts/vision_check.py" "$@"; }

check() {
  python3 -m unittest discover -s tests
  python3 services/brain/main.py > /dev/null && echo "brain smoke: PASS"
  python3 scripts/smoke_test.py
}

dev() {
  dev_inner "--headless"
}

dev_visible() {
  if [ -z "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]; then
    echo "Run.sh: no display found (WAYLAND_DISPLAY/DISPLAY unset)." >&2; exit 1
  fi
  dev_inner ""
}

dev_inner() {
  local headless_flag="$1"
  echo "Dev slice: brain + events + avatar. Ctrl+C stops."
  python3 services/brain/server.py 2> /tmp/ff-brain.log &
  BRAIN_PID=$!
  AVATAR_PID=""
  cleanup() { kill "$BRAIN_PID" ${AVATAR_PID:+$AVATAR_PID} 2>/dev/null || true; }
  trap 'cleanup; exit 0' INT TERM EXIT
  sleep 1
  MODEL_RES=$(ls "$ROOT"/apps/avatar-renderer/runtime/local/*.fbx 2>/dev/null | head -n 1 || true)
  if command -v godot >/dev/null 2>&1 && [ -n "$MODEL_RES" ]; then
    MODEL_NAME="res://local/$(basename "$MODEL_RES")"
    if [ -n "$headless_flag" ]; then
      godot --headless --path "$ROOT/apps/avatar-renderer/runtime" \
        -- --model "$MODEL_NAME" --brain http://127.0.0.1:8771 > /tmp/ff-avatar.log 2>&1 &
    else
      godot --path "$ROOT/apps/avatar-renderer/runtime" \
        -- --model "$MODEL_NAME" --brain http://127.0.0.1:8771 > /tmp/ff-avatar.log 2>&1 &
    fi
    AVATAR_PID=$!
  else
    echo "avatar runtime skipped (godot or staged model unavailable)"
  fi
  python3 scripts/dev_events.py
  echo "--- brain log ---"; tail -n 8 /tmp/ff-brain.log
  if [ -n "$AVATAR_PID" ]; then
    sleep 6
    echo "--- avatar log ---"; grep -E "FF_RUNTIME|ERROR" /tmp/ff-avatar.log | head -n 8 || true
  fi
  trap - INT TERM EXIT
  cleanup
  echo "dev demo complete"
}

MODE="${1:---smoke-default}"

case "$MODE" in
  --help|-h|help) usage ;;
  --smoke) smoke ;;
  --tests|--test) tests ;;
  --check) check ;;
  --dev) dev ;;
  --dev-visible) dev_visible ;;
  --overlay) overlay ;;
  --probe) probe ;;
  --vision) shift; vision "$@" ;;
  --validate) validate ;;
  --smoke-default)
    smoke
    echo ""
    echo "Fruit-Fly: idle. Avatar not running."
    echo "Run: --dev | --overlay | --probe | --validate"
    echo "See README.md and docs/development/FF-02C-RUNBOOK.md."
    ;;
  *) echo "Run.sh: unknown mode '$MODE'. Try ./Run.sh --help" >&2; exit 1 ;;
esac
