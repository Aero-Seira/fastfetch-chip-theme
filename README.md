# fastfetch-chip-theme

A collection of geometry-generated fastfetch chip themes.

Currently included:

| Chip | Files | Preview |
|---|---|---|
| `m4pro` | `chips/m4pro/m4pro.txt`, `chips/m4pro/m4pro_small.txt` | `chips/m4pro/preview.png` |

## What this repository provides

- Chip logo themes rendered from geometry (not traced bitmaps).
- fastfetch-compatible `$1..$9` color placeholders for easy recoloring.
- Shared config template + install/uninstall scripts.
- A layout that can grow by adding new chip folders under `chips/`.

## Install and select a chip theme

Install the default chip (`m4pro`) and default size (`full`):

```sh
bin/install.sh
```

Install a specific chip and size:

```sh
bin/install.sh m4pro full
bin/install.sh m4pro small
```

Backward-compatible shorthand is still supported:

```sh
bin/install.sh small
```

This writes `~/.config/fastfetch/config.jsonc` and the selected logo file(s), then:

```sh
fastfetch
```

Uninstall managed files with:

```sh
bin/uninstall.sh
```

## Try without installing

```sh
fastfetch -c templates/config.jsonc --logo-type file --logo chips/m4pro/m4pro.txt
```

## Generate and customize chip themes

Regenerate theme text + preview for a chip folder:

```sh
python3 tools/gen_logo.py --chip m4pro --size pcb
python3 tools/gen_logo.py --chip m4pro --size pcb32
```

Common customizations:

```sh
python3 tools/gen_logo.py --chip m4pro --size pcb --lockup caps
python3 tools/gen_logo.py --chip m4pro --size pcb --power 2.4 --reach 1.6
python3 tools/gen_logo.py --chip m4pro --size full --mono
```

The generator remains geometry-based and self-contained. Python 3 is required;
`Pillow` is optional for preview PNG output.

## Repository layout

```text
chips/
  m4pro/                  chip-specific logo outputs and previews
templates/
  config.jsonc            shared fastfetch config template (@LOGO@ placeholder)
tools/
  gen_logo.py             geometry generator
bin/
  install.sh              install selected chip theme
  uninstall.sh            remove managed fastfetch theme files
```
