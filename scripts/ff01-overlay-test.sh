#!/usr/bin/env bash
# FF-01 overlay target test launcher. Builds/runs the existing overlay.
# Never daemonizes silently: PID is printed and process stays in foreground.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/apps/overlay-linux"

echo "FF-01 TARGET VALIDATION"
echo "timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
if command -v rustc >/dev/null 2>&1; then rustc --version; fi
if command -v cargo >/dev/null 2>&1; then cargo --version; fi

echo "Launching overlay in foreground. Note the PID below."
echo "Test: press Ctrl+C (terminal SIGINT, NOT Super+C), verify exit code,"
echo "prompt returns, and no child process remains (ps -p <PID>)."
echo "PID will be printed by the shell (echo \$!)."
echo ""

# Run in foreground so Ctrl+C reaches the process.
cargo run --release &
PID=$!
echo "OVERLAY_PID=$PID"
wait $PID
CODE=$?
echo "overlay exited with code $CODE"
exit $CODE
