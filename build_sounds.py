#!/usr/bin/env python3
"""Generate F-18 / RWR-themed event sounds for the TX15 combat model.

Writes mono 16-bit 32 kHz WAVs (EdgeTX format) to sdcard/SOUNDS/en/.
Synthesized to evoke an F/A-18 ALR-67 RWR + master-arm vibe:
  armed   -> authoritative rising "master arm" two-tone + confirm chirp
  disarm  -> calm descending "safe" tone
  lowbat  -> RWR search/acquisition: slow buzzy "beep .. beep" (someone's looking)
  critbat -> RWR missile-launch: urgent fast warble "deedledeedle"
  caution -> master-caution double chirp (for the weapon-hot-while-safe warning)

Run: python3 build_sounds.py
"""
import io, os, math, struct

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "sdcard", "SOUNDS", "en")
RATE = 32000

def _env(i, n, a_ms=4, r_ms=8):
    # short attack/release envelope (samples) to avoid clicks
    a = int(RATE * a_ms / 1000); r = int(RATE * r_ms / 1000)
    if i < a:      return i / a
    if i > n - r:  return max(0.0, (n - i) / r)
    return 1.0

def tone(freq, ms, amp=0.55, shape="buzz"):
    """buzz = odd-harmonic (RWR-ish rasp); sine = clean."""
    n = int(RATE * ms / 1000); out = []
    for i in range(n):
        t = i / RATE
        if shape == "buzz":
            s = (math.sin(2*math.pi*freq*t)
                 + 0.33*math.sin(2*math.pi*3*freq*t)
                 + 0.20*math.sin(2*math.pi*5*freq*t)) / 1.53
        else:
            s = math.sin(2*math.pi*freq*t)
        out.append(amp * s * _env(i, n))
    return out

def warble(f1, f2, seg_ms, total_ms, amp=0.6, shape="buzz"):
    """rapid alternation between two pitches — the RWR launch 'deedle'."""
    out = []
    while len(out) < int(RATE*total_ms/1000):
        out += tone(f1, seg_ms, amp, shape)
        out += tone(f2, seg_ms, amp, shape)
    return out[:int(RATE*total_ms/1000)]

def gap(ms): return [0.0]*int(RATE*ms/1000)

def write(name, samples):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    w = io.open(p, "wb")
    import wave
    wf = wave.open(w, "wb"); wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE)
    wf.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(s*32767)))) for s in samples))
    wf.close(); w.close()
    print("wrote", os.path.relpath(p, HERE), "%.2fs" % (len(samples)/RATE))

def build():
    # ARM: rising two-tone + high confirm chirp ("master arm, weapons hot")
    write("armed.wav",
          tone(520, 130) + gap(30) + tone(780, 150) + gap(40) + tone(1180, 90, 0.5))
    # DISARM: calm descending (sine, softer) -> "safe"
    write("disarm.wav",
          tone(780, 130, 0.5, "sine") + gap(25) + tone(430, 190, 0.45, "sine"))
    # LOW BATT: RWR search — slow buzzy beeps at ~900 Hz
    write("lowbat.wav",
          tone(900, 90) + gap(110) + tone(900, 90) + gap(110) + tone(900, 90))
    # CRITICAL: RWR missile-launch — urgent fast warble
    write("critbat.wav",
          warble(1500, 1950, 28, 950, 0.62))
    # MASTER CAUTION: double chirp (weapon commanded while safe)
    write("caution.wav",
          tone(1300, 70, 0.5) + gap(60) + tone(1300, 70, 0.5))

if __name__ == "__main__":
    build()
