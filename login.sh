#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p "$HOME/.local/state/bytecek"
exec startx /opt/bytecek/session.sh -- :0 vt1 -nolisten tcp -background none >"$HOME/.local/state/bytecek/xsession.log" 2>&1
