--!strict
--[[
	ChainSolver - pure, engine-agnostic fixed-length chain simulation (Verlet + distance constraints).

	Used by WarlinkChain (Roblox) and by the tests in roblox/tests (run outside Roblox with a Vector3 shim).
	Only uses Vector3 arithmetic (+, -, *, /, .Magnitude, .Unit, :Dot, :Cross) so it runs anywhere.

	Model: LinkCount rigid links joined at LinkCount+1 joint points, every link exactly Pitch long.
	  * Points[1] and Points[LinkCount+1] are pinned to the two eyelets every step.
	  * Links never stretch while the eyelet gap <= chain length. If an animation pushes the eyelets
	    further apart than the chain allows (animations cannot be stopped by a visual chain), the chain
	    goes perfectly straight and every link shares the extra evenly, so there is never a visible gap.
	    Stats.Stretch reports it; Stats.Overextended turns true past MaxStretch (default 3%), which means
	    LinkCount is too low for that animation (size it with tools/MeasureHandSpan).
	  * Mode "Hang": the whole chain is always between the eyelets; gravity sag, clamped above FloorY.
	  * Mode "Coil": only the links needed to span the gap (plus RestSlack) are "paid out"; the rest are
	    parked on a helix around the A-side forearm (coil frame supplied by the caller) and unwind as the
	    hands separate. The total link count never changes, so length stays coherent.
]]

export type Config = {
	LinkCount: number,
	Pitch: number, -- centre-to-centre spacing of two interlocked links (studs)
	Gravity: Vector3?, -- studs/s^2, default (0, -workspace.Gravity-ish)
	Damping: number?, -- 0..1 velocity retained per 1/60 s, default 0.9
	Iterations: number?, -- constraint passes per step, default 2 x links (16..90)
	Relaxation: number?, -- over-relaxation factor for early passes (1 = off), default 1.6
	MaxStretch: number?, -- allowed fractional stretch when overextended, default 0.03
	Mode: ("Hang" | "Coil")?,
	RestSlack: number?, -- Coil: paid-out length = gap * RestSlack (>= 1), default 1.25
	MinPaidOut: number?, -- Coil: never fewer links than this between the hands, default 4
	FloorClearance: number?, -- keep joints this far above FloorY, default 0.05
}

export type CoilFrame = {
	Origin: Vector3, -- point on the forearm axis where the coil starts (near the eyelet)
	Axis: Vector3, -- unit vector along the forearm, pointing up the arm (away from the hand)
	Radius: number, -- coil radius (R6 arm half-width + link width), e.g. 0.62
	Turn: number?, -- radians of coil per parked link, default 1.05
	Rise: number?, -- studs along Axis per parked link, default 0.06
}

export type Stats = {
	Gap: number,
	ChainLength: number,
	PaidOut: number,
	Overextended: boolean, -- true when stretch exceeds MaxStretch: raise LinkCount
	Overshoot: number, -- studs beyond ChainLength (0 when fine)
	Stretch: number, -- fractional stretch per link right now (0 when slack)
	MaxObservedGap: number,
}

local ChainSolver = {}
ChainSolver.__index = ChainSolver

export type Solver = typeof(setmetatable(
	{} :: {
		Config: Config,
		Points: { Vector3 },
		Prev: { Vector3 },
		PaidOut: number,
		Stats: Stats,
		_initialised: boolean,
	},
	ChainSolver
))

local DEFAULT_GRAVITY = Vector3.new(0, -60, 0) -- softer than workspace.Gravity (196.2): reads as heavy chain, not jitter

local function clampNum(x: number, lo: number, hi: number): number
	if x < lo then
		return lo
	elseif x > hi then
		return hi
	end
	return x
end

function ChainSolver.new(config: Config): Solver
	assert(config.LinkCount >= 2, "ChainSolver: LinkCount must be >= 2")
	assert(config.Pitch > 0, "ChainSolver: Pitch must be > 0")
	local self = setmetatable({
		Config = config,
		Points = {},
		Prev = {},
		PaidOut = config.LinkCount,
		Stats = {
			Gap = 0,
			ChainLength = config.LinkCount * config.Pitch,
			PaidOut = config.LinkCount,
			Overextended = false,
			Overshoot = 0,
			Stretch = 0,
			MaxObservedGap = 0,
		},
		_initialised = false,
	}, ChainSolver)
	return self
end

function ChainSolver.Length(self: Solver): number
	return self.Config.LinkCount * self.Config.Pitch
end

-- Number of links currently between the hands (Coil mode pays out; Hang mode uses all of them).
function ChainSolver._targetPaidOut(self: Solver, gap: number): number
	local c = self.Config
	if (c.Mode or "Hang") ~= "Coil" then
		return c.LinkCount
	end
	local slack = c.RestSlack or 1.25
	local want = math.ceil((gap * slack) / c.Pitch)
	return clampNum(want, math.min(c.MinPaidOut or 4, c.LinkCount), c.LinkCount)
end

-- Place n+1 points from a to b with a sag, used to (re)initialise or when the paid-out count changes.
local function seed(a: Vector3, b: Vector3, n: number, pitch: number): { Vector3 }
	local pts = table.create(n + 1)
	local gap = (b - a).Magnitude
	local length = n * pitch
	local sag = 0
	if length > gap then
		-- parabola depth that roughly preserves arc length: L ~= g + 8 d^2 / (3 g)
		local g = math.max(gap, 1e-3)
		sag = math.sqrt(math.max(0, (length - g) * 3 * g / 8))
	end
	for i = 0, n do
		local t = i / n
		pts[i + 1] = a:Lerp(b, t) - Vector3.new(0, sag * 4 * t * (1 - t), 0)
	end
	return pts
end

--[[
	Step the simulation.
	a, b      : eyelet world positions this frame
	dt        : seconds since last step (clamped internally)
	floorY    : optional ground height under the chain (nil = no floor)
	coil      : CoilFrame for the A side (Coil mode only)
	returns   : array of joint points for the PAID-OUT links (length PaidOut+1, from a to b)
]]
function ChainSolver.Step(self: Solver, a: Vector3, b: Vector3, dt: number, floorY: number?, coil: CoilFrame?): { Vector3 }
	local c = self.Config
	local pitch = c.Pitch
	local gap = (b - a).Magnitude
	local target = self:_targetPaidOut(gap)

	-- hysteresis: pay out immediately, reel in only when clearly slack (prevents flicker)
	if not self._initialised then
		self.PaidOut = target
	elseif target > self.PaidOut then
		self.PaidOut = target
	elseif target < self.PaidOut - 1 then
		self.PaidOut = self.PaidOut - 1
	end
	local n = self.PaidOut

	if not self._initialised or #self.Points ~= n + 1 then
		local old = self.Points
		local fresh = seed(a, b, n, pitch)
		if self._initialised and #old > 0 then
			-- keep continuity: reuse old interior shape where it exists (shifted toward the B end)
			local shift = (n + 1) - #old
			for i = 1, #old do
				local j = i + math.max(shift, 0)
				if j >= 2 and j <= n then
					fresh[j] = old[i]
				end
			end
		end
		self.Points = fresh
		self.Prev = table.clone(fresh)
		self._initialised = true
	end

	local pts, prev = self.Points, self.Prev
	local length = n * pitch
	local maxStretch = c.MaxStretch or 0.03

	-- overextended: chain is straight and every link shares the extra length evenly (never a gap).
	-- Stretch beyond MaxStretch means LinkCount is too low for this animation: flagged in Stats.
	if gap >= length then
		local stretch = gap / length - 1
		self.Stats.Stretch = stretch
		self.Stats.Overextended = stretch > maxStretch
		self.Stats.Overshoot = math.max(0, gap - length)
		for i = 0, n do
			local p = a:Lerp(b, i / n)
			prev[i + 1] = p
			pts[i + 1] = p
		end
	else
		self.Stats.Overextended = false
		self.Stats.Overshoot = 0
		self.Stats.Stretch = 0
		local h = clampNum(dt, 1 / 240, 1 / 30)
		local damping = (c.Damping or 0.9) ^ (h * 60)
		local accel = (c.Gravity or DEFAULT_GRAVITY) * (h * h)
		-- integrate interior points
		for i = 2, n do
			local p = pts[i]
			local v = (p - prev[i]) * damping
			prev[i] = p
			pts[i] = p + v + accel
		end
		pts[1], pts[n + 1] = a, b
		prev[1], prev[n + 1] = a, b
		-- satisfy distance constraints (alternate sweep direction to remove bias)
		-- Gauss-Seidel needs ~O(n) passes for corrections to cross a chain pinned at both ends
		local iters = c.Iterations or math.clamp(math.floor(n * 2), 16, 90)
		local clearance = c.FloorClearance or 0.05
		for it = 1, iters do
			-- successive over-relaxation for the bulk of the passes, plain projection for the last few
			local relax = if it <= iters - 4 then (c.Relaxation or 1.6) else 1.0
			local fwd = it % 2 == 1
			for k = 1, n do
				local i = if fwd then k else n - k + 1
				local p, q = pts[i], pts[i + 1]
				local d = q - p
				local len = d.Magnitude
				if len > 1e-6 then
					local diff = relax * (len - pitch) / len
					if i == 1 then
						pts[i + 1] = q - d * diff
					elseif i == n then
						pts[i] = p + d * diff
					else
						pts[i] = p + d * (0.5 * diff)
						pts[i + 1] = q - d * (0.5 * diff)
					end
				end
			end
			pts[1], pts[n + 1] = a, b
			if floorY then
				local minY = floorY + clearance
				for i = 2, n do
					local p = pts[i]
					if p.Y < minY then
						pts[i] = Vector3.new(p.X, minY, p.Z)
					end
				end
			end
		end
	end

	self.Stats.Gap = gap
	self.Stats.PaidOut = n
	self.Stats.ChainLength = self:Length()
	if gap > self.Stats.MaxObservedGap then
		self.Stats.MaxObservedGap = gap
	end
	return pts
end

--[[
	Coil slots for the links NOT paid out (Coil mode). Returns array of {Center, Tangent} pairs, one per
	parked link, wrapping a helix around the forearm starting at coil.Origin and rising along coil.Axis.
]]
function ChainSolver.CoilSlots(self: Solver, coil: CoilFrame): { { Center: Vector3, Tangent: Vector3 } }
	local parked = self.Config.LinkCount - self.PaidOut
	local out = table.create(parked)
	if parked <= 0 then
		return out
	end
	local axis = coil.Axis.Unit
	local ref = if math.abs(axis.Y) < 0.9 then Vector3.new(0, 1, 0) else Vector3.new(1, 0, 0)
	local u = axis:Cross(ref).Unit
	local v = axis:Cross(u).Unit
	local turn = coil.Turn or 1.05
	local rise = coil.Rise or 0.06
	for k = 1, parked do
		local ang = k * turn
		local radial = u * math.cos(ang) + v * math.sin(ang)
		local center = coil.Origin + axis * (rise * k) + radial * coil.Radius
		local tangent = (u * -math.sin(ang) + v * math.cos(ang)) * coil.Radius * turn + axis * rise
		out[k] = { Center = center, Tangent = tangent.Unit }
	end
	return out
end

-- Suggest a LinkCount for a measured maximum eyelet gap (studs) and pitch, with a safety margin.
function ChainSolver.SuggestLinkCount(maxGap: number, pitch: number, margin: number?): number
	return math.ceil((maxGap * (1 + (margin or 0.05))) / pitch - 1e-9)
end

return ChainSolver
