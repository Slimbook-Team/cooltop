# USB HID telemetry protocol (experimental)

This driver currently targets **VID:PID `1a2c:4984`**, USB HID **Feature report `0x07`**. Hardware implementations can differ even if they use similar Windows utilities.

It is based on independent protocol research in [cpu-temp-monitor-linux](https://github.com/ricardofrancini/cpu-temp-monitor-linux). The current Python code does not contain binaries, assets, or extracted libraries from Windows software.

## Telemetry packet

| Byte offset | Value | Meaning |
| --- | --- | --- |
| 0 | `0x07` | HID report ID |
| 1–3 | Hundreds, tens, units | CPU temperature, as decimal digits |
| 4 | `0x10` plus optional `0x01` | Usage/value mode flag; Fahrenheit flag |
| 5–7 | Hundreds, tens, units | CPU utilization (0–100%) |
| 8–63 (or 64) | Zero | Padding |

Default report length in this implementation is **64 bytes including report ID** (via hidraw `HIDIOCSFEATURE`). A **65-byte** alternative can be tried with `--report-size 65` after verifying the USB device and HID interface. This is pending direct validation on the target revision.

## Safety and validation

- The script **only selects** hidraw nodes reporting the expected USB VID:PID **and** a HID descriptor that associates a `Feature` item with report ID `0x07`.
- If more than one eligible interface is present, interface `01` is preferred **only if unique**; ambiguity results in no target.
- No firmware commands, firmware reads, arbitrary reports, raw USB transfers, or interface detaching.
- An exact USB match is **not enough** to establish support for a model or firmware revision.
- The feature-report format is independently unit-tested, but actual end-to-end display behavior must be checked with hardware.

## Limits

- Some devices are exposed by `lsusb` but cannot be accessed via `/dev/hidraw*` because a USB HID kernel driver cannot bind or does not publish a report descriptor. This implementation deliberately does not attempt a raw-USB fallback.
- CPU sensor selection is heuristic; multiple CPUs/package sensors can require manual selection with `--sensor`.
- No control of RGB lighting, fans, pumps, or the hardware's safety-critical cooling behavior.

If you have a nonmatching device, please submit a safe diagnostic report instead of patching VID:PID and testing random report bytes.
