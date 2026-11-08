# CoolTop — CPU Temperature Display for Linux

**Experimental, open-source Linux driver for USB-connected CPU cooler temperature displays.**

**Repository:** [Slimbook-Team/cooltop](https://github.com/Slimbook-Team/cooltop) · [OpenRGB guide](docs/OPENRGB.md) · [Hardware testing](docs/HARDWARE_TESTING.md) · [Issues](https://github.com/Slimbook-Team/cooltop/issues)

CoolTop reads CPU temperature and usage from Linux and sends them to a compatible CPU cooler's digital display through its internal motherboard USB connection. It runs without Wine, a graphical desktop, third-party Python packages, or proprietary Windows binaries.

> [!WARNING]
> **Pre-release: real-hardware testing is pending.** The USB protocol and packet-building code have been studied and unit-tested, but this exact build has not yet been verified on an MT880-V4D display. Do **not** describe it as confirmed working until a physical test succeeds.

## What it controls

| Component | Connection | Software |
| --- | --- | --- |
| **Temperature display** | Internal motherboard USB | CoolTop (`cpu_temp_display.py`) |
| **ARGB fan lighting** | 3-pin **5 V** ARGB header or compatible ARGB controller (on applicable variants) | [OpenRGB](https://openrgb.org/) |
| **Fan speed** | Fan PWM header | BIOS/UEFI or a separate fan-control solution |

The displayed temperature is the CPU sensor reading, **not a direct measurement of the heatsink or coolant**. RGB color changes are **not** supported by this Python driver: see **[docs/OPENRGB.md](docs/OPENRGB.md)**.

## Model compatibility

| Model | Linux display status | OpenRGB lighting status |
| --- | --- | --- |
| **MT880-V4D** | **Experimental — pending USB and display test** | **Not tested on this revision** |
| MT880 (earlier model) | Not tested with this Linux driver | Previously reported working with OpenRGB on one PC; setup not yet documented |
| Other displays exposing USB ID `1a2c:4984` | May be compatible; test and report results | Depends on wiring and lighting controller |

A matching USB ID alone does not guarantee compatibility. The driver also requires a matching HID Feature report descriptor. Additional models or hardware revisions can be documented as testing progresses.

## Features

- CPU sensor selection via standard Linux `hwmon` and thermal interfaces.
- CPU utilization from `/proc/stat`.
- USB HID Feature report `0x07`, using USB ID `1a2c:4984`.
- Update interval (default one second), Celsius or Fahrenheit.
- `list` to inspect sensors/USB nodes and `--dry-run` for testing without USB writes.
- Automatic reconnection after disconnecting and reconnecting the USB device.
- Optional systemd service and narrowly scoped udev permissions.

**No firmware updates, fan-speed control, pump control, LED control, or USB-driver detachment.**

## Requirements

- Linux with **Python 3.10+**.
- Access to CPU temperature sensors under `/sys/class/hwmon` (or `/sys/class/thermal`).
- A compatible cooler attached to an internal USB header with a readable `/dev/hidraw*` interface.
- For background installation: systemd, udev, and standard Linux account tools.

On Ubuntu/Debian, `lsusb` and `sensors` are useful optional diagnostic tools:

```bash
sudo apt update
sudo apt install usbutils lm-sensors
```

## Quick start: test before installing

Clone the official CoolTop repository (or use **Code → Download ZIP** on GitHub and extract it):

```bash
git clone https://github.com/Slimbook-Team/cooltop.git
cd cooltop
```


**1. Identify your hardware without writing to USB:**

```bash
lsusb | grep -i '1a2c:4984'
python3 cpu_temp_display.py list
```

You should see a matching `/dev/hidrawN` node and ideally a `Selected device:` entry. If `lsusb` has a **different USB ID**, do not force another device ID into the script. Save the diagnostics instead. If the expected device is visible but the HID descriptor is not readable, try `sudo python3 cpu_temp_display.py list` to diagnose permissions before any USB write.

**2. Check the temperature and telemetry packet without touching the display:**

```bash
python3 cpu_temp_display.py run --dry-run --once
```

**3. Test the physical display** only when the `list` command identifies a verified interface:

```bash
sudo python3 cpu_temp_display.py run --verbose
```

Let it run for several seconds. Stop with **Ctrl+C**. This temporary root invocation is only for the initial test; normal service operation uses restricted permissions.

If the USB write fails with a report-length error, an alternative length is available for testing **only on the verified matching device**:

```bash
sudo python3 cpu_temp_display.py run --report-size 65 --verbose
```

**4. Install a background service — only after the manual test works:**

```bash
sudo ./install.sh
sudo systemctl enable --now cpu-temp-display.service
sudo systemctl status cpu-temp-display.service
```

The installer deliberately does **not** start or enable the service. You explicitly turn it on after confirming the hardware works. View logs with:

```bash
sudo journalctl -u cpu-temp-display.service -n 50 --no-pager
```

To stop it or remove it:

```bash
sudo systemctl disable --now cpu-temp-display.service
sudo ./uninstall.sh
```

## CLI options

```bash
python3 cpu_temp_display.py list
python3 cpu_temp_display.py run --dry-run --once
sudo python3 cpu_temp_display.py run --verbose
sudo python3 cpu_temp_display.py run --fahrenheit
sudo python3 cpu_temp_display.py run --sensor /sys/class/hwmon/hwmon0/temp1_input
sudo python3 cpu_temp_display.py run --interval 2
sudo python3 cpu_temp_display.py run --report-size 65
```

The `run` command sends repeated updates. A single update with `--once` might disappear quickly on displays that expect periodic telemetry.

## ARGB and OpenRGB

The digital temperature display and the fan LEDs may use **separate connections**. On a unit with 3-pin 5V ARGB lighting, OpenRGB generally controls the **motherboard ARGB header or external controller**, rather than discovering the cooler as its own USB RGB device.

An earlier MT880 setup was reportedly controlled successfully with OpenRGB, but the **MT880-V4D has not yet been physically tested here**. That makes OpenRGB a sensible first thing to try, not a guarantee of compatibility.

**[Open the full OpenRGB setup guide](docs/OPENRGB.md)** for wiring, official installation, Linux udev permissions, choosing the correct device and zone, and setting colors.

> **Electrical safety:** Never connect a 3-pin **5 V ARGB** plug to a 4-pin **12 V RGB** header. Confirm the label and pinout in your motherboard manual. Turn off the PC before moving internal RGB or USB connections.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `lsusb` doesn't show `1a2c:4984` | Inspect the internal USB cable/header; record the actual `lsusb` output. |
| Matching USB ID but no selected device | HID report descriptor may not be accessible, may differ, or the driver may not bind. **Do not bypass** the safety check. |
| No CPU temperature sensor | Run `sensors`; try `--sensor` with an existing valid `temp*_input` path. |
| `Permission denied` | Test with `sudo`; after installation check the udev rule. |
| HID write fails | Stop and collect logs; if the interface is verified, try `--report-size 65`. |
| Screen stays blank | Run for a few seconds; collect logs, exact model and USB ID. |
| ARGB is not listed in OpenRGB | Find the motherboard/controller and its ARGB zone, not necessarily the cooler name. See the separate guide. |

For a more systematic checklist, see **[docs/HARDWARE_TESTING.md](docs/HARDWARE_TESTING.md)**. Open a [hardware report issue](https://github.com/Slimbook-Team/cooltop/issues/new/choose) using the included template. Remove hardware serial numbers and private details before sharing logs.

## Development

Tests require no hardware and no third-party Python packages:

```bash
python3 -m unittest discover -s tests -v
```

Passing tests verifies program behavior and packet formatting, **not a successful hardware USB transmission**. A GitHub Actions workflow runs these tests on each push and pull request.

The packet format and its limitations are documented in **[docs/PROTOCOL.md](docs/PROTOCOL.md)**.

## Publishing on GitHub

The repository is **[Slimbook-Team/cooltop](https://github.com/Slimbook-Team/cooltop)**. Maintainers who already created the Git repository should follow **[docs/PUBLISHING.md](docs/PUBLISHING.md)** to update and push the existing `main` branch. Do **not** reinitialize an existing clone.

## Contributing

Hardware feedback, extra Linux sensor support, and documentation improvements are welcome. Report bugs via [GitHub Issues](https://github.com/Slimbook-Team/cooltop/issues) and propose changes via [pull requests](https://github.com/Slimbook-Team/cooltop/pulls). Please read [CONTRIBUTING.md](CONTRIBUTING.md). Do not submit proprietary executables, drivers, firmware, or copyrighted program assets.

## License and credits

MIT License — see [LICENSE](LICENSE). This is an independent community project, not an official hardware driver.

USB protocol research/reference implementation: [cpu-temp-monitor-linux by ricardofrancini](https://github.com/ricardofrancini/cpu-temp-monitor-linux). The code in this repository is a separate Python implementation; no Windows binaries or assets are redistributed.
