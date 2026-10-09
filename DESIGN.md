# Design spec — TX15 combat-robot model

**Radio:** RadioMaster TX15 (EdgeTX 2.12.2), 2× RGB gimbal rings (10 LEDs each,
20 total). SE is a 2POS switch. **Robot:** ELRS RX + BLHeli/DShot weapon ESC.
**Model:** `model3.yml` ("New Multirotor").

## Goals (from the request)
1. Right gimbal ring = robot **battery** gauge, green (full) → red (dead).
2. Left gimbal ring = **weapon** indicator (RPM if available, else throttle).
3. Fix reversed **forward/back on the right stick**; left/right is correct.
4. **SE = software arm** for the weapon: weapon output forced to 0 unless SE
   armed, regardless of throttle. When safe but throttle is commanded above zero,
   the left ring blinks **purple** (purple only in this state, left ring only).

## Key findings that shaped the design
- **LED indexing** (from EdgeTX's own `SCRIPTS/RGBLED/gimbal.lua`): ring 0 =
  right gimbal = indices 0–9; ring 1 = left gimbal = indices 10–19;
  `LED_STRIP_LENGTH` is unreliable, so 20/10 are hardcoded.
- **RGB LED API** (EdgeTX ≥2.10): `setRGBLedColor(index,r,g,b)` +
  `applyRGBLedColors()`. `getValue()` reads sticks/switches/telemetry inside the
  same script; `getTime()` (10 ms ticks) drives the blink. An "RGB leds" special
  function calls the script's `run()` continuously while its switch is active.
- **Telemetry discovered on the model:** link stats, and a battery frame with
  **`RxBt`** (voltage), `Curr`, `Capa`, `Bat%`, plus a `Volt` sensor. **No RPM /
  eRPM sensor** — a bare ELRS RX doesn't decode bidirectional-DShot RPM. So the
  weapon ring uses **commanded throttle**, with a one-line hook to switch to a
  real RPM sensor later. Battery uses measured `RxBt` (not `Bat%`, which is
  unreliable without a current-sensor config).
- **Channel map** (confirmed from the model; consistent with "only fwd/back is
  wrong"): CH1 = Ele (drive fwd/back), CH2 = Thr (weapon), CH3 = Ail (steering).
- **Schema tokens verified against EdgeTX source:** `swtch: "ON"` = always-true
  (`SWSRC_ON`); `srcRaw: "MAX"` = +100% constant (`MIXSRC_MAX`); `SE2` = SE down;
  `RGB_LED` customFn `def` format `"<script>,1,On"` (matches the AERO model).

## Implementation
**Mixer** (`model3.yml`):
- CH1 mix weight 100 → **−100** (reverse drive fwd/back).
- CH2 gains a 2nd line: `MAX` × −100, REPLACE, switch `!SE2` → weapon forced to
  −100 whenever SE is up (safe). Base `Thr` line unchanged.
- New `customFn 0`: `RGB_LED`, switch `ON`, `def "combat,1,On"`.

**Script** (`SCRIPTS/RGBLED/combat.lua`): every cycle —
- Right ring: `RxBt` → % over [V_DEAD, V_FULL] → two-segment green↔yellow↔red at
  full brightness; no telemetry → off.
- Left ring: read raw `thr` (pre-gate) and `se`.
  - `not armed and commanding` → blink purple (128,0,128) on a `BLINK_PERIOD`
    duty cycle.
  - `armed` → ramp `(0.6·f·255, f·255, 40+215·f)`, f = throttle fraction.
  - else → off.
- `applyRGBLedColors()` once.

Reading the **raw stick** (not CH2) for the left ring is deliberate: CH2 is held
at −100 when safe, so only the raw stick reveals a commanded-while-safe state to
trigger the purple warning.

## Verification
- `luac -p` clean.
- Stubbed-API harness over states: FULL→green, 50%→yellow, DEAD→red, no-telem→off;
  armed idle→dim blue, 50%→(77,128,148), 100%→(153,255,255); safe+idle→off;
  safe+commanding→purple toggling with `getTime()`. Asserted purple never on the
  right ring and all 20 LEDs painted each cycle.
- On-bot behavior (drive direction, telemetry presence, weapon cut) must be
  confirmed on the bench — see `README.md`.

## Parameters (this build)
3S: V_FULL 12.6, V_DEAD 9.9. WEAPON_SRC "thr", range [−1024, 1024], deadband 40.
ARM: SE down = armed (`se > 0` / `!SE2` cut). BLINK_PERIOD 40 ticks (~2.5 Hz).
