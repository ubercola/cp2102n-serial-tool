#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "Environment is not installed. Run ./setup.sh first." >&2
    exit 1
fi

exec "$PYTHON" "$PROJECT_DIR/cp2102n_serial.py" "$@"
