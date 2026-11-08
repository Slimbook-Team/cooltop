# Hardware testing checklist

**No live MT880-V4D validation has been completed for this pre-release.** Please follow these steps in order. Do not begin with background-service installation.

## Before power-on

- Check the internal USB cable is correctly seated and matched to the motherboard header.
- If testing LEDs, check the separate 3-pin **5 V** ARGB header. Never connect it to 12 V RGB.
- Confirm your CPU is cooled normally using working fans, independent of the screen.

## Non-writing checks

```bash
uname -r
lsusb
python3 cpu_temp_display.py list
python3 cpu_temp_display.py run --dry-run --once
python3 -m unittest discover -s tests -v
```

Make a note of the exact USB VID:PID shown by `lsusb`, the selected HID node, and the CPU sensor chosen. If the VID:PID is not `1a2c:4984`, **stop here** and file an issue instead of editing IDs or sending unknown packets.

## Manual USB write test

Only if `list` clearly selects a verified `/dev/hidraw*` interface:

```bash
sudo python3 cpu_temp_display.py run --verbose
```

Watch the physical display for 10–20 seconds. Note if the temperature changes sensibly with CPU load. Stop with Ctrl+C. If HID transport errors occur, collect the message, then optionally test the alternate known payload length:

```bash
sudo python3 cpu_temp_display.py run --report-size 65 --verbose
```

**Stop** if the display becomes unstable, shows implausible values, or errors persist. Never guess report IDs or try raw control transfers without a separately reviewed and documented implementation.

## Enable persistence only after success

```bash
sudo ./install.sh
sudo systemctl enable --now cpu-temp-display.service
sudo systemctl status cpu-temp-display.service
sudo journalctl -u cpu-temp-display.service -n 50 --no-pager
```

Check that it still works after reboot, and ideally after USB disconnect/reconnect while powered off. The service does not control cooling or fan curves.

## OpenRGB validation

Follow [OPENRGB.md](OPENRGB.md). Record your motherboard/controller model, connector (direct ARGB header vs hub), OpenRGB version and which zone reacted to a static color.

## Report template

```text
Cooler model/revision:
Distribution and version:
Kernel (uname -r):
USB ID (lsusb):
HID interface selected (list command):
CPU sensor selected:
64-byte report result:
65-byte report result (only if tested):
Temperature display updates? yes/no:
OpenRGB version and device/zone (if applicable):
Notes and any error text:
```

Please redact unique serial numbers, account names, hostnames and identifying data before posting a public issue.
