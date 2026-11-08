#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
  echo 'Run as root: sudo ./uninstall.sh' >&2
  exit 1
fi
systemctl disable --now cpu-temp-display.service 2>/dev/null || true
rm -f /etc/systemd/system/cpu-temp-display.service /etc/udev/rules.d/70-cpu-temp-display.rules
rm -rf /usr/local/lib/cpu-temp-display
systemctl daemon-reload
udevadm control --reload-rules
# Keep the system account to avoid deleting an account unexpectedly.
echo 'The service and files were removed. The system account was preserved.'
