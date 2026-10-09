-- combat.lua - TX15 combat-robot gimbal LED controller
--
-- Right gimbal ring (LEDs 0-9)  : battery gauge, green (full) -> red (dead)
-- Left  gimbal ring (LEDs 10-19): weapon indicator
--     * SAFE (SE up) + weapon throttle commanded above zero -> BLINK PURPLE (warning)
--     * ARMED (SE down)                                     -> throttle ramp, dim blue -> bright cyan
--     * SAFE + throttle at zero                             -> off
--   Purple appears ONLY in the safe+commanding state, and only on the left ring.
--
-- Runs continuously via an "RGB leds" special function with the switch set to ON.
-- LED mapping (ring 0 = right, ring 1 = left, 10 per ring) matches EdgeTX's own
-- gimbal.lua reference for the TX15.
--
-- Tested target: RadioMaster TX15 (2POS SE), EdgeTX 2.12.

------------------------------------------------------------------- config -----
local CFG = {
  -- Battery, right ring. Values are the ROBOT pack voltage from telemetry.
  BATT_SENSOR = "RxBt",  -- ELRS RX vbat sensor (confirmed discovered on this model)
  V_FULL      = 8.4,     -- 2S full  (4.20 V/cell) -> full green
  V_DEAD      = 6.6,     -- 2S dead  (3.30 V/cell) -> full red

  -- Weapon, left ring. Commanded throttle today; swap to a real RPM sensor later
  -- by setting WEAPON_SRC to the sensor name and WEAPON_MIN=0, WEAPON_MAX=<max eRPM>.
  WEAPON_SRC      = "thr",  -- left-stick throttle (raw stick, before the SE gate)
  WEAPON_MIN      = -1024,  -- source value at zero throttle
  WEAPON_MAX      =  1024,  -- source value at full throttle
  WEAPON_DEADBAND =  40,    -- ignore tiny values just off the bottom

  -- Arm switch: SE down (>0) = armed/live, SE up = safe.
  ARM_SRC = "se",

  -- Purple warning blink: getTime() ticks for a full on+off cycle (~400ms = 2.5 Hz).
  BLINK_PERIOD = 40,
}

-- LED index ranges (do not change for TX15)
local R_LO, R_HI = 0, 9    -- right ring: battery
local L_LO, L_HI = 10, 19  -- left ring : weapon

------------------------------------------------------------------- helpers ----
local ids = {}
local hasLeds = false

local function readSource(name)
  local id = ids[name]
  if id == nil then
    local fi = getFieldInfo(name)
    if fi then id = fi.id; ids[name] = id end
  end
  if id ~= nil then return getValue(id) or 0 end
  return getValue(name) or 0
end

local function clamp(x, lo, hi)
  if x < lo then return lo elseif x > hi then return hi else return x end
end

local function round(x) return math.floor(x + 0.5) end

local function fill(lo, hi, r, g, b)
  for i = lo, hi do setRGBLedColor(i, r, g, b) end
end

-- green (full) -> yellow (mid) -> red (dead), full brightness across the range
local function battColor(v)
  if not v or v <= 0.5 then return 0, 0, 0 end  -- no telemetry -> ring off
  local pct = clamp((v - CFG.V_DEAD) / (CFG.V_FULL - CFG.V_DEAD), 0, 1)
  if pct >= 0.5 then
    return round(255 * (1 - pct) * 2), 255, 0
  else
    return 255, round(255 * pct * 2), 0
  end
end

--------------------------------------------------------------------- api -------
local function init()
  hasLeds = (setRGBLedColor ~= nil) and (applyRGBLedColors ~= nil)
end

local function run()
  if not hasLeds then return end

  -- Right ring: battery
  local br, bg, bb = battColor(readSource(CFG.BATT_SENSOR))
  fill(R_LO, R_HI, br, bg, bb)

  -- Left ring: weapon
  local thr        = readSource(CFG.WEAPON_SRC)
  local armed      = readSource(CFG.ARM_SRC) > 0
  local commanding = thr > (CFG.WEAPON_MIN + CFG.WEAPON_DEADBAND)

  if (not armed) and commanding then
    -- WARNING: throttle commanded while safe -> blink purple (this state only)
    if (getTime() % CFG.BLINK_PERIOD) < (CFG.BLINK_PERIOD / 2) then
      fill(L_LO, L_HI, 128, 0, 128)
    else
      fill(L_LO, L_HI, 0, 0, 0)
    end
  elseif armed then
    -- throttle ramp: dim blue at idle -> bright white-cyan at full
    local frac = clamp((thr - CFG.WEAPON_MIN) / (CFG.WEAPON_MAX - CFG.WEAPON_MIN), 0, 1)
    fill(L_LO, L_HI, round(255 * frac * 0.6), round(255 * frac), round(40 + 215 * frac))
  else
    -- safe and idle
    fill(L_LO, L_HI, 0, 0, 0)
  end

  applyRGBLedColors()
end

local function background()
end

return { run = run, background = background, init = init }
