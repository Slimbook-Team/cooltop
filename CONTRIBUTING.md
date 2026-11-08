# Contributing to CoolTop

Thanks for helping improve Linux support for internal-USB CPU temperature displays.

## Priorities

1. Confirm real-hardware behavior of the **MT880-V4D**: USB ID, HID node, report length, screen updates.
2. Document OpenRGB motherboard/controller zones for MT880 and MT880-V4D lighting.
3. Improve CPU sensor selection, permissions, packaging, and diagnostics.
4. Add tests for new behaviors before changing the USB protocol.

Run `python3 -m unittest discover -s tests -v` before opening a pull request. Keep Python 3.10 compatibility and avoid third-party runtime dependencies unless there is a compelling reason.

Don't add a new USB ID or bypass descriptor verification without a report from actual hardware and an explanation of the risk. Never bundle firmware, vendor drivers, Windows executables, or proprietary artwork. If submitting logs, redact serial numbers, usernames, hostnames and personal data.

Issues are welcome even for negative test results; please follow the structured issue template.

Submit hardware test reports through the [CoolTop issue templates](https://github.com/Slimbook-Team/cooltop/issues/new/choose) and code improvements through [pull requests](https://github.com/Slimbook-Team/cooltop/pulls).
