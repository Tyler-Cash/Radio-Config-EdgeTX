local function init()
end

local function setLed(ring, h, v)
   local magnitude = math.sqrt(h^2 + v^2)
   if magnitude < 0.1 then return end

   local angle = math.atan2(v, h)
   angle = (math.deg(angle) + 360) % 360
   local center_index = math.floor(angle / 36 + 0.5) % 10
   center_index = center_index + ring * 10

   local base_intensity = 250 * magnitude
   base_intensity = math.min(255, base_intensity)

   local spread = 2

   for offset = -spread, spread do
     local index = (center_index + offset) % 10 + ring * 10
     local distance = math.abs(offset)
     local factor = math.exp(-0.5 * (distance ^ 2))
     local intensity = math.floor(base_intensity * factor)
     setRGBLedColor(index, intensity, intensity, intensity)
   end
end
    
local function run()
  for i=0, LED_STRIP_LENGTH - 1, 1
  do
    setRGBLedColor(i, 64, 26, 45) -- Pink color (scaled to match original brightness)
  end
  
  setLed(0, -getValue("ail")/1024, getValue("thr")/1024)
  setLed(1, getValue("rud")/1024, -getValue("ele")/1024)

  applyRGBLedColors()
end

local function background()
  -- Called periodically while the Special Function switch is off
end

return { run=run, background=background, init=init }