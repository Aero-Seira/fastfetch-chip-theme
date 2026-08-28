#!/bin/sh
# Install the M4 Pro fastfetch theme into the user config directory.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
SIZE="${1:-full}"
[ "$SIZE" = "small" ] && LOGO="$DEST/m4pro_small.txt" || LOGO="$DEST/m4pro.txt"

mkdir -p "$DEST"
cp "$ROOT/themes/m4pro.txt" "$ROOT/themes/m4pro_small.txt" "$DEST/"
sed "s|@LOGO@|$LOGO|" "$ROOT/themes/config.jsonc" > "$DEST/config.jsonc"
echo "installed:"
echo "  $DEST/config.jsonc        (logo -> $LOGO)"
echo "  $DEST/m4pro.txt  $DEST/m4pro_small.txt"
echo "run:  fastfetch"
