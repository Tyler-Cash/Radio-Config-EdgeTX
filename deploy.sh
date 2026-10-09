#!/usr/bin/env bash
# Deploy the tracked config (sdcard/) onto a mounted EdgeTX SD card, or into the
# simulator's SD folder. Source of truth is this repo; never hand-edit the card.
#
#   ./deploy.sh            # auto-detect a mounted EdgeTX card under /Volumes
#   ./deploy.sh /path/sd   # deploy to an explicit SD root (e.g. the sim's sdcard)
#
# It copies files INTO the target without deleting anything else (models/scripts
# you keep on the card are left alone). Run build_model.py first.
set -euo pipefail
cd "$(dirname "$0")"

SRC="sdcard"
[ -d "$SRC" ] || { echo "No $SRC/ — run: python3 build_model.py"; exit 1; }

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  # find a mounted EdgeTX card (has edgetx.sdcard.version at its root)
  for v in /Volumes/*/; do
    if [ -f "${v}edgetx.sdcard.version" ]; then TARGET="$v"; break; fi
  done
  [ -n "$TARGET" ] || { echo "No mounted EdgeTX card found under /Volumes (put the radio in USB-storage mode, or pass an SD path)."; exit 1; }
fi
[ -d "$TARGET" ] || { echo "Target not a directory: $TARGET"; exit 1; }

echo "Deploying $SRC/ -> $TARGET"
# copy tree, preserving structure; -n would skip existing, we want to overwrite our files
( cd "$SRC" && find . -type f -print0 ) | while IFS= read -r -d '' f; do
  dest="$TARGET/${f#./}"
  mkdir -p "$(dirname "$dest")"
  cp "$SRC/$f" "$dest"
  echo "  $f"
done
sync
echo "Done. Eject the card cleanly before unplugging."
