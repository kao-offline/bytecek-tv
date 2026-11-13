#!/usr/bin/env bash
# Optional one-command bootstrap, after publication at the repo URL below.
set -Eeuo pipefail
REPO='kao-offline/bytecek-tv'
BRANCH='main'
URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
command -v curl >/dev/null || { echo 'Install curl first: sudo apt install curl' >&2;exit 1; }
command -v tar >/dev/null || { echo 'Missing tar' >&2;exit 1; }
curl --fail --location --silent --show-error "$URL" -o "$TMP/bytecek.tar.gz"
tar -xzf "$TMP/bytecek.tar.gz" -C "$TMP"
cd "$TMP/bytecek-tv-${BRANCH}"
sudo bash install.sh
