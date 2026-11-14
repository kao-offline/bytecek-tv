#!/usr/bin/env python3
"""Fullscreen velvet curtain (same look as Home) that opens onto the desktop.

curtain.py [delay_ms]  - appears closed at once, opens after delay_ms, then exits."""
import sys
import time
import tkinter as tk

STOPS = [(0, '#2c070c'), (5, '#6a1520'), (9, '#3a0910'), (15, '#7a1a25'), (19, '#450b13'), (24, '#5e121c'),
         (28, '#2f080d'), (35, '#741823'), (40, '#4a0c14'), (46, '#6b1621'), (50, '#320a0f'), (57, '#701723'),
         (62, '#420b12'), (69, '#7c1b26'), (74, '#3b0a11'), (80, '#62131d'), (85, '#2e070c'), (92, '#731822'),
         (100, '#3d0a11')]
RGB = [(p, tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))) for p, c in STOPS]


def colour(pct, shade):
    for (p0, c0), (p1, c1) in zip(RGB, RGB[1:]):
        if pct <= p1:
            t = (pct - p0) / (p1 - p0) if p1 > p0 else 0
            return '#%02x%02x%02x' % tuple(int((a + (b - a) * t) * shade) for a, b in zip(c0, c1))
    return STOPS[-1][1]


def curtain_half(width, height, mirror):
    """Velvet folds across, darker toward the top and bottom edges (as on Home)."""
    img = tk.PhotoImage(width=width, height=height)
    xs = list(range(width - 1, -1, -1)) if mirror else list(range(width))
    edge = int(height * .18)
    bands = 18
    spans = [(edge, height - edge, 1.0)]
    for band in range(bands):
        y0, y1 = edge * band // bands, edge * (band + 1) // bands
        spans.append((y0, y1, .5 + .5 * band / bands))
        spans.append((height - y1, height - y0, .55 + .45 * band / bands))
    for y0, y1, shade in spans:
        if y1 > y0:
            row = '{' + ' '.join(colour(x / (width - 1) * 100, shade) for x in xs) + '}'
            img.put(row, to=(0, y0, width, y1))
    return img


def ease(t):
    # close to Home's cubic-bezier(.72,0,.18,1)
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def main():
    delay = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    root = tk.Tk()
    root.withdraw()
    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    half = w // 2 + 10

    # No compositor here, so the halves are separate windows that slide off-screen
    # and the real desktop shows through the opening gap.
    def panel(x, mirror):
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.geometry(f'{half}x{h}+{x}+0')
        win.configure(bg='#2c070c', cursor='none')
        canvas = tk.Canvas(win, width=half, height=h, highlightthickness=0, bd=0, bg='#2c070c')
        canvas.pack()
        img = curtain_half(half, h, mirror)
        canvas.create_image(0, 0, image=img, anchor='nw')
        canvas.image = img
        win.attributes('-topmost', True)
        return win

    left, right = panel(0, False), panel(w - half, True)
    logo = None
    try:
        logo_img = tk.PhotoImage(file='/opt/bytecek/boot/b.png')
        lw, lh = logo_img.width(), logo_img.height()
        logo = tk.Toplevel(root)
        logo.overrideredirect(True)
        logo.geometry(f'{lw}x{lh}+{(w - lw) // 2}+{(h - lh) // 2}')
        lc = tk.Canvas(logo, width=lw, height=lh, highlightthickness=0, bd=0, bg='#320a0f')
        lc.pack()
        lc.create_image(0, 0, image=logo_img, anchor='nw')
        lc.image = logo_img
        logo.attributes('-topmost', True)
    except tk.TclError:
        pass
    root.update()

    duration = 1.05
    start = [None]

    def frame():
        if start[0] is None:
            start[0] = time.monotonic()
        t = min(1.0, (time.monotonic() - start[0]) / duration)
        offset = int(half * 1.02 * ease(t))
        left.geometry(f'+{-offset}+0')
        right.geometry(f'+{w - half + offset}+0')
        if logo is not None and t > .1:
            logo.withdraw()
        if t < 1:
            root.after(8, frame)
        else:
            root.after(30, root.destroy)

    root.after(delay, frame)
    root.after(delay + 5000, root.destroy)  # never leave the screen covered
    root.mainloop()


if __name__ == '__main__':
    main()
