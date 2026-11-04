--[[
	WarlinkChainController (LocalScript in StarterPlayerScripts)
	Shows the Warlink chain for EVERY character (yours and other players') while a Warlink tool is
	equipped, and removes it on unequip, tool destroy, respawn or character removal.

	A Warlink tool is any Tool tagged "Warlink" (CollectionService) containing two parts that each have an
	Attachment named "ChainEnd" (the eyelets): the Handle (right cleaver) and "CleaverL".
	Tool attributes (optional): LinkCount (number), Pitch (number), ChainMode ("Coil" | "Hang").
]]
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local modules = ReplicatedStorage:WaitForChild("WarlinkModules")
local WarlinkChain = require(modules:WaitForChild("WarlinkChain"))

local DEFAULT_LINKS = 32 -- placeholder: replace with the MeasureHandSpan result for your animations

local active: { [Tool]: any } = {}

local function eyelet(part: Instance?): Attachment?
	if part then
		local a = part:FindFirstChild("ChainEnd")
		if a and a:IsA("Attachment") then
			return a
		end
	end
	return nil
end

local function stop(tool: Tool)
	local c = active[tool]
	if c then
		c:Destroy()
		active[tool] = nil
	end
end

local function refresh(tool: Tool)
	local character = tool.Parent
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		stop(tool)
		return
	end
	if active[tool] then
		return
	end
	local a = eyelet(tool:FindFirstChild("CleaverL"))
	local b = eyelet(tool:FindFirstChild("Handle"))
	if not (a and b) then
		return -- parts still streaming in; AncestryChanged/ChildAdded will retry
	end
	active[tool] = WarlinkChain.new(a, b, {
		LinkCount = tool:GetAttribute("LinkCount") or DEFAULT_LINKS,
		Pitch = tool:GetAttribute("Pitch") or 0.21,
		Mode = tool:GetAttribute("ChainMode") or "Coil",
		CoilArm = character:FindFirstChild("Left Arm") :: BasePart?,
		Ignore = { character },
	})
end

local function track(tool: Instance)
	if not tool:IsA("Tool") then
		return
	end
	refresh(tool)
	tool.AncestryChanged:Connect(function()
		if tool:IsDescendantOf(game) then
			refresh(tool)
		else
			stop(tool)
		end
	end)
	tool.ChildAdded:Connect(function()
		refresh(tool)
	end)
	tool.Destroying:Connect(function()
		stop(tool)
	end)
end

for _, t in CollectionService:GetTagged("Warlink") do
	track(t)
end
CollectionService:GetInstanceAddedSignal("Warlink"):Connect(track)
CollectionService:GetInstanceRemovedSignal("Warlink"):Connect(function(t)
	if t:IsA("Tool") then
		stop(t)
	end
end)
