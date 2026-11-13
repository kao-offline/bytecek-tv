#!/usr/bin/env bash
# F9 returns to the still-running launcher window; closes the foreground media window.
set -u
LAUNCHER="$(xdotool search --onlyvisible --name '^Bytecek Launcher( - .*)?$' 2>/dev/null | tail -n 1 || true)"
if [[ -z "$LAUNCHER" ]]; then exit 0; fi
ACTIVE="${1:-$(xdotool getactivewindow 2>/dev/null || true)}"
if [[ -n "$ACTIVE" && "$ACTIVE" != "$LAUNCHER" ]]; then
  CLASS="$(xprop -id "$ACTIVE" WM_CLASS 2>/dev/null || true)"
  case "$CLASS" in
    *hromium*|*hrome*) xdotool windowclose "$ACTIVE" 2>/dev/null || true ;;
  esac
fi
xdotool windowactivate --sync "$LAUNCHER" 2>/dev/null || true
