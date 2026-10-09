#!/usr/bin/env python3
"""Generate sdcard/MODELS/model3.yml for the TX15 combat robot.

Edit CONFIG, run `python3 build_model.py`, test in the EdgeTX simulator, then
`./deploy.sh`. Source of truth = this file; never hand-edit the card.

Base template: backups/model3.yml.orig (untouched "New Multirotor").
Mode-2 radio, inputs: I0=Rud(left L/R), I1=Ele(right U/D), I2=Thr(left U/D), I3=Ail(right L/R).

CONTROL LAYOUT
  CH1 steering     = Rud  (left stick L/R)      -> BBB white
  CH2 forward/back = Ele  (right stick U/D)     -> BBB yellow
  CH3 weapon       = Thr  (left stick U/D)      -> weapon ESC (REVERSIBLE / 3D)

WEAPON (reversible ESC: channel 0% = idle/off, +100% fwd, -100% rev)
  Stick bottom (rest) -> 0% (off).  Mid-stick -> 50%.  Top -> 100%.
  Spin direction = GV1 polarity XOR live SA reversal.
  Disarmed (or armed-but-not-idle-first) -> forced to centre (off).

GV1  (Model -> Global Variables): weapon direction / motor-polarity fix.
     0 = normal, 100 = reversed. One value flips spin direction.

SA (3-pos) live reversal:
  up   = normal
  mid  = weapon reversed
  down = weapon + steering reversed   (forward/back NOT reversed)

ARM = SE (down = armed). Arm is "soft": the weapon only goes live after SE is
down AND the weapon stick has been seen at idle (can't arm into a spun-up stick).

2S low-voltage alarms on RxBt (tele10): warn 7.0 V, critical 6.6 V (3.5/3.3 V/cell).
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "backups", "model3.yml.orig")
OUT  = os.path.join(HERE, "sdcard", "MODELS", "model3.yml")

# ============================== EDITABLE CONFIG ==============================
NAME        = "ANT"
IDLE_THRESH = -98     # Thr below this = weapon idle (for the soft-arm gate)
VWARN       = 70      # RxBt tenths of a volt: 2S warn  = 7.0 V (3.5 V/cell)
VCRIT       = 66      # RxBt tenths of a volt: 2S crit  = 6.6 V (3.3 V/cell)
VDELAY      = 10      # alarm sustain (tenths of a second) so spin-up sag won't trip it
RXBT        = "tele(10)"

# mix line: (destCh0, srcRaw, weight, offset, mltpx, swtch, name)
MIXES = [
    # CH1 steering (Rud), reversed when SA down (L9)
    (0, "I0",  100, 0, "ADD",  "NONE", "Steer"),
    (0, "I0", -100, 0, "REPL", "L9",   "SteerR"),
    # CH2 forward/back (Ele) -- direction set on the bench; flip weight sign if wrong
    (1, "I1",  100, 0, "ADD",  "NONE", "Drive"),
    # CH3 weapon (Thr): off at rest, 50% at mid, 100% at top; fwd/rev gated
    (2, "I2",   50,  50, "REPL", "L7",  "WpnF"),   # forward  (armsafe & not net-reverse)
    (2, "I2",  -50, -50, "REPL", "L8",  "WpnR"),   # reverse  (armsafe & net-reverse)
]

# logical switch: (func, def, delay)
LOGIC = [
    ("FUNC_VNEG",  "Thr,%d" % IDLE_THRESH, 0),   # L1 weapon stick idle
    ("FUNC_AND",   "SE2,L1",               0),   # L2 armed AND idle
    ("FUNC_STICKY","L2,!SE2",              0),   # L3 arm-safe latch (set armed+idle, reset disarm)
    ("FUNC_VPOS",  "GV1,0",                0),   # L4 base polarity reversed (GV1 > 0)
    ("FUNC_VPOS",  "SA,-50",               0),   # L5 SA mid/down -> weapon reverse
    ("FUNC_XOR",   "L4,L5",                0),   # L6 net weapon reverse
    ("FUNC_AND",   "L3,!L6",               0),   # L7 weapon FORWARD enabled
    ("FUNC_AND",   "L3,L6",                0),   # L8 weapon REVERSE enabled
    ("FUNC_VPOS",  "SA,50",                0),   # L9 SA down -> steering reverse
    ("FUNC_VNEG",  "%s,%d" % (RXBT, VWARN), VDELAY),  # L10 low-volt warn
    ("FUNC_VNEG",  "%s,%d" % (RXBT, VCRIT), VDELAY),  # L11 low-volt critical
    ("FUNC_AND",   "!L3,!L1",              0),        # L12 safe + weapon stick commanded (caution)
]

# special function: (swtch, func, def).  Sounds are F-18/RWR themed (build_sounds.py).
CUSTOM_FN = [
    ("ON",   "RGB_LED",          "combat,1,On"),   # gimbal LED rings (combat.lua)
    ("ON",   "VOLUME",           "S2,1"),          # S2 pot = speaker volume
    ("!L3",  "OVERRIDE_CHANNEL", "2,0,1"),         # force CH3 to centre/off unless arm-safe
    ("L3",   "PLAY_TRACK",       "armed,1,1x"),    # weapon armed  -> ALR-67 missile launch x4
    ("!L3",  "PLAY_TRACK",       "disarm,1,1x"),   # weapon safe   -> deedle-deedle
    ("L10",  "PLAY_TRACK",       "lowbat,1,1x"),   # low volt      -> "Fuel low" (once)
    ("L11",  "PLAY_TRACK",       "critbat,1,2"),   # critical volt -> "Bingo!" low, near-constant (every 2 s)
    ("L12",  "PLAY_TRACK",       "caution,1,2"),   # weapon hot while safe -> A320 cavalry x4 (every 2 s)
]
# ============================================================================

def mix(d, src, w, off, m, sw, nm):
    return [" -", "   destCh: %d" % d, '   srcRaw: "%s"' % src, "   carryTrim: 0",
            "   mixWarn: 0", "   mltpx: %s" % m, "   delayPrec: 0", "   speedPrec: 0",
            "   flightModes: 000000000", "   weight: %d" % w, "   offset: %d" % off,
            '   swtch: "%s"' % sw, "   delayUp: 0", "   delayDown: 0", "   speedUp: 0",
            "   speedDown: 0", '   name: "%s"' % nm]

def ls(i, fn, df, dl):
    return ["   %d:" % i, "      func: %s" % fn, '      def: "%s"' % df, '      andsw: "NONE"',
            "      lsPersist: 0", "      lsState: 0", "      delay: %d" % dl, "      duration: 0"]

def cf(i, sw, fn, df):
    return ["   %d:" % i, '      swtch: "%s"' % sw, "      func: %s" % fn, '      def: "%s"' % df]

def main():
    lines = io.open(SRC, encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
    def find(pfx):
        for i, l in enumerate(lines):
            if l.startswith(pfx): return i
        return -1

    lines = "\n".join(lines).replace('name: "New Multirotor"', 'name: "%s"' % NAME, 1).split("\n")

    # mixData
    md = ["mixData: "]
    for m in MIXES: md += mix(*m)
    lines[find("mixData:"):find("expoData:")] = md

    # logicalSw + customFn inserted before flightModeData (template has neither)
    block = ["logicalSw: "]
    for i, L in enumerate(LOGIC): block += ls(i, *L)
    block += ["customFn: "]
    for i, c in enumerate(CUSTOM_FN): block += cf(i, *c)
    anchor = find("flightModeData:")
    if anchor == -1: anchor = find("moduleData:")
    lines[anchor:anchor] = block

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write("\n".join(lines))
    print("wrote", OUT, "(%d lines)" % len(lines))

if __name__ == "__main__":
    main()
