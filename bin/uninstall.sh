#!/bin/sh
set -e
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
rm -f "$DEST/config.jsonc" "$DEST/m4pro.txt" "$DEST/m4pro_small.txt"
echo "removed $DEST/{config.jsonc,m4pro.txt,m4pro_small.txt}"
