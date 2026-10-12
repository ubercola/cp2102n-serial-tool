#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required. See README.md." >&2
    exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Python venv support is required. See README.md." >&2
    exit 1
fi

python3 -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/python" -m pip install \
    --no-index \
    --find-links "$PROJECT_DIR/vendor" \
    -r "$PROJECT_DIR/requirements.txt"

echo
echo "Python environment is ready."
echo "If USB permissions are not configured, run:"
echo "  sudo $PROJECT_DIR/install-udev-rule.sh"
echo "Then unplug and reconnect the CP2102N."
echo
echo "Start the tool with:"
echo "  $PROJECT_DIR/run.sh"
