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
	    parked in a coil wound up the A-side forearm from eyelet A (CoilSlots). The caller then simulates the
	    free span from the coil's exit joint to eyelet B. Topology: eyelet A -> coil -> free span -> eyelet B.
	    The total link count never changes, so length stays coherent.
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
	Start: Vector3, -- where the coil begins: eyelet A (first parked link hangs off it)
	Origin: Vector3, -- point on the forearm axis at the eyelet's height
	Axis: Vector3, -- unit vector along the forearm, pointing up the arm (away from the hand)
	U: Vector3?, -- arm face axis (R6: arm.CFrame.RightVector); keeps the coil basis attached to the arm
	HalfWidth: number?, -- arm half-width, R6 = 0.5 (1x2x1 arm)
	Clearance: number?, -- arm face -> link centre line, default 0.08 (link half-width 0.05 + 0.03 air)
	RisePerTurn: number?, -- studs climbed along Axis per full turn, default 0.115 (~one link width)
}

export type CoilSlot = { Center: Vector3, Tangent: Vector3, Radial: Vector3, From: Vector3, To: Vector3 }

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
	a, b      : free-span endpoints this frame (Hang: the eyelets; Coil: coil exit joint and eyelet B)
	dt        : seconds since last step (clamped internally)
	floorY    : optional ground height under the chain (nil = no floor)
	payoutGap : Coil mode: eyelet A -> eyelet B distance used to decide how many links are paid out
	returns   : array of joint points for the PAID-OUT links (length PaidOut+1, from a to b)
]]
function ChainSolver.Step(self: Solver, a: Vector3, b: Vector3, dt: number, floorY: number?, payoutGap: number?): { Vector3 }
	local c = self.Config
	local pitch = c.Pitch
	local gap = (b - a).Magnitude
	-- Coil: decide pay-out from the real eyelet-to-eyelet gap, not the coil-exit gap (which moves as links pay out)
	local target = self:_targetPaidOut(payoutGap or gap)

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
		local old, oldPrev = self.Points, self.Prev
		local fresh = seed(a, b, n, pitch)
		local freshPrev = table.clone(fresh)
		if self._initialised and #old > 0 then
			-- links enter/leave at the A end (the coil side) in both directions: old joint i -> new joint i+shift.
			-- Keeps every link's identity (and its render parity) and carries momentum over.
			local shift = (n + 1) - #old
			for i = 1, #old do
				local j = i + shift
				if j >= 2 and j <= n then
					fresh[j] = old[i]
					freshPrev[j] = oldPrev[i] or old[i]
				end
			end
		end
		self.Points = fresh
		self.Prev = freshPrev
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
	Coil for the links NOT paid out (Coil mode). The parked links hang from eyelet A to the arm, then wind up
	the forearm along the exact offset outline of the square R6 arm (straight faces + rounded corners), with
	consecutive joints exactly one Pitch apart so links sit edge to edge.
	Returns slots in order from the eyelet outward, and the exit joint where the free span begins.
]]
function ChainSolver.CoilSlots(self: Solver, coil: CoilFrame): ({ CoilSlot }, Vector3)
	local parked = self.Config.LinkCount - self.PaidOut
	local out: { CoilSlot } = table.create(math.max(parked, 0))
	if parked <= 0 then
		return out, coil.Start
	end
	local pitch = self.Config.Pitch
	local axis = coil.Axis.Unit
	local u: Vector3
	if coil.U then
		u = (coil.U - axis * coil.U:Dot(axis)).Unit
	else
		local ref = if math.abs(axis.Y) < 0.9 then Vector3.new(0, 1, 0) else Vector3.new(1, 0, 0)
		u = axis:Cross(ref).Unit
	end
	local v = axis:Cross(u)
	local hw = coil.HalfWidth or 0.5
	local d = coil.Clearance or 0.08 -- arm face -> link centre line (link half-width 0.05 + 0.03 air)
	local risePerArc = (coil.RisePerTurn or 0.115) / (8 * hw + 2 * math.pi * d)
	-- exact offset outline of the square arm: four straight faces at distance hw+d, quarter-circle corners
	-- of radius d around the arm corners; parameterised by arc length so the coil never clips a corner
	local side = 2 * hw
	local arcLen = 0.5 * math.pi * d
	local perimeter = 4 * (side + arcLen)
	local function outline(sArc: number): (number, number)
		local q = sArc % perimeter
		local seg = side + arcLen
		local k = math.floor(q / seg) -- which face (0..3), rotating +90 deg each
		local r = q - k * seg
		local x, y
		if r < side then -- straight face along +y at x = hw + d
			x, y = hw + d, -hw + r
		else -- corner arc around (hw, hw)
			local t = (r - side) / d
			x, y = hw + d * math.cos(t), hw + d * math.sin(t)
		end
		for _ = 1, k do
			x, y = -y, x
		end
		return x, y
	end
	-- start the outline on the side of the arm facing the eyelet
	local rel = coil.Start - coil.Origin
	local ru, rv = rel:Dot(u), rel:Dot(v)
	local s0, best = 0, -math.huge
	for i = 0, 255 do
		local sa = perimeter * i / 256
		local x, y = outline(sa)
		local score = (x * ru + y * rv) / math.sqrt(x * x + y * y)
		if score > best then
			best, s0 = score, sa
		end
	end
	local function pathPoint(sArc: number): Vector3
		local x, y = outline(sArc)
		return coil.Origin + axis * (risePerArc * (sArc - s0)) + u * x + v * y
	end
	local joints = table.create(parked + 1)
	joints[1] = coil.Start
	-- hang straight links from the eyelet to the arm surface if the eyelet sits away from it
	local first = pathPoint(s0)
	while #joints < parked + 1 and (first - joints[#joints]).Magnitude > pitch do
		table.insert(joints, joints[#joints] + (first - joints[#joints]).Unit * pitch)
	end
	local sArc = s0
	local step = 0.01
	local guard = 0
	while #joints < parked + 1 and guard < 200000 do
		guard += 1
		local prevS = sArc
		sArc += step
		local last = joints[#joints]
		if (pathPoint(sArc) - last).Magnitude >= pitch then
			-- bisect to the exact arc position where the chord equals one pitch (links edge to edge)
			local lo, hi = prevS, sArc
			for _ = 1, 24 do
				local mid = (lo + hi) * 0.5
				if (pathPoint(mid) - last).Magnitude >= pitch then
					hi = mid
				else
					lo = mid
				end
			end
			sArc = hi
			table.insert(joints, pathPoint(hi))
		end
	end
	local minClear = 0.05 + 0.01 -- link half-width + air
	for k = 1, parked do
		local j0, j1 = joints[k], joints[k + 1] or joints[k]
		local c = (j0 + j1) * 0.5
		-- a straight link spanning an arm corner would cut into the face: stand it off the corner
		local lc = c - coil.Origin
		local lx, ly = lc:Dot(u), lc:Dot(v)
		local qx = math.clamp(lx, -hw, hw)
		local qy = math.clamp(ly, -hw, hw)
		local dx, dy = lx - qx, ly - qy
		local dist = math.sqrt(dx * dx + dy * dy)
		if dist < minClear and dist > 1e-6 and lc:Dot(axis) > -0.05 then
			local push = minClear - dist
			c += (u * (dx / dist) + v * (dy / dist)) * push
		end
		local t = j1 - j0
		local tang = if t.Magnitude > 1e-6 then t.Unit else axis
		local radial = c - coil.Origin
		radial = radial - axis * radial:Dot(axis)
		out[k] = { Center = c, Tangent = tang, Radial = if radial.Magnitude > 1e-6 then radial.Unit else u, From = j0, To = j1 }
	end
	return out, joints[#joints]
end

-- Forget the shape (call after teleports or when a culled chain comes back): next Step re-seeds.
function ChainSolver.Reset(self: Solver)
	self._initialised = false
	self.Points = {}
	self.Prev = {}
end

-- Suggest a LinkCount for a measured maximum eyelet gap (studs) and pitch, with a safety margin.
function ChainSolver.SuggestLinkCount(maxGap: number, pitch: number, margin: number?): number
	return math.ceil((maxGap * (1 + (margin or 0.05))) / pitch - 1e-9)
end

return ChainSolver
