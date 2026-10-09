#!/usr/bin/env python3
"""Convert the real source clips in sounds-src/ into EdgeTX event WAVs
(mono, 16-bit, 32 kHz) in sdcard/SOUNDS/en/, applying the per-event repeat and
volume. Supersedes the old synthesized build_sounds.py.

Requires ffmpeg. Run: python3 import_sounds.py
"""
import os, subprocess, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "sounds-src")
OUT  = os.path.join(HERE, "sdcard", "SOUNDS", "en")

# out name, source file, times-to-play (concatenated), volume (1.0 = unchanged)
JOBS = [
    ("armed.wav",   "missile_launch.wav", 4, 1.0),  # weapon armed  -> ALR-67 launch x4
    ("disarm.wav",  "deedle.mp3",         1, 1.0),  # weapon safe   -> deedle-deedle
    ("caution.wav", "cavalry.mp3",        4, 1.0),  # master caution-> A320 cavalry x4
    ("lowbat.wav",  "fuel_low.mp3",       1, 1.0),  # low battery   -> "Fuel low"
    ("critbat.wav", "bingo.mp3",          1, 0.45), # critical      -> "Bingo!" low volume
]

def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")
    os.makedirs(OUT, exist_ok=True)
    for out, src, plays, vol in JOBS:
        srcp = os.path.join(SRC, src)
        outp = os.path.join(OUT, out)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-stream_loop", str(plays - 1), "-i", srcp,
               "-af", "volume=%s" % vol,
               "-ac", "1", "-ar", "32000", "-c:a", "pcm_s16le", outp]
        subprocess.run(cmd, check=True)
        import wave
        w = wave.open(outp); dur = w.getnframes() / w.getframerate(); w.close()
        print("wrote %-12s <- %-20s x%d vol %.2f  (%.2fs)" % (out, src, plays, vol, dur))

if __name__ == "__main__":
    main()
