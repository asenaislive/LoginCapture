# LoginCapture

A small Linux security tool that photographs whoever types a wrong password at your login screen.

It runs as a **systemd service from boot**, follows the system journal in real time, and when it sees a failed login it captures a short burst of webcam frames, stitches them into one clearer image, and saves it with a timestamp. After a correct login, it releases the camera and shuts down cleanly.

> ⚠️ **For your own devices only.** Photographing people without their consent can violate privacy laws. Use this only on machines you own.

---

## How it works

```
journalctl -f  ──▶  Python script  ──▶  match failure line?  ──▶  capture 25 frames  ──▶  stitch  ──▶  save image
   (live journal)     (subprocess.Popen)         (PAM log)           (OpenCV)                       image_<timestamp>.jpg
```

1. A systemd service starts the script at boot, **before anyone logs in**.
2. The script launches `journalctl` with `subprocess.Popen` and reads its output line by line, so it reacts the moment a line appears.
3. Each line is checked against the PAM authentication-failure patterns.
4. On a match, the camera captures 25 frames, which are combined into a single, higher-quality image.
5. The image is saved as `image_<DD-MM-YYYY_HH-MM-SS>.jpg`.
6. When a correct login is detected, the script releases the camera and exits.

## Features

- **Real-time log watching** with `subprocess.Popen` and `journalctl`, with no polling.
- **Boot-time operation** as a systemd service, so it is already watching at the login screen.
- **Multi-frame capture:** 25 frames stitched into one image for better quality.
- **Careful error handling:** OpenCV's `imwrite` can fail silently, so the script checks every capture result and handles camera and OpenCV errors instead of crashing.
- **Clean shutdown:** The camera is released when a login succeeds and relaunches on logout or at lockscreen.
- **Path handling with `pathlib`**, so the script does not depend on the directory it was launched from.
- **Timestamped filenames** that sort naturally, e.g. `image_25-04-2025_13-34-40.jpg`.

## Requirements

- A Linux distribution that uses **systemd** (`journalctl` is required)
- Python 3 (developed on 3.12)
- A webcam at `/dev/video0` (or accessible to OpenCV)
- `opencv-python` (or `opencv-python-headless` on systems without graphics libraries)
- Root access, to read the full journal and run a system service

## Installation

These steps use `/opt/login-capture` as the install location.

**1. Copy the script into place** (use `cp`, not `mv`):

```bash
sudo mkdir -p /opt/login-capture
sudo cp journal.py /opt/login-capture/
```

**2. Create a virtual environment inside `/opt`** (do not copy an existing one, since venvs store their own absolute paths):

```bash
sudo python3 -m venv /opt/login-capture/.venv
sudo /opt/login-capture/.venv/bin/pip install opencv-python
```

**3. Make everything root-owned**, so a normal user cannot edit code that root runs:

```bash
sudo chown -R root:root /opt/login-capture
```

**4. Install the service:**

```bash
sudo cp watcher.service /etc/systemd/system/
systemd-analyze verify /etc/systemd/system/watcher.service
sudo systemctl daemon-reload
sudo systemctl enable --now watcher
```

**5. Check that it is running:**

```bash
sudo systemctl status watcher
sudo journalctl -u watcher -f
```

`enable` makes it start on every boot. `start` alone only runs it until the next reboot.

## Testing it

1. Log out and type a wrong password once at the login screen.
2. Confirm that exactly one image appears in the photo folder, that it is not black or green, and that the service is still `active (running)`.
3. Log in with the correct password and confirm the camera is released (the camera light goes off or open camera to check).

## Security notes

- **Photos are sensitive data.** Keep the folder readable only by its owner (`chmod 700`).
- **The script and service file should be root-owned and not writable by other users.** A script that root runs at boot is a privilege-escalation path if a normal user can edit it.
- **Evidence protection (manual):** Linux file attributes can make deleting captured photos harder. `chattr +a` on the photo folder allows new files but blocks deletion and renaming, and `chattr +i` on a file blocks any change to it. Check with `lsattr`.
- **Limit:** anyone with root can remove these attributes, so they add friction and do not make deletion impossible. Copying images off the machine is the stronger protection (see the roadmap).

## Tested on

| System | Desktop | Status |
|---|---|---|
| Fedora | GNOME (GDM) | ✅ Tested |
| Ubuntu, Debian, Mint, others | various | ⚠️ Not yet tested |

## Known limitations

- **Only tested on Fedora with GNOME.** The patterns the script matches (such as the `gdm-password` PAM service) are specific to GNOME's login screen. Other display managers (SDDM, LightDM) log under different names, so they would need their own patterns.
- **Requires systemd.** Distributions without `journalctl` are not supported.
- **Photos are stored locally.** An attacker with root can delete or alter them.
- **SELinux and AppArmor behaviour differs between distributions.** The setup steps above were verified on Fedora, which enforces SELinux.
- **Webcam only.** If another program holds the camera at that moment, the capture fails (the error is handled and logged, and the watcher keeps running).

## Roadmap

- [ ] Keep the login-service match patterns in one configurable list
- [ ] Open the camera only when a failure is detected, instead of holding it
- [ ] Automatically set `chattr +i` on each new photo
- [ ] Send each photo off the machine immediately (for example to a phone) so local deletion cannot destroy the evidence
- [ ] Restart watching after logout, not only at boot
- [ ] Test on Ubuntu, Debian and KDE-based systems
- [ ] Unit tests for the log-line matching

## What I learned building this

- Why `subprocess.run` cannot follow an endless command and `Popen` can
- Why leaving a pipe unread causes a silent deadlock
- That OpenCV's `imwrite` returns `False` instead of raising an error
- How a script that works in the terminal can fail as a service: working directory, `PATH`, packages, permissions and SELinux
- How to reason about an attacker's next move, such as deleting the evidence

## License

Released under the [MIT License](LICENSE). © 2026 AsenaisLive
