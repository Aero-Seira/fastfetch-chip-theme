#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_logo.py -- build an Apple-Silicon "M4 Pro" badge logo for fastfetch.

The artwork is a square chip die:
  * a light hairline package rim
  * a dark navy die body with a blue glow rising from the bottom-left corner
  * the silver lockup:  Apple-mark + "M4", with "PRO" centred underneath

Everything is drawn from geometry (no bitmap is required), then quantised to a
9-colour palette.  The output file uses fastfetch's "$1" .. "$9" colour
placeholders, so the whole logo can be re-tinted from `logo.color` in the
fastfetch config.

Usage:
    python3 tools/gen_logo.py [-o themes/m4pro.txt] [--preview assets/preview.png]
                              [--cols 38] [--rows 19] [--mono]
"""
import argparse, math, os, sys

# --------------------------------------------------------------------------
# palette: index 0..8  ->  $1..$9
# --------------------------------------------------------------------------
PALETTE = [
    (10, 14, 28),     # $1  die body, near-black navy
    (16, 26, 50),     # $2  navy
    (26, 48, 104),    # $3  indigo
    (38, 78, 168),    # $4  azure
    (56, 122, 216),   # $5  bright blue
    (96, 168, 236),   # $6  sky
    (150, 196, 228),  # $7  pale blue   (package rim)
    (200, 222, 238),  # $8  silver      (lettering)
    (244, 250, 255),  # $9  bright silver (highlight)
]
RIM, INK = 6, 7      # 0-based palette indices

BLOCK = "\u2588"     # full block, used for every painted cell

# ==========================================================================
# shape rasteriser -- cell space: 1 column = 1 unit wide, 1 row = 2 units tall
# ==========================================================================
class Shape:
    def __init__(self): self.parts = []
    def add(self, fn): self.parts.append((1, fn)); return self
    def sub(self, fn): self.parts.append((-1, fn)); return self
    def hit(self, x, y):
        on = False
        for sign, fn in self.parts:
            h = fn(x, y)
            on = (on or h) if sign > 0 else (on and not h)
        return on

def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
def circle(cx, cy, r):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r
def ellipse(cx, cy, rx, ry, ang=0.0):
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    def f(x, y):
        dx, dy = x - cx, y - cy
        u, v = dx * ca - dy * sa, dx * sa + dy * ca
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0
    return f
def seg(x0, y0, x1, y1, t):
    r = t / 2.0
    def f(x, y):
        dx, dy = x1 - x0, y1 - y0
        L = dx * dx + dy * dy
        s = 0.0 if L == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L))
        px, py = x0 + s * dx, y0 + s * dy
        return (x - px) ** 2 + (y - py) ** 2 <= r * r
    return f

def raster(cols, rows, shape, sub=6, thr=0.45):
    out = []
    for r in range(rows):
        line = []
        for c in range(cols):
            hit = 0
            for sy in range(sub):
                for sx in range(sub):
                    x = c + (sx + 0.5) / sub
                    y = 2 * r + 2 * (sy + 0.5) / sub
                    if shape.hit(x, y): hit += 1
            line.append(1 if hit / (sub * sub) >= thr else 0)
        out.append(line)
    return out

# ==========================================================================
# glyphs of the lockup
# ==========================================================================
def glyph_apple(cols, rows):
    """Apple mark: two lobes + leaf, circular bite on the right edge."""
    W, H = cols, rows * 2.0
    sx, sy = W / 12.0, H / 14.0
    s = Shape()
    s.add(circle(3.6 * sx, 6.2 * sy, 3.3 * sx))          # left lobe
    s.add(circle(8.4 * sx, 6.2 * sy, 3.3 * sx))          # right lobe
    s.add(ellipse(6.0 * sx, 9.0 * sy, 5.9 * sx, 5.0 * sy))  # lower body
    s.sub(circle(12.6 * sx, 7.4 * sy, 2.7 * sx))         # bite
    s.add(ellipse(7.4 * sx, 1.7 * sy, 2.3 * sx, 1.0 * sy, -32))  # leaf
    return raster(cols, rows, s)

def glyph_M(cols, rows):
    W, H = cols, rows * 2.0; t = W * 0.165
    s = Shape()
    s.add(rect(0, 0, t, H)); s.add(rect(W - t, 0, W, H))
    s.add(seg(t * 0.5, 0, W * 0.5, H * 0.60, t * 1.05))
    s.add(seg(W - t * 0.5, 0, W * 0.5, H * 0.60, t * 1.05))
    return raster(cols, rows, s)

def glyph_4(cols, rows):
    W, H = cols, rows * 2.0; t = W * 0.185
    stem, bar0, bar1 = W * 0.66, H * 0.575, H * 0.735
    s = Shape()
    s.add(rect(stem, 0, stem + t, H))
    s.add(seg(stem + t * 0.5, t * 0.3, W * 0.06, bar0 + t * 0.4, t * 1.1))
    s.add(rect(0, bar0, W, bar1))
    return raster(cols, rows, s)

def _bowl(W, H): return ellipse(W * 0.52, H * 0.275, W * 0.47, H * 0.30)
def _counter(W, H): return ellipse(W * 0.52, H * 0.275, W * 0.23, H * 0.135)

def glyph_P(cols, rows):
    W, H = cols, rows * 2.0; t = W * 0.255
    s = Shape(); s.add(rect(0, 0, t, H)); s.add(_bowl(W, H)); s.sub(_counter(W, H))
    return raster(cols, rows, s)

def glyph_R(cols, rows):
    W, H = cols, rows * 2.0; t = W * 0.255
    s = Shape(); s.add(rect(0, 0, t, H)); s.add(_bowl(W, H)); s.sub(_counter(W, H))
    s.add(seg(W * 0.45, H * 0.45, W * 0.98, H, t * 1.25))
    return raster(cols, rows, s)

def glyph_O(cols, rows):
    W, H = cols, rows * 2.0
    s = Shape()
    s.add(ellipse(W * 0.5, H * 0.5, W * 0.5, H * 0.5))
    s.sub(ellipse(W * 0.5, H * 0.5, W * 0.27, H * 0.30))
    return raster(cols, rows, s)

# ==========================================================================
# die field: radial blue glow anchored at the bottom-left corner
# ==========================================================================
def die_field(cols, rows, power=1.55, reach=1.16):
    grid = []
    for r in range(rows):
        line = []
        for c in range(cols):
            u = (c + 0.5) / cols                 # 0 = left  edge, 1 = right edge
            v = (r + 0.5) / rows                 # 0 = top   edge, 1 = bottom edge
            d = math.hypot(u, 1.0 - v) / reach   # distance from bottom-left corner
            t = max(0.0, 1.0 - d) ** power
            idx = int(round(t * 5.0))            # 0..5 -> $1..$6
            line.append(min(5, idx))
        grid.append(line)
    return grid

# ==========================================================================
# compose
# ==========================================================================
# rim pieces: continuous hairline frame (top / bottom / left / right / corners)
RIM_T, RIM_B, RIM_L, RIM_R = "\u2580", "\u2584", "\u258c", "\u2590"
RIM_TL, RIM_TR, RIM_BL, RIM_BR = "\u259b", "\u259c", "\u2599", "\u259f"

SIZES = {
    #            cols rows  apple   M     4     PRO    gaps(a-M,M-4,P-R)
    "full":  dict(cols=38, rows=19, apple=(12, 7), m=(9, 7), f=(8, 7), pro=(7, 4),
                  gaps=(2, 1, 2), pad_top=3, pad_pro=2),
    "small": dict(cols=34, rows=17, apple=(11, 7), m=(8, 6), f=(7, 6), pro=(6, 4),
                  gaps=(2, 1, 2), pad_top=2, pad_pro=1),
}

def build(size="full", ink=INK, rim=RIM, power=1.55, reach=1.16):
    sp = SIZES[size]
    cols, rows = sp["cols"], sp["rows"]
    g = die_field(cols, rows, power, reach)
    cells = [[(v, BLOCK) for v in row] for row in g]

    def put(x, y, i, glyph=BLOCK):
        if 0 <= x < cols and 0 <= y < rows: cells[y][x] = (i, glyph)

    # ---- package rim (hairline) ----
    for x in range(cols):
        put(x, 0, rim, RIM_T); put(x, rows - 1, rim, RIM_B)
    for y in range(rows):
        put(0, y, rim, RIM_L); put(cols - 1, y, rim, RIM_R)
    put(0, 0, rim, RIM_TL); put(cols - 1, 0, rim, RIM_TR)
    put(0, rows - 1, rim, RIM_BL); put(cols - 1, rows - 1, rim, RIM_BR)

    # ---- lockup: apple + M + 4 ----
    aw, ah = sp["apple"]; mw, mh = sp["m"]; fw, fh = sp["f"]
    g1, g2, g3 = sp["gaps"]
    total = aw + g1 + mw + g2 + fw
    ox = (cols - total) // 2
    oy = sp["pad_top"]; base = oy + ah
    def blit(bmp, x, y):
        for cy, row in enumerate(bmp):
            for cx, v in enumerate(row):
                if v: put(x + cx, y + cy, ink)
    blit(glyph_apple(aw, ah), ox, oy)
    blit(glyph_M(mw, mh), ox + aw + g1, base - mh)
    blit(glyph_4(fw, fh), ox + aw + g1 + mw + g2, base - fh)

    # ---- PRO ----
    pw, ph = sp["pro"]
    ptot = pw * 3 + g3 * 2
    pox = (cols - ptot) // 2; poy = base + sp["pad_pro"]
    blit(glyph_P(pw, ph), pox, poy)
    blit(glyph_R(pw, ph), pox + pw + g3, poy)
    blit(glyph_O(pw, ph), pox + 2 * (pw + g3), poy)
    return cells

def emit(cells, mono=False):
    lines = []
    for row in cells:
        out = []
        for i, glyph in row:
            out.append("$%d%s" % ((1 if mono else i + 1), glyph))
        lines.append("".join(out))
    return "\n".join(lines) + "\n"

def preview(cells, path, cw=18, ch=36, bg=(26, 28, 34)):
    from PIL import Image, ImageDraw
    rows, cols = len(cells), len(cells[0])
    img = Image.new("RGB", (cols * cw, rows * ch), bg)
    dr = ImageDraw.Draw(img)
    for y in range(rows):
        for x in range(cols):
            i, glyph = cells[y][x]
            c = PALETTE[i]; L, T = x * cw, y * ch
            half_w, half_h = cw // 2, ch // 2
            box = {BLOCK: (L, T, L + cw - 1, T + ch - 1),
                   RIM_T: (L, T, L + cw - 1, T + half_h - 1),
                   RIM_B: (L, T + half_h, L + cw - 1, T + ch - 1),
                   RIM_L: (L, T, L + half_w - 1, T + ch - 1),
                   RIM_R: (L + half_w, T, L + cw - 1, T + ch - 1),
                   RIM_TL: (L, T, L + half_w - 1, T + half_h - 1),
                   RIM_TR: (L + half_w, T, L + cw - 1, T + half_h - 1),
                   RIM_BL: (L, T + half_h, L + half_w - 1, T + ch - 1),
                   RIM_BR: (L + half_w, T + half_h, L + cw - 1, T + ch - 1)}[glyph]
            dr.rectangle(list(box), fill=c)
    img.save(path)

def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", choices=list(SIZES), default="full")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--mono", action="store_true", help="emit a single-colour logo ($1 only)")
    ap.add_argument("--ascii-preview", action="store_true")
    ap.add_argument("--power", type=float, default=1.55)
    ap.add_argument("--reach", type=float, default=1.16)
    a = ap.parse_args()
    out = a.output or os.path.join(here, "themes", "m4pro%s.txt" % ("_small" if a.size == "small" else ""))
    cells = build(a.size, power=a.power, reach=a.reach)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(emit(cells, a.mono))
    print("wrote %s  (%dx%d)" % (out, len(cells[0]), len(cells)))
    pre = a.preview or os.path.join(here, "assets", "preview%s.png" % ("_small" if a.size == "small" else ""))
    if not a.mono:
        try:
            preview(cells, pre); print("wrote %s" % pre)
        except ImportError:
            print("Pillow missing: preview skipped", file=sys.stderr)
    if a.ascii_preview:
        ramp = " .:-=+*#%@"
        for row in cells: print("".join(ramp[i] if glyph == BLOCK else "X" for i, glyph in row))

if __name__ == "__main__":
    main()
