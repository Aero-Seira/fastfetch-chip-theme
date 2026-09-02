#!/bin/sh
# Install a chip fastfetch theme into the user config directory.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
CHIP="${1:-m4pro}"
SIZE="${2:-full}"

# Backward compatibility: bin/install.sh small
case "$CHIP" in
  full|small)
    SIZE="$CHIP"
    CHIP="m4pro"
    ;;
esac

case "$SIZE" in
  full|small) ;;
  *)
    echo "usage: bin/install.sh [chip] [full|small]"
    exit 1
    ;;
esac

THEME_DIR="$ROOT/chips/$CHIP"
FULL_SRC="$THEME_DIR/$CHIP.txt"
SMALL_SRC="$THEME_DIR/${CHIP}_small.txt"
FULL_DEST="$DEST/$CHIP.txt"
SMALL_DEST="$DEST/${CHIP}_small.txt"
LOGO="$FULL_DEST"

[ -f "$FULL_SRC" ] || { echo "missing theme: $FULL_SRC"; exit 1; }
[ "$SIZE" = "small" ] && [ ! -f "$SMALL_SRC" ] && { echo "missing small theme: $SMALL_SRC"; exit 1; }
[ "$SIZE" = "small" ] && LOGO="$SMALL_DEST"

mkdir -p "$DEST"
cp "$FULL_SRC" "$FULL_DEST"
[ -f "$SMALL_SRC" ] && cp "$SMALL_SRC" "$SMALL_DEST"
sed "s|@LOGO@|$LOGO|" "$ROOT/templates/config.jsonc" > "$DEST/config.jsonc"
echo "installed:"
echo "  $DEST/config.jsonc        (logo -> $LOGO)"
echo "  $FULL_DEST"
[ -f "$SMALL_SRC" ] && echo "  $SMALL_DEST"
echo "run:  fastfetch"
