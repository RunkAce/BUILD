--!strict
-- GhostVan runtime setup. Put this Script and the GhostVanConfig ModuleScript inside the imported GhostVan Model.
-- The van is a parked investigation HQ: every part is anchored, doors open with ProximityPrompts,
-- lights follow the model attribute "LightsOn" (true/false), and seats are created at the cab seats + stool.
-- Rotate/move the WHOLE model (Model:PivotTo), never single parts: door hinges are worked out in the van's frame.

local TweenService = game:GetService("TweenService")

local model = script.Parent :: Model
local Config = require(model:WaitForChild("GhostVanConfig")) :: any

local function part(name: string): BasePart?
	return model:FindFirstChild(name, true) :: BasePart?
end

local body = part(Config.BodyPart)
assert(body, "GhostVan: Body MeshPart not found")
-- model origin (ground point between the axles) in world space; all Config.Points are relative to it
local origin = body.CFrame * CFrame.new(-Config.BodyBoxCentre)

local function rgb(c: { number }): Color3
	return Color3.fromRGB(c[1], c[2], c[3])
end

-- ------------------------------------------------------------------ parts
for _, d in model:GetDescendants() do
	if d:IsA("BasePart") then
		d.Anchored = true
	end
end
for _, n in Config.NoCollide do
	local p = part(n)
	if p then
		p.CanCollide = false
		p.CanQuery = false
	end
end
for n, c in Config.Neon do
	local p = part(n)
	if p then
		p.Material = Enum.Material.Neon
		p.Color = rgb(c)
		p.CastShadow = false
	end
end
local glass = part(Config.Glass.Part)
if glass then
	glass.Material = Enum.Material.Glass
	glass.Color = rgb(Config.Glass.Color)
	glass.Transparency = Config.Glass.Transparency
	glass.CastShadow = false
end

-- ------------------------------------------------------------------ screens: SurfaceGui ready for camera feeds
for n, s in Config.Screens do
	local p = part(n)
	if p and not p:FindFirstChildOfClass("SurfaceGui") then
		p.Material = Enum.Material.SmoothPlastic
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Feed"
		gui.Face = Enum.NormalId[s.Face]
		gui.LightInfluence = 0
		gui.PixelsPerStud = 80
		gui.Parent = p
		local label = Instance.new("TextLabel")
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundColor3 = Color3.fromRGB(6, 26, 16)
		label.TextColor3 = Color3.fromRGB(80, 255, 160)
		label.Font = Enum.Font.Code
		label.TextScaled = true
		label.Text = n == "Screen1" and "CAM 1\nNO SIGNAL" or n == "Screen2" and "EMF\n--" or "AUDIO\n--"
		label.Parent = gui
	end
end

-- ------------------------------------------------------------------ lights
local lights: { Light } = {}
local function addLight(p: BasePart?, kind: string, props: { [string]: any })
	if not p then
		return
	end
	local l = Instance.new(kind :: any) :: any
	for k, v in props do
		l[k] = v
	end
	l.Parent = p
	table.insert(lights, l)
end
addLight(part("HeadLights"), "SpotLight", { Face = Enum.NormalId.Front, Range = 40, Angle = 70, Brightness = 3,
	Color = Color3.fromRGB(255, 240, 210), Shadows = true })
addLight(part("TailLights"), "PointLight", { Range = 8, Brightness = 1.5, Color = Color3.fromRGB(255, 40, 40) })
addLight(part("LightBar"), "PointLight", { Range = 14, Brightness = 1.5, Color = Color3.fromRGB(108, 255, 176) })
addLight(part("CabinLights"), "SurfaceLight", { Face = Enum.NormalId.Bottom, Range = 12, Angle = 120, Brightness = 2.2,
	Color = Color3.fromRGB(170, 245, 255), Shadows = true })

local neonParts = {}
for n in Config.Neon do
	local p = part(n)
	if p then
		neonParts[p] = p.Color
	end
end
local function applyLights()
	local on = model:GetAttribute("LightsOn") ~= false
	for _, l in lights do
		l.Enabled = on
	end
	for p, c in neonParts do
		p.Material = on and Enum.Material.Neon or Enum.Material.SmoothPlastic
		p.Color = on and c or c:Lerp(Color3.new(0, 0, 0), 0.75)
	end
end
if model:GetAttribute("LightsOn") == nil then
	model:SetAttribute("LightsOn", true)
end
model:GetAttributeChangedSignal("LightsOn"):Connect(applyLights)
applyLights()

-- ------------------------------------------------------------------ seats
local function seat(name: string, at: Vector3, facing: Vector3)
	local s = Instance.new("Seat")
	s.Name = name
	s.Size = Vector3.new(1.8, 0.4, 1.8)
	s.Transparency = 1
	s.Anchored = true
	s.CanCollide = false
	local pos = origin * at
	s.CFrame = CFrame.lookAt(pos, pos + origin:VectorToWorldSpace(facing))
	s.Parent = model
end
seat("DriverSeat", Config.Points.DriverSeat, Vector3.new(0, 0, -1))
seat("PassengerSeat", Config.Points.PassengerSeat, Vector3.new(0, 0, -1))
seat("DeskSeat", Config.Points.Stool, Vector3.new(-1, 0, 0))   -- faces the monitors on the left wall

-- ------------------------------------------------------------------ doors
local TWEEN = TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)

local function makeDoor(name: string, d: any)
	local p = part(name)
	if not p then
		return
	end
	local closed = p.CFrame
	local hinge = closed * CFrame.new(d.HingeOffset)        -- door parts share the van's orientation
	local rel = hinge:Inverse() * closed
	local t = Instance.new("NumberValue")
	t.Name = "OpenAmount"
	t.Parent = p
	t.Changed:Connect(function(a: number)
		if d.Kind == "Hinge" then
			p.CFrame = hinge * CFrame.Angles(0, math.rad(d.Angle * a), 0) * rel
		else
			-- slide out first (0..0.25), then back along the rail
			local out = math.clamp(a / 0.25, 0, 1)
			local back = math.clamp((a - 0.25) / 0.75, 0, 1)
			p.CFrame = closed * CFrame.new(d.Out * out, 0, d.Back * back)
		end
	end)
	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "Open"
	prompt.ObjectText = (name:gsub("(%l)(%u)", "%1 %2"))
	prompt.MaxActivationDistance = 9
	prompt.RequiresLineOfSight = false
	prompt.Parent = p
	local open = false
	prompt.Triggered:Connect(function()
		open = not open
		prompt.ActionText = open and "Close" or "Open"
		TweenService:Create(t, TWEEN, { Value = open and 1 or 0 }):Play()
	end)
end

for name, d in Config.Doors do
	makeDoor(name, d)
end
