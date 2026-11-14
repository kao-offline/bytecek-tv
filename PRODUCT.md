# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

A household (several family members) sitting on a couch in front of a TV connected over HDMI to a dedicated Debian laptop. They control it from across the room with a wireless keyboard and/or mouse. Their job: pick something to watch (Spilled, ČT24 live, the web) in a couple of seconds, get back Home, and power the box off.

## Product Purpose

Bytecek TV is a lightweight custom TV launcher that turns an old laptop into a media box without a full desktop environment. Success means anyone in the family can boot it, launch a streaming app, return Home with the corner Menu or F9, and shut down — without seeing Linux.

## Positioning

A personal, self-hosted family TV home screen with its own Bytecek identity (hand-drawn red B), not a generic smart-TV OS: no ads, no store, only the family's own shortcuts.

## Operating Context

- Rendered full-screen in a Chromium app window (1920×1080 over HDMI, eDP 1920×1080 on the laptop) by a local Python server on 127.0.0.1:8765; Openbox window manager.
- Viewed from 2–4 m; inputs are arrow keys, Enter, Escape, Delete, mouse hover/click; F9 returns Home, F10 toggles service mode.
- A separate Tk overlay (`kiosk_overlay.py`) shows the corner Menu over running apps; it is outside the launcher page.
- The box may boot before the network is up: the launcher UI must not depend on remote fonts or CDNs.

## Capabilities and Constraints

- Tiles: Spilled, ČT24, Chrome, user-added web shortcuts (max 20, saved in localStorage, removed with Delete or right-click), Add Shortcut.
- Power menu: shutdown, restart, sleep, each behind a confirmation; `exit >` leaves to the desktop after confirmation.
- Launching shows an "Opening …" state; launched apps resume their existing window.
- API calls need a CSRF token from `/api/config`; static files are served with `no-store`.
- Plain static HTML/CSS/JS, no build step, no framework.

## Brand Commitments

- Name **Bytecek**; the hand-drawn red B logo (`ui/b.svg`) is binding and doubles as the "B" of the wordmark.
- Casual lowercase Czech-household voice in controls ("u sure", "exit >", "shutdown/restart/sleep") is the established tone.
- The user asked (2026-11-14) for a full visual redesign with big, cinematic animation.

## Evidence on Hand

- App icons in `ui/icons/` (spilled.png, ct24.svg, chrome.svg, sources in SOURCES.md).
- No screenshots of real content or posters are available; do not fabricate program listings, now-playing data, or weather.

## Product Principles

1. Readable from the couch: big targets, unmistakable focus, nothing small that matters.
2. Two seconds to watching: Home is a launcher, not a feed.
3. Never feel like a computer: no Linux chrome, no technical errors in plain sight.
4. Safe power actions: anything that turns the box off asks first.
5. Works offline and on modest laptop GPUs; motion must stay smooth.

## Accessibility & Inclusion

Mixed-age family audience: large type, high-contrast focus visible at distance, full keyboard operation, and honour `prefers-reduced-motion`.
