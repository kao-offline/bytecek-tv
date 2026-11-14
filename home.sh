#!/usr/bin/env bash
# Pause the active site and show Home on top of it; tabs and playback position are kept.
set -u
ACTIVE="${1:-$(xdotool getactivewindow 2>/dev/null || true)}"
if [[ -n "$ACTIVE" ]]; then
  NAME="$(xdotool getwindowname "$ACTIVE" 2>/dev/null || true)"
  CLASS="$(xprop -id "$ACTIVE" WM_CLASS 2>/dev/null || true)"
  if [[ "$NAME" != Bytecek\ Launcher* ]]; then
    case "$CLASS" in *hromium*|*hrome*)
      # Pause its media (browser-extension/media.js); the app stays mapped behind Home.
      xdotool windowactivate --sync "$ACTIVE" key --clearmodifiers ctrl+alt+shift+F12 2>/dev/null || true ;;
    esac
  fi
fi
exec /opt/bytecek/show-launcher.sh
