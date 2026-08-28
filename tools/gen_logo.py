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
    #  cols rows  apple  M     4     PRO     gaps(apple-M, M-4, P-R)  pad_top  pad_pro
    "full":  dict(cols=36, rows=18, apple=None,       m=(11, 6), f=(9, 6),  pro=(6, 5),
                  gaps=(2, 1, 1), pad_top=3, pad_pro=1),
    "small": dict(cols=32, rows=16, apple=None,       m=(9, 5),  f=(7, 5),  pro=(5, 5),
                  gaps=(2, 1, 1), pad_top=2, pad_pro=1),
    # previous revision, kept for comparison / people who like the mark in the fetch
    "mark":  dict(cols=38, rows=19, apple=(12, 7),    m=(9, 7),  f=(8, 7),  pro=(7, 4),
                  gaps=(2, 1, 2), pad_top=3, pad_pro=2),
}

def build(size="full", ink=INK, rim=RIM, power=1.55, reach=1.16, apple=None):
    sp = SIZES[size]
    cols, rows = sp["cols"], sp["rows"]
    if apple is None: apple = sp["apple"]
    g = die_field(cols, rows, power, reach)
    cells = [[(v, BLOCK) for v in row] for row in g]

    def put(x, y, i, glyph=BLOCK):
        if 0 <= x < cols and 0 <= y < rows: cells[y][x] = (i, glyph)

    # ---- package rim (continuous hairline frame) ----
    for x in range(cols):
        put(x, 0, rim, RIM_T); put(x, rows - 1, rim, RIM_B)
    for y in range(rows):
        put(0, y, rim, RIM_L); put(cols - 1, y, rim, RIM_R)
    put(0, 0, rim, RIM_TL); put(cols - 1, 0, rim, RIM_TR)
    put(0, rows - 1, rim, RIM_BL); put(cols - 1, rows - 1, rim, RIM_BR)

    aw, ah = apple if apple else (0, 0)
    mw, mh = sp["m"]; fw, fh = sp["f"]
    g1, g2, g3 = sp["gaps"]
    total = (aw + g1 if aw else 0) + mw + g2 + fw
    ox = (cols - total) // 2
    oy = sp["pad_top"]; base = oy + max(ah, mh)

    def blit(bmp, x, y):
        for cy, row in enumerate(bmp):
            for cx, v in enumerate(row):
                if v: put(x + cx, y + cy, ink)

    if aw: blit(glyph_apple(aw, ah), ox, oy)
    blit(glyph_M(mw, mh), ox + (aw + g1 if aw else 0), base - mh)
    blit(glyph_4(fw, fh), ox + (aw + g1 if aw else 0) + mw + g2, base - fh)

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

def preview(cells, path=None, cw=18, ch=36, bg=(26, 28, 34)):
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
    if path: img.save(path)
    return img


# ==========================================================================
# PCB style: compact die + half-block pixel lockup + circuit fan-out
# ==========================================================================
N,E,S,W = 1,2,4,8
BOX = {N|S:"│", E|W:"─", N|E:"└", N|W:"┘", S|E:"┌", S|W:"┐",
       N|E|S:"├", N|E|W:"┴", N|S|W:"┤", E|S|W:"┬", N|E|S|W:"┼",
       N:"╹", S:"╻", E:"╺", W:"╸"}

class Board:
    def __init__(self, cols, rows):
        self.w, self.h = cols, rows
        self.mask = [[0]*cols for _ in range(rows)]
        self.ch = [[None]*cols for _ in range(rows)]
        self.col = [[0]*cols for _ in range(rows)]
    def set(self, x, y, bits, cidx, ch=None):
        if not (0 <= x < self.w and 0 <= y < self.h): return
        self.mask[y][x] |= bits
        self.col[y][x] = cidx
        if ch: self.ch[y][x] = ch
    def trace(self, pts, cidx, via="\u25cb"):
        """pts = list of (x,y) polyline nodes; draws orthogonal runs between them"""
        for i in range(len(pts)-1):
            (x0,y0), (x1,y1) = pts[i], pts[i+1]
            dx, dy = (x1>x0)-(x1<x0), (y1>y0)-(y1<y0)
            x, y = x0, y0
            while (x,y) != (x1,y1):
                b = (S if dy>0 else N if dy<0 else 0) | (E if dx>0 else W if dx<0 else 0)
                self.set(x, y, b, cidx)
                x, y = x+dx, y+dy
            self.set(x1, y1, 0, cidx)          # node (may gain bits from other runs)
        # endpoints
        for (x,y) in (pts[0], pts[-1]):
            if 0 <= x < self.w and 0 <= y < self.h:
                self.ch[y][x] = via; self.mask[y][x] = 0
    def render(self):
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                ch = self.ch[y][x] or BOX.get(self.mask[y][x], " ")
                row.append((self.col[y][x], ch))
            out.append(row)
        return out
    def blit(self, cells, x0, y0):
        for y,row in enumerate(cells):
            for x,(i,ch) in enumerate(row):
                if ch == " ": continue
                X, Y = x0+x, y0+y
                if 0 <= X < self.w and 0 <= Y < self.h:
                    self.ch[Y][X] = ch; self.col[Y][X] = i; self.mask[Y][X] = 0


# --- half-block pixel font: 1 pixel = 1 cell wide, half a cell tall (2 px / row) ---
FONT = {
 "M": ["X.....X",
       "XX...XX",
       "X.X.X.X",
       "X..X..X",
       "X.....X",
       "X.....X",
       "X.....X"],
 "4": ["....XX.",
       "...X.X.",
       "..X..X.",
       ".X...X.",
       "XXXXXXX",
       ".....X.",
       ".....X."],
 "P": ["XXX.",
       "X..X",
       "XXX.",
       "X...",
       "X..."],
 "R": ["XXX.",
       "X..X",
       "XX..",
       "X.X.",
       "X..X"],
 "O": [".XX.",
       "X..X",
       "X..X",
       "X..X",
       ".XX."],
}
HB = {(0,0):" ", (1,0):"\u2580", (0,1):"\u2584", (1,1):"\u2588"}

def blit_font(board, text, x, y, idx, gap=1):
    """blit a word on a shared baseline; returns the width in cells"""
    cx = x
    for t in text:
        bmp = FONT[t]
        h = len(bmp); w = len(bmp[0])
        for c in range(w):
            for r in range((h + 1)//2):
                top = 1 if 2*r < h and bmp[2*r][c] == "X" else 0
                bot = 1 if 2*r+1 < h and bmp[2*r+1][c] == "X" else 0
                g = HB[(top, bot)]
                if g != " ": board.set(cx+c, y+r, 0, idx, g)
        cx += w + gap
    return cx - x - gap

def lockup_width(text, gap=1):
    return sum(len(FONT[t]) and len(FONT[t][0]) for t in text) + gap*(len(text)-1)

# the wordmark written with literal characters (no fake font at all)
# both lines of every lockup are the same width, so the wordmark is justified
LOCKUPS = {
    "ascii": ("\u25cf M 4", "P R O"),                       # plain ASCII - renders everywhere
    "caps":  ("\u25cf \u1d0d 4", "\u1d18 \u0280 \u1d0f"),           # small caps
    "super": ("\u25cf \u1d39 \u2074", "\u1d3e \u1d3f \u1d3c"),           # superscript caps
}

def build_pcb(COLS=32, ROWS=16, DW=14, DH=7, ink=8, rim=6, trace=3, pad=4, via=5,
              power=2.0, reach=1.45, lockup="ascii"):
    ox, oy = (COLS-DW)//2, (ROWS-DH)//2
    L, R, T, B = ox, ox+DW, oy, oy+DH          # boundary cells: cols L..R-1, rows T..B-1
    b = Board(COLS, ROWS)
    N, E, S, W = 1, 2, 4, 8
    VIA = "\u25cb"

    # ---- die field: radial blue glow out of the bottom-left corner ----
    for y in range(T+1, B-1):
        for x in range(L+1, R-1):
            u = (x-(L+1)+0.5)/(DW-2); v = (y-(T+1)+0.5)/(DH-2)
            d = math.hypot(u, 1.0-v)/reach
            t = max(0.0, 1.0-d)**power
            b.set(x, y, 0, min(5, int(round(t*4.4))), BLOCK)

    # ---- traces: stubs leave the die boundary, join bus rails, end in vias ----
    def hrun(y, x0, x1, c):
        for x in range(min(x0,x1), max(x0,x1)+1): b.set(x, y, E|W, c)
    def vrun(x, y0, y1, c):
        for y in range(min(y0,y1), max(y0,y1)+1): b.set(x, y, N|S, c)
    top_cols = list(range(L+2, R-1, 3))
    bot_cols = list(range(L+3, R-2, 3))
    lr_rows  = list(range(T+1, B-1, 2))
    # top rail (row 0) + stubs down to the die
    hrun(0, L-2, R+1, pad)
    for x in top_cols:
        vrun(x, 0, T-1, trace); b.set(x, 0, E|S|W, pad); b.set(x, T, N, rim)
    b.set(L-2, 0, 0, via, VIA); b.set(R+1, 0, 0, via, VIA)
    # bottom rail (last row) + stubs up to the die
    hrun(ROWS-1, L-2, R+1, pad)
    for x in bot_cols:
        vrun(x, B, ROWS-1, trace); b.set(x, ROWS-1, N|E|S, pad); b.set(x, B-1, S, rim)
    b.set(L-2, ROWS-1, 0, via, VIA); b.set(R+1, ROWS-1, 0, via, VIA)
    # left rail + stubs
    vrun(2, 0, ROWS-1, pad)
    for y in lr_rows:
        hrun(y, 2, L-1, trace); b.set(2, y, N|E|S, pad); b.set(L, y, W, rim)
    b.set(2, 0, 0, via, VIA); b.set(2, ROWS-1, 0, via, VIA)
    # right rail + stubs
    vrun(COLS-3, 0, ROWS-1, pad)
    for y in lr_rows:
        hrun(y, R, COLS-3, trace); b.set(COLS-3, y, N|S|W, pad); b.set(R-1, y, E, rim)
    b.set(COLS-3, 0, 0, via, VIA); b.set(COLS-3, ROWS-1, 0, via, VIA)

    # ---- die rim: hairline frame, junctions resolve automatically ----
    for x in range(L+1, R-1):
        b.set(x, T, E|W, rim); b.set(x, B-1, E|W, rim)
    for y in range(T+1, B-1):
        b.set(L, y, N|S, rim); b.set(R-1, y, N|S, rim)
    b.set(L, T, S|E, rim); b.set(R-1, T, S|W, rim)
    b.set(L, B-1, N|E, rim); b.set(R-1, B-1, N|W, rim)

    # ---- lockup: the wordmark, as plain characters, centred in the die ----
    l1, l2 = LOCKUPS[lockup]
    top = T + 1 + max(0, (DH - 2 - 3) // 2)
    for i, line in enumerate((l1, l2)):
        y = top + i * 2
        x = ox + (DW - len(line)) // 2          # equal widths -> same x -> justified
        for c, ch in enumerate(line):
            if ch != " ": b.set(x + c, y, 0, ink, ch)
    return b, (ox, oy, DW, DH)


KNOWN = set(" \u2588\u2580\u2584\u258c\u2590\u259b\u259c\u2599\u259f\u25cb\u00b7"
            "\u2596\u2597\u2598\u259d\u259a\u259e") | set(BOX.values())

def _font(px):
    from PIL import ImageFont
    for cand, idx in (("/System/Library/Fonts/Menlo.ttc", 0),
                      ("/System/Library/Fonts/SFMono-Regular.otf", 0),
                      ("/Library/Fonts/JetBrainsMonoNerdFont-Regular.ttf", 0)):
        try: return ImageFont.truetype(cand, px, index=idx)
        except Exception: pass
    return ImageFont.load_default()

def preview_board(board, path=None, cw=18, ch=36, bg=(26, 28, 34)):
    from PIL import Image, ImageDraw
    rows, cols = board.h, board.w
    img = Image.new("RGB", (cols*cw, rows*ch), bg)
    dr = ImageDraw.Draw(img)
    LW = max(1, cw//8)
    fnt = _font(int(cw*1.55))
    def line(x0,y0,x1,y1,c): dr.line([x0,y0,x1,y1], fill=c, width=LW)
    for y in range(rows):
        for x in range(cols):
            i = board.col[y][x]; ch_ = board.ch[y][x] or BOX.get(board.mask[y][x], " ")
            c = PALETTE[i]; L, T = x*cw, y*ch; R, B = L+cw-1, T+ch-1; cx, cy = L+cw//2, T+ch//2
            if ch_ == " ": continue
            elif ch_ not in KNOWN:                       # literal wordmark character
                try:
                    bb = dr.textbbox((0, 0), ch_, font=fnt)
                    dr.text((L + (cw - (bb[2]-bb[0]))/2 - bb[0], T + (ch - (bb[3]-bb[1]))/2 - bb[1]),
                            ch_, font=fnt, fill=c)
                except Exception:
                    dr.text((L+2, T+2), ch_, font=fnt, fill=c)
                continue
            elif ch_ == BLOCK: dr.rectangle([L,T,R,B], fill=c)
            elif ch_ == "\u2580": dr.rectangle([L,T,R,T+ch//2-1], fill=c)
            elif ch_ == "\u2584": dr.rectangle([L,T+ch//2,R,B], fill=c)
            elif ch_ == "\u258c": dr.rectangle([L,T,L+cw//2-1,B], fill=c)
            elif ch_ == "\u2590": dr.rectangle([L+cw//2,T,R,B], fill=c)
            elif ch_ in "\u259b\u259c\u2599\u259f\u2596\u2597\u2598\u259d\u259a\u259e":
                m = {v:k for k,v in QUAD.items()}[ch_]
                for qy in range(2):
                    for qx in range(2):
                        if m & ((1 if qy==0 else 4) << (0 if qx==0 else 1)):
                            dr.rectangle([L+qx*cw//2, T+qy*ch//2, L+(qx+1)*cw//2-1, T+(qy+1)*ch//2-1], fill=c)
            elif ch_ in ("\u25cb","\u00b7","\u25cf"):
                r = cw//3 if ch_ != "\u00b7" else cw//7
                if ch_ == "\u00b7": dr.ellipse([cx-r,cy-r,cx+r,cy+r], fill=c)
                else: dr.ellipse([cx-r,cy-r,cx+r,cy+r], outline=c, width=LW)
            else:
                bits = {v:k for k,v in BOX.items()}.get(ch_, 0)
                if bits & N: line(cx, T, cx, cy, c)
                if bits & S: line(cx, B, cx, cy, c)
                if bits & E: line(R, cy, cx, cy, c)
                if bits & W: line(L, cy, cx, cy, c)
                if not bits: dr.ellipse([cx-LW,cy-LW,cx+LW,cy+LW], fill=c)
    if path: img.save(path)
    return img

def emit_board(board):
    lines = []
    for y in range(board.h):
        s = ""
        for x in range(board.w):
            i = board.col[y][x]; ch_ = board.ch[y][x] or BOX.get(board.mask[y][x], " ")
            s += ("$%d%s" % (i+1, ch_)) if ch_ != " " else " "
        lines.append(s)
    return "\n".join(lines) + "\n"


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=["pcb", "die"], default="pcb")
    ap.add_argument("--size", choices=["pcb", "pcb32"] + list(SIZES), default="pcb")
    ap.add_argument("--lockup", choices=list(LOCKUPS), default="ascii",
                    help="how the wordmark is spelled (caps/super need a font with those codepoints)")
    ap.add_argument("--apple", action="store_true", help="force the Apple mark into the lockup")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--mono", action="store_true", help="emit a single-colour logo ($1 only)")
    ap.add_argument("--ascii-preview", action="store_true")
    ap.add_argument("--power", type=float, default=1.55)
    ap.add_argument("--reach", type=float, default=1.16)
    a = ap.parse_args()
    tag = {"pcb32": "_small", "small": "_small", "mark": "_mark"}.get(a.size, "")
    out = a.output or os.path.join(here, "themes", "m4pro%s.txt" % tag)
    # COLS = 2*ROWS keeps the whole fetch square (1 cell = 1 x 2 units)
    PCB = {"pcb":   dict(COLS=32, ROWS=16, DW=14, DH=7),
           "pcb32": dict(COLS=36, ROWS=18, DW=16, DH=8)}
    board = None
    if a.size in PCB:
        board = build_pcb(**PCB[a.size], power=a.power, reach=a.reach, lockup=a.lockup)[0]
        grid = board.render()
        cells = None
    else:
        cells = build(a.size, power=a.power, reach=a.reach, apple=(12, 7) if a.apple else None)
        grid = cells
    os.makedirs(os.path.dirname(out), exist_ok=True)
    text = emit_board(board) if board else emit(cells, a.mono)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s  (%dx%d)" % (out, len(grid[0]), len(grid)))
    pre = a.preview or os.path.join(here, "assets", "preview%s.png" % tag)
    if not a.mono:
        try:
            (preview_board(board, pre) if board else preview(cells, pre)); print("wrote %s" % pre)
        except ImportError:
            print("Pillow missing: preview skipped", file=sys.stderr)
    if a.ascii_preview:
        ramp = " .:-=+*#%@"
        for row in grid: print("".join(ramp[i] if gl == BLOCK else gl for i, gl in row))

if __name__ == "__main__":
    main()
