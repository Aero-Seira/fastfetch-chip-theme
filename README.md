# fastfetch-m4pro-theme

An Apple-Silicon **M4 Pro** badge, redrawn as a fastfetch logo.

![preview](assets/preview.png)

## What it is

The official M4 Pro artwork is a square chip package: a light hairline substrate
edge, a near-black die with a blue glow rising out of the bottom-left corner, and
a silver lockup (`apple` + `M4`, with `PRO` centred underneath).

This theme reproduces that as a 38 x 19 cell block drawing:

| layer | cells | colour |
|---|---|---|
| package rim | `▛▀▜` `▌` `▐` `▙▄▟` hairlines | `$6` sky `#60A8EC` |
| die body + glow | `█` full blocks, radial ramp | `$1`-`$5` navy → bright blue |
| `apple M4 PRO` | `█` full blocks | `$8` silver `#C8DEEE` |

* **Geometry, not a trace.** Every glyph (apple lobes / bite / leaf, `M`, `4`,
  `P`, `R`, `O`) is rasterised from circles, ellipses, rectangles and stroked
  segments, then sampled into terminal cells where **1 column = 1 unit wide and
  1 row = 2 units tall** — so a 38 x 19 grid renders as a true square.
* **Re-tintable.** The logo file only contains fastfetch's `$1`…`$9` colour
  placeholders, so the whole badge is recoloured from `logo.color` in the config
  — no need to edit the art.
* **Background independent.** The die is painted with solid blocks, so it reads
  correctly on both dark and light terminals.

## Install

```sh
bin/install.sh          # 38x19 logo (default)
bin/install.sh small    # 34x17 logo for narrow terminals
```

That copies the logos to `~/.config/fastfetch/` and writes
`~/.config/fastfetch/config.jsonc`, which fastfetch loads automatically:

```sh
fastfetch
```

Uninstall with `bin/uninstall.sh`.

Requirements: a terminal with truecolour support and Unicode block-drawing
glyphs (U+2580-U+259F — Menlo, JetBrainsMono Nerd Font, SF Mono, etc.).

## Try it without installing

```sh
fastfetch -c themes/config.jsonc --logo-type file --logo themes/m4pro.txt
```

## Regenerate / customise

```sh
python3 tools/gen_logo.py --size full          # -> themes/m4pro.txt + assets/preview.png
python3 tools/gen_logo.py --size small         # -> themes/m4pro_small.txt
python3 tools/gen_logo.py --power 1.8 --reach 1.05   # tighter glow
python3 tools/gen_logo.py --mono               # single-colour logo ($1 only)
```

Only Python 3 is required; `Pillow` is used for the PNG preview and is optional.
The generator is self-contained — the reference artwork is *not* stored in this
repository (it is Apple's copyrighted image), the logo is drawn from geometry.

## Files

```
themes/m4pro.txt          38x19 logo, $1..$9 colour placeholders
themes/m4pro_small.txt    34x17 variant
themes/config.jsonc       fastfetch config (logo palette + key/title colours + structure)
tools/gen_logo.py         the generator
bin/install.sh            install / bin/uninstall.sh remove
assets/preview*.png       rendered previews
```

The module list in `config.jsonc` is 19 lines so that the full logo is printed
without being clipped (`logo.printRemaining` is also enabled as a fallback).
