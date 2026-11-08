# CoolTop: OpenRGB setup for cooler ARGB lighting (Linux)

This guide belongs to **[CoolTop](https://github.com/Slimbook-Team/cooltop)**. It explains how to control **fan/heatsink LEDs** using **[OpenRGB](https://openrgb.org/)**. It is separate from the USB CPU temperature display driver in this repository.

## Status

- **MT880 (earlier model):** previously reported working with OpenRGB in one PC setup; motherboard and zone information were not recorded.
- **MT880-V4D:** not tested yet. Similar hardware is encouraging, but this is not a confirmed compatibility claim.
- This guide applies to units that actually include compatible **5 V addressable RGB (ARGB)** connectors. Units without LEDs or with proprietary controllers may behave differently.

## 1. Identify the correct cables

The cooler may use distinct connections:

| Function | Typical connector | Control |
| --- | --- | --- |
| Digital temperature display | Motherboard internal USB | `cpu_temp_display.py` |
| Addressable LED effects | **3-pin 5 V ARGB** (may be routed through a hub) | OpenRGB, via the motherboard/ARGB controller |
| Cooling fan speed | 4-pin PWM or 3-pin fan | BIOS/UEFI or fan-control software |

**Turn the PC off before rewiring.** Connect 5 V ARGB only to the correct 5 V ARGB header (often marked `ADD_GEN2`, `D_LED`, `JRAINBOW`, or `ARGB`). Header names depend on the board. Verify the **5 V pin alignment** in its manual. **A 3-pin 5 V ARGB connector must never go to a 4-pin 12 V RGB header.**

If the LEDs run through a hub, check whether the hub has motherboard-sync mode. A hub using its own remote/controller may not expose individually addressable LEDs to the motherboard.

## 2. Install OpenRGB

Get the current stable Linux build from the official project:

- https://openrgb.org/releases.html
- https://openrgb.org/

Use a suitable distribution package, AppImage, or Flatpak. For example, if using an **official AppImage** downloaded into the current directory:

```bash
chmod +x ./OpenRGB*.AppImage
./OpenRGB*.AppImage
```

If you installed the `openrgb` command through your distribution, launch it with `openrgb` (or from the application menu). Package names and OpenRGB builds differ between distributions.

## 3. Configure Linux hardware access

Some RGB controllers require USB or I2C access. **Prefer OpenRGB's udev rules over running the whole graphical application as root.**

Distribution packages may already install the rules. When using an **AppImage**, official OpenRGB guidance is:

```bash
sudo mkdir -p /etc/udev/rules.d
sudo ./OpenRGB*.AppImage --generate-udev-rules /etc/udev/rules.d/60-openrgb.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Run the `--generate-udev-rules` command with the actual filename if your shell wildcard expands to more than one AppImage. If needed, replug the affected USB device or reboot before testing again.

Other formats (Flatpak/source build) have their own official instructions: https://openrgb.org/udev.html

**Do not alter kernel parameters or load experimental SMBus drivers just to try this cooler.** If OpenRGB needs additional motherboard-specific access, consult the official documentation and consider the risks first.

## 4. Find and configure the correct ARGB zone

1. Launch OpenRGB and let it detect devices.
2. Select the **motherboard RGB controller** (or the external ARGB controller/hub). Do not expect the cooler's name to appear as a standalone USB RGB device.
3. Find a lighting zone such as an addressable header / digital LED strip.
4. Choose a basic **Static** mode and a distinctive color to test.
5. If the zone is resizable and the LEDs behave strangely, check its configured LED count against the connected fan/hub layout. Avoid random changes on unrelated controllers.
6. Once it works, save the configuration as an OpenRGB profile and enable your preferred OpenRGB startup behavior through its interface or desktop session.

If multiple ARGB components are wired to the same header/hub, changing that zone may change all of them together. Individual fan control requires a controller/wiring arrangement that exposes separate zones.

### Optional command-line example

Use the command that matches your installation (`openrgb` for a package or `./OpenRGB.AppImage` with the actual AppImage filename):

```bash
openrgb --list-devices
```

Then select the **actual motherboard/controller number and zone index**, replacing the placeholders:

```bash
openrgb --device DEVICE_NUMBER --zone ZONE_NUMBER --mode static --color 00AAFF
```

**Never copy and run this command with guessed device/zone indexes.** Modes and zone indexes differ by controller; the graphical interface is safest for the initial setup. OpenRGB's supported command-line flags are documented in its built-in `--help`.

## 5. Using OpenRGB together with the temperature display

They can generally run at the same time because they control **different interfaces**:

- OpenRGB sends lighting commands to the board/controller via its supported bus.
- This repository sends temperature/usage telemetry to a verified internal-USB HID display.

This separation is an architectural expectation, not a promise that every motherboard/hub/firmware combination will work.

## Troubleshooting

| Problem | Check |
| --- | --- |
| No RGB LEDs | Confirm the specific cooler variant has lighting and the ARGB cable is connected to a 5 V header/controller. |
| OpenRGB doesn't show the cooler | Look for the **motherboard/ARGB controller**, not the cooler model. |
| No motherboard controller detected | Verify [OpenRGB's supported device list](https://openrgb.org/devices_pipeline.html), version and udev rules. |
| Static color does nothing | Test motherboard-sync mode on any hub, try the correct ARGB zone, and check wiring. |
| Only part of the LEDs change | Inspect the zone's configured LED count, controller limitations and hub wiring. |
| Display works but LEDs do not | Troubleshoot **OpenRGB/ARGB**, not the USB telemetry driver. |
| LEDs work but display doesn't | Troubleshoot the USB HID driver using [HARDWARE_TESTING.md](HARDWARE_TESTING.md). |

## Please help document MT880-V4D

When you test the V4D, [open a CoolTop GitHub issue](https://github.com/Slimbook-Team/cooltop/issues/new/choose) with the motherboard model, OpenRGB version, ARGB connector/controller, zone name, results, and (optionally) a photo with private details removed. A reproducible report can turn this guide from an educated starting point into verified instructions.

## References

- [Official OpenRGB releases](https://openrgb.org/releases.html)
- [Official OpenRGB Linux udev permissions](https://openrgb.org/udev.html)
- [OpenRGB supported devices](https://openrgb.org/devices_pipeline.html)
