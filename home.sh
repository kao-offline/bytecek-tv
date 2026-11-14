#!/usr/bin/env bash
# Hide the active site and show Home; do not close tabs or lose playback position.
set -u
ACTIVE="${1:-$(xdotool getactivewindow 2>/dev/null || true)}"
if [[ -n "$ACTIVE" ]]; then
  NAME="$(xdotool getwindowname "$ACTIVE" 2>/dev/null || true)"
  CLASS="$(xprop -id "$ACTIVE" WM_CLASS 2>/dev/null || true)"
  if [[ "$NAME" != Bytecek\ Launcher* ]]; then
    case "$CLASS" in *hromium*|*hrome*)
      # Let the app draw its curtain closed first (see browser-extension/intro.js).
      xdotool windowactivate --sync "$ACTIVE" key --clearmodifiers ctrl+alt+shift+F12 2>/dev/null || true
      sleep 0.2
      xdotool windowminimize "$ACTIVE" 2>/dev/null || true ;;
    esac
  fi
fi
exec /opt/bytecek/show-launcher.sh
