# TX15 Combat Robot — model config

EdgeTX config for a combat robot on a **RadioMaster TX15** (EdgeTX 2.12), model
**"New Multirotor"** (`model3.yml`). Right-stick drive, left-stick weapon, an
SE software-arm on the weapon, and both gimbal LED rings used as live indicators.

## What was applied to the radio (already done)

Edits made directly to `MODELS/model3.yml` on the SD card, plus a Lua script
copied to `SCRIPTS/RGBLED/combat.lua`.

### Mixer
| Ch | Function | Source | Change |
|----|----------|--------|--------|
| CH1 | Drive forward/back | Ele (right stick Y) | **weight → −100** (this is the flip you asked for) |
| CH2 | Weapon | Thr (left stick Y) | **SE software-arm gate** (see below) |
| CH3 | Steering | Ail (right stick X) | unchanged (left/right was already correct) |

**Weapon soft-arm (CH2):** two mix lines —
1. `Thr` weight 100 (normal throttle)
2. `MAX` weight −100, **REPLACE**, switch `!SE2` — when **SE is up (safe)** this
   forces CH2 to −100 (weapon off) *regardless of the throttle stick*.

So the weapon ESC only ever sees throttle when **SE is down (armed)**. Your
existing hardware Arm on SF (CH4) is untouched and independent.

### Gimbal LEDs — `combat.lua`
Runs continuously via an "RGB leds" special function (`customFn 0`, switch `ON`).

**Right ring (LEDs 0–9) — battery**, from the `RxBt` telemetry sensor (3S):
- 12.6 V → green · ~11.25 V → yellow · 9.9 V → red · no telemetry → off

**Left ring (LEDs 10–19) — weapon:**
- **Safe (SE up) + throttle commanded above zero → blinks PURPLE** (~2.5 Hz).
  This is the only place purple ever appears.
- **Armed (SE down) → throttle ramp:** dim blue at idle → bright white-cyan at full.
- **Safe + throttle at zero → off.**

## Bench test (do this before running the weapon)

Disconnect USB, let the radio reboot, select **New Multirotor**, then:

1. **Right stick / drive:** push right stick forward → bot should now drive
   forward (was reversed). Left/right unchanged.
2. **Battery ring:** power the bot on charged → right gimbal ring green; as the
   pack drains it shifts toward red. (If it stays off, telemetry isn't arriving —
   re-check the bind / `RxBt` sensor.)
3. **Soft-arm, weapon SAFE (SE up):** with wheels up / weapon belt off, push the
   weapon throttle up. Left ring should **blink purple** and the weapon must
   **stay stopped** (CH2 held at −100). Confirm on the bot before trusting it.
4. **Arm (SE down):** left ring switches to the blue→cyan ramp and tracks the
   throttle stick; weapon now responds. Pull throttle to zero, SE up to safe.
5. Throttle-warning on power-up is left enabled (weapon on the throttle stick) —
   that's intentional; drop the stick to clear it.

## Tuning
Everything adjustable lives in the `CFG` block at the top of `combat.lua`:
- Battery scale: `V_FULL` / `V_DEAD` (per-cell × 3). Different pack → change here.
- Weapon source: `WEAPON_SRC` is `"thr"` (commanded throttle). If a real RPM
  sensor ever shows up in telemetry discovery, set `WEAPON_SRC` to its name and
  `WEAPON_MIN=0`, `WEAPON_MAX=<max eRPM>` — no other changes needed.
- Arm direction: gate uses `!SE2` in the mixer and `se > 0` in the script (SE
  down = armed). To flip, invert both.
- Blink rate: `BLINK_PERIOD` (getTime ticks; 40 ≈ 2.5 Hz).

To edit the script: change `combat.lua` in this folder, then copy it to
`SCRIPTS/RGBLED/combat.lua` on the card.

## Backups
`backups/model3.yml.orig` — the model before any edits.
`backups/RGBLED.orig/` — the entire RGBLED script folder as it was (53 scripts),
in case anything needs restoring.

## Verification done here
- `combat.lua` passes `luac -p` and was run through a stubbed-API harness across
  all battery/weapon/arm states (see `DESIGN.md`). Colors and ring assignment
  confirmed. **Final on-bot verification is the checklist above** — this is
  hardware I can't drive from here.
