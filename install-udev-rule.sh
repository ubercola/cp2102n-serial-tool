#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RULE_SOURCE="$PROJECT_DIR/udev/99-cp210x.rules"
RULE_TARGET="/etc/udev/rules.d/99-cp210x.rules"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run this script with sudo." >&2
    exit 1
fi

install -m 0644 "$RULE_SOURCE" "$RULE_TARGET"
udevadm control --reload-rules
udevadm trigger

echo "Installed $RULE_TARGET"
echo "Unplug and reconnect the CP2102N before running the tool."
