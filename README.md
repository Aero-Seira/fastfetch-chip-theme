# fastfetch-chip-theme

Geometry-generated fastfetch chip themes that identify your exact CPU and
redraw each vendor's badge: the wordmark carries your real model number
(`CORE i7 / 13700K`, `RYZEN 9 / 7950X`, `● M 4 / P R O`), the die artwork
follows the vendor's marketing design, and wordmarks are literal characters
(render in any monospace font).

## Per-vendor artwork

| Vendor | Die artwork | Palette |
|---|---|---|
| Apple | radial glow from the bottom-left corner (keynote die renders) | per tier, see below |
| Intel | tilted horizontal swoosh band (Core badge) | per tier blue |
| AMD | centred ring (Ryzen mark) | per tier orange-red |

## Chips

All 22 chips are generated from the registry in `tools/chips.py` — adding a
new chip is a registry entry (wordmark + palette + CPU match patterns), not
new drawing code.

| Vendor | Chips | Palette |
|---|---|---|
| Apple | `m1` `m2` `m3` `m4` | graphite silver |
| Apple Pro | `m1pro` `m2pro` `m3pro` `m4pro` | blue |
| Apple Max | `m1max` `m2max` `m3max` `m4max` | violet |
| Apple Ultra | `m1ultra` `m2ultra` `m3ultra` | copper |
| Intel | `i3` `i5` `i7` `i9` | sky / Intel blue / indigo / carbon |
| AMD | `ryzen5` `ryzen7` `ryzen9` | amber / orange / red |

Tier colours follow the vendors' badge designs (Intel blue `#0068B5` family,
Ryzen orange-to-red, Apple's graphite/space-black keynote renders).

## Install

Identify the host CPU (tier + exact model) and generate a personalised theme
straight into the fastfetch config dir (default size `full`):

```sh
bin/install.sh        # needs python3; falls back to pre-generated themes
```

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

Uninstall managed files with:

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

## Adding a chip

1. Add an entry to `CHIPS` in `tools/chips.py` (wordmark lines, palette name,
   CPU-detection regexes). Reuse a palette from `PALETTES` or add a new
   9-colour one (`$1..$6` die gradient, `$7` rim, `$8` lettering, `$9` highlight).
2. Map its `family` to a die field in `FAMILY_FIELDS` (`glow` / `band` /
   `ring`), or add a new field function in `tools/gen_logo.py`.
3. Extend `identify()`/`wordmark()` if the model number needs new parsing.
4. Run `python3 tools/gen_logo.py --all`.

## Repository layout

```text
chips/
  <chip>/               per-chip logos, previews and config.jsonc
templates/
  config.jsonc          fastfetch config template (@LOGO@ + @C1@..@C9@ placeholders)
tools/
  chips.py              chip registry: wordmarks, palettes, CPU detection
  gen_logo.py           geometry generator
bin/
  install.sh            auto-detect + install selected chip theme
  uninstall.sh          remove managed fastfetch theme files
```
