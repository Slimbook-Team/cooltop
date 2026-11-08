# Changelog

## 0.2.0-alpha.1 (2026-11-08)

- Prepared a neutral, English-only GitHub repository with no cooler-vendor branding.
- Added the standalone OpenRGB lighting guide, testing checklist, and protocol notes.
- Renamed the Python program, systemd unit, system account, and udev rule consistently.
- Improved HID descriptor parsing to match Feature report `0x07` on the selected interface.
- Changed installation so the service must be **explicitly enabled after** successful manual testing.
- Added community issue template and CI tests.
- Real MT880-V4D hardware remains **unverified**.

## 0.1.0

- Initial Linux USB HID feature-report proof of concept.
