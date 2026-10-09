#!/usr/bin/env python3
"""Generate sdcard/MODELS/model3.yml for the TX15 combat robot from a clean
template + an editable CONFIG block. This is the source of truth for the model's
mixer/outputs/logic — edit CONFIG, run `python3 build_model.py`, test in the
simulator, then `./deploy.sh`.

Base template: backups/model3.yml.orig (the untouched "New Multirotor"), whose
inputs are I0=Rud, I1=Ele, I2=Thr, I3=Ail (Mode-2 radio: Thr=left-V, Ele=right-V,
Ail=right-H, Rud=left-H).
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "backups", "model3.yml.orig")
OUT  = os.path.join(HERE, "sdcard", "MODELS", "model3.yml")

# ============================== EDITABLE CONFIG ==============================
# This encodes the Sep-6 baseline design. We iterate from here in the simulator.
NAME = "ANT"

# Each mix line: (destCh 0-based, srcRaw, weight, offset, mltpx, swtch, name)
#   mltpx: "ADD" or "REPL".  swtch: "NONE","SE2","!SE2","SF2", a logical "L1".. etc.
MIXES = [
    (0, "I1",  -100, 0, "ADD",  "NONE", "Drive"),  # CH1 fwd/back = Ele (right-V), reversed
    (2, "I3",   100, 0, "ADD",  "NONE", "Steer"),  # CH3 steering = Ail (right-H)
    (1, "I2",   100, 0, "ADD",  "NONE", "Weapon"), # CH2 weapon base = Thr (left-V)
    (1, "MAX", -100, 0, "REPL", "!SE2", "Safe"),   # CH2 forced -100 when SE up (disarmed)
]

# Special functions: (swtch, func, def)
CUSTOM_FN = [
    ("ON", "RGB_LED", "combat,1,On"),   # gimbal LED rings (combat.lua)
]
# ============================================================================

def mix(d, src, w, off, m, sw, nm):
    return [" -", "   destCh: %d" % d, '   srcRaw: "%s"' % src, "   carryTrim: 0",
            "   mixWarn: 0", "   mltpx: %s" % m, "   delayPrec: 0", "   speedPrec: 0",
            "   flightModes: 000000000", "   weight: %d" % w, "   offset: %d" % off,
            '   swtch: "%s"' % sw, "   delayUp: 0", "   delayDown: 0", "   speedUp: 0",
            "   speedDown: 0", '   name: "%s"' % nm]

def cf(i, sw, fn, df):
    return ["   %d:" % i, '      swtch: "%s"' % sw, "      func: %s" % fn, '      def: "%s"' % df]

def main():
    lines = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    def find(pfx):
        for i, l in enumerate(lines):
            if l.startswith(pfx): return i
        return -1
    # name
    txt = "\n".join(lines).replace('name: "New Multirotor"', 'name: "%s"' % NAME, 1)
    lines = txt.split("\n")
    # mixData
    md = ["mixData: "]
    for m in MIXES: md += mix(*m)
    lines[find("mixData:"):find("expoData:")] = md
    # customFn: replace the block if present, else insert it before flightModeData
    cfb = ["customFn: "]
    for i, c in enumerate(CUSTOM_FN): cfb += cf(i, *c)
    cs = find("customFn:")
    if cs != -1:
        # end of the existing customFn block = next top-level key
        end = next((j for j in range(cs + 1, len(lines)) if lines[j] and lines[j][0].isalpha()), len(lines))
        lines[cs:end] = cfb
    else:
        anchor = find("flightModeData:")
        if anchor == -1: anchor = find("moduleData:")
        lines[anchor:anchor] = cfb
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("wrote", OUT, "(%d lines)" % len(lines))

if __name__ == "__main__":
    main()
