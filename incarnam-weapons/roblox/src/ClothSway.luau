--!strict
--[[
	ClothSway (ModuleScript, client) - procedural secondary motion for the skinned Sunbound streamer and the
	Flarecrest ribbon. Sets Bone.Transform (an offset on top of the bind pose) every frame, so do NOT also
	key these cloth bones in animations (they are not part of the R6 rig, so existing animations don't).
	The root bone (ClothRoot / RibbonRoot) is never driven, so the attachment point stays pinned.

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
	IdleAmplitude: number?, -- total degrees at the tip (summed down the chain), default 14
	Stiffness: number?, -- spring stiffness, default 60
	DampingRatio: number?, -- default 0.55 (under-damped: a little overshoot, then settle)
	InertiaGain: number?, -- degrees per stud/s of weapon motion, default 2.2
	MaxLean: number?, -- total degrees clamp at the tip, default 45
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
	local missing = {}
	for _, n in boneNames do
		local b = part:FindFirstChild(n, true)
		if b and b:IsA("Bone") then
			if not (cfg.Pinned and cfg.Pinned[n]) then
				table.insert(bones, b)
			end
		else
			table.insert(missing, n)
		end
	end
	if #missing > 0 then
		warn(string.format("[ClothSway] %s is missing bones: %s (was the FBX imported as a skinned mesh?)",
			part:GetFullName(), table.concat(missing, ", ")))
	end
	-- Bone.Transform is parent-relative, so rotations add up down the chain: give each bone only its
	-- INCREMENT of the curve (dw), so the summed angle at the tip equals the configured total.
	local n = #bones
	local dw = table.create(n, 0)
	for i = 1, n do
		dw[i] = (i / n) ^ 1.3 - ((i - 1) / n) ^ 1.3
	end
	local self = setmetatable({
		Part = part,
		Bones = bones,
		Config = cfg,
		_dw = dw,
		_t = 0,
		_lastPos = part.Position,
		_sx = table.create(n, 0),
		_sv = table.create(n, 0),
		_sz = table.create(n, 0),
		_svz = table.create(n, 0),
		_conn = nil :: RBXScriptConnection?,
	}, ClothSway)
	self._conn = RunService.RenderStepped:Connect(function(dt)
		self:Update(dt)
	end)
	return self
end

function ClothSway.Update(self: any, rawDt: number)
	local part: BasePart = self.Part
	if not part.Parent then
		self:Destroy()
		return
	end
	local dt = math.clamp(rawDt, 1 / 240, 1 / 20) -- for springs and the idle phase
	local cfg: Config = self.Config
	self._t += dt
	local period = cfg.Period or 3
	local ph = 2 * math.pi * (self._t % period) / period
	-- world velocity from the REAL frame time (a hitch must not inflate it); ignore teleports/equip snaps
	local pos = part.Position
	local delta = pos - self._lastPos
	self._lastPos = pos
	local worldVel = if delta.Magnitude > 5 then Vector3.zero else delta / math.max(rawDt, 1 / 240)
	local gain = math.rad(cfg.InertiaGain or 2.2)
	local maxLean = math.rad(cfg.MaxLean or 45)
	local k, zeta = cfg.Stiffness or 60, cfg.DampingRatio or 0.55
	local amp = math.rad(cfg.IdleAmplitude or 14)
	local dw = self._dw
	for i, bone in self.Bones do
		local lag = i * 0.7
		-- velocity in the frame the bone's Transform is applied in (parent pose * bone rest)
		local parent = bone.Parent
		local frame = (if parent and parent:IsA("Bone") then (parent :: Bone).TransformedWorldCFrame else part.CFrame) * bone.CFrame
		local v = frame:VectorToObjectSpace(worldVel)
		-- bones point along +Y: rotating +X swings the tip toward +Z, rotating +Z swings it toward -X.
		-- Trail BEHIND the motion: tip goes toward -v.
		local share = dw[i]
		local tx = math.clamp(-v.Z * gain, -maxLean, maxLean) * share
		local tz = math.clamp(v.X * gain, -maxLean, maxLean) * share
		local kk = k / (1 + i * 0.25)
		self._sx[i], self._sv[i] = ClothSway.SpringStep(self._sx[i], self._sv[i], tx, kk, zeta, dt)
		self._sz[i], self._svz[i] = ClothSway.SpringStep(self._sz[i], self._svz[i], tz, kk, zeta, dt)
		local idleX = amp * share * math.sin(ph - lag)
		local idleY = amp * 0.7 * share * math.sin(2 * ph - lag * 1.3 + 1.0)
		local idleZ = amp * 0.55 * share * math.sin(ph - lag + 2.0)
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

-- Pure helper (testable): the per-bone increments sum to exactly 1 (tip total = configured total).
function ClothSway.Increments(n: number): { number }
	local out = table.create(n, 0)
	for i = 1, n do
		out[i] = (i / n) ^ 1.3 - ((i - 1) / n) ^ 1.3
	end
	return out
end

return ClothSway
