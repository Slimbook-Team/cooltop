# Publishing and updating CoolTop on GitHub

**Official repository:** <https://github.com/Slimbook-Team/cooltop>

**Repository description:** Experimental Linux USB HID CPU-temperature display driver, with an OpenRGB ARGB lighting guide.

**Suggested topics:** `linux`, `usb-hid`, `hwmon`, `cpu-temperature`, `openrgb`, `argb`, `systemd`, `python`, `cooltop`.

## Maintainer: the repository already exists

**Do not run `git init`, `git remote add origin`, or `gh repo create` again.** The current checkout at `~/scripts/cooltop` already has a `.git` directory, a `main` branch, an `origin` remote, and an initial README commit. The first push failed because an HTTPS account password was used; GitHub does not allow that authentication method for Git operations.

### 1. Copy the updated project into the existing working directory

If you downloaded `cooltop-v0.2.0-alpha.2.zip` to `~/Downloads`:

```bash
mkdir -p /tmp/cooltop-upload
unzip -o ~/Downloads/cooltop-v0.2.0-alpha.2.zip -d /tmp/cooltop-upload
cp -a /tmp/cooltop-upload/cooltop/. ~/scripts/cooltop/
cd ~/scripts/cooltop
```

The archive contains the complete source tree, **without a `.git` directory**. Copying its *contents* preserves the existing Git history and remote. Adjust the ZIP path if your browser downloaded it elsewhere. This replaces the previously committed README with the current one and adds the remaining files.

### 2. Review and test locally

```bash
git status
python3 -m unittest discover -s tests -v
bash -n install.sh uninstall.sh
```

These tests do not prove the temperature display works on physical hardware. Do not run the USB write test on a machine without the matching display. See [HARDWARE_TESTING.md](HARDWARE_TESTING.md).

### 3. Configure SSH authentication (recommended)

Check for an existing public key first:

```bash
ls -l ~/.ssh/*.pub
```

If you already have a working GitHub SSH key, reuse it. Otherwise create one:

```bash
ssh-keygen -t ed25519 -C "cooltop-github"
cat ~/.ssh/id_ed25519.pub
```

Add **only the public key** to your GitHub account under [SSH and GPG keys](https://github.com/settings/keys). Never upload or share the private key. If necessary, load the key with `ssh-add`. Confirm GitHub access:

```bash
ssh -T git@github.com
```

If your organization requires SSO authorization, authorize your SSH key for the organization as well.

### 4. Update the existing remote, commit, and push

From `~/scripts/cooltop`:

```bash
git remote -v
git remote set-url origin git@github.com:Slimbook-Team/cooltop.git
git add -A
git commit -m "Prepare CoolTop Linux driver and community documentation"
git push -u origin main
```

If Git says there is nothing to commit, check `git status`; there may already be an identical commit. If Git says it cannot authenticate, check your SSH key and repository write permissions. If Git says the remote branch contains commits absent locally, inspect them and integrate them intentionally; **do not force-push**.

### HTTPS alternative

HTTPS works with a credential manager, a personal access token, or GitHub CLI (`gh auth login`), but **not** an account password. The SSH remote above avoids repeated HTTPS credential prompts.

## Before making a public release

- Verify there are no Windows binaries, proprietary assets, hardware serial numbers, or personal logs.
- Keep the **MT880-V4D marked as unverified** until its actual USB interface and telemetry behavior have been tested.
- Test OpenRGB separately from CoolTop and document the ARGB controller/zone rather than assuming compatibility.
- Until hardware verification, use a **pre-release** label (e.g., `v0.2.0-alpha.2`) and avoid claims of stable support.
- After testing, submit an [issue with a hardware compatibility report](https://github.com/Slimbook-Team/cooltop/issues/new/choose), update the compatibility table in [README.md](../README.md), and document the confirmed steps in [OPENRGB.md](OPENRGB.md) and [HARDWARE_TESTING.md](HARDWARE_TESTING.md).

## GitHub project links

- [Source code](https://github.com/Slimbook-Team/cooltop)
- [Issues](https://github.com/Slimbook-Team/cooltop/issues)
- [Pull requests](https://github.com/Slimbook-Team/cooltop/pulls)
- [Releases](https://github.com/Slimbook-Team/cooltop/releases)
