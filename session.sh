#!/usr/bin/env bash
set -Eeuo pipefail
export DISPLAY="${DISPLAY:-:0}"
export XDG_CURRENT_DESKTOP=openbox
export XDG_SESSION_DESKTOP=openbox
# D-Bus services must inherit the real X display, otherwise portal startup times out.
dbus-update-activation-environment --systemd DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP || true
systemctl --user reset-failed xdg-desktop-portal.service xdg-desktop-portal-gtk.service || true

# Start a minimal WM, no desktop shell / task bar.
xsetroot -solid "#242424"
unclutter -idle 2 -root &
CURSOR_PID=$!
openbox --config-file /opt/bytecek/openbox.xml --sm-disable >/tmp/bytecek-openbox.log 2>&1 &
WM_PID=$!
python3 /opt/bytecek/kiosk_overlay.py >/tmp/bytecek-overlay.log 2>&1 &
OVERLAY_PID=$!
xset s off -dpms >/dev/null 2>&1 || true
xset s noblank >/dev/null 2>&1 || true

# Prefer HDMI at 1080p/60 where supported; don't hardcode a GPU-dependent connector.
if command -v xrandr >/dev/null 2>&1; then
  EXTERNAL="$(xrandr --query | awk '$2=="connected" && $1~/^(HDMI|DP)/ {print $1;exit}')"
  if [[ -n "$EXTERNAL" ]]; then
    xrandr --output "$EXTERNAL" --mode 1920x1080 --rate 60 --primary 2>/dev/null || xrandr --output "$EXTERNAL" --auto --primary || true
    INTERNAL="$(xrandr --query | awk '$2=="connected" && $1~/^(eDP|LVDS)/ {print $1;exit}')"
    if [[ -n "$INTERNAL" ]]; then xrandr --output "$INTERNAL" --off || true; fi
  else
    xrandr --auto || true
  fi
fi

xbindkeys -f /opt/bytecek/xbindkeysrc >/tmp/bytecek-keys.log 2>&1 &
KEYS_PID=$!
python3 /opt/bytecek/server.py >/tmp/bytecek-server.log 2>&1 &
SERVER_PID=$!

cleanup() {
  kill "$SERVER_PID" "$KEYS_PID" "$WM_PID" "$CURSOR_PID" "$OVERLAY_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Let the local API bind before opening Chromium.
for _ in {1..40}; do
  if curl -fsS http://127.0.0.1:8765/api/config >/dev/null 2>&1; then break; fi
  sleep .1
done

if ! curl -fsS http://127.0.0.1:8765/api/config >/dev/null 2>&1; then
  xterm -title 'Bytecek recovery' -e bash -c 'echo "Launcher service failed. Check /tmp/bytecek-server.log"; exec bash'
  exit 1
fi

BROWSER="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
if [[ -z "$BROWSER" ]]; then
  echo 'No Chrome/Chromium found';exec xterm
fi

# The WM owns the session lifetime. Exiting Home reveals the desktop button.
/opt/bytecek/show-launcher.sh
wait "$WM_PID"
