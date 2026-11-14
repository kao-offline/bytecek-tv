#!/usr/bin/env bash
set -u
LAUNCHER="$(xdotool search --name '^Bytecek Launcher( - .*)?$' 2>/dev/null | tail -n 1 || true)"
if [[ -n "$LAUNCHER" ]]; then
  xdotool windowmap "$LAUNCHER" windowactivate --sync "$LAUNCHER" 2>/dev/null || true
  exit 0
fi
BROWSER="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
[[ -n "$BROWSER" ]] || exit 1
"$BROWSER" --user-data-dir="$HOME/.config/bytecek-launcher" --password-store=basic --force-dark-mode --no-first-run --no-default-browser-check --disable-session-crashed-bubble --kiosk http://127.0.0.1:8765/ >/tmp/bytecek-browser.log 2>&1 &
