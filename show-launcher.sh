#!/usr/bin/env bash
set -u
/opt/bytecek/desktop.sh off
LAUNCHER="$(xdotool search --name '^Bytecek Launcher( - .*)?$' 2>/dev/null | tail -n 1 || true)"
if [[ -n "$LAUNCHER" ]]; then
  RUN="/run/user/$(id -u tvbox 2>/dev/null || id -u)"
  ACTIVE="$(xdotool getactivewindow 2>/dev/null || true)"
  if [[ "$ACTIVE" != "$LAUNCHER" ]]; then
    # The curtain closes over the app/desktop, Home comes up behind it, the curtain opens.
    rm -f "$RUN/bytecek-curtain-closed"
    setsid python3 /opt/bytecek/desktop/curtain.py cover 600 >/dev/null 2>&1 </dev/null &
    for _ in $(seq 1 40); do [[ -e "$RUN/bytecek-curtain-closed" ]] && break; sleep 0.05; done
  fi
  touch "$RUN/bytecek-home-shown" 2>/dev/null || true
  xdotool windowmap "$LAUNCHER" windowactivate --sync "$LAUNCHER" 2>/dev/null || true
  exit 0
fi
BROWSER="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
[[ -n "$BROWSER" ]] || exit 1
"$BROWSER" --user-data-dir="$HOME/.config/bytecek-launcher" --password-store=basic --force-dark-mode --no-first-run --no-default-browser-check --disable-session-crashed-bubble --kiosk http://127.0.0.1:8765/ >/tmp/bytecek-browser.log 2>&1 &
