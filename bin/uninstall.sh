#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
rm -f "$DEST/config.jsonc"

for theme in "$ROOT"/chips/*/*.txt; do
    [ -f "$theme" ] || continue
    rm -f "$DEST/$(basename "$theme")"
done

echo "removed managed chip themes from $DEST"
