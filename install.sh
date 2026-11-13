#!/usr/bin/env bash
set -Eeuo pipefail
if (( EUID != 0 )); then echo 'Run: sudo bash install.sh' >&2;exit 1;fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$SCRIPT_DIR/server.py" || ! -f "$SCRIPT_DIR/ui/index.html" ]];then echo 'Missing package files. Extract the full archive first.' >&2;exit 1;fi
if [[ ! -f /etc/debian_version ]];then echo 'This installer supports Debian only.' >&2;exit 1;fi
if [[ "$(dpkg --print-architecture)" != 'amd64' ]]; then echo 'This installer currently targets amd64 (Intel/AMD 64-bit) laptops.' >&2;exit 1;fi

printf '\nBytecek TV launcher installer\n'
printf 'This creates user tvbox, enables tty1 automatic login and boots into a Chromium kiosk.\n'
printf 'WARNING: tty1 will log in without a password. Do not use on shared devices.\n\n'
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  xorg xinit openbox xbindkeys xdotool xterm x11-xserver-utils \
  chromium python3 dbus-x11 ca-certificates curl unzip sudo fonts-dejavu-core \
  mesa-va-drivers vainfo alsa-utils
# PipeWire for HDMI audio when available (some base images may already include it).
if apt-cache show pipewire-audio >/dev/null 2>&1;then apt-get install -y --no-install-recommends pipewire-audio wireplumber || true;fi
if apt-cache show intel-media-va-driver >/dev/null 2>&1;then apt-get install -y --no-install-recommends intel-media-va-driver || true;fi

if ! id -u tvbox >/dev/null 2>&1;then
  useradd --create-home --shell /bin/bash tvbox
fi
install -d -m 755 /opt/bytecek /opt/bytecek/ui
install -m 644 "$SCRIPT_DIR/server.py" /opt/bytecek/server.py
install -m 644 "$SCRIPT_DIR/xbindkeysrc" /opt/bytecek/xbindkeysrc
install -m 755 "$SCRIPT_DIR/home.sh" /opt/bytecek/home.sh
install -m 755 "$SCRIPT_DIR/session.sh" /opt/bytecek/session.sh
install -m 755 "$SCRIPT_DIR/power.sh" /usr/local/sbin/bytecek-power
mkdir -p /etc/sudoers.d
cat >/etc/sudoers.d/bytecek-power <<'SUDOERS'
tvbox ALL=(root) NOPASSWD: /usr/local/sbin/bytecek-power
SUDOERS
chmod 440 /etc/sudoers.d/bytecek-power
visudo -cf /etc/sudoers.d/bytecek-power
cp -f "$SCRIPT_DIR"/ui/{index.html,style.css,app.js,b.svg} /opt/bytecek/ui/
chmod 644 /opt/bytecek/ui/*

PROFILE=/home/tvbox/.bash_profile
if [[ ! -f "$PROFILE" ]];then touch "$PROFILE";fi
if ! grep -q 'BYTECEK AUTO START' "$PROFILE";then
  cat >>"$PROFILE" <<'PROFILE_END'

# BYTECEK AUTO START - graphical launcher on the local TV console only
if [[ -z "${DISPLAY:-}" ]] && [[ "$(tty)" == /dev/tty1 ]]; then
  startx /opt/bytecek/session.sh -- :0 vt1 -nolisten tcp
fi
PROFILE_END
fi
chown tvbox:tvbox "$PROFILE"

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat >/etc/systemd/system/getty@tty1.service.d/bytecek.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin tvbox --noclear %I $TERM
Type=idle
UNIT

# Avoid suspending when the laptop lid closes on an HDMI television.
mkdir -p /etc/systemd/logind.conf.d
cat >/etc/systemd/logind.conf.d/bytecek.conf <<'LOGIND'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
LOGIND

systemctl daemon-reload
printf '\nInstalled Bytecek to /opt/bytecek\n'
printf 'REBOOT to enter the launcher: sudo reboot\n'
printf 'F9 = Home | Delete = remove focused custom shortcut | bottom left = power\n'
printf 'If you need a console, use Ctrl+Alt+F2 and log in with your original user.\n'
printf 'Note: choose the HDMI audio output manually if your GPU defaults to laptop speakers.\n'
