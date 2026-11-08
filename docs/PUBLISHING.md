# Publishing this repository on GitHub

Suggested repository name: **`usb-cpu-temp-display-linux`**

Suggested description: **Experimental Linux USB HID CPU temperature display driver with separate OpenRGB ARGB setup guide.**

Suggested topics: `linux`, `usb-hid`, `hwmon`, `cpu-temperature`, `openrgb`, `argb`, `systemd`, `python`

## Before publishing

1. Run the unit tests and review `README.md` and the hardware support status.
2. Do not claim verified MT880-V4D support until tested on actual hardware.
3. Verify there are **no Windows installers, proprietary assets, hardware serial numbers, or sensitive logs** in the repository.
4. If you publish before testing the hardware, consider labeling the first GitHub release as a **pre-release** (`v0.2.0-alpha.1`).

## Upload using the GitHub website

1. Create a new **public**, empty GitHub repository named `usb-cpu-temp-display-linux`.
2. Leave the GitHub options to generate a README, `.gitignore`, or license unchecked; this repository already includes them.
3. Extract the ZIP and upload **the contents of the folder**, including the `.github` folder (don't upload the ZIP as a source file).
4. Commit the files, then check that `README.md` renders on the homepage.

## Or publish using Git

In the extracted project directory:

```bash
python3 -m unittest discover -s tests -v
git init -b main
git add .
git commit -m "Initial experimental Linux display driver and OpenRGB guide"
```

After creating an empty GitHub repository, replace `YOUR-USERNAME`:

```bash
git remote add origin https://github.com/YOUR-USERNAME/usb-cpu-temp-display-linux.git
git push -u origin main
```

For HTTPS Git authentication, use an approved credential manager, a personal access token, or the GitHub CLI (`gh auth login`). **GitHub does not accept account passwords for Git operations.** Alternatively configure SSH keys and use the SSH remote URL.

You can also create/push directly with the GitHub CLI once authenticated:

```bash
gh repo create usb-cpu-temp-display-linux --public --source=. --remote=origin --push
```

## After the first real-hardware test

- File the first compatibility report (including USB VID:PID and which report length worked).
- Update the compatibility table in the main `README.md`.
- Update `docs/HARDWARE_TESTING.md` with any corrections to the instructions.
- If the MT880-V4D ARGB zone works with OpenRGB, document the motherboard/controller model, OpenRGB version, and zone name in `docs/OPENRGB.md`.
- Only then publish a stable release or advertise the model as confirmed supported.
