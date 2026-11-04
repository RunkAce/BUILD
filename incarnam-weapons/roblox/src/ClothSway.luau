--!strict
--[[
	ClothSway (ModuleScript, client) - procedural secondary motion for the skinned Sunbound streamer and the
	Flarecrest ribbon. Drives Bone.Transform (an offset on top of the bind pose), so it layers with any
	animation and never moves the cloth root (Sunbound pommel ring / Flarecrest ribbon root stay pinned).

	Behaviour (from the 1.mp4 study): root locked, amplitude and lag grow toward the free end, a seamless
	idle loop with distinct poses, plus an inertial response: when the weapon moves, the cloth trails
	behind on damped springs and settles back.

	Usage:
	  local sway = ClothSway.new(meshPart, { "Cloth1", "Cloth2", "Cloth3", "Cloth4", "Cloth5" }, { Period = 3 })
	  sway:Destroy()
]]
local RunService = game:GetService("RunService")

export type Config = {
	Period: number?, -- idle loop length (s), default 3
	IdleAmplitude: number?, -- degrees at the tip, default 14
	Stiffness: number?, -- spring stiffness, default 60
	DampingRatio: number?, -- default 0.55 (under-damped: a little overshoot, then settle)
	InertiaGain: number?, -- degrees per stud/s of weapon motion, default 2.2
	MaxLean: number?, -- degrees clamp, default 45
	Pinned: { [string]: boolean }?, -- bones that never move (e.g. RibbonRoot)
}

local ClothSway = {}
ClothSway.__index = ClothSway

-- Pure helper (testable): one semi-implicit Euler step of a damped spring toward target.
function ClothSway.SpringStep(x: number, v: number, target: number, k: number, zeta: number, dt: number): (number, number)
	local c = 2 * zeta * math.sqrt(k)
	local a = k * (target - x) - c * v
	v += a * dt
	x += v * dt
	return x, v
end

function ClothSway.new(part: BasePart, boneNames: { string }, config: Config?)
	local cfg: Config = config or {}
	local bones: { Bone } = {}
	for _, n in boneNames do
		local b = part:FindFirstChild(n, true)
		if b and b:IsA("Bone") and not (cfg.Pinned and cfg.Pinned[n]) then
			table.insert(bones, b)
		end
	end
	local self = setmetatable({
		Part = part,
		Bones = bones,
		Config = cfg,
		_t = 0,
		_lastPos = part.Position,
		_sx = table.create(#bones, 0),
		_sv = table.create(#bones, 0),
		_sz = table.create(#bones, 0),
		_svz = table.create(#bones, 0),
		_conn = nil :: RBXScriptConnection?,
	}, ClothSway)
	self._conn = RunService.RenderStepped:Connect(function(dt)
		self:Update(dt)
	end)
	return self
end

function ClothSway.Update(self: any, dt: number)
	local part: BasePart = self.Part
	if not part.Parent then
		self:Destroy()
		return
	end
	dt = math.clamp(dt, 1 / 240, 1 / 20)
	local cfg: Config = self.Config
	self._t += dt
	local period = cfg.Period or 3
	local ph = 2 * math.pi * (self._t % period) / period
	-- weapon velocity in the part's local space drives the inertial lean
	local pos = part.Position
	local vel = part.CFrame:VectorToObjectSpace((pos - self._lastPos) / dt)
	self._lastPos = pos
	local gain = math.rad(cfg.InertiaGain or 2.2)
	local maxLean = math.rad(cfg.MaxLean or 45)
	local k, zeta = cfg.Stiffness or 60, cfg.DampingRatio or 0.55
	local amp = math.rad(cfg.IdleAmplitude or 14)
	local n = #self.Bones
	for i, bone in self.Bones do
		local w = (i / n) ^ 1.3 -- freedom grows toward the tip
		local lag = i * 0.7
		-- springs chase a target lean opposite to the motion (cloth trails behind), stronger toward the tip
		local tx = math.clamp(vel.Z * gain * w, -maxLean, maxLean)
		local tz = math.clamp(-vel.X * gain * w, -maxLean, maxLean)
		self._sx[i], self._sv[i] = ClothSway.SpringStep(self._sx[i], self._sv[i], tx, k / (1 + i * 0.25), zeta, dt)
		self._sz[i], self._svz[i] = ClothSway.SpringStep(self._sz[i], self._svz[i], tz, k / (1 + i * 0.25), zeta, dt)
		local idleX = amp * (0.25 + 0.75 * w) * math.sin(ph - lag)
		local idleY = amp * 0.7 * w * math.sin(2 * ph - lag * 1.3 + 1.0)
		local idleZ = amp * 0.55 * w * math.sin(ph - lag + 2.0)
		bone.Transform = CFrame.Angles(idleX + self._sx[i], idleY, idleZ + self._sz[i])
	end
end

function ClothSway.Destroy(self: any)
	if self._conn then
		self._conn:Disconnect()
		self._conn = nil
	end
	for _, b in self.Bones do
		if b.Parent then
			b.Transform = CFrame.identity
		end
	end
end

return ClothSway
