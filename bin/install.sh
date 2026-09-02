#!/bin/sh
# Install a chip fastfetch theme into the user config directory.
# With no arguments the chip is auto-detected from the host CPU.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${XDG_CONFIG_HOME:-$HOME/.config}/fastfetch"
CHIP="${1:-}"
SIZE="${2:-full}"

# Backward compatibility: bin/install.sh small
case "$CHIP" in
  full|small)
    SIZE="$CHIP"
    CHIP=""
    ;;
esac

case "$SIZE" in
  full|small) ;;
  *)
    echo "usage: bin/install.sh [chip] [full|small]"
    echo "available chips:"
    ls "$ROOT/chips" | sed 's/^/  /'
    exit 1
    ;;
esac

# --- auto-detect the chip from the CPU brand string -----------------------
detect_chip() {
  brand=""
  case "$(uname -s)" in
    Darwin) brand="$(sysctl -n machdep.cpu.brand_string 2>/dev/null)" ;;
    Linux)  brand="$(sed -n 's/^model name[^:]*: *//p' /proc/cpuinfo 2>/dev/null | head -1)" ;;
  esac
  norm="$(printf '%s' "$brand" | tr 'A-Z' 'a-z' | tr -d '()' | tr -s ' ')"
  case "$norm" in
    # Apple silicon: specific tiers first ("apple m4" also matches "apple m4 pro")
    *"apple m1 ultra"*) echo m1ultra ;;  *"apple m2 ultra"*) echo m2ultra ;;
    *"apple m3 ultra"*) echo m3ultra ;;
    *"apple m1 max"*)   echo m1max   ;;  *"apple m2 max"*)   echo m2max   ;;
    *"apple m3 max"*)   echo m3max   ;;  *"apple m4 max"*)   echo m4max   ;;
    *"apple m1 pro"*)   echo m1pro   ;;  *"apple m2 pro"*)   echo m2pro   ;;
    *"apple m3 pro"*)   echo m3pro   ;;  *"apple m4 pro"*)   echo m4pro   ;;
    *"apple m1"*)       echo m1      ;;  *"apple m2"*)       echo m2      ;;
    *"apple m3"*)       echo m3      ;;  *"apple m4"*)       echo m4      ;;
    # Intel Core i-series ("13th Gen Intel Core i7-13700K")
    *"core i9"*|*i9-?*) echo i9 ;;
    *"core i7"*|*i7-?*) echo i7 ;;
    *"core i5"*|*i5-?*) echo i5 ;;
    *"core i3"*|*i3-?*) echo i3 ;;
    # AMD Ryzen
    *"ryzen 9"*|*ryzen9*) echo ryzen9 ;;
    *"ryzen 7"*|*ryzen7*) echo ryzen7 ;;
    *"ryzen 5"*|*ryzen5*) echo ryzen5 ;;
    *) echo "" ;;
  esac
}

# Preferred path: identify tier + exact model and generate a model-specific
# theme straight into the config dir (needs python3).
if [ -z "$CHIP" ] && command -v python3 >/dev/null 2>&1; then
  mkdir -p "$DEST"
  if python3 "$ROOT/tools/gen_logo.py" --auto --dest "$DEST" --install-size "$SIZE" 2>&1; then
    exit 0
  fi
  echo "falling back to pre-generated themes"
fi

if [ -z "$CHIP" ]; then
  CHIP="$(detect_chip)"
  if [ -z "$CHIP" ]; then
    echo "could not detect this CPU; falling back to m4pro"
    CHIP="m4pro"
  else
    echo "detected chip: $CHIP"
  fi
fi

THEME_DIR="$ROOT/chips/$CHIP"
FULL_SRC="$THEME_DIR/$CHIP.txt"
SMALL_SRC="$THEME_DIR/${CHIP}_small.txt"
FULL_DEST="$DEST/$CHIP.txt"
SMALL_DEST="$DEST/${CHIP}_small.txt"
LOGO="$FULL_DEST"

[ -f "$FULL_SRC" ] || {
  echo "unknown chip: $CHIP"
  echo "available chips:"
  ls "$ROOT/chips" | sed 's/^/  /'
  exit 1
}
[ "$SIZE" = "small" ] && [ ! -f "$SMALL_SRC" ] && { echo "missing small theme: $SMALL_SRC"; exit 1; }
[ "$SIZE" = "small" ] && LOGO="$SMALL_DEST"

# per-chip config (brand palette baked in) falls back to the shared template
CONFIG_SRC="$THEME_DIR/config.jsonc"
[ -f "$CONFIG_SRC" ] || CONFIG_SRC="$ROOT/templates/config.jsonc"

mkdir -p "$DEST"
cp "$FULL_SRC" "$FULL_DEST"
[ -f "$SMALL_SRC" ] && cp "$SMALL_SRC" "$SMALL_DEST"
sed "s|@LOGO@|$LOGO|" "$CONFIG_SRC" > "$DEST/config.jsonc"
echo "installed:"
echo "  $DEST/config.jsonc        (logo -> $LOGO)"
echo "  $FULL_DEST"
[ -f "$SMALL_SRC" ] && echo "  $SMALL_DEST"
echo "run:  fastfetch"
