--[[
	ClothSwayController (LocalScript in StarterPlayerScripts)
	Runs ClothSway on the skinned cloth of every equipped weapon, for every character, and stops it on
	unequip / destroy / respawn.

	Tag the weapon Tool "ClothSway" and set two string attributes on it:
	  ClothPart  = name of the skinned MeshPart inside the tool   (e.g. "Streamer" or "Ribbon")
	  ClothBones = comma-separated bones to drive, root excluded    (e.g. "Cloth1,Cloth2,Cloth3,Cloth4,Cloth5")
	Sunbound:   ClothBones = "Cloth1,Cloth2,Cloth3,Cloth4,Cloth5"                       (ClothRoot stays fixed)
	Flarecrest: ClothBones = "Ribbon1,Ribbon2,Ribbon3,Ribbon4,Ribbon5,Ribbon6,Ribbon7,Ribbon8" (RibbonRoot fixed)
]]
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local ClothSway = require(ReplicatedStorage:WaitForChild("WarlinkModules"):WaitForChild("ClothSway"))

local active: { [Tool]: any } = {}

local function stop(tool: Tool)
	local s = active[tool]
	if s then
		s:Destroy()
		active[tool] = nil
	end
end

local function refresh(tool: Tool)
	local character = tool.Parent
	if not (character and character:FindFirstChildOfClass("Humanoid")) then
		stop(tool)
		return
	end
	if active[tool] then
		return
	end
	local partName = tool:GetAttribute("ClothPart")
	local bones = tool:GetAttribute("ClothBones")
	local part = typeof(partName) == "string" and tool:FindFirstChild(partName, true)
	if not (part and part:IsA("BasePart") and typeof(bones) == "string") then
		return -- not streamed in yet; DescendantAdded retries
	end
	local names = {}
	for name in string.gmatch(bones, "[^,%s]+") do
		table.insert(names, name)
	end
	active[tool] = ClothSway.new(part, names)
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
	tool.DescendantAdded:Connect(function()
		refresh(tool)
	end)
	tool.Destroying:Connect(function()
		stop(tool)
	end)
end

for _, t in CollectionService:GetTagged("ClothSway") do
	track(t)
end
CollectionService:GetInstanceAddedSignal("ClothSway"):Connect(track)
CollectionService:GetInstanceRemovedSignal("ClothSway"):Connect(function(t)
	if t:IsA("Tool") then
		stop(t)
	end
end)
