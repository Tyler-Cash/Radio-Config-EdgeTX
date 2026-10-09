#!/usr/bin/env python3
"""Validate the generated SD payload before packaging.
Checks the model YAML structure and that every event WAV is EdgeTX-compatible
(mono / 16-bit / 32 kHz). Runs luac on the Lua scripts if a luac is available.
Exit non-zero on any failure. Run: python3 validate.py
"""
import io, os, sys, glob, wave, shutil, subprocess

HERE  = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "sdcard", "MODELS", "model3.yml")
SND   = os.path.join(HERE, "sdcard", "SOUNDS", "en")
LUA   = glob.glob(os.path.join(HERE, "sdcard", "SCRIPTS", "**", "*.lua"), recursive=True)

errors = []

def check_model():
    t = io.open(MODEL, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    keys = [l.split(":")[0] for l in t if l and l[0].isalpha()]
    import collections
    dups = [k for k, c in collections.Counter(keys).items() if c > 1]
    if dups: errors.append("model3.yml duplicate top-level keys: %s" % dups)
    need = ["mixData", "expoData", "logicalSw", "customFn", "flightModeData", "telemetrySensors", "moduleData"]
    have = set(keys)
    missing = [s for s in need if s not in have]
    if missing: errors.append("model3.yml missing sections: %s" % missing)
    # every PLAY_TRACK references a WAV that exists
    import re
    for m in re.finditer(r'func: PLAY_TRACK\s*\n\s*def: "([^,"]+)', "\n".join(t)):
        wav = m.group(1) + ".wav"
        if not os.path.exists(os.path.join(SND, wav)):
            errors.append("PLAY_TRACK references missing sound: %s" % wav)
    print("model3.yml: %d top-level keys, sections OK" % len(keys) if not (dups or missing) else "model3.yml: ISSUES")

def check_wavs():
    wavs = sorted(glob.glob(os.path.join(SND, "*.wav")))
    if not wavs: errors.append("no WAVs in %s" % SND)
    for w in wavs:
        f = wave.open(w)
        ch, sw, fr = f.getnchannels(), f.getsampwidth(), f.getframerate()
        f.close()
        ok = (ch == 1 and sw == 2 and fr == 32000)
        print("  %-14s %dch %dbit %dHz %s" % (os.path.basename(w), ch, sw*8, fr, "OK" if ok else "BAD"))
        if not ok: errors.append("%s is not mono/16-bit/32kHz" % os.path.basename(w))

def check_lua():
    luac = next((shutil.which(x) for x in ("luac", "luac5.4", "luac5.3", "luac5.1") if shutil.which(x)), None)
    if not luac:
        print("luac not found — skipping Lua syntax check")
        return
    for s in LUA:
        r = subprocess.run([luac, "-p", s], capture_output=True, text=True)
        print("  %s %s" % (os.path.relpath(s, HERE), "OK" if r.returncode == 0 else "SYNTAX ERROR"))
        if r.returncode != 0: errors.append("%s: %s" % (s, r.stderr.strip()))

if __name__ == "__main__":
    print("== model =="); check_model()
    print("== sounds =="); check_wavs()
    print("== lua =="); check_lua()
    if errors:
        print("\nFAILED:"); [print("  -", e) for e in errors]; sys.exit(1)
    print("\nAll checks passed.")
