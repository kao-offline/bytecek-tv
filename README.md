# Bytecek TV Launcher

A light custom HDMI TV launcher for **Debian 13 amd64**, styled after the supplied Bytecek mockups. Runs without GNOME/KDE/Electron; Chromium is used for streaming and for the launcher UI.

## Screenshot and behavior

- Red **B** splash; dark charcoal screen, top-centered Bytecek logo.
- Spilled → https://spilled.kaooffline.top/
- ČT24 → https://ct24.ceskatelevize.cz/video/zive-vysilani
- Chrome tile → opens your installed **Google Chrome if present**, otherwise Debian Chromium.
- Add Shortcut (+) → enter a name and web URL; shortcuts persist in Chromium local storage.
- Red button → shutdown / restart / sleep, with an `u sure` confirmation dialog.
- `exit >` → closes the launcher and opens an X terminal.
- **F9** from a video/site window → closes the foreground browser window and returns to the launcher. Arrow keys, Tab and Enter work in the UI.
- Custom shortcut: focus and press **Delete** to remove it, or right-click it.

## Installation: download bundle

1. Install Debian 13 amd64, selecting only **standard system utilities** (no full desktop).
2. Download and unzip this repository. In its folder run:

```bash
sudo bash install.sh
sudo reboot
```

> The installer creates a `tvbox` account, makes tty1 auto-login, changes the laptop's lid-close behavior, installs Xorg/Openbox/Chromium, and puts files in `/opt/bytecek`. Run it only on a dedicated media-box laptop, not your daily computer. Your existing Linux installation is not replaced, but tty1 auto-login is changed.

## One-command installer (after repo is published)

Requires `curl`, `tar`, and `sudo`. If curl is missing: `sudo apt install curl`. Review the remote script first. You can then run:

```bash
curl -fsSL https://raw.githubusercontent.com/kao-offline/bytecek-tv/main/bootstrap.sh | bash
```

Reboot after the installer completes.

## Troubleshooting

- **F9 doesn't work:** run `pgrep xbindkeys`; `cat /tmp/bytecek-keys.log`.
- **Black screen:** Ctrl+Alt+F2, log into your original admin account. Check `cat /tmp/bytecek-openbox.log` and `cat /tmp/bytecek-server.log` (logs live in the tvbox user's shared `/tmp`).
- **Streaming stutters:** test `vainfo`, `chrome://gpu`, and the video decoder; hardware decoding varies by GPU/driver and Chrome/Chromium version.
- **No HDMI audio:** choose your HDMI device with `wpctl status` and `wpctl set-default DEVICE_ID`, assuming PipeWire is active.
- **TV blank:** on the console run `DISPLAY=:0 xrandr --query`; the installer does not always know the correct output name or TV mode.
- **Power commands denied:** ensure the `tvbox` session is local and logind/polkit permit shutdown/suspend. A narrowly scoped sudo rule grants the `tvbox` user permission to run only the root-owned `/usr/local/sbin/bytecek-power` script, which accepts just poweroff, reboot, or suspend.

## Security design

Local web server binds only to `127.0.0.1:8765`. API writes require a session CSRF token and same-origin requests. Custom shortcut URLs accept only HTTP and HTTPS. The launcher runs as an unprivileged `tvbox` user; there is no public API and a passwordless `sudo` rule restricted to the root-owned power helper.

## Project files

- `install.sh`: setup on Debian (run as root)
- `bootstrap.sh`: GitHub archive downloader
- `session.sh`: Openbox, HDMI mode, browser startup
- `power.sh`: narrowly restricted shutdown/reboot/suspend entry point
- `home.sh`: F9 window switch
- `server.py`: local launch and power control API
- `ui/`: the editable HTML/CSS/JS plus original red B SVG

## Uninstall / rollback

From a separate admin console:

```bash
sudo rm -f /etc/systemd/system/getty@tty1.service.d/bytecek.conf
sudo rm -f /etc/systemd/logind.conf.d/bytecek.conf
sudo systemctl daemon-reload
sudo rm -f /etc/sudoers.d/bytecek-power /usr/local/sbin/bytecek-power
sudo rm -rf /opt/bytecek
sudo reboot
```

The dedicated `tvbox` account remains (in case you want to preserve browser history and shortcuts); you may remove it with `sudo userdel -r tvbox` if you have no data to keep. The installed Debian packages remain.

## Development and release kit

```bash
python3 -m unittest discover -s tests -p 'test_server.py'
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 tests/test_ui.py
python3 tools/package.py
```

The packager creates `dist/bytecek-tv.tar.gz`, `dist/bytecek-tv-source.zip`, and
`dist/SHA256SUMS`. Both archives contain a `bytecek-tv/` directory. Extract the
installer on Debian and run `sudo bash install.sh`, then reboot. No Python
packages are required by the installed launcher.

GitHub Actions checks shell syntax, the API, and the UI. Pushing a `v*` tag
also publishes the two bundles and their checksums as a GitHub release.
Debian boot, HDMI, audio, suspend, and streaming playback require a physical
hardware check; automated tests do not validate these.
