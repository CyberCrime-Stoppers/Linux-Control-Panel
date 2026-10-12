#!/bin/bash
# ShowFullPathInTitlebar.sh — toggle Dolphin's full-path-in-titlebar setting
# Usage: ./ShowFullPathInTitlebar.sh [on|off|status]   (no arg = toggle)

CFG="$HOME/.config/dolphinrc"
GROUP="General"
KEY="ShowFullPathInTitlebar"

if command -v kreadconfig6 >/dev/null 2>&1; then
    KR="kreadconfig6"; KW="kwriteconfig6"
elif command -v kreadconfig5 >/dev/null 2>&1; then
    KR="kreadconfig5"; KW="kwriteconfig5"
else
    echo "Error: kreadconfig5/6 not found"; exit 1
fi

current=$("$KR" --file "$CFG" --group "$GROUP" --key "$KEY")

case "$1" in
    on)      value="false" ;;
    off)     value="true" ;;
    status)  echo "$KEY: $current"; exit 0 ;;
    "")      [[ "$current" == "true" ]] && value="false" || value="true" ;;
    *)       echo "Usage: $0 [on|off|status]"; exit 1 ;;
esac

"$KW" --file "$CFG" --group "$GROUP" --key "$KEY" "$value"
echo "$KEY: $current -> $value (restart Dolphin to apply)"
