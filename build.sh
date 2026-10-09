#!/usr/bin/env bash
# Regenerate the SD payload from source and package it as an SD-overlay zip.
# Usable locally and in CI. Needs: python3, ffmpeg, zip (and luac for the Lua check).
#
#   ./build.sh            # build + validate + package into dist/
set -euo pipefail
cd "$(dirname "$0")"

echo ">> sounds";     python3 import_sounds.py
echo ">> model";      python3 build_model.py
echo ">> soundboard"; python3 build_soundboard.py
echo ">> validate";   python3 validate.py

VER="$(git describe --tags --always --dirty 2>/dev/null || date +%Y%m%d)"
ZIP="dist/tx15-ant-sdcard-${VER}.zip"
rm -rf dist && mkdir -p dist

# WRITING.txt rides along inside the zip so the payload is self-explanatory
cat > sdcard/WRITING.txt <<TXT
TX15 combat model "ANT" — SD overlay (${VER})

This is an OVERLAY, not a full card. Copy these folders onto an EdgeTX SD card
that already has the 2.12.x SD contents (from EdgeTX Buddy):

  MODELS/model3.yml           -> the model
  SCRIPTS/RGBLED/combat.lua   -> gimbal LED script
  SOUNDS/en/*.wav             -> F-18/RWR event sounds

Eject the card cleanly before unplugging. See the repo README for the design.
TXT

( cd sdcard && zip -q -r -X "../${ZIP}" MODELS SCRIPTS SOUNDS WRITING.txt )
rm -f sdcard/WRITING.txt
echo ">> packaged ${ZIP} ($(du -h "${ZIP}" | cut -f1))"
