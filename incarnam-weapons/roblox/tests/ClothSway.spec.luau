-- ClothSway spring math (the Roblox-dependent parts are compile-checked only)
game = { GetService = function() return { RenderStepped = { Connect = function() return { Disconnect = function() end } end } } end }
local ClothSway = require("ClothSway")
local passed, failed = 0, 0
local function check(name, cond, detail)
	if cond then passed += 1 else failed += 1; print("FAIL  " .. name .. (detail and ("  -- " .. detail) or "")) end
end
-- settles to target, overshoots a little (under-damped), stays finite
local x, v, peak = 0, 0, 0
for _ = 1, 600 do
	x, v = ClothSway.SpringStep(x, v, 1, 60, 0.55, 1 / 60)
	peak = math.max(peak, x)
end
check("spring: settles", math.abs(x - 1) < 1e-3, tostring(x))
check("spring: slight overshoot", peak > 1.02 and peak < 1.35, tostring(peak))
-- stable at the largest dt the module allows
x, v = 0, 0
local finite = true
for _ = 1, 400 do
	x, v = ClothSway.SpringStep(x, v, 1, 60, 0.55, 1 / 20)
	if x ~= x or math.abs(x) > 10 then finite = false end
end
check("spring: stable at dt=1/20", finite and math.abs(x - 1) < 1e-2, tostring(x))
print(string.format("ClothSway: %d passed, %d failed", passed, failed))
return failed
