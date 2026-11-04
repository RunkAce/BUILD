--[[
	WarlinkTool (Script inside the Warlink Tool)
	R6 only has a RIGHT grip. The Tool's Handle (right cleaver) is held by Roblox's RightGrip weld as
	usual; this script welds the second cleaver ("CleaverL") to the R6 "Left Arm" at the same hand
	offset, mirrored. Your animations move the arms, so both cleavers and both chain eyelets follow.

	If your animations already drive weapon parts with custom Motor6Ds (animated tool rig), skip this
	script and use your own joints: the chain only needs the two "ChainEnd" attachments.
]]
local tool = script.Parent :: Tool
local left = tool:WaitForChild("CleaverL") :: BasePart

-- R6 hand point and default tool orientation: same as RightGrip's C0 on the Right Arm.
local HAND = CFrame.new(0, -1, 0) * CFrame.Angles(-math.pi / 2, 0, 0)
local MIRROR = CFrame.Angles(0, 0, 0) -- set to CFrame.Angles(0, math.pi, 0) if the left cleaver faces the wrong way

local weld: Weld? = nil

local function cleanup()
	if weld then
		weld:Destroy()
		weld = nil
	end
end

tool.Equipped:Connect(function()
	cleanup()
	local character = tool.Parent
	local arm = character and character:FindFirstChild("Left Arm")
	if not (arm and arm:IsA("BasePart")) then
		warn("[WarlinkTool] Left Arm not found: this tool expects an R6 character")
		return
	end
	left.Anchored = false
	left.CanCollide = false
	left.Massless = true
	local w = Instance.new("Weld")
	w.Name = "LeftGrip"
	w.Part0 = arm
	w.Part1 = left
	w.C0 = HAND
	w.C1 = tool.Grip * MIRROR
	w.Parent = arm
	weld = w
end)

tool.Unequipped:Connect(cleanup)
tool.Destroying:Connect(cleanup)
