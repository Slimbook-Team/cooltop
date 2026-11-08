#!/usr/bin/env python3
"""USB CPU temperature display driver for Linux.

HID-only, stdlib-only telemetry sender for USB 1a2c:4984.
Does not modify firmware or control fans, LEDs or USB configuration.
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import os
from pathlib import Path
import re
import signal
import sys
import time

VENDOR_ID = 0x1A2C
PRODUCT_ID = 0x4984
REPORT_ID = 0x07
REPORT_LEN = 64
SYS_HIDRAW = Path('/sys/class/hidraw')
SYS_HWMON = Path('/sys/class/hwmon')
SYS_THERMAL = Path('/sys/class/thermal')


def hid_iocsfeature(size: int) -> int:
    """linux/hidraw.h: _IOC(_IOC_READ|_IOC_WRITE, 'H', 0x06, size)."""
    return (3 << 30) | (size << 16) | (ord('H') << 8) | 0x06


def telemetry_packet(cpu_temp: int, value2: int, *, fahrenheit: bool = False,
                     second_is_usage: bool = True, size: int = REPORT_LEN) -> bytearray:
    if size not in (64, 65):
        raise ValueError('HID report length must be 64 or 65 bytes')
    cpu_temp = max(0, min(999, int(round(cpu_temp))))
    value2 = max(0, min(100 if second_is_usage else 999, int(round(value2))))
    b = bytearray(size)
    b[0] = REPORT_ID
    b[1:4] = bytes([(cpu_temp // 100) % 10, (cpu_temp // 10) % 10, cpu_temp % 10])
    b[4] = (0x01 if fahrenheit else 0) | (0x10 if second_is_usage else 0)
    b[5:8] = bytes([(value2 // 100) % 10, (value2 // 10) % 10, value2 % 10])
    return b


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace').strip()
    except (OSError, PermissionError):
        return ''


def read_temp_c(path: Path) -> float | None:
    try:
        raw = float(read_text(path))
        temp = raw / 1000.0 if abs(raw) >= 200 else raw
        # Rather than sending a bogus value to a display, reject nonsense.
        if not (-10 < temp < 150):
            return None
        return temp
    except (ValueError, OverflowError):
        return None


def cpu_temp_candidates() -> list[tuple[int, Path, str]]:
    result: list[tuple[int, Path, str]] = []
    preferences = {'k10temp': 0, 'zenpower': 0, 'coretemp': 0,
                   'cpu_thermal': 10, 'x86_pkg_temp': 10}
    for directory in sorted(SYS_HWMON.glob('hwmon*')):
        name = read_text(directory / 'name').lower()
        if name not in preferences:
            continue
        for value in sorted(directory.glob('temp*_input')):
            label = read_text(value.with_name(value.name.replace('_input', '_label')))
            score = preferences[name]
            low = label.lower()
            if 'tdie' in low or 'package id' in low or 'package' in low:
                score -= 7
            elif 'tctl' in low:
                score -= 4
            elif 'ccd' in low or 'core ' in low:
                score += 6
            if read_temp_c(value) is not None:
                result.append((score, value, f'{name} · {label or value.name}'))
    for directory in sorted(SYS_THERMAL.glob('thermal_zone*')):
        name = read_text(directory / 'type').lower()
        if name in ('x86_pkg_temp', 'cpu-thermal', 'cpu_thermal', 'soc_thermal'):
            value = directory / 'temp'
            if read_temp_c(value) is not None:
                result.append((30, value, f'thermal · {name}'))
    return sorted(result, key=lambda item: (item[0], str(item[1])))


def parse_hid_id(uevent: str) -> tuple[int, int] | None:
    # HID_ID=0003:00001A2C:00004984 (bus type : vendor : product)
    match = re.search(r'(?m)^HID_ID=[0-9a-fA-F]+:([0-9a-fA-F]+):([0-9a-fA-F]+)$', uevent)
    return (int(match.group(1), 16), int(match.group(2), 16)) if match else None


def read_interface(device: Path) -> str:
    current = device.resolve()
    for candidate in (current, *current.parents):
        number = read_text(candidate / 'bInterfaceNumber')
        if number:
            return number
    return '?'


def descriptor_has_feature_report(descriptor: bytes, report_id: int) -> bool:
    """Parse HID items and find a Feature item assigned to report_id.

    A HID report descriptor is a sequence of short (and occasionally long)
    items. Report ID (0x85) is a global item, while Feature (0xB0..0xB3)
    is a main item. Track Report ID across the descriptor to avoid matching
    an unrelated Feature report on the same USB interface.
    """
    offset = 0
    active_report_id = 0  # HID devices without an ID use 0.
    global_stack: list[int] = []
    while offset < len(descriptor):
        prefix = descriptor[offset]
        offset += 1
        if prefix == 0xFE:  # Long item: length, tag, payload.
            if offset + 2 > len(descriptor):
                return False
            length = descriptor[offset]
            offset += 2 + length
            if offset > len(descriptor):
                return False
            continue
        data_size = (0, 1, 2, 4)[prefix & 3]
        if offset + data_size > len(descriptor):
            return False
        data = descriptor[offset:offset + data_size]
        offset += data_size
        kind = (prefix >> 2) & 3
        tag = (prefix >> 4) & 15
        if kind == 1 and tag == 8:  # Global: Report ID
            if len(data) != 1:
                return False
            active_report_id = data[0]
        elif kind == 1 and tag == 10:  # Global: Push
            global_stack.append(active_report_id)
        elif kind == 1 and tag == 11:  # Global: Pop
            if not global_stack:
                return False
            active_report_id = global_stack.pop()
        elif kind == 0 and tag == 11 and active_report_id == report_id:
            return True
    return False


def discover_hidraw() -> list[dict]:
    found: list[dict] = []
    for directory in sorted(SYS_HIDRAW.glob('hidraw*')):
        device = directory / 'device'
        vendor_product = parse_hid_id(read_text(device / 'uevent'))
        if vendor_product != (VENDOR_ID, PRODUCT_ID):
            continue
        descriptor_file = device / 'report_descriptor'
        try:
            descriptor = descriptor_file.read_bytes()
        except OSError:
            descriptor = b''
        # Check that report ID 0x07 actually OWNS a Feature item.
        # A byte-substring search is unsafe: different report IDs can exist
        # in the same descriptor.
        has_feature = descriptor_has_feature_report(descriptor, REPORT_ID)
        interface = read_interface(device)
        found.append(dict(path=Path('/dev') / directory.name,
                          interface=interface,
                          has_descriptor=bool(descriptor),
                          safe_match=has_feature))
    return found


def select_device() -> Path | None:
    devs = discover_hidraw()
    safe = [d for d in devs if d['safe_match']]
    if len(safe) == 1:
        return safe[0]['path']
    if len(safe) > 1:
        iface1 = [d for d in safe if d['interface'].lower() in ('01', '1')]
        if len(iface1) == 1:
            return iface1[0]['path']
    # Some devices expose report descriptors only to root. Interface 1 is
    # reported by known variants, but selecting it without proof is risky.
    return None


def print_diagnostics() -> None:
    print(f'Target USB HID device: {VENDOR_ID:04x}:{PRODUCT_ID:04x}')
    devices = discover_hidraw()
    if not devices:
        print('No matching hidraw nodes found. Check lsusb and the internal USB connection.')
    for item in devices:
        flags = 'HID feature report 0x07 detected' if item['safe_match'] else 'report descriptor not verified'
        print(f"  {item['path']} | interface {item['interface']} | {flags}")
    selected = select_device()
    print('Selected device:', selected or '(none; no data will be sent to an unverified HID interface)')
    print('CPU temperature sensors:')
    candidates = cpu_temp_candidates()
    if not candidates:
        print('  No CPU temperature sensor found in hwmon or thermal sysfs.')
    for score, path, label in candidates:
        print(f'  {label} | {read_temp_c(path)} °C | {path} | priority {score}')


class CpuLoad:
    prev: tuple[int, int] | None = None

    def sample(self) -> float | None:
        try:
            parts = Path('/proc/stat').read_text().splitlines()[0].split()
            values = [int(v) for v in parts[1:]]
            # idle plus iowait are non-busy time; guest included in user/nice.
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            total = sum(values[:8])
            previous = self.prev
            self.prev = total, idle
            if previous is None:
                return None
            elapsed, idle_elapsed = total - previous[0], idle - previous[1]
            if elapsed <= 0:
                return None
            return max(0.0, min(100.0, 100.0 * (1.0 - idle_elapsed / elapsed)))
        except (OSError, ValueError, IndexError):
            return None


def run(args: argparse.Namespace) -> int:
    sensor = Path(args.sensor) if args.sensor else None
    load = CpuLoad()
    device = None
    fd = None
    stop = False
    last_message = ''
    last_send_failed = False

    def handle_signal(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    if not args.dry_run and args.once and select_device() is None:
        print("No verified compatible HID device found. Run the 'list' command first.", file=sys.stderr)
        return 2

    while not stop:
        if sensor is None or read_temp_c(sensor) is None:
            candidates = cpu_temp_candidates()
            sensor = candidates[0][1] if candidates else None
        temp = read_temp_c(sensor) if sensor else None
        usage = load.sample()

        if temp is None:
            msg = 'No valid CPU temperature detected. No data will be sent.'
            if msg != last_message:
                print(msg, file=sys.stderr, flush=True)
                last_message = msg
            if args.once:
                return 3
            time.sleep(args.interval)
            continue

        if usage is None:
            # The first /proc/stat sample cannot yield utilization. Do not
            # misrepresent missing usage as 0%; warm it up before sending.
            if args.once or args.dry_run:
                time.sleep(min(args.interval, 0.2))
                usage = load.sample()
            else:
                time.sleep(min(args.interval, 0.2))
                usage = load.sample()
        if usage is None:
            usage = 0.0

        display_temp = round(temp * 9/5 + 32) if args.fahrenheit else round(temp)
        packet = telemetry_packet(display_temp, round(usage), fahrenheit=args.fahrenheit,
                                  size=args.report_size)
        if args.dry_run:
            print(f'DRY RUN: CPU {temp:.1f}°C | usage {usage:.1f}% | sensor={sensor} | frame={packet.hex(" ")}', flush=True)
        else:
            try:
                target = select_device()
                if not target:
                    raise OSError(errno.ENODEV, 'HID device disconnected or interface could not be verified')
                if fd is None or target != device:
                    if fd is not None:
                        os.close(fd)
                    fd = os.open(target, os.O_RDWR | os.O_CLOEXEC)
                    device = target
                    print(f'Connected: {device} | sensor={sensor}', flush=True)
                fcntl.ioctl(fd, hid_iocsfeature(len(packet)), packet, True)
                if args.verbose:
                    print(f'{temp:.1f} °C · CPU {usage:.0f}% · {device}', flush=True)
                last_message = ''
                last_send_failed = False
            except OSError as error:
                last_send_failed = True
                if fd is not None:
                    os.close(fd)
                fd = None
                device = None
                msg = f'Unable to send a USB HID report: {error}. Retrying...'
                if msg != last_message:
                    print(msg, file=sys.stderr, flush=True)
                    last_message = msg
        if args.once:
            break
        time.sleep(args.interval)
    if fd is not None:
        os.close(fd)
    return 4 if args.once and last_send_failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='USB CPU Temperature Display for Linux (USB HID 1a2c:4984)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='List compatible HID interfaces and CPU temperature sensors')
    sender = sub.add_parser('run', help="Update the cooler's temperature display")
    sender.add_argument('--interval', type=float, default=1.0, help='Update interval in seconds')
    sender.add_argument('--sensor', type=str, help='Absolute path to the desired temp*_input sensor')
    sender.add_argument('--fahrenheit', action='store_true')
    sender.add_argument('--report-size', type=int, choices=(64, 65), default=64)
    sender.add_argument('--once', action='store_true', help='Send a single update and exit')
    sender.add_argument('--dry-run', action='store_true', help='Do not send any USB data')
    sender.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args(argv)
    if args.command == 'list':
        print_diagnostics()
        return 0
    if not 0.2 <= args.interval <= 60:
        parser.error('--interval must be between 0.2 and 60 seconds')
    if args.sensor and (not Path(args.sensor).is_file() or not Path(args.sensor).is_absolute()):
        parser.error('--sensor must be an absolute path to a sensor file')
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
