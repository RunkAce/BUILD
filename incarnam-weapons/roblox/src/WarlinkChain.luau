--!strict
--[[
	WarlinkChain (ModuleScript, client) - visual chain built from ONE link mesh, strung between two
	Attachments every frame. Purely cosmetic: no physics, no collisions, no gameplay authority.

	Setup (see README "Warlink chain"):
	  ReplicatedStorage.WarlinkAssets.ChainLink     MeshPart (box-frame link, SurfaceAppearance)
	  ReplicatedStorage.WarlinkAssets.ChainEndLink  MeshPart (gold end link)      [optional]
	  Each cleaver has an Attachment named "ChainEnd" at its eyelet.

	Usage:
	  local chain = WarlinkChain.new(attachA, attachB, {
	      LinkCount = 32, Pitch = 0.21, Mode = "Coil", CoilArm = character["Left Arm"],
	      Ignore = { character },
	  })
	  ...
	  chain:Destroy()

	Mesh orientation: the exported link has its long axis on the part's +Y and its frame in the XY
	plane (Blender Z-up -> Roblox Y-up). If your importer settings differ, set Config.LinkRotation once.
]]

local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ChainSolver = require(script.Parent:WaitForChild("ChainSolver"))

export type Config = {
	LinkCount: number,
	Pitch: number?, -- default 0.21 (matches the exported link: 0.27 long, 0.03 bars)
	Mode: ("Hang" | "Coil")?,
	CoilArm: BasePart?, -- R6 "Left Arm" for Coil mode
	CoilRadius: number?, -- default 0.62 (R6 arm half-width 0.5 + link half-width)
	LinkTemplate: BasePart?,
	EndTemplate: BasePart?,
	LinkRotation: CFrame?, -- extra rotation applied to every link (importer orientation fix)
	Ignore: { Instance }?, -- excluded from the floor raycast (pass the character)
	FloorCheckInterval: number?, -- seconds between floor raycasts, default 0.1
	MaxDistance: number?, -- skip updates beyond this camera distance (studs), default 250
	FarUpdateInterval: number?, -- seconds between updates when far (LOD), default 1/15
	FarDistance: number?, -- studs from camera where LOD kicks in, default 80
	Parent: Instance?,
	Solver: { [string]: any }?, -- passthrough to ChainSolver (Gravity, Damping, MaxStretch, RestSlack...)
}

local WarlinkChain = {}
WarlinkChain.__index = WarlinkChain

local HALF_PI = math.pi / 2
local WORLD_UP = Vector3.new(0, 1, 0)
local WORLD_X = Vector3.new(1, 0, 0)

local function getVisualFolder(): Instance
	local f = workspace:FindFirstChild("_ChainVisuals")
	if not f then
		f = Instance.new("Folder")
		f.Name = "_ChainVisuals"
		f.Parent = workspace
	end
	return f :: Instance
end

local function prepPart(p: BasePart)
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.Massless = true
	p.CastShadow = true
end

-- Orientation for a link spanning p -> q. odd links are rolled 90 deg about the chain tangent.
local function linkCFrame(p: Vector3, q: Vector3, odd: boolean, sideHint: Vector3, extra: CFrame): (CFrame, Vector3)
	local d = q - p
	local len = d.Magnitude
	local t = if len > 1e-6 then d / len else WORLD_UP
	-- parallel-transport the side vector from the previous link to avoid twisting/flipping
	local side = sideHint - t * sideHint:Dot(t)
	if side.Magnitude < 1e-3 then
		local ref = if math.abs(t.Y) < 0.95 then WORLD_UP else WORLD_X
		side = ref:Cross(t)
	end
	side = side.Unit
	local x = if odd then t:Cross(side) else side
	local z = x:Cross(t)
	return CFrame.fromMatrix((p + q) * 0.5, x, t, z) * extra, side
end

function WarlinkChain.new(attachA: Attachment, attachB: Attachment, config: Config)
	local assets = ReplicatedStorage:FindFirstChild("WarlinkAssets")
	local linkT = config.LinkTemplate or (assets and assets:FindFirstChild("ChainLink")) :: BasePart?
	assert(linkT, "WarlinkChain: no link template (ReplicatedStorage.WarlinkAssets.ChainLink)")
	local endT = config.EndTemplate or (assets and assets:FindFirstChild("ChainEndLink")) :: BasePart?
	local n = config.LinkCount
	local pitch = config.Pitch or 0.21

	local solverCfg = table.clone(config.Solver or {})
	solverCfg.LinkCount = n
	solverCfg.Pitch = pitch
	solverCfg.Mode = config.Mode or "Hang"

	local model = Instance.new("Model")
	model.Name = "WarlinkChain"
	local parts: { BasePart } = table.create(n)
	for i = 1, n do
		local isEnd = (i == 1 or i == n) and endT ~= nil
		local p = ((if isEnd then endT else linkT) :: BasePart):Clone()
		p.Name = string.format("Link%02d", i)
		prepPart(p)
		p.Parent = model
		parts[i] = p
	end
	model.Parent = config.Parent or getVisualFolder()

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ignore = table.clone(config.Ignore or {})
	table.insert(ignore, model)
	params.FilterDescendantsInstances = ignore

	local self = setmetatable({
		A = attachA,
		B = attachB,
		Config = config,
		Solver = ChainSolver.new(solverCfg :: any),
		Model = model,
		Parts = parts,
		CFrames = table.create(n) :: { CFrame },
		_params = params,
		_floorY = nil :: number?,
		_floorTimer = 0,
		_lodTimer = 0,
		_conn = nil :: RBXScriptConnection?,
		_extra = config.LinkRotation or CFrame.identity,
		_side = WORLD_X,
		_warned = false,
	}, WarlinkChain)

	self._conn = RunService.RenderStepped:Connect(function(dt)
		self:Update(dt)
	end)
	return self
end

function WarlinkChain.Update(self: any, dt: number)
	local A: Attachment, B: Attachment = self.A, self.B
	if not (A.Parent and B.Parent) then
		self:Destroy()
		return
	end
	local cfg: Config = self.Config
	local a, b = A.WorldPosition, B.WorldPosition

	-- distance LOD
	local cam = workspace.CurrentCamera
	if cam then
		local dist = (cam.CFrame.Position - a).Magnitude
		if dist > (cfg.MaxDistance or 250) then
			return
		elseif dist > (cfg.FarDistance or 80) then
			self._lodTimer += dt
			if self._lodTimer < (cfg.FarUpdateInterval or 1 / 15) then
				return
			end
			dt = self._lodTimer
		end
		self._lodTimer = 0
	end

	-- floor under the chain (throttled raycast from the eyelet midpoint)
	self._floorTimer -= dt
	if self._floorTimer <= 0 then
		self._floorTimer = cfg.FloorCheckInterval or 0.1
		local mid = (a + b) * 0.5
		local hit = workspace:Raycast(mid, Vector3.new(0, -(self.Solver:Length() + 2), 0), self._params)
		self._floorY = if hit then hit.Position.Y else nil
	end

	local coil = nil
	if (cfg.Mode or "Hang") == "Coil" and cfg.CoilArm then
		local arm = cfg.CoilArm
		local up = arm.CFrame.UpVector
		coil = {
			Origin = arm.Position - up * 0.55,
			Axis = up,
			Radius = cfg.CoilRadius or 0.62,
		}
	end

	local pts = self.Solver:Step(a, b, dt, self._floorY, coil)
	local stats = self.Solver.Stats
	if stats.Overextended and not self._warned then
		self._warned = true
		warn(string.format("[WarlinkChain] eyelets %.2f studs apart > chain %.2f: raise LinkCount to %d",
			stats.Gap, stats.ChainLength, ChainSolver.SuggestLinkCount(stats.MaxObservedGap, self.Solver.Config.Pitch)))
	end

	local parts: { BasePart } = self.Parts
	local cfs: { CFrame } = self.CFrames
	local extra: CFrame = self._extra
	local n = #parts
	local paid = self.Solver.PaidOut
	-- parked (coiled) links first, wrapping up the forearm; paid-out links follow the solver points
	local slots = if coil then self.Solver:CoilSlots(coil) else {}
	local side = self._side
	local idx = 0
	for k = #slots, 1, -1 do
		idx += 1
		local s = slots[k]
		local cf
		cf, side = linkCFrame(s.Center - s.Tangent * 0.5 * self.Solver.Config.Pitch,
			s.Center + s.Tangent * 0.5 * self.Solver.Config.Pitch, idx % 2 == 0, side, extra)
		cfs[idx] = cf
	end
	side = self._side
	for i = 1, paid do
		idx += 1
		local cf
		cf, side = linkCFrame(pts[i], pts[i + 1], idx % 2 == 0, side, extra)
		cfs[idx] = cf
	end
	self._side = side
	for i = idx + 1, n do
		cfs[i] = cfs[idx]
	end
	workspace:BulkMoveTo(parts, cfs, Enum.BulkMoveMode.FireCFrameChanged)
end

function WarlinkChain.Destroy(self: any)
	if self._conn then
		self._conn:Disconnect()
		self._conn = nil
	end
	if self.Model then
		self.Model:Destroy()
		self.Model = nil
	end
end

return WarlinkChain
