#!/usr/bin/env bash
set -Eeuo pipefail
export DISPLAY="${DISPLAY:-:0}"
export XDG_CURRENT_DESKTOP=openbox
export XDG_SESSION_DESKTOP=openbox

# Start a minimal WM, no desktop shell / task bar.
openbox --sm-disable >/tmp/bytecek-openbox.log 2>&1 &
WM_PID=$!
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
  kill "$SERVER_PID" "$KEYS_PID" "$WM_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Let the local API bind before opening Chromium.
for _ in {1..40}; do
  if bash -c 'echo >/dev/tcp/127.0.0.1/8765' 2>/dev/null; then break; fi
  sleep .1
done

BROWSER="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
if [[ -z "$BROWSER" ]]; then
  echo 'No Chrome/Chromium found';exec xterm
fi

# Launcher stays open in its own Chromium window. Sites open as separate windows.
"$BROWSER" --no-first-run --no-default-browser-check --disable-session-crashed-bubble --kiosk 'http://127.0.0.1:8765/' || true

# Exit launcher => minimal terminal rather than a blank/black screen.
echo 'Bytecek launcher exited. Run: chromium --kiosk http://127.0.0.1:8765/'
xterm -fa 'DejaVu Sans Mono' -fs 13 -title 'Bytecek terminal' || true
