-- ChainSolver behaviour tests. Run with: node roblox/tests/run.mjs
Vector3 = require("Vector3Shim") -- global, as in Roblox
local ChainSolver = require("ChainSolver")

local passed, failed = 0, 0
local function check(name: string, cond: boolean, detail: string?)
	if cond then
		passed += 1
	else
		failed += 1
		print("FAIL  " .. name .. (if detail then ("  -- " .. detail) else ""))
	end
end

local function segStats(pts, pitch)
	local worst = 0
	for i = 1, #pts - 1 do
		local e = math.abs((pts[i + 1] - pts[i]).Magnitude - pitch) / pitch
		if e > worst then
			worst = e
		end
	end
	return worst
end

local function finite(pts)
	for _, p in pts do
		if p.X ~= p.X or p.Y ~= p.Y or p.Z ~= p.Z or math.abs(p.X) > 1e6 or math.abs(p.Y) > 1e6 then
			return false
		end
	end
	return true
end

local PITCH = 0.21
local DT = 1 / 60

-- 1) Hang: slack chain keeps every link at pitch (within 2%) and endpoints pinned
do
	local s = ChainSolver.new({ LinkCount = 28, Pitch = PITCH, Mode = "Hang" })
	local a, b = Vector3.new(-1.5, 2, 0), Vector3.new(1.5, 2, 0)
	local pts
	for _ = 1, 240 do
		pts = s:Step(a, b, DT)
	end
	check("hang: link count", #pts == 29, tostring(#pts))
	check("hang: endpoints pinned", (pts[1] - a).Magnitude < 1e-6 and (pts[#pts] - b).Magnitude < 1e-6)
	local err = segStats(pts, PITCH)
	check("hang: no stretch (<2%)", err < 0.02, string.format("worst %.3f", err))
	local lowest = math.huge
	for _, p in pts do
		lowest = math.min(lowest, p.Y)
	end
	check("hang: sags below the hands", lowest < 1.5, string.format("lowest %.2f", lowest))
	check("hang: not overextended", not s.Stats.Overextended)
end

-- 2) Floor clamp: long chain never goes through the floor
do
	local s = ChainSolver.new({ LinkCount = 40, Pitch = PITCH, Mode = "Hang" })
	local a, b = Vector3.new(-1.0, 2, 0), Vector3.new(1.0, 2, 0)
	local pts
	for _ = 1, 300 do
		pts = s:Step(a, b, DT, 0.0)
	end
	local lowest = math.huge
	for _, p in pts do
		lowest = math.min(lowest, p.Y)
	end
	check("floor: stays above floor + clearance", lowest >= 0.05 - 1e-6, string.format("lowest %.4f", lowest))
end

-- 3) Overextended: straight, reaches both eyelets (no gap), stretch reported
do
	local s = ChainSolver.new({ LinkCount = 10, Pitch = PITCH, Mode = "Hang", MaxStretch = 0.03 })
	local len = 10 * PITCH
	local a, b = Vector3.new(0, 2, 0), Vector3.new(len * 1.10, 2, 0)
	local pts = s:Step(a, b, DT)
	check("over: reaches B", (pts[#pts] - b).Magnitude < 1e-6)
	local straight = true
	for _, p in pts do
		if math.abs(p.Y - 2) > 1e-6 then
			straight = false
		end
	end
	check("over: straight", straight)
	check("over: flagged", s.Stats.Overextended)
	check("over: stretch ~10%", math.abs(s.Stats.Stretch - 0.10) < 1e-3, tostring(s.Stats.Stretch))
	-- within tolerance: reported but not flagged
	local s2 = ChainSolver.new({ LinkCount = 10, Pitch = PITCH, MaxStretch = 0.03 })
	s2:Step(a, Vector3.new(len * 1.02, 2, 0), DT)
	check("over: 2% within tolerance not flagged", not s2.Stats.Overextended)
end

-- 4) Taut exactly at chain length, then slack again: no explosion, lengths recover
do
	local s = ChainSolver.new({ LinkCount = 24, Pitch = PITCH, Mode = "Hang" })
	local len = 24 * PITCH
	local pts
	local worstSlack = 0
	for f = 0, 600 do
		local t = f / 600
		local w = 0.5 - 0.5 * math.cos(2 * math.pi * 2 * t)
		local gap = 2.5 + w * (len * 1.05 - 2.5) -- swings from idle to slightly past taut
		local a = Vector3.new(-gap / 2, 2 + 0.3 * math.sin(7 * t), 0.2 * math.cos(5 * t))
		local b = Vector3.new(gap / 2, 2, 0)
		pts = s:Step(a, b, DT, 0)
		check("swing: finite", finite(pts))
		if gap < len * 0.95 then
			worstSlack = math.max(worstSlack, segStats(pts, PITCH))
		end
	end
	-- Visual tolerance: interlocked box links hide up to ~one bar thickness of extra spacing
	-- (bar 0.03 / pitch 0.21 = 14%). Require half of that during fast, oscillating swings.
	check("swing: links hold length while slack (<7.5%)", worstSlack < 0.075, string.format("worst %.3f", worstSlack))
end

-- 5) Coil: pays out with the gap, conserves link count, parks the rest
do
	local s = ChainSolver.new({ LinkCount = 30, Pitch = PITCH, Mode = "Coil", RestSlack = 1.25, MinPaidOut = 4 })
	local coil = { Origin = Vector3.new(-1.5, 2.2, 0), Axis = Vector3.new(0, 1, 0), Radius = 0.62 }
	local a = Vector3.new(-1.5, 2, 0)
	local pts = s:Step(a, Vector3.new(-1.0, 2, 0), DT, nil, coil) -- hands close together
	local closeOut = s.PaidOut
	check("coil: min paid out respected", closeOut >= 4, tostring(closeOut))
	check("coil: short when hands close", closeOut < 30, tostring(closeOut))
	check("coil: slots = parked links", #s:CoilSlots(coil) == 30 - closeOut)
	check("coil: points match paid out", #pts == closeOut + 1)
	local last = closeOut
	local monotonic = true
	for f = 1, 120 do
		local gap = 0.5 + f / 120 * 5.5
		s:Step(a, a + Vector3.new(gap, 0, 0), DT, nil, coil)
		if s.PaidOut < last then
			monotonic = false
		end
		last = s.PaidOut
	end
	check("coil: pays out monotonically as hands separate", monotonic)
	check("coil: fully paid out when wide", s.PaidOut == 30, tostring(s.PaidOut))
	check("coil: all links accounted", s.PaidOut + #s:CoilSlots(coil) == 30)
	-- reel back in with hysteresis (one link per step at most)
	local before = s.PaidOut
	s:Step(a, a + Vector3.new(0.6, 0, 0), DT, nil, coil)
	check("coil: reels in gradually", before - s.PaidOut <= 1, string.format("%d -> %d", before, s.PaidOut))
	local slots = s:CoilSlots(coil)
	local onRadius = true
	for _, sl in slots do
		local rel = sl.Center - coil.Origin
		local radial = (rel - coil.Axis * rel:Dot(coil.Axis)).Magnitude
		if math.abs(radial - 0.62) > 1e-6 then
			onRadius = false
		end
	end
	check("coil: slots wrap at the coil radius", onRadius)
end

-- 6) SuggestLinkCount
do
	check("suggest: 7 studs @0.21 + 5%", ChainSolver.SuggestLinkCount(7.0, 0.21) == 35, tostring(ChainSolver.SuggestLinkCount(7.0, 0.21)))
	check("suggest: custom margin", ChainSolver.SuggestLinkCount(4.2, 0.21, 0) == 20)
end

-- 7) Robustness: identical endpoints, huge dt, teleport
do
	local s = ChainSolver.new({ LinkCount = 12, Pitch = PITCH })
	local p = Vector3.new(0, 3, 0)
	local pts = s:Step(p, p, DT)
	check("robust: zero gap finite", finite(pts))
	pts = s:Step(p, p + Vector3.new(0.5, 0, 0), 5.0) -- dt clamped
	check("robust: huge dt finite", finite(pts))
	pts = s:Step(Vector3.new(500, 3, 0), Vector3.new(501, 3, 0), DT) -- character teleported
	check("robust: teleport finite", finite(pts))
	for _ = 1, 60 do
		pts = s:Step(Vector3.new(500, 3, 0), Vector3.new(501, 3, 0), DT)
	end
	check("robust: recovers after teleport", segStats(pts, PITCH) < 0.05, string.format("%.3f", segStats(pts, PITCH)))
end

print(string.format("ChainSolver: %d passed, %d failed", passed, failed))
return failed
