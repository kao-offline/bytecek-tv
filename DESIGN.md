---
name: Bytecek TV
description: A family TV launcher dressed as a small night-time cinema, with a marquee that lights on the thing you choose.
colors:
  ground: "#120809"
  ground-deep: "#0b0506"
  velvet: "#5a1019"
  velvet-dark: "#2c070c"
  card: "#24120f"
  cream: "#f6e9cc"
  cream-dim: "#bfae91"
  brass: "#a7814b"
  bulb: "#ffd98c"
  logo-red: "#e12929"
typography:
  display:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontSize: "clamp(34px, 3.6vw, 60px)"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontSize: "clamp(28px, 2.8vw, 44px)"
    fontWeight: 600
    lineHeight: 1.1
  title:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontSize: "clamp(20px, 1.6vw, 30px)"
    fontWeight: 600
    letterSpacing: "0.02em"
  body:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontSize: "22px"
    fontWeight: 500
  label:
    fontFamily: "Big Shoulders, Arial Narrow, sans-serif"
    fontSize: "clamp(16px, 1.1vw, 21px)"
    fontWeight: 500
rounded:
  tile: "24%"
  card: "16px"
  panel: "18px"
  dialog: "24px"
  toast: "12px"
  field: "10px"
  full: "50%"
spacing:
  inset: "16px"
  stack: "14px"
  gap-x: "clamp(18px, 2.3vw, 44px)"
  dialog: "22px 36px 26px"
components:
  app-tile:
    backgroundColor: "{colors.card}"
    textColor: "{colors.cream-dim}"
    typography: "{typography.title}"
    rounded: "{rounded.tile}"
    width: "150px"
  app-tile-focus:
    textColor: "{colors.cream}"
  resume-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.cream}"
    rounded: "{rounded.card}"
  text-action:
    textColor: "{colors.cream-dim}"
    typography: "{typography.headline}"
    padding: "4px 6px"
  text-action-focus:
    textColor: "{colors.bulb}"
  power-button:
    backgroundColor: "{colors.logo-red}"
    textColor: "#ffffff"
    rounded: "{rounded.full}"
    size: "clamp(40px, 3.4vw, 56px)"
  dialog:
    backgroundColor: "{colors.card}"
    textColor: "{colors.cream}"
    rounded: "{rounded.dialog}"
    padding: "{spacing.dialog}"
  text-field:
    backgroundColor: "#160a09"
    textColor: "{colors.cream}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "10px 12px"
---

# Design System: Bytecek TV

## Overview

**Creative North Star: "The Kino Marquee"**

The living-room cinema at night. The house is near-black oxblood velvet with one warm spotlight falling from above; everything sits quietly in the dark until it is chosen, and then a ring of marquee bulbs lights around it while the rest of the house dims. Launching an app closes a velvet curtain behind the family; returning Home parts it again.

The screen is read from 2 to 4 m, so density is low and type is large: one condensed display face does every job, set in cream like bulb light. Brass hairlines frame every object instead of borders or fills. Motion is cinematic but restrained: the bulbs pulse slowly rather than chase, and the curtain is the one big move. The system refuses the smart-TV card wall with a blurred backdrop.

**Key Characteristics:**
- Dark velvet house, one top-centre spotlight, vignette to the floor.
- A single typeface (Big Shoulders, self-hosted) for every role.
- Brass inset hairlines frame tiles, cards, panels and dialogs.
- Focus is a dotted bulb ring plus lift; siblings dim to 62%.
- Velvet curtain opens on boot and return, closes on launch.

## Colors

A warm, low-key palette: oxblood blacks, cream light, brass trim, and one hot red that belongs to the logo.

### Primary
- **Marquee Bulb** (bulb): the focus colour. The dotted bulb ring, focused text actions, the progress fill, input caret and focus outlines. Never a resting fill.

### Secondary
- **Logo Red** (logo-red): reserved for the hand-drawn B, the power button and text selection.

### Tertiary
- **Brass Trim** (brass): hairline frames only, as inset 1px strokes at 38-55% alpha (`rgba(167,129,75,.38)` resting, `.45` on dialogs and toast, `.55` on fields).

### Neutral
- **House Ground** (ground) and **Deep Ground** (ground-deep): the page and the bottom of its vertical gradient.
- **Velvet** (velvet) and **Dark Velvet** (velvet-dark): the curtain cloth and the artwork fallback gradient on episode cards.
- **Booth Brown** (card): every raised surface: tiles, episode cards, power panel (at 94%), dialogs, toast.
- **Cream Light** (cream): primary text and focused labels.
- **Dim Cream** (cream-dim): resting labels, section headings, resting text actions, the clock.

### Named Rules
**The One Red Rule.** Logo red appears on the B, the power button and selection, nowhere else. Focus is bulb gold, not red.

**The Dark House Rule.** At rest nothing glows. Light (bulb ring, cream label, lifted shadow) is the response to focus or hover.

## Typography

**Display Font:** Big Shoulders (variable 100-900, self-hosted at `/fonts/BigShouldersDisplay.ttf`, fallback Arial Narrow)
**Body Font:** the same face; there is no second family.

**Character:** Tall, condensed, marquee-sign letters that stay legible at couch distance and give lowercase household copy ("u sure", "exit >") a cinema-front voice.

### Hierarchy
- **Display** (600, clamp(34px, 3.6vw, 60px), 1): the wordmark. Dialog titles use the same size at 700.
- **Headline** (600, clamp(28px, 2.8vw, 44px), 1.1): text actions in dialogs; the power menu and exit run larger at clamp(30-34px, 3.2-3.4vw, 50-58px).
- **Title** (600, clamp(20px, 1.6vw, 30px), +0.02em): tile labels, the row heading (clamp(22px, 1.7vw, 32px), +0.03em), episode show names (700, line-height 1.05).
- **Body** (500, 22px): field text, field labels, toast.
- **Label** (500, clamp(16px, 1.1vw, 21px)): episode meta lines. The clock is tabular figures at clamp(26px, 2.4vw, 44px).

### Named Rules
**The Couch Distance Rule.** No text below 16px; every size is a `clamp()` keyed to viewport width so 1920x1080 over HDMI reads from the sofa.

**The Lowercase Voice Rule.** Controls and headings are lowercase as written in the copy; never force uppercase or letterspaced caps.

## Layout

A full-viewport, non-scrolling page (`100dvh`, body overflow hidden) in three bands: a top bar (clamp(84px, 13vh, 150px)) with the wordmark centred and the clock absolute top right; a flexible, vertically centred stage; corner controls pinned bottom left (power) and bottom right (exit).

The app grid is centred, up to 6 columns of max 150px (`--columns` set from the item count), column gap `gap-x`, row gap clamp(30px, 4vh, 46px), max width 1280px. The continue-watching row is a horizontal scroll-snap strip of 16:9 cards, four per 1500px measure, with edge padding `max(28px, (100vw - 1500px) / 2)`.

Breakpoints: at 900px the grid drops to 4 columns and the clock hides; at 600px it drops to 3 columns (gap 24px 18px) and cards become 72vw.

## Elevation & Depth

Depth is lighting, not stacking. Surfaces sit on soft black drop shadows under a brass inset hairline; focus raises the object and warms its hairline. The house itself gets depth from a radial spotlight at the top and a radial vignette at the floor.

### Shadow Vocabulary
- **Resting** (`inset 0 0 0 1px rgba(167,129,75,.38), 0 10px 22px rgba(0,0,0,.45)`): tiles and episode cards.
- **Lifted** (`inset 0 0 0 1px rgba(255,217,140,.6), 0 18px 34px rgba(0,0,0,.55)`): focused or hovered tile and card, with translateY(-6 to -7px) and scale 1.04-1.05.
- **Floating** (`inset 0 0 0 1px rgba(167,129,75,.45), 0 26px 60px rgba(0,0,0,.65)`): dialogs; the power panel uses `0 18px 40px rgba(0,0,0,.6)`.
- **Bulb glow** (`drop-shadow(0 0 5px rgba(255,200,110,.85))`): only on the bulb ring.

### Named Rules
**The Hairline Frame Rule.** Raised surfaces are framed with an inset brass hairline, never an outer border.

## Shapes

Soft, theatre-sign rounding. App tiles are squircle-like squares (24% radius); episode cards 16px; the power panel 18px; dialogs 24px; toast 12px; fields 10px; the power button is a full circle. The bulb ring sits 13px outside its object, a 5px dotted stroke whose radius follows the object (24% + 6px on tiles, 24px on cards).

## Components

### App Tile
Quiet booth-brown square with an icon at 64% (brand icons may fill or tint the square), dim-cream label below. On focus or hover: lift, warm hairline, cream label, lit bulb ring; every other tile dims to 62% opacity. The add tile is transparent with a 2px dim-cream inset stroke.

### Episode Card (continue watching)
16:9 card, artwork cover-fit (or a velvet gradient with a faint 22%-cream initial), a bottom scrim to `rgba(10,4,5,.88)`, show name and meta inset 16px, and a 4px progress bar (22% cream track, bulb fill). Same focus behaviour as the tile.

### Text Actions (exit, power menu, dialog buttons)
No fill, no border: large type in dim cream (exit rests in cream). Focus and hover turn the text bulb gold with a 4px dotted underline offset 8-10px, the bulb ring's typographic echo.

### Power Button
Logo-red circle, white stroke icon at 52%, scales to 1.12 on focus. Opens a booth-brown panel above it that pops in from the bottom left.

### Dialog
Booth-brown, 24px radius, floating shadow, centred title at display size, two text actions spaced apart. Backdrop `rgba(8,3,4,.6)`.

### Text Field
Dark field (`#160a09`), 1px brass border at 55%, 10px radius, cream text, bulb caret; focus shows a 2px bulb outline offset 2px.

### Curtain (signature)
Two velvet halves with a vertical pleat gradient and top/bottom shading, sliding over 1.05s on `cubic-bezier(.72,0,.18,1)`; the house dims behind them and, when closed for a launch, the B logo flickers on in the centre.

## Do's and Don'ts

### Do:
- **Do** mark focus with the dotted bulb ring (5px dotted, 13px outside, slow 2.4s two-step pulse) plus lift, and dim siblings to 62%.
- **Do** frame every raised surface with the brass inset hairline and a soft black drop shadow.
- **Do** keep every size a viewport `clamp()` with nothing below 16px.
- **Do** ease state changes on `cubic-bezier(.16,1,.3,1)`, and collapse all motion under `prefers-reduced-motion`.
- **Do** self-host the font; the box may boot offline.

### Don't:
- **Don't** use logo red for focus, accents or decoration beyond the B, the power button and selection.
- **Don't** animate the bulbs as a running chase or add glow at rest.
- **Don't** build a smart-TV card wall with a blurred backdrop.
- **Don't** introduce a second typeface or uppercase letterspaced labels.
