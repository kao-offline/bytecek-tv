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
  chromium python3 python3-tk xdg-desktop-portal-gtk dbus-x11 ca-certificates curl unzip sudo fonts-dejavu-core \
  mesa-va-drivers vainfo alsa-utils unclutter plymouth plymouth-themes
# PipeWire for HDMI audio when available (some base images may already include it).
if apt-cache show pipewire-audio >/dev/null 2>&1;then apt-get install -y --no-install-recommends pipewire-audio wireplumber || true;fi
if apt-cache show intel-media-va-driver >/dev/null 2>&1;then apt-get install -y --no-install-recommends intel-media-va-driver || true;fi

if ! id -u tvbox >/dev/null 2>&1;then
  useradd --create-home --shell /bin/bash tvbox
fi
install -d -m 755 /opt/bytecek /opt/bytecek/ui
install -d -m 755 /opt/bytecek/boot /opt/bytecek/browser-extension
install -m 644 "$SCRIPT_DIR"/boot/* /opt/bytecek/boot/
install -m 644 "$SCRIPT_DIR"/browser-extension/* /opt/bytecek/browser-extension/
install -m 644 "$SCRIPT_DIR/kiosk_overlay.py" /opt/bytecek/kiosk_overlay.py
install -m 644 "$SCRIPT_DIR/openbox.xml" /opt/bytecek/openbox.xml
install -m 644 "$SCRIPT_DIR/server.py" /opt/bytecek/server.py
install -m 644 "$SCRIPT_DIR/xbindkeysrc" /opt/bytecek/xbindkeysrc
install -m 755 "$SCRIPT_DIR/login.sh" /opt/bytecek/login.sh
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
install -d -m 755 /opt/bytecek/ui/icons
install -m 644 "$SCRIPT_DIR"/ui/icons/* /opt/bytecek/ui/icons/
find /opt/bytecek/ui -type f -exec chmod 644 {} +

PROFILE=/home/tvbox/.bash_profile
if [[ ! -f "$PROFILE" ]];then touch "$PROFILE";fi
if ! grep -q 'BYTECEK AUTO START' "$PROFILE";then
  cat >>"$PROFILE" <<'PROFILE_END'

# BYTECEK AUTO START - graphical launcher on the local TV console only
if [[ -z "${DISPLAY:-}" ]] && [[ "$(tty)" == /dev/tty1 ]]; then
  /opt/bytecek/login.sh
fi
PROFILE_END
fi
# Upgrade profiles written by the original installer as well.
sed -i 's|^  startx /opt/bytecek/session.sh.*|  /opt/bytecek/login.sh|' "$PROFILE"
chown tvbox:tvbox "$PROFILE"
install -d -o tvbox -g tvbox /home/tvbox/.config/xdg-desktop-portal
printf '[preferred]\ndefault=gtk\n' >/home/tvbox/.config/xdg-desktop-portal/portals.conf
chown tvbox:tvbox /home/tvbox/.config/xdg-desktop-portal/portals.conf
touch /home/tvbox/.hushlogin
chown tvbox:tvbox /home/tvbox/.hushlogin

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat >/etc/systemd/system/getty@tty1.service.d/bytecek.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin tvbox --noissue --noclear %I $TERM
Type=idle
StandardOutput=tty
TTYVTDisallocate=yes
UNIT

# Avoid suspending when the laptop lid closes on an HDMI television.
mkdir -p /etc/systemd/logind.conf.d
cat >/etc/systemd/logind.conf.d/bytecek.conf <<'LOGIND'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
LOGIND

# Branded initramfs splash and quiet GRUB startup; firmware screens are outside Linux.
install -d -m 755 /usr/share/plymouth/themes/bytecek
install -m 644 "$SCRIPT_DIR"/boot/* /usr/share/plymouth/themes/bytecek/
plymouth-set-default-theme bytecek
if command -v update-grub >/dev/null 2>&1; then
  mkdir -p /etc/default/grub.d
  cat >/etc/default/grub.d/bytecek.cfg <<'GRUB'
GRUB_TIMEOUT_STYLE=hidden
GRUB_TIMEOUT=0
GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT quiet splash loglevel=3 systemd.show_status=false vt.global_cursor_default=0"
GRUB
  update-grub
fi
update-initramfs -u
# TV startup does not need printer discovery or a blocking Wi-Fi wait.
systemctl disable cups-browsed.service NetworkManager-wait-online.service 2>/dev/null || true
systemctl set-default multi-user.target
systemctl enable getty@tty1.service
systemctl daemon-reload
printf '\nInstalled Bytecek to /opt/bytecek\n'
printf 'REBOOT to enter the launcher: sudo reboot\n'
printf 'F9 = Home | Delete = remove focused custom shortcut | bottom left = power\n'
printf 'If you need a console, use Ctrl+Alt+F2 and log in with your original user.\n'
printf 'Note: choose the HDMI audio output manually if your GPU defaults to laptop speakers.\n'
