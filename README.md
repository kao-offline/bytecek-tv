# Bytecek TV Launcher

A light custom HDMI TV launcher for **Debian 13 amd64**, styled after the supplied Bytecek mockups. Runs without GNOME/KDE/Electron; Chromium is used for streaming and for the launcher UI.

## Screenshot and behavior

- Red **B** splash; dark charcoal screen, top-centered Bytecek logo.
- Spilled → https://spilled.kaooffline.top/
- ČT24 → https://ct24.ceskatelevize.cz/video/zive-vysilani
- Chrome tile → opens your installed **Google Chrome if present**, otherwise Debian Chromium.
- Add Shortcut (+) → enter a name and web URL; shortcuts persist in Chromium local storage.
- Red button → shutdown / restart / sleep, with an `u sure` confirmation dialog.
- `exit >`: hides Home and reveals the desktop launcher button.
- **F9**: hides the active app and returns Home. Its tile restores the same live window.
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
- **Black screen:** Ctrl+Alt+F2, log into your original admin account. Check `cat /home/tvbox/.local/state/bytecek/xsession.log`, `cat /tmp/bytecek-openbox.log` and `cat /tmp/bytecek-server.log` (logs live in the tvbox user's shared `/tmp`).
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
sudo rm -f /etc/default/grub.d/bytecek.cfg
sudo plymouth-set-default-theme text
sudo update-initramfs -u
sudo update-grub
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

## Kiosk startup and icons

The installer sets `multi-user.target` as the boot target and enables automatic
login to `tvbox` on tty1 with `agetty --autologin`. No TV account password is
requested at boot; other accounts and consoles keep their authentication.
GRUB is hidden with a zero timeout, Linux uses quiet/splash flags, and Plymouth
displays the original B on charcoal. Firmware logos and encrypted-disk prompts
are outside account autologin. X startup logs go to
`/home/tvbox/.local/state/bytecek/xsession.log`; the cursor hides after two seconds.
If returning to an existing desktop installation, restore `graphical.target`
with `sudo systemctl set-default graphical.target` after uninstalling.

Launcher and websites use separate browser profiles so closing a website with
F9 leaves Home alive. Websites open fullscreen;
Chrome opens a separate maximized browser window with tabs, address bar and window controls. A short Opening overlay
acknowledges launch requests; it is not a website loading progress indicator.
Saved custom shortcuts stay in the launcher's profile across reinstalls.
Existing shortcuts from the original release's default Chromium profile must be
added again after this profile change.

Tiles wrap after six entries (including Add Shortcut) on TV displays, four on
medium displays and three on small ones. Up/down follows rows. Long labels
truncate visually while retaining their full accessible name and tooltip.
Bundled logos are documented in `ui/icons/SOURCES.md`. New shortcuts request a
website icon from Google's favicon service using only the hostname, with an
offline globe fallback. No URL path or query is sent to that service.

To upgrade, rerun the same bootstrap command and reboot. The installer updates
the original autostart block as well as the new one. Boot graphics, real window
focus/F9, HDMI, and power still require testing on the target Debian laptop.

## Smooth startup and fullscreen Home

The X session exports its display environment to D-Bus before Chromium starts;
this prevents the GTK portal from waiting for a display it cannot find. A native
dark B cover bridges X startup. Both browser profiles prefer dark UI and reduced
motion. Website windows use the same password-store backend as the launcher so
an unavailable desktop keyring cannot silently block first launch.

A small native **Home | F9** control expands from a top-right pill in fullscreen apps.
Hover over or click the small top-right pill to reveal Home, or press F9. Home minimizes the site window and focuses the launcher; its tile restores the same live page. The
control stays outside website content and does not occupy the top-left back
navigation area. It disappears on the launcher.

The bundled Chromium extension supplies a temporary dark canvas while page HTML
arrives. For Spilled only, it reduces animations and backdrop blur; video and
images remain enabled. This reduces rendering work rather than disabling GPU
acceleration. Sites may still paint their own white loading screens.

On the tested Dell Inspiron 7348, native Home clicks and F9 both returned to the
launcher, the GTK portal ran successfully, and Intel accelerated rendering plus
H.264 decoding were available. Website response time and playback still depend
on the service, codec, and Wi-Fi connection.

Startup now explicitly says **Starting Bytecek TV...** in Plymouth and the X
cover; a slow launch keeps a visible status instead of hiding it after a fixed
timeout. A short power-button press is ignored to prevent accidental shutdown
while the display changes modes. Use the launcher's power menu for shutdown.
A hardware-enforced long hold remains an emergency power-off.

The target notebook has also recorded interrupted early boots before the
launcher starts. Their cause is not established; working launcher tests do not
prove unattended boot reliability. Diagnostics are retained on that machine at
`/root/bytecek-boot-diagnostics/`, with frequent journal syncing enabled.

## Desktop, app resume and playback

Exiting Home now minimizes it and reveals **Open Bytecek TV** on the minimal
desktop. Click that button to restore it. A `Bytecek TV` desktop entry is also
installed under `/usr/local/share/applications` and the TV user's Desktop.

Home/F9 minimizes a site instead of closing it. Selecting its tile restores the
same window, including its current navigation and video position. Chrome opens
as a regular maximized browser with tabs and an address bar. Explicitly closing
a window with the browser's own close button still closes it. Live page state
is retained while the browser remains running; this is not a promise to retain
live playback state through reboot. Hidden tabs may continue audio playback.

The fullscreen control rests as a small pill at the top right. Hover/click to
expand Home; moving away collapses it. It is absent from regular Chrome windows,
where F9 remains available. User cookies and local storage stay in the existing
`~/.config/bytecek-sites` browser profile.

On Debian/Intel systems requiring full video processing, install the official
`intel-media-va-driver-non-free` package with Debian's `non-free` component
enabled. Driver capability alone does not prove browser decoding is accelerated;
verify the active decoder using Chromium's Media diagnostics.

The notebook's full Intel media driver and OpenGL/zero-copy browser settings were
verified with synthetic 1080p H.264 playback: Chromium selected
`VaapiVideoDecoder` and reported `kIsPlatformVideoDecoder=true`. This confirms
the tested codec/path, not hardware support for every stream or codec. The
Broadwell GPU does not provide modern AV1 hardware decoding. Full-feature driver
reference: https://github.com/intel/media-driver
