#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"

# Git Bash / MSYS / Cygwin: uninstall what bin/install.ps1 installed instead
case "$(uname -s 2>/dev/null)${MSYSTEM:-}" in   # set by Git Bash / MSYS / Cygwin
  MINGW*|MSYS*|CYGWIN*)
    if command -v powershell.exe >/dev/null 2>&1 \
       && command -v cygpath >/dev/null 2>&1 \
       && [ -f "$ROOT/bin/uninstall.ps1" ]; then
      exec powershell.exe -NoProfile -ExecutionPolicy Bypass \
        -File "$(cygpath -w "$ROOT/bin/uninstall.ps1")"
    fi
    ;;
esac
rm -f "$DEST/config.jsonc"

for theme in "$ROOT"/chips/*/*.txt; do
    [ -f "$theme" ] || continue
    rm -f "$DEST/$(basename "$theme")"
done

echo "removed managed chip themes from $DEST"
