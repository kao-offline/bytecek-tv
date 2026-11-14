#!/usr/bin/env bash
# Switch the running X session between Bytecek TV and a normal LXQt desktop.
#   desktop.sh on   - wallpaper + desktop icons, LXQt panel, decorated windows
#   desktop.sh off  - back to the bare TV session
set -u
ACTIVE="$HOME/.config/bytecek/openbox-active.xml"
mkdir -p "$(dirname "$ACTIVE")"
use_wm_config(){ cmp -s "$1" "$ACTIVE" || { cp -f "$1" "$ACTIVE" && openbox --reconfigure 2>/dev/null; }; }
case "${1:-}" in
  on)
    themed="$HOME/.config/bytecek/openbox-desktop.xml"
    [ -f "$themed" ] || python3 /opt/bytecek/desktop/apply-theme.py >/dev/null 2>&1
    use_wm_config "$( [ -f "$themed" ] && echo "$themed" || echo /etc/xdg/openbox/rc.xml )"
    pgrep -u "$(id -u)" -x lxqt-panel >/dev/null && exit 0
    export XDG_CURRENT_DESKTOP=LXQt XDG_MENU_PREFIX=lxqt- QT_QPA_PLATFORMTHEME=lxqt
    setsid pcmanfm-qt --desktop --profile=lxqt >>/tmp/bytecek-desktop.log 2>&1 </dev/null &
    setsid lxqt-panel >>/tmp/bytecek-desktop.log 2>&1 </dev/null &
    ;;
  off)
    pkill -u "$(id -u)" -x lxqt-panel
    pkill -u "$(id -u)" -f 'pcmanfm-qt --desktop'
    use_wm_config /opt/bytecek/openbox-tv.xml
    ;;
esac
exit 0
