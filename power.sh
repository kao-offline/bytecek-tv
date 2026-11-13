#!/bin/sh
# Installed root-owned. Only these three operations can run via the tvbox sudoers rule.
[ "$#" -eq 1 ] || exit 2
case "$1" in
  poweroff|reboot|suspend) exec /usr/bin/systemctl "$1" ;;
  *) echo 'Unsupported power action' >&2; exit 2 ;;
esac
