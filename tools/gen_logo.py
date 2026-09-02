#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_logo.py -- build chip badge logos for fastfetch.

The artwork is a square chip die on a PCB:
  * a light hairline package rim with circuit fan-out (traces, rails, vias)
  * a dark die body with a glow rising from the bottom-left corner
  * the wordmark as literal characters (two centred lines), e.g.:

        intel            AMD             M 4
        CORE i7          RYZEN 9        P R O

Chip wordmarks, brand palettes and CPU-detection patterns live in
tools/chips.py -- adding a chip is a registry entry, not new code.

Everything is drawn from geometry (no bitmap is required), then quantised to a
9-colour palette.  The output file uses fastfetch's "$1" .. "$9" colour
placeholders, so the whole logo can be re-tinted from `logo.color` in the
fastfetch config.  A ready-to-use per-chip config.jsonc is emitted next to the
logo files.

Usage:
    python3 tools/gen_logo.py --detect                # chip for this machine
    python3 tools/gen_logo.py --list                  # registered chips
    python3 tools/gen_logo.py --all                   # regenerate everything
    python3 tools/gen_logo.py --auto                  # model-specific logo
    python3 tools/gen_logo.py --auto --dest ~/.config/fastfetch
    py -3 tools/gen_logo.py --auto --dest %APPDATA%/fastfetch  # Windows
    python3 tools/gen_logo.py --chip i7               # one chip, pcb + small
    python3 tools/gen_logo.py --chip m4pro --size pcb [-o out.txt]
"""
import argparse, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chips as registry

# Windows: redirected stdout uses the OEM code page, so a chip label holding
# U+25CF would raise UnicodeEncodeError -- replace unmappable chars instead.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def json_path(path):
    """Filesystem path -> JSON string (bare Windows backslashes are illegal)."""
    return path.replace("\\", "/")

# default palette (Apple Pro blue); every chip normally brings its own
PALETTE = registry.PALETTES["apple-blue"]
RIM, INK = 6, 7      # 0-based palette indices

BLOCK = "\u2588"     # full block, used for every painted die cell

# ==========================================================================
# die fields: one per vendor badge design (see tools/chips.py docstring).
# Each returns a grid of t in 0..1; callers map t to palette indices.
# ==========================================================================
def _field_glow(cols, rows, power, reach):
    # radial glow out of the bottom-left corner (Apple keynote die renders)
    g = []
    for r in range(rows):
        row = []
        for c in range(cols):
            u = (c + 0.5) / cols                 # 0 = left  edge, 1 = right edge
            v = (r + 0.5) / rows                 # 0 = top   edge, 1 = bottom edge
            d = math.hypot(u, 1.0 - v) / reach   # distance from bottom-left corner
            row.append(max(0.0, 1.0 - d) ** power)
        g.append(row)
    return g

def _field_band(cols, rows, power, reach):
    # tilted horizontal swoosh band (Intel Core badge)
    g = []
    for r in range(rows):
        row = []
        for c in range(cols):
            u = (c + 0.5) / cols
            v = (r + 0.5) / rows
            band = v - 0.30 * (u - 0.5)          # slight upward tilt
            d = abs(band - 0.60) / (0.42 * reach)
            row.append(max(0.0, 1.0 - d) ** power)
        g.append(row)
    return g

def _field_ring(cols, rows, power, reach):
    # centred ring (AMD Ryzen mark); cell space: 1 col = 1 unit, 1 row = 2 units
    g = []
    cx, cy = cols / 2.0, float(rows)
    R = min(cols, rows * 2) * 0.40 * reach
    for r in range(rows):
        row = []
        for c in range(cols):
            x, y = c + 0.5, 2 * r + 1.0
            d = abs(math.hypot(x - cx, y - cy) - R) / (R * 0.5)
            row.append(max(0.0, 1.0 - d) ** power)
        g.append(row)
    return g

FIELDS = {"glow": _field_glow, "band": _field_band, "ring": _field_ring}

def field_idx(field, cols, rows, power, reach, scale):
    t = FIELDS[field](cols, rows, power, reach)
    return [[min(5, int(round(v * scale))) for v in row] for row in t]

# rim pieces: continuous hairline frame (top / bottom / left / right / corners)
RIM_T, RIM_B, RIM_L, RIM_R = "\u2580", "\u2584", "\u258c", "\u2590"
RIM_TL, RIM_TR, RIM_BL, RIM_BR = "\u259b", "\u259c", "\u2599", "\u259f"

SIZES = {
    "full":  dict(cols=36, rows=18),
    "small": dict(cols=32, rows=16),
}

def _lockup_rows(lines):
    """centre 1-2 literal text lines; lines sit two rows apart"""
    texts = [l for l in lines if l and l.strip()]
    return texts, 2 * len(texts) - 1

def build(size="full", lines=("\u25cf M 4", "P R O"), ink=INK, rim=RIM,
          power=1.55, reach=1.16, field="glow"):
    """bare die style: vendor field + hairline rim + literal wordmark"""
    sp = SIZES[size]
    cols, rows = sp["cols"], sp["rows"]
    g = field_idx(field, cols, rows, power, reach, scale=5.0)
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

    # ---- wordmark: literal characters, centred ----
    texts, block = _lockup_rows(lines)
    y0 = max(1, (rows - block) // 2)
    for i, line in enumerate(texts):
        y = y0 + i * 2
        x = (cols - len(line)) // 2
        for c, ch in enumerate(line):
            if ch != " ": put(x + c, y, ink, ch)
    return cells

def emit(cells, mono=False):
    lines = []
    for row in cells:
        out = []
        for i, glyph in row:
            out.append("$%d%s" % ((1 if mono else i + 1), glyph))
        lines.append("".join(out))
    return "\n".join(lines) + "\n"

# ==========================================================================
# PCB style: compact die + literal wordmark + circuit fan-out
# ==========================================================================
N, E, S, W = 1, 2, 4, 8
BOX = {N|S:"│", E|W:"─", N|E:"└", N|W:"┘", S|E:"┌", S|W:"┐",
       N|E|S:"├", N|E|W:"┴", N|S|W:"┤", E|S|W:"┬", N|E|S|W:"┼",
       N:"╹", S:"╻", E:"╺", W:"╸"}
QUAD = {1:"\u2598", 2:"\u259d", 4:"\u2596", 8:"\u2597",
        1|2:"\u2580", 4|8:"\u2584", 1|4:"\u258c", 2|8:"\u2590",
        1|2|4:"\u259b", 1|2|8:"\u259c", 1|4|8:"\u2599", 2|4|8:"\u259f",
        1|8:"\u259a", 2|4:"\u259e", 1|2|4|8:"\u2588"}

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
    def put(self, x, y, bits, cidx, ch=None):
        """exact bits (no OR) -- for corner turns that must not become ┼"""
        if not (0 <= x < self.w and 0 <= y < self.h): return
        self.mask[y][x] = bits
        self.col[y][x] = cidx
        self.ch[y][x] = ch
    def render(self):
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                ch = self.ch[y][x] or BOX.get(self.mask[y][x], " ")
                row.append((self.col[y][x], ch))
            out.append(row)
        return out

def build_pcb(COLS=32, ROWS=16, DW=16, DH=8, ink=8, rim=6, trace=3, pad=4,
              via=5, power=2.0, reach=1.45, lines=("\u25cf M 4", "P R O"),
              field="glow", dual=False):
    ox, oy = (COLS-DW)//2, (ROWS-DH)//2
    L, R, T, B = ox, ox+DW, oy, oy+DH          # boundary cells: cols L..R-1, rows T..B-1
    b = Board(COLS, ROWS)
    VIA = "\u25cb"

    # ---- die field: vendor-specific badge artwork ----
    g = field_idx(field, DW-2, DH-2, power, reach, scale=4.4)
    for y in range(T+1, B-1):
        for x in range(L+1, R-1):
            b.set(x, y, 0, g[y-(T+1)][x-(L+1)], BLOCK)

    # ---- traces: a closed bus loop rounds the board corners; stubs escape
    # the die with a one-cell jog, like real fan-out routing ----
    def hrun(y, x0, x1, c):
        for x in range(min(x0,x1), max(x0,x1)+1): b.set(x, y, E|W, c)
    def vrun(x, y0, y1, c):
        for y in range(min(y0,y1), max(y0,y1)+1): b.set(x, y, N|S, c)

    RL_, RR_ = 2, COLS - 3                   # left / right rail columns
    # closed bus loop with proper corner turns
    hrun(0, RL_, RR_, pad); hrun(ROWS-1, RL_, RR_, pad)
    vrun(RL_, 0, ROWS-1, pad); vrun(RR_, 0, ROWS-1, pad)
    b.put(RL_, 0, S|E, pad); b.put(RR_, 0, S|W, pad)
    b.put(RL_, ROWS-1, N|E, pad); b.put(RR_, ROWS-1, N|W, pad)
    # mounting holes in the board corners
    for hx in (0, COLS-1):
        for hy in (0, ROWS-1):
            b.put(hx, hy, 0, via, VIA)

    top_cols = list(range(L+2, R-1, 3))
    bot_cols = list(range(L+3, R-2, 3))
    lr_rows  = list(range(T+1, B-1, 2))

    # top stubs: drop from the rail, jog one column, land on the die
    for i, x in enumerate(top_cols):
        j = 1 if i % 2 == 0 else -1
        vrun(x, 0, 1, trace)
        hrun(1, x, x+j, trace)
        vrun(x+j, 1, T-1, trace)
        b.put(x, 1, N | (E if j > 0 else W), trace)
        b.put(x+j, 1, S | (W if j > 0 else E), trace)
        b.put(x, 0, E|S|W, pad)              # ┬ junction on the rail
        b.set(x+j, T, N, rim)                # lands on the die rim
    # bottom stubs: mirror image, jogging the other way
    for i, x in enumerate(bot_cols):
        j = -1 if i % 2 == 0 else 1
        vrun(x, ROWS-2, ROWS-1, trace)
        hrun(ROWS-2, x, x+j, trace)
        vrun(x+j, B, ROWS-2, trace)
        b.put(x, ROWS-2, S | (E if j > 0 else W), trace)
        b.put(x+j, ROWS-2, N | (W if j > 0 else E), trace)
        b.put(x, ROWS-1, N|E|S, pad)         # ┴ junction on the rail
        b.set(x+j, B-1, S, rim)
    # left stubs: run out of the die, jog one row down, join the rail
    xm = (RL_ + L) // 2
    for y in lr_rows:
        yj = y + 1 if y + 1 < B - 1 else y - 1
        hrun(y, xm, L-1, trace)
        vrun(xm, min(y, yj), max(y, yj), trace)
        hrun(yj, RL_, xm, trace)
        b.put(xm, y, E | (S if yj > y else N), trace)
        b.put(xm, yj, W | (N if yj > y else S), trace)
        b.set(RL_, yj, N|E|S, pad)           # ├ junction on the rail
        b.set(L, y, W, rim)
    # right stubs: mirror image, jogging one row up
    xm2 = (R + RR_) // 2
    for y in lr_rows:
        yj = y - 1 if y - 1 > T else y + 1
        hrun(y, R, xm2, trace)
        vrun(xm2, min(y, yj), max(y, yj), trace)
        hrun(yj, xm2, RR_, trace)
        b.put(xm2, y, W | (N if yj < y else S), trace)
        b.put(xm2, yj, E | (S if yj < y else N), trace)
        b.set(RR_, yj, N|S|W, pad)           # ┤ junction on the rail
        b.set(R-1, y, E, rim)

    # ---- die rim: hairline frame, junctions resolve automatically ----
    for x in range(L+1, R-1):
        b.set(x, T, E|W, rim); b.set(x, B-1, E|W, rim)
    for y in range(T+1, B-1):
        b.set(L, y, N|S, rim); b.set(R-1, y, N|S, rim)
    b.set(L, T, S|E, rim); b.set(R-1, T, S|W, rim)
    b.set(L, B-1, N|E, rim); b.set(R-1, B-1, N|W, rim)

    # ---- UltraFusion seam: two fused dies (Apple Ultra) ----
    if dual:
        mx = L + DW // 2
        for y in range(T+1, B-1):
            b.put(mx, y, 0, rim, "\u2502")

    # ---- wordmark: literal characters, centred in the die ----
    texts, block = _lockup_rows(lines)
    for line in texts:
        assert len(line) <= DW - 2, "wordmark %r too wide for die" % line
    top = T + 1 + max(0, (DH - 2 - block) // 2)
    for i, line in enumerate(texts):
        y = top + i * 2
        x = ox + (DW - len(line)) // 2
        for c, ch in enumerate(line):
            if ch != " ": b.set(x + c, y, 0, ink, ch)
    return b, (ox, oy, DW, DH)

def emit_board(board):
    lines = []
    for y in range(board.h):
        s = ""
        for x in range(board.w):
            i = board.col[y][x]; ch_ = board.ch[y][x] or BOX.get(board.mask[y][x], " ")
            s += ("$%d%s" % (i+1, ch_)) if ch_ != " " else " "
        lines.append(s)
    return "\n".join(lines) + "\n"

# ==========================================================================
# previews (Pillow)
# ==========================================================================
KNOWN = set(" \u2588\u2580\u2584\u258c\u2590\u259b\u259c\u2599\u259f\u25cb\u00b7\u25cf"
            "\u2596\u2597\u2598\u259d\u259a\u259e") | set(BOX.values())

def _font(px):
    from PIL import ImageFont
    for cand, idx in (("/System/Library/Fonts/Menlo.ttc", 0),
                      ("/System/Library/Fonts/SFMono-Regular.otf", 0),
                      ("/Library/Fonts/JetBrainsMonoNerdFont-Regular.ttf", 0)):
        try: return ImageFont.truetype(cand, px, index=idx)
        except Exception: pass
    return ImageFont.load_default()

def _draw_char(dr, ch_, box, c, fnt, LW):
    L, T, R, B = box; cw, ch = R-L+1, B-T+1; cx, cy = L+cw//2, T+ch//2
    def line(x0, y0, x1, y1): dr.line([x0, y0, x1, y1], fill=c, width=LW)
    if ch_ == " ": return
    if ch_ not in KNOWN:                       # literal wordmark character
        try:
            bb = dr.textbbox((0, 0), ch_, font=fnt)
            dr.text((L + (cw - (bb[2]-bb[0]))/2 - bb[0], T + (ch - (bb[3]-bb[1]))/2 - bb[1]),
                    ch_, font=fnt, fill=c)
        except Exception:
            dr.text((L+2, T+2), ch_, font=fnt, fill=c)
    elif ch_ == BLOCK: dr.rectangle([L, T, R, B], fill=c)
    elif ch_ == "\u2580": dr.rectangle([L, T, R, T+ch//2-1], fill=c)
    elif ch_ == "\u2584": dr.rectangle([L, T+ch//2, R, B], fill=c)
    elif ch_ == "\u258c": dr.rectangle([L, T, L+cw//2-1, B], fill=c)
    elif ch_ == "\u2590": dr.rectangle([L+cw//2, T, R, B], fill=c)
    elif ch_ in "\u259b\u259c\u2599\u259f\u2596\u2597\u2598\u259d\u259a\u259e":
        m = {v: k for k, v in QUAD.items()}[ch_]
        for qy in range(2):
            for qx in range(2):
                if m & ((1 if qy == 0 else 4) << (0 if qx == 0 else 1)):
                    dr.rectangle([L+qx*cw//2, T+qy*ch//2, L+(qx+1)*cw//2-1, T+(qy+1)*ch//2-1], fill=c)
    elif ch_ in ("\u25cb", "\u00b7", "\u25cf"):
        r = cw//3 if ch_ != "\u00b7" else cw//7
        if ch_ == "\u00b7": dr.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)
        else: dr.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=LW)
    else:
        bits = {v: k for k, v in BOX.items()}.get(ch_, 0)
        if bits & N: line(cx, T, cx, cy)
        if bits & S: line(cx, B, cx, cy)
        if bits & E: line(R, cy, cx, cy)
        if bits & W: line(L, cy, cx, cy)
        if not bits: dr.ellipse([cx-LW, cy-LW, cx+LW, cy+LW], fill=c)

def preview(cells, path=None, palette=None, cw=18, ch=36, bg=(26, 28, 34)):
    from PIL import Image, ImageDraw
    palette = palette or PALETTE
    rows, cols = len(cells), len(cells[0])
    img = Image.new("RGB", (cols*cw, rows*ch), bg)
    dr = ImageDraw.Draw(img)
    LW = max(1, cw//8)
    fnt = _font(int(cw*1.55))
    for y in range(rows):
        for x in range(cols):
            i, glyph = cells[y][x]
            _draw_char(dr, glyph, (x*cw, y*ch, (x+1)*cw-1, (y+1)*ch-1),
                       palette[i], fnt, LW)
    if path: img.save(path)
    return img

def preview_board(board, path=None, palette=None, cw=18, ch=36, bg=(26, 28, 34)):
    from PIL import Image, ImageDraw
    palette = palette or PALETTE
    img = Image.new("RGB", (board.w*cw, board.h*ch), bg)
    dr = ImageDraw.Draw(img)
    LW = max(1, cw//8)
    fnt = _font(int(cw*1.55))
    for y in range(board.h):
        for x in range(board.w):
            i = board.col[y][x]
            ch_ = board.ch[y][x] or BOX.get(board.mask[y][x], " ")
            _draw_char(dr, ch_, (x*cw, y*ch, (x+1)*cw-1, (y+1)*ch-1),
                       palette[i], fnt, LW)
    if path: img.save(path)
    return img

# ==========================================================================
# per-chip fastfetch config
# ==========================================================================
def write_config(palette, path):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "templates", "config.jsonc"), encoding="utf-8") as f:
        tpl = f.read()
    rep = {"@C%d@" % (i+1): "#%02X%02X%02X" % c for i, c in enumerate(palette)}
    rep["@CK@"] = rep["@C6@"]   # keys        = light accent
    rep["@CT@"] = rep["@C8@"]   # title       = silver
    rep["@CO@"] = rep["@C7@"]   # output      = pale accent
    rep["@CS@"] = rep["@C4@"]   # separator   = mid accent
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    with open(path, "w", encoding="utf-8") as f:
        f.write(tpl)

# ==========================================================================
# driver
# ==========================================================================
PCB = {"pcb":   dict(COLS=32, ROWS=16, DW=16, DH=8),
       "pcb32": dict(COLS=36, ROWS=18, DW=20, DH=10)}
PCB_BIG = {"pcb":   dict(COLS=36, ROWS=18, DW=20, DH=10),
           "pcb32": dict(COLS=40, ROWS=20, DW=24, DH=12)}
TAGS = {"pcb": "", "full": "", "pcb32": "_small", "small": "_small"}

def pcb_set(spec):
    return PCB_BIG if spec.get("form") == "big" else PCB

def generate(chip_id, size, power, reach, line1=None, line2=None, mono=False,
             out=None, pre=None, quiet=False, field=None):
    spec = registry.CHIPS[chip_id]
    lines = ((spec["line1"] if line1 is None else line1),
             (spec["line2"] if line2 is None else line2))
    palette = registry.PALETTES[spec["palette"]]
    field = field or registry.FAMILY_FIELDS[spec["family"]]
    pcbs = pcb_set(spec)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = out is None
    out = out or os.path.join(here, "chips", chip_id, "%s%s.txt" % (chip_id, TAGS[size]))
    if size in pcbs:
        board = build_pcb(**pcbs[size], power=power, reach=reach, lines=lines,
                          field=field, dual=spec.get("dual", False))[0]
        text = emit_board(board)
        grid = board.render()
    else:
        cells = build(size, lines=lines, power=power, reach=reach, field=field)
        text = emit(cells, mono)
        grid = cells
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    if not quiet:
        print("wrote %s  (%dx%d)" % (out, len(grid[0]), len(grid)))
    if not mono and pre is not False:
        pre = pre or os.path.join(here, "chips", chip_id, "preview%s.png" % TAGS[size])
        try:
            os.makedirs(os.path.dirname(pre), exist_ok=True)
            if size in pcbs: preview_board(board, pre, palette)
            else: preview(cells, pre, palette)
            if not quiet: print("wrote %s" % pre)
        except ImportError:
            print("Pillow missing: preview skipped", file=sys.stderr)
    if default_out and TAGS[size] == "" and pre is not False:
        cfg = os.path.join(here, "chips", chip_id, "config.jsonc")
        write_config(palette, cfg)
        if not quiet: print("wrote %s" % cfg)
    return grid

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chip", default=None,
                    help="chip id from the registry (default: auto-detect, "
                         "fallback m4pro)")
    ap.add_argument("--all", action="store_true",
                    help="regenerate pcb + small + previews + config for every chip")
    ap.add_argument("--list", action="store_true", help="list registered chips")
    ap.add_argument("--detect", action="store_true",
                    help="print the chip id matching this machine's CPU")
    ap.add_argument("--auto", action="store_true",
                    help="identify this CPU (tier + exact model) and generate a "
                         "model-specific theme")
    ap.add_argument("--brand", default=None,
                    help="override the CPU brand string (for testing --auto)")
    ap.add_argument("--dest", default=None,
                    help="with --auto: install logos + config into this fastfetch "
                         "config directory")
    ap.add_argument("--install-size", choices=["full", "small"], default="full",
                    help="with --auto --dest: which size the config points at")
    ap.add_argument("--field", choices=["glow", "band", "ring"], default=None,
                    help="override the die artwork field")
    ap.add_argument("--size", choices=["pcb", "pcb32"] + list(SIZES), default=None,
                    help="one size only (default with --chip: pcb and pcb32)")
    ap.add_argument("--line1", default=None, help="override wordmark line 1")
    ap.add_argument("--line2", default=None, help="override wordmark line 2")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--mono", action="store_true", help="emit a single-colour logo ($1 only)")
    ap.add_argument("--ascii-preview", action="store_true")
    ap.add_argument("--power", type=float, default=1.55)
    ap.add_argument("--reach", type=float, default=1.16)
    a = ap.parse_args()

    if a.list:
        for cid, spec in registry.CHIPS.items():
            print("%-8s %-18s %s / %s" % (cid, spec["label"], spec["line1"], spec["line2"]))
        return
    if a.detect:
        brand = registry.host_cpu_name()
        print(registry.detect(brand) or "")
        return

    if a.all:
        for cid in registry.CHIPS:
            generate(cid, "pcb", 2.0, 1.45, mono=a.mono)
            generate(cid, "pcb32", 2.0, 1.45, mono=a.mono)
        return

    if a.auto:
        info = registry.identify(a.brand)
        if not info:
            sys.exit("no known chip in %r" % (a.brand or registry.host_cpu_name()))
        chip = info["chip_id"]
        spec = registry.CHIPS[chip]
        l1, l2 = registry.wordmark(info)
        palette = registry.PALETTES[spec["palette"]]
        field = a.field or registry.FAMILY_FIELDS[spec["family"]]
        print("identified: %s -> %s (%s)" % (a.brand or registry.host_cpu_name(),
                                             chip, info["model"] or spec["label"]),
              file=sys.stderr)
        if not a.dest:                       # pipe mode: full-size logo to stdout
            board = build_pcb(**pcb_set(spec)["pcb"], lines=(l1, l2), field=field,
                              dual=spec.get("dual", False))[0]
            sys.stdout.write(emit_board(board))
            return
        os.makedirs(a.dest, exist_ok=True)
        for tag, size in (("", "pcb"), ("_small", "pcb32")):
            generate(chip, size, 2.0, 1.45, l1, l2,
                     out=os.path.join(a.dest, "%s%s.txt" % (chip, tag)),
                     pre=False, quiet=True, field=field)
        logo = os.path.join(a.dest, "%s%s.txt" % (
            chip, "_small" if a.install_size == "small" else ""))
        cfg = os.path.join(a.dest, "config.jsonc")
        write_config(palette, cfg)
        with open(cfg, encoding="utf-8") as f:
            txt = f.read()
        with open(cfg, "w", encoding="utf-8") as f:
            f.write(txt.replace("@LOGO@", json_path(logo)))
        print("installed:")
        print("  %s  (logo -> %s)" % (cfg, json_path(logo)))
        print("  %s" % os.path.join(a.dest, chip + ".txt"))
        print("  %s" % os.path.join(a.dest, chip + "_small.txt"))
        print("run:  fastfetch")
        return

    chip = a.chip or registry.detect() or "m4pro"
    if chip not in registry.CHIPS:
        sys.exit("unknown chip %r (try --list)" % chip)
    spec0 = registry.CHIPS[chip]
    sizes = [a.size] if a.size else (["pcb"] if a.output else ["pcb", "pcb32"])
    for size in sizes:
        grid = generate(chip, size,
                        2.0 if size in pcb_set(spec0) else a.power,
                        1.45 if size in pcb_set(spec0) else a.reach,
                        a.line1, a.line2, a.mono, a.output, a.preview,
                        field=a.field)
    if a.ascii_preview:
        ramp = " .:-=+*#%@"
        for row in grid:
            print("".join(ramp[i] if gl == BLOCK else gl for i, gl in row))

if __name__ == "__main__":
    main()
