# fastfetch-chip-theme

Geometry-generated fastfetch chip themes that identify your exact CPU and
redraw each vendor's badge: the wordmark carries your real model number
(`CORE i7 / 13700K`, `RYZEN 9 / 7950X`, `● M 4 / P R O`), the die artwork
follows the vendor's marketing design, and wordmarks are literal characters
(render in any monospace font).

| | | |
|---|---|---|
| ![Apple M4 Pro](chips/m4pro/preview.png) | ![Intel Core i7](chips/i7/preview.png) | ![AMD Ryzen 9](chips/ryzen9/preview.png) |
| ![Apple M5 Ultra](chips/m5ultra/preview.png) | ![Intel Core Ultra 7](chips/ultra7/preview.png) | ![AMD EPYC](chips/epyc/preview.png) |

## How it works

```text
CPU brand string           (sysctl machdep.cpu.brand_string / /proc/cpuinfo)
      |  tools/chips.py: identify()
      v
{ family, tier, exact model }            e.g. intel / i7 / "13700K"
      |  registry: CHIPS
      v
wordmark (literal text)  +  palette (9 colours)  +  die field + form factor
      |  tools/gen_logo.py
      v
<chip>.txt  with fastfetch $1..$9 colour placeholders
config.jsonc  with the brand palette baked in (only @LOGO@ left to fill)
```

- **Wordmarks** are literal characters centred in the die — no fake pixel
  font, so they render identically in every monospace terminal font.
- **Die artwork** is per vendor (`glow` / `band` / `ring`, see below).
- **Palettes** follow the vendors' badge designs. Logos only contain `$1..$9`
  placeholders, so the whole theme can be re-tinted from `logo.color` in the
  fastfetch config.

## Per-vendor artwork

| Vendor | Die artwork | Palette |
|---|---|---|
| Apple | radial glow from the bottom-left corner (keynote die renders) | per tier, see below |
| Intel | tilted horizontal swoosh band (Core badge) | per tier blue |
| AMD | centred ring (Ryzen mark) | per tier orange-red |

## Chips

All 34 chips are generated from the registry in `tools/chips.py` — adding a
new chip is a registry entry (wordmark + palette + CPU match patterns), not
new drawing code.

| Vendor | Chips | Palette |
|---|---|---|
| Apple | `m1` .. `m6` | graphite silver |
| Apple Pro | `m1pro` .. `m5pro` | blue |
| Apple Max | `m1max` .. `m5max` | violet |
| Apple Ultra | `m1ultra` `m2ultra` `m3ultra` `m5ultra` | copper |
| Intel Core | `i3` `i5` `i7` `i9` | sky / Intel blue / indigo / carbon |
| Intel Core Ultra | `ultra5` `ultra7` `ultra9` | blue-violet gradient |
| Intel Xeon | `xeon` | workstation slate |
| AMD Ryzen | `ryzen3` `ryzen5` `ryzen7` `ryzen9` | gold / amber / orange / red |
| AMD Threadripper | `threadripper` | rust |
| AMD EPYC | `epyc` | datacenter teal |

Tier colours follow the vendors' badge designs (Intel blue `#0068B5` family,
Ryzen orange-to-red, Apple's graphite/space-black keynote renders).

### Large packages

Large packages get a physically bigger die (20x10 full / 24x12 small instead
of 16x8 / 20x10): `epyc`, `threadripper`, `xeon` and every Apple Ultra.
Apple Ultra additionally shows the UltraFusion seam between the two fused
dies (`dual` flag in the registry).

## Install

Identify the host CPU (tier + exact model) and generate a personalised theme
straight into the fastfetch config dir (default size `full`):

```sh
bin/install.sh        # needs python3; falls back to pre-generated themes
```

The auto path detects the CPU via `sysctl` (macOS) or `/proc/cpuinfo`
(Linux), prints the model number into the wordmark and picks the matching
palette, die artwork and form factor. Without python3 (or for unknown CPUs)
it falls back to shell-based detection and the pre-generated themes.

Install a specific chip and size:

```sh
bin/install.sh i7 full
bin/install.sh ryzen9 small
```

Backward-compatible shorthand is still supported:

```sh
bin/install.sh small
```

This writes `~/.config/fastfetch/config.jsonc` (with the chip's brand palette
baked in) and the selected logo file(s), then:

```sh
fastfetch
```

Uninstall managed files (config + every installed chip logo) with:

```sh
bin/uninstall.sh
```

## Try without installing

```sh
sed "s|@LOGO@|$PWD/chips/i7/i7.txt|" chips/i7/config.jsonc > /tmp/ff.jsonc
fastfetch -c /tmp/ff.jsonc
```

## Generate and customize chip themes

```sh
python3 tools/gen_logo.py --detect            # chip id for this machine's CPU
python3 tools/gen_logo.py --auto              # model-specific logo to stdout
python3 tools/gen_logo.py --auto --dest ~/.config/fastfetch
python3 tools/gen_logo.py --auto --brand "AMD Ryzen 7 7800X3D 8-Core Processor"
python3 tools/gen_logo.py --list              # all registered chips
python3 tools/gen_logo.py --all               # regenerate every chip
python3 tools/gen_logo.py --chip m4pro        # pcb + small + previews + config
python3 tools/gen_logo.py --chip i7 --size pcb --line1 "intel" --line2 "CORE i7"
python3 tools/gen_logo.py --chip m4 --size full --mono
python3 tools/gen_logo.py --chip ryzen9 --field glow   # override die artwork
```

Each chip folder gets `<chip>.txt`, `<chip>_small.txt`, both previews and a
ready-to-use `config.jsonc` (only `@LOGO@` is left for `bin/install.sh`).
The generator remains geometry-based and self-contained. Python 3 is required;
`Pillow` is optional for preview PNG output.

### CLI reference

| Flag | Effect |
|---|---|
| `--chip ID` | pick a registered chip (default: auto-detect, fallback `m4pro`) |
| `--all` | regenerate logos + previews + configs for every chip |
| `--auto` | identify the host CPU and print a model-specific logo |
| `--auto --dest DIR` | same, but install logos + config into DIR |
| `--brand "STR"` | override the CPU brand string (for testing `--auto`) |
| `--install-size full\|small` | which size `--auto --dest` points the config at |
| `--size pcb\|pcb32\|full\|small` | render one size only |
| `--list` / `--detect` | list registry / print this machine's chip id |
| `--line1`, `--line2` | override the wordmark text |
| `--field glow\|band\|ring` | override the die artwork |
| `--mono` | single-colour logo (`$1` only) |
| `--power`, `--reach` | tune the die field falloff / extent |
| `-o`, `--preview` | custom output / preview paths |
| `--ascii-preview` | print the palette-index grid to the terminal |

### Sizes

| `--size` | Output file | Standard die | Large-package die |
|---|---|---|---|
| `pcb` (default) | `<chip>.txt` | 16x8 die, 32x16 board | 20x10 die, 36x18 board |
| `pcb32` | `<chip>_small.txt` | 20x10 die, 36x18 board | 24x12 die, 40x20 board |
| `full` / `small` | same filenames | bare-die style (no PCB), 36x18 / 32x16 | — |

Wordmark lines must fit the die interior: max 14 characters on a standard
die, 18 on a large one.

## Palettes

Every palette has nine slots: `$1..$6` die background gradient (darkest to
brightest accent), `$7` pale accent (package rim), `$8` silver (lettering),
`$9` bright silver (highlight). `templates/config.jsonc` maps them to
`logo.color` and derives the `display` colours from them (keys = `$6`,
title = `$8`, output = `$7`, separator = `$4`).

## Adding a chip

1. Add an entry to `CHIPS` in `tools/chips.py` (wordmark lines, palette name,
   CPU-detection regexes). Reuse a palette from `PALETTES` or add a new
   9-colour one. Optional flags: `form: "big"` (large package) and
   `dual: True` (dual-die seam).
2. Map its `family` to a die field in `FAMILY_FIELDS` (`glow` / `band` /
   `ring`), or add a new field function in `tools/gen_logo.py`.
3. Extend `identify()`/`wordmark()` if the model number needs new parsing,
   and add the fallback glob pattern to `detect_chip()` in `bin/install.sh`.
4. Run `python3 tools/gen_logo.py --all` and check the previews.

## Repository layout

```text
chips/
  <chip>/               per-chip logos, previews and config.jsonc
templates/
  config.jsonc          fastfetch config template (@LOGO@ + @C1@..@C9@ placeholders)
tools/
  chips.py              chip registry: wordmarks, palettes, CPU identification
  gen_logo.py           geometry generator (fields, PCB routing, previews)
bin/
  install.sh            auto-detect + install selected chip theme
  uninstall.sh          remove managed fastfetch theme files
```
