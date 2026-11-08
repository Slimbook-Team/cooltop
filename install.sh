#!/usr/bin/env bash
set -euo pipefail
if (( EUID != 0 )); then
  echo 'Run as root: sudo ./install.sh' >&2
  exit 1
fi
cd "$(dirname "$0")"
for command in python3 systemctl udevadm getent; do
  command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 1; }
done
python3 - <<'CHECK'
import sys
if sys.version_info < (3, 10):
    raise SystemExit('Python 3.10 or later is required.')
CHECK
if ! getent group cpu-temp-display >/dev/null; then
  groupadd --system cpu-temp-display
fi
if ! id cpu-temp-display >/dev/null 2>&1; then
  useradd --system --no-create-home --gid cpu-temp-display --shell /usr/sbin/nologin cpu-temp-display
fi
install -d -m 0755 /usr/local/lib/cpu-temp-display
install -m 0755 cpu_temp_display.py /usr/local/lib/cpu-temp-display/cpu_temp_display.py
install -m 0644 udev/70-cpu-temp-display.rules /etc/udev/rules.d/70-cpu-temp-display.rules
install -m 0644 systemd/cpu-temp-display.service /etc/systemd/system/cpu-temp-display.service
udevadm control --reload-rules
udevadm trigger --subsystem-match=hidraw || true
systemctl daemon-reload
# Deliberately do NOT auto-enable or start an unverified USB driver.
echo 'Installed; service NOT started or enabled.'
echo 'Inspect hardware first: python3 /usr/local/lib/cpu-temp-display/cpu_temp_display.py list'
echo 'After confirming a manual test: sudo systemctl enable --now cpu-temp-display.service'
